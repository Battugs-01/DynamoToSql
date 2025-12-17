"""
banks table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid


class BankDepositHistoryMigration(BaseMigration):
    """Migration for bank_deposit_history table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "user-bank-deposits"
    
    @property
    def postgres_table_name(self) -> str:
        return "bank_deposit_histories"

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB user_bank_deposits item to PostgreSQL format"""
        # Handle USER_NOT_FOUND - set to None (NULL) for nullable user_id
        user_id = item.get('userId')
        if user_id == 'USER_NOT_FOUND':
            user_id = None
        
        # Handle EMAIL_NOT_FOUND - set to empty string
        email = item.get('email')
        if email == 'EMAIL_NOT_FOUND':
            email = ''
        
        return {
            'id': item.get('depositId'),
            'created_at': self.convert_epoch_to_iso(item.get('requestTime')),
            'updated_at': self.convert_epoch_to_iso(item.get('requestTime')),
            'transfer_time': self.convert_epoch_to_iso(item.get('transferTime')),
            'deleted_at': None,
            'user_id': user_id,  # Can be None now
            'payment_wallet_id': item.get('paymentWalletId'),
            'deposit_amount': self.convert_to_float(item.get('depositAmount')),
            'currency': item.get('currency'),
            'status': item.get('status'),
            'email': email,
            'txn_amount': self.convert_to_float(item.get('txnAmount')),
            'txn_id': item.get('txnId'),
        }    

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for bank_deposit_histories table"""
        return """
            INSERT INTO bank_deposit_histories (
               id, created_at, updated_at, deleted_at, user_id, payment_wallet_id, deposit_amount, currency, status, email, txn_amount, txn_id, transfer_time
            )
            VALUES (%(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(user_id)s, %(payment_wallet_id)s, %(deposit_amount)s, %(currency)s, %(status)s, %(email)s, %(txn_amount)s, %(txn_id)s, %(transfer_time)s)
            ON CONFLICT (id) DO UPDATE SET
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                transfer_time = EXCLUDED.transfer_time,
                deleted_at = EXCLUDED.deleted_at,
                user_id = EXCLUDED.user_id,
                payment_wallet_id = EXCLUDED.payment_wallet_id,
                deposit_amount = EXCLUDED.deposit_amount,
                currency = EXCLUDED.currency,
                status = EXCLUDED.status,
                email = EXCLUDED.email,
                txn_amount = EXCLUDED.txn_amount,
                txn_id = EXCLUDED.txn_id
        """
