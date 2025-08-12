
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from . import models, schemas

def create_user(db: Session, data: schemas.UserCreate) -> models.User:
    user = models.User(id=data.id, email=data.email)
    db.add(user); db.commit(); db.refresh(user)
    return user

def get_user(db: Session, user_id: str):
    return db.get(models.User, user_id)

def create_portfolio(db: Session, data: schemas.PortfolioCreate) -> models.Portfolio:
    pf = models.Portfolio(user_id=data.user_id, name=data.name)
    db.add(pf); db.commit(); db.refresh(pf)
    return pf

def get_portfolio(db: Session, portfolio_id: int):
    return db.get(models.Portfolio, portfolio_id)

def add_transaction(db: Session, portfolio_id: int, tx: schemas.TxCreate) -> models.Transaction:
    t = models.Transaction(
        portfolio_id=portfolio_id,
        type=tx.type,
        symbol=tx.symbol,
        quantity=tx.quantity,
        price=tx.price,
        amount=tx.amount,
    )
    db.add(t); db.commit(); db.refresh(t)
    return t

def list_transactions(db: Session, portfolio_id: int):
    stmt = select(models.Transaction).where(models.Transaction.portfolio_id == portfolio_id).order_by(models.Transaction.id.desc())
    return db.execute(stmt).scalars().all()

def compute_summary(db: Session, portfolio_id: int) -> dict:
   
    deposits = db.query(func.coalesce(func.sum(models.Transaction.amount), 0)).filter(
        models.Transaction.portfolio_id==portfolio_id, models.Transaction.type=="deposit").scalar()
    withdraws = db.query(func.coalesce(func.sum(models.Transaction.amount), 0)).filter(
        models.Transaction.portfolio_id==portfolio_id, models.Transaction.type=="withdraw").scalar()
    cash = float(deposits) - float(withdraws)

    
    rows = db.execute(
        select(models.Transaction.symbol, func.coalesce(func.sum(models.Transaction.quantity), 0))
        .where(models.Transaction.portfolio_id==portfolio_id, models.Transaction.symbol.is_not(None))
        .group_by(models.Transaction.symbol)
    ).all()
    positions = []
    for sym, qty in rows:
        qty = float(qty or 0)
        if qty == 0: 
            continue
        
        last_price = db.execute(
            select(models.Transaction.price)
            .where(models.Transaction.portfolio_id==portfolio_id, models.Transaction.symbol==sym, models.Transaction.price.is_not(None))
            .order_by(models.Transaction.id.desc())
        ).scalars().first() or 1.0
        positions.append({"symbol": sym, "quantity": qty, "market_value": qty * float(last_price)})

   
    buys = db.query(func.coalesce(func.sum(models.Transaction.quantity * models.Transaction.price), 0)).filter(
        models.Transaction.portfolio_id==portfolio_id, models.Transaction.type=="buy").scalar()
    sells = db.query(func.coalesce(func.sum(models.Transaction.quantity * models.Transaction.price), 0)).filter(
        models.Transaction.portfolio_id==portfolio_id, models.Transaction.type=="sell").scalar()
    cash = cash - float(buys) + float(sells)

    return {"cash": cash, "positions": positions}
