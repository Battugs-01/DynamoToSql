"""
banks table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid
import logging

logger = logging.getLogger(__name__)


class BankWidthrawalHistoryMigration(BaseMigration):
    """Migration for bank_widthrawal_history table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "user-bank-withdrawals"
    
    @property
    def postgres_table_name(self) -> str:
        return "bank_withdrawal_histories"

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB user_bank_withdrawals item to PostgreSQL format"""
        bank_code = item.get('bankCode')
        payment_wallet_id = item.get('paymentWalletId')
        
        # Handle USER_NOT_FOUND - set to None (NULL) for nullable user_id
        user_id = item.get('userId')
        if user_id == 'USER_NOT_FOUND':
            user_id = None
        
        return {
            'id': item.get('withdrawalId'),
            'created_at': self.convert_epoch_to_iso(item.get('requestTime')),
            'updated_at': self.convert_epoch_to_iso(item.get('requestTime')),
            'transfer_time': self.convert_epoch_to_iso(item.get('transferTime')),
            'deleted_at': None,
            'user_id': user_id,  # Can be None now
            'wallet_id': self.get_payment_wallet_id(payment_wallet_id),  # Can be None now
            'account_number': item.get('accountNumber'),
            'bank_id': self.get_bank_id(bank_code),
            'currency': item.get('currency'),
            'status': item.get('status'),
            'fee_amount': self.convert_to_float(item.get('feeAmount')),
            'receive_amount': self.convert_to_float(item.get('receiveAmount')),
            'total_amount': self.convert_to_float(item.get('totalAmount')),
            'metadata': self.convert_to_json(item.get('metadata')) if item.get('metadata') else None,
        }  

    def get_bank_id(self, bank_code: str) -> str:
        """Get bank ID from bank code"""
        cursor = self.postgres.get_cursor()
        cursor.execute(
            "SELECT id FROM banks WHERE code = %s",
            (bank_code,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Bank code {bank_code} not found")
    
    def get_payment_wallet_id(self, payment_wallet_id: str):
        """Get payment wallet ID from payment wallet ID, return None if not found"""
        if not payment_wallet_id:
            return None
        
        cursor = self.postgres.get_cursor()
        cursor.execute(
            "SELECT id FROM user_bank_account_wallets WHERE wallet_code = %s",
            (payment_wallet_id,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            # Return None instead of raising error (wallet_id is nullable now)
            logger.warning(f"Payment wallet ID {payment_wallet_id} not found, setting to NULL")
            return None
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for bank_withdrawal_histories table"""
        return """
            INSERT INTO bank_withdrawal_histories (
               id, created_at, updated_at, deleted_at, user_id, wallet_id, account_number, bank_id, currency, status, fee_amount, receive_amount, total_amount, metadata, transfer_time
            )
            VALUES (%(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(user_id)s, %(wallet_id)s, %(account_number)s, %(bank_id)s, %(currency)s, %(status)s, %(fee_amount)s, %(receive_amount)s, %(total_amount)s, %(metadata)s, %(transfer_time)s)
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at,
                user_id = EXCLUDED.user_id,
                wallet_id = EXCLUDED.wallet_id,
                account_number = EXCLUDED.account_number,
                bank_id = EXCLUDED.bank_id,
                currency = EXCLUDED.currency,
                status = EXCLUDED.status,
                fee_amount = EXCLUDED.fee_amount,
                receive_amount = EXCLUDED.receive_amount,
                total_amount = EXCLUDED.total_amount,
                metadata = EXCLUDED.metadata,
                transfer_time = EXCLUDED.transfer_time
        """
