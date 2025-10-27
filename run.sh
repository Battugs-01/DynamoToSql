#!/bin/bash
source venv/bin/activate


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
    python migrate.py --list
    exit 0
fi

if [ "$1" = "all" ]; then
    python migrate.py --all "${@:2}"
elif [ "$1" = "list" ]; then
    python migrate.py --list
else
    python migrate.py --table "$1" "${@:2}"
fi
