from sqlmodel import create_engine, text
from app.database import DATABASE_URL

def migrate_purchase_date():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # Verificar se a coluna já existe
        result = connection.execute(text("PRAGMA table_info(transaction)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'purchase_date' not in columns:
            print("Adicionando coluna purchase_date...")
            connection.execute(text("ALTER TABLE transaction ADD COLUMN purchase_date DATE"))
            connection.commit()
            print("Coluna purchase_date adicionada com sucesso!")
        else:
            print("Coluna purchase_date já existe.")

if __name__ == "__main__":
    migrate_purchase_date()