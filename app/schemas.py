from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import List, Optional
from app.models import CardType, CreatedVia

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    telefone: str
    id_telegram: Optional[int] = None
    username_telegram: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    id_telegram: Optional[int] = None
    username_telegram: Optional[str] = None
    telefone: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    telefone: Optional[str] = None
    id_telegram: Optional[int] = None
    username_telegram: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class EmailVerification(BaseModel):
    token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

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

class CardCreateBot(BaseModel):
    bank_id: int
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

class IncomeTypeResponse(BaseModel):
    id: int
    name: str

class PaymentMethodResponse(BaseModel):
    id: int
    name: str

class IncomeCategoryCreate(BaseModel):
    name: str
    color: Optional[str] = "#007bff"

class IncomeCategoryResponse(BaseModel):
    id: int
    user_id: int
    name: str
    color: Optional[str] = "#007bff"

class DepositCreate(BaseModel):
    bank_id: int
    amount: float
    description: Optional[str] = None
    type_id: int
    payment_method_id: int
    income_category_id: Optional[int] = None
    income_category_name: Optional[str] = None
    date: date
    add_to_balance: bool = True

class DepositUpdate(BaseModel):
    bank_id: Optional[int] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    type_id: Optional[int] = None
    payment_method_id: Optional[int] = None
    income_category_id: Optional[int] = None
    date: Optional[str] = None
    adjust_balance: bool = False

class DepositResponse(BaseModel):
    id: int
    user_id: int
    bank_id: int
    bank_name: Optional[str] = None
    amount: float
    description: Optional[str] = None
    type_id: int
    type_name: Optional[str] = None
    payment_method_id: int
    payment_method_name: Optional[str] = None
    income_category_id: Optional[int] = None
    income_category_name: Optional[str] = None
    income_category_color: Optional[str] = None
    date: date
    source: Optional[str] = None

class TransactionCreate(BaseModel):
    card_id: int
    amount: float
    description: str
    date: date
    purchase_date: Optional[date] = None
    category_id: Optional[int] = None
    group_id: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None

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
    description: str
    date: date
    purchase_date: Optional[date] = None
    is_paid: bool
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    group_id: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    created_via: CreatedVia
    card_name: str
    card_type: CardType
    bank_name: str

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

# ── Pending Statement Items ──────────────────────────────────────────────────
class PendingItemUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data_compra: Optional[date] = None
    card_id: Optional[int] = None
    category_id: Optional[int] = None
    status: Optional[str] = None  # pending | approved | rejected
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None

class PendingItemResponse(BaseModel):
    id: int
    batch_id: str
    card_id: int
    card_name: Optional[str] = None
    bank_name: Optional[str] = None
    descricao: str
    valor: float
    data_compra: date
    tipo: Optional[str] = None
    status: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    filename: Optional[str] = None
    installment_number: Optional[int] = None
    total_installments: Optional[int] = None
    created_at: datetime

class BatchSummary(BaseModel):
    batch_id: str
    filename: Optional[str]
    card_name: Optional[str]
    bank_name: Optional[str]
    total_items: int
    pending: int
    approved: int
    rejected: int
    created_at: datetime

# ── Pending Bank Items (extrato bancário) ────────────────────────────────────
class PendingBankItemUpdate(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[float] = None
    data: Optional[date] = None
    bank_id: Optional[int] = None
    category_id: Optional[int] = None
    status: Optional[str] = None

class PendingBankItemResponse(BaseModel):
    id: int
    batch_id: str
    bank_id: Optional[int] = None
    bank_name: Optional[str] = None
    descricao: str
    valor: float
    data: date
    tipo: Optional[str] = None
    status: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    filename: Optional[str] = None
    created_at: datetime

class BankBatchSummary(BaseModel):
    batch_id: str
    filename: Optional[str]
    bank_id: Optional[int]
    bank_name: Optional[str]
    total_items: int
    pending: int
    approved: int
    rejected: int
    confirmed: int
    created_at: datetime