from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from app.database import get_session
from app.schemas import CardResponse, CardUpdate
from app import crud
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/cards", tags=["cards"])

@router.get("/", response_model=List[CardResponse])
def list_cards(bank_id: Optional[int] = Query(None), session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    cards = crud.get_cards(session, current_user.id, bank_id)
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
def update_card(card_id: int, card_update: CardUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    card = crud.update_card(session, card_id, card_update, current_user.id)
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
def delete_card(card_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if not crud.delete_card(session, card_id, current_user.id):
        raise HTTPException(status_code=404, detail="Card not found")
    return {"message": "Card deleted successfully"}