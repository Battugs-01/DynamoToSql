import psycopg2
from config.database import PostgresConfig

def drop_constraint():
    cfg = PostgresConfig.from_env()
    conn = psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        database=cfg.database,
        user=cfg.user,
        password=cfg.password
    )
    cur = conn.cursor()
    
    try:
        print("Dropping problematic constraints...")
        cur.execute("ALTER TABLE spot_trade_histories DROP CONSTRAINT IF EXISTS fk_spot_trade_histories_order;")
        cur.execute("ALTER TABLE spot_commissions DROP CONSTRAINT IF EXISTS fk_spot_commissions_trade;")
        conn.commit()
        print("Constraints dropped successfully.")
    except Exception as e:
        print(f"Error dropping constraint: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    drop_constraint()
