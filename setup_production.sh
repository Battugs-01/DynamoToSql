#!/bin/bash

# =============================================================================
# Production PostgreSQL Migration Setup
# =============================================================================
# IMPORTANT: This script sets up environment for PRODUCTION database migration
# Use with EXTREME CAUTION!
# =============================================================================

echo "🚨 PRODUCTION DATABASE MIGRATION SETUP"
echo "======================================="
echo ""
echo "⚠️  WARNING: You are about to migrate to PRODUCTION database!"
echo ""

# Production PostgreSQL Configuration
export PG_HOST="localhost"  # TODO: Add your production PostgreSQL host
export PG_PORT="5432"
export PG_DATABASE="xmeta"
export PG_USER="postgres"
export PG_PASSWORD="Pass1234!"

# AWS DynamoDB Configuration
export AWS_DEFAULT_REGION="ap-southeast-1"
export AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_KEY"

# Migration Settings
export MIGRATION_BATCH_SIZE="100"
export LOG_LEVEL="INFO"
export DRY_RUN="false"

echo "✅ Production environment variables set!"
echo ""
echo "📊 Configuration:"
echo "   PostgreSQL Host: $PG_HOST"
echo "   PostgreSQL Database: $PG_DATABASE"
echo "   PostgreSQL User: $PG_USER"
echo "   AWS Region: $AWS_DEFAULT_REGION"
echo ""
echo "💡 Usage examples:"
echo "   source setup_production.sh               # Load production settings"
echo "   python3 migrate.py --table users --dry-run  # Test migration (no writes)"
echo "   python3 migrate.py --table users         # Run actual migration"
echo "   python3 migrate.py --all                 # Migrate all tables"
echo ""
echo "⚠️  RECOMMENDATION: Always run with --dry-run first!"
echo ""
