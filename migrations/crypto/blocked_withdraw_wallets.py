"""
blocked_withdraw_wallets migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging
import uuid

logger = logging.getLogger(__name__)


class BlockedWithdrawWalletsMigration(BaseMigration):
    """Migration for blocked_withdraw_wallets table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "blocked-withdraw-wallets"
    
    @property
    def postgres_table_name(self) -> str:
        return "blocked_withdraw_wallets"

    def get_admin_user_id(self, uid: str) -> str:
        """Get admin user ID from uid, return the uid if exists in admin_users"""
        if not uid:
            return None
        
        # Cache admin user lookups
        if not hasattr(self, '_admin_user_cache'):
            self._admin_user_cache = {}
        
        if uid in self._admin_user_cache:
            return self._admin_user_cache[uid]
        
        try:
            cursor = self.postgres.get_cursor()
            cursor.execute("SELECT id FROM admin_users WHERE id = %s", (uid,))
            result = cursor.fetchone()
            if result:
                self._admin_user_cache[uid] = result[0]
                return result[0]
            else:
                self._admin_user_cache[uid] = None
                logger.warning(f"Admin user not found for uid: {uid}")
                return None
        except Exception as e:
            logger.error(f"Error getting admin user ID for uid {uid}: {e}")
            return None

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB blocked-withdraw-wallets item to PostgreSQL format
        
        JSON format:
        {
            "address": "TG9LD6wcaKa3zAUY1NnS3P2pvGthHEDuNc",
            "network": "TRX",
            "createdUser": {
                "email": "erdenekhishig@x-meta.com",
                "uid": "02dc5a9d-8a99-41e8-aa3b-2fcee21f60eb"
            },
            "createTime": 1758771316127,
            "reason": "global prime investment...",
            "status": 1,
            "updatetime": 1758771316127
        }
        """
        # Get or generate ID
        item_id = item.get('id')
        if not item_id:
            # Generate ID from address + network combination
            item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{item.get('address', '')}_{item.get('network', '')}"))
        
        # Get created_user_id from createdUser object and verify it exists in admin_users
        created_user = item.get('createdUser', {})
        created_user_uid = created_user.get('uid') if isinstance(created_user, dict) else None
        created_user_id = self.get_admin_user_id(created_user_uid)
        
        created_at_iso = self.convert_epoch_to_iso(item.get('createTime'))
        updated_at_iso = self.convert_epoch_to_iso(item.get('updatetime') or item.get('createTime'))
        
        return {
            'id': item_id,
            'created_at': created_at_iso,
            'updated_at': updated_at_iso,
            'deleted_at': None,
            'address': item.get('address'),
            'network': item.get('network'),
            'created_user_id': created_user_id,
            'reason': item.get('reason'),
            'status': self.convert_to_integer(item.get('status')),
        }

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for blocked_withdraw_wallets table"""
        return """
            INSERT INTO blocked_withdraw_wallets (
                id, created_at, updated_at, deleted_at,
                address, network, created_user_id, reason, status
            )
            VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(address)s, %(network)s, %(created_user_id)s, %(reason)s, %(status)s
            )
            ON CONFLICT (id) DO NOTHING
        """

    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for blocked_withdraw_wallets table"""
        return """
            INSERT INTO blocked_withdraw_wallets (
                id, created_at, updated_at, deleted_at,
                address, network, created_user_id, reason, status
            )
            VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(address)s, %(network)s, %(created_user_id)s, %(reason)s, %(status)s
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                address = EXCLUDED.address,
                network = EXCLUDED.network,
                created_user_id = EXCLUDED.created_user_id,
                reason = EXCLUDED.reason,
                status = EXCLUDED.status
        """
