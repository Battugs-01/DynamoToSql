"""
crypto_withdraw_transfers table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class WithdrawTransfersMigration(BaseMigration):
    """Migration for crypto_withdraw_transfers table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "withdraw-transfers"
    
    @property
    def postgres_table_name(self) -> str:
        return "crypto_withdraw_transfers"

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB withdraw-transfers item to PostgreSQL format"""
        # Get user ID from uid
        user_id = self.get_user_id_by_uuid(item.get('uid'))
        
        # Get coin info
        coin_symbol = item.get('coin') or ''
        coin_id = self.get_coin_id(coin_symbol)
        
        if not coin_id and coin_symbol:
            logger.warning(f"Coin '{coin_symbol}' not found for transfer {item.get('id')}, setting coin_id to NULL")

        return {
            'id': item.get('id'),
            'created_at': self.convert_epoch_to_iso(item.get('transferTime')),
            'updated_at': self.convert_epoch_to_iso(item.get('transferTime')),
            'deleted_at': None,
            'user_id': user_id,
            'address': item.get('address'),
            'amount': self.convert_to_float(item.get('amount')) or 0.0,
            'apply_time': item.get('applyTime') or '',
            'coin_id': coin_id,
            'coin_symbol': coin_symbol,
            'complete_time': item.get('completeTime') or '',
            'confirm_no': self.convert_to_integer(item.get('confirmNo')) or 0,
            'email_sent': self.convert_to_integer(item.get('emailSent')) or 0,
            'history_id': item.get('historyId'),
            'info': item.get('info'),
            'network': item.get('network') or '',
            'status': self.convert_to_integer(item.get('status')) or 0,
            'transaction_fee': self.convert_to_float(item.get('transactionFee')) or 0.0,
            'transfer_time': item.get('transferTime') or 0,
            'transfer_type': self.convert_to_integer(item.get('transferType')) or 0,
            'tx_id': item.get('txId') or '',
            'tx_key': item.get('txKey') or '',
            'wallet_type': self.convert_to_integer(item.get('walletType')) or 0,
            'withdraw_order_id': item.get('withdrawOrderId') or '',
        }

    def get_user_id_by_uuid(self, user_uuid: str):
        """Get user ID directly from UUID"""
        if not user_uuid:
            return None
        
        # Cache user lookups
        if not hasattr(self, '_user_cache'):
            self._user_cache = {}
        
        if user_uuid in self._user_cache:
            return self._user_cache[user_uuid]
        
        try:
            cursor = self.postgres.get_cursor()
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_uuid,))
            result = cursor.fetchone()
            if result:
                self._user_cache[user_uuid] = result[0]
                return result[0]
            else:
                self._user_cache[user_uuid] = None
                return None
        except Exception as e:
            logger.error(f"Error getting user ID for uuid {user_uuid}: {e}")
            return None

    def get_coin_id(self, coin: str) -> str:
        """Get coin ID from coin symbol"""
        if not coin:
            return None
        
        # Cache coin lookups
        if not hasattr(self, '_coin_cache'):
            self._coin_cache = {}
        
        if coin in self._coin_cache:
            return self._coin_cache[coin]
        
        try:
            cursor = self.postgres.get_cursor()
            cursor.execute("SELECT id FROM coins WHERE coin = %s", (coin,))
            result = cursor.fetchone()
            if result:
                coin_id = str(result[0])
                self._coin_cache[coin] = coin_id
                return coin_id
            else:
                self._coin_cache[coin] = None
                return None
        except Exception as e:
            logger.error(f"Error getting coin ID for coin {coin}: {e}")
            return None

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for crypto_withdraw_transfers table"""
        return """
            INSERT INTO crypto_withdraw_transfers (
               id, created_at, updated_at, deleted_at, user_id, address, amount, apply_time, coin_id, coin_symbol, complete_time, confirm_no, email_sent, history_id, info, network, status, transaction_fee, transfer_time, transfer_type, tx_id, tx_key, wallet_type, withdraw_order_id
            )
            VALUES (%(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(user_id)s, %(address)s, %(amount)s, %(apply_time)s, %(coin_id)s, %(coin_symbol)s, %(complete_time)s, %(confirm_no)s, %(email_sent)s, %(history_id)s, %(info)s, %(network)s, %(status)s, %(transaction_fee)s, %(transfer_time)s, %(transfer_type)s, %(tx_id)s, %(tx_key)s, %(wallet_type)s, %(withdraw_order_id)s)
            ON CONFLICT (id) DO UPDATE SET
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at,
                user_id = EXCLUDED.user_id,
                address = EXCLUDED.address,
                amount = EXCLUDED.amount,
                apply_time = EXCLUDED.apply_time,
                coin_id = EXCLUDED.coin_id,
                coin_symbol = EXCLUDED.coin_symbol,
                complete_time = EXCLUDED.complete_time,
                confirm_no = EXCLUDED.confirm_no,
                email_sent = EXCLUDED.email_sent,
                history_id = EXCLUDED.history_id,
                info = EXCLUDED.info,
                network = EXCLUDED.network,
                status = EXCLUDED.status,
                transaction_fee = EXCLUDED.transaction_fee,
                transfer_time = EXCLUDED.transfer_time,
                transfer_type = EXCLUDED.transfer_type,
                tx_id = EXCLUDED.tx_id,
                tx_key = EXCLUDED.tx_key,
                wallet_type = EXCLUDED.wallet_type,
                withdraw_order_id = EXCLUDED.withdraw_order_id
        """
