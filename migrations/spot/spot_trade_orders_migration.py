import json
from typing import Dict, Any, List
from utils.migration_base import BaseMigration
from decimal import Decimal

class SpotTradeOrdersMigration(BaseMigration):
    def __init__(self, dynamo_conn, postgres_conn, config):
        super().__init__(dynamo_conn, postgres_conn, config)
        self.symbol_map = {}
        self.user_to_broker_map = {}
        self.op_to_broker_map = {}

    @property
    def dynamo_table_name(self) -> str:
        return "spot-trade-orders"

    @property
    def postgres_table_name(self) -> str:
        return "spot_trade_orders"

    def load_maps(self):
        """Load mappings from PostgreSQL"""
        cursor = self.postgres.get_cursor()
        
        if not self.symbol_map:
            cursor.execute("SELECT symbol, id FROM spot_symbols")
            for row in cursor.fetchall():
                self.symbol_map[row[0]] = row[1]
                
        if not self.user_to_broker_map:
            cursor.execute("SELECT user_id, id FROM broker_users WHERE user_id IS NOT NULL")
            for row in cursor.fetchall():
                self.user_to_broker_map[row[0]] = row[1]

        if not self.op_to_broker_map:
            cursor.execute("SELECT operation_id, id FROM broker_users WHERE operation_id IS NOT NULL")
            for row in cursor.fetchall():
                self.op_to_broker_map[row[0]] = row[1]

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure maps are loaded
        self.load_maps()
        
        # Get symbol ID
        symbol_name = item.get('symbol')
        symbol_id = self.symbol_map.get(symbol_name)
        
        if not symbol_id:
            return None

        # Resolve BrokerUser ID
        uid = item.get('uid')
        broker_user_id = self.user_to_broker_map.get(uid) or self.op_to_broker_map.get(uid)
        
        if not broker_user_id:
            return None

        # Convert timestamps
        created_at = self.convert_epoch_to_iso(item.get('createTime'))
        transact_time = self.convert_epoch_to_iso(item.get('transactTime'))
        
        return {
            'id': str(item.get('orderId')),
            'created_at': created_at,
            'updated_at': created_at,
            'deleted_at': None,
            'broker_user_id': broker_user_id,
            'symbol_id': symbol_id,
            'client_order_id': item.get('clientOrderId'),
            'cummulative_quote_qty': item.get('cummulativeQuoteQty'),
            'executed_qty': item.get('executedQty'),
            'order_list_id': int(item.get('orderListId', -1)),
            'orig_client_order_id': item.get('origClientOrderId'),
            'orig_qty': item.get('origQty'),
            'price': item.get('price'),
            'self_trade_prevention_mode': item.get('selfTradePreventionMode'),
            'side': item.get('side'),
            'status': item.get('status'),
            'time_in_force': item.get('timeInForce'),
            'transact_time': transact_time,
            'type': item.get('type')
        }

    def get_insert_query(self) -> str:
        return f"""
            INSERT INTO {self.postgres_table_name} (
                id, created_at, updated_at, deleted_at,
                broker_user_id, symbol_id, client_order_id,
                cummulative_quote_qty, executed_qty, order_list_id,
                orig_client_order_id, orig_qty, price,
                self_trade_prevention_mode, side, status,
                time_in_force, transact_time, type
            ) VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(broker_user_id)s, %(symbol_id)s, %(client_order_id)s,
                %(cummulative_quote_qty)s, %(executed_qty)s, %(order_list_id)s,
                %(orig_client_order_id)s, %(orig_qty)s, %(price)s,
                %(self_trade_prevention_mode)s, %(side)s, %(status)s,
                %(time_in_force)s, %(transact_time)s, %(type)s
            )
        """

    def get_upsert_query(self) -> str:
        return f"""
            INSERT INTO {self.postgres_table_name} (
                id, created_at, updated_at, deleted_at,
                broker_user_id, symbol_id, client_order_id,
                cummulative_quote_qty, executed_qty, order_list_id,
                orig_client_order_id, orig_qty, price,
                self_trade_prevention_mode, side, status,
                time_in_force, transact_time, type
            ) VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(broker_user_id)s, %(symbol_id)s, %(client_order_id)s,
                %(cummulative_quote_qty)s, %(executed_qty)s, %(order_list_id)s,
                %(orig_client_order_id)s, %(orig_qty)s, %(price)s,
                %(self_trade_prevention_mode)s, %(side)s, %(status)s,
                %(time_in_force)s, %(transact_time)s, %(type)s
            )
            ON CONFLICT (id) DO UPDATE SET
                broker_user_id = EXCLUDED.broker_user_id,
                symbol_id = EXCLUDED.symbol_id,
                client_order_id = EXCLUDED.client_order_id,
                cummulative_quote_qty = EXCLUDED.cummulative_quote_qty,
                executed_qty = EXCLUDED.executed_qty,
                order_list_id = EXCLUDED.order_list_id,
                orig_client_order_id = EXCLUDED.orig_client_order_id,
                orig_qty = EXCLUDED.orig_qty,
                price = EXCLUDED.price,
                self_trade_prevention_mode = EXCLUDED.self_trade_prevention_mode,
                side = EXCLUDED.side,
                status = EXCLUDED.status,
                time_in_force = EXCLUDED.time_in_force,
                transact_time = EXCLUDED.transact_time,
                type = EXCLUDED.type,
                updated_at = EXCLUDED.updated_at
        """
