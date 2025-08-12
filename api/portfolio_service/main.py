
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from . import schemas, crud, models
from .db import Base, engine
from .deps import get_db
from .events import publish

app = FastAPI(title="StashMock Portfolio API", version="0.1.0")


Base.metadata.create_all(bind=engine)

REQUEST_LATENCY = Histogram("portfolio_request_latency_seconds", "Latency for Portfolio API requests")
REQUEST_COUNT = Counter("portfolio_requests_total", "Total Portfolio API requests")

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/metrics")
def metrics(): return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/users", response_model=schemas.UserOut)
@REQUEST_LATENCY.time()
def create_user(data: schemas.UserCreate, db: Session = Depends(get_db)):
    REQUEST_COUNT.inc()
    if crud.get_user(db, data.id):
        raise HTTPException(409, "user exists")
    user = crud.create_user(db, data)
    publish("user.created", {"user_id": user.id, "email": user.email})
    return user


@app.post("/portfolios", response_model=schemas.PortfolioOut)
@REQUEST_LATENCY.time()
def create_portfolio(data: schemas.PortfolioCreate, db: Session = Depends(get_db)):
    REQUEST_COUNT.inc()
    if not crud.get_user(db, data.user_id):
        raise HTTPException(404, "user not found")
    pf = crud.create_portfolio(db, data)
    publish("portfolio.created", {"portfolio_id": pf.id, "user_id": pf.user_id, "name": pf.name})
    return pf

@app.get("/portfolios/{pid}", response_model=schemas.PortfolioOut)
@REQUEST_LATENCY.time()
def get_portfolio(pid: int, db: Session = Depends(get_db)):
    REQUEST_COUNT.inc()
    pf = crud.get_portfolio(db, pid)
    if not pf: raise HTTPException(404, "not found")
    return pf


@app.post("/portfolios/{pid}/transactions", response_model=schemas.TxOut)
@REQUEST_LATENCY.time()
def add_tx(pid: int, tx: schemas.TxCreate, db: Session = Depends(get_db)):
    REQUEST_COUNT.inc()
    if not crud.get_portfolio(db, pid):
        raise HTTPException(404, "portfolio not found")
    created = crud.add_transaction(db, pid, tx)
    publish("transaction.created", {"portfolio_id": pid, "tx_id": created.id, "type": tx.type})
    return created

@app.get("/portfolios/{pid}/transactions", response_model=list[schemas.TxOut])
@REQUEST_LATENCY.time()
def list_tx(pid: int, db: Session = Depends(get_db)):
    REQUEST_COUNT.inc()
    if not crud.get_portfolio(db, pid):
        raise HTTPException(404, "portfolio not found")
    return crud.list_transactions(db, pid)


@app.get("/portfolios/{pid}/summary", response_model=schemas.PortfolioSummary)
@REQUEST_LATENCY.time()
def summary(pid: int, db: Session = Depends(get_db)):
    REQUEST_COUNT.inc()
    pf = crud.get_portfolio(db, pid)
    if not pf: raise HTTPException(404, "portfolio not found")
    s = crud.compute_summary(db, pid)
    return {"portfolio": pf, **s}
