"""
banks table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid


class BanksMigration(BaseMigration):
    """Migration for banks table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "banks"
    
    @property
    def postgres_table_name(self) -> str:
        return "banks"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB bank item to PostgreSQL format"""
        # Use code as a deterministic ID base to avoid conflicts
        bank_code = item.get('code')
        return {
            'id': str(uuid.uuid4()),
            'code': bank_code,
            'created_at': self.now_iso() if not item.get('createdAt') else self.convert_epoch_to_iso(item.get('createdAt')),
            'updated_at': self.now_iso() if not item.get('updatedAt') else self.convert_epoch_to_iso(item.get('updatedAt')),
            'clearing_code': item.get('clearingCode'),
            'icon': item.get('icon'),
            'is_enabled': self.convert_to_boolean(item.get('isEnabled')),
            'length': item.get('length'),
            'name_en': item.get('nameEn'),
            'name_mn': item.get('nameMn'),
            'order': self.convert_to_integer(item.get('order'))
        }

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for banks table"""
        return """
            INSERT INTO banks (
               id, code, created_at, updated_at, clearing_code, icon, is_enabled, length, name_en, name_mn, "order"
            )
            VALUES (%(id)s, %(code)s, %(created_at)s, %(updated_at)s, %(clearing_code)s, %(icon)s, %(is_enabled)s, %(length)s, %(name_en)s, %(name_mn)s, %(order)s)
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                clearing_code = EXCLUDED.clearing_code,
                icon = EXCLUDED.icon,
                is_enabled = EXCLUDED.is_enabled,
                length = EXCLUDED.length,
                name_en = EXCLUDED.name_en,
                name_mn = EXCLUDED.name_mn,
                "order" = EXCLUDED."order"
        """
