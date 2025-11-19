from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from app.database import get_session
from app.schemas import CardResponse, CardUpdate
from app import crud

router = APIRouter(prefix="/api/cards", tags=["cards"])

@router.get("/", response_model=List[CardResponse])
def list_cards(bank_id: Optional[int] = Query(None), session: Session = Depends(get_session)):
    cards = crud.get_cards(session, bank_id)
    return [
        CardResponse(
            id=card.id,
            bank_id=card.bank_id,
            name=card.name,
            type=card.type,
            limit_amount=card.limit_amount,
            due_day=card.due_day
        )
        for card in cards
    ]

@router.put("/{card_id}", response_model=CardResponse)
def update_card(card_id: int, card_update: CardUpdate, session: Session = Depends(get_session)):
    card = crud.update_card(session, card_id, card_update)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return CardResponse(
        id=card.id,
        bank_id=card.bank_id,
        name=card.name,
        type=card.type,
        limit_amount=card.limit_amount,
        due_day=card.due_day
    )

@router.delete("/{card_id}")
def delete_card(card_id: int, session: Session = Depends(get_session)):
    if not crud.delete_card(session, card_id):
        raise HTTPException(status_code=404, detail="Card not found")
    return {"message": "Card deleted successfully"}