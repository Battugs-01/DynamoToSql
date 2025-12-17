"""
Exchange Bank Account Wallets table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class ExchangeBankAccountWalletsMigration(BaseMigration):
    """Migration for exchange_bank_wallets table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "exchange-bank-account-wallets"
    
    @property
    def postgres_table_name(self) -> str:
        return "exchange_bank_wallets"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB exchange bank account wallets item to PostgreSQL format"""
        # walletId is required
        wallet_id = item.get("walletId")
        if not wallet_id:
            logger.warning(f"Skipping exchange bank wallet - missing required walletId")
            return None
        
        # All fields are NOT NULL in PostgreSQL - provide defaults if missing
        return {
            'id': wallet_id,
            'account_name': item.get("accountName") or "",
            'account_number': item.get("accountNumber") or "",
            'balance': self.convert_to_float(item.get("balance")) if item.get("balance") is not None else 0.0,
            'bank_code': item.get("bankCode") or "",
            'currency': item.get("currency") or "MNT",
            'iban': item.get("iban") or "",
            'order': self.convert_to_integer(item.get("order")) if item.get("order") is not None else 0,
            'status': item.get("status") or "ok",
            'usage': item.get("usage") or "",
            'created_at': self.convert_epoch_to_iso(item.get("createTime")) or self.now_iso(),
            'updated_at': self.convert_epoch_to_iso(item.get("updateTime")) or self.now_iso(),
            'deleted_at': self.convert_epoch_to_iso(item.get("deletedAt")) if item.get("deletedAt") else None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for exchange_bank_wallets table (skip existing)"""
        return """
            INSERT INTO exchange_bank_wallets (
                id, account_name, account_number, balance, bank_code, currency, 
                iban, "order", status, usage, created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(account_name)s, %(account_number)s, %(balance)s, %(bank_code)s, %(currency)s,
                %(iban)s, %(order)s, %(status)s, %(usage)s, %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for exchange_bank_wallets table (update existing)"""
        return """
            INSERT INTO exchange_bank_wallets (
                id, account_name, account_number, balance, bank_code, currency, 
                iban, "order", status, usage, created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(account_name)s, %(account_number)s, %(balance)s, %(bank_code)s, %(currency)s,
                %(iban)s, %(order)s, %(status)s, %(usage)s, %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                account_name = EXCLUDED.account_name,
                account_number = EXCLUDED.account_number,
                balance = EXCLUDED.balance,
                bank_code = EXCLUDED.bank_code,
                currency = EXCLUDED.currency,
                iban = EXCLUDED.iban,
                "order" = EXCLUDED."order",
                status = EXCLUDED.status,
                usage = EXCLUDED.usage,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
