#!/usr/bin/env python3
"""
DynamoDB to PostgreSQL Migration CLI

Usage:
    python migrate.py --table users                    # Migrate specific table
    python migrate.py --all                           # Migrate all tables
    python migrate.py --list                          # List available migrations
    python migrate.py --dry-run --table users         # Dry run mode
"""
import argparse
import logging
import sys
from pathlib import Path
from importlib import import_module
from typing import Dict, List

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database import DynamoConfig, PostgresConfig, MigrationConfig
from utils.database import DynamoConnection, PostgresConnection
from utils.migration_base import BaseMigration


# Registry of available migrations
AVAILABLE_MIGRATIONS = {
    'users': 'migrations.users_migration.UsersMigration',
    'banks': 'migrations.banks_migration.BanksMigration',
    'bank-account-wallets': 'migrations.bank-account-wallets_migration.BankAccountWalletsMigration',
    'bank-account-verify-challange': 'migrations.bank-account-verify-challange.BankAccountVerifyChallangeMigration',
    'bank-deposit-history': 'migrations.bank-deposit-history.BankDepositHistoryMigration',
    'bank-widthrawal-history': 'migrations.bank-widthrawal-history.BankWidthrawalHistoryMigration',
    # Add more migrations here as you create them
    # 'products': 'migrations.products_migration.ProductsMigration',
    # 'orders': 'migrations.orders_migration.OrdersMigration',
}


def setup_logging(level: str):
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/migration.log')
        ]
    )


def load_migration_class(module_path: str) -> BaseMigration:
    """Dynamically load migration class"""
    module_name, class_name = module_path.rsplit('.', 1)
    module = import_module(module_name)
    return getattr(module, class_name)


def run_migration(table_name: str, 
                 dynamo_conn: DynamoConnection,
                 postgres_conn: PostgresConnection,
                 migration_config: MigrationConfig) -> Dict[str, int]:
    """Run migration for a specific table"""
    if table_name not in AVAILABLE_MIGRATIONS:
        raise ValueError(f"Migration not found for table: {table_name}")
    
    logger = logging.getLogger(__name__)
    logger.info(f"Running migration for table: {table_name}")
    
    migration_class = load_migration_class(AVAILABLE_MIGRATIONS[table_name])
    
    migration = migration_class(dynamo_conn, postgres_conn, migration_config)
    result = migration.run_migration()
    
    return result


def main():
    parser = argparse.ArgumentParser(description='DynamoDB to PostgreSQL Migration Tool')
    
    parser.add_argument('--table', type=str, help='Migrate specific table')
    parser.add_argument('--all', action='store_true', help='Migrate all tables')
    parser.add_argument('--list', action='store_true', help='List available migrations')
    
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual writes)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for migration')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    if args.list:
        print("Available migrations:")
        for table_name in AVAILABLE_MIGRATIONS.keys():
            print(f"  - {table_name}")
        return
    
    dynamo_config = DynamoConfig.from_env()
    postgres_config = PostgresConfig.from_env()
    migration_config = MigrationConfig(
        batch_size=args.batch_size,
        log_level=args.log_level,
        dry_run=args.dry_run
    )
    
    dynamo_conn = DynamoConnection(dynamo_config)
    postgres_conn = PostgresConnection(postgres_config)
    
    try:
        if args.table:
            result = run_migration(args.table, dynamo_conn, postgres_conn, migration_config)
            logger.info(f"Migration completed for {args.table}: {result}")
            
        elif args.all:
            total_results = {}
            for table_name in AVAILABLE_MIGRATIONS.keys():
                try:
                    result = run_migration(table_name, dynamo_conn, postgres_conn, migration_config)
                    total_results[table_name] = result
                    logger.info(f"Migration completed for {table_name}: {result}")
                except Exception as e:
                    logger.error(f"Migration failed for {table_name}: {e}")
                    total_results[table_name] = {'error': str(e)}
                
            logger.info("=== MIGRATION SUMMARY ===")
            for table_name, result in total_results.items():
                if 'error' in result:
                    logger.error(f"{table_name}: FAILED - {result['error']}")
                else:
                    logger.info(f"{table_name}: SUCCESS - {result['migrated']}/{result['total']} migrated")
        
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    
    finally:
        postgres_conn.close()


if __name__ == '__main__':
    main()
