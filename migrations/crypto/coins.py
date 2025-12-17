"""
admin_groups table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid


class CoinsMigration(BaseMigration):
    """Migration for coins table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "Coins"
    
    @property
    def postgres_table_name(self) -> str:
        return "coins"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB admin_groups item to PostgreSQL format"""
        # Get permission IDs from permission names
        
        return {
            'id': self.get_id(),
            'coin': item.get('coin'),
            'name': item.get('name'),
            'image': item.get('image'),
            'image_name': item.get('imageName'),
            'is_enabled': item.get('isEnabled'),
            'is_featured': item.get('isFeatured'),
            'is_legal_money': self.convert_to_boolean(item.get('isLegalMoney')),
            'deposit_all_enable': self.convert_to_boolean(item.get('depositAllEnable')),
            'withdraw_all_enable': self.convert_to_boolean(item.get('withdrawAllEnable')),
            'trading': self.convert_to_boolean(item.get('trading')),
            'network_list': self.convert_to_json(item.get('networkList')),
            'created_at': self.now_iso(),
            'updated_at': self.now_iso(),
            'deleted_at': None,
        }

    def get_id(self) -> int:
        """Get the next coin ID"""
        if not hasattr(self, '_coin_id_counter'):
            self._coin_id_counter = 1
        else:
            self._coin_id_counter += 1
        return self._coin_id_counter

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for coins table"""
        return """
            INSERT INTO coins (
               id, coin, name, image, image_name, is_enabled, is_featured, is_legal_money, deposit_all_enable, withdraw_all_enable, trading, network_list, created_at, updated_at, deleted_at
            )
            VALUES (%(id)s, %(coin)s, %(name)s, %(image)s, %(image_name)s, %(is_enabled)s, %(is_featured)s, %(is_legal_money)s, %(deposit_all_enable)s, %(withdraw_all_enable)s, %(trading)s, %(network_list)s, %(created_at)s, %(updated_at)s, %(deleted_at)s)
            ON CONFLICT (id) DO UPDATE SET
                coin = EXCLUDED.coin,
                name = EXCLUDED.name,
                image = EXCLUDED.image,
                image_name = EXCLUDED.image_name,
                is_enabled = EXCLUDED.is_enabled,
                is_featured = EXCLUDED.is_featured,
                is_legal_money = EXCLUDED.is_legal_money,
                deposit_all_enable = EXCLUDED.deposit_all_enable,
                withdraw_all_enable = EXCLUDED.withdraw_all_enable,
                trading = EXCLUDED.trading,
                network_list = EXCLUDED.network_list,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
