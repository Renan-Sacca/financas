from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.database import get_session
from app.auth import get_current_user
from app.models import User, PendingBankItem, Bank, IncomeCategory, Deposit, IncomeType, PaymentMethod
from app.schemas import PendingBankItemResponse, PendingBankItemUpdate, BankBatchSummary
import uuid
from datetime import datetime, date

router = APIRouter(prefix="/api/pending-bank", tags=["Pending Bank Statements"])

# Tipo padrão para depósitos criados via extrato
DEFAULT_INCOME_TYPE_ID = 1
DEFAULT_PAYMENT_METHOD_ID = 1


def _build_response(db: Session, item: PendingBankItem) -> PendingBankItemResponse:
    bank = db.get(Bank, item.bank_id) if item.bank_id else None
    cat = db.get(IncomeCategory, item.category_id) if item.category_id else None
    return PendingBankItemResponse(
        id=item.id,
        batch_id=item.batch_id,
        bank_id=item.bank_id,
        bank_name=bank.name if bank else None,
        descricao=item.descricao,
        valor=item.valor,
        data=item.data,
        tipo=item.tipo,
        status=item.status,
        category_id=item.category_id,
        category_name=cat.name if cat else None,
        filename=item.filename,
        created_at=item.created_at,
    )


@router.get("/batches", response_model=List[BankBatchSummary])
def list_batches(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    items = db.exec(
        select(PendingBankItem).where(
            PendingBankItem.user_id == current_user.id,
        ).order_by(PendingBankItem.created_at.desc())
    ).all()

    batches: dict[str, dict] = {}
    for item in items:
        bid = item.batch_id
        if bid not in batches:
            bank = db.get(Bank, item.bank_id) if item.bank_id else None
            batches[bid] = {
                "batch_id": bid,
                "filename": item.filename,
                "bank_id": item.bank_id,
                "bank_name": bank.name if bank else None,
                "total_items": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "confirmed": 0,
                "created_at": item.created_at,
            }
        batches[bid]["total_items"] += 1
        display_status = "approved" if item.status == "confirmed" else item.status
        batches[bid][display_status] += 1

    return [BankBatchSummary(**v) for v in batches.values()]


@router.get("/batch/{batch_id}", response_model=List[PendingBankItemResponse])
def list_batch(
    batch_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    items = db.exec(
        select(PendingBankItem).where(
            PendingBankItem.batch_id == batch_id,
            PendingBankItem.user_id == current_user.id,
        ).order_by(PendingBankItem.data)
    ).all()
    if not items:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    return [_build_response(db, i) for i in items]


@router.put("/{item_id}", response_model=PendingBankItemResponse)
def update_item(
    item_id: int,
    data: PendingBankItemUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = db.exec(
        select(PendingBankItem).where(
            PendingBankItem.id == item_id,
            PendingBankItem.user_id == current_user.id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    if data.descricao is not None:
        item.descricao = data.descricao
    if data.valor is not None:
        item.valor = data.valor
    if data.data is not None:
        item.data = data.data
    if data.bank_id is not None:
        item.bank_id = data.bank_id
    if data.category_id is not None:
        item.category_id = data.category_id
    if data.status is not None:
        if data.status not in ("pending", "approved", "rejected"):
            raise HTTPException(status_code=400, detail="Status inválido")
        item.status = data.status

    db.add(item)
    db.commit()
    db.refresh(item)
    return _build_response(db, item)


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = db.exec(
        select(PendingBankItem).where(
            PendingBankItem.id == item_id,
            PendingBankItem.user_id == current_user.id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    db.delete(item)
    db.commit()


@router.patch("/{item_id}/status")
def set_item_status(
    item_id: int,
    status: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if status not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=400, detail="Status inválido")
    item = db.exec(
        select(PendingBankItem).where(
            PendingBankItem.id == item_id,
            PendingBankItem.user_id == current_user.id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    item.status = status
    db.add(item)
    db.commit()
    return {"id": item_id, "status": status}


@router.post("/batch/{batch_id}/confirm")
def confirm_batch(
    batch_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    items = db.exec(
        select(PendingBankItem).where(
            PendingBankItem.batch_id == batch_id,
            PendingBankItem.user_id == current_user.id,
            PendingBankItem.status == "approved",
        )
    ).all()

    if not items:
        raise HTTPException(status_code=400, detail="Nenhum item aprovado pendente de confirmação neste lote")

    # Garante que existem tipo e método de pagamento padrão
    income_type = db.get(IncomeType, DEFAULT_INCOME_TYPE_ID)
    payment_method = db.get(PaymentMethod, DEFAULT_PAYMENT_METHOD_ID)
    if not income_type or not payment_method:
        raise HTTPException(status_code=500, detail="Tipo de renda ou método de pagamento padrão não encontrado")

    created = 0
    for item in items:
        db.add(Deposit(
            user_id=current_user.id,
            bank_id=item.bank_id,
            amount=item.valor,
            description=item.descricao,
            type_id=DEFAULT_INCOME_TYPE_ID,
            payment_method_id=DEFAULT_PAYMENT_METHOD_ID,
            income_category_id=item.category_id,
            date=item.data,
            source="extrato",
        ))
        # Ajusta saldo do banco (positivo = entrada, negativo = saída)
        if item.bank_id:
            bank = db.get(Bank, item.bank_id)
            if bank:
                bank.current_balance += item.valor
                db.add(bank)
        item.status = "confirmed"
        db.add(item)
        created += 1

    db.commit()
    return {"message": f"{created} depósito(s) criado(s) com sucesso", "created": created}
