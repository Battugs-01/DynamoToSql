"""
Exchange Bank Transactions table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class ExchangeBankTxnMigration(BaseMigration):
    """Migration for exchange_bank_txns table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "exchange-bank-txn"
    
    @property
    def postgres_table_name(self) -> str:
        return "exchange_bank_txns"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB exchange bank txn item to PostgreSQL format"""
        # txnId is required
        txn_id = item.get("txnId")
        if not txn_id:
            logger.warning(f"Skipping exchange bank txn - missing required txnId")
            return None
        
        return {
            'id': txn_id,
            'bank_account_id': item.get("bankAccountId") or "",
            'amount': self.convert_to_float(item.get("amount")) if item.get("amount") is not None else 0.0,
            'amount_type': item.get("amountType") or "",
            'amount_type_process_status_search_key': item.get("amountTypeProcessStatusSearchKey") or "",
            'bank_record_number': item.get("bankRecordNumber") or "",
            'begin_balance': self.convert_to_float(item.get("beginBalance")) if item.get("beginBalance") is not None else 0.0,
            'currency': item.get("currency") or "MNT",
            'description': item.get("description") or "",
            'end_balance': self.convert_to_float(item.get("endBalance")) if item.get("endBalance") is not None else 0.0,
            'main_account_number': item.get("mainAccountNumber") or "",
            'metadata': self.convert_to_json(item.get("metadata")) if item.get("metadata") else None,
            'process_status': item.get("processStatus") or "",
            'raw_description': item.get("rawDescription") or "",
            'related_account_number': item.get("relatedAccountNumber") or "",
            'txn_time': self.convert_epoch_to_iso(item.get("txnTime")) or self.now_iso(),
            'created_at': self.convert_epoch_to_iso(item.get("createdAt")) or self.now_iso(),
            'updated_at': self.convert_epoch_to_iso(item.get("updatedAt")) or self.now_iso(),
            'deleted_at': self.convert_epoch_to_iso(item.get("deletedAt")) if item.get("deletedAt") else None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for exchange_bank_txns table (skip existing)"""
        return """
            INSERT INTO exchange_bank_txns (
                id, bank_account_id, amount, amount_type, 
                amount_type_process_status_search_key, bank_record_number, begin_balance, 
                currency, description, end_balance, main_account_number, metadata, 
                process_status, raw_description, related_account_number, txn_time,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(bank_account_id)s, %(amount)s, %(amount_type)s,
                %(amount_type_process_status_search_key)s, %(bank_record_number)s, %(begin_balance)s,
                %(currency)s, %(description)s, %(end_balance)s, %(main_account_number)s, %(metadata)s,
                %(process_status)s, %(raw_description)s, %(related_account_number)s, %(txn_time)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for exchange_bank_txns table (update existing)"""
        return """
            INSERT INTO exchange_bank_txns (
                id, bank_account_id, amount, amount_type, 
                amount_type_process_status_search_key, bank_record_number, begin_balance, 
                currency, description, end_balance, main_account_number, metadata, 
                process_status, raw_description, related_account_number, txn_time,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(bank_account_id)s, %(amount)s, %(amount_type)s,
                %(amount_type_process_status_search_key)s, %(bank_record_number)s, %(begin_balance)s,
                %(currency)s, %(description)s, %(end_balance)s, %(main_account_number)s, %(metadata)s,
                %(process_status)s, %(raw_description)s, %(related_account_number)s, %(txn_time)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                bank_account_id = EXCLUDED.bank_account_id,
                amount = EXCLUDED.amount,
                amount_type = EXCLUDED.amount_type,
                amount_type_process_status_search_key = EXCLUDED.amount_type_process_status_search_key,
                bank_record_number = EXCLUDED.bank_record_number,
                begin_balance = EXCLUDED.begin_balance,
                currency = EXCLUDED.currency,
                description = EXCLUDED.description,
                end_balance = EXCLUDED.end_balance,
                main_account_number = EXCLUDED.main_account_number,
                metadata = EXCLUDED.metadata,
                process_status = EXCLUDED.process_status,
                raw_description = EXCLUDED.raw_description,
                related_account_number = EXCLUDED.related_account_number,
                txn_time = EXCLUDED.txn_time,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
