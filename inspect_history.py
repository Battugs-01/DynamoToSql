import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config.database import DynamoConfig
from utils.database import DynamoConnection

def inspect_item():
    dynamo_cfg = DynamoConfig.from_env()
    dynamo_conn = DynamoConnection(dynamo_cfg)
    
    table_name = 'spot-trade-history'
    try:
        table = dynamo_conn.get_table(table_name)
        response = table.scan(Limit=10)
        items = response.get('Items', [])
        
        if items:
            import json
            from decimal import Decimal
            
            def default(obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                return str(obj)
                
            print(f"Scanned {len(items)} items from {table_name}.")
            
            all_keys = set()
            for item in items:
                all_keys.update(item.keys())
            
            print(f"All keys found in sample: {all_keys}")
            
            if 'uid' in all_keys:
                print("FOUND 'uid' in sample!")
            else:
                print("'uid' NOT FOUND in sample.")
            
            # Print first item as example
            print(json.dumps(items[0], indent=2, default=default))
        else:
            print(f"No items found in {table_name}")
            
    except Exception as e:
        print(f"Error accessing {table_name}: {e}")

if __name__ == "__main__":
    inspect_item()
