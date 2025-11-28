from sqlmodel import SQLModel, create_engine, Session, text
from app.database import engine
from app.models import User, Bank, Card, Transaction, Category

def migrate_to_auth():
    """Migração para adicionar autenticação e user_id às tabelas existentes"""
    
    with Session(engine) as session:
        try:
            # Criar todas as tabelas primeiro
            SQLModel.metadata.create_all(engine)
            
            # Verificar se a tabela user existe e tem dados
            result = session.exec(text("SELECT name FROM sqlite_master WHERE type='table' AND name='user'"))
            user_table_exists = result.first() is not None
            
            # Verificar se as colunas user_id já existem nas tabelas
            result = session.exec(text("PRAGMA table_info(bank)"))
            bank_columns = [row[1] for row in result.fetchall()]
            
            if 'user_id' not in bank_columns:
                print("Adicionando colunas user_id...")
                
                # Verificar e adicionar colunas user_id apenas se não existirem
                try:
                    session.exec(text("ALTER TABLE bank ADD COLUMN user_id INTEGER"))
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
                
                try:
                    session.exec(text("ALTER TABLE category ADD COLUMN user_id INTEGER"))
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
                
                # Criar um usuário padrão se não existir
                result = session.exec(text("SELECT COUNT(*) FROM user"))
                user_count = result.first()[0]
                
                if user_count == 0:
                    print("Criando usuário padrão...")
                    session.exec(text("""
                        INSERT INTO user (email, hashed_password, full_name, is_active, is_verified, created_at) 
                        VALUES ('admin@admin.com', '$2b$12$dummy.hash.for.migration', 'Usuário Padrão', 1, 1, datetime('now'))
                    """))
                    session.commit()
                
                # Obter ID do primeiro usuário
                result = session.exec(text("SELECT id FROM user LIMIT 1"))
                user_id = result.first()[0]
                
                # Atualizar registros existentes com user_id
                session.exec(text(f"UPDATE bank SET user_id = {user_id} WHERE user_id IS NULL"))
                session.exec(text(f"UPDATE category SET user_id = {user_id} WHERE user_id IS NULL"))
                
                session.commit()
                print("Migração concluída com sucesso!")
            else:
                print("Migração já foi executada anteriormente.")
                
        except Exception as e:
            print(f"Erro durante a migração: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    migrate_to_auth()