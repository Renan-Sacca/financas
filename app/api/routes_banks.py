from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.database import get_session
from app.schemas import BankCreate, BankUpdate, BankResponse, CardCreate, CardResponse
from app import crud

router = APIRouter(prefix="/api/banks", tags=["banks"])

@router.get("/", response_model=List[BankResponse])
def list_banks(session: Session = Depends(get_session)):
    banks = crud.get_banks(session)
    return [
        BankResponse(
            id=bank.id,
            name=bank.name,
            current_balance=bank.current_balance
        )
        for bank in banks
    ]

@router.post("/", response_model=BankResponse, status_code=201)
def create_bank(bank: BankCreate, session: Session = Depends(get_session)):
    try:
        db_bank = crud.create_bank(session, bank)
        return BankResponse(
            id=db_bank.id,
            name=db_bank.name,
            current_balance=db_bank.current_balance
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Bank name already exists")

@router.get("/{bank_id}", response_model=BankResponse)
def get_bank(bank_id: int, session: Session = Depends(get_session)):
    bank = crud.get_bank(session, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    return BankResponse(
        id=bank.id,
        name=bank.name,
        current_balance=bank.current_balance
    )

@router.put("/{bank_id}", response_model=BankResponse)
def update_bank(bank_id: int, bank_update: BankUpdate, session: Session = Depends(get_session)):
    bank = crud.update_bank(session, bank_id, bank_update)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    return BankResponse(
        id=bank.id,
        name=bank.name,
        current_balance=bank.current_balance
    )

@router.delete("/{bank_id}")
def delete_bank(bank_id: int, session: Session = Depends(get_session)):
    if not crud.delete_bank(session, bank_id):
        raise HTTPException(status_code=404, detail="Bank not found")
    return {"message": "Bank deleted successfully"}

@router.post("/{bank_id}/cards", response_model=CardResponse, status_code=201)
def create_card(bank_id: int, card: CardCreate, session: Session = Depends(get_session)):
    bank = crud.get_bank(session, bank_id)
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    
    db_card = crud.create_card(session, bank_id, card)
    return CardResponse(
        id=db_card.id,
        bank_id=db_card.bank_id,
        name=db_card.name,
        type=db_card.type
    )