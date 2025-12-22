import json
from datetime import datetime
from utils.migration_base import BaseMigration

class BuyNowOrdersMigration(BaseMigration):
    dynamo_table_name = "buynow-orders"
    postgres_table_name = "buy_now_orders"

    def __init__(self, dynamo_conn, postgres_conn, config):
        super().__init__(dynamo_conn, postgres_conn, config)
        self.symbol_map = {}
        try:
             self._load_symbol_map()
        except Exception as e:
             print(f"Warning: Could not load symbol map: {e}")

    def _load_symbol_map(self):
        # Fetch all symbols from postgres buy_now_symbols
        with self.postgres.get_cursor() as cursor:
            cursor.execute("SELECT symbol, id FROM buy_now_symbols")
            self.symbol_map = {row[0]: row[1] for row in cursor.fetchall()}

    def transform_item(self, item):
        # Handle metadata json
        metadata = item.get("metadata", {})
        if metadata:
            metadata = self.convert_decimal_to_number(metadata)
            metadata = json.dumps(metadata)
        else:
            metadata = '{}'
            
        # Timestamp conversion (ms to datetime)
        create_time_ms = int(item.get("createTime", 0))
        created_at = datetime.fromtimestamp(create_time_ms / 1000.0) if create_time_ms else self.now()
        
        update_time_ms = int(item.get("updateTime", 0))
        updated_at = datetime.fromtimestamp(update_time_ms / 1000.0) if update_time_ms else created_at

        # Symbol Lookup
        crypto = item.get("cryptoCurrency")
        symbol_id = None
        if crypto:
            # Try constructing symbol name. Most symbols are [Crypto]USDT
            symbol_name = f"{crypto}USDT"
            symbol_id = self.symbol_map.get(symbol_name)
            
            # Special handling for USDT
            if not symbol_id and crypto == 'USDT':
                 symbol_id = self.symbol_map.get('USDTMNT')
            
            # If still not found, try exact match
            if not symbol_id:
                 symbol_id = self.symbol_map.get(crypto)
        
        return {
            "id": item.get("orderId"), # mapped from orderId
            "symbol_id": symbol_id, # Might still be None for USDT
            "user_id": item.get("userId"),
            "crypto_currency": item.get("cryptoCurrency"),
            "metadata": metadata,
            "mnt_usdt_rate": float(item.get("mntUsdtRate", 0)),
            "order_status": item.get("orderStatus"),
            "quote_price": float(item.get("quotePrice", 0)),
            "user_get_amount_in_crypto": float(item.get("userGetAmountInCrypto", 0)),
            "user_get_amount_in_fiat": float(item.get("userGetAmountInFiat", 0)),
            "user_pay_amount_in_crypto": float(item.get("userPayAmountInCrypto", 0)),
            "user_pay_amount_in_fiat": float(item.get("userPayAmountInFiat", 0)),
            "user_total_fee_amount_in_crypto": float(item.get("userTotalFeeAmountInCrypto", 0)),
            "user_total_fee_amount_in_fiat": float(item.get("userTotalFeeAmountInFiat", 0)),
            "x_meta_rate_mnt_usdt": float(item.get("xMetaRateMntUsdt", 0)),
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def get_insert_query(self):
        return """
            INSERT INTO buy_now_orders (
                id, symbol_id, user_id, crypto_currency, metadata, mnt_usdt_rate,
                order_status, quote_price, user_get_amount_in_crypto,
                user_get_amount_in_fiat, user_pay_amount_in_crypto, user_pay_amount_in_fiat,
                user_total_fee_amount_in_crypto, user_total_fee_amount_in_fiat,
                x_meta_rate_mnt_usdt, created_at, updated_at
            ) VALUES (
                %(id)s, %(symbol_id)s, %(user_id)s, %(crypto_currency)s, %(metadata)s, %(mnt_usdt_rate)s,
                %(order_status)s, %(quote_price)s, %(user_get_amount_in_crypto)s,
                %(user_get_amount_in_fiat)s, %(user_pay_amount_in_crypto)s, %(user_pay_amount_in_fiat)s,
                %(user_total_fee_amount_in_crypto)s, %(user_total_fee_amount_in_fiat)s,
                %(x_meta_rate_mnt_usdt)s, %(created_at)s, %(updated_at)s
            )
        """

    def get_upsert_query(self):
        return """
            INSERT INTO buy_now_orders (
                id, symbol_id, user_id, crypto_currency, metadata, mnt_usdt_rate,
                order_status, quote_price, user_get_amount_in_crypto,
                user_get_amount_in_fiat, user_pay_amount_in_crypto, user_pay_amount_in_fiat,
                user_total_fee_amount_in_crypto, user_total_fee_amount_in_fiat,
                x_meta_rate_mnt_usdt, created_at, updated_at
            ) VALUES (
                %(id)s, %(symbol_id)s, %(user_id)s, %(crypto_currency)s, %(metadata)s, %(mnt_usdt_rate)s,
                %(order_status)s, %(quote_price)s, %(user_get_amount_in_crypto)s,
                %(user_get_amount_in_fiat)s, %(user_pay_amount_in_crypto)s, %(user_pay_amount_in_fiat)s,
                %(user_total_fee_amount_in_crypto)s, %(user_total_fee_amount_in_fiat)s,
                %(x_meta_rate_mnt_usdt)s, %(created_at)s, %(updated_at)s
            ) ON CONFLICT (id) DO UPDATE SET
                symbol_id = EXCLUDED.symbol_id,
                user_id = EXCLUDED.user_id,
                crypto_currency = EXCLUDED.crypto_currency,
                metadata = EXCLUDED.metadata,
                mnt_usdt_rate = EXCLUDED.mnt_usdt_rate,
                order_status = EXCLUDED.order_status,
                quote_price = EXCLUDED.quote_price,
                user_get_amount_in_crypto = EXCLUDED.user_get_amount_in_crypto,
                user_get_amount_in_fiat = EXCLUDED.user_get_amount_in_fiat,
                user_pay_amount_in_crypto = EXCLUDED.user_pay_amount_in_crypto,
                user_pay_amount_in_fiat = EXCLUDED.user_pay_amount_in_fiat,
                user_total_fee_amount_in_crypto = EXCLUDED.user_total_fee_amount_in_crypto,
                user_total_fee_amount_in_fiat = EXCLUDED.user_total_fee_amount_in_fiat,
                x_meta_rate_mnt_usdt = EXCLUDED.x_meta_rate_mnt_usdt,
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at
        """
