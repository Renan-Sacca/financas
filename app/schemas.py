from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from app.models import CardType, TransactionType

class BankCreate(BaseModel):
    name: str
    initial_balance: Optional[float] = 0.0

class BankUpdate(BaseModel):
    name: Optional[str] = None
    initial_balance: Optional[float] = None

class BankResponse(BaseModel):
    id: int
    name: str
    initial_balance: float
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

class TransactionCreate(BaseModel):
    card_id: int
    amount: float
    type: TransactionType = TransactionType.expense
    description: str
    date: date
    purchase_date: Optional[date] = None
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