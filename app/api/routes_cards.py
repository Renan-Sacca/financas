from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from app.db_utils import execute_with_retry
from app.schemas import CardResponse, CardUpdate
from app import crud
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/cards", tags=["cards"])

@router.get("/", response_model=List[CardResponse])
def list_cards(bank_id: Optional[int] = Query(None), current_user: User = Depends(get_current_user)):
    def get_cards_query(session):
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
    
    return execute_with_retry(get_cards_query)

@router.put("/{card_id}", response_model=CardResponse)
def update_card(card_id: int, card_update: CardUpdate, current_user: User = Depends(get_current_user)):
    def update_card_query(session):
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
    
    return execute_with_retry(update_card_query)

@router.delete("/{card_id}")
def delete_card(card_id: int, current_user: User = Depends(get_current_user)):
    def delete_card_query(session):
        if not crud.delete_card(session, card_id, current_user.id):
            raise HTTPException(status_code=404, detail="Card not found")
        return {"message": "Card deleted successfully"}
    
    return execute_with_retry(delete_card_query)