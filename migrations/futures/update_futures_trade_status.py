#!/usr/bin/env python3
"""
Update futuresTrade status:
- Keep futuresTrade = 1 ONLY for users with status = 9 orders
- Set futuresTrade = 0 for all other users who currently have futuresTrade = 1
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from datetime import datetime

# NEW AWS Credentials
NEW_AWS_ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
NEW_AWS_SECRET_KEY = "YOUR_AWS_SECRET_KEY"
NEW_AWS_REGION = "ap-southeast-1"

USERS_TABLE = "xmeta-users"

print("="*70)
print("Update futuresTrade Status")
print("="*70)
print()

# Connect to DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=NEW_AWS_ACCESS_KEY,
    aws_secret_access_key=NEW_AWS_SECRET_KEY,
    region_name=NEW_AWS_REGION
)

users_table = dynamodb.Table(USERS_TABLE)

# Step 1: Load UIDs with status = 9 from saved file
print("[Step 1] Loading UIDs from status = 9 orders...")
try:
    with open('status_9_uids_20251125_153830.json', 'r') as f:
        status_9_uids = json.load(f)
    print(f"✓ Loaded {len(status_9_uids)} UIDs with status = 9")
    print(f"  These users will keep futuresTrade = 1")
    print()
except FileNotFoundError:
    print("✗ Error: status_9_uids file not found!")
    print("  Please run get_status_9_orders.py first")
    exit(1)

# Step 2: Get all users with futuresTrade = 1
print("[Step 2] Getting all users with futuresTrade = 1...")
futures_users = []
scanned_count = 0

try:
    response = users_table.scan(
        FilterExpression=Attr('futuresTrade').eq(1)
    )
    
    futures_users.extend(response.get('Items', []))
    scanned_count += response.get('ScannedCount', 0)
    
    while 'LastEvaluatedKey' in response:
        print(f"  Scanned {scanned_count} items, found {len(futures_users)} with futuresTrade=1...")
        response = users_table.scan(
            FilterExpression=Attr('futuresTrade').eq(1),
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        futures_users.extend(response.get('Items', []))
        scanned_count += response.get('ScannedCount', 0)
    
    print(f"✓ Found {len(futures_users)} users with futuresTrade = 1")
    print()
    
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Step 3: Identify users to update
print("[Step 3] Identifying users to update...")
users_to_disable = []

for user in futures_users:
    uid = user.get('uid')
    if uid and uid not in status_9_uids:
        users_to_disable.append(user)

print(f"  Users with status = 9 (keep futuresTrade=1): {len(status_9_uids)}")
print(f"  Users to disable (set futuresTrade=0): {len(users_to_disable)}")
print()

# Step 4: Confirm before updating
print("="*70)
print("CONFIRMATION")
print("="*70)
print(f"About to update {len(users_to_disable)} users:")
print(f"  - Set futuresTrade = 0 for {len(users_to_disable)} users")
print(f"  - Keep futuresTrade = 1 for {len(status_9_uids)} users (with status=9 orders)")
print()
print("Status = 9 UIDs that will keep futuresTrade = 1:")
for i, uid in enumerate(status_9_uids, 1):
    print(f"  {i}. {uid}")
print()

response = input("Continue? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("Cancelled by user")
    exit(0)

print()
print("[Step 5] Updating users...")

# Update users
updated_count = 0
failed_count = 0
failed_users = []

for i, user in enumerate(users_to_disable, 1):
    uid = user.get('uid')
    email = user.get('email', 'N/A')
    
    try:
        # Update futuresTrade to 0
        users_table.update_item(
            Key={'uid': uid},
            UpdateExpression='SET futuresTrade = :val',
            ExpressionAttributeValues={':val': 0}
        )
        updated_count += 1
        
        if i % 100 == 0:
            print(f"  Updated {updated_count}/{len(users_to_disable)} users...")
        
    except Exception as e:
        failed_count += 1
        failed_users.append({'uid': uid, 'email': email, 'error': str(e)})
        print(f"  ✗ Failed to update {email} ({uid}): {e}")

print(f"✓ Update completed!")
print()

# Save results
results = {
    'timestamp': datetime.now().isoformat(),
    'total_users_with_futures_trade': len(futures_users),
    'users_kept_enabled': len(status_9_uids),
    'users_disabled': updated_count,
    'failed_updates': failed_count,
    'status_9_uids': status_9_uids,
    'failed_users': failed_users
}

result_file = f"futures_trade_update_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(result_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"✓ Results saved to: {result_file}")
print()

# Summary
print("="*70)
print("SUMMARY")
print("="*70)
print(f"Total users scanned: {scanned_count}")
print(f"Users with futuresTrade = 1 (before): {len(futures_users)}")
print(f"Users kept with futuresTrade = 1: {len(status_9_uids)}")
print(f"Users updated to futuresTrade = 0: {updated_count}")
print(f"Failed updates: {failed_count}")
print()
print("✓ Operation completed successfully!")
print("="*70)
