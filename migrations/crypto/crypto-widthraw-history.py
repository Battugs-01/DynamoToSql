"""
crypto_withdraw_histories migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class CryptoWithdrawHistoryMigration(BaseMigration):
    """Migration for crypto_withdraw_history table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "withdraw-history"
    
    @property
    def postgres_table_name(self) -> str:
        return "crypto_withdraw_histories"

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB withdraw_history item to PostgreSQL format"""
        sub_account_id = item.get('subAccountId')
        
        # Get user ID
        user_id = self.get_user_id(sub_account_id)
        
        # 'asset' is the coin code/key
        coin_symbol = item.get('asset') or ''
        coin_id = self.get_coin_id(coin_symbol)
        
        if not coin_id and coin_symbol:
            logger.warning(f"Coin '{coin_symbol}' not found for withdraw {item.get('id')}, setting coin_id to NULL")

        tx_type = item.get('type', '').upper()
        is_crypto = tx_type == 'CRYPTO'
        if not is_crypto:
            # Only migrate CRYPTO records
            return None

        address_val = item.get('address')
        created_at_iso = self.convert_epoch_to_iso(item.get('requestTime'))

        return {
            'id': item.get('id') or item.get('uid') or item.get('txnId'),
            'created_at': created_at_iso,
            'updated_at': created_at_iso,
            'deleted_at': None,
            'user_id': user_id,
            'address': address_val if is_crypto and address_val != '' else None,
            'address_tag': item.get('addressTag') if is_crypto and item.get('addressTag', '') != '' else None,
            'amount': self.convert_to_float(item.get('amount')),
            'receive_amount': self.convert_to_float(item.get('receiveAmount')) if 'receiveAmount' in item else None,
            'transfer_amount': self.convert_to_float(item.get('transferAmount')) if 'transferAmount' in item else None,
            'bw_fee': self.convert_to_float(item.get('BWFee')) if 'BWFee' in item else None,
            'sw_fee': self.convert_to_float(item.get('SWFee')) if 'SWFee' in item else None,
            'coin_id': coin_id,
            'coin_symbol': coin_symbol,
            'network': item.get('network') if is_crypto else None,
            'status': self.convert_to_integer(item.get('status')),
            'confirm_times': None,
            'tx_id': str(item.get('txnId')) if 'txnId' in item else None,
            'source_address': None,
            'usdt_valuation': self.convert_to_float(item.get('usdtValuation')) if 'usdtValuation' in item else None,
            'transfer_status': None,
            'transfer_time': self.convert_epoch_to_iso(item.get('transferTime')) if is_crypto and 'transferTime' in item else None,
            'self_return_status': None,
            'transfer_type': None,
            'metadata': self.convert_to_json(item.get('metadata')) if 'metadata' in item else None,
            'fetched_at': None,
            'insert_time': self.convert_epoch_to_iso(item.get('requestTime')) if 'requestTime' in item else None,
        }

    def get_user_id(self, sub_account_id: str):
        """Get user ID from sub_account_id, return None if not found"""
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
                return None
        except Exception as e:
            logger.error(f"Error getting user ID for sub_account_id {sub_account_id}: {e}")
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
        """Get PostgreSQL INSERT query for crypto_withdraw_histories table"""
        return """
            INSERT INTO crypto_withdraw_histories (
               id, created_at, updated_at, deleted_at, user_id, address, amount, receive_amount, transfer_amount, bw_fee, sw_fee, coin_id, coin_symbol, network, status, confirm_times, tx_id, source_address, usdt_valuation, transfer_status, transfer_time, address_tag, self_return_status, transfer_type, metadata, fetched_at, insert_time
            )
            VALUES (%(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(user_id)s, %(address)s, %(amount)s, %(receive_amount)s, %(transfer_amount)s, %(bw_fee)s, %(sw_fee)s, %(coin_id)s, %(coin_symbol)s, %(network)s, %(status)s, %(confirm_times)s, %(tx_id)s, %(source_address)s, %(usdt_valuation)s, %(transfer_status)s, %(transfer_time)s, %(address_tag)s, %(self_return_status)s, %(transfer_type)s, %(metadata)s, %(fetched_at)s, %(insert_time)s)
            ON CONFLICT (id) DO UPDATE SET
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at,
                user_id = EXCLUDED.user_id,
                address = EXCLUDED.address,
                amount = EXCLUDED.amount,
                receive_amount = EXCLUDED.receive_amount,
                transfer_amount = EXCLUDED.transfer_amount,
                bw_fee = EXCLUDED.bw_fee,
                sw_fee = EXCLUDED.sw_fee,
                coin_id = EXCLUDED.coin_id,
                coin_symbol = EXCLUDED.coin_symbol,
                network = EXCLUDED.network,
                status = EXCLUDED.status,
                confirm_times = EXCLUDED.confirm_times,
                tx_id = EXCLUDED.tx_id,
                source_address = EXCLUDED.source_address,
                usdt_valuation = EXCLUDED.usdt_valuation,
                transfer_status = EXCLUDED.transfer_status,
                transfer_time = EXCLUDED.transfer_time,
                address_tag = EXCLUDED.address_tag,
                self_return_status = EXCLUDED.self_return_status,
                transfer_type = EXCLUDED.transfer_type,
                metadata = EXCLUDED.metadata,
                fetched_at = EXCLUDED.fetched_at,
                insert_time = EXCLUDED.insert_time
        """
