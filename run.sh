#!/bin/bash

# Check if virtual environment exists, if not use system python3
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Load .env file if it exists
if [ -f ".env" ]; then
    echo "📁 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ $# -eq 0 ]; then
    echo "🚀 DynamoDB to PostgreSQL Migration Tool"
    echo ""
    echo "Usage:"
    echo "  ./run.sh users              # Migrate users table"
    echo "  ./run.sh all               # Migrate all tables" 
    echo "  ./run.sh list              # List available migrations"
    echo "  ./run.sh users --dry-run   # Dry run users migration"
    echo ""
    echo "Available tables:"
    $PYTHON_CMD migrate.py --list
    exit 0
fi

if [ "$1" = "all" ]; then
    $PYTHON_CMD migrate.py --all "${@:2}"
elif [ "$1" = "list" ]; then
    $PYTHON_CMD migrate.py --list
else
    $PYTHON_CMD migrate.py --table "$1" "${@:2}"
fi
