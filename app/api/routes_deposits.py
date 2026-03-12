from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Bank, Deposit, User
from app import crud
from app.auth import get_current_user
from app.schemas import DepositCreate, DepositResponse
from datetime import date
from typing import List, Optional

router = APIRouter(prefix="/api/deposits", tags=["deposits"])

@router.post("/", response_model=DepositResponse)
def create_deposit(deposit: DepositCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Verificar se o banco existe e pertence ao usuário
    bank = session.exec(select(Bank).where(Bank.id == deposit.bank_id, Bank.user_id == current_user.id)).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banco não encontrado")
    
    db_deposit = crud.create_deposit(session, deposit)
    
    return DepositResponse(
        id=db_deposit.id,
        bank_id=db_deposit.bank_id,
        bank_name=bank.name,
        amount=db_deposit.amount,
        description=db_deposit.description,
        date=db_deposit.date,
        created_via=db_deposit.created_via
    )

@router.get("/", response_model=List[DepositResponse])
def get_deposits(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    bank_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Deposit).join(Bank).where(Bank.user_id == current_user.id)
    
    if bank_id:
        query = query.where(Deposit.bank_id == bank_id)
    if date_from:
        query = query.where(Deposit.date >= date_from)
    if date_to:
        query = query.where(Deposit.date <= date_to)
    
    results = session.exec(query).all()
    
    response = []
    for d in results:
        bank = session.get(Bank, d.bank_id)
        response.append(DepositResponse(
            id=d.id,
            bank_id=d.bank_id,
            bank_name=bank.name if bank else "N/A",
            amount=d.amount,
            description=d.description,
            date=d.date,
            created_via=d.created_via
        ))
    
    return sorted(response, key=lambda x: x.date, reverse=True)

@router.delete("/{deposit_id}")
def delete_deposit(deposit_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Verificar se o depósito existe e pertence ao usuário (através do banco)
    deposit = session.exec(
        select(Deposit).join(Bank)
        .where(Deposit.id == deposit_id, Bank.user_id == current_user.id)
    ).first()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Depósito não encontrado")
    
    if crud.delete_deposit(session, deposit_id):
        return {"message": "Depósito excluído com sucesso"}
    
    raise HTTPException(status_code=500, detail="Erro ao excluir depósito")