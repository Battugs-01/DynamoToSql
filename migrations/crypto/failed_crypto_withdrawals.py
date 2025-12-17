"""
failed_crypto_withdrawals migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class FailedCryptoWithdrawalsMigration(BaseMigration):
    """Migration for failed_crypto_withdrawals table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "failed-crypto-withdrawals"
    
    @property
    def postgres_table_name(self) -> str:
        return "failed_crypto_withdrawals"

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB failed-crypto-withdrawals item to PostgreSQL format
        
        JSON format:
        {
            "id": "e83ca05ba80d45e29074f265be9cef91",
            "createdAt": 1706891006131,
            "feeRefundStatus": 1,
            "mainRefundStatus": 1,
            "resolvedAt": 1707114174498,
            "resolvedBy": "394a159c-c0e1-7043-2c9a-7f4a2ddb4799",
            "status": "REFUNDED",
            "type": "NETWORK_BUSY",
            "uid": "9beb766a-161b-44f6-847b-9b9c5173d1c1"
        }
        """
        created_at_iso = self.convert_epoch_to_iso(item.get('createdAt'))
        
        return {
            'id': item.get('id'),
            'created_at': created_at_iso,
            'updated_at': created_at_iso,
            'deleted_at': None,
            'uid': item.get('uid'),  # User ID
            'fee_refund_status': self.convert_to_integer(item.get('feeRefundStatus')),
            'main_refund_status': self.convert_to_integer(item.get('mainRefundStatus')),
            'resolved_at': item.get('resolvedAt'),  # Keep as epoch timestamp (int64)
            'resolved_by': item.get('resolvedBy'),  # Admin user ID who resolved
            'status': item.get('status'),  # e.g., "REFUNDED"
            'type': item.get('type'),  # e.g., "NETWORK_BUSY"
        }

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for failed_crypto_withdrawals table"""
        return """
            INSERT INTO failed_crypto_withdrawals (
                id, created_at, updated_at, deleted_at,
                uid, fee_refund_status, main_refund_status,
                resolved_at, resolved_by, status, type
            )
            VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(uid)s, %(fee_refund_status)s, %(main_refund_status)s,
                %(resolved_at)s, %(resolved_by)s, %(status)s, %(type)s
            )
            ON CONFLICT (id) DO NOTHING
        """

    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for failed_crypto_withdrawals table"""
        return """
            INSERT INTO failed_crypto_withdrawals (
                id, created_at, updated_at, deleted_at,
                uid, fee_refund_status, main_refund_status,
                resolved_at, resolved_by, status, type
            )
            VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(uid)s, %(fee_refund_status)s, %(main_refund_status)s,
                %(resolved_at)s, %(resolved_by)s, %(status)s, %(type)s
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                uid = EXCLUDED.uid,
                fee_refund_status = EXCLUDED.fee_refund_status,
                main_refund_status = EXCLUDED.main_refund_status,
                resolved_at = EXCLUDED.resolved_at,
                resolved_by = EXCLUDED.resolved_by,
                status = EXCLUDED.status,
                type = EXCLUDED.type
        """
