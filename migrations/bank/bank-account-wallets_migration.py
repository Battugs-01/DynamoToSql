"""
banks table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid


class BankAccountWalletsMigration(BaseMigration):
    """Migration for user_bank_account_wallets table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "user-bank-account-wallets"
    
    @property
    def postgres_table_name(self) -> str:
        return "user_bank_account_wallets"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB user_bank_account_wallets item to PostgreSQL format"""
        # Skip items without user_id
        user_id = item.get('userId')
        if not user_id:
            print(f"Warning: Bank account wallet {item.get('walletId', 'unknown')} has no user_id, skipping")
            return None
            
        # Get bank_id from bank code
        bank_code = item.get('bankCode')
        bank_id = self.get_bank_id(bank_code)
        if bank_id is None:
            return None
            
        return {
            'id': self.get_id(),
            'created_at': self.convert_epoch_to_iso(item.get('createTime')),
            'updated_at': self.now_iso(),  
            'deleted_at': self.convert_epoch_to_iso(item.get('deleteTime')) if item.get('deleteTime') else None,
            'wallet_code': item.get('walletId'),
            'account_name': item.get('accountName'),
            'account_number': item.get('accountNumber'),
            'bank_id': bank_id,
            'iban': item.get('iban'),
            'status': item.get('status'),
            'verified_at': self.convert_epoch_to_iso(item.get('verifyTime')) if item.get('verifyTime') else None,
            'user_id': user_id,
        }
    
    def get_id(self) -> int:
        """Get the next bank account wallet ID"""
        if not hasattr(self, '_bank_account_wallet_id_counter'):
            self._bank_account_wallet_id_counter = 1
        else:
            self._bank_account_wallet_id_counter += 1
        return self._bank_account_wallet_id_counter
    
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

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for user_bank_account_wallets table"""
        return """
            INSERT INTO user_bank_account_wallets (
               id, created_at, updated_at, deleted_at, wallet_code, account_name, account_number, bank_id, iban, status, verified_at, user_id
            )
            VALUES (%(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(wallet_code)s, %(account_name)s, %(account_number)s, %(bank_id)s, %(iban)s, %(status)s, %(verified_at)s, %(user_id)s)
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at,
                wallet_code = EXCLUDED.wallet_code,
                account_name = EXCLUDED.account_name,
                account_number = EXCLUDED.account_number,
                bank_id = EXCLUDED.bank_id,
                iban = EXCLUDED.iban,
                status = EXCLUDED.status,
                 verified_at = EXCLUDED.verified_at,
                user_id = EXCLUDED.user_id
        """
