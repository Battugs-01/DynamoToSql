"""
BrokerUsers Migration Script
============================
Энэ script нь DynamoDB-ээс биш PostgreSQL-ийн users болон operation_accounts 
table-үүдээс уншиж broker_users table-д оруулна.

broker_users нь Users + OperationAccounts-ийн SubAccountID-уудыг нэгтгэсэн table.
InternalTransactions дээр foreign key болгон ашиглана.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from utils.migration_base import BaseMigration
from utils.database import DynamoConnection, PostgresConnection
from config.database import MigrationConfig

logger = logging.getLogger(__name__)


class BrokerUsersMigration(BaseMigration):
    """Special migration that reads from PostgreSQL tables, not DynamoDB"""
    
    def __init__(self, 
                 dynamo_conn: DynamoConnection, 
                 postgres_conn: PostgresConnection,
                 config: MigrationConfig):
        super().__init__(dynamo_conn, postgres_conn, config)
    
    @property
    def dynamo_table_name(self) -> str:
        # Not used - энэ migration DynamoDB-ээс уншдаггүй
        return "broker-users-placeholder"
    
    @property
    def postgres_table_name(self) -> str:
        return "broker_users"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # Not used - энэ migration run_migration-д шууд ажиллана
        return item
    
    def get_insert_query(self) -> str:
        return """
            INSERT INTO broker_users (
                id, sub_account_id, type, user_id, operation_id,
                name, email, binance_email, can_trade, can_withdraw,
                first_name, last_name, is_whitelist_enabled, kyc_level, vip_level, status, meta_data,
                api_key, secret_key, description,
                created_at, updated_at
            )
            VALUES (
                %(id)s, %(sub_account_id)s, %(type)s, %(user_id)s, %(operation_id)s,
                %(name)s, %(email)s, %(binance_email)s, %(can_trade)s, %(can_withdraw)s,
                %(first_name)s, %(last_name)s, %(is_whitelist_enabled)s, %(kyc_level)s, %(vip_level)s, %(status)s, %(meta_data)s,
                %(api_key)s, %(secret_key)s, %(description)s,
                %(created_at)s, %(updated_at)s
            )
            ON CONFLICT (sub_account_id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        return self.get_insert_query()
    
    def run_migration(self) -> Dict[str, int]:
        """Override run_migration to read from PostgreSQL instead of DynamoDB"""
        logger.info("Starting BrokerUsers migration from PostgreSQL tables...")
        
        conn = self.postgres.connection
        cur = conn.cursor()
        
        migrated = 0
        errors = 0
        
        try:
            now = datetime.utcnow().isoformat()
            
            # 1. Users-ээс SubAccountID байгаа бүгдийг авах
            logger.info("Fetching users with SubAccountID...")
            cur.execute("""
                SELECT id, sub_account_id, email, binance_email, first_name, last_name,
                       can_trade, can_withdraw, is_whitelist_enabled, kyc_level, vip_level, 
                       status, meta_data
                FROM users 
                WHERE sub_account_id IS NOT NULL AND sub_account_id != ''
            """)
            users = cur.fetchall()
            logger.info(f"Found {len(users)} users with SubAccountID")
            
            # 2. OperationAccounts-ээс бүгдийг авах
            logger.info("Fetching operation accounts...")
            cur.execute("""
                SELECT id, sub_account_id, name, binance_email, can_trade, can_withdraw,
                       api_key, secret_key, description
                FROM operation_accounts 
                WHERE sub_account_id IS NOT NULL AND sub_account_id != ''
            """)
            operations = cur.fetchall()
            logger.info(f"Found {len(operations)} operation accounts")
            
            # 3. Users оруулах
            for user in users:
                try:
                    (user_id, sub_account_id, email, binance_email, first_name, last_name,
                     can_trade, can_withdraw, is_whitelist_enabled, kyc_level, vip_level, 
                     status, meta_data) = user
                    
                    name = f"{first_name or ''} {last_name or ''}".strip() or None
                    
                    data = {
                        'id': str(uuid.uuid4()),
                        'sub_account_id': sub_account_id,
                        'type': 'user',
                        'user_id': user_id,
                        'operation_id': None,
                        'name': name,
                        'email': email,
                        'binance_email': binance_email,
                        'can_trade': can_trade,
                        'can_withdraw': can_withdraw,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_whitelist_enabled': is_whitelist_enabled,
                        'kyc_level': kyc_level,
                        'vip_level': vip_level,
                        'status': status,
                        'meta_data': meta_data,
                        'api_key': None,
                        'secret_key': None,
                        'description': None,
                        'created_at': now,
                        'updated_at': now
                    }
                    
                    cur.execute(self.get_insert_query(), data)
                    migrated += 1
                except Exception as e:
                    logger.error(f"Failed to insert user broker: {e}")
                    errors += 1
            
            logger.info(f"Inserted {migrated} user broker_users")
            
            # 4. Operations оруулах
            ops_migrated = 0
            for op in operations:
                try:
                    (op_id, sub_account_id, name, binance_email, can_trade, can_withdraw,
                     api_key, secret_key, description) = op
                    
                    data = {
                        'id': str(uuid.uuid4()),
                        'sub_account_id': sub_account_id,
                        'type': 'operation',
                        'user_id': None,
                        'operation_id': op_id,
                        'name': name,
                        'email': None,
                        'binance_email': binance_email,
                        'can_trade': can_trade,
                        'can_withdraw': can_withdraw,
                        'first_name': None,
                        'last_name': None,
                        'is_whitelist_enabled': None,
                        'kyc_level': None,
                        'vip_level': None,
                        'status': None,
                        'meta_data': None,
                        'api_key': api_key,
                        'secret_key': secret_key,
                        'description': description,
                        'created_at': now,
                        'updated_at': now
                    }
                    
                    cur.execute(self.get_insert_query(), data)
                    migrated += 1
                    ops_migrated += 1
                except Exception as e:
                    logger.error(f"Failed to insert operation broker: {e}")
                    errors += 1
            
            logger.info(f"Inserted {ops_migrated} operation broker_users")
            
            conn.commit()
            logger.info(f"Migration completed. Total migrated: {migrated}, Errors: {errors}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            cur.close()
        
        return {'migrated': migrated, 'errors': errors, 'total': len(users) + len(operations)}
