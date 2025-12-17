"""
admin_users table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any, Optional
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class AdminUsersMigration(BaseMigration):
    """Migration for admin_users table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "admin-users"
    
    @property
    def postgres_table_name(self) -> str:
        return "admin_users"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB admin_users item to PostgreSQL format"""
        # Get admin_group_id from group name
        group_name = item.get('group')
        admin_group_id = None
        if group_name:
            admin_group_id = self.get_admin_group_id(group_name)
            if not admin_group_id:
                logger.warning(f"Admin group '{group_name}' not found for user {item.get('email')}")
        
        # Convert isEnabled string to boolean
        is_enabled = item.get('isEnabled', 'true')
        if isinstance(is_enabled, str):
            is_enabled = is_enabled.lower() == 'true'
        else:
            is_enabled = bool(is_enabled)
        
        return {
            'id': item.get('uid'),
            'email': item.get('email'),
            'admin_group_id': admin_group_id,
            'status': item.get('status'),
            'is_enabled': is_enabled,
            'user_create_date': item.get('userCreateDate'),
            'created_at': self.convert_epoch_to_iso(item.get('createdAt')),
            'updated_at': self.convert_epoch_to_iso(item.get('updatedAt')),
            'deleted_at': self.convert_epoch_to_iso(item.get('deletedAt')) if item.get('deletedAt') else None,
        }
    
    def get_admin_group_id(self, group_name: str) -> Optional[int]:
        """Get admin_group_id from group name"""
        try:
            cursor = self.postgres.get_cursor()
            cursor.execute(
                "SELECT id FROM admin_groups WHERE name = %s",
                (group_name,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                logger.warning(f"Admin group '{group_name}' not found in admin_groups table")
                return None
        except Exception as e:
            logger.error(f"Error looking up admin group '{group_name}': {str(e)}")
            return None
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for admin_users table (skip existing)"""
        return """
            INSERT INTO admin_users (
                id, email, admin_group_id, status, is_enabled, 
                user_create_date, created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(email)s, %(admin_group_id)s, %(status)s, %(is_enabled)s,
                %(user_create_date)s, %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for admin_users table (update existing)"""
        return """
            INSERT INTO admin_users (
                id, email, admin_group_id, status, is_enabled, 
                user_create_date, created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(email)s, %(admin_group_id)s, %(status)s, %(is_enabled)s,
                %(user_create_date)s, %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                admin_group_id = EXCLUDED.admin_group_id,
                status = EXCLUDED.status,
                is_enabled = EXCLUDED.is_enabled,
                user_create_date = EXCLUDED.user_create_date,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
