from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.schemas import TransferCreate
from app import crud

router = APIRouter(prefix="/api/transfers", tags=["transfers"])

@router.post("/", status_code=201)
def create_transfer(transfer: TransferCreate, session: Session = Depends(get_session)):
    if transfer.from_bank_id == transfer.to_bank_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same bank")
    
    if not crud.create_transfer(session, transfer):
        raise HTTPException(status_code=400, detail="Transfer failed - check if banks exist and have cards")
    
    return {"message": "Transfer completed successfully"}