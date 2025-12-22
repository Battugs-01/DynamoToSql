import os
import boto3
from dotenv import load_dotenv

load_dotenv()

def inspect_orders():
    region = os.getenv('AWS_REGION', 'ap-southeast-1')
    dynamo = boto3.resource('dynamodb', region_name=region)
    table = dynamo.Table('spot-trade-orders')
    
    try:
        response = table.scan(Limit=1)
        items = response.get('Items', [])
        if items:
            print("Successfully scanned spot-trade-orders")
            print(f"Sample item: {items[0]}")
            print(f"Item keys: {items[0].keys()}")
        else:
            print("Table spot-trade-orders is empty in DynamoDB")
    except Exception as e:
        print(f"Error scanning spot-trade-orders: {e}")

if __name__ == "__main__":
    inspect_orders()
