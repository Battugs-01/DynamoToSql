import json
import uuid
from typing import Dict, Any, List
from utils.migration_base import BaseMigration
from decimal import Decimal

class SpotSymbolsMigration(BaseMigration):
    def __init__(self, dynamo_conn, postgres_conn, config):
        super().__init__(dynamo_conn, postgres_conn, config)

    @property
    def dynamo_table_name(self) -> str:
        return "Symbols"

    @property
    def postgres_table_name(self) -> str:
        return "spot_symbols"

    def convert_decimal_to_number(self, item: Any) -> Any:
        if isinstance(item, list):
            return [self.convert_decimal_to_number(i) for i in item]
        elif isinstance(item, dict):
            return {k: self.convert_decimal_to_number(v) for k, v in item.items()}
        elif isinstance(item, Decimal):
            return float(item)
        return item

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # Generate ID based on symbol for determinism
        symbol = item.get('symbol')
        if not symbol:
            return None
            
        record_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"spot_symbol_{symbol}"))
        
        # Handle JSON fields
        allowed_prevention_modes = item.get('allowedSelfTradePreventionModes', [])
        filters = self.convert_decimal_to_number(item.get('filters', []))
        order_types = item.get('orderTypes', [])
        permissions = item.get('permissions', [])
        
        return {
            'id': record_id,
            'created_at': self.now_iso(),
            'updated_at': self.now_iso(),
            'deleted_at': None,
            
            'symbol': symbol,
            'allowed_self_trade_prevention_modes': json.dumps(allowed_prevention_modes),
            'allow_trailing_stop': bool(item.get('allowTrailingStop', False)),
            'base_asset': item.get('baseAsset'),
            'base_asset_name': item.get('baseAssetName'),
            'base_asset_precision': int(item.get('baseAssetPrecision', 0)),
            'base_commission_precision': int(item.get('baseCommissionPrecision', 0)),
            'cancel_replace_allowed': bool(item.get('cancelReplaceAllowed', False)),
            'default_self_trade_prevention_mode': item.get('defaultSelfTradePreventionMode'),
            'featured_sort': int(item.get('featuredSort', 0)),
            'filters': json.dumps(filters),
            'iceberg_allowed': bool(item.get('icebergAllowed', False)),
            'image': item.get('image'),
            'image_dark': item.get('imageDark'),
            'is_enabled': int(item.get('isEnabled', 0)),
            'is_featured': int(item.get('isFeatured', 0)),
            'is_margin_trading_allowed': bool(item.get('isMarginTradingAllowed', False)),
            'is_spot_trading_allowed': bool(item.get('isSpotTradingAllowed', False)),
            'oco_allowed': bool(item.get('ocoAllowed', False)),
            'order_types': json.dumps(order_types),
            'permissions': json.dumps(permissions),
            'quote_asset': item.get('quoteAsset'),
            'quote_asset_name': item.get('quoteAssetName'),
            'quote_asset_precision': int(item.get('quoteAssetPrecision', 0)),
            'quote_commission_precision': int(item.get('quoteCommissionPrecision', 0)),
            'quote_order_qty_market_allowed': bool(item.get('quoteOrderQtyMarketAllowed', False)),
            'quote_precision': int(item.get('quotePrecision', 0)),
            'status': item.get('status')
        }

    def get_insert_query(self) -> str:
        return f"""
            INSERT INTO {self.postgres_table_name} (
                id, created_at, updated_at, deleted_at,
                symbol, allowed_self_trade_prevention_modes, allow_trailing_stop,
                base_asset, base_asset_name, base_asset_precision, base_commission_precision,
                cancel_replace_allowed, default_self_trade_prevention_mode, featured_sort,
                filters, iceberg_allowed, image, image_dark, is_enabled, is_featured,
                is_margin_trading_allowed, is_spot_trading_allowed, oco_allowed,
                order_types, permissions, quote_asset, quote_asset_name,
                quote_asset_precision, quote_commission_precision,
                quote_order_qty_market_allowed, quote_precision, status
            ) VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(symbol)s, %(allowed_self_trade_prevention_modes)s, %(allow_trailing_stop)s,
                %(base_asset)s, %(base_asset_name)s, %(base_asset_precision)s, %(base_commission_precision)s,
                %(cancel_replace_allowed)s, %(default_self_trade_prevention_mode)s, %(featured_sort)s,
                %(filters)s, %(iceberg_allowed)s, %(image)s, %(image_dark)s, %(is_enabled)s, %(is_featured)s,
                %(is_margin_trading_allowed)s, %(is_spot_trading_allowed)s, %(oco_allowed)s,
                %(order_types)s, %(permissions)s, %(quote_asset)s, %(quote_asset_name)s,
                %(quote_asset_precision)s, %(quote_commission_precision)s,
                %(quote_order_qty_market_allowed)s, %(quote_precision)s, %(status)s
            )
        """

    def get_upsert_query(self) -> str:
        return f"""
            INSERT INTO {self.postgres_table_name} (
                id, created_at, updated_at, deleted_at,
                symbol, allowed_self_trade_prevention_modes, allow_trailing_stop,
                base_asset, base_asset_name, base_asset_precision, base_commission_precision,
                cancel_replace_allowed, default_self_trade_prevention_mode, featured_sort,
                filters, iceberg_allowed, image, image_dark, is_enabled, is_featured,
                is_margin_trading_allowed, is_spot_trading_allowed, oco_allowed,
                order_types, permissions, quote_asset, quote_asset_name,
                quote_asset_precision, quote_commission_precision,
                quote_order_qty_market_allowed, quote_precision, status
            ) VALUES (
                %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s,
                %(symbol)s, %(allowed_self_trade_prevention_modes)s, %(allow_trailing_stop)s,
                %(base_asset)s, %(base_asset_name)s, %(base_asset_precision)s, %(base_commission_precision)s,
                %(cancel_replace_allowed)s, %(default_self_trade_prevention_mode)s, %(featured_sort)s,
                %(filters)s, %(iceberg_allowed)s, %(image)s, %(image_dark)s, %(is_enabled)s, %(is_featured)s,
                %(is_margin_trading_allowed)s, %(is_spot_trading_allowed)s, %(oco_allowed)s,
                %(order_types)s, %(permissions)s, %(quote_asset)s, %(quote_asset_name)s,
                %(quote_asset_precision)s, %(quote_commission_precision)s,
                %(quote_order_qty_market_allowed)s, %(quote_precision)s, %(status)s
            )
            ON CONFLICT (id) DO UPDATE SET
                symbol = EXCLUDED.symbol,
                allowed_self_trade_prevention_modes = EXCLUDED.allowed_self_trade_prevention_modes,
                allow_trailing_stop = EXCLUDED.allow_trailing_stop,
                base_asset = EXCLUDED.base_asset,
                base_asset_name = EXCLUDED.base_asset_name,
                base_asset_precision = EXCLUDED.base_asset_precision,
                base_commission_precision = EXCLUDED.base_commission_precision,
                cancel_replace_allowed = EXCLUDED.cancel_replace_allowed,
                default_self_trade_prevention_mode = EXCLUDED.default_self_trade_prevention_mode,
                featured_sort = EXCLUDED.featured_sort,
                filters = EXCLUDED.filters,
                iceberg_allowed = EXCLUDED.iceberg_allowed,
                image = EXCLUDED.image,
                image_dark = EXCLUDED.image_dark,
                is_enabled = EXCLUDED.is_enabled,
                is_featured = EXCLUDED.is_featured,
                is_margin_trading_allowed = EXCLUDED.is_margin_trading_allowed,
                is_spot_trading_allowed = EXCLUDED.is_spot_trading_allowed,
                oco_allowed = EXCLUDED.oco_allowed,
                order_types = EXCLUDED.order_types,
                permissions = EXCLUDED.permissions,
                quote_asset = EXCLUDED.quote_asset,
                quote_asset_name = EXCLUDED.quote_asset_name,
                quote_asset_precision = EXCLUDED.quote_asset_precision,
                quote_commission_precision = EXCLUDED.quote_commission_precision,
                quote_order_qty_market_allowed = EXCLUDED.quote_order_qty_market_allowed,
                quote_precision = EXCLUDED.quote_precision,
                status = EXCLUDED.status,
                updated_at = EXCLUDED.updated_at
        """
