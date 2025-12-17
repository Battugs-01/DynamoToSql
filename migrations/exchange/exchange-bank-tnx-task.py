"""
exchange-bank-tnx-task table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration


class ExchangeBankTnxTaskMigration(BaseMigration):
    """Migration for exchange_bank_tnx_task table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "exchange-bank-txn-tasks"
    
    @property
    def postgres_table_name(self) -> str:
        return "exchange-bank-txn-task"

    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB exchange-bank-tnx-task item to PostgreSQL format"""
        # RequestTime is required (not null in Go struct)
        request_time = item.get('requestTime')
        if not request_time:
            print(f"Warning: Item {item.get('txnTaskId', 'unknown')} has no requestTime, skipping")
            return None
        
        # TransferTime is nullable (not null removed from Go struct)
        # If transferTime is missing, use None (NULL)
        transfer_time = item.get('transferTime')
        
        return {
            'id': item.get('txnTaskId'),
            'created_at': self.convert_epoch_to_iso(request_time),
            'updated_at': self.convert_epoch_to_iso(transfer_time) if transfer_time else self.convert_epoch_to_iso(request_time),
            'deleted_at': None,
            'amount': self.convert_to_float(item.get('amount')),
            'currency': item.get('currency'),
            'description': item.get('description'),
            'reason': item.get('reason'),
            'receiver_bank_code': item.get('receiverBankCode'),
            'receiver_iban': item.get('receiverIBAN'),
            'receiver_name': item.get('receiverName'),
            'request_time': self.convert_epoch_to_iso(request_time),
            'sender_bank_code': item.get('senderBankCode'),
            'sender_iban': item.get('senderIBAN'),
            'status': item.get('status'),
            # transfer_time is nullable, use None if missing
            'transfer_time': self.convert_epoch_to_iso(transfer_time) if transfer_time else None,
            'bank_response': self.convert_to_json(item.get('bankResponse')) if item.get('bankResponse') else None,
            'metadata': self.convert_to_json(item.get('metadata')) if item.get('metadata') else None,
        }

    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for exchange-bank-txn-task table"""
        return """
            INSERT INTO "exchange-bank-txn-task" (
               id, created_at, updated_at, deleted_at, amount, currency, description, reason,
               receiver_bank_code, receiver_iban, receiver_name, request_time,
               sender_bank_code, sender_iban, status, transfer_time,
               bank_response, metadata
            )
            VALUES (
               %(id)s, %(created_at)s, %(updated_at)s, %(deleted_at)s, %(amount)s, %(currency)s,
               %(description)s, %(reason)s, %(receiver_bank_code)s, %(receiver_iban)s,
               %(receiver_name)s, %(request_time)s, %(sender_bank_code)s, %(sender_iban)s,
               %(status)s, %(transfer_time)s, %(bank_response)s, %(metadata)s
            )
            ON CONFLICT (id) DO UPDATE SET
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at,
                amount = EXCLUDED.amount,
                currency = EXCLUDED.currency,
                description = EXCLUDED.description,
                reason = EXCLUDED.reason,
                receiver_bank_code = EXCLUDED.receiver_bank_code,
                receiver_iban = EXCLUDED.receiver_iban,
                receiver_name = EXCLUDED.receiver_name,
                request_time = EXCLUDED.request_time,
                sender_bank_code = EXCLUDED.sender_bank_code,
                sender_iban = EXCLUDED.sender_iban,
                status = EXCLUDED.status,
                transfer_time = EXCLUDED.transfer_time,
                bank_response = EXCLUDED.bank_response,
                metadata = EXCLUDED.metadata
        """
