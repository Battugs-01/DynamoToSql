import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database import DynamoConfig, PostgresConfig
from utils.database import DynamoConnection, PostgresConnection

def check_counts():
    dynamo_config = DynamoConfig.from_env()
    postgres_config = PostgresConfig.from_env()
    
    dy_conn = DynamoConnection(dynamo_config)
    pg_conn = PostgresConnection(postgres_config)
    
    pg_cur = pg_conn.get_cursor()
    # DynamoDB client from connection resource
    dynamo_client = dy_conn.resource.meta.client

    tables_to_check = [
        ('broker_users', None),
        ('spot_symbols', 'Symbols'),
        ('spot_trade_orders', 'spot-trade-orders'),
        ('spot_trade_histories', 'spot-trade-history'),
        ('spot_commissions', 'broker-spot-commissions')
    ]

    print(f"{'Table':<25} {'Postgres':<10} {'DynamoDB (Est)':<15} {'Status'}")
    print("-" * 65)

    for pg_table, dy_table in tables_to_check:
        # Postgres count
        pg_cur.execute(f"SELECT count(*) FROM {pg_table}")
        pg_count = pg_cur.fetchone()[0]

        # Dynamo count
        if dy_table:
            dy_meta = dynamo_client.describe_table(TableName=dy_table)
            dy_count = dy_meta['Table']['ItemCount']
            status = "MATCH (Est)" if pg_count >= dy_count * 0.95 else "CHECK LOGS"
        else:
            dy_count = "-"
            status = "-"

        print(f"{pg_table:<25} {pg_count:<10} {dy_count:<15} {status}")

    # Specific check for orphans-now linked to BrokerUser
    pg_cur.execute("SELECT count(*) FROM spot_trade_histories WHERE broker_user_id IS NULL")
    orphans = pg_cur.fetchone()[0]
    print(f"\nOrphaned Trade Histories (missing broker_user_id): {orphans}")

    pg_cur.execute("SELECT count(*) FROM spot_commissions WHERE broker_user_id IS NULL")
    orphans_comm = pg_cur.fetchone()[0]
    print(f"Orphaned Commissions (missing broker_user_id): {orphans_comm}")

    pg_conn.close()

if __name__ == "__main__":
    check_counts()
