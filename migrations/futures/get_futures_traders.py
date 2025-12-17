#!/usr/bin/env python3
"""
Get users from xmeta-users table where futuresTrade = true
"""

import boto3
from boto3.dynamodb.conditions import Attr
import json
from datetime import datetime

# NEW AWS Credentials
NEW_AWS_ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
NEW_AWS_SECRET_KEY = "YOUR_AWS_SECRET_KEY"
NEW_AWS_REGION = "ap-southeast-1"

TABLE_NAME = "xmeta-users"

print("="*70)
print("Fetching users with futuresTrade = 1 (enabled)")
print("="*70)
print(f"Table: {TABLE_NAME}")
print(f"Region: {NEW_AWS_REGION}")
print()

# Connect to DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=NEW_AWS_ACCESS_KEY,
    aws_secret_access_key=NEW_AWS_SECRET_KEY,
    region_name=NEW_AWS_REGION
)

table = dynamodb.Table(TABLE_NAME)

# Check if table exists
try:
    table_info = table.table_status
    print(f"✓ Table '{TABLE_NAME}' found")
    print()
except Exception as e:
    print(f"✗ Error accessing table: {e}")
    exit(1)

# Scan table with filter
print("Scanning table for users with futuresTrade = 1...")
print("This may take a moment for large tables...")
print()

futures_traders = []
scanned_count = 0

try:
    # Initial scan with filter (futuresTrade = 1, not boolean true)
    response = table.scan(
        FilterExpression=Attr('futuresTrade').eq(1)
    )
    
    futures_traders.extend(response.get('Items', []))
    scanned_count += response.get('ScannedCount', 0)
    
    # Continue scanning if there's more data
    while 'LastEvaluatedKey' in response:
        print(f"  Scanned {scanned_count} items so far, found {len(futures_traders)} matches...")
        response = table.scan(
            FilterExpression=Attr('futuresTrade').eq(1),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        futures_traders.extend(response.get('Items', []))
        scanned_count += response.get('ScannedCount', 0)
    
    print(f"✓ Scan completed!")
    print(f"  Total items scanned: {scanned_count}")
    print(f"  Users with futuresTrade = 1: {len(futures_traders)}")
    print()
    
except Exception as e:
    print(f"✗ Error scanning table: {e}")
    exit(1)

# Display results
if len(futures_traders) == 0:
    print("No users found with futuresTrade = 1")
else:
    print("="*70)
    print(f"Found {len(futures_traders)} users with futuresTrade = 1")
    print("="*70)
    print()
    
    # Display first 10 users
    display_count = min(10, len(futures_traders))
    print(f"Showing first {display_count} users:\n")
    
    for i, user in enumerate(futures_traders[:display_count], 1):
        print(f"--- User {i} ---")
        print(f"ID: {user.get('id', 'N/A')}")
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Username: {user.get('username', user.get('userName', 'N/A'))}")
        print(f"futuresTrade: {user.get('futuresTrade', 'N/A')}")
        print()
    
    if len(futures_traders) > 10:
        print(f"... and {len(futures_traders) - 10} more users")
        print()
    
    # Save to file
    output_file = f"futures_traders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(futures_traders, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"✓ Full list saved to: {output_file}")
    print()

# Summary
print("="*70)
print("Summary")
print("="*70)
print(f"Total users scanned: {scanned_count}")
print(f"Users with futuresTrade = 1: {len(futures_traders)}")
print(f"Percentage: {len(futures_traders)/scanned_count*100:.1f}%" if scanned_count > 0 else "N/A")
print("="*70)
