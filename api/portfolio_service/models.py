# api/portfolio_service/models.py
from __future__ import annotations
from typing import Tuple, Dict, List
from .db import DB, User, Portfolio, Transaction

def create_user(user_id: str, email: str) -> User:
    if user_id in DB.users:
        raise ValueError("user_exists")
    u = User(id=user_id, email=email)
    DB.users[user_id] = u
    return u

def get_user(user_id: str) -> User:
    u = DB.users.get(user_id)
    if not u:
        raise KeyError("user_not_found")
    return u

def create_portfolio(user_id: str, name: str, risk_level: int) -> Portfolio:
    if user_id not in DB.users:
        raise KeyError("user_not_found")
    pid = DB.next_portfolio_id()
    p = Portfolio(id=pid, user_id=user_id, name=name, risk_level=risk_level)
    DB.portfolios[pid] = p
    return p

def get_portfolio(pid: int) -> Portfolio:
    p = DB.portfolios.get(pid)
    if not p:
        raise KeyError("portfolio_not_found")
    return p

def list_transactions(pid: int) -> List[Transaction]:
    return DB.transactions_by_portfolio.get(pid, [])

def _cash_and_positions(pid: int) -> Tuple[float, Dict[str, Tuple[float, float]]]:
    """
    Returns:
      cash (float),
      positions map: symbol -> (net_qty, last_seen_price)
    """
    txs = list_transactions(pid)
    cash = 0.0
    positions: Dict[str, Tuple[float, float]] = {}  # symbol -> (qty, last_price)
    for tx in txs:
        if tx.type == "deposit":
            cash += round(float(tx.amount or 0.0), 2)
        elif tx.type == "withdraw":
            cash -= round(float(tx.amount or 0.0), 2)
        elif tx.type == "buy":
            cost = float(tx.quantity or 0.0) * float(tx.price or 0.0)
            cash -= round(cost, 2)
            qty, _last = positions.get(tx.symbol or "", (0.0, 0.0))
            positions[tx.symbol or ""] = (qty + float(tx.quantity or 0.0), float(tx.price or 0.0))
        elif tx.type == "sell":
            proceeds = float(tx.quantity or 0.0) * float(tx.price or 0.0)
            cash += round(proceeds, 2)
            qty, _last = positions.get(tx.symbol or "", (0.0, 0.0))
            positions[tx.symbol or ""] = (qty - float(tx.quantity or 0.0), float(tx.price or 0.0))
    return round(cash, 2), positions

def _would_cash_go_negative(pid: int, new_tx: Transaction) -> bool:
    cash, _ = _cash_and_positions(pid)
    if new_tx.type == "withdraw":
        return cash - round(float(new_tx.amount or 0.0), 2) < 0
    if new_tx.type == "buy":
        cost = float(new_tx.quantity or 0.0) * float(new_tx.price or 0.0)
        return cash - round(cost, 2) < 0
    return False

def add_transaction(
    pid: int,
    type_: str,
    amount: float | None = None,
    symbol: str | None = None,
    quantity: float | None = None,
    price: float | None = None,
) -> Transaction:
    if pid not in DB.portfolios:
        raise KeyError("portfolio_not_found")

    # Validate minimally (deep validation happens at API layer)
    tx = Transaction(
        id=DB.next_tx_id(),
        portfolio_id=pid,
        type=type_,
        amount=amount,
        symbol=symbol,
        quantity=quantity,
        price=price,
    )
    if _would_cash_go_negative(pid, tx):
        raise ValueError("insufficient_funds")

    DB.transactions_by_portfolio[pid].append(tx)
    # Keep newest-first order for convenience
    DB.transactions_by_portfolio[pid].sort(key=lambda t: t.id, reverse=True)
    return tx

def compute_summary(pid: int):
    p = get_portfolio(pid)
    cash, positions_map = _cash_and_positions(pid)

    positions_out = []
    total_positions_value = 0.0
    for sym, (qty, last_price) in positions_map.items():
        if round(qty, 6) == 0.0:
            continue
        mv = round(qty * last_price, 2)
        total_positions_value += mv
        positions_out.append({"symbol": sym, "quantity": round(qty, 6), "market_value": mv})

    total_value = round(cash + total_positions_value, 2)
    return {
        "portfolio": {"id": p.id, "user_id": p.user_id, "name": p.name, "risk_level": p.risk_level},
        "cash": cash,
        "positions": positions_out,
        "total_value": total_value,
    }
