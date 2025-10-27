"""
Template for creating new table migrations
Copy this file and customize for your table.
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration


class TableNameMigration(BaseMigration):
    """Migration for [TABLE_NAME] table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "your-dynamodb-table-name" 
    
    @property
    def postgres_table_name(self) -> str:
        return "your_postgres_table_name" 
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB item to PostgreSQL format"""
        return {
            'id': item.get("id"),  
            'name': item.get("name"),
            'created_at': self.convert_epoch_to_iso(item.get("createdAt")),
            'updated_at': self.convert_epoch_to_iso(item.get("updatedAt")),
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query"""
        return """
            INSERT INTO your_table_name (
                id, name, created_at, updated_at
            )
            VALUES (%(id)s, %(name)s, %(created_at)s, %(updated_at)s)
            ON CONFLICT (id) DO NOTHING
        """
