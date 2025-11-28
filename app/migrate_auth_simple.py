from sqlmodel import SQLModel, Session, text
from app.database import engine
import os

def migrate_to_auth():
    """Migração simples e segura para autenticação"""
    
    # Se o banco não existe, criar tudo do zero
    db_path = "data/finance.db"
    if not os.path.exists(db_path):
        print("Criando banco de dados do zero...")
        SQLModel.metadata.create_all(engine)
        return
    
    with Session(engine) as session:
        try:
            # Sempre criar/atualizar tabelas
            SQLModel.metadata.create_all(engine)
            
            # Verificar se já existe usuário
            try:
                result = session.exec(text("SELECT COUNT(*) FROM user"))
                user_count = result.first()[0]
                print(f"Usuários existentes: {user_count}")
            except:
                print("Tabela user não existe, será criada automaticamente")
                return
            
            # Verificar se bancos têm user_id
            try:
                result = session.exec(text("SELECT user_id FROM bank LIMIT 1"))
                print("Colunas user_id já existem")
                return
            except:
                print("Adicionando colunas user_id...")
            
            # Criar usuário padrão se não existir
            if user_count == 0:
                print("Criando usuário padrão...")
                session.exec(text("""
                    INSERT INTO user (email, hashed_password, full_name, is_active, is_verified, created_at) 
                    VALUES ('admin@admin.com', '$2b$12$LQv3c1yqBWVHxkd0LQ4YCOIYd2nkUlyqeqhUDdC.O2jLxU09dO/Nu', 'Usuário Padrão', 1, 1, datetime('now'))
                """))
                session.commit()
            
            # Obter ID do primeiro usuário
            result = session.exec(text("SELECT id FROM user LIMIT 1"))
            user_id = result.first()[0]
            
            # Adicionar colunas user_id se não existirem
            try:
                session.exec(text("ALTER TABLE bank ADD COLUMN user_id INTEGER"))
            except:
                pass  # Coluna já existe
                
            try:
                session.exec(text("ALTER TABLE category ADD COLUMN user_id INTEGER"))
            except:
                pass  # Coluna já existe
            
            # Atualizar registros sem user_id
            session.exec(text(f"UPDATE bank SET user_id = {user_id} WHERE user_id IS NULL"))
            session.exec(text(f"UPDATE category SET user_id = {user_id} WHERE user_id IS NULL"))
            
            session.commit()
            print("Migração concluída!")
            
        except Exception as e:
            print(f"Erro na migração: {e}")
            session.rollback()

if __name__ == "__main__":
    migrate_to_auth()