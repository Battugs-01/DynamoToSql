import json
import uuid
from utils.migration_base import BaseMigration

class BuyNowSymbolsMigration(BaseMigration):
    dynamo_table_name = "buynow-symbols"
    postgres_table_name = "buy_now_symbols"

    def transform_item(self, item):
        # Handle list/json fields
        filters = item.get("filters", [])
        if filters:
            filters = self.convert_decimal_to_number(filters)
            filters = json.dumps(filters)
        else:
            filters = '[]'

        allowed_prevention_modes = item.get("allowedSelfTradePreventionModes", [])
        if allowed_prevention_modes:
            allowed_prevention_modes = json.dumps(allowed_prevention_modes)
        else:
            allowed_prevention_modes = '[]'

        order_types = item.get("orderTypes", [])
        if order_types:
            order_types = json.dumps(order_types)
        else:
            order_types = '[]'

        permissions = item.get("permissions", [])
        if permissions:
            permissions = json.dumps(permissions)
        else:
            permissions = '[]'

        symbol = item.get("symbol")
        # Generate deterministic UUID based on symbol
        if symbol:
            record_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, symbol))
        else:
            record_id = str(uuid.uuid4())

        return {
            "id": record_id,
            "symbol": symbol,
            "allowed_self_trade_prevention_modes": allowed_prevention_modes,
            "allow_trailing_stop": item.get("allowTrailingStop", False),
            "base_asset": item.get("baseAsset"),
            "base_asset_name": item.get("baseAssetName"),
            "base_asset_precision": int(item.get("baseAssetPrecision", 0)),
            "base_commission_precision": int(item.get("baseCommissionPrecision", 0)),
            "cancel_replace_allowed": item.get("cancelReplaceAllowed", False),
            "default_self_trade_prevention_mode": item.get("defaultSelfTradePreventionMode"),
            "filters": filters,
            "iceberg_allowed": item.get("icebergAllowed", False),
            "image": item.get("image"),
            "image_dark": item.get("imageDark"),
            "is_active": int(item.get("isActive", 1)),
            "is_margin_trading_allowed": item.get("isMarginTradingAllowed", False),
            "is_spot_trading_allowed": item.get("isSpotTradingAllowed", False),
            "oco_allowed": item.get("ocoAllowed", False),
            "order": int(item.get("order", 0)),
            "order_types": order_types,
            "permissions": permissions,
            "quote_asset": item.get("quoteAsset"),
            "quote_asset_name": item.get("quoteAssetName"),
            "quote_asset_precision": int(item.get("quoteAssetPrecision", 0)),
            "quote_commission_precision": int(item.get("quoteCommissionPrecision", 0)),
            "quote_order_qty_market_allowed": item.get("quoteOrderQtyMarketAllowed", False),
            "quote_precision": int(item.get("quotePrecision", 0)),
            "status": item.get("status"),
            "created_at": item.get("createdAt") or self.now_iso(),
            "updated_at": item.get("updatedAt") or self.now_iso(),
        }

    def get_insert_query(self):
        return """
            INSERT INTO buy_now_symbols (
                id, symbol, allowed_self_trade_prevention_modes, allow_trailing_stop,
                base_asset, base_asset_name, base_asset_precision, base_commission_precision,
                cancel_replace_allowed, default_self_trade_prevention_mode, filters,
                iceberg_allowed, image, image_dark, is_active,
                is_margin_trading_allowed, is_spot_trading_allowed, oco_allowed,
                "order", order_types, permissions, quote_asset, quote_asset_name,
                quote_asset_precision, quote_commission_precision, quote_order_qty_market_allowed,
                quote_precision, status, created_at, updated_at
            ) VALUES (
                %(id)s, %(symbol)s, %(allowed_self_trade_prevention_modes)s, %(allow_trailing_stop)s,
                %(base_asset)s, %(base_asset_name)s, %(base_asset_precision)s, %(base_commission_precision)s,
                %(cancel_replace_allowed)s, %(default_self_trade_prevention_mode)s, %(filters)s,
                %(iceberg_allowed)s, %(image)s, %(image_dark)s, %(is_active)s,
                %(is_margin_trading_allowed)s, %(is_spot_trading_allowed)s, %(oco_allowed)s,
                %(order)s, %(order_types)s, %(permissions)s, %(quote_asset)s, %(quote_asset_name)s,
                %(quote_asset_precision)s, %(quote_commission_precision)s, %(quote_order_qty_market_allowed)s,
                %(quote_precision)s, %(status)s, %(created_at)s, %(updated_at)s
            )
        """

    def get_upsert_query(self):
        return """
            INSERT INTO buy_now_symbols (
                id, symbol, allowed_self_trade_prevention_modes, allow_trailing_stop,
                base_asset, base_asset_name, base_asset_precision, base_commission_precision,
                cancel_replace_allowed, default_self_trade_prevention_mode, filters,
                iceberg_allowed, image, image_dark, is_active,
                is_margin_trading_allowed, is_spot_trading_allowed, oco_allowed,
                "order", order_types, permissions, quote_asset, quote_asset_name,
                quote_asset_precision, quote_commission_precision, quote_order_qty_market_allowed,
                quote_precision, status, created_at, updated_at
            ) VALUES (
                %(id)s, %(symbol)s, %(allowed_self_trade_prevention_modes)s, %(allow_trailing_stop)s,
                %(base_asset)s, %(base_asset_name)s, %(base_asset_precision)s, %(base_commission_precision)s,
                %(cancel_replace_allowed)s, %(default_self_trade_prevention_mode)s, %(filters)s,
                %(iceberg_allowed)s, %(image)s, %(image_dark)s, %(is_active)s,
                %(is_margin_trading_allowed)s, %(is_spot_trading_allowed)s, %(oco_allowed)s,
                %(order)s, %(order_types)s, %(permissions)s, %(quote_asset)s, %(quote_asset_name)s,
                %(quote_asset_precision)s, %(quote_commission_precision)s, %(quote_order_qty_market_allowed)s,
                %(quote_precision)s, %(status)s, %(created_at)s, %(updated_at)s
            ) ON CONFLICT (symbol) DO UPDATE SET
                allowed_self_trade_prevention_modes = EXCLUDED.allowed_self_trade_prevention_modes,
                allow_trailing_stop = EXCLUDED.allow_trailing_stop,
                base_asset = EXCLUDED.base_asset,
                base_asset_name = EXCLUDED.base_asset_name,
                base_asset_precision = EXCLUDED.base_asset_precision,
                base_commission_precision = EXCLUDED.base_commission_precision,
                cancel_replace_allowed = EXCLUDED.cancel_replace_allowed,
                default_self_trade_prevention_mode = EXCLUDED.default_self_trade_prevention_mode,
                filters = EXCLUDED.filters,
                iceberg_allowed = EXCLUDED.iceberg_allowed,
                image = EXCLUDED.image,
                image_dark = EXCLUDED.image_dark,
                is_active = EXCLUDED.is_active,
                is_margin_trading_allowed = EXCLUDED.is_margin_trading_allowed,
                is_spot_trading_allowed = EXCLUDED.is_spot_trading_allowed,
                oco_allowed = EXCLUDED.oco_allowed,
                "order" = EXCLUDED."order",
                order_types = EXCLUDED.order_types,
                permissions = EXCLUDED.permissions,
                quote_asset = EXCLUDED.quote_asset,
                quote_asset_name = EXCLUDED.quote_asset_name,
                quote_asset_precision = EXCLUDED.quote_asset_precision,
                quote_commission_precision = EXCLUDED.quote_commission_precision,
                quote_order_qty_market_allowed = EXCLUDED.quote_order_qty_market_allowed,
                quote_precision = EXCLUDED.quote_precision,
                status = EXCLUDED.status,
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at
        """
