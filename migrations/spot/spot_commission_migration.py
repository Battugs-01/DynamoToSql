import uuid
from typing import Dict, Any, List
from utils.migration_base import BaseMigration
from datetime import datetime

class SpotCommissionMigration(BaseMigration):
    def __init__(self, dynamo_conn, postgres_conn, config):
        super().__init__(dynamo_conn, postgres_conn, config)
        self.broker_user_map = {}

    @property
    def dynamo_table_name(self) -> str:
        return "broker-spot-commissions"

    @property
    def postgres_table_name(self) -> str:
        return "spot_commissions"

    def load_broker_user_map(self):
        """Load BrokerUser mapping from PostgreSQL (sub_account_id -> id)"""
        if not self.broker_user_map:
            cursor = self.postgres.get_cursor()
            cursor.execute("SELECT sub_account_id, id FROM broker_users")
            for row in cursor.fetchall():
                self.broker_user_map[row[0]] = row[1]

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        self.load_broker_user_map()
        
        # Get BrokerUser ID via subAccountId
        sub_account_id = item.get('subAccountId')
        broker_user_id = self.broker_user_map.get(sub_account_id)
        
        if not broker_user_id:
            return None

        # Convert timestamps
        fetched_at = self.convert_epoch_to_iso(item.get('fetchedAt'))
        created_at = self.convert_epoch_to_iso(item.get('time'))
        
        # Handle Boolean for isCollected
        is_collected = bool(int(item.get('isCollected', 0)))
        
        # Handle Status as string
        status = str(item.get('status', '0'))

        return {
            'id': str(uuid.uuid4()),
            'created_at': created_at,
            'updated_at': created_at,
            'deleted_at': None,
            
            'broker_user_id': broker_user_id,
            'trade_id': str(item.get('tradeId')),
            'fetched_at': fetched_at,
            'income': item.get('income'),
            'is_collected': is_collected,
            'status': status
        }

    def get_insert_query(self) -> str:
        return f"""
            INSERT INTO {self.postgres_table_name} (
                id, created_at, updated_at, deleted_at,
                broker_user_id, trade_id, fetched_at, income, is_collected, status
            ) VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(broker_user_id)s, %(trade_id)s, %(fetched_at)s, %(income)s, %(is_collected)s, %(status)s
            )
        """

    def get_upsert_query(self) -> str:
        # Since we generate UUIDs, upsert on ID doesn't make much sense unless we use trade_id as key
        # But if a trade can have multiple commissions (unlikely but possible), UUID is safer.
        # However, for consistency with other migrations:
        return self.get_insert_query()
