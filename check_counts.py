import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database import DynamoConfig, PostgresConfig, MigrationConfig
from utils.database import DynamoConnection, PostgresConnection

def get_counts():
    # Load default configs from env
    dynamo_cfg = DynamoConfig.from_env()
    postgres_cfg = PostgresConfig.from_env()
    
    dynamo_conn = DynamoConnection(dynamo_cfg)
    postgres_conn = PostgresConnection(postgres_cfg)
    
    # DynamoDB count (Estimated)
    # Note: Table.item_count is refreshed approximately every 6 hours.
    dynamo_table = dynamo_conn.get_table('spot-trade-orders')
    dynamo_count_est = dynamo_table.item_count
    
    # Postgres count
    cursor = postgres_conn.get_cursor()
    cursor.execute("SELECT count(*) FROM spot_trade_orders")
    postgres_count = cursor.fetchone()[0]
    
    print(f"DynamoDB (Table item_count - estimated): {dynamo_count_est}")
    print(f"PostgreSQL (Direct count): {postgres_count}")
    
    # Also report the last migration scan result for context
    print("\nNote: The latest migration scan reported exactly 143,326 items processed.")

if __name__ == "__main__":
    get_counts()
