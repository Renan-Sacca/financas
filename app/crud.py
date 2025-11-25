from sqlmodel import Session, select
from app.models import Bank, Card, Transaction, TransactionType
from app.schemas import BankCreate, BankUpdate, CardCreate, CardUpdate, TransactionCreate, TransferCreate
from typing import List, Optional
from datetime import date

def create_bank(session: Session, bank: BankCreate) -> Bank:
    db_bank = Bank(**bank.dict())
    session.add(db_bank)
    session.commit()
    session.refresh(db_bank)
    return db_bank

def get_banks(session: Session) -> List[Bank]:
    return session.exec(select(Bank)).all()

def get_bank(session: Session, bank_id: int) -> Optional[Bank]:
    return session.get(Bank, bank_id)

def update_bank(session: Session, bank_id: int, bank_update: BankUpdate) -> Optional[Bank]:
    bank = session.get(Bank, bank_id)
    if bank:
        update_data = bank_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bank, field, value)
        session.commit()
        session.refresh(bank)
        return bank
    return None

def delete_bank(session: Session, bank_id: int) -> bool:
    bank = session.get(Bank, bank_id)
    if bank:
        # Excluir todas as transações dos cartões deste banco
        cards = session.exec(select(Card).where(Card.bank_id == bank_id)).all()
        for card in cards:
            transactions = session.exec(select(Transaction).where(Transaction.card_id == card.id)).all()
            for transaction in transactions:
                session.delete(transaction)
            session.delete(card)
        
        session.delete(bank)
        session.commit()
        return True
    return False

def create_card(session: Session, bank_id: int, card: CardCreate) -> Card:
    db_card = Card(**card.dict(), bank_id=bank_id)
    session.add(db_card)
    session.commit()
    session.refresh(db_card)
    return db_card

def get_card(session: Session, card_id: int) -> Optional[Card]:
    return session.get(Card, card_id)

def get_cards(session: Session, bank_id: Optional[int] = None) -> List[Card]:
    query = select(Card)
    if bank_id:
        query = query.where(Card.bank_id == bank_id)
    return session.exec(query).all()

def update_card(session: Session, card_id: int, card_update: CardUpdate) -> Optional[Card]:
    card = session.get(Card, card_id)
    if card:
        update_data = card_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(card, field, value)
        session.commit()
        session.refresh(card)
        return card
    return None

def delete_card(session: Session, card_id: int) -> bool:
    card = session.get(Card, card_id)
    if card:
        session.delete(card)
        session.commit()
        return True
    return False

def create_transaction(session: Session, transaction: TransactionCreate) -> Transaction:
    db_transaction = Transaction(**transaction.dict())
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction

def get_transactions(session: Session, bank_id: Optional[int] = None, card_id: Optional[int] = None, date_from: Optional[date] = None, date_to: Optional[date] = None, status: Optional[str] = None) -> List[Transaction]:
    query = select(Transaction).join(Card).join(Bank)
    if bank_id:
        query = query.where(Bank.id == bank_id)
    if card_id:
        query = query.where(Card.id == card_id)
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    if status == 'paid':
        query = query.where(Transaction.is_paid == True)
    elif status == 'pending':
        query = query.where(Transaction.is_paid == False)
    return session.exec(query).all()

def create_transfer(session: Session, transfer: TransferCreate) -> bool:
    from_bank = session.get(Bank, transfer.from_bank_id)
    to_bank = session.get(Bank, transfer.to_bank_id)
    
    if not from_bank or not to_bank:
        return False
    
    # Buscar primeiro cartão de cada banco
    from_card = session.exec(select(Card).where(Card.bank_id == transfer.from_bank_id)).first()
    to_card = session.exec(select(Card).where(Card.bank_id == transfer.to_bank_id)).first()
    
    if not from_card or not to_card:
        return False
    
    # Criar transação de saída
    out_transaction = Transaction(
        card_id=from_card.id,
        amount=transfer.amount,
        type=TransactionType.transfer_out,
        description=f"Transferência para {to_bank.name}: {transfer.description}",
        date=transfer.date,
        transfer_to_bank_id=transfer.to_bank_id
    )
    
    # Criar transação de entrada
    in_transaction = Transaction(
        card_id=to_card.id,
        amount=transfer.amount,
        type=TransactionType.transfer_in,
        description=f"Transferência de {from_bank.name}: {transfer.description}",
        date=transfer.date
    )
    
    session.add(out_transaction)
    session.add(in_transaction)
    session.commit()
    return True

def calculate_bank_balance(session: Session, bank_id: int) -> float:
    bank = session.get(Bank, bank_id)
    if not bank:
        return 0.0
    
    balance = bank.initial_balance
    
    # Buscar todas as transações dos cartões deste banco
    transactions = session.exec(
        select(Transaction).join(Card).where(Card.bank_id == bank_id)
    ).all()
    
    for transaction in transactions:
        if transaction.is_paid:  # Só considera transações pagas
            if transaction.type in [TransactionType.expense, TransactionType.transfer_out]:
                balance -= transaction.amount
            elif transaction.type in [TransactionType.payment, TransactionType.refund, TransactionType.deposit, TransactionType.transfer_in]:
                balance += transaction.amount
    
    return balance

def get_transaction(session: Session, transaction_id: int) -> Optional[Transaction]:
    return session.get(Transaction, transaction_id)

def update_transaction(session: Session, transaction_id: int, transaction_update: TransactionCreate) -> Optional[Transaction]:
    transaction = session.get(Transaction, transaction_id)
    if transaction:
        update_data = transaction_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)
        session.commit()
        session.refresh(transaction)
        return transaction
    return None

def toggle_transaction_payment(session: Session, transaction_id: int) -> Optional[Transaction]:
    transaction = session.get(Transaction, transaction_id)
    if transaction:
        transaction.is_paid = not transaction.is_paid
        session.commit()
        session.refresh(transaction)
        return transaction
    return None

def bulk_update_transaction_status(session: Session, transaction_ids: List[int], is_paid: bool) -> List[Transaction]:
    transactions = session.exec(select(Transaction).where(Transaction.id.in_(transaction_ids))).all()
    if transactions:
        for transaction in transactions:
            transaction.is_paid = is_paid
        session.commit()
        for transaction in transactions:
            session.refresh(transaction)
        return transactions
    return []

def mark_previous_transactions_as_paid(session: Session, current_date) -> int:
    from datetime import date
    transactions = session.exec(
        select(Transaction).where(
            Transaction.date < current_date,
            Transaction.is_paid == False
        )
    ).all()
    
    count = 0
    for transaction in transactions:
        transaction.is_paid = True
        count += 1
    
    session.commit()
    return count

def delete_transaction(session: Session, transaction_id: int) -> bool:
    transaction = session.get(Transaction, transaction_id)
    if transaction:
        session.delete(transaction)
        session.commit()
        return True
    return False