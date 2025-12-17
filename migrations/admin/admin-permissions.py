"""
admin_permissions table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid


class AdminPermissionsMigration(BaseMigration):
    """Migration for admin_permissions table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "admin-permissions"
    
    @property
    def postgres_table_name(self) -> str:
        return "admin_permissions"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB admin_permissions item to PostgreSQL format"""

        return {
            'id': self.get_id(), 
            'name': item.get('sid'),
            'created_at': self.convert_epoch_to_iso(item.get('createdAt')),
            'updated_at': self.convert_epoch_to_iso(item.get('updatedAt')),
            'deleted_at': self.convert_epoch_to_iso(item.get('deletedAt')) if item.get('deletedAt') else None,
            'description': item.get('sid'),
        }

    def get_id(self) -> int:
        """Get the next admin permission ID"""
        if not hasattr(self, '_admin_permission_id_counter'):
            self._admin_permission_id_counter = 1
        else:
            self._admin_permission_id_counter += 1
        return self._admin_permission_id_counter

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for admin_permissions table"""
        return """
            INSERT INTO admin_permissions (
               id, name, created_at, updated_at, deleted_at, description
            )
            VALUES (%(id)s, %(name)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(description)s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at,
                description = EXCLUDED.description
        """
