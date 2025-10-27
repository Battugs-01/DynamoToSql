"""
Database configuration settings
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DynamoConfig:
    """DynamoDB configuration"""
    region: str
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        return cls(
            region=os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-1'),
            access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )


@dataclass
class PostgresConfig:
    """PostgreSQL configuration"""
    host: str = "localhost"
    port: int = 5433
    database: str = "x-meta"
    user: str = "postgres"
    password: str = "Pass1234!"
    
    @classmethod
    def from_env(cls):
        return cls(
            host=os.getenv('PG_HOST', 'localhost'),
            port=int(os.getenv('PG_PORT', '5433')),
            database=os.getenv('PG_DATABASE', 'x-meta'),
            user=os.getenv('PG_USER', 'postgres'),
            password=os.getenv('PG_PASSWORD', 'Pass1234!')
        )
    
    @property
    def connection_string(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class MigrationConfig:
    """Migration settings"""
    batch_size: int = 100
    log_level: str = "INFO"
    dry_run: bool = False
    
    @classmethod
    def from_env(cls):
        return cls(
            batch_size=int(os.getenv('MIGRATION_BATCH_SIZE', '100')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            dry_run=os.getenv('DRY_RUN', 'false').lower() == 'true'
        )
