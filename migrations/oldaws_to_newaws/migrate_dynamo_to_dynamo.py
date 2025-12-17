#!/usr/bin/env python3
"""
DynamoDB to DynamoDB Migration Script with S3 Assets
Migrates data from one AWS account's DynamoDB table to another AWS account's DynamoDB table
Also migrates S3 assets (images) and updates URLs in DynamoDB records
"""

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError
import logging
from datetime import datetime
import time
import re
from urllib.parse import urlparse
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'dynamo_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# AWS OLD Credentials
OLD_AWS_ACCESS_KEY = "YOUR_AWS_OLD_ACCESS_KEY"
OLD_AWS_SECRET_KEY = "YOUR_AWS_OLD_SECRET_KEY"
OLD_AWS_REGION = "ap-southeast-1"  # Өөрчлөх шаардлагатай бол

# AWS NEW Credentials
NEW_AWS_ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
NEW_AWS_SECRET_KEY = "YOUR_AWS_SECRET_KEY"
NEW_AWS_REGION = "ap-southeast-1"  # Өөрчлөх шаардлагатай бол

# Table name to migrate
TABLE_NAME = "news"

# S3 Configuration
OLD_S3_BUCKET = "x-meta-asset"
OLD_S3_PREFIX = "news/"
NEW_S3_BUCKET = "x-meta-2-asset"
NEW_S3_PREFIX = "public/assets/news/"

# URL Configuration
OLD_CDN_URL_PREFIX = "https://cdn.x-meta.com/news/"
NEW_CDN_URL_PREFIX = "https://dp1fq59gs1u5e.cloudfront.net/assets/news/"

# Batch size for writing
BATCH_SIZE = 25  # DynamoDB batch_write_item maximum


class DynamoDBMigrator:
    def __init__(self, source_credentials, target_credentials, table_name):
        """
        Initialize DynamoDB and S3 migrator
        
        Args:
            source_credentials: Dict with access_key, secret_key, region for source
            target_credentials: Dict with access_key, secret_key, region for target
            table_name: Name of the table to migrate
        """
        self.table_name = table_name
        
        # Create source DynamoDB client and resource
        self.source_dynamodb_client = boto3.client(
            'dynamodb',
            aws_access_key_id=source_credentials['access_key'],
            aws_secret_access_key=source_credentials['secret_key'],
            region_name=source_credentials['region']
        )
        
        self.source_dynamodb_resource = boto3.resource(
            'dynamodb',
            aws_access_key_id=source_credentials['access_key'],
            aws_secret_access_key=source_credentials['secret_key'],
            region_name=source_credentials['region']
        )
        
        # Create source S3 client
        self.source_s3_client = boto3.client(
            's3',
            aws_access_key_id=source_credentials['access_key'],
            aws_secret_access_key=source_credentials['secret_key'],
            region_name=source_credentials['region']
        )
        
        # Create target DynamoDB client and resource
        self.target_dynamodb_client = boto3.client(
            'dynamodb',
            aws_access_key_id=target_credentials['access_key'],
            aws_secret_access_key=target_credentials['secret_key'],
            region_name=target_credentials['region']
        )
        
        self.target_dynamodb_resource = boto3.resource(
            'dynamodb',
            aws_access_key_id=target_credentials['access_key'],
            aws_secret_access_key=target_credentials['secret_key'],
            region_name=target_credentials['region']
        )
        
        # Create target S3 client
        self.target_s3_client = boto3.client(
            's3',
            aws_access_key_id=target_credentials['access_key'],
            aws_secret_access_key=target_credentials['secret_key'],
            region_name=target_credentials['region']
        )
        
        # Statistics
        self.s3_migrated_count = 0
        self.s3_failed_count = 0
        self.s3_skipped_count = 0
        
        logger.info(f"Initialized migrator for table: {table_name}")
    
    def check_tables_exist(self):
        """Check if source and target tables exist"""
        try:
            # Check source table
            source_response = self.source_dynamodb_client.describe_table(TableName=self.table_name)
            logger.info(f"✓ Source table '{self.table_name}' exists")
            logger.info(f"  Item count: {source_response['Table'].get('ItemCount', 'Unknown')}")
            
            # Check target table
            target_response = self.target_dynamodb_client.describe_table(TableName=self.table_name)
            logger.info(f"✓ Target table '{self.table_name}' exists")
            logger.info(f"  Item count: {target_response['Table'].get('ItemCount', 'Unknown')}")
            
            return True
        except ClientError as e:
            logger.error(f"Error checking tables: {e}")
            return False
    
    def check_s3_buckets_exist(self):
        """Check if source and target S3 buckets exist"""
        try:
            # Check source bucket
            self.source_s3_client.head_bucket(Bucket=OLD_S3_BUCKET)
            logger.info(f"✓ Source S3 bucket '{OLD_S3_BUCKET}' exists")
        except ClientError as e:
            logger.error(f"Error checking source S3 bucket: {e}")
            return False
        
        try:
            # Check target bucket
            self.target_s3_client.head_bucket(Bucket=NEW_S3_BUCKET)
            logger.info(f"✓ Target S3 bucket '{NEW_S3_BUCKET}' exists")
        except ClientError as e:
            # If 403, bucket might exist but no head_bucket permission
            # We'll try to proceed and fail later if needed
            if e.response['Error']['Code'] == '403':
                logger.warning(f"⚠ Cannot verify target S3 bucket '{NEW_S3_BUCKET}' (403 Forbidden)")
                logger.warning(f"  Bucket might exist but lacks HeadBucket permission")
                logger.warning(f"  Proceeding anyway - will fail if cannot write files")
                return True  # Proceed anyway
            else:
                logger.error(f"Error checking target S3 bucket: {e}")
                return False
        
        return True
    
    def scan_source_table(self):
        """
        Scan all items from source table
        
        Returns:
            List of items from source table
        """
        logger.info(f"Starting scan of source table: {self.table_name}")
        
        source_table = self.source_dynamodb_resource.Table(self.table_name)
        items = []
        
        try:
            # Initial scan
            response = source_table.scan()
            items.extend(response.get('Items', []))
            
            # Continue scanning if there's more data
            while 'LastEvaluatedKey' in response:
                logger.info(f"Scanned {len(items)} items so far...")
                response = source_table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            logger.info(f"✓ Completed scan. Total items: {len(items)}")
            return items
            
        except ClientError as e:
            logger.error(f"Error scanning source table: {e}")
            raise
    
    def extract_image_urls(self, item):
        """
        Extract all image URLs from a DynamoDB item
        
        Args:
            item: DynamoDB item dict
            
        Returns:
            List of image URLs found in the item
        """
        urls = []
        
        def extract_from_value(value):
            """Recursively extract URLs from any value"""
            if isinstance(value, str):
                # Check if it's an old CDN URL
                if value.startswith(OLD_CDN_URL_PREFIX):
                    urls.append(value)
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
            elif isinstance(value, list):
                for v in value:
                    extract_from_value(v)
        
        # Check all fields in the item
        extract_from_value(item)
        
        return urls
    
    def migrate_s3_file(self, old_url):
        """
        Migrate a single S3 file from old bucket to new bucket
        
        Args:
            old_url: The old CDN URL
            
        Returns:
            new_url: The new CDN URL, or None if migration failed
        """
        try:
            # Extract filename from URL
            if not old_url.startswith(OLD_CDN_URL_PREFIX):
                logger.warning(f"URL doesn't match old CDN prefix: {old_url}")
                return None
            
            filename = old_url[len(OLD_CDN_URL_PREFIX):]
            
            # Source and destination S3 keys
            source_key = OLD_S3_PREFIX + filename
            dest_key = NEW_S3_PREFIX + filename
            
            # Check if file already exists in target
            try:
                self.target_s3_client.head_object(Bucket=NEW_S3_BUCKET, Key=dest_key)
                logger.debug(f"File already exists in target: {dest_key}")
                self.s3_skipped_count += 1
                return NEW_CDN_URL_PREFIX + filename
            except ClientError:
                pass  # File doesn't exist, proceed with copy
            
            # Download from OLD AWS and upload to NEW AWS
            # This approach works for cross-account transfer
            logger.debug(f"Migrating: {source_key} -> {dest_key}")
            
            # Step 1: Download from OLD AWS
            response = self.source_s3_client.get_object(
                Bucket=OLD_S3_BUCKET,
                Key=source_key
            )
            file_content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            
            # Step 2: Upload to NEW AWS
            self.target_s3_client.put_object(
                Bucket=NEW_S3_BUCKET,
                Key=dest_key,
                Body=file_content,
                ContentType=content_type
            )
            
            self.s3_migrated_count += 1
            new_url = NEW_CDN_URL_PREFIX + filename
            logger.debug(f"✓ Migrated: {filename}")
            
            return new_url
            
        except ClientError as e:
            logger.error(f"Failed to migrate S3 file: {e}")
            self.s3_failed_count += 1
            return None
    
    def update_item_urls(self, item):
        """
        Update all image URLs in a DynamoDB item
        
        Args:
            item: DynamoDB item dict
            
        Returns:
            Updated item with new URLs
        """
        def update_value(value):
            """Recursively update URLs in any value"""
            if isinstance(value, str):
                # Check if it's an old CDN URL
                if value.startswith(OLD_CDN_URL_PREFIX):
                    # Migrate the S3 file
                    new_url = self.migrate_s3_file(value)
                    if new_url:
                        return new_url
                    else:
                        logger.warning(f"Failed to migrate URL, keeping old: {value}")
                        return value
                return value
            elif isinstance(value, dict):
                return {k: update_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [update_value(v) for v in value]
            else:
                return value
        
        # Update all fields in the item
        updated_item = {}
        for key, value in item.items():
            updated_item[key] = update_value(value)
        
        return updated_item
    
    def write_items_batch(self, items):
        """
        Write items to target table in batches (with URL updates)
        
        Args:
            items: List of items to write
        """
        logger.info(f"Starting batch write of {len(items)} items to target table")
        logger.info("Note: S3 files will be migrated and URLs updated during this process")
        
        target_table = self.target_dynamodb_resource.Table(self.table_name)
        success_count = 0
        error_count = 0
        
        # Write items one by one (not using batch_writer to avoid BatchWriteItem permission issue)
        for i, item in enumerate(items):
            try:
                # Update URLs and migrate S3 files
                updated_item = self.update_item_urls(item)
                target_table.put_item(Item=updated_item)
                
                success_count += 1
                
                # Log progress every 10 items
                if (i + 1) % 10 == 0:
                    logger.info(f"✓ Written {success_count}/{len(items)} items")
                
                # Small delay to avoid throttling
                if (i + 1) % 25 == 0:
                    time.sleep(0.1)
                
            except ClientError as e:
                error_count += 1
                logger.error(f"Failed to write item {i+1}: {e}")
        
        logger.info(f"\nDynamoDB Migration Summary:")
        logger.info(f"  Total items: {len(items)}")
        logger.info(f"  Successfully written: {success_count}")
        logger.info(f"  Failed: {error_count}")
        
        logger.info(f"\nS3 Migration Summary:")
        logger.info(f"  Files migrated: {self.s3_migrated_count}")
        logger.info(f"  Files skipped (already exist): {self.s3_skipped_count}")
        logger.info(f"  Files failed: {self.s3_failed_count}")
        
        return success_count, error_count
    
    def migrate(self):
        """
        Main migration function
        """
        logger.info("="*60)
        logger.info("DynamoDB + S3 Migration")
        logger.info("="*60)
        logger.info(f"Source: AWS OLD ({OLD_AWS_REGION})")
        logger.info(f"  - DynamoDB: {self.table_name}")
        logger.info(f"  - S3: {OLD_S3_BUCKET}/{OLD_S3_PREFIX}")
        logger.info(f"Target: AWS NEW ({NEW_AWS_REGION})")
        logger.info(f"  - DynamoDB: {self.table_name}")
        logger.info(f"  - S3: {NEW_S3_BUCKET}/{NEW_S3_PREFIX}")
        logger.info("="*60)
        
        start_time = time.time()
        
        # Step 1: Check DynamoDB tables
        logger.info("\n[Step 1] Checking DynamoDB tables...")
        if not self.check_tables_exist():
            logger.error("DynamoDB table check failed. Aborting migration.")
            return False
        
        # Step 2: Check S3 buckets
        logger.info("\n[Step 2] Checking S3 buckets...")
        if not self.check_s3_buckets_exist():
            logger.error("S3 bucket check failed. Aborting migration.")
            return False
        
        # Step 3: Scan source table
        logger.info("\n[Step 3] Reading data from source DynamoDB table...")
        try:
            items = self.scan_source_table()
            if not items:
                logger.warning("No items found in source table.")
                return True
        except Exception as e:
            logger.error(f"Failed to read source table: {e}")
            return False
        
        # Step 4: Write to target table (includes S3 migration)
        logger.info("\n[Step 4] Migrating data and S3 assets...")
        try:
            success_count, error_count = self.write_items_batch(items)
        except Exception as e:
            logger.error(f"Failed to write to target table: {e}")
            return False
        
        # Summary
        elapsed_time = time.time() - start_time
        logger.info("\n" + "="*60)
        logger.info("Migration Completed!")
        logger.info("="*60)
        logger.info(f"Time taken: {elapsed_time:.2f} seconds ({elapsed_time/60:.1f} minutes)")
        logger.info(f"DynamoDB success rate: {success_count}/{len(items)} ({success_count/len(items)*100:.1f}%)")
        logger.info(f"S3 files migrated: {self.s3_migrated_count}")
        logger.info(f"S3 files skipped: {self.s3_skipped_count}")
        logger.info(f"S3 files failed: {self.s3_failed_count}")
        
        return error_count == 0 and self.s3_failed_count == 0


def main():
    """Main execution function"""
    
    # Setup credentials
    source_credentials = {
        'access_key': OLD_AWS_ACCESS_KEY,
        'secret_key': OLD_AWS_SECRET_KEY,
        'region': OLD_AWS_REGION
    }
    
    target_credentials = {
        'access_key': NEW_AWS_ACCESS_KEY,
        'secret_key': NEW_AWS_SECRET_KEY,
        'region': NEW_AWS_REGION
    }
    
    # Create migrator and run migration
    migrator = DynamoDBMigrator(
        source_credentials=source_credentials,
        target_credentials=target_credentials,
        table_name=TABLE_NAME
    )
    
    try:
        success = migrator.migrate()
        if success:
            logger.info("\n✓ Migration completed successfully!")
            return 0
        else:
            logger.error("\n✗ Migration completed with errors.")
            return 1
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
