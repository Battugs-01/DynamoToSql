"""
banks table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import uuid


class BankAccountVerifyChallangeMigration(BaseMigration):
    """Migration for user_bank_account_verify_challange table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "user-bank-account-verification-challenges"
    
    @property
    def postgres_table_name(self) -> str:
        return "bank_account_verification_challenges"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB user_bank_account_verify_challange item to PostgreSQL format"""
        # Use code as a deterministic ID base to avoid conflicts
        wallet_code = item.get('walletId')
        bank_code = item.get('bankCode')
        return {
            'id': str(uuid.uuid4()),
            'created_at': self.convert_epoch_to_iso(item.get('createTime')),
            'updated_at': self.convert_epoch_to_iso(item.get('createTime')),
            'deleted_at': self.convert_epoch_to_iso(item.get('deleteTime')) if item.get('deleteTime') else None,
            'wallet_id': self.get_wallet_id(wallet_code),
            'account_number': item.get('accountNumber'),
            'bank_id': self.get_bank_id(bank_code),
            'challenge_otp': item.get('challengeOTP'),
            'otp_txn_time': self.convert_epoch_to_iso(item.get('otpTxnTime')) if item.get('otpTxnTime') else None,
            'iban': item.get('iban'),
            'metadata': self.convert_to_json(item.get('metadata')) if item.get('metadata') else None,
            'status': item.get('status'),
            'verified_at': self.convert_epoch_to_iso(item.get('verifyTime')) if item.get('verifyTime') else None,
            'user_id': item.get('userId'),
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
    
    def get_wallet_id(self, wallet_code: str) -> str:
        """Get wallet ID from wallet ID"""
        cursor = self.postgres.get_cursor()
        cursor.execute(
            "SELECT id FROM user_bank_account_wallets WHERE wallet_code = %s",
            (wallet_code,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:   
            raise ValueError(f"Wallet {wallet_code} not found")

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for bank_account_verification_challenges table"""
        return """
            INSERT INTO bank_account_verification_challenges (
               id, created_at, updated_at, deleted_at, wallet_id, account_number, bank_id, challenge_otp, otp_txn_time, iban, metadata, status, verified_at, user_id
            )
            VALUES (%(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(wallet_id)s, %(account_number)s, %(bank_id)s, %(challenge_otp)s, %(otp_txn_time)s, %(iban)s, %(metadata)s, %(status)s, %(verified_at)s, %(user_id)s)
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at,
                wallet_id = EXCLUDED.wallet_id,
                account_number = EXCLUDED.account_number,
                bank_id = EXCLUDED.bank_id,
                challenge_otp = EXCLUDED.challenge_otp,
                otp_txn_time = EXCLUDED.otp_txn_time,
                iban = EXCLUDED.iban,
                status = EXCLUDED.status,
                verified_at = EXCLUDED.verified_at,
                user_id = EXCLUDED.user_id
        """
