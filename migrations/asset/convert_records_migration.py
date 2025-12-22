"""
Convert Records Migration Script
=================================
DynamoDB: convert-records → PostgreSQL: convert_records
"""
import logging
from typing import Dict, Any

from utils.migration_base import BaseMigration

logger = logging.getLogger(__name__)


class ConvertRecordsMigration(BaseMigration):
    """Migration for convert_records table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "convert-records"
    
    @property
    def postgres_table_name(self) -> str:
        return "convert_records"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB convert record item to PostgreSQL format"""
        record_id = item.get("id")
        uid = item.get("uid")
        
        if not record_id:
            logger.warning(f"Skipping convert record - missing id")
            return None
        
        if not uid:
            logger.warning(f"Skipping convert record {record_id} - missing uid")
            return None
        
        create_time = item.get("createTime")
        update_time = item.get("updateTime")
        
        return {
            'id': record_id,
            'user_id': uid,
            'from_amount': self.convert_to_float(item.get("fromAmount")) or 0.0,
            'from_asset': item.get("fromAsset"),
            'from_txn_id': item.get("fromTxnId"),
            'to_amount': self.convert_to_float(item.get("toAmount")) or 0.0,
            'to_asset': item.get("toAsset"),
            'to_txn_id': item.get("toTxnId"),
            'post_date': item.get("postDate"),
            'rate': item.get("rate"),
            'status': item.get("status"),
            # Base struct fields
            'created_at': self.convert_epoch_to_iso(create_time) or self.now_iso(),
            'updated_at': self.convert_epoch_to_iso(update_time) or self.now_iso(),
            'deleted_at': None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for convert_records table"""
        return """
            INSERT INTO convert_records (
                id, user_id, from_amount, from_asset, from_txn_id,
                to_amount, to_asset, to_txn_id, post_date, rate, status,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(user_id)s, %(from_amount)s, %(from_asset)s, %(from_txn_id)s,
                %(to_amount)s, %(to_asset)s, %(to_txn_id)s, %(post_date)s, %(rate)s, %(status)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for convert_records table"""
        return """
            INSERT INTO convert_records (
                id, user_id, from_amount, from_asset, from_txn_id,
                to_amount, to_asset, to_txn_id, post_date, rate, status,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(user_id)s, %(from_amount)s, %(from_asset)s, %(from_txn_id)s,
                %(to_amount)s, %(to_asset)s, %(to_txn_id)s, %(post_date)s, %(rate)s, %(status)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                from_amount = EXCLUDED.from_amount,
                from_asset = EXCLUDED.from_asset,
                from_txn_id = EXCLUDED.from_txn_id,
                to_amount = EXCLUDED.to_amount,
                to_asset = EXCLUDED.to_asset,
                to_txn_id = EXCLUDED.to_txn_id,
                post_date = EXCLUDED.post_date,
                rate = EXCLUDED.rate,
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at
        """
