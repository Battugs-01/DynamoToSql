"""
Internal Transactions Record table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class InternalTransactionsRecordMigration(BaseMigration):
    """Migration for internal-transaction-record table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "internal-transaction-records"
    
    @property
    def postgres_table_name(self) -> str:
        return "internal_transaction_records"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB internal transaction record item to PostgreSQL format"""
        # txnId is required (primary key)
        txn_id = item.get("txnId")
        if not txn_id:
            logger.warning(f"Skipping internal transaction record - missing required txnId field")
            return None
        
        # Get timestamp for created_at/updated_at
        timestamp = item.get("timestamp")
        created_timestamp = self.convert_epoch_to_iso(timestamp) if timestamp else self.now_iso()
        
        # Amount is string in this table
        amount = item.get("amount")
        if amount is not None:
            amount = str(amount)
        
        return {
            'id': txn_id,  # Use txnId as id
            'txn_id': txn_id,
            'amount': amount,
            'asset': item.get("asset"),
            'client_tran_id': item.get("clientTranId"),
            'from_id': item.get("fromId"),
            'status': item.get("status"),
            'to_id': item.get("toId"),
            
            # Timestamps - use DynamoDB timestamp for created_at/updated_at
            'created_at': created_timestamp,
            'updated_at': created_timestamp,
            'deleted_at': None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for internal_transaction_records table"""
        return """
            INSERT INTO internal_transaction_records (
                id, txn_id, amount, asset, client_tran_id,
                from_id, status, to_id,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(txn_id)s, %(amount)s, %(asset)s, %(client_tran_id)s,
                %(from_id)s, %(status)s, %(to_id)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for internal_transaction_records table"""
        return """
            INSERT INTO internal_transaction_records (
                id, txn_id, amount, asset, client_tran_id,
                from_id, status, to_id,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(txn_id)s, %(amount)s, %(asset)s, %(client_tran_id)s,
                %(from_id)s, %(status)s, %(to_id)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                txn_id = EXCLUDED.txn_id,
                amount = EXCLUDED.amount,
                asset = EXCLUDED.asset,
                client_tran_id = EXCLUDED.client_tran_id,
                from_id = EXCLUDED.from_id,
                status = EXCLUDED.status,
                to_id = EXCLUDED.to_id,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
