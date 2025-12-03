from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.db_utils import execute_with_retry
from app.schemas import TransactionCreate, TransactionResponse
from app import crud
from app.models import Card, Bank, Category, User
from app.auth import get_current_user

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionResponse, status_code=201)
def create_transaction(transaction: TransactionCreate, current_user: User = Depends(get_current_user)):
    def create_transaction_query(session):
        card = session.get(Card, transaction.card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        db_transaction = crud.create_transaction(session, transaction)
        
        transfer_to_bank_name = None
        if db_transaction.transfer_to_bank_id:
            transfer_bank = session.get(Bank, db_transaction.transfer_to_bank_id)
            transfer_to_bank_name = transfer_bank.name if transfer_bank else None
        
        category_name = None
        if db_transaction.category_id:
            category = session.get(Category, db_transaction.category_id)
            category_name = category.name if category else None
        
        return TransactionResponse(
            id=db_transaction.id,
            card_id=db_transaction.card_id,
            amount=db_transaction.amount,
            type=db_transaction.type,
            description=db_transaction.description,
            date=db_transaction.date,
            purchase_date=db_transaction.purchase_date,
            is_paid=db_transaction.is_paid,
            category_id=db_transaction.category_id,
            category_name=category_name,
            group_id=db_transaction.group_id,
            installment_number=db_transaction.installment_number,
            total_installments=db_transaction.total_installments,
            created_via=db_transaction.created_via,
            card_name=card.name,
            card_type=card.type,
            bank_name=card.bank.name,
            transfer_to_bank_name=transfer_to_bank_name
        )
    
    return execute_with_retry(create_transaction_query)

@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    bank_id: Optional[int] = Query(None),
    card_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    created_via: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    def get_transactions_query(session):
        transactions = crud.get_transactions(session, bank_id, card_id, date_from, date_to, status, current_user.id, created_via)
        
        result = []
        for transaction in transactions:
            card = session.get(Card, transaction.card_id)
            bank = session.get(Bank, card.bank_id)
            
            transfer_to_bank_name = None
            if transaction.transfer_to_bank_id:
                transfer_bank = session.get(Bank, transaction.transfer_to_bank_id)
                transfer_to_bank_name = transfer_bank.name if transfer_bank else None
            
            category_name = None
            if transaction.category_id:
                category = session.get(Category, transaction.category_id)
                category_name = category.name if category else None
            
            result.append(TransactionResponse(
                id=transaction.id,
                card_id=transaction.card_id,
                amount=transaction.amount,
                type=transaction.type,
                description=transaction.description,
                date=transaction.date,
                purchase_date=transaction.purchase_date,
                is_paid=transaction.is_paid,
                category_id=transaction.category_id,
                category_name=category_name,
                group_id=transaction.group_id,
                installment_number=transaction.installment_number,
                total_installments=transaction.total_installments,
                created_via=transaction.created_via or 'web',
                card_name=card.name,
                card_type=card.type,
                bank_name=bank.name,
                transfer_to_bank_name=transfer_to_bank_name
            ))
        
        return result
    
    return execute_with_retry(get_transactions_query)

@router.patch("/{transaction_id}/toggle-payment", response_model=TransactionResponse)
def toggle_transaction_payment(transaction_id: int):
    def toggle_payment_query(session):
        updated_transaction = crud.toggle_transaction_payment(session, transaction_id)
        if not updated_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        card = session.get(Card, updated_transaction.card_id)
        transfer_to_bank_name = None
        if updated_transaction.transfer_to_bank_id:
            transfer_bank = session.get(Bank, updated_transaction.transfer_to_bank_id)
            transfer_to_bank_name = transfer_bank.name if transfer_bank else None
        
        category_name = None
        if updated_transaction.category_id:
            category = session.get(Category, updated_transaction.category_id)
            category_name = category.name if category else None
        
        return TransactionResponse(
            id=updated_transaction.id,
            card_id=updated_transaction.card_id,
            amount=updated_transaction.amount,
            type=updated_transaction.type,
            description=updated_transaction.description,
            date=updated_transaction.date,
            purchase_date=updated_transaction.purchase_date,
            is_paid=updated_transaction.is_paid,
            category_id=updated_transaction.category_id,
            category_name=category_name,
            group_id=updated_transaction.group_id,
            installment_number=updated_transaction.installment_number,
            total_installments=updated_transaction.total_installments,
            created_via=updated_transaction.created_via,
            card_name=card.name,
            card_type=card.type,
            bank_name=card.bank.name,
            transfer_to_bank_name=transfer_to_bank_name
        )
    
    return execute_with_retry(toggle_payment_query)

class BulkUpdateRequest(BaseModel):
    transaction_ids: List[int]
    is_paid: bool

@router.patch("/bulk-update-status", response_model=List[TransactionResponse])
def bulk_update_transaction_status(request: BulkUpdateRequest):
    def bulk_update_query(session):
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
                purchase_date=transaction.purchase_date,
                is_paid=transaction.is_paid,
                category_id=transaction.category_id,
                group_id=transaction.group_id,
                installment_number=transaction.installment_number,
                total_installments=transaction.total_installments,
                created_via=transaction.created_via or 'web',
                card_name=card.name,
                card_type=card.type,
                bank_name=card.bank.name,
                transfer_to_bank_name=transfer_to_bank_name
            ))
        
        return result
    
    return execute_with_retry(bulk_update_query)

@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int):
    def delete_transaction_query(session):
        transaction = crud.get_transaction(session, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        crud.delete_transaction(session, transaction_id)
        return None
    
    return execute_with_retry(delete_transaction_query)