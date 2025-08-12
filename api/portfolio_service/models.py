
from sqlalchemy import Column, String, Integer, ForeignKey, Numeric, Enum, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum
from .db import Base

class TxType(str, enum.Enum):
    deposit = "deposit"
    withdraw = "withdraw"
    buy = "buy"
    sell = "sell"

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    portfolios: Mapped[list["Portfolio"]] = relationship("Portfolio", back_populates="user")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    type: Mapped[TxType] = mapped_column(Enum(TxType))
    
    symbol: Mapped[str | None] = mapped_column(String, nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(18, 6), nullable=True)
   
    amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="transactions")
