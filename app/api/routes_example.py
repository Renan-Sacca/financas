"""
Exemplo de como usar o novo sistema de conexão MySQL
Este arquivo mostra como implementar rotas com retry automático
"""
from fastapi import APIRouter, HTTPException
from app.db_utils import execute_with_retry
from app.models import Bank, User
from app.schemas import BankResponse
from sqlmodel import select
from typing import List

router = APIRouter(prefix="/api/example", tags=["example"])

@router.get("/banks-with-retry", response_model=List[BankResponse])
def list_banks_with_retry(user_id: int):
    """Exemplo de listagem de bancos com retry automático"""
    
    def get_banks_query(session):
        banks = session.exec(select(Bank).where(Bank.user_id == user_id)).all()
        return [
            BankResponse(
                id=bank.id,
                name=bank.name,
                current_balance=bank.current_balance
            )
            for bank in banks
        ]
    
    try:
        return execute_with_retry(get_banks_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na conexão com banco: {str(e)}")

@router.get("/test-connection")
def test_connection():
    """Endpoint para testar a conexão com o banco"""
    
    def test_query(session):
        # Testa uma query simples
        user_count = len(session.exec(select(User)).all())
        return {"status": "connected", "user_count": user_count}
    
    try:
        result = execute_with_retry(test_query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha na conexão: {str(e)}")