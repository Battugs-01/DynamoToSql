"""
delisted_coin_transfers migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging
import uuid

logger = logging.getLogger(__name__)


class DelistedCoinTransfersMigration(BaseMigration):
    """Migration for delisted_coin_transfers table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "delist-coin-transfers"
    
    @property
    def postgres_table_name(self) -> str:
        return "delisted_coin_transfers"

    def get_user_id(self, sub_account_id: str) -> str:
        """Get user ID from sub_account_id"""
        if not sub_account_id:
            return None
        
        # Cache user lookups
        if not hasattr(self, '_user_cache'):
            self._user_cache = {}
        
        if sub_account_id in self._user_cache:
            return self._user_cache[sub_account_id]
        
        try:
            cursor = self.postgres.get_cursor()
            cursor.execute("SELECT id FROM users WHERE sub_account_id = %s", (sub_account_id,))
            result = cursor.fetchone()
            if result:
                self._user_cache[sub_account_id] = result[0]
                return result[0]
            else:
                self._user_cache[sub_account_id] = None
                logger.warning(f"User not found for sub_account_id: {sub_account_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting user ID for sub_account_id {sub_account_id}: {e}")
            return None

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB delist-coin-transfers item to PostgreSQL format
        
        JSON format:
        {
            "subAccountId": "3733090415562793728",
            "asset": "ALPACA",
            "amount": "1.0658",
            "createTime": 1746154700172,
            "price": "0.244310795",
            "returnAmount": "0.260386445",
            "returnAsset": "USDT",
            "returnTxnId": null,
            "status": "PENDING",
            "txnId": "258845759297",
            "usdtValuation": "0.34582848450000003"
        }
        """
        # Get or generate ID
        item_id = item.get('id')
        if not item_id:
            # Generate ID from txnId
            txn_id = item.get('txnId', '')
            item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"delist_{txn_id}"))
        
        # Get user_id from subAccountId
        sub_account_id = item.get('subAccountId')
        user_id = self.get_user_id(sub_account_id)
        
        created_at_iso = self.convert_epoch_to_iso(item.get('createTime'))
        
        return {
            'id': item_id,
            'created_at': created_at_iso,
            'updated_at': created_at_iso,
            'deleted_at': None,
            'user_id': user_id,
            'asset': item.get('asset'),
            'amount': self.convert_to_float(item.get('amount')),
            'price': self.convert_to_float(item.get('price')),
            'return_amount': self.convert_to_float(item.get('returnAmount')),
            'return_asset': item.get('returnAsset'),
            'return_txn_id': item.get('returnTxnId'),
            'status': item.get('status'),
            'txn_id': item.get('txnId'),
            'usdt_valuation': self.convert_to_float(item.get('usdtValuation')),
        }

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for delisted_coin_transfers table"""
        return """
            INSERT INTO delisted_coin_transfers (
                id, created_at, updated_at, deleted_at,
                user_id, asset, amount, price, return_amount, return_asset,
                return_txn_id, status, txn_id, usdt_valuation
            )
            VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(user_id)s, %(asset)s, %(amount)s, %(price)s, %(return_amount)s, %(return_asset)s,
                %(return_txn_id)s, %(status)s, %(txn_id)s, %(usdt_valuation)s
            )
            ON CONFLICT (id) DO NOTHING
        """

    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for delisted_coin_transfers table"""
        return """
            INSERT INTO delisted_coin_transfers (
                id, created_at, updated_at, deleted_at,
                user_id, asset, amount, price, return_amount, return_asset,
                return_txn_id, status, txn_id, usdt_valuation
            )
            VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(user_id)s, %(asset)s, %(amount)s, %(price)s, %(return_amount)s, %(return_asset)s,
                %(return_txn_id)s, %(status)s, %(txn_id)s, %(usdt_valuation)s
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                user_id = EXCLUDED.user_id,
                asset = EXCLUDED.asset,
                amount = EXCLUDED.amount,
                price = EXCLUDED.price,
                return_amount = EXCLUDED.return_amount,
                return_asset = EXCLUDED.return_asset,
                return_txn_id = EXCLUDED.return_txn_id,
                status = EXCLUDED.status,
                txn_id = EXCLUDED.txn_id,
                usdt_valuation = EXCLUDED.usdt_valuation
        """
