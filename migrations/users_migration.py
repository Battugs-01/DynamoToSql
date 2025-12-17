"""
Users table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration


class UsersMigration(BaseMigration):
    """Migration for users table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "xmeta-users"
    
    @property
    def postgres_table_name(self) -> str:
        return "users"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB user item to PostgreSQL format"""
        # Skip users without email (required field in PostgreSQL)
        email = item.get("email")
        if not email:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Skipping user {item.get('uid')} - missing required email field")
            return None
        
        return {
            'id': item.get("uid"),
            'first_name': item.get("firstName"),
            'last_name': item.get("lastName"),
            'email': email,
            'created_at': self.convert_epoch_to_iso(item.get("createdAt")),
            'updated_at': self.convert_epoch_to_iso(item.get("updatedAt")),
            'status': item.get("status"),
            'can_trade': self.convert_to_boolean(item.get("canTrade")),
            'can_withdraw': self.convert_to_boolean(item.get("canWithdraw")),
            'is_whitelist_enabled': self.convert_to_boolean(item.get("isWhitelistEnabled")),
            'kyc_level': item.get("kycLevel"),
            'vip_level': item.get("vipLevel"),
            'binance_email': item.get("binanceEmail"),
            'sub_account_id': item.get("subAccountId"),
            'meta_data': self.convert_to_json(item.get("metaData"))
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for users table"""
        return """
            INSERT INTO users (
                id, first_name, last_name, email, created_at, updated_at,
                status, can_trade, can_withdraw, is_whitelist_enabled,
                kyc_level, vip_level, binance_email, sub_account_id, meta_data
            )
            VALUES (%(id)s, %(first_name)s, %(last_name)s, %(email)s, %(created_at)s, %(updated_at)s,
                    %(status)s, %(can_trade)s, %(can_withdraw)s, %(is_whitelist_enabled)s,
                    %(kyc_level)s, %(vip_level)s, %(binance_email)s, %(sub_account_id)s, %(meta_data)s)
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query - UPDATE existing records on conflict"""
        return """
            INSERT INTO users (
                id, first_name, last_name, email, created_at, updated_at,
                status, can_trade, can_withdraw, is_whitelist_enabled,
                kyc_level, vip_level, binance_email, sub_account_id, meta_data
            )
            VALUES (%(id)s, %(first_name)s, %(last_name)s, %(email)s, %(created_at)s, %(updated_at)s,
                    %(status)s, %(can_trade)s, %(can_withdraw)s, %(is_whitelist_enabled)s,
                    %(kyc_level)s, %(vip_level)s, %(binance_email)s, %(sub_account_id)s, %(meta_data)s)
            ON CONFLICT (id) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                email = EXCLUDED.email,
                updated_at = EXCLUDED.updated_at,
                status = EXCLUDED.status,
                can_trade = EXCLUDED.can_trade,
                can_withdraw = EXCLUDED.can_withdraw,
                is_whitelist_enabled = EXCLUDED.is_whitelist_enabled,
                kyc_level = EXCLUDED.kyc_level,
                vip_level = EXCLUDED.vip_level,
                binance_email = EXCLUDED.binance_email,
                sub_account_id = EXCLUDED.sub_account_id,
                meta_data = EXCLUDED.meta_data
        """