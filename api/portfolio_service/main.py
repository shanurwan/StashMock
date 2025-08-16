# api/portfolio_service/main.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException, Response, Depends
from typing import List, Optional
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from sqlalchemy.orm import Session
from .db import init_db, get_session
from .schemas import (
    HealthOut, UserCreate, UserOut, PortfolioCreate, PortfolioOut,
    TransactionCreate, TransactionOut, SummaryOut, ErrorOut
)
from .models import (
    create_user, get_user, create_portfolio, get_portfolio,
    add_transaction, list_transactions, compute_summary
)
from .metrics import prometheus_middleware

app = FastAPI(title="StashMock Portfolio Service (M2: DB)", version="0.2.0")
app.middleware("http")(prometheus_middleware())

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health", response_model=HealthOut)
def health():
    return {"status": "ok"}

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

@app.get("/users/{user_id}", response_model=UserOut, responses={404: {"model": ErrorOut}})
def get_user_ep(user_id: str, db: Session = Depends(get_session)):
    try:
        u = get_user(db, user_id)
        return {"id": u.id, "email": u.email}
    except KeyError:
        raise HTTPException(status_code=404, detail="user not found")

# ---- Portfolios ----
@app.post("/portfolios", response_model=PortfolioOut, responses={404: {"model": ErrorOut}})
def create_portfolio_ep(body: PortfolioCreate, db: Session = Depends(get_session)):
    try:
        p = create_portfolio(db, body.user_id, body.name, body.risk_level)
        return {"id": p.id, "user_id": p.user_id, "name": p.name, "risk_level": p.risk_level}
    except KeyError:
        raise HTTPException(status_code=404, detail="user not found")

@app.get("/portfolios/{pid}", response_model=PortfolioOut, responses={404: {"model": ErrorOut}})
def get_portfolio_ep(pid: int, db: Session = Depends(get_session)):
    try:
        p = get_portfolio(db, pid)
        return {"id": p.id, "user_id": p.user_id, "name": p.name, "risk_level": p.risk_level}
    except KeyError:
        raise HTTPException(status_code=404, detail="portfolio not found")

# ---- Transactions ----
@app.post(
    "/portfolios/{pid}/transactions",
    response_model=TransactionOut,
    responses={404: {"model": ErrorOut}, 422: {"model": ErrorOut}}
)
def create_tx_ep(pid: int, body: TransactionCreate, db: Session = Depends(get_session)):
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
            db=db,
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
            "amount": float(tx.amount) if tx.amount is not None else None,
            "symbol": tx.symbol,
            "quantity": float(tx.quantity) if tx.quantity is not None else None,
            "price": float(tx.price) if tx.price is not None else None,
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
def list_txs_ep(pid: int, limit: int = 50, before_id: Optional[int] = None, db: Session = Depends(get_session)):
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
        out.append({
            "id": t.id,
            "portfolio_id": t.portfolio_id,
            "type": t.type,
            "amount": float(t.amount) if t.amount is not None else None,
            "symbol": t.symbol,
            "quantity": float(t.quantity) if t.quantity is not None else None,
            "price": float(t.price) if t.price is not None else None,
            "created_at": t.created_at,
        })
    return out

# ---- Summary ----
@app.get("/portfolios/{pid}/summary", response_model=SummaryOut, responses={404: {"model": ErrorOut}})
def summary_ep(pid: int, db: Session = Depends(get_session)):
    try:
        data = compute_summary(db, pid)
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail="portfolio not found")


