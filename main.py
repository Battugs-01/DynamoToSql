import os
import json
import boto3
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json
from datetime import datetime, timezone
# === CONFIG ===
DYNAMO_TABLE = "xmeta-users"

AWS_REGION = os.getenv('AWS_DEFAULT_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

PG_HOST = "localhost"
PG_PORT = 5433
PG_DATABASE = "x-meta"
PG_USER = "postgres"
PG_PASSWORD = "Pass1234!"


if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
else:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

table = dynamodb.Table(DYNAMO_TABLE)

conn = psycopg2.connect(
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DATABASE,
    user=PG_USER,
    password=PG_PASSWORD
)
cursor = conn.cursor()

response = table.scan(Limit=100)
items = response.get('Items', [])

print(f"Found {len(items)} items from DynamoDB.")

for item in items:
    uid = item.get("uid")
    first_name = item.get("firstName")
    last_name = item.get("lastName")
    email = item.get("email")
    created_at_epoch = item.get("createdAt")
    updated_at_epoch = item.get("updatedAt")
    created_at = (
        datetime.fromtimestamp(float(created_at_epoch) / 1000, tz=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        if created_at_epoch is not None else None
    )
    updated_at = (
        datetime.fromtimestamp(float(updated_at_epoch) / 1000, tz=timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        if updated_at_epoch is not None else None
    )
    status = item.get("status")
    can_trade = bool(item.get("canTrade")) if item.get("canTrade") is not None else None
    can_withdraw = bool(item.get("canWithdraw")) if item.get("canWithdraw") is not None else None
    is_whitelist_enabled = bool(item.get("isWhitelistEnabled")) if item.get("isWhitelistEnabled") is not None else None
    kyc_level = item.get("kycLevel")
    vip_level = item.get("vipLevel")
    binance_email = item.get("binanceEmail")
    sub_account_id = item.get("subAccountId")
    meta_data = item.get("metaData")
    
    meta_data_json = Json(meta_data) if meta_data else None

    cursor.execute(
        sql.SQL("""
            INSERT INTO users (
                id, first_name, last_name, email, created_at, updated_at,
                status, can_trade, can_withdraw, is_whitelist_enabled,
                kyc_level, vip_level, binance_email, sub_account_id, meta_data
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """),
        (uid, first_name, last_name, email, created_at, updated_at,
         status, can_trade, can_withdraw, is_whitelist_enabled,
         kyc_level, vip_level, binance_email, sub_account_id, meta_data_json)
    )

conn.commit()
print("✅ Successfully inserted first 100 users into PostgreSQL.")

cursor.close()
conn.close()
