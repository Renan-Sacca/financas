import sqlite3
import os
import re
from datetime import datetime

def migrate_group_old_transactions():
    db_path = "/app/data/finance.db"
    
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Buscar transações sem group_id que têm padrão de parcela na descrição
        cursor.execute("""
            SELECT id, description, card_id, amount, date, purchase_date, category_id
            FROM "transaction" 
            WHERE group_id IS NULL 
            AND description LIKE '%(%/%)'
            ORDER BY description, date
        """)
        
        transactions = cursor.fetchall()
        grouped_count = 0
        
        # Agrupar por descrição base (removendo a parte da parcela)
        groups = {}
        
        for transaction in transactions:
            id, description, card_id, amount, date, purchase_date, category_id = transaction
            
            # Extrair descrição base removendo (X/Y)
            base_description = re.sub(r' \(\d+/\d+\)$', '', description)
            
            # Extrair número da parcela e total
            match = re.search(r' \((\d+)/(\d+)\)$', description)
            if match:
                current_installment = int(match.group(1))
                total_installments = int(match.group(2))
                
                # Criar chave única para o grupo
                group_key = f"{base_description}_{card_id}_{total_installments}"
                
                if group_key not in groups:
                    groups[group_key] = []
                
                groups[group_key].append({
                    'id': id,
                    'installment_number': current_installment,
                    'total_installments': total_installments,
                    'base_description': base_description,
                    'card_id': card_id,
                    'amount': amount,
                    'date': date,
                    'purchase_date': purchase_date,
                    'category_id': category_id
                })
        
        # Processar cada grupo
        for group_key, group_transactions in groups.items():
            if len(group_transactions) > 1:  # Só processar se tem mais de 1 transação
                # Gerar group_id único
                group_id = f"migrated_{int(datetime.now().timestamp())}_{hash(group_key) % 10000}"
                
                # Atualizar todas as transações do grupo
                for transaction in group_transactions:
                    cursor.execute("""
                        UPDATE "transaction" 
                        SET group_id = ?, 
                            installment_number = ?, 
                            total_installments = ?
                        WHERE id = ?
                    """, (
                        group_id,
                        transaction['installment_number'],
                        transaction['total_installments'],
                        transaction['id']
                    ))
                
                grouped_count += len(group_transactions)
                print(f"Agrupadas {len(group_transactions)} parcelas: {group_transactions[0]['base_description']}")
        
        conn.commit()
        print(f"Migração concluída! {grouped_count} transações foram agrupadas.")
        
    except Exception as e:
        print(f"Erro na migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_group_old_transactions()
