import json
from typing import Dict, Any, List
from utils.migration_base import BaseMigration
from decimal import Decimal

class SpotTradeHistoryMigration(BaseMigration):
    def __init__(self, dynamo_conn, postgres_conn, config):
        super().__init__(dynamo_conn, postgres_conn, config)
        self.symbol_map = {}
        self.broker_user_map = {}

    @property
    def dynamo_table_name(self) -> str:
        return "spot-trade-history"

    @property
    def postgres_table_name(self) -> str:
        return "spot_trade_histories"

    def load_maps(self):
        """Load symbol and broker_user mappings from PostgreSQL"""
        cursor = self.postgres.get_cursor()
        
        # Load Symbols
        if not self.symbol_map:
            cursor.execute("SELECT symbol, id FROM spot_symbols")
            for row in cursor.fetchall():
                self.symbol_map[row[0]] = row[1]
                
        # Load BrokerUsers (sub_account_id -> id)
        if not self.broker_user_map:
            cursor.execute("SELECT sub_account_id, id FROM broker_users")
            for row in cursor.fetchall():
                self.broker_user_map[row[0]] = row[1]

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        self.load_maps()
        
        # Get Symbol ID
        symbol_name = item.get('symbol')
        symbol_id = self.symbol_map.get(symbol_name)
        if not symbol_id:
            return None # Skip if symbol not found
            
        # Get BrokerUser ID via subAccountId
        sub_account_id = item.get('subAccountId')
        broker_user_id = self.broker_user_map.get(sub_account_id)
        if not broker_user_id:
            return None # Skip if user not found
            
        # Convert timestamp (ms to ISO)
        created_at = self.convert_epoch_to_iso(item.get('time'))
        
        # Helper to convert decimal/float to string or float
        def to_str(val):
            return str(val) if val is not None else None
            
        def to_int(val):
            try:
                return int(float(val)) if val is not None else None
            except:
                return None

        return {
            'id': str(item.get('tradeId')),
            'created_at': created_at,
            'updated_at': created_at,
            'deleted_at': None,
            
            'broker_user_id': broker_user_id,
            'symbol_id': symbol_id,
            'order_id': to_str(item.get('orderId')),
            
            'commission': to_str(item.get('commission')),
            'commission_asset': item.get('commissionAsset'),
            'commission_income': to_str(item.get('commissionIncome')),
            
            'is_best_match': to_int(item.get('isBestMatch')),
            'is_buyer': to_int(item.get('isBuyer')),
            'is_maker': to_int(item.get('isMaker')),
            
            'price': to_str(item.get('price')),
            'qty': to_str(item.get('qty')),
            'quote_price': float(item.get('quotePrice', 0)),
            'quote_qty': to_str(item.get('quoteQty')),
            'trade_status': to_str(item.get('tradeStatus'))
        }

    def get_insert_query(self) -> str:
        return f"""
            INSERT INTO {self.postgres_table_name} (
                id, created_at, updated_at, deleted_at,
                broker_user_id, symbol_id, order_id,
                commission, commission_asset, commission_income,
                is_best_match, is_buyer, is_maker,
                price, qty, quote_price, quote_qty, trade_status
            ) VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(broker_user_id)s, %(symbol_id)s, %(order_id)s,
                %(commission)s, %(commission_asset)s, %(commission_income)s,
                %(is_best_match)s, %(is_buyer)s, %(is_maker)s,
                %(price)s, %(qty)s, %(quote_price)s, %(quote_qty)s, %(trade_status)s
            )
        """

    def get_upsert_query(self) -> str:
        return f"""
            INSERT INTO {self.postgres_table_name} (
                id, created_at, updated_at, deleted_at,
                broker_user_id, symbol_id, order_id,
                commission, commission_asset, commission_income,
                is_best_match, is_buyer, is_maker,
                price, qty, quote_price, quote_qty, trade_status
            ) VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(broker_user_id)s, %(symbol_id)s, %(order_id)s,
                %(commission)s, %(commission_asset)s, %(commission_income)s,
                %(is_best_match)s, %(is_buyer)s, %(is_maker)s,
                %(price)s, %(qty)s, %(quote_price)s, %(quote_qty)s, %(trade_status)s
            )
            ON CONFLICT (id) DO UPDATE SET
                broker_user_id = EXCLUDED.broker_user_id,
                symbol_id = EXCLUDED.symbol_id,
                order_id = EXCLUDED.order_id,
                commission = EXCLUDED.commission,
                commission_asset = EXCLUDED.commission_asset,
                commission_income = EXCLUDED.commission_income,
                is_best_match = EXCLUDED.is_best_match,
                is_buyer = EXCLUDED.is_buyer,
                is_maker = EXCLUDED.is_maker,
                price = EXCLUDED.price,
                qty = EXCLUDED.qty,
                quote_price = EXCLUDED.quote_price,
                quote_qty = EXCLUDED.quote_qty,
                trade_status = EXCLUDED.trade_status,
                updated_at = EXCLUDED.updated_at
        """
