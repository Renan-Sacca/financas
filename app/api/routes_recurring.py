from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel
from app.db_utils import execute_with_retry
from app.models import Card, Bank, Category, User, CreatedVia
from app.auth import get_current_user
from sqlmodel import Session, select

router = APIRouter(prefix="/api/recurring", tags=["recurring"])

# ──── Models ────
from sqlmodel import SQLModel, Field

class RecurringPurchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    card_id: int = Field(foreign_key="card.id")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    description: str
    amount: float = Field(gt=0)
    day_of_month: int = Field(ge=1, le=31)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)

# ──── Schemas ────
class RecurringPurchaseCreate(BaseModel):
    card_id: int
    category_id: Optional[int] = None
    description: str
    amount: float
    day_of_month: int

class RecurringPurchaseUpdate(BaseModel):
    card_id: Optional[int] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    day_of_month: Optional[int] = None
    is_active: Optional[bool] = None

class RecurringPurchaseResponse(BaseModel):
    id: int
    card_id: int
    card_name: str
    bank_name: str
    category_id: Optional[int]
    category_name: Optional[str]
    category_color: Optional[str]
    description: str
    amount: float
    day_of_month: int
    is_active: bool

# ──── Routes ────
@router.post("", response_model=RecurringPurchaseResponse, status_code=201)
def create_recurring(data: RecurringPurchaseCreate, current_user: User = Depends(get_current_user)):
    def query(session: Session):
        card = session.get(Card, data.card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        bank = session.get(Bank, card.bank_id)
        if bank.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Card does not belong to user")
        
        recurring = RecurringPurchase(
            user_id=current_user.id,
            card_id=data.card_id,
            category_id=data.category_id,
            description=data.description,
            amount=data.amount,
            day_of_month=data.day_of_month
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)
        
        category_name = None
        category_color = None
        if recurring.category_id:
            category = session.get(Category, recurring.category_id)
            if category:
                category_name = category.name
                category_color = category.color
        
        return RecurringPurchaseResponse(
            id=recurring.id,
            card_id=recurring.card_id,
            card_name=card.name,
            bank_name=bank.name,
            category_id=recurring.category_id,
            category_name=category_name,
            category_color=category_color,
            description=recurring.description,
            amount=recurring.amount,
            day_of_month=recurring.day_of_month,
            is_active=recurring.is_active
        )
    
    return execute_with_retry(query)

@router.get("", response_model=List[RecurringPurchaseResponse])
def list_recurring(current_user: User = Depends(get_current_user)):
    def query(session: Session):
        items = session.exec(
            select(RecurringPurchase).where(RecurringPurchase.user_id == current_user.id)
        ).all()
        
        result = []
        for item in items:
            card = session.get(Card, item.card_id)
            bank = session.get(Bank, card.bank_id)
            
            category_name = None
            category_color = None
            if item.category_id:
                category = session.get(Category, item.category_id)
                if category:
                    category_name = category.name
                    category_color = category.color
            
            result.append(RecurringPurchaseResponse(
                id=item.id,
                card_id=item.card_id,
                card_name=card.name,
                bank_name=bank.name,
                category_id=item.category_id,
                category_name=category_name,
                category_color=category_color,
                description=item.description,
                amount=item.amount,
                day_of_month=item.day_of_month,
                is_active=item.is_active
            ))
        
        return result
    
    return execute_with_retry(query)

@router.put("/{recurring_id}", response_model=RecurringPurchaseResponse)
def update_recurring(recurring_id: int, data: RecurringPurchaseUpdate, current_user: User = Depends(get_current_user)):
    def query(session: Session):
        recurring = session.exec(
            select(RecurringPurchase).where(
                RecurringPurchase.id == recurring_id,
                RecurringPurchase.user_id == current_user.id
            )
        ).first()
        
        if not recurring:
            raise HTTPException(status_code=404, detail="Recurring purchase not found")
        
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(recurring, field, value)
        
        session.commit()
        session.refresh(recurring)
        
        card = session.get(Card, recurring.card_id)
        bank = session.get(Bank, card.bank_id)
        
        category_name = None
        category_color = None
        if recurring.category_id:
            category = session.get(Category, recurring.category_id)
            if category:
                category_name = category.name
                category_color = category.color
        
        return RecurringPurchaseResponse(
            id=recurring.id,
            card_id=recurring.card_id,
            card_name=card.name,
            bank_name=bank.name,
            category_id=recurring.category_id,
            category_name=category_name,
            category_color=category_color,
            description=recurring.description,
            amount=recurring.amount,
            day_of_month=recurring.day_of_month,
            is_active=recurring.is_active
        )
    
    return execute_with_retry(query)

@router.delete("/{recurring_id}", status_code=204)
def delete_recurring(recurring_id: int, current_user: User = Depends(get_current_user)):
    def query(session: Session):
        recurring = session.exec(
            select(RecurringPurchase).where(
                RecurringPurchase.id == recurring_id,
                RecurringPurchase.user_id == current_user.id
            )
        ).first()
        
        if not recurring:
            raise HTTPException(status_code=404, detail="Recurring purchase not found")
        
        session.delete(recurring)
        session.commit()
        return None
    
    return execute_with_retry(query)

@router.post("/{recurring_id}/insert", response_model=dict)
def insert_recurring_as_transaction(recurring_id: int, current_user: User = Depends(get_current_user)):
    """Insere a compra recorrente como uma transação no mês atual"""
    from app.models import Transaction
    
    def query(session: Session):
        recurring = session.exec(
            select(RecurringPurchase).where(
                RecurringPurchase.id == recurring_id,
                RecurringPurchase.user_id == current_user.id
            )
        ).first()
        
        if not recurring:
            raise HTTPException(status_code=404, detail="Recurring purchase not found")
        
        card = session.get(Card, recurring.card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        today = date.today()
        purchase_day = min(recurring.day_of_month, 28)
        purchase_date = date(today.year, today.month, purchase_day)
        
        # Calcular data da fatura (mesma lógica das compras normais)
        if card.type == "credit" and card.due_day:
            due_day = card.due_day
            
            # Determinar o mês da fatura
            first_due_year = today.year
            first_due_month = today.month
            
            # Se o dia da compra já passou do vencimento, vai pra próxima fatura
            if purchase_day > due_day:
                first_due_month += 1
                if first_due_month > 12:
                    first_due_month = 1
                    first_due_year += 1
            
            transaction_date = date(first_due_year, first_due_month, due_day)
        else:
            # Cartão débito: usa a data da compra
            transaction_date = purchase_date
        
        # Criar a transação
        transaction = Transaction(
            card_id=recurring.card_id,
            amount=recurring.amount,
            description=recurring.description,
            date=transaction_date,
            purchase_date=purchase_date,
            category_id=recurring.category_id,
            created_via=CreatedVia.web
        )
        
        session.add(transaction)
        session.commit()
        
        return {"message": "Compra inserida com sucesso", "transaction_date": str(transaction_date)}
    
    return execute_with_retry(query)

@router.post("/insert-all", response_model=dict)
def insert_all_recurring_as_transactions(current_user: User = Depends(get_current_user)):
    """Insere todas as compras recorrentes ativas como transações no mês atual"""
    from app.models import Transaction
    
    def query(session: Session):
        items = session.exec(
            select(RecurringPurchase).where(
                RecurringPurchase.user_id == current_user.id,
                RecurringPurchase.is_active == True
            )
        ).all()
        
        if not items:
            return {"message": "Nenhuma compra recorrente ativa", "count": 0}
        
        today = date.today()
        count = 0
        
        for recurring in items:
            card = session.get(Card, recurring.card_id)
            if not card:
                continue
            
            purchase_day = min(recurring.day_of_month, 28)
            purchase_date = date(today.year, today.month, purchase_day)
            
            if card.type == "credit" and card.due_day:
                due_day = card.due_day
                first_due_year = today.year
                first_due_month = today.month
                
                if purchase_day > due_day:
                    first_due_month += 1
                    if first_due_month > 12:
                        first_due_month = 1
                        first_due_year += 1
                
                transaction_date = date(first_due_year, first_due_month, due_day)
            else:
                transaction_date = purchase_date
            
            transaction = Transaction(
                card_id=recurring.card_id,
                amount=recurring.amount,
                description=recurring.description,
                date=transaction_date,
                purchase_date=purchase_date,
                category_id=recurring.category_id,
                created_via=CreatedVia.web
            )
            
            session.add(transaction)
            count += 1
        
        session.commit()
        return {"message": f"{count} compras inseridas com sucesso", "count": count}
    
    return execute_with_retry(query)
