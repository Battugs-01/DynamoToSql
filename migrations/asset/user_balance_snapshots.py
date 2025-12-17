"""
User Balance Snapshots table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class UserBalanceSnapshotsMigration(BaseMigration):
    """Migration for user_balance_snapshots table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "user-balances-snapshots"
    
    @property
    def postgres_table_name(self) -> str:
        return "user_balance_snapshots"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB user balance snapshot item to PostgreSQL format"""
        # userId is required
        user_id = item.get("userId")
        if not user_id:
            logger.warning(f"Skipping user balance snapshot - missing required userId field")
            return None
        
        # Check if user exists in PostgreSQL users table (foreign key constraint)
        if not hasattr(self, '_valid_user_ids'):
            try:
                import psycopg2
                conn = psycopg2.connect(host='localhost', database='xmeta', user='postgres', password='Pass1234!')
                cur = conn.cursor()
                cur.execute('SELECT id FROM users;')
                self._valid_user_ids = set([row[0] for row in cur.fetchall()])
                cur.close()
                conn.close()
                logger.info(f"Loaded {len(self._valid_user_ids)} valid user IDs from PostgreSQL")
            except Exception as e:
                logger.warning(f"Could not load user IDs from PostgreSQL: {e}")
                self._valid_user_ids = None
        
        # Skip if user doesn't exist in users table
        if self._valid_user_ids is not None and user_id not in self._valid_user_ids:
            logger.debug(f"Skipping user balance snapshot for userId {user_id} - user not found in users table")
            return None
        
        # Generate unique ID from userId + date
        date = item.get("date", "")
        record_id = f"{user_id}_{date}" if date else user_id
        
        # Get snapshotTime for timestamps
        snapshot_time = item.get("snapshotTime")
        created_timestamp = self.convert_epoch_to_iso(snapshot_time) if snapshot_time else self.now_iso()
        
        return {
            'id': record_id,
            'user_id': user_id,
            'date': item.get("date"),
            'sub_account_id': item.get("subAccountId"),
            'snapshot_time': snapshot_time,
            'bank_balances': self.convert_to_json(item.get("bankBalances")),
            'futures_balances': self.convert_to_json(item.get("futuresBalances")),
            'spot_balances': self.convert_to_json(item.get("spotBalances")),
            'overall': self.convert_to_json(item.get("overall")),
            'mnt_valuation': self.convert_to_float(item.get("mntValuation")),
            'usdt_valuation': self.convert_to_float(item.get("usdtValuation")),
            
            # Timestamps
            'created_at': created_timestamp,
            'updated_at': created_timestamp,
            'deleted_at': None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for user_balance_snapshots table"""
        return """
            INSERT INTO user_balance_snapshots (
                id, user_id, date, sub_account_id, snapshot_time,
                bank_balances, futures_balances, spot_balances, overall,
                mnt_valuation, usdt_valuation, created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(user_id)s, %(date)s, %(sub_account_id)s, %(snapshot_time)s,
                %(bank_balances)s, %(futures_balances)s, %(spot_balances)s, %(overall)s,
                %(mnt_valuation)s, %(usdt_valuation)s, %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for user_balance_snapshots table"""
        return """
            INSERT INTO user_balance_snapshots (
                id, user_id, date, sub_account_id, snapshot_time,
                bank_balances, futures_balances, spot_balances, overall,
                mnt_valuation, usdt_valuation, created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(user_id)s, %(date)s, %(sub_account_id)s, %(snapshot_time)s,
                %(bank_balances)s, %(futures_balances)s, %(spot_balances)s, %(overall)s,
                %(mnt_valuation)s, %(usdt_valuation)s, %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                date = EXCLUDED.date,
                sub_account_id = EXCLUDED.sub_account_id,
                snapshot_time = EXCLUDED.snapshot_time,
                bank_balances = EXCLUDED.bank_balances,
                futures_balances = EXCLUDED.futures_balances,
                spot_balances = EXCLUDED.spot_balances,
                overall = EXCLUDED.overall,
                mnt_valuation = EXCLUDED.mnt_valuation,
                usdt_valuation = EXCLUDED.usdt_valuation,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
