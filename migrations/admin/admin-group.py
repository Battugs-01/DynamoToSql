"""
admin_groups table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration


class AdminGroupMigration(BaseMigration):
    """Migration for admin_groups table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "admin-groups"
    
    @property
    def postgres_table_name(self) -> str:
        return "admin_groups"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB admin_groups item to PostgreSQL format"""
        return {
            'id': self.get_id(),
            'name': item.get('gid'),
            'created_at': self.convert_epoch_to_iso(item.get('createdAt')),
            'updated_at': self.convert_epoch_to_iso(item.get('updatedAt')),
            'deleted_at': self.convert_epoch_to_iso(item.get('deletedAt')) if item.get('deletedAt') else None,
        }

    def get_id(self) -> int:
        """Get the next admin group ID"""
        if not hasattr(self, '_admin_group_id_counter'):
            self._admin_group_id_counter = 1
        else:
            self._admin_group_id_counter += 1
        return self._admin_group_id_counter

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for admin_groups table (skip existing)"""
        return """
            INSERT INTO admin_groups (
               id, name, created_at, updated_at, deleted_at
            )
            VALUES (%(id)s, %(name)s, %(created_at)s, %(updated_at)s, %(deleted_at)s)
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for admin_groups table (update existing)"""
        return """
            INSERT INTO admin_groups (
               id, name, created_at, updated_at, deleted_at
            )
            VALUES (%(id)s, %(name)s, %(created_at)s, %(updated_at)s, %(deleted_at)s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
