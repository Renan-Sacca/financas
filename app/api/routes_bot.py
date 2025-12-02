from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models import User, Bank, Card, Transaction, Category
from app.schemas import BankCreate, CardCreateBot, TransactionCreate, BankResponse, CardResponse, TransactionResponse, CategoryCreate, CategoryResponse
from typing import List

router = APIRouter(prefix="/api/bot", tags=["Bot Telegram"])

def get_user_by_telegram_id(telegram_id: int, session: Session = Depends(get_session)) -> User:
    """Busca usuário pelo ID do Telegram"""
    user = session.exec(select(User).where(User.id_telegram == telegram_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado com este ID do Telegram"
        )
    return user

@router.post("/banks/{telegram_id}", response_model=BankResponse)
def create_bank_for_telegram_user(telegram_id: int, bank: BankCreate, session: Session = Depends(get_session)):
    user = get_user_by_telegram_id(telegram_id, session)
    
    db_bank = Bank(
        user_id=user.id,
        name=bank.name,
        current_balance=bank.current_balance or 0.0
    )
    
    session.add(db_bank)
    session.commit()
    session.refresh(db_bank)
    return db_bank

@router.get("/banks/{telegram_id}", response_model=List[BankResponse])
def get_banks_for_telegram_user(telegram_id: int, session: Session = Depends(get_session)):
    user = get_user_by_telegram_id(telegram_id, session)
    banks = session.exec(select(Bank).where(Bank.user_id == user.id)).all()
    return banks

@router.post("/cards/{telegram_id}", response_model=CardResponse)
def create_card_for_telegram_user(telegram_id: int, card: CardCreateBot, session: Session = Depends(get_session)):
    user = get_user_by_telegram_id(telegram_id, session)
    
    # Verificar se o banco pertence ao usuário
    bank = session.exec(select(Bank).where(Bank.id == card.bank_id, Bank.user_id == user.id)).first()
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banco não encontrado ou não pertence ao usuário"
        )
    
    db_card = Card(
        bank_id=card.bank_id,
        name=card.name,
        type=card.type,
        limit_amount=card.limit_amount,
        due_day=card.due_day
    )
    
    session.add(db_card)
    session.commit()
    session.refresh(db_card)
    return db_card

@router.get("/cards/{telegram_id}", response_model=List[CardResponse])
def get_cards_for_telegram_user(telegram_id: int, session: Session = Depends(get_session)):
    user = get_user_by_telegram_id(telegram_id, session)
    
    cards = session.exec(
        select(Card)
        .join(Bank)
        .where(Bank.user_id == user.id)
    ).all()
    return cards

@router.post("/transactions/{telegram_id}")
def create_transaction_for_telegram_user(telegram_id: int, transaction: TransactionCreate, session: Session = Depends(get_session)):
    from datetime import datetime
    import uuid
    
    user = get_user_by_telegram_id(telegram_id, session)
    
    # Verificar se o cartão pertence ao usuário
    card = session.exec(
        select(Card)
        .join(Bank)
        .where(Card.id == transaction.card_id, Bank.user_id == user.id)
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cartão não encontrado ou não pertence ao usuário"
        )
    
    # Se tem parcelas, criar múltiplas transações
    if transaction.total_installments and transaction.total_installments > 1:
        group_id = str(uuid.uuid4())
        installment_amount = transaction.amount / transaction.total_installments
        
        # Usar a data fornecida como purchase_date
        purchase_date = transaction.date
        due_day = card.due_day if card.due_day else 1
        
        year, month, day = purchase_date.year, purchase_date.month, purchase_date.day
        first_due_year = year
        first_due_month = month
        if day > due_day:
            first_due_month += 1
            if first_due_month > 12:
                first_due_month = 1
                first_due_year += 1
        
        transactions = []
        for i in range(transaction.total_installments):
            installment_year = first_due_year
            installment_month = first_due_month + i
            
            while installment_month > 12:
                installment_month -= 12
                installment_year += 1
            
            installment_date = datetime(installment_year, installment_month, due_day).date()
            installment_description = f"{transaction.description} ({i + 1}/{transaction.total_installments})"
            
            db_transaction = Transaction(
                card_id=transaction.card_id,
                amount=installment_amount,
                type=transaction.type,
                description=installment_description,
                date=installment_date,
                purchase_date=purchase_date,
                category_id=transaction.category_id,
                group_id=group_id,
                installment_number=i + 1,
                total_installments=transaction.total_installments,
                transfer_to_bank_id=transaction.transfer_to_bank_id,
                created_via="bot"
            )
            
            session.add(db_transaction)
            transactions.append(db_transaction)
        
        session.commit()
        
        return {
            "message": f"Compra parcelada criada com {transaction.total_installments} parcelas",
            "group_id": group_id,
            "installments": transaction.total_installments,
            "installment_amount": installment_amount,
            "total_amount": transaction.amount
        }
    
    # Transação única - calcular data de vencimento igual às parcelas
    else:
        purchase_date = transaction.date
        due_day = card.due_day if card.due_day else 1
        
        year, month, day = purchase_date.year, purchase_date.month, purchase_date.day
        due_year = year
        due_month = month
        if day > due_day:
            due_month += 1
            if due_month > 12:
                due_month = 1
                due_year += 1
        
        due_date = datetime(due_year, due_month, due_day).date()
        
        db_transaction = Transaction(
            card_id=transaction.card_id,
            amount=transaction.amount,
            type=transaction.type,
            description=transaction.description,
            date=due_date,
            purchase_date=purchase_date,
            category_id=transaction.category_id,
            group_id=transaction.group_id,
            installment_number=transaction.installment_number,
            total_installments=transaction.total_installments,
            transfer_to_bank_id=transaction.transfer_to_bank_id,
            created_via="bot"
        )
        
        session.add(db_transaction)
        session.commit()
        session.refresh(db_transaction)
        
        return TransactionResponse(
            id=db_transaction.id,
            card_id=db_transaction.card_id,
            amount=db_transaction.amount,
            type=db_transaction.type,
            description=db_transaction.description,
            date=db_transaction.date,
            purchase_date=db_transaction.purchase_date,
            is_paid=db_transaction.is_paid,
            category_id=db_transaction.category_id,
            group_id=db_transaction.group_id,
            installment_number=db_transaction.installment_number,
            total_installments=db_transaction.total_installments,
            created_via=db_transaction.created_via,
            card_name=card.name,
            card_type=card.type,
            bank_name=card.bank.name
        )

@router.post("/categories/{telegram_id}", response_model=CategoryResponse)
def create_category_for_telegram_user(telegram_id: int, category: CategoryCreate, session: Session = Depends(get_session)):
    from app import crud
    user = get_user_by_telegram_id(telegram_id, session)
    
    db_category = crud.create_category(session, category, user.id)
    return CategoryResponse(
        id=db_category.id,
        name=db_category.name,
        color=db_category.color
    )

@router.get("/categories/{telegram_id}", response_model=List[CategoryResponse])
def get_categories_for_telegram_user(telegram_id: int, session: Session = Depends(get_session)):
    from app import crud
    user = get_user_by_telegram_id(telegram_id, session)
    categories = crud.get_categories(session, user.id)
    return [
        CategoryResponse(
            id=category.id,
            name=category.name,
            color=category.color
        )
        for category in categories
    ]

@router.get("/deposits/{telegram_id}")
def get_deposits_for_telegram_user(telegram_id: int, session: Session = Depends(get_session)):
    user = get_user_by_telegram_id(telegram_id, session)
    
    # Buscar todas as transações de depósito do usuário
    deposits = session.exec(
        select(Transaction)
        .join(Card)
        .join(Bank)
        .where(Bank.user_id == user.id, Transaction.type == "deposit")
    ).all()
    
    result = []
    for deposit in deposits:
        card = session.get(Card, deposit.card_id)
        bank = session.get(Bank, card.bank_id)
        result.append({
            "id": deposit.id,
            "amount": deposit.amount,
            "description": deposit.description,
            "date": deposit.date,
            "bank_name": bank.name,
            "bank_id": bank.id
        })
    
    return result

@router.post("/deposits/{telegram_id}")
def create_deposit_for_telegram_user(telegram_id: int, bank_id: int, amount: float, description: str, date: str, session: Session = Depends(get_session)):
    from datetime import datetime
    user = get_user_by_telegram_id(telegram_id, session)
    
    # Verificar se o banco pertence ao usuário
    bank = session.exec(select(Bank).where(Bank.id == bank_id, Bank.user_id == user.id)).first()
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banco não encontrado ou não pertence ao usuário"
        )
    
    # Buscar primeiro cartão do banco
    card = session.exec(select(Card).where(Card.bank_id == bank_id)).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum cartão encontrado para este banco"
        )
    
    # Converter string de data para objeto date
    deposit_date = datetime.strptime(date, "%Y-%m-%d").date()
    
    # Criar transação de depósito
    db_transaction = Transaction(
        card_id=card.id,
        amount=amount,
        type="deposit",
        description=description,
        date=deposit_date,
        purchase_date=deposit_date,
        is_paid=True,
        created_via="bot"
    )
    
    session.add(db_transaction)
    
    # Atualizar saldo do banco
    bank.current_balance += amount
    
    session.commit()
    session.refresh(db_transaction)
    
    return {
        "message": "Depósito criado com sucesso",
        "transaction_id": db_transaction.id,
        "amount": amount,
        "new_balance": bank.current_balance
    }

@router.get("/user/{telegram_id}")
def get_user_info_by_telegram_id(telegram_id: int, session: Session = Depends(get_session)):
    user = get_user_by_telegram_id(telegram_id, session)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "telefone": user.telefone,
        "id_telegram": user.id_telegram,
        "username_telegram": user.username_telegram
    }