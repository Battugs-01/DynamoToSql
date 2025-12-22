import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database import PostgresConfig
from utils.database import PostgresConnection

def scan():
    load_dotenv()
    postgres_config = PostgresConfig.from_env()
    postgres_conn = PostgresConnection(postgres_config)
    
    try:
        cursor = postgres_conn.get_cursor()
        
        tables = ['spot_trade_orders', 'spot_trade_histories', 'spot_commissions', 'spot_symbols']
        
        for table in tables:
            print(f"\n--- Table: {table} ---")
            
            # For orders, history, commissions, symbols we want status
            # For history it might be trade_status
            
            status_field = 'status'
            if table == 'spot_trade_histories':
                status_field = 'trade_status'
            
            try:
                cursor.execute(f"SELECT DISTINCT {status_field} FROM {table}")
                statuses = cursor.fetchall()
                print(f"Unique {status_field} values: {[s[0] for s in statuses]}")
            except Exception as e:
                print(f"Error scanning {table} for status: {e}")
                postgres_conn.rollback()

            if table == 'spot_trade_orders':
                cursor.execute(f"SELECT DISTINCT side FROM {table}")
                sides = cursor.fetchall()
                print(f"Unique side values: {[s[0] for s in sides]}")
                
                cursor.execute(f"SELECT DISTINCT type FROM {table}")
                types = cursor.fetchall()
                print(f"Unique type values: {[s[0] for s in types]}")
            
            if table == 'spot_symbols':
                # Check status and other relevant fields for symbols
                pass

    finally:
        postgres_conn.close()

if __name__ == '__main__':
    scan()
