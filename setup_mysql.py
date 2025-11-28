#!/usr/bin/env python3
"""
Script para configurar o banco MySQL na VPS
"""
import pymysql
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

def setup_database():
    """Configura o banco de dados MySQL"""
    
    print("🔧 Configurando banco de dados MySQL...")
    
    try:
        # Conectar ao MySQL (sem especificar database)
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # Criar database se não existir
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Database '{MYSQL_DATABASE}' criado/verificado")
        
        # Usar o database
        cursor.execute(f"USE {MYSQL_DATABASE}")
        
        # Criar tabelas
        create_tables(cursor)
        
        conn.commit()
        print("🎉 Configuração do MySQL concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao configurar MySQL: {e}")
    
    finally:
        if 'conn' in locals():
            conn.close()

def create_tables(cursor):
    """Cria as tabelas necessárias"""
    
    print("📋 Criando tabelas...")
    
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
    
    print("✅ Tabelas criadas com sucesso!")

if __name__ == "__main__":
    setup_database()