"""
Database connection utilities
"""
import boto3
import psycopg2
from psycopg2 import sql
from config.database import DynamoConfig, PostgresConfig
import logging

logger = logging.getLogger(__name__)


class DynamoConnection:
    """DynamoDB connection manager"""
    
    def __init__(self, config: DynamoConfig):
        self.config = config
        self._resource = None
    
    @property
    def resource(self):
        if self._resource is None:
            if self.config.access_key_id and self.config.secret_access_key:
                self._resource = boto3.resource(
                    'dynamodb',
                    region_name=self.config.region,
                    aws_access_key_id=self.config.access_key_id,
                    aws_secret_access_key=self.config.secret_access_key
                )
            else:
                self._resource = boto3.resource('dynamodb', region_name=self.config.region)
        return self._resource
    
    def get_table(self, table_name: str):
        """Get DynamoDB table"""
        return self.resource.Table(table_name)


class PostgresConnection:
    """PostgreSQL connection manager"""
    
    def __init__(self, config: PostgresConfig):
        self.config = config
        self._connection = None
    
    @property
    def connection(self):
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
        return self._connection
    
    def get_cursor(self):
        """Get database cursor"""
        return self.connection.cursor()
    
    def commit(self):
        """Commit transaction"""
        self.connection.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.connection.rollback()
    
    def close(self):
        """Close connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
