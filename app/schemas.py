from pydantic import BaseModel, EmailStr
from datetime import date
from typing import List, Optional
from app.models import CardType, TransactionType

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_verified: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class EmailVerification(BaseModel):
    token: str

class BankCreate(BaseModel):
    name: str
    current_balance: Optional[float] = 0.0

class BankUpdate(BaseModel):
    name: Optional[str] = None
    current_balance: Optional[float] = None

class BankResponse(BaseModel):
    id: int
    name: str
    current_balance: float

class CardCreate(BaseModel):
    name: str
    type: CardType
    limit_amount: Optional[float] = None
    due_day: Optional[int] = None

class CardUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[CardType] = None
    limit_amount: Optional[float] = None
    due_day: Optional[int] = None

class CardResponse(BaseModel):
    id: int
    bank_id: int
    name: str
    type: CardType
    limit_amount: Optional[float] = None
    due_day: Optional[int] = None

class CategoryCreate(BaseModel):
    name: str
    color: Optional[str] = "#007bff"

class CategoryResponse(BaseModel):
    id: int
    name: str
    color: str

class TransactionCreate(BaseModel):
    card_id: int
    amount: float
    type: TransactionType = TransactionType.expense
    description: str
    date: date
    purchase_date: Optional[date] = None
    category_id: Optional[int] = None
    group_id: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    transfer_to_bank_id: Optional[int] = None

class TransferCreate(BaseModel):
    from_bank_id: int
    to_bank_id: int
    amount: float
    description: str
    date: date

class TransactionResponse(BaseModel):
    id: int
    card_id: int
    amount: float
    type: TransactionType
    description: str
    date: date
    purchase_date: Optional[date] = None
    is_paid: bool
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    group_id: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    card_name: str
    card_type: CardType
    bank_name: str
    transfer_to_bank_name: Optional[str] = None

class BankSummary(BaseModel):
    bank_id: int
    bank_name: str
    balance: float

class Summary(BaseModel):
    banks: List[BankSummary]
    total_balance: float

class CreditLimitSummary(BaseModel):
    card_name: str
    bank_name: str
    total_limit: float
    used_limit: float
    available_limit: float