import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Set

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database import DynamoConfig, PostgresConfig
from utils.database import DynamoConnection, PostgresConnection

def diagnose():
    dynamo_cfg = DynamoConfig.from_env()
    postgres_cfg = PostgresConfig.from_env()
    
    dynamo_conn = DynamoConnection(dynamo_cfg)
    postgres_conn = PostgresConnection(postgres_cfg)
    
    # Load Maps
    cursor = postgres_conn.get_cursor()
    cursor.execute("SELECT symbol FROM spot_symbols")
    valid_symbols = {row[0] for row in cursor.fetchall()}
    
    cursor.execute("SELECT sub_account_id FROM users WHERE sub_account_id IS NOT NULL")
    valid_users = {row[0] for row in cursor.fetchall()}
    
    # 1. Diagnose Spot Trade History
    print("\n--- Diagnosing Spot Trade History ---")
    history_table = dynamo_conn.get_table('spot-trade-history')
    h_missing_symbols = set()
    h_missing_users = set()
    h_total = 0
    h_skipped_symbol = 0
    h_skipped_user = 0
    
    response = history_table.scan()
    items = response.get('Items', [])
    while True:
        for item in items:
            h_total += 1
            if h_total % 10000 == 0:
                print(f"Scanned {h_total} history items...")
            symbol = item.get('symbol')
            sub_acc = item.get('subAccountId')
            
            s_found = symbol in valid_symbols
            u_found = sub_acc in valid_users
            
            if not s_found:
                h_skipped_symbol += 1
                h_missing_symbols.add(symbol)
            if not u_found:
                h_skipped_user += 1
                h_missing_users.add(sub_acc)
                
        if 'LastEvaluatedKey' in response:
            response = history_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items = response.get('Items', [])
        else:
            break
            
    print(f"Total History Items Scanned: {h_total}")
    print(f"Skipped due to missing Symbol: {h_skipped_symbol}")
    print(f"Skipped due to missing User: {h_skipped_user}")
    print(f"Unique missing Symbols: {list(h_missing_symbols)[:10]}")
    print(f"Unique missing Users (subAccountId): {list(h_missing_users)[:10]}")

    # 2. Diagnose Spot Commissions
    print("\n--- Diagnosing Spot Commissions ---")
    comm_table = dynamo_conn.get_table('broker-spot-commissions')
    c_missing_users = set()
    c_total = 0
    c_skipped_user = 0
    
    response = comm_table.scan()
    items = response.get('Items', [])
    while True:
        for item in items:
            c_total += 1
            if c_total % 10000 == 0:
                print(f"Scanned {c_total} commission items...")
            sub_acc = item.get('subAccountId')
            u_found = sub_acc in valid_users
            
            if not u_found:
                c_skipped_user += 1
                c_missing_users.add(sub_acc)
                
        if 'LastEvaluatedKey' in response:
            response = comm_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items = response.get('Items', [])
        else:
            break
            
    print(f"Total Commission Items Scanned: {c_total}")
    print(f"Skipped due to missing User: {c_skipped_user}")
    print(f"Unique missing Users (subAccountId): {list(c_missing_users)[:10]}")

if __name__ == "__main__":
    diagnose()
