# This is the main portfolio to enable product and QA teams to rapidly access real account data for tesing/demo
# Goal for portfolio service :
# 1 - user see their investment status
# 2 - user perform investment actions
# 3 - user view their investment history
# 4 - user gets real time update and notification



# api/portfolio_service/main.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import List, Optional

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .schemas import (
    HealthOut, UserCreate, UserOut, PortfolioCreate, PortfolioOut,
    TransactionCreate, TransactionOut, SummaryOut, ErrorOut
)
from .models import (
    create_user, get_user, create_portfolio, get_portfolio,
    add_transaction, list_transactions, compute_summary
)
from .metrics import prometheus_middleware

app = FastAPI(title="StashMock Portfolio Service (M1)", version="0.1.0")

# Prometheus middleware
app.middleware("http")(prometheus_middleware())

# --- Health ---
@app.get("/health", response_model=HealthOut)
def health():
    return {"status": "ok"}

# --- Metrics ---
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# --- Users ---
@app.post("/users", response_model=UserOut, responses={409: {"model": ErrorOut}})
def create_user_ep(body: UserCreate):
    try:
        u = create_user(body.id, body.email)
        return {"id": u.id, "email": u.email}
    except ValueError:
        raise HTTPException(status_code=409, detail="user already exists")

@app.get("/users/{user_id}", response_model=UserOut, responses={404: {"model": ErrorOut}})
def get_user_ep(user_id: str):
    try:
        u = get_user(user_id)
        return {"id": u.id, "email": u.email}
    except KeyError:
        raise HTTPException(status_code=404, detail="user not found")

# --- Portfolios ---
@app.post("/portfolios", response_model=PortfolioOut, responses={404: {"model": ErrorOut}})
def create_portfolio_ep(body: PortfolioCreate):
    try:
        p = create_portfolio(body.user_id, body.name, body.risk_level)
        return {"id": p.id, "user_id": p.user_id, "name": p.name, "risk_level": p.risk_level}
    except KeyError:
        raise HTTPException(status_code=404, detail="user not found")

@app.get("/portfolios/{pid}", response_model=PortfolioOut, responses={404: {"model": ErrorOut}})
def get_portfolio_ep(pid: int):
    try:
        p = get_portfolio(pid)
        return {"id": p.id, "user_id": p.user_id, "name": p.name, "risk_level": p.risk_level}
    except KeyError:
        raise HTTPException(status_code=404, detail="portfolio not found")

# --- Transactions ---
@app.post(
    "/portfolios/{pid}/transactions",
    response_model=TransactionOut,
    responses={404: {"model": ErrorOut}, 422: {"model": ErrorOut}}
)
def create_tx_ep(pid: int, body: TransactionCreate):
    # basic validation
    t = body.type
    if t in ("deposit", "withdraw"):
        if body.amount is None or body.amount <= 0:
            raise HTTPException(status_code=422, detail="amount must be > 0")
    elif t in ("buy", "sell"):
        if not body.symbol or body.quantity is None or body.price is None:
            raise HTTPException(status_code=422, detail="symbol, quantity and price are required")
        if body.quantity <= 0 or body.price <= 0:
            raise HTTPException(status_code=422, detail="quantity and price must be > 0")
    else:
        raise HTTPException(status_code=422, detail="unknown transaction type")

    try:
        tx = add_transaction(
            pid=pid,
            type_=t,
            amount=body.amount,
            symbol=body.symbol,
            quantity=body.quantity,
            price=body.price,
        )
        return {
            "id": tx.id,
            "portfolio_id": tx.portfolio_id,
            "type": tx.type,
            "amount": tx.amount,
            "symbol": tx.symbol,
            "quantity": tx.quantity,
            "price": tx.price,
            "created_at": tx.created_at,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="portfolio not found")
    except ValueError as e:
        if str(e) == "insufficient_funds":
            raise HTTPException(status_code=422, detail="cash would go negative")
        raise

@app.get(
    "/portfolios/{pid}/transactions",
    response_model=List[TransactionOut],
    responses={404: {"model": ErrorOut}}
)
def list_txs_ep(pid: int, limit: int = 50, before_id: Optional[int] = None):
    if limit <= 0:
        limit = 50
    if limit > 200:
        limit = 200
    try:
        txs = list_transactions(pid)
    except Exception:
        raise HTTPException(status_code=404, detail="portfolio not found")
    if before_id is not None:
        txs = [t for t in txs if t.id < before_id]
    return [
        {
            "id": t.id,
            "portfolio_id": t.portfolio_id,
            "type": t.type,
            "amount": t.amount,
            "symbol": t.symbol,
            "quantity": t.quantity,
            "price": t.price,
            "created_at": t.created_at,
        }
        for t in txs[:limit]
    ]

# --- Summary ---
@app.get("/portfolios/{pid}/summary", response_model=SummaryOut, responses={404: {"model": ErrorOut}})
def summary_ep(pid: int):
    try:
        data = compute_summary(pid)
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail="portfolio not found")

