
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime

class UserCreate(BaseModel):
    id: str = Field(min_length=1)
    email: EmailStr

class UserOut(BaseModel):
    id: str
    email: EmailStr
    class Config: from_attributes = True

class PortfolioCreate(BaseModel):
    user_id: str
    name: str

class PortfolioOut(BaseModel):
    id: int
    user_id: str
    name: str
    class Config: from_attributes = True

TxType = Literal["deposit", "withdraw", "buy", "sell"]

class TxCreate(BaseModel):
    type: TxType
    symbol: Optional[str] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    amount: Optional[float] = None

class TxOut(BaseModel):
    id: int
    portfolio_id: int
    type: TxType
    symbol: Optional[str]
    quantity: Optional[float]
    price: Optional[float]
    amount: Optional[float]
    created_at: datetime
    class Config: from_attributes = True

class Position(BaseModel):
    symbol: str
    quantity: float
    market_value: float

class PortfolioSummary(BaseModel):
    portfolio: PortfolioOut
    cash: float
    positions: List[Position]
