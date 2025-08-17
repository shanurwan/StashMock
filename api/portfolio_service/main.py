# api/portfolio_service/main.py
from __future__ import annotations
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Response, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text
from sqlalchemy.orm import Session
import os, json
from redis import Redis
import fakeredis

from .db import get_session, engine
from .schemas import (
    HealthOut,
    UserCreate,
    UserOut,
    PortfolioCreate,
    PortfolioOut,
    TransactionCreate,
    TransactionOut,
    SummaryOut,
    ErrorOut,
)
from .models import (
    create_user,
    get_user,
    create_portfolio,
    get_portfolio,
    add_transaction,
    list_transactions,
    compute_summary,
)
from .metrics import observability_middleware  # M3: enhanced metrics/logging



REDIS_URL = os.getenv("REDIS_URL", "fakeredis://")
NOTIFY_QUEUE = os.getenv("NOTIFY_QUEUE", "notify_events")
TASK_QUEUE = os.getenv("TASK_QUEUE", "worker_tasks")

def _redis_client() -> Redis:
    if REDIS_URL.startswith("fakeredis://"):
        return fakeredis.FakeRedis(decode_responses=True)
    return Redis.from_url(REDIS_URL, decode_responses=True)

rpub = _redis_client()


app = FastAPI(title="StashMock Portfolio Service (M3: Observability)", version="0.3.0")

# M3: structured logs + Prometheus metrics (latency buckets, in-flight, errors)
app.middleware("http")(observability_middleware())


# --- Liveness (fast, no deps) ---
@app.get("/live")
def live():
    return {"status": "ok"}


# --- Readiness (checks DB quickly) ---
@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="db not ready")


# --- Health (lightweight, no DB touch) ---
@app.get("/health", response_model=HealthOut)
def health():
    return {"status": "ok"}


# --- Metrics (Prometheus) ---
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---- Users ----
@app.post("/users", response_model=UserOut, responses={409: {"model": ErrorOut}})
def create_user_ep(body: UserCreate, db: Session = Depends(get_session)):
    try:
        u = create_user(db, body.id, body.email)
        return {"id": u.id, "email": u.email}
    except ValueError:
        raise HTTPException(status_code=409, detail="user already exists")


@app.get(
    "/users/{user_id}", response_model=UserOut, responses={404: {"model": ErrorOut}}
)
def get_user_ep(user_id: str, db: Session = Depends(get_session)):
    try:
        u = get_user(db, user_id)
        return {"id": u.id, "email": u.email}
    except KeyError:
        raise HTTPException(status_code=404, detail="user not found")


# ---- Portfolios ----
@app.post(
    "/portfolios", response_model=PortfolioOut, responses={404: {"model": ErrorOut}}
)
def create_portfolio_ep(body: PortfolioCreate, db: Session = Depends(get_session)):
    try:
        p = create_portfolio(db, body.user_id, body.name, body.risk_level)
        return {
            "id": p.id,
            "user_id": p.user_id,
            "name": p.name,
            "risk_level": p.risk_level,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="user not found")


@app.get(
    "/portfolios/{pid}",
    response_model=PortfolioOut,
    responses={404: {"model": ErrorOut}},
)
def get_portfolio_ep(pid: int, db: Session = Depends(get_session)):
    try:
        p = get_portfolio(db, pid)
        return {
            "id": p.id,
            "user_id": p.user_id,
            "name": p.name,
            "risk_level": p.risk_level,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="portfolio not found")


# ---- Transactions ----
    try:
        tx = add_transaction(
            db=db,
            pid=pid,
            type_=t,
            amount=body.amount,
            symbol=body.symbol,
            quantity=body.quantity,
            price=body.price,
        )

        # --- publish events to Redis ---
        try:
            rpub.rpush(NOTIFY_QUEUE, json.dumps({
                "event": "transaction_created",
                "portfolio_id": pid,
                "tx_id": tx.id,
                "type": tx.type,
            }))
            rpub.rpush(TASK_QUEUE, json.dumps({
                "task": "recompute_summary_hint",
                "portfolio_id": pid
            }))
        except Exception:
            # best-effort, don’t block the API if queueing fails
            pass

        # --- normal API response ---
        return {
            "id": tx.id,
            "portfolio_id": tx.portfolio_id,
            "type": tx.type,
            "amount": float(tx.amount) if tx.amount is not None else None,
            "symbol": tx.symbol,
            "quantity": float(tx.quantity) if tx.quantity is not None else None,
            "price": float(tx.price) if tx.price is not None else None,
            "created_at": tx.created_at,
        }



@app.get(
    "/portfolios/{pid}/transactions",
    response_model=List[TransactionOut],
    responses={404: {"model": ErrorOut}},
)
def list_txs_ep(
    pid: int,
    limit: int = 50,
    before_id: Optional[int] = None,
    db: Session = Depends(get_session),
):
    if limit <= 0:
        limit = 50
    if limit > 200:
        limit = 200
    try:
        txs = list_transactions(db, pid)
    except KeyError:
        raise HTTPException(status_code=404, detail="portfolio not found")

    if before_id is not None:
        txs = [t for t in txs if t.id < before_id]
    out = []
    for t in txs[:limit]:
        out.append(
            {
                "id": t.id,
                "portfolio_id": t.portfolio_id,
                "type": t.type,
                "amount": float(t.amount) if t.amount is not None else None,
                "symbol": t.symbol,
                "quantity": float(t.quantity) if t.quantity is not None else None,
                "price": float(t.price) if t.price is not None else None,
                "created_at": t.created_at,
            }
        )
    return out


# ---- Summary ----
@app.get(
    "/portfolios/{pid}/summary",
    response_model=SummaryOut,
    responses={404: {"model": ErrorOut}},
)
def summary_ep(pid: int, db: Session = Depends(get_session)):
    try:
        data = compute_summary(db, pid)
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail="portfolio not found")
