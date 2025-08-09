import os
import asyncio
from typing import Dict, List, Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from redis.asyncio import from_url as redis_from_url
from prometheus_fastapi_instrumentator import Instrumentator

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_EVENTS = os.getenv("STREAM_EVENTS", "events")
STREAM_TASKS = os.getenv("STREAM_TASKS", "tasks")

# Toggle: when true, do email/logging inline (slow baseline).
# When false, offload to Redis-backed notification service (fast).
SYNC_NOTIFICATIONS = os.getenv("SYNC_NOTIFICATIONS", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

app = FastAPI(title="portfolio_service")
Instrumentator().instrument(app).expose(app)


# ---- In-memory store (swap to Postgres later) ----
class Portfolio(BaseModel):
    id: int
    owner_name: str
    balance: float = 0.0


class PortfolioCreate(BaseModel):
    owner_name: str = Field(..., min_length=1)


class TxnCreate(BaseModel):
    portfolio_id: int
    amount: float = Field(..., gt=0)
    type: Literal["deposit", "withdraw"] = "deposit"


PORTFOLIOS: Dict[int, Portfolio] = {}
TXNS: Dict[int, List[TxnCreate]] = {}
_portfolio_id_seq = 0

# ---- Redis client ----
redis = redis_from_url(REDIS_URL)


@app.on_event("startup")
async def _startup():
    # sanity: ping redis on startup
    await redis.ping()


@app.get("/health")
async def health():
    return {"status": "ok", "sync_notifications": SYNC_NOTIFICATIONS}


# ---- Simulated blocking I/O for baseline comparison ----
async def _send_email_blocking(to: str, subject: str, body: str):
    # Simulate network+SMTP latency (~80ms)
    await asyncio.sleep(0.08)


async def _write_audit_log_blocking(entry: str):
    # Simulate log shipper / fsync / HTTP log sink (~40ms)
    await asyncio.sleep(0.04)


@app.post("/portfolios", response_model=Portfolio)
async def create_portfolio(body: PortfolioCreate):
    global _portfolio_id_seq
    _portfolio_id_seq += 1
    p = Portfolio(id=_portfolio_id_seq, owner_name=body.owner_name, balance=0.0)
    PORTFOLIOS[p.id] = p
    TXNS[p.id] = []
    return p


@app.get("/portfolios/{pid}", response_model=Portfolio)
async def get_portfolio(pid: int):
    p = PORTFOLIOS.get(pid)
    if not p:
        raise HTTPException(404, "Portfolio not found")
    return p


@app.post("/transactions")
async def create_txn(body: TxnCreate):
    p = PORTFOLIOS.get(body.portfolio_id)
    if not p:
        raise HTTPException(404, "Portfolio not found")

    if body.type == "deposit":
        p.balance += body.amount
    else:
        if p.balance < body.amount:
            raise HTTPException(400, "Insufficient funds")
        p.balance -= body.amount

    TXNS[body.portfolio_id].append(body)

    # Prepare email payload
    email_payload = {
        "event_type": "email",
        "to": f"{p.owner_name}@example.com",
        "subject": "Transaction receipt",
        "body": f"{body.type.title()} of {body.amount:.2f} processed for portfolio {p.id}.",
    }

    if SYNC_NOTIFICATIONS:
        # Baseline: do side effects inline on the request path (slower)
        await _send_email_blocking(
            to=email_payload["to"],
            subject=email_payload["subject"],
            body=email_payload["body"],
        )
        await _write_audit_log_blocking(
            f"txn:{body.type} amount:{body.amount} pid:{p.id}"
        )
    else:
        # Offload: enqueue for the notifications service (faster)
        await redis.xadd(STREAM_EVENTS, email_payload)  # Redis Stream

    # Publish a background recalculation task (always offloaded)
    await redis.xadd(
        STREAM_TASKS,
        {
            "task_type": "recalc",
            "portfolio_id": str(p.id),
        },
    )

    return {
        "ok": True,
        "new_balance": p.balance,
        "notifications_offloaded": not SYNC_NOTIFICATIONS,
    }


# Dev server tip:
# uvicorn api.portfolio_service.main:app --reload --port 8001
