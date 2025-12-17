"""
crypto_deposit_histories table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid
import logging

logger = logging.getLogger(__name__)


class CryptoDepositHistoryMigration(BaseMigration):
    """Migration for crypto_deposit_history table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "deposit-history"
    
    @property
    def postgres_table_name(self) -> str:
        return "crypto_deposit_histories"

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB deposit_history item to PostgreSQL format"""
        sub_account_id = item.get('subAccountId')
        
        # Get foreign key IDs - check both users and operation_accounts
        user_id = self.get_user_id(sub_account_id)
        operation_account_id = self.get_operation_account_id(sub_account_id) if not user_id else None
        
        address_id = self.get_address_id(item.get('address'))
        coin_id = self.get_coin_id(item.get('coin'))
        
        # CoinID is now nullable - log warning but don't skip
        if not coin_id:
            logger.warning(f"Coin '{item.get('coin')}' not found for deposit {item.get('depositId')}, setting coin_id to NULL")
        
        # Map the DynamoDB deposit-history item to PostgreSQL format
        return {
            'id': item.get('depositId'),
            'created_at': self.convert_epoch_to_iso(item.get('insertTime')),
            'updated_at': self.convert_epoch_to_iso(item.get('fetchedAt')),
            'deleted_at': None,
            'user_id': user_id,  # Nullable - for regular users
            'operation_account_id': operation_account_id,  # Nullable - for operation accounts
            'address_id': address_id,  # Nullable
            'deposit_address': item.get('address') or '',  # Raw address string
            'amount': self.convert_to_float(item.get('amount')) or 0.0,
            'coin_id': coin_id,  # Nullable - can be NULL if coin not found
            'coin_symbol': item.get('coin') or '',  # Raw coin symbol (e.g., "CAT", "BTC")
            'network': item.get('network'),  # Nullable
            'status': self.convert_to_integer(item.get('status')) or 0,
            'confirm_times': item.get('confirmTimes') or '',
            'tx_id': item.get('txId') or '',
            'source_address': item.get('sourceAddress') or '',
            'usdt_valuation': self.convert_to_float(item.get('usdtValuation')) or 0.0,
            'transfer_status': self.convert_to_integer(item.get('transferStatus')) or 0,
            'transfer_time': self.convert_epoch_to_iso(item.get('transferTime')),
            'address_tag': item.get('addressTag') or '',
            'self_return_status': self.convert_to_integer(item.get('selfReturnStatus')) or 0,
            'transfer_type': self.convert_to_integer(item.get('transferType')) or 0,
            'fetched_at': self.convert_epoch_to_iso(item.get('fetchedAt')),
            'insert_time': self.convert_epoch_to_iso(item.get('insertTime')),
        }

    def get_user_id(self, sub_account_id: str):
        """Get user ID from sub_account_id, return None if not found (nullable)"""
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

    def get_operation_account_id(self, sub_account_id: str):
        """Get operation account ID from sub_account_id, return None if not found"""
        if not sub_account_id:
            return None
        
        # Cache operation account lookups
        if not hasattr(self, '_op_account_cache'):
            self._op_account_cache = {}
        
        if sub_account_id in self._op_account_cache:
            return self._op_account_cache[sub_account_id]
        
        try:
            cursor = self.postgres.get_cursor()
            cursor.execute("SELECT id FROM operation_accounts WHERE sub_account_id = %s", (sub_account_id,))
            result = cursor.fetchone()
            if result:
                self._op_account_cache[sub_account_id] = result[0]
                return result[0]
            else:
                self._op_account_cache[sub_account_id] = None
                return None
        except Exception as e:
            logger.error(f"Error getting operation account ID for sub_account_id {sub_account_id}: {e}")
            return None
    
    def get_address_id(self, address: str):
        """Get address ID from wallet address, return None if not found (nullable)"""
        if not address:
            return None
        
        # Cache address lookups
        if not hasattr(self, '_address_cache'):
            self._address_cache = {}
        
        if address in self._address_cache:
            return self._address_cache[address]
        
        try:
            cursor = self.postgres.get_cursor()
            cursor.execute("SELECT id FROM wallet_addresses WHERE address = %s", (address,))
            result = cursor.fetchone()
            if result:
                address_id = str(result[0])  # Convert to string
                self._address_cache[address] = address_id
                return address_id
            else:
                self._address_cache[address] = None
                return None
        except Exception as e:
            logger.error(f"Error getting address ID for address {address}: {e}")
            return None

    def get_coin_id(self, coin: str) -> str:
        """Get coin ID from coin symbol"""
        if not coin:
            logger.warning("Coin symbol is empty")
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
                coin_id = str(result[0])  # Convert to string as CoinID is string in struct
                self._coin_cache[coin] = coin_id
                return coin_id
            else:
                logger.warning(f"Coin '{coin}' not found in coins table")
                self._coin_cache[coin] = None
                return None
        except Exception as e:
            logger.error(f"Error getting coin ID for coin {coin}: {e}")
            return None

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for crypto_deposit_histories table"""
        return """
            INSERT INTO crypto_deposit_histories (
               id, created_at, updated_at, deleted_at, user_id, operation_account_id, address_id, deposit_address, amount, coin_id, coin_symbol, network, status, confirm_times, tx_id, source_address, usdt_valuation, transfer_status, transfer_time, address_tag, self_return_status, transfer_type, fetched_at, insert_time
            )
            VALUES (%(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(user_id)s, %(operation_account_id)s, %(address_id)s, %(deposit_address)s, %(amount)s, %(coin_id)s, %(coin_symbol)s, %(network)s, %(status)s, %(confirm_times)s, %(tx_id)s, %(source_address)s, %(usdt_valuation)s, %(transfer_status)s, %(transfer_time)s, %(address_tag)s, %(self_return_status)s, %(transfer_type)s, %(fetched_at)s, %(insert_time)s)
            ON CONFLICT (id) DO UPDATE SET
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at,
                user_id = EXCLUDED.user_id,
                operation_account_id = EXCLUDED.operation_account_id,
                address_id = EXCLUDED.address_id,
                deposit_address = EXCLUDED.deposit_address,
                amount = EXCLUDED.amount,
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
                fetched_at = EXCLUDED.fetched_at,
                insert_time = EXCLUDED.insert_time
        """
