import psycopg2
from config.database import PostgresConfig

def clear_tables():
    cfg = PostgresConfig.from_env()
    conn = psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        database=cfg.database,
        user=cfg.user,
        password=cfg.password
    )
    cur = conn.cursor()
    
    tables = [
        'spot_trade_histories',
        'spot_trade_orders',
        'spot_commissions'
    ]
    
    for table in tables:
        print(f"Clearing {table}...")
        cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Tables cleared successfully.")

if __name__ == "__main__":
    clear_tables()
