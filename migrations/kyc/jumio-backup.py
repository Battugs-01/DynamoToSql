"""
Jumio Backup table migration from DynamoDB to PostgreSQL
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration
import logging

logger = logging.getLogger(__name__)


class JumioBackupMigration(BaseMigration):
    """Migration for jumio_backups table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "jumio-backup"
    
    @property
    def postgres_table_name(self) -> str:
        return "jumio_backups"
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB Jumio backup item to PostgreSQL format"""
        # scanReference is required (primary key)
        scan_reference = item.get("scanReference")
        if not scan_reference:
            logger.warning(f"Skipping Jumio backup - missing required scanReference field")
            return None
        
        # All fields are nullable except scanReference
        def get_value_or_none(key):
            """Get value from item, convert empty string to None"""
            val = item.get(key)
            if val == "" or val == "null":
                return None
            return val
        
        # Get infoCreatedAt for timestamps
        info_created_at = item.get("infoCreatedAt")
        created_timestamp = self.convert_epoch_to_iso(info_created_at) if info_created_at else self.now_iso()
        
        return {
            'id': scan_reference,  # Use scanReference as id
            'scan_reference': scan_reference,
            'customer_id': get_value_or_none("customerId"),
            'first_name': get_value_or_none("firstName"),
            'last_name': get_value_or_none("lastName"),
            'type': get_value_or_none("type"),
            'detail_status': item.get("detailStatus"),
            'info_created_at': info_created_at,
            'country': self.convert_to_json(item.get("country")),
            'detail': self.convert_to_json(item.get("detail")),
            'images': self.convert_to_json(item.get("images")),
            'liveness_images': self.convert_to_json(item.get("liveness_images")),
            
            # Timestamps - created_at and updated_at are NOT NULL in PostgreSQL
            'created_at': created_timestamp,
            'updated_at': created_timestamp,
            'deleted_at': None,
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for jumio_backups table"""
        return """
            INSERT INTO jumio_backups (
                id, scan_reference, customer_id, first_name, last_name,
                type, detail_status, info_created_at, country, detail,
                images, liveness_images, created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(scan_reference)s, %(customer_id)s, %(first_name)s, %(last_name)s,
                %(type)s, %(detail_status)s, %(info_created_at)s, %(country)s, %(detail)s,
                %(images)s, %(liveness_images)s, %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO NOTHING
        """
    
    def get_upsert_query(self) -> str:
        """Get PostgreSQL UPSERT query for jumio_backups table"""
        return """
            INSERT INTO jumio_backups (
                id, scan_reference, customer_id, first_name, last_name,
                type, detail_status, info_created_at, country, detail,
                images, liveness_images, created_at, updated_at, deleted_at
            )
            VALUES (
                %(id)s, %(scan_reference)s, %(customer_id)s, %(first_name)s, %(last_name)s,
                %(type)s, %(detail_status)s, %(info_created_at)s, %(country)s, %(detail)s,
                %(images)s, %(liveness_images)s, %(created_at)s, %(updated_at)s, %(deleted_at)s
            )
            ON CONFLICT (id) DO UPDATE SET
                scan_reference = EXCLUDED.scan_reference,
                customer_id = EXCLUDED.customer_id,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                type = EXCLUDED.type,
                detail_status = EXCLUDED.detail_status,
                info_created_at = EXCLUDED.info_created_at,
                country = EXCLUDED.country,
                detail = EXCLUDED.detail,
                images = EXCLUDED.images,
                liveness_images = EXCLUDED.liveness_images,
                updated_at = EXCLUDED.updated_at,
                deleted_at = EXCLUDED.deleted_at
        """
