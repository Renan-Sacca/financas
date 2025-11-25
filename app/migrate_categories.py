import sqlite3
import os

def migrate_add_categories():
    db_path = "data/finance.db"
    
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela category já existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='category'")
        if not cursor.fetchone():
            # Criar tabela category
            cursor.execute("""
                CREATE TABLE category (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL UNIQUE,
                    color VARCHAR DEFAULT '#007bff',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Tabela category criada")
        
        # Verificar se a coluna category_id já existe na tabela transaction
        cursor.execute("PRAGMA table_info(transaction)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category_id' not in columns:
            # Adicionar coluna category_id
            cursor.execute("ALTER TABLE transaction ADD COLUMN category_id INTEGER")
            print("Coluna category_id adicionada à tabela transaction")
        
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro na migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_add_categories()