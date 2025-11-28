from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Bank, Card, Transaction, TransactionType, User
from app.crud import update_bank_balance
from app.auth import get_current_user
from pydantic import BaseModel
from datetime import date
from typing import List, Optional

router = APIRouter(prefix="/api/deposits", tags=["deposits"])

class DepositCreate(BaseModel):
    bank_id: int
    amount: float
    description: str
    date: date

class DepositResponse(BaseModel):
    id: int
    bank_name: str
    amount: float
    description: str
    date: date

@router.post("/", response_model=DepositResponse)
def create_deposit(deposit: DepositCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Verificar se o banco existe e pertence ao usuário
    bank = session.exec(select(Bank).where(Bank.id == deposit.bank_id, Bank.user_id == current_user.id)).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banco não encontrado")
    
    # Buscar o primeiro cartão do banco (ou criar um padrão)
    card = session.exec(select(Card).where(Card.bank_id == deposit.bank_id)).first()
    if not card:
        # Criar cartão padrão para depósitos
        card = Card(
            bank_id=deposit.bank_id,
            name=f"{bank.name} - Depósitos",
            type="debit"
        )
        session.add(card)
        session.commit()
        session.refresh(card)
    
    # Criar transação de depósito
    transaction = Transaction(
        card_id=card.id,
        amount=deposit.amount,
        type=TransactionType.deposit,
        description=deposit.description,
        date=deposit.date,
        is_paid=True
    )
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    # Atualizar saldo do banco
    update_bank_balance(session, deposit.bank_id, deposit.amount, True)
    
    return DepositResponse(
        id=transaction.id,
        bank_name=bank.name,
        amount=transaction.amount,
        description=transaction.description,
        date=transaction.date
    )

@router.get("/", response_model=List[DepositResponse])
def get_deposits(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    bank_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Transaction, Card, Bank).select_from(Transaction).join(Card).join(Bank).where(Transaction.type == TransactionType.deposit, Bank.user_id == current_user.id)
    
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    if bank_id:
        query = query.where(Bank.id == bank_id)
    
    results = session.exec(query).all()
    
    deposits = []
    for transaction, card, bank in results:
        deposits.append(DepositResponse(
            id=transaction.id,
            bank_name=bank.name,
            amount=transaction.amount,
            description=transaction.description,
            date=transaction.date
        ))
    
    return sorted(deposits, key=lambda x: x.date, reverse=True)

@router.delete("/{deposit_id}")
def delete_deposit(deposit_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Verificar se o depósito existe e pertence ao usuário
    transaction = session.exec(
        select(Transaction).join(Card).join(Bank)
        .where(Transaction.id == deposit_id, Transaction.type == TransactionType.deposit, Bank.user_id == current_user.id)
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Depósito não encontrado")
    
    # Buscar banco para reverter saldo
    card = session.get(Card, transaction.card_id)
    if card:
        update_bank_balance(session, card.bank_id, transaction.amount, False)
    
    session.delete(transaction)
    session.commit()
    return {"message": "Depósito excluído com sucesso"}