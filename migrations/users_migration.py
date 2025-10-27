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
        return {
            'id': item.get("uid"),
            'first_name': item.get("firstName"),
            'last_name': item.get("lastName"),
            'email': item.get("email"),
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
