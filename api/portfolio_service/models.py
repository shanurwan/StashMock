# api/portfolio_service/models.py
from __future__ import annotations
from decimal import Decimal
from typing import Dict, List, Tuple
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from .db import User, Portfolio, Transaction

# ---- Users ----
def create_user(db: Session, user_id: str, email: str) -> User:
    if db.get(User, user_id):
        raise ValueError("user_exists")
    u = User(id=user_id, email=email)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def get_user(db: Session, user_id: str) -> User:
    u = db.get(User, user_id)
    if not u:
        raise KeyError("user_not_found")
    return u

# ---- Portfolios ----
def create_portfolio(db: Session, user_id: str, name: str, risk_level: int) -> Portfolio:
    if not db.get(User, user_id):
        raise KeyError("user_not_found")
    p = Portfolio(user_id=user_id, name=name, risk_level=risk_level)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def get_portfolio(db: Session, pid: int) -> Portfolio:
    p = db.get(Portfolio, pid)
    if not p:
        raise KeyError("portfolio_not_found")
    return p

# ---- Transactions ----
def list_transactions(db: Session, pid: int) -> List[Transaction]:
    if not db.get(Portfolio, pid):
        raise KeyError("portfolio_not_found")
    q = select(Transaction).where(Transaction.portfolio_id == pid).order_by(desc(Transaction.id))
    return list(db.scalars(q))

def _cash_and_positions(db: Session, pid: int) -> Tuple[Decimal, Dict[str, Tuple[Decimal, Decimal]]]:
    txs = list_transactions(db, pid)
    cash = Decimal("0.00")
    positions: Dict[str, Tuple[Decimal, Decimal]] = {}  # symbol -> (qty, last_price)
    for tx in txs:
        t = tx.type
        amt = Decimal(str(tx.amount)) if tx.amount is not None else Decimal("0")
        qty = Decimal(str(tx.quantity)) if tx.quantity is not None else Decimal("0")
        price = Decimal(str(tx.price)) if tx.price is not None else Decimal("0")
        sym = (tx.symbol or "").upper()

        if t == "deposit":
            cash += amt
        elif t == "withdraw":
            cash -= amt
        elif t == "buy":
            cash -= (qty * price)
            q0, _ = positions.get(sym, (Decimal("0"), Decimal("0")))
            positions[sym] = (q0 + qty, price)
        elif t == "sell":
            cash += (qty * price)
            q0, _ = positions.get(sym, (Decimal("0"), Decimal("0")))
            positions[sym] = (q0 - qty, price)
    # rounding rules
    cash = cash.quantize(Decimal("0.01"))
    return cash, positions

def _would_cash_go_negative(db: Session, pid: int, new_type: str, amount, quantity, price) -> bool:
    cash, _ = _cash_and_positions(db, pid)
    if new_type == "withdraw" and amount is not None:
        return (cash - Decimal(str(amount))).quantize(Decimal("0.01")) < Decimal("0.00")
    if new_type == "buy" and quantity is not None and price is not None:
        cost = (Decimal(str(quantity)) * Decimal(str(price))).quantize(Decimal("0.01"))
        return (cash - cost) < Decimal("0.00")
    return False

def add_transaction(
    db: Session,
    pid: int,
    type_: str,
    amount: float | None = None,
    symbol: str | None = None,
    quantity: float | None = None,
    price: float | None = None,
) -> Transaction:
    if not db.get(Portfolio, pid):
        raise KeyError("portfolio_not_found")

    if _would_cash_go_negative(db, pid, type_, amount, quantity, price):
        raise ValueError("insufficient_funds")

    tx = Transaction(
        portfolio_id=pid,
        type=type_,
        amount=amount,
        symbol=(symbol.upper() if symbol else None),
        quantity=quantity,
        price=price,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

# ---- Summary ----
def compute_summary(db: Session, pid: int):
    p = get_portfolio(db, pid)
    cash, positions_map = _cash_and_positions(db, pid)

    positions_out = []
    total_positions_value = Decimal("0.00")
    for sym, (qty, last_price) in positions_map.items():
        if qty.quantize(Decimal("0.000001")) == Decimal("0"):
            continue
        mv = (qty * last_price).quantize(Decimal("0.01"))
        total_positions_value += mv
        positions_out.append(
            {
                "symbol": sym,
                "quantity": float(qty),
                "market_value": float(mv),
            }
        )

    total_value = (cash + total_positions_value).quantize(Decimal("0.01"))
    return {
        "portfolio": {"id": p.id, "user_id": p.user_id, "name": p.name, "risk_level": p.risk_level},
        "cash": float(cash),
        "positions": positions_out,
        "total_value": float(total_value),
    }

