"""
withdraw_bans migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging
import uuid

logger = logging.getLogger(__name__)


class WithdrawBansMigration(BaseMigration):
    """Migration for withdraw_bans table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "withdraw-bans"
    
    @property
    def postgres_table_name(self) -> str:
        return "withdraw_bans"

    def get_user_id(self, uid: str) -> str:
        """Get user ID from uid, return the uid if exists in users table"""
        if not uid:
            return None
        
        # Cache user lookups
        if not hasattr(self, '_user_cache'):
            self._user_cache = {}
        
        if uid in self._user_cache:
            return self._user_cache[uid]
        
        try:
            cursor = self.postgres.get_cursor()
            cursor.execute("SELECT id FROM users WHERE id = %s", (uid,))
            result = cursor.fetchone()
            if result:
                self._user_cache[uid] = result[0]
                return result[0]
            else:
                self._user_cache[uid] = uid  # Use uid directly even if not found
                logger.warning(f"User not found for uid: {uid}, using uid as user_id")
                return uid
        except Exception as e:
            logger.error(f"Error getting user ID for uid {uid}: {e}")
            return uid

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB withdraw-bans item to PostgreSQL format
        
        JSON format:
        {
            "uid": "2de82f27-e8b4-4c34-873a-09ae8ba721af",
            "endTime": 1701930425994,
            "reason": "RECOVERED_ASSET_SECURITY",
            "startTime": 1701757625994,
            "status": "CLEANED_BY_SYSTEM"
        }
        """
        # Get or generate ID
        item_id = item.get('id')
        if not item_id:
            # Generate ID from uid
            uid = item.get('uid', '')
            item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"withdraw_ban_{uid}"))
        
        # Get user_id from uid
        uid = item.get('uid')
        user_id = self.get_user_id(uid)
        
        # startTime -> created_at, endTime -> updated_at
        created_at_iso = self.convert_epoch_to_iso(item.get('startTime'))
        updated_at_iso = self.convert_epoch_to_iso(item.get('endTime') or item.get('startTime'))
        
        return {
            'id': item_id,
            'created_at': created_at_iso,
            'updated_at': updated_at_iso,
            'deleted_at': None,
            'user_id': user_id,
            'reason': item.get('reason'),
            'status': item.get('status'),
        }

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for withdraw_bans table"""
        return """
            INSERT INTO withdraw_bans (
                id, created_at, updated_at, deleted_at,
                user_id, reason, status
            )
            VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(user_id)s, %(reason)s, %(status)s
            )
            ON CONFLICT (id) DO NOTHING
        """

    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for withdraw_bans table"""
        return """
            INSERT INTO withdraw_bans (
                id, created_at, updated_at, deleted_at,
                user_id, reason, status
            )
            VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(user_id)s, %(reason)s, %(status)s
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                user_id = EXCLUDED.user_id,
                reason = EXCLUDED.reason,
                status = EXCLUDED.status
        """
