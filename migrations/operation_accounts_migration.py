"""
Operation Accounts table migration from DynamoDB to PostgreSQL
Internal company accounts for operations
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class OperationAccountsMigration(BaseMigration):
    """Migration for operation_accounts table"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id_counter = 0
    
    @property
    def dynamo_table_name(self) -> str:
        return "operation-accounts"
    
    @property
    def postgres_table_name(self) -> str:
        return "operation_accounts"
    
    def get_next_id(self) -> int:
        """Get next auto-increment ID"""
        if self._id_counter == 0:
            # Get max ID from database
            try:
                cursor = self.postgres.get_cursor()
                cursor.execute(f"SELECT COALESCE(MAX(CAST(id AS INTEGER)), 0) FROM {self.postgres_table_name}")
                result = cursor.fetchone()
                self._id_counter = result[0] if result else 0
            except Exception:
                self._id_counter = 0
        
        self._id_counter += 1
        return self._id_counter
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB operation account item to PostgreSQL format"""
        sub_account_id = item.get("subAccountId")
        if not sub_account_id:
            logger.warning(f"Skipping operation account {item.get('name')} - missing subAccountId")
            return None
        
        return {
            'id': str(self.get_next_id()),  # Auto-increment ID starting from 1
            'sub_account_id': sub_account_id,  # SubAccountId can be duplicated
            'name': item.get("name"),
            'api_key': item.get("apiKey"),
            'binance_email': item.get("binanceEmail"),
            'can_trade': self.convert_to_boolean(item.get("canTrade")),
            'can_withdraw': self.convert_to_boolean(item.get("canWithdraw")),
            'description': item.get("description"),
            'secret_key': item.get("secretKey"),
            'created_at': self.convert_epoch_to_iso(item.get("createdAt")),
            'updated_at': self.convert_epoch_to_iso(item.get("createdAt")),
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for operation_accounts table"""
        return """
            INSERT INTO operation_accounts (
                id, sub_account_id, name, api_key, binance_email,
                can_trade, can_withdraw, description,
                secret_key, created_at, updated_at
            )
            VALUES (
                %(id)s, %(sub_account_id)s, %(name)s, %(api_key)s, %(binance_email)s,
                %(can_trade)s, %(can_withdraw)s, %(description)s,
                %(secret_key)s, %(created_at)s, %(updated_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query - UPDATE existing records on conflict"""
        return """
            INSERT INTO operation_accounts (
                id, sub_account_id, name, api_key, binance_email,
                can_trade, can_withdraw, description,
                secret_key, created_at, updated_at
            )
            VALUES (
                %(id)s, %(sub_account_id)s, %(name)s, %(api_key)s, %(binance_email)s,
                %(can_trade)s, %(can_withdraw)s, %(description)s,
                %(secret_key)s, %(created_at)s, %(updated_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                sub_account_id = EXCLUDED.sub_account_id,
                name = EXCLUDED.name,
                api_key = EXCLUDED.api_key,
                binance_email = EXCLUDED.binance_email,
                can_trade = EXCLUDED.can_trade,
                can_withdraw = EXCLUDED.can_withdraw,
                description = EXCLUDED.description,
                secret_key = EXCLUDED.secret_key,
                updated_at = EXCLUDED.updated_at
        """
