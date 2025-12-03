from sqlmodel import SQLModel, Session
from .db_utils import create_fresh_engine

def create_db_and_tables():
    engine = create_fresh_engine()
    try:
        SQLModel.metadata.create_all(engine)
    finally:
        engine.dispose()

def get_session():
    engine = create_fresh_engine()
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()