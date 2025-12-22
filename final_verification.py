import os
import psycopg2
import boto3
from dotenv import load_dotenv

load_dotenv()

def check_counts():
    # PostgreSQL connection
    pg_conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        dbname=os.getenv('DB_NAME')
    )
    pg_cur = pg_conn.cursor()

    # DynamoDB client
    dynamo = boto3.client('dynamodb', region_name=os.getenv('AWS_REGION'))

    tables_to_check = [
        ('broker_users', None), # Consolidated
        ('spot_symbols', 'SpotSymbol'),
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
            dy_meta = dynamo.describe_table(TableName=dy_table)
            dy_count = dy_meta['Table']['ItemCount']
            status = "MATCH (Est)" if pg_count >= dy_count * 0.95 else "CHECK LOGS"
            if pg_table == 'spot_trade_histories' or pg_table == 'spot_commissions':
                # We know some are skipped due to symbols, but now we should have fewer skips
                pass
        else:
            dy_count = "-"
            status = "-"

        print(f"{pg_table:<25} {pg_count:<10} {dy_count:<15} {status}")

    # Specific check for orphans
    pg_cur.execute("SELECT count(*) FROM spot_trade_histories WHERE broker_user_id IS NULL")
    orphans = pg_cur.fetchone()[0]
    print(f"\nOrphaned Trade Histories: {orphans}")

    pg_cur.execute("SELECT count(*) FROM spot_commissions WHERE broker_user_id IS NULL")
    orphans_comm = pg_cur.fetchone()[0]
    print(f"Orphaned Commissions: {orphans_comm}")

    pg_conn.close()

if __name__ == "__main__":
    check_counts()
