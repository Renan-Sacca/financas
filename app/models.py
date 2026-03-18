from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
import uuid

class CardType(str, Enum):
    credit = "credit"
    debit = "debit"

# TransactionType removido pois a tabela Transaction será exclusiva para cartões
# Depósitos agora têm sua própria tabela

class CreatedVia(str, Enum):
    web = "web"
    bot = "bot"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    is_active: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None)
    reset_token: Optional[str] = Field(default=None)
    id_telegram: Optional[int] = Field(default=None, unique=True, index=True)
    username_telegram: Optional[str] = Field(default=None, index=True)
    telefone: str = Field(max_length=15, unique=True, index=True)
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

class IncomeType(SQLModel, table=True):
    __tablename__ = "income_type"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class PaymentMethod(SQLModel, table=True):
    __tablename__ = "payment_method"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class IncomeCategory(SQLModel, table=True):
    __tablename__ = "income_category"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    color: Optional[str] = Field(default="#007bff")
    created_at: datetime = Field(default_factory=datetime.now)

class Deposit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    bank_id: Optional[int] = Field(default=None, foreign_key="bank.id")
    amount: float = Field(gt=0)
    description: Optional[str] = Field(default=None)
    type_id: int = Field(foreign_key="income_type.id")
    payment_method_id: int = Field(foreign_key="payment_method.id")
    income_category_id: Optional[int] = Field(default=None, foreign_key="income_category.id")
    date: date
    created_at: datetime = Field(default_factory=datetime.now)
    source: Optional[str] = Field(default="web")

    bank: Optional[Bank] = Relationship()
    income_type: IncomeType = Relationship()
    payment_method: PaymentMethod = Relationship()
    income_category: Optional[IncomeCategory] = Relationship()

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id")
    amount: float = Field(gt=0)
    description: str
    date: date
    purchase_date: Optional[date] = Field(default=None)
    is_paid: bool = Field(default=False)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    group_id: Optional[str] = Field(default=None)
    installment_number: Optional[int] = Field(default=None)
    total_installments: Optional[int] = Field(default=None)
    created_via: CreatedVia = Field(default=CreatedVia.web)
    created_at: datetime = Field(default_factory=datetime.now)
    
    card: Card = Relationship(back_populates="transactions")
    category: Optional[Category] = Relationship(back_populates="transactions")