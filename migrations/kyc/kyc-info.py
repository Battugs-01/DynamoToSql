"""
KYC Info table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class KYCInfoMigration(BaseMigration):
    """Migration for kyc_infos table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "KYC-info"
    
    @property
    def postgres_table_name(self) -> str:
        return "kyc_infos"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB KYC info item to PostgreSQL format"""
        # uid is required (maps to user_id)
        user_id = item.get("uid")
        if not user_id:
            logger.warning(f"Skipping KYC info - missing required uid field")
            return None
        
        # Check if user exists in PostgreSQL users table (foreign key constraint)
        if not hasattr(self, '_valid_user_ids'):
            try:
                import psycopg2
                conn = psycopg2.connect(host='localhost', database='xmeta', user='postgres', password='Pass1234!')
                cur = conn.cursor()
                cur.execute('SELECT id FROM users;')
                self._valid_user_ids = set([row[0] for row in cur.fetchall()])
                cur.close()
                conn.close()
                logger.info(f"Loaded {len(self._valid_user_ids)} valid user IDs from PostgreSQL")
            except Exception as e:
                logger.warning(f"Could not load user IDs from PostgreSQL: {e}")
                self._valid_user_ids = None
        
        # Skip if user doesn't exist in users table
        if self._valid_user_ids is not None and user_id not in self._valid_user_ids:
            logger.debug(f"Skipping KYC info for uid {user_id} - user not found in users table")
            return None
        
        # All fields are nullable in PostgreSQL - handle empty strings as None
        def get_value_or_none(key):
            """Get value from item, convert empty string to None"""
            val = item.get(key)
            if val == "" or val == "null":
                return None
            return val
        
        return {
            'id': user_id,  # Use user_id as id (UUID format like other tables)
            'user_id': user_id,
            'email_status': item.get("emailStatus"),
            'fail_reason': get_value_or_none("failReason"),
            'initiate_response': self.convert_to_json(item.get("initiateResponse")),
            'kyc_passed': item.get("kycPassed"),
            'kyc_status': get_value_or_none("kycStatus"),
            'kyc_user_id': get_value_or_none("kycUserId"),
            'verification_status': get_value_or_none("verificationStatus"),
            
            # Link KYC fields - only present when KYC is SUCCESS
            'link_address': item.get("link_address"),
            'link_country': get_value_or_none("link_country"),
            'link_dob': get_value_or_none("link_dob"),
            'link_document_id': get_value_or_none("link_documentId"),
            'link_document_type': get_value_or_none("link_documentType"),
            'link_expiry_date': get_value_or_none("link_expiryDate"),
            'link_first_name': get_value_or_none("link_firstName"),
            'link_gender': item.get("link_gender"),
            'link_kyc_level_name': get_value_or_none("link_kycLevelName"),
            'link_last_name': get_value_or_none("link_lastName"),
            'link_middle_name': get_value_or_none("link_middleName"),
            'link_nationality': get_value_or_none("link_nationality"),
            'link_pep': item.get("link_pep"),
            'link_residence_country': get_value_or_none("link_residenceCountry"),
            'link_risk_level': get_value_or_none("link_riskLevel"),
            'link_risk_score': item.get("link_riskScore"),
            'link_sanction_hit': item.get("link_sanctionHit"),
            'link_withdraw_crypto_daily_limit': self.convert_to_float(item.get("link_withdrawCryptoDailyLimit")) if item.get("link_withdrawCryptoDailyLimit") is not None else None,
            'link_withdraw_fiat_daily_limit': self.convert_to_float(item.get("link_withdrawFiatDailyLimit")) if item.get("link_withdrawFiatDailyLimit") is not None else None,
            
            # Timestamps - created_at and updated_at are NOT NULL in PostgreSQL
            'created_at': self.convert_epoch_to_iso(item.get("createdAt")) or self.convert_epoch_to_iso(item.get("updatedAt")) or self.now_iso(),
            'updated_at': self.convert_epoch_to_iso(item.get("updatedAt")) or self.convert_epoch_to_iso(item.get("createdAt")) or self.now_iso(),
            'deleted_at': self.convert_epoch_to_iso(item.get("deletedAt")) if item.get("deletedAt") else None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for kyc_infos table (skip existing by user_id)"""
        return """
            INSERT INTO kyc_infos (
                id, user_id, email_status, fail_reason, initiate_response,
                kyc_passed, kyc_status, kyc_user_id, verification_status,
                link_address, link_country, link_dob, link_document_id, link_document_type,
                link_expiry_date, link_first_name, link_gender, link_kyc_level_name,
                link_last_name, link_middle_name, link_nationality, link_pep,
                link_residence_country, link_risk_level, link_risk_score, link_sanction_hit,
                link_withdraw_crypto_daily_limit, link_withdraw_fiat_daily_limit,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(user_id)s, %(email_status)s, %(fail_reason)s, %(initiate_response)s,
                %(kyc_passed)s, %(kyc_status)s, %(kyc_user_id)s, %(verification_status)s,
                %(link_address)s, %(link_country)s, %(link_dob)s, %(link_document_id)s, %(link_document_type)s,
                %(link_expiry_date)s, %(link_first_name)s, %(link_gender)s, %(link_kyc_level_name)s,
                %(link_last_name)s, %(link_middle_name)s, %(link_nationality)s, %(link_pep)s,
                %(link_residence_country)s, %(link_risk_level)s, %(link_risk_score)s, %(link_sanction_hit)s,
                %(link_withdraw_crypto_daily_limit)s, %(link_withdraw_fiat_daily_limit)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for kyc_infos table (update existing by user_id)"""
        return """
            INSERT INTO kyc_infos (
                id, user_id, email_status, fail_reason, initiate_response,
                kyc_passed, kyc_status, kyc_user_id, verification_status,
                link_address, link_country, link_dob, link_document_id, link_document_type,
                link_expiry_date, link_first_name, link_gender, link_kyc_level_name,
                link_last_name, link_middle_name, link_nationality, link_pep,
                link_residence_country, link_risk_level, link_risk_score, link_sanction_hit,
                link_withdraw_crypto_daily_limit, link_withdraw_fiat_daily_limit,
                created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(user_id)s, %(email_status)s, %(fail_reason)s, %(initiate_response)s,
                %(kyc_passed)s, %(kyc_status)s, %(kyc_user_id)s, %(verification_status)s,
                %(link_address)s, %(link_country)s, %(link_dob)s, %(link_document_id)s, %(link_document_type)s,
                %(link_expiry_date)s, %(link_first_name)s, %(link_gender)s, %(link_kyc_level_name)s,
                %(link_last_name)s, %(link_middle_name)s, %(link_nationality)s, %(link_pep)s,
                %(link_residence_country)s, %(link_risk_level)s, %(link_risk_score)s, %(link_sanction_hit)s,
                %(link_withdraw_crypto_daily_limit)s, %(link_withdraw_fiat_daily_limit)s,
                %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                email_status = EXCLUDED.email_status,
                fail_reason = EXCLUDED.fail_reason,
                initiate_response = EXCLUDED.initiate_response,
                kyc_passed = EXCLUDED.kyc_passed,
                kyc_status = EXCLUDED.kyc_status,
                kyc_user_id = EXCLUDED.kyc_user_id,
                verification_status = EXCLUDED.verification_status,
                link_address = EXCLUDED.link_address,
                link_country = EXCLUDED.link_country,
                link_dob = EXCLUDED.link_dob,
                link_document_id = EXCLUDED.link_document_id,
                link_document_type = EXCLUDED.link_document_type,
                link_expiry_date = EXCLUDED.link_expiry_date,
                link_first_name = EXCLUDED.link_first_name,
                link_gender = EXCLUDED.link_gender,
                link_kyc_level_name = EXCLUDED.link_kyc_level_name,
                link_last_name = EXCLUDED.link_last_name,
                link_middle_name = EXCLUDED.link_middle_name,
                link_nationality = EXCLUDED.link_nationality,
                link_pep = EXCLUDED.link_pep,
                link_residence_country = EXCLUDED.link_residence_country,
                link_risk_level = EXCLUDED.link_risk_level,
                link_risk_score = EXCLUDED.link_risk_score,
                link_sanction_hit = EXCLUDED.link_sanction_hit,
                link_withdraw_crypto_daily_limit = EXCLUDED.link_withdraw_crypto_daily_limit,
                link_withdraw_fiat_daily_limit = EXCLUDED.link_withdraw_fiat_daily_limit,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
