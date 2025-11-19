from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = "sqlite:///./data/finance.db"

# Criar diretório data se não existir
os.makedirs("data", exist_ok=True)

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session