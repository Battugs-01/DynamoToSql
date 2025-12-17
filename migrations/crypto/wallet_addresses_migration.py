"""
wallet_addresses table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid
import logging

logger = logging.getLogger(__name__)


class WalletAddressesMigration(BaseMigration):
    """Migration for wallet_addresses table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "wallet-addresses"
    
    @property
    def postgres_table_name(self) -> str:
        return "wallet_addresses"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB wallet-addresses item to PostgreSQL format"""
        # Handle USER_NOT_FOUND - set to None
        user_id = item.get('uid')
        if user_id == 'USER_NOT_FOUND':
            logger.warning(f"USER_NOT_FOUND for address {item.get('address')}, setting user_id to NULL")
            user_id = None
        elif user_id:
            # Check if user exists in users table, set to NULL if not found
            try:
                cursor = self.postgres.get_cursor()
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                if not result:
                    logger.warning(f"User {user_id} not found, setting user_id to NULL for address {item.get('address')}")
                    user_id = None
            except Exception as e:
                logger.error(f"Error checking user {user_id}: {str(e)}, setting user_id to NULL")
                user_id = None
        
        # Get coin_id from coin symbol
        coin_symbol = item.get('coin')
        coin_id = self.get_coin_id(coin_symbol) if coin_symbol else None
        
        # Extract network from coin-network if network is missing
        network = item.get('network')
        if not network:
            coin_network = item.get('coin-network', '')
            if '@' in coin_network:
                # Extract network from coin-network (e.g., BTC@BSC -> BSC)
                network = coin_network.split('@')[1]
                logger.warning(f"Network was NULL, extracted '{network}' from coin-network '{coin_network}' for address {item.get('address')}")
            else:
                network = coin_network or 'UNKNOWN'
                logger.warning(f"Network was NULL and could not extract from coin-network, using '{network}' for address {item.get('address')}")
            
        return {
            'id': self.get_id(),
            'user_id': user_id,  # Can be None now
            'address': item.get('address'),
            'coin_id': coin_id,  # Lookup from coins table
            'network': network,
            'coin_network': item.get('coin-network'),
            'is_default': self.convert_to_boolean(item.get('isDefault')),
            'tag': item.get('tag') or '',
            'url': item.get('url') or '',
            'created_at': self.convert_epoch_to_iso(item.get('createdAt')),
            'updated_at': self.convert_epoch_to_iso(item.get('createdAt')),
            'deleted_at': None,
        }

    def get_id(self) -> int:
        """Get the next wallet address ID starting from 1"""
        if not hasattr(self, '_wallet_address_id_counter'):
            # Get the maximum existing ID from database and start from next
            try:
                cursor = self.postgres.get_cursor()
                cursor.execute(f"SELECT COALESCE(MAX(id), 0) FROM {self.postgres_table_name}")
                result = cursor.fetchone()
                max_id = result[0] if result else 0
                self._wallet_address_id_counter = max_id
            except Exception as e:
                # If table doesn't exist or error, start from 0
                self._wallet_address_id_counter = 0
        
        self._wallet_address_id_counter += 1
        return self._wallet_address_id_counter
    
    def get_coin_id(self, coin_symbol: str):
        """Get coin ID from coin symbol, return None if not found"""
        if not coin_symbol:
            return None
        
        # Cache coin lookups to avoid repeated queries
        if not hasattr(self, '_coin_cache'):
            self._coin_cache = {}
        
        if coin_symbol in self._coin_cache:
            return self._coin_cache[coin_symbol]
        
        cursor = self.postgres.get_cursor()
        cursor.execute("SELECT id FROM coins WHERE coin = %s", (coin_symbol,))
        result = cursor.fetchone()
        
        if result:
            coin_id = str(result[0])  # Convert to string as CoinID is *string
            self._coin_cache[coin_symbol] = coin_id
            return coin_id
        else:
            logger.warning(f"Coin symbol '{coin_symbol}' not found in coins table, setting to NULL")
            self._coin_cache[coin_symbol] = None
            return None


    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for wallet_addresses table - allows duplicates"""
        return """
            INSERT INTO wallet_addresses (
               id, user_id, address, coin_id, network, coin_network, is_default, tag, url, created_at, updated_at, deleted_at
            )
            VALUES (%(id)s, %(user_id)s, %(address)s, %(coin_id)s, %(network)s, %(coin_network)s, %(is_default)s, %(tag)s, %(url)s, %(created_at)s, %(updated_at)s, %(deleted_at)s)
        """
