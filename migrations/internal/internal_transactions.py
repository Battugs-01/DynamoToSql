"""
Internal Transactions table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class InternalTransactionsMigration(BaseMigration):
    """Migration for internal_transactions table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "internal-transactions"
    
    @property
    def postgres_table_name(self) -> str:
        return "internal_transactions"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB internal transaction item to PostgreSQL format"""
        # txnId is required (primary key)
        txn_id = item.get("txnId")
        if not txn_id:
            logger.warning(f"Skipping internal transaction - missing required txnId field")
            return None
        
        # Get timestamp for created_at/updated_at
        timestamp = item.get("timestamp")
        created_timestamp = self.convert_epoch_to_iso(timestamp) if timestamp else self.now_iso()
        
        return {
            'id': txn_id,  # Use txnId as id
            'txn_id': txn_id,
            'amount': self.convert_to_float(item.get("amount")),
            'asset': item.get("asset"),
            'binance_txn_id': item.get("binanceTxnId"),
            'code': item.get("code"),
            'from_id': item.get("fromId"),
            'metadata': self.convert_to_json(item.get("metadata")),
            'to_id': item.get("toId"),
            
            # Timestamps - use DynamoDB timestamp for created_at/updated_at
            'created_at': created_timestamp,
            'updated_at': created_timestamp,
            'deleted_at': None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for internal_transactions table"""
        return """
            INSERT INTO internal_transactions (
                id, txn_id, amount, asset, binance_txn_id, code,
                from_id, metadata, to_id,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(txn_id)s, %(amount)s, %(asset)s, %(binance_txn_id)s, %(code)s,
                %(from_id)s, %(metadata)s, %(to_id)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for internal_transactions table"""
        return """
            INSERT INTO internal_transactions (
                id, txn_id, amount, asset, binance_txn_id, code,
                from_id, metadata, to_id,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(txn_id)s, %(amount)s, %(asset)s, %(binance_txn_id)s, %(code)s,
                %(from_id)s, %(metadata)s, %(to_id)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                txn_id = EXCLUDED.txn_id,
                amount = EXCLUDED.amount,
                asset = EXCLUDED.asset,
                binance_txn_id = EXCLUDED.binance_txn_id,
                code = EXCLUDED.code,
                from_id = EXCLUDED.from_id,
                metadata = EXCLUDED.metadata,
                to_id = EXCLUDED.to_id,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
