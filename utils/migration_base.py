"""
Base migration utility class
"""
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from decimal import Decimal

from psycopg2 import sql
from psycopg2.extras import Json

from utils.database import DynamoConnection, PostgresConnection
from config.database import MigrationConfig

logger = logging.getLogger(__name__)


class BaseMigration(ABC):
    """Base class for all table migrations"""
    
    def __init__(self, 
                 dynamo_conn: DynamoConnection, 
                 postgres_conn: PostgresConnection,
                 config: MigrationConfig):
        self.dynamo = dynamo_conn
        self.postgres = postgres_conn
        self.config = config
        self.migrated_count = 0
        self.error_count = 0
    
    @property
    @abstractmethod
    def dynamo_table_name(self) -> str:
        """DynamoDB table name"""
        pass
    
    @property
    @abstractmethod
    def postgres_table_name(self) -> str:
        """PostgreSQL table name"""
        pass
    
    @abstractmethod
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB item to PostgreSQL format"""
        pass
    
    @abstractmethod
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query"""
        pass
    
    def convert_epoch_to_iso(self, epoch_value: Any) -> Optional[str]:
        """Convert epoch timestamp to ISO8601 format"""
        if epoch_value is None:
            return None
        try:
            epoch_float = float(epoch_value) / 1000
            dt = datetime.fromtimestamp(epoch_float, tz=timezone.utc)
            return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert epoch {epoch_value}: {e}")
            return None
    
    def convert_to_boolean(self, value: Any) -> Optional[bool]:
        """Convert value to boolean (handles 0/1 to False/True)"""
        if value is None:
            return None
        return bool(value)

    def now_iso(self) -> str:
        """Get current time in ISO8601 format"""
        return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    def convert_to_integer(self, value: Any) -> Optional[int]:
        """Convert value to integer"""
        if value is None:
            return None
        return int(value)

    def convert_to_float(self, value: Any) -> Optional[float]:
        """Convert value to float"""
        if value is None:
            return None
        return float(value)

    def convert_decimal_to_number(self, obj):
        """Recursively convert Decimal objects to int/float for JSON serialization"""
        if isinstance(obj, dict):
            return {key: self.convert_decimal_to_number(val) for key, val in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_decimal_to_number(item) for item in obj]
        elif isinstance(obj, Decimal):
            # Convert Decimal to int if it's a whole number, otherwise float
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        else:
            return obj
    
    
    def convert_to_string(self, value: Any) -> Optional[str]:
        """Convert value to string"""
        if value is None:
            return None
        return str(value)

    def convert_to_json(self, value: Any) -> Optional[Json]:
        """Convert dict to PostgreSQL JSON, handling Decimal objects"""
        if value is None:
            return None
        cleaned_value = self.convert_decimal_to_number(value)
        return Json(cleaned_value)
    
    def scan_dynamodb_table(self) -> List[Dict[str, Any]]:
        """Scan DynamoDB table and return all items"""
        logger.info(f"Scanning DynamoDB table: {self.dynamo_table_name}")
        
        table = self.dynamo.get_table(self.dynamo_table_name)
        items = []
        
        response = table.scan(Limit=self.config.batch_size)
        items.extend(response.get('Items', []))
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                Limit=self.config.batch_size,
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response.get('Items', []))
            logger.info(f"Scanned {len(items)} items so far...")
        
        logger.info(f"Total items found: {len(items)}")
        return items
    
    def insert_items(self, items: List[Dict[str, Any]]):
        """Insert transformed items into PostgreSQL with batch processing"""
        if self.config.dry_run:
            logger.info(f"DRY RUN: Would insert {len(items)} items")
            return
        
        cursor = self.postgres.get_cursor()
        query = self.get_insert_query()
        batch_size = 100
        
        for i, item in enumerate(items):
            try:
                transformed = self.transform_item(item)
                cursor.execute(query, transformed)
                self.migrated_count += 1
                
                if (i + 1) % batch_size == 0:
                    self.postgres.commit()
                    logger.info(f"Migrated {self.migrated_count} items (committed batch)...")
                    
            except Exception as e:
                item_id = item.get('uid', item.get('id', 'unknown'))
                logger.error(f"Failed to insert item {item_id}: {e}")
                self.error_count += 1
                
                self.postgres.rollback()
                cursor = self.postgres.get_cursor()
        
        try:
            self.postgres.commit()
            logger.info(f"Final batch committed. Total migrated: {self.migrated_count}")
        except Exception as e:
            logger.error(f"Failed to commit final batch: {e}")
            self.postgres.rollback()
    
    def run_migration(self) -> Dict[str, int]:
        """Run the complete migration"""
        logger.info(f"Starting migration: {self.dynamo_table_name} -> {self.postgres_table_name}")
        
        try:
            items = self.scan_dynamodb_table()
            
            self.insert_items(items)
            
            logger.info(f"Migration completed. Migrated: {self.migrated_count}, Errors: {self.error_count}")
            
            return {
                'migrated': self.migrated_count,
                'errors': self.error_count,
                'total': len(items)
            }
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.postgres.rollback()
            raise
