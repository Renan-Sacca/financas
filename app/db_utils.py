from sqlmodel import Session, create_engine
from .config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    MYSQL_CONNECT_TIMEOUT, MYSQL_READ_TIMEOUT, MYSQL_WRITE_TIMEOUT
)
from contextlib import contextmanager
import logging

# URL de conexão com MySQL
DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

def create_fresh_engine():
    """Cria uma nova engine com configurações otimizadas para evitar desconexões"""
    return create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # Verifica conexão antes de usar
        pool_recycle=1800,   # Recicla conexões a cada 30 minutos
        pool_size=0,         # Não mantém pool de conexões
        max_overflow=0,      # Não permite overflow
        connect_args={
            "connect_timeout": MYSQL_CONNECT_TIMEOUT,
            "read_timeout": MYSQL_READ_TIMEOUT,
            "write_timeout": MYSQL_WRITE_TIMEOUT,
            "autocommit": False,
            "charset": "utf8mb4"
        }
    )

@contextmanager
def get_fresh_session():
    """Context manager que cria uma nova sessão para cada operação"""
    engine = create_fresh_engine()
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        logging.error(f"Erro na sessão do banco: {e}")
        raise
    finally:
        engine.dispose()

def execute_with_retry(func, *args, **kwargs):
    """Executa uma função com retry em caso de erro de conexão"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with get_fresh_session() as session:
                return func(session, *args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logging.warning(f"Tentativa {attempt + 1} falhou: {e}")