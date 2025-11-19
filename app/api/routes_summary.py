from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database import get_session
from app.schemas import Summary, BankSummary
from app import crud

router = APIRouter(prefix="/api/summary", tags=["summary"])

@router.get("/", response_model=Summary)
def get_summary(session: Session = Depends(get_session)):
    banks = crud.get_banks(session)
    bank_summaries = []
    total_balance = 0.0
    
    for bank in banks:
        balance = crud.calculate_bank_balance(session, bank.id)
        bank_summaries.append(BankSummary(
            bank_id=bank.id,
            bank_name=bank.name,
            balance=balance
        ))
        total_balance += balance
    
    return Summary(
        banks=bank_summaries,
        total_balance=total_balance
    )