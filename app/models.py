from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
import uuid

class CardType(str, Enum):
    credit = "credit"
    debit = "debit"

class TransactionType(str, Enum):
    expense = "expense"
    payment = "payment"
    refund = "refund"
    deposit = "deposit"
    transfer_out = "transfer_out"
    transfer_in = "transfer_in"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    is_active: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None)
    reset_token: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    
    banks: List["Bank"] = Relationship(back_populates="user")
    categories: List["Category"] = Relationship(back_populates="user")

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    color: Optional[str] = Field(default="#007bff")
    created_at: datetime = Field(default_factory=datetime.now)
    
    user: User = Relationship(back_populates="categories")
    transactions: List["Transaction"] = Relationship(back_populates="category")

class Bank(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    current_balance: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.now)
    
    user: User = Relationship(back_populates="banks")
    cards: List["Card"] = Relationship(back_populates="bank")

class Card(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    name: str
    type: CardType
    limit_amount: Optional[float] = Field(default=None)
    due_day: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    
    bank: Bank = Relationship(back_populates="cards")
    transactions: List["Transaction"] = Relationship(back_populates="card")

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id")
    amount: float = Field(gt=0)
    type: TransactionType = Field(default=TransactionType.expense)
    description: str
    date: date
    purchase_date: Optional[date] = Field(default=None)
    is_paid: bool = Field(default=False)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    group_id: Optional[str] = Field(default=None)
    installment_number: Optional[int] = Field(default=None)
    total_installments: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    transfer_to_bank_id: Optional[int] = Field(default=None, foreign_key="bank.id")
    
    card: Card = Relationship(back_populates="transactions")
    category: Optional[Category] = Relationship(back_populates="transactions")
    transfer_to_bank: Optional[Bank] = Relationship()