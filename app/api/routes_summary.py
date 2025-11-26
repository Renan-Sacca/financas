from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from app.database import get_session
from app.schemas import Summary, BankSummary
from app import crud
from app.models import Transaction, Card, Bank
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/summary", tags=["summary"])

@router.get("/", response_model=Summary)
def get_summary(session: Session = Depends(get_session)):
    banks = crud.get_banks(session)
    bank_summaries = []
    total_balance = 0.0
    
    for bank in banks:
        bank_summaries.append(BankSummary(
            bank_id=bank.id,
            bank_name=bank.name,
            balance=bank.current_balance
        ))
        total_balance += bank.current_balance
    
    return Summary(
        banks=bank_summaries,
        total_balance=total_balance
    )

@router.get("/monthly-expenses")
def get_monthly_expenses(
    bank_id: Optional[int] = Query(None),
    card_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    # Query base para transações de despesa
    query = select(Transaction).where(Transaction.type == "expense")
    
    # Aplicar filtros
    if card_id:
        query = query.where(Transaction.card_id == card_id)
    elif bank_id:
        query = query.join(Card).where(Card.bank_id == bank_id)
    
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    
    transactions = session.exec(query).all()
    
    # Filtrar por ano se especificado
    if year:
        transactions = [t for t in transactions if t.date.year == year]
    
    # Filtrar por mês se especificado
    if month:
        transactions = [t for t in transactions if t.date.month == month]
    
    # Se mês específico foi selecionado, agrupar por dia
    if month and year:
        daily_data = {}
        for transaction in transactions:
            day_key = transaction.date.strftime("%Y-%m-%d")
            day_name = transaction.date.strftime("%d/%m")
            
            if day_key not in daily_data:
                daily_data[day_key] = {
                    "month": day_name,
                    "total": 0.0
                }
            
            daily_data[day_key]["total"] += transaction.amount
        
        # Ordenar por data e retornar
        result = sorted(daily_data.values(), key=lambda x: datetime.strptime(x["month"] + f"/{year}", "%d/%m/%Y"))
        return result
    else:
        # Agrupar por mês
        monthly_data = {}
        for transaction in transactions:
            month_key = transaction.date.strftime("%Y-%m")
            month_name = transaction.date.strftime("%b/%Y")
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_name,
                    "total": 0.0
                }
            
            monthly_data[month_key]["total"] += transaction.amount
        
        # Ordenar por data e retornar
        result = sorted(monthly_data.values(), key=lambda x: datetime.strptime(x["month"], "%b/%Y"))
        return result

@router.get("/card-expenses")
def get_card_expenses(
    bank_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    # Query base para transações de despesa
    query = select(Transaction, Card).join(Card).where(Transaction.type == "expense")
    
    # Aplicar filtros
    if bank_id:
        query = query.where(Card.bank_id == bank_id)
    
    if date_from:
        query = query.where(Transaction.date >= date_from)
    
    if date_to:
        query = query.where(Transaction.date <= date_to)
    
    results = session.exec(query).all()
    
    # Agrupar por cartão
    card_data = {}
    for transaction, card in results:
        card_name = card.name
        
        if card_name not in card_data:
            card_data[card_name] = 0.0
        
        card_data[card_name] += transaction.amount
    
    # Converter para formato do gráfico
    result = [{
        "card": card_name,
        "total": total
    } for card_name, total in card_data.items()]
    
    return sorted(result, key=lambda x: x["total"], reverse=True)

@router.get("/category-expenses")
def get_category_expenses(
    bank_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    from app.models import Category
    
    # Query base para transações de despesa com categoria
    query = select(Transaction, Category).join(Category, Transaction.category_id == Category.id, isouter=True).where(Transaction.type == "expense")
    
    # Aplicar filtros
    if bank_id:
        query = query.join(Card).where(Card.bank_id == bank_id)
    
    if date_from:
        query = query.where(Transaction.date >= date_from)
    
    if date_to:
        query = query.where(Transaction.date <= date_to)
    
    results = session.exec(query).all()
    
    # Agrupar por categoria
    category_data = {}
    for transaction, category in results:
        category_name = category.name if category else "Sem categoria"
        
        if category_name not in category_data:
            category_data[category_name] = 0.0
        
        category_data[category_name] += transaction.amount
    
    # Converter para formato do gráfico
    result = [{
        "category": category_name,
        "total": total
    } for category_name, total in category_data.items()]
    
    return sorted(result, key=lambda x: x["total"], reverse=True)

@router.get("/credit-limits")
def get_credit_limits(
    bank_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    # Query para cartões de crédito com limite
    query = select(Card, Bank).join(Bank).where(
        Card.type == "credit",
        Card.limit_amount.isnot(None),
        Card.limit_amount > 0
    )
    
    if bank_id:
        query = query.where(Bank.id == bank_id)
    
    cards_with_limits = session.exec(query).all()
    
    result = []
    total_limit_sum = 0
    total_used_sum = 0
    
    for card, bank in cards_with_limits:
        # Calcular valor usado (transações pendentes)
        transactions_query = select(Transaction).where(
            Transaction.card_id == card.id,
            Transaction.type == "expense",
            Transaction.is_paid == False
        )
        
        pending_transactions = session.exec(transactions_query).all()
        used_limit = sum(t.amount for t in pending_transactions)
        available_limit = card.limit_amount - used_limit
        
        result.append({
            "card_name": card.name,
            "bank_name": bank.name,
            "total_limit": card.limit_amount,
            "used_limit": used_limit,
            "available_limit": available_limit
        })
        
        total_limit_sum += card.limit_amount
        total_used_sum += used_limit
    
    # Adicionar totais
    if result:
        result.append({
            "card_name": "TOTAL",
            "bank_name": "",
            "total_limit": total_limit_sum,
            "used_limit": total_used_sum,
            "available_limit": total_limit_sum - total_used_sum
        })
    
    return result