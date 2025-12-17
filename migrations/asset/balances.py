"""
Balances Migration Script
=========================
DynamoDB: balances → PostgreSQL: balances
subAccountId-аар broker_users-тэй холбогдоно
"""
import logging
from typing import Dict, Any

from utils.migration_base import BaseMigration

logger = logging.getLogger(__name__)


class BalancesMigration(BaseMigration):
    """Migration for balances table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "balance"
    
    @property
    def postgres_table_name(self) -> str:
        return "balances"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB balance item to PostgreSQL format"""
        sub_account_id = item.get("subAccountId")
        asset = item.get("asset")
        
        if not sub_account_id:
            logger.warning(f"Skipping balance - missing subAccountId")
            return None
        
        if not asset:
            logger.warning(f"Skipping balance - missing asset")
            return None
        
        # Use subAccountId + asset as unique identifier
        unique_id = f"{sub_account_id}_{asset}"
        
        create_time = item.get("createTime")
        update_time = item.get("updateTime")
        
        return {
            'id': unique_id,
            'sub_account_id': sub_account_id,
            'asset': asset,
            'balance': self.convert_to_float(item.get("balance")) or 0.0,
            # Base struct-ийн created_at, updated_at ашиглана
            'created_at': self.convert_epoch_to_iso(create_time) or self.now_iso(),
            'updated_at': self.convert_epoch_to_iso(update_time) or self.now_iso(),
            'deleted_at': None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for balances table"""
        return """
            INSERT INTO balances (
                id, sub_account_id, asset, balance,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(sub_account_id)s, %(asset)s, %(balance)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for balances table"""
        return """
            INSERT INTO balances (
                id, sub_account_id, asset, balance,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(sub_account_id)s, %(asset)s, %(balance)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                sub_account_id = EXCLUDED.sub_account_id,
                asset = EXCLUDED.asset,
                balance = EXCLUDED.balance,
                updated_at = EXCLUDED.updated_at
        """
