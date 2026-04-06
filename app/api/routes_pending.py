from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from app.database import get_session
from app.auth import get_current_user
from app.models import User, PendingStatementItem, Card, Bank, Category, Transaction, CreatedVia
from app.schemas import PendingItemResponse, PendingItemUpdate, BatchSummary
from app.db_utils import execute_with_retry
import uuid
from datetime import datetime, date

router = APIRouter(prefix="/api/pending", tags=["Pending Statements"])


def _build_response(db: Session, item: PendingStatementItem) -> PendingItemResponse:
    card = db.get(Card, item.card_id)
    bank = db.get(Bank, card.bank_id) if card else None
    cat = db.get(Category, item.category_id) if item.category_id else None
    return PendingItemResponse(
        id=item.id,
        batch_id=item.batch_id,
        card_id=item.card_id,
        card_name=card.name if card else None,
        bank_name=bank.name if bank else None,
        descricao=item.descricao,
        valor=item.valor,
        data_compra=item.data_compra,
        tipo=item.tipo,
        status=item.status,
        category_id=item.category_id,
        category_name=cat.name if cat else None,
        filename=item.filename,
        installment_number=item.installment_number,
        total_installments=item.total_installments,
        created_at=item.created_at,
    )


# ── Listar todos os itens pendentes do usuário ────────────────────────────────
@router.get("", response_model=List[PendingItemResponse])
def list_pending(
    status: str = "pending",
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(PendingStatementItem).where(
        PendingStatementItem.user_id == current_user.id,
    )
    if status != "all":
        query = query.where(PendingStatementItem.status == status)
    query = query.order_by(PendingStatementItem.created_at.desc())
    items = db.exec(query).all()
    return [_build_response(db, i) for i in items]


# ── Listar itens de um lote específico ────────────────────────────────────────
@router.get("/batch/{batch_id}", response_model=List[PendingItemResponse])
def list_batch(
    batch_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    items = db.exec(
        select(PendingStatementItem).where(
            PendingStatementItem.batch_id == batch_id,
            PendingStatementItem.user_id == current_user.id,
        ).order_by(PendingStatementItem.data_compra)
    ).all()
    if not items:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    return [_build_response(db, i) for i in items]


# ── Resumo de todos os lotes do usuário ───────────────────────────────────────
@router.get("/batches", response_model=List[BatchSummary])
def list_batches(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    items = db.exec(
        select(PendingStatementItem).where(
            PendingStatementItem.user_id == current_user.id,
        ).order_by(PendingStatementItem.created_at.desc())
    ).all()

    batches: dict[str, dict] = {}
    for item in items:
        bid = item.batch_id
        if bid not in batches:
            card = db.get(Card, item.card_id)
            bank = db.get(Bank, card.bank_id) if card else None
            batches[bid] = {
                "batch_id": bid,
                "filename": item.filename,
                "card_name": card.name if card else None,
                "bank_name": bank.name if bank else None,
                "total_items": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "confirmed": 0,
                "created_at": item.created_at,
            }
        batches[bid]["total_items"] += 1
        # Agrupa "confirmed" junto com "approved" para exibição
        display_status = "approved" if item.status == "confirmed" else item.status
        batches[bid][display_status] += 1

    return [BatchSummary(**v) for v in batches.values()]


# ── Editar item individual ────────────────────────────────────────────────────
@router.put("/{item_id}", response_model=PendingItemResponse)
def update_item(
    item_id: int,
    data: PendingItemUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = db.exec(
        select(PendingStatementItem).where(
            PendingStatementItem.id == item_id,
            PendingStatementItem.user_id == current_user.id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    if data.descricao is not None:
        item.descricao = data.descricao
    if data.valor is not None:
        item.valor = data.valor
    if data.data_compra is not None:
        item.data_compra = data.data_compra
    if data.card_id is not None:
        item.card_id = data.card_id
    if data.category_id is not None:
        item.category_id = data.category_id
    if data.installment_number is not None:
        item.installment_number = data.installment_number
    if data.total_installments is not None:
        item.total_installments = data.total_installments
    if data.status is not None:
        if data.status not in ("pending", "approved", "rejected"):
            raise HTTPException(status_code=400, detail="Status inválido")
        item.status = data.status

    db.add(item)
    db.commit()
    db.refresh(item)
    return _build_response(db, item)


# ── Deletar item ──────────────────────────────────────────────────────────────
@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    item = db.exec(
        select(PendingStatementItem).where(
            PendingStatementItem.id == item_id,
            PendingStatementItem.user_id == current_user.id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    db.delete(item)
    db.commit()


# ── Confirmar lote inteiro (approved → Transaction) ───────────────────────────
@router.post("/batch/{batch_id}/confirm")
def confirm_batch(
    batch_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Busca apenas itens aprovados que ainda NÃO foram confirmados
    items = db.exec(
        select(PendingStatementItem).where(
            PendingStatementItem.batch_id == batch_id,
            PendingStatementItem.user_id == current_user.id,
            PendingStatementItem.status == "approved",
        )
    ).all()

    if not items:
        raise HTTPException(status_code=400, detail="Nenhum item aprovado pendente de confirmação neste lote")

    created = 0
    for item in items:
        card = db.get(Card, item.card_id)
        due_day = (card.due_day or 1) if card else 1

        # Determina se é parcelado
        total = item.total_installments or 1
        current = item.installment_number or 1
        group_id = str(uuid.uuid4()) if total > 1 else None

        # Calcula a data de vencimento da parcela atual
        def calc_due_date(purchase: date, offset_months: int = 0) -> date:
            import calendar
            m = purchase.month + offset_months
            y = purchase.year
            while m > 12:
                m -= 12
                y += 1
            while m < 1:
                m += 12
                y -= 1
            # Se a compra foi depois do dia de vencimento, cai no mês seguinte
            if purchase.day > due_day and offset_months == 0:
                m += 1
                if m > 12:
                    m = 1
                    y += 1
            last_day = calendar.monthrange(y, m)[1]
            return date(y, m, min(due_day, last_day))

        # Parcela base: vencimento da parcela "current"
        # offset = 0 para a parcela atual, -1 para anterior, +1 para próxima
        base_due = calc_due_date(item.data_compra)

        # Gera todas as parcelas (anteriores + atual + futuras)
        for i in range(1, total + 1):
            offset = i - current  # negativo = anterior, 0 = atual, positivo = futura
            import calendar
            m = base_due.month + offset
            y = base_due.year
            while m > 12:
                m -= 12
                y += 1
            while m < 1:
                m += 12
                y -= 1
            last_day = calendar.monthrange(y, m)[1]
            due = date(y, m, min(due_day, last_day))

            # Data de compra estimada para parcelas geradas (mesmo dia, mês ajustado)
            pm = item.data_compra.month + offset
            py = item.data_compra.year
            while pm > 12:
                pm -= 12
                py += 1
            while pm < 1:
                pm += 12
                py += 1
            last_pd = calendar.monthrange(py, pm)[1]
            purchase_d = date(py, pm, min(item.data_compra.day, last_pd))

            db.add(Transaction(
                card_id=item.card_id,
                amount=item.valor,
                description=item.descricao if total == 1 else f"{item.descricao} ({i}/{total})",
                date=due,
                purchase_date=purchase_d,
                category_id=item.category_id,
                group_id=group_id,
                installment_number=i,
                total_installments=total,
                created_via=CreatedVia.bot,
            ))
            created += 1

        item.status = "confirmed"
        db.add(item)

    db.commit()
    return {"message": f"{created} transação(ões) criada(s) com sucesso", "created": created}


# ── Aprovar/rejeitar item individual ─────────────────────────────────────────
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
        select(PendingStatementItem).where(
            PendingStatementItem.id == item_id,
            PendingStatementItem.user_id == current_user.id,
        )
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    item.status = status
    db.add(item)
    db.commit()
    return {"id": item_id, "status": status}
