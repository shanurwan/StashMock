# api/portfolio_service/schemas.py
from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal, List
from datetime import datetime

class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"

# ---- Users ----
class UserCreate(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    email: EmailStr

class UserOut(BaseModel):
    id: str
    email: EmailStr

# ---- Portfolios ----
class PortfolioCreate(BaseModel):
    user_id: str
    name: str = Field(min_length=1, max_length=100)
    risk_level: int = Field(ge=1, le=20)

class PortfolioOut(BaseModel):
    id: int
    user_id: str
    name: str
    risk_level: int

# ---- Transactions ----
TxType = Literal["deposit", "withdraw", "buy", "sell"]

class TransactionCreate(BaseModel):
    type: TxType
    # money movement
    amount: Optional[float] = None
    # trading
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None

    @field_validator("amount")
    @classmethod
    def _amount_pos(cls, v, info):
        # Only validate when used
        return v

    @field_validator("symbol")
    @classmethod
    def _symbol_upper(cls, v):
        return v.upper() if v else v

class TransactionOut(BaseModel):
    id: int
    portfolio_id: int
    type: TxType
    amount: Optional[float] = None
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    created_at: datetime

# ---- Positions & Summary ----
class PositionOut(BaseModel):
    symbol: str
    quantity: float
    market_value: float

class SummaryOut(BaseModel):
    portfolio: PortfolioOut
    cash: float
    positions: List[PositionOut]
    total_value: float

# ---- Errors (shape) ----
class ErrorOut(BaseModel):
    error: str
    detail: str
