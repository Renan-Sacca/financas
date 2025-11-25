import sqlite3
import os

def migrate_database():
    db_path = "/app/data/finance.db"
    
    if not os.path.exists(db_path):
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se a coluna transfer_to_bank_id já existe
    cursor.execute('PRAGMA table_info("transaction")')
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'transfer_to_bank_id' not in columns:
        try:
            cursor.execute('ALTER TABLE "transaction" ADD COLUMN transfer_to_bank_id INTEGER')
            conn.commit()
            print("Migração concluída: coluna transfer_to_bank_id adicionada")
        except Exception as e:
            print(f"Erro na migração: {e}")
    
    # Verificar se as colunas do cartão já existem
    cursor.execute('PRAGMA table_info(card)')
    card_columns = [column[1] for column in cursor.fetchall()]
    
    if 'limit_amount' not in card_columns:
        try:
            cursor.execute('ALTER TABLE card ADD COLUMN limit_amount REAL')
            conn.commit()
            print("Migração concluída: coluna limit_amount adicionada")
        except Exception as e:
            print(f"Erro na migração: {e}")
    
    if 'due_day' not in card_columns:
        try:
            cursor.execute('ALTER TABLE card ADD COLUMN due_day INTEGER')
            conn.commit()
            print("Migração concluída: coluna due_day adicionada")
        except Exception as e:
            print(f"Erro na migração: {e}")
    
    # Verificar se a coluna is_paid já existe
    cursor.execute('PRAGMA table_info("transaction")')
    transaction_columns = [column[1] for column in cursor.fetchall()]
    
    if 'is_paid' not in transaction_columns:
        try:
            cursor.execute('ALTER TABLE "transaction" ADD COLUMN is_paid BOOLEAN DEFAULT 0')
            conn.commit()
            print("Migração concluída: coluna is_paid adicionada")
        except Exception as e:
            print(f"Erro na migração: {e}")
    
    if 'purchase_date' not in transaction_columns:
        try:
            cursor.execute('ALTER TABLE "transaction" ADD COLUMN purchase_date DATE')
            conn.commit()
            print("Migração concluída: coluna purchase_date adicionada")
        except Exception as e:
            print(f"Erro na migração: {e}")
    
    conn.close()

if __name__ == "__main__":
    migrate_database()