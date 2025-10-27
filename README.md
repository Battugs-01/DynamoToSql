# DynamoDB to PostgreSQL Migration Tool

Зохион байгуулалттай migration tool олон DynamoDB table-ыг PostgreSQL руу шилжүүлэхэд зориулсан.

## 📁 Project Structure

```
DynamoToSql/
├── config/                 # Configuration files
│   ├── __init__.py
│   └── database.py        # Database configurations
├── utils/                 # Shared utilities
│   ├── __init__.py
│   ├── database.py        # Connection managers
│   └── migration_base.py  # Base migration class
├── migrations/            # Individual table migrations
│   ├── __init__.py
│   └── users_migration.py # Users table migration
├── templates/             # Migration templates
│   └── migration_template.py
├── logs/                  # Migration logs
├── main.py               # Old single-table script (deprecated)
├── migrate.py            # New CLI interface
├── run.sh               # Quick run script
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Migrations

**Single table migration:**

```bash
python migrate.py --table users
```

**All tables migration:**

```bash
python migrate.py --all
```

**List available migrations:**

```bash
python migrate.py --list
```

**Dry run (no actual writes):**

```bash
python migrate.py --dry-run --table users
```

### 3. Configuration

Environment variables:

```bash
# AWS
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# PostgreSQL
export PG_HOST=localhost
export PG_PORT=5433
export PG_DATABASE=x-meta
export PG_USER=postgres
export PG_PASSWORD=Pass1234!
```

## ➕ Adding New Table Migration

### 1. Copy Template

```bash
cp templates/migration_template.py migrations/your_table_migration.py
```

### 2. Customize Migration

```python
# migrations/your_table_migration.py
class YourTableMigration(BaseMigration):
    @property
    def dynamo_table_name(self) -> str:
        return "your-dynamodb-table"

    @property
    def postgres_table_name(self) -> str:
        return "your_postgres_table"

    def transform_item(self, item):
        return {
            'id': item.get("id"),
            'name': item.get("name"),
            'created_at': self.convert_epoch_to_iso(item.get("createdAt")),
            # Add more fields...
        }

    def get_insert_query(self) -> str:
        return """
            INSERT INTO your_table (id, name, created_at)
            VALUES (%(id)s, %(name)s, %(created_at)s)
            ON CONFLICT (id) DO NOTHING
        """
```

### 3. Register Migration

```python
# migrate.py - Add to AVAILABLE_MIGRATIONS
AVAILABLE_MIGRATIONS = {
    'users': 'migrations.users_migration.UsersMigration',
    'your_table': 'migrations.your_table_migration.YourTableMigration',  # Add this line
}
```

## 🔧 Utility Functions

Base migration class includes helpful converters:

- `convert_epoch_to_iso()` - Epoch → ISO8601 (`2022-09-27T18:00:00.000Z`)
- `convert_to_boolean()` - Integer (0/1) → Boolean (True/False)
- `convert_to_json()` - Dict → PostgreSQL JSON

## 📊 Migration Features

- ✅ **Batch Processing**: Configurable batch sizes
- ✅ **Error Handling**: Continues on individual item errors
- ✅ **Dry Run Mode**: Test without writing
- ✅ **Progress Logging**: Real-time progress updates
- ✅ **Conflict Resolution**: `ON CONFLICT DO NOTHING` для дубликатов
- ✅ **Type Conversion**: Automatic data type handling
- ✅ **Modular Design**: Easy to add new tables

## 🔍 Troubleshooting

### Common Issues:

1. **Module import errors**: Make sure `__init__.py` files exist
2. **Database connection**: Check your environment variables
3. **Column mismatch**: Verify PostgreSQL table structure matches migration
4. **Type errors**: Check data type conversions in `transform_item()`

### Logs:

```bash
tail -f logs/migration.log
```

## 🎯 Examples

**Migrate users table with debug logging:**

```bash
python migrate.py --table users --log-level DEBUG
```

**Dry run all tables:**

```bash
python migrate.py --all --dry-run
```

**Custom batch size:**

```bash
python migrate.py --table users --batch-size 50
```
# DynamoToSql
