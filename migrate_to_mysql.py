#!/usr/bin/env python3
"""
Script para migrar dados do SQLite para MySQL
"""
import sqlite3
import pymysql
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
SQLITE_DB = "./data/finance.db"
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

def migrate_data():
    """Migra dados do SQLite para MySQL"""
    
    # Verificar se o arquivo SQLite existe
    if not os.path.exists(SQLITE_DB):
        print("❌ Arquivo SQLite não encontrado. Criando apenas as tabelas no MySQL...")
        create_mysql_tables()
        return
    
    print("🔄 Iniciando migração do SQLite para MySQL...")
    
    # Conectar ao SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # Conectar ao MySQL
    mysql_conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4'
    )
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # Criar tabelas no MySQL
        create_mysql_tables_with_cursor(mysql_cursor)
        
        # Migrar dados das tabelas
        tables = ['user', 'bank', 'card', 'category', 'transaction', 'deposit', 'transfer']
        
        for table in tables:
            print(f"📋 Migrando tabela: {table}")
            
            # Verificar se a tabela existe no SQLite
            sqlite_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not sqlite_cursor.fetchone():
                print(f"⚠️  Tabela {table} não existe no SQLite, pulando...")
                continue
            
            # Obter dados do SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"📭 Tabela {table} está vazia")
                continue
            
            # Obter nomes das colunas
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Inserir dados no MySQL
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            insert_query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            
            for row in rows:
                try:
                    mysql_cursor.execute(insert_query, tuple(row))
                except Exception as e:
                    print(f"❌ Erro ao inserir linha na tabela {table}: {e}")
                    print(f"   Dados: {dict(row)}")
            
            mysql_conn.commit()
            print(f"✅ Tabela {table} migrada com sucesso ({len(rows)} registros)")
        
        print("🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        mysql_conn.rollback()
    
    finally:
        sqlite_conn.close()
        mysql_conn.close()

def create_mysql_tables():
    """Cria apenas as tabelas no MySQL sem migrar dados"""
    mysql_conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4'
    )
    mysql_cursor = mysql_conn.cursor()
    
    try:
        create_mysql_tables_with_cursor(mysql_cursor)
        mysql_conn.commit()
        print("✅ Tabelas criadas no MySQL com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
    finally:
        mysql_conn.close()

def create_mysql_tables_with_cursor(cursor):
    """Cria as tabelas no MySQL"""
    
    # Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de bancos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            initial_balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de cartões
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS card (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type ENUM('credit', 'debit') NOT NULL,
            bank_id INT NOT NULL,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bank_id) REFERENCES bank(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de categorias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de transações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction (
            id INT AUTO_INCREMENT PRIMARY KEY,
            card_id INT NOT NULL,
            category_id INT,
            amount DECIMAL(10,2) NOT NULL,
            type ENUM('expense', 'payment', 'refund') NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES card(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de depósitos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deposit (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bank_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bank_id) REFERENCES bank(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )
    """)
    
    # Tabela de transferências
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfer (
            id INT AUTO_INCREMENT PRIMARY KEY,
            from_bank_id INT NOT NULL,
            to_bank_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_bank_id) REFERENCES bank(id) ON DELETE CASCADE,
            FOREIGN KEY (to_bank_id) REFERENCES bank(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        )
    """)

if __name__ == "__main__":
    migrate_data()