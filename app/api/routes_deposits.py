from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Bank, Card, Transaction, TransactionType
from pydantic import BaseModel
from datetime import date
from typing import List

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
def create_deposit(deposit: DepositCreate, session: Session = Depends(get_session)):
    # Verificar se o banco existe
    bank = session.get(Bank, deposit.bank_id)
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
    
    return DepositResponse(
        id=transaction.id,
        bank_name=bank.name,
        amount=transaction.amount,
        description=transaction.description,
        date=transaction.date
    )

@router.get("/", response_model=List[DepositResponse])
def get_deposits(session: Session = Depends(get_session)):
    query = select(Transaction, Card, Bank).select_from(Transaction).join(Card).join(Bank).where(Transaction.type == TransactionType.deposit)
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