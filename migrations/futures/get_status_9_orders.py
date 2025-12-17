#!/usr/bin/env python3
"""
Get orders from f-order-history table where status = 9
"""

import boto3
from boto3.dynamodb.conditions import Attr
import json
from datetime import datetime

# NEW AWS Credentials
NEW_AWS_ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
NEW_AWS_SECRET_KEY = "YOUR_AWS_SECRET_KEY"
NEW_AWS_REGION = "ap-southeast-1"

TABLE_NAME = "f-order-history"

print("="*70)
print("Fetching orders with status = 9")
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

# First, check structure of one item
print("Checking table structure (first item)...")
try:
    sample_response = table.scan(Limit=1)
    if sample_response['Items']:
        sample_item = sample_response['Items'][0]
        print("\nSample item fields:")
        for key in sorted(sample_item.keys()):
            value = sample_item[key]
            if isinstance(value, str) and len(str(value)) > 50:
                value = str(value)[:50] + '...'
            print(f"  {key}: {value}")
        print()
except Exception as e:
    print(f"Warning: Could not get sample item: {e}")
    print()

# Scan table with filter
print("Scanning table for orders with status = 9...")
print("This may take a moment for large tables...")
print()

status_9_orders = []
scanned_count = 0
unique_uids = set()

try:
    # Initial scan with filter
    response = table.scan(
        FilterExpression=Attr('status').eq(9)
    )
    
    status_9_orders.extend(response.get('Items', []))
    scanned_count += response.get('ScannedCount', 0)
    
    # Collect unique UIDs
    for order in response.get('Items', []):
        uid = order.get('uid')
        if uid:
            unique_uids.add(uid)
    
    # Continue scanning if there's more data
    while 'LastEvaluatedKey' in response:
        print(f"  Scanned {scanned_count} items so far, found {len(status_9_orders)} matches, {len(unique_uids)} unique users...")
        response = table.scan(
            FilterExpression=Attr('status').eq(9),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        status_9_orders.extend(response.get('Items', []))
        scanned_count += response.get('ScannedCount', 0)
        
        # Collect unique UIDs
        for order in response.get('Items', []):
            uid = order.get('uid')
            if uid:
                unique_uids.add(uid)
    
    print(f"✓ Scan completed!")
    print(f"  Total items scanned: {scanned_count}")
    print(f"  Orders with status = 9: {len(status_9_orders)}")
    print(f"  Unique users (UIDs): {len(unique_uids)}")
    print()
    
except Exception as e:
    print(f"✗ Error scanning table: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Display results
if len(status_9_orders) == 0:
    print("No orders found with status = 9")
else:
    print("="*70)
    print(f"Found {len(status_9_orders)} orders with status = 9")
    print(f"From {len(unique_uids)} unique users")
    print("="*70)
    print()
    
    # Display first 10 orders
    display_count = min(10, len(status_9_orders))
    print(f"Showing first {display_count} orders:\n")
    
    for i, order in enumerate(status_9_orders[:display_count], 1):
        print(f"--- Order {i} ---")
        print(f"UID: {order.get('uid', 'N/A')}")
        print(f"Order ID: {order.get('orderId', order.get('id', 'N/A'))}")
        print(f"Status: {order.get('status', 'N/A')}")
        print(f"Symbol: {order.get('symbol', 'N/A')}")
        print(f"Side: {order.get('side', 'N/A')}")
        print(f"Quantity: {order.get('quantity', order.get('qty', 'N/A'))}")
        print()
    
    if len(status_9_orders) > 10:
        print(f"... and {len(status_9_orders) - 10} more orders")
        print()
    
    # Save orders to file
    orders_file = f"status_9_orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(orders_file, 'w', encoding='utf-8') as f:
        json.dump(status_9_orders, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"✓ Full orders list saved to: {orders_file}")
    
    # Save unique UIDs to file
    uids_file = f"status_9_uids_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(uids_file, 'w', encoding='utf-8') as f:
        json.dump(list(unique_uids), f, indent=2, ensure_ascii=False)
    
    print(f"✓ Unique UIDs saved to: {uids_file}")
    print()

# Summary
print("="*70)
print("Summary")
print("="*70)
print(f"Total orders scanned: {scanned_count}")
print(f"Orders with status = 9: {len(status_9_orders)}")
print(f"Unique users (UIDs): {len(unique_uids)}")
if scanned_count > 0:
    print(f"Percentage of orders: {len(status_9_orders)/scanned_count*100:.1f}%")
print("="*70)
