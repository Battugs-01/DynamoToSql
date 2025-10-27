"""
Example: Products table migration from DynamoDB to PostgreSQL
This is an example of how to create a new migration for a different table.
"""
from typing import Dict, Any
from utils.migration_base import BaseMigration


class ProductsMigration(BaseMigration):
    """Example migration for products table"""
    
    @property
    def dynamo_table_name(self) -> str:
        return "xmeta-products"  # Your DynamoDB table name
    
    @property
    def postgres_table_name(self) -> str:
        return "products"  # Your PostgreSQL table name
    
    def transform_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Transform DynamoDB product item to PostgreSQL format"""
        return {
            'id': item.get("productId"),  # Map productId -> id
            'name': item.get("name"),
            'description': item.get("description"),
            'price': float(item.get("price", 0)) if item.get("price") else None,
            'category_id': item.get("categoryId"),
            'is_active': self.convert_to_boolean(item.get("isActive")),
            'in_stock': self.convert_to_boolean(item.get("inStock")),
            'stock_count': item.get("stockCount"),
            'tags': self.convert_to_json(item.get("tags")),  # JSON array
            'metadata': self.convert_to_json(item.get("metadata")),  # JSON object
            'created_at': self.convert_epoch_to_iso(item.get("createdAt")),
            'updated_at': self.convert_epoch_to_iso(item.get("updatedAt")),
        }
    
    def get_insert_query(self) -> str:
        """Get PostgreSQL INSERT query for products table"""
        return """
            INSERT INTO products (
                id, name, description, price, category_id, 
                is_active, in_stock, stock_count, tags, metadata,
                created_at, updated_at
            )
            VALUES (%(id)s, %(name)s, %(description)s, %(price)s, %(category_id)s,
                    %(is_active)s, %(in_stock)s, %(stock_count)s, %(tags)s, %(metadata)s,
                    %(created_at)s, %(updated_at)s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                price = EXCLUDED.price,
                is_active = EXCLUDED.is_active,
                in_stock = EXCLUDED.in_stock,
                stock_count = EXCLUDED.stock_count,
                tags = EXCLUDED.tags,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at
        """
