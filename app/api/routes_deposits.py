from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Bank, Deposit, User, IncomeType, PaymentMethod, IncomeCategory
from app import crud
from app.auth import get_current_user
from app.schemas import DepositCreate, DepositUpdate, DepositResponse, IncomeTypeResponse, PaymentMethodResponse, IncomeCategoryCreate, IncomeCategoryResponse
from datetime import date
from typing import List, Optional

router = APIRouter(prefix="/api/deposits", tags=["deposits"])


def _build_deposit_response(session: Session, d: Deposit) -> DepositResponse:
    bank = session.get(Bank, d.bank_id) if d.bank_id else None
    income_type = session.get(IncomeType, d.type_id) if d.type_id else None
    payment_method = session.get(PaymentMethod, d.payment_method_id) if d.payment_method_id else None
    income_cat = session.get(IncomeCategory, d.income_category_id) if d.income_category_id else None

    return DepositResponse(
        id=d.id,
        user_id=d.user_id,
        bank_id=d.bank_id,
        bank_name=bank.name if bank else None,
        amount=d.amount,
        description=d.description,
        type_id=d.type_id,
        type_name=income_type.name if income_type else None,
        payment_method_id=d.payment_method_id,
        payment_method_name=payment_method.name if payment_method else None,
        income_category_id=d.income_category_id,
        income_category_name=income_cat.name if income_cat else None,
        income_category_color=income_cat.color if income_cat else None,
        date=d.date,
        source=d.source,
    )


@router.post("", response_model=DepositResponse)
def create_deposit(
    deposit: DepositCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Validar amount
    if deposit.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")

    # Validar type_id
    income_type = session.get(IncomeType, deposit.type_id)
    if not income_type:
        raise HTTPException(status_code=400, detail="Tipo de entrada inválido")

    # Validar payment_method_id
    pm = session.get(PaymentMethod, deposit.payment_method_id)
    if not pm:
        raise HTTPException(status_code=400, detail="Forma de pagamento inválida")

    # Validar bank_id
    bank = session.exec(select(Bank).where(Bank.id == deposit.bank_id, Bank.user_id == current_user.id)).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Banco não encontrado")

    # Resolver income_category
    if deposit.income_category_id:
        cat = session.exec(
            select(IncomeCategory).where(
                IncomeCategory.id == deposit.income_category_id,
                IncomeCategory.user_id == current_user.id,
            )
        ).first()
        if not cat:
            raise HTTPException(status_code=400, detail="Categoria de entrada não encontrada")
    elif deposit.income_category_name and deposit.income_category_name.strip():
        cat = crud.find_or_create_income_category(session, deposit.income_category_name, current_user.id)
        deposit.income_category_id = cat.id

    db_deposit = crud.create_deposit(session, deposit, current_user.id, deposit.add_to_balance)
    return _build_deposit_response(session, db_deposit)


@router.get("", response_model=List[DepositResponse])
def get_deposits(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    bank_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    payment_method_id: Optional[int] = Query(None),
    income_category_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Deposit).where(Deposit.user_id == current_user.id)

    if bank_id:
        query = query.where(Deposit.bank_id == bank_id)
    if type_id:
        query = query.where(Deposit.type_id == type_id)
    if payment_method_id:
        query = query.where(Deposit.payment_method_id == payment_method_id)
    if income_category_id:
        query = query.where(Deposit.income_category_id == income_category_id)
    if date_from:
        query = query.where(Deposit.date >= date_from)
    if date_to:
        query = query.where(Deposit.date <= date_to)

    query = query.order_by(Deposit.date.desc())
    results = session.exec(query).all()

    return [_build_deposit_response(session, d) for d in results]


@router.put("/{deposit_id}", response_model=DepositResponse)
def update_deposit(
    deposit_id: int,
    data: DepositUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    deposit = session.exec(
        select(Deposit).where(Deposit.id == deposit_id, Deposit.user_id == current_user.id)
    ).first()
    if not deposit:
        raise HTTPException(status_code=404, detail="Depósito não encontrado")

    old_amount = deposit.amount
    old_bank_id = deposit.bank_id

    if data.bank_id is not None:
        bank = session.exec(select(Bank).where(Bank.id == data.bank_id, Bank.user_id == current_user.id)).first()
        if not bank:
            raise HTTPException(status_code=404, detail="Banco não encontrado")
        deposit.bank_id = data.bank_id
    if data.amount is not None:
        if data.amount <= 0:
            raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
        deposit.amount = data.amount
    if data.description is not None:
        deposit.description = data.description
    if data.type_id is not None:
        income_type = session.get(IncomeType, data.type_id)
        if not income_type:
            raise HTTPException(status_code=400, detail="Tipo de entrada inválido")
        deposit.type_id = data.type_id
    if data.payment_method_id is not None:
        pm = session.get(PaymentMethod, data.payment_method_id)
        if not pm:
            raise HTTPException(status_code=400, detail="Forma de pagamento inválida")
        deposit.payment_method_id = data.payment_method_id
    if data.income_category_id is not None:
        if data.income_category_id != 0:
            cat = session.exec(
                select(IncomeCategory).where(
                    IncomeCategory.id == data.income_category_id,
                    IncomeCategory.user_id == current_user.id,
                )
            ).first()
            if not cat:
                raise HTTPException(status_code=400, detail="Categoria de entrada não encontrada")
        else:
            deposit.income_category_id = None
        if data.income_category_id != 0:
            deposit.income_category_id = data.income_category_id
    if data.date is not None:
        from datetime import date as date_type
        if isinstance(data.date, str):
            deposit.date = date_type.fromisoformat(data.date)
        else:
            deposit.date = data.date

    # Ajustar saldo do banco se solicitado e o valor mudou
    if data.adjust_balance and data.amount is not None and data.amount != old_amount:
        diff = data.amount - old_amount
        # Se o banco mudou, reverter do antigo e adicionar no novo
        if data.bank_id is not None and data.bank_id != old_bank_id:
            crud.update_bank_balance(session, old_bank_id, old_amount, False)
            crud.update_bank_balance(session, data.bank_id, data.amount, True)
        else:
            crud.update_bank_balance(session, deposit.bank_id, diff, True)
    elif data.adjust_balance and data.bank_id is not None and data.bank_id != old_bank_id:
        # Banco mudou mas valor não: reverter do antigo, adicionar no novo
        crud.update_bank_balance(session, old_bank_id, old_amount, False)
        crud.update_bank_balance(session, data.bank_id, deposit.amount, True)

    session.add(deposit)
    session.commit()
    session.refresh(deposit)
    return _build_deposit_response(session, deposit)


@router.delete("/{deposit_id}")
def delete_deposit(
    deposit_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    deposit = session.exec(
        select(Deposit).where(Deposit.id == deposit_id, Deposit.user_id == current_user.id)
    ).first()

    if not deposit:
        raise HTTPException(status_code=404, detail="Depósito não encontrado")

    if crud.delete_deposit(session, deposit_id):
        return {"message": "Depósito excluído com sucesso"}

    raise HTTPException(status_code=500, detail="Erro ao excluir depósito")


# ──── INCOME TYPES ────
@router.get("/income-types", response_model=List[IncomeTypeResponse])
def list_income_types(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return crud.get_income_types(session)


# ──── PAYMENT METHODS ────
@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
def list_payment_methods(session: Session = Depends(get_session), _: User = Depends(get_current_user)):
    return crud.get_payment_methods(session)


# ──── INCOME CATEGORIES ────
@router.get("/income-categories", response_model=List[IncomeCategoryResponse])
def list_income_categories(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return crud.get_income_categories(session, current_user.id)


@router.post("/income-categories", response_model=IncomeCategoryResponse, status_code=201)
def create_income_category(
    category: IncomeCategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return crud.create_income_category(session, category, current_user.id)


@router.put("/income-categories/{category_id}", response_model=IncomeCategoryResponse)
def update_income_category(
    category_id: int,
    category: IncomeCategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    updated = crud.update_income_category(session, category_id, category, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return updated


@router.delete("/income-categories/{category_id}", status_code=204)
def delete_income_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not crud.delete_income_category(session, category_id, current_user.id):
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return None
