import sqlite3
import os

def migrate_database():
    db_path = "data/finance.db"
    
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
    
    # Migração para categorias
    try:
        # Verificar se a tabela category já existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='category'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE category (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL UNIQUE,
                    color VARCHAR DEFAULT '#007bff',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Migração concluída: tabela category criada")
        
        # Verificar se a coluna category_id já existe na tabela transaction
        cursor.execute('PRAGMA table_info("transaction")')
        transaction_columns_updated = [column[1] for column in cursor.fetchall()]
        
        if 'category_id' not in transaction_columns_updated:
            cursor.execute('ALTER TABLE "transaction" ADD COLUMN category_id INTEGER')
            conn.commit()
            print("Migração concluída: coluna category_id adicionada")
        
        # Verificar e adicionar colunas de agrupamento
        cursor.execute('PRAGMA table_info("transaction")')
        transaction_columns_final = [column[1] for column in cursor.fetchall()]
        
        if 'group_id' not in transaction_columns_final:
            cursor.execute('ALTER TABLE "transaction" ADD COLUMN group_id VARCHAR')
            conn.commit()
            print("Migração concluída: coluna group_id adicionada")
        
        if 'installment_number' not in transaction_columns_final:
            cursor.execute('ALTER TABLE "transaction" ADD COLUMN installment_number INTEGER')
            conn.commit()
            print("Migração concluída: coluna installment_number adicionada")
        
        if 'total_installments' not in transaction_columns_final:
            cursor.execute('ALTER TABLE "transaction" ADD COLUMN total_installments INTEGER')
            conn.commit()
            print("Migração concluída: coluna total_installments adicionada")
            
    except Exception as e:
        print(f"Erro na migração de categorias: {e}")
    
    # Migração para current_balance
    cursor.execute('PRAGMA table_info(bank)')
    bank_columns = [column[1] for column in cursor.fetchall()]
    
    if 'current_balance' not in bank_columns:
        try:
            cursor.execute('ALTER TABLE bank ADD COLUMN current_balance REAL DEFAULT 0.0')
            # Copiar initial_balance para current_balance se existir
            if 'initial_balance' in bank_columns:
                cursor.execute('UPDATE bank SET current_balance = initial_balance')
            conn.commit()
            print("Migração concluída: coluna current_balance adicionada")
        except Exception as e:
            print(f"Erro na migração de current_balance: {e}")
    
    conn.close()

if __name__ == "__main__":
    migrate_database()