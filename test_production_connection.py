#!/usr/bin/env python3
"""
Test Production PostgreSQL Connection
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        
        print("🔍 Testing Production PostgreSQL Connection...")
        print("=" * 60)
        
        # Get connection details
        host = os.getenv('PG_HOST')
        port = os.getenv('PG_PORT', '5432')
        database = os.getenv('PG_DATABASE')
        user = os.getenv('PG_USER')
        password = os.getenv('PG_PASSWORD')
        
        print(f"📊 Connection Details:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Database: {database}")
        print(f"   User: {user}")
        print(f"   Password: {'*' * len(password) if password else 'Not set'}")
        print()
        
        # Try to connect
        print("🔌 Connecting...")
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connection successful!")
        print(f"   PostgreSQL version: {version[0][:50]}...")
        print()
        
        # List tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"📋 Available tables ({len(tables)}):")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("✅ Production database is ready for migration!")
        print()
        print("🚀 Next steps:")
        print("   1. Test migration: ./run.sh users --dry-run")
        print("   2. Run migration: ./run.sh users")
        print("   3. Migrate all: ./run.sh all")
        
        return True
        
    except ImportError:
        print("❌ Error: psycopg2-binary is not installed")
        print("   Run: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print()
        print("🔍 Troubleshooting:")
        print("   - Check if PostgreSQL host is accessible")
        print("   - Verify credentials in .env file")
        print("   - Ensure firewall allows connection from your IP")
        print("   - Check if PostgreSQL is running")
        return False

def test_dynamodb_connection():
    """Test DynamoDB connection"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        print()
        print("🔍 Testing AWS DynamoDB Connection...")
        print("=" * 60)
        
        region = os.getenv('AWS_DEFAULT_REGION')
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        print(f"📊 AWS Details:")
        print(f"   Region: {region}")
        print(f"   Access Key: {access_key[:10]}..." if access_key else "   Access Key: Not set")
        print()
        
        # Create DynamoDB client
        dynamodb = boto3.client(
            'dynamodb',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # List tables
        print("🔌 Connecting...")
        response = dynamodb.list_tables(Limit=50)
        tables = response.get('TableNames', [])
        
        print(f"✅ Connection successful!")
        print(f"📋 Available DynamoDB tables ({len(tables)}):")
        for table in sorted(tables):
            print(f"   - {table}")
        
        print()
        print("=" * 60)
        print("✅ DynamoDB is accessible!")
        
        return True
        
    except ImportError:
        print("❌ Error: boto3 is not installed")
        print("   Run: pip install -r requirements.txt")
        return False
        
    except ClientError as e:
        print(f"❌ AWS connection failed: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print()
    print("🧪 PRODUCTION CONNECTION TEST")
    print("=" * 60)
    print()
    
    pg_ok = test_postgres_connection()
    dynamo_ok = test_dynamodb_connection()
    
    print()
    print("=" * 60)
    if pg_ok and dynamo_ok:
        print("✅ ALL CONNECTIONS SUCCESSFUL - READY TO MIGRATE!")
    else:
        print("❌ SOME CONNECTIONS FAILED - FIX ISSUES BEFORE MIGRATING")
    print("=" * 60)
    print()
    
    sys.exit(0 if (pg_ok and dynamo_ok) else 1)
