from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.database import get_session
from app.schemas import TransactionCreate, TransactionResponse
from app import crud
from app.models import Card, Bank

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionResponse, status_code=201)
def create_transaction(transaction: TransactionCreate, session: Session = Depends(get_session)):
    # Verificar se o cartão existe
    card = session.get(Card, transaction.card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    db_transaction = crud.create_transaction(session, transaction)
    
    transfer_to_bank_name = None
    if db_transaction.transfer_to_bank_id:
        transfer_bank = session.get(Bank, db_transaction.transfer_to_bank_id)
        transfer_to_bank_name = transfer_bank.name if transfer_bank else None
    
    return TransactionResponse(
        id=db_transaction.id,
        card_id=db_transaction.card_id,
        amount=db_transaction.amount,
        type=db_transaction.type,
        description=db_transaction.description,
        date=db_transaction.date,
        purchase_date=db_transaction.purchase_date,
        is_paid=db_transaction.is_paid,
        card_name=card.name,
        card_type=card.type,
        bank_name=card.bank.name,
        transfer_to_bank_name=transfer_to_bank_name
    )

@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    bank_id: Optional[int] = Query(None),
    card_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    transactions = crud.get_transactions(session, bank_id, card_id, date_from, date_to, status)
    
    result = []
    for transaction in transactions:
        card = session.get(Card, transaction.card_id)
        bank = session.get(Bank, card.bank_id)
        
        transfer_to_bank_name = None
        if transaction.transfer_to_bank_id:
            transfer_bank = session.get(Bank, transaction.transfer_to_bank_id)
            transfer_to_bank_name = transfer_bank.name if transfer_bank else None
        
        result.append(TransactionResponse(
            id=transaction.id,
            card_id=transaction.card_id,
            amount=transaction.amount,
            type=transaction.type,
            description=transaction.description,
            date=transaction.date,
            purchase_date=transaction.purchase_date,
            is_paid=transaction.is_paid,
            card_name=card.name,
            card_type=card.type,
            bank_name=bank.name,
            transfer_to_bank_name=transfer_to_bank_name
        ))
    
    return result

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: int, transaction_update: TransactionCreate, session: Session = Depends(get_session)):
    updated_transaction = crud.update_transaction(session, transaction_id, transaction_update)
    if not updated_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    card = session.get(Card, updated_transaction.card_id)
    transfer_to_bank_name = None
    if updated_transaction.transfer_to_bank_id:
        transfer_bank = session.get(Bank, updated_transaction.transfer_to_bank_id)
        transfer_to_bank_name = transfer_bank.name if transfer_bank else None
    
    return TransactionResponse(
        id=updated_transaction.id,
        card_id=updated_transaction.card_id,
        amount=updated_transaction.amount,
        type=updated_transaction.type,
        description=updated_transaction.description,
        date=updated_transaction.date,
        is_paid=updated_transaction.is_paid,
        card_name=card.name,
        card_type=card.type,
        bank_name=card.bank.name,
        transfer_to_bank_name=transfer_to_bank_name
    )

@router.patch("/{transaction_id}/toggle-payment", response_model=TransactionResponse)
def toggle_transaction_payment(transaction_id: int, session: Session = Depends(get_session)):
    updated_transaction = crud.toggle_transaction_payment(session, transaction_id)
    if not updated_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    card = session.get(Card, updated_transaction.card_id)
    transfer_to_bank_name = None
    if updated_transaction.transfer_to_bank_id:
        transfer_bank = session.get(Bank, updated_transaction.transfer_to_bank_id)
        transfer_to_bank_name = transfer_bank.name if transfer_bank else None
    
    return TransactionResponse(
        id=updated_transaction.id,
        card_id=updated_transaction.card_id,
        amount=updated_transaction.amount,
        type=updated_transaction.type,
        description=updated_transaction.description,
        date=updated_transaction.date,
        is_paid=updated_transaction.is_paid,
        card_name=card.name,
        card_type=card.type,
        bank_name=card.bank.name,
        transfer_to_bank_name=transfer_to_bank_name
    )

class BulkUpdateRequest(BaseModel):
    transaction_ids: List[int]
    is_paid: bool

@router.patch("/bulk-update-status", response_model=List[TransactionResponse])
def bulk_update_transaction_status(
    request: BulkUpdateRequest,
    session: Session = Depends(get_session)
):
    updated_transactions = crud.bulk_update_transaction_status(session, request.transaction_ids, request.is_paid)
    if not updated_transactions:
        raise HTTPException(status_code=404, detail="No transactions found")
    
    result = []
    for transaction in updated_transactions:
        card = session.get(Card, transaction.card_id)
        transfer_to_bank_name = None
        if transaction.transfer_to_bank_id:
            transfer_bank = session.get(Bank, transaction.transfer_to_bank_id)
            transfer_to_bank_name = transfer_bank.name if transfer_bank else None
        
        result.append(TransactionResponse(
            id=transaction.id,
            card_id=transaction.card_id,
            amount=transaction.amount,
            type=transaction.type,
            description=transaction.description,
            date=transaction.date,
            is_paid=transaction.is_paid,
            card_name=card.name,
            card_type=card.type,
            bank_name=card.bank.name,
            transfer_to_bank_name=transfer_to_bank_name
        ))
    
    return result

@router.patch("/mark-previous-as-paid", response_model=dict)
def mark_previous_transactions_as_paid(session: Session = Depends(get_session)):
    from datetime import date
    today = date.today()
    updated_count = crud.mark_previous_transactions_as_paid(session, today)
    return {"message": f"{updated_count} transações marcadas como pagas", "count": updated_count}

@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, session: Session = Depends(get_session)):
    transaction = crud.get_transaction(session, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    crud.delete_transaction(session, transaction_id)
    return None