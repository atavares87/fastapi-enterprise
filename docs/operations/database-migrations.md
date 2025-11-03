# Database Migrations with Alembic

## Overview

This guide covers database schema management using Alembic, SQLAlchemy's migration tool. Alembic provides version control for your database schema, allowing you to track changes, upgrade/downgrade schemas, and maintain consistency across environments.

## Alembic Configuration

### Setup and Configuration

Alembic is configured in the `migrations/` directory:

```
migrations/
├── alembic.ini          # Alembic configuration file
├── env.py               # Migration environment setup
├── script.py.mako       # Migration script template
└── versions/            # Migration version files
    ├── 001_initial_schema.py
    ├── 002_add_pricing_tables.py
    └── 003_add_cost_tables.py
```

**Alembic Configuration** (`alembic.ini`):

```ini
[alembic]
# Path to migration scripts
script_location = migrations

# Template for new migration files
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# Database URL (can be overridden by environment)
sqlalchemy.url = postgresql+asyncpg://postgres:password@localhost:5432/fastapi_enterprise

# Timezone for migration timestamps
timezone = UTC

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Environment Configuration** (`migrations/env.py`):

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Import your SQLAlchemy models
from app.adapter.outbound.persistence.models import Base
from app.core.config import settings

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def get_database_url() -> str:
    """Get database URL from settings or config"""
    return settings.postgres_url or config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """Run migrations with database connection"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """Run migrations in async mode"""
    connectable = create_async_engine(
        get_database_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Common Migration Commands

### Basic Commands

```bash
# Check current migration status
make db-current
# or manually
uv run alembic current

# Show migration history
make db-history
# or manually
uv run alembic history

# Show pending migrations
make db-show-pending
# or manually
uv run alembic show

# Upgrade to latest migration
make db-upgrade
# or manually
uv run alembic upgrade head

# Downgrade by one revision
make db-downgrade
# or manually
uv run alembic downgrade -1

# Upgrade to specific revision
uv run alembic upgrade <revision_id>

# Downgrade to specific revision
uv run alembic downgrade <revision_id>
```

### Creating Migrations

```bash
# Generate migration automatically from model changes
make db-revision MESSAGE="Add user authentication tables"
# or manually
uv run alembic revision --autogenerate -m "Add user authentication tables"

# Create empty migration (for data migrations, etc.)
make db-revision-empty MESSAGE="Migrate user data"
# or manually
uv run alembic revision -m "Migrate user data"

# Review the generated migration before applying
cat migrations/versions/20241201_1430_add_user_authentication_tables.py
```

### Migration Information

```bash
# Show current migration
uv run alembic current

# Show migration history with details
uv run alembic history --verbose

# Show specific migration
uv run alembic show <revision_id>

# Generate SQL without executing (for review)
uv run alembic upgrade --sql head > upgrade.sql
uv run alembic downgrade --sql -1 > downgrade.sql
```

## Migration Best Practices

### 1. Review Generated Migrations

Always review auto-generated migrations before applying:

```python
# Example generated migration
"""Add user authentication tables

Revision ID: abc123def456
Revises: 789ghi012jkl
Create Date: 2024-01-15 14:30:00.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'abc123def456'
down_revision = '789ghi012jkl'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
```

### 2. Safe Migration Practices

**Schema Changes**:
```python
def upgrade() -> None:
    # Safe: Add new columns with defaults
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

    # Safe: Add indexes
    op.create_index('ix_users_phone', 'users', ['phone'])

    # Potentially unsafe: Dropping columns (consider renaming first)
    # op.drop_column('users', 'old_column')  # Be careful!

def downgrade() -> None:
    op.drop_index('ix_users_phone')
    op.drop_column('users', 'phone')
```

**Data Migrations**:
```python
from sqlalchemy import text

def upgrade() -> None:
    # Schema change first
    op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))

    # Then data migration
    connection = op.get_bind()
    connection.execute(
        text("""
            UPDATE users
            SET full_name = CONCAT(first_name, ' ', last_name)
            WHERE first_name IS NOT NULL AND last_name IS NOT NULL
        """)
    )

    # Finally, make column non-nullable if needed
    op.alter_column('users', 'full_name', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

### 3. Large Table Migrations

For large tables, use careful strategies:

```python
def upgrade() -> None:
    # For large tables, add column as nullable first
    op.add_column('large_table', sa.Column('new_status', sa.String(20), nullable=True))

    # Update in batches (implement in separate script for very large tables)
    connection = op.get_bind()

    # Small batch update
    batch_size = 1000
    offset = 0

    while True:
        result = connection.execute(
            text(f"""
                UPDATE large_table
                SET new_status = 'active'
                WHERE new_status IS NULL
                AND id IN (
                    SELECT id FROM large_table
                    WHERE new_status IS NULL
                    ORDER BY id
                    LIMIT {batch_size}
                )
            """)
        )

        if result.rowcount == 0:
            break

    # Make column non-nullable after all data is migrated
    op.alter_column('large_table', 'new_status', nullable=False)
```

## Advanced Migration Scenarios

### 1. Complex Schema Changes

**Renaming Tables**:
```python
def upgrade() -> None:
    op.rename_table('old_table_name', 'new_table_name')

    # Update any foreign key references
    op.drop_constraint('fk_other_table_old_ref', 'other_table', type_='foreignkey')
    op.create_foreign_key(
        'fk_other_table_new_ref',
        'other_table',
        'new_table_name',
        ['ref_column'],
        ['id']
    )
```

**Splitting Tables**:
```python
def upgrade() -> None:
    # Create new table
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bio', sa.Text()),
        sa.Column('avatar_url', sa.String(500)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )

    # Migrate data
    connection = op.get_bind()
    connection.execute(text("""
        INSERT INTO user_profiles (id, user_id, bio, avatar_url)
        SELECT gen_random_uuid(), id, bio, avatar_url
        FROM users
        WHERE bio IS NOT NULL OR avatar_url IS NOT NULL
    """))

    # Remove columns from original table
    op.drop_column('users', 'bio')
    op.drop_column('users', 'avatar_url')
```

### 2. Data Transformation Migrations

**Normalizing Data**:
```python
def upgrade() -> None:
    # Create lookup table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False)
    )

    # Populate categories from existing data
    connection = op.get_bind()

    # Get unique categories
    result = connection.execute(text("SELECT DISTINCT category FROM products WHERE category IS NOT NULL"))
    categories = [row[0] for row in result]

    # Insert categories
    for category in categories:
        connection.execute(
            text("INSERT INTO categories (name) VALUES (:name)"),
            {"name": category}
        )

    # Add foreign key column
    op.add_column('products', sa.Column('category_id', sa.Integer))

    # Update references
    connection.execute(text("""
        UPDATE products
        SET category_id = categories.id
        FROM categories
        WHERE products.category = categories.name
    """))

    # Create foreign key constraint
    op.create_foreign_key('fk_products_category', 'products', 'categories', ['category_id'], ['id'])

    # Drop old column
    op.drop_column('products', 'category')

    # Make category_id non-nullable
    op.alter_column('products', 'category_id', nullable=False)
```

### 3. Performance-Optimized Migrations

**Adding Indexes Concurrently** (PostgreSQL):
```python
def upgrade() -> None:
    # Create index concurrently to avoid locking
    op.create_index(
        'ix_orders_customer_id_status',
        'orders',
        ['customer_id', 'status'],
        postgresql_concurrently=True
    )

def downgrade() -> None:
    op.drop_index('ix_orders_customer_id_status')
```

## Testing Migrations

### 1. Migration Testing Strategy

```python
# tests/test_migrations.py
import pytest
from alembic.command import upgrade, downgrade
from alembic.config import Config
from sqlalchemy import create_engine, text

class TestMigrations:
    def test_migration_up_and_down(self, alembic_config: Config, database_url: str):
        """Test that migrations can be applied and rolled back"""
        engine = create_engine(database_url)

        # Start from clean state
        downgrade(alembic_config, "base")

        # Apply all migrations
        upgrade(alembic_config, "head")

        # Verify final state
        with engine.connect() as conn:
            # Check that expected tables exist
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]

            assert 'users' in tables
            assert 'pricing_calculations' in tables
            assert 'cost_components' in tables

        # Test rollback
        downgrade(alembic_config, "base")

        # Verify clean state
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]

            # Only alembic version table should remain
            assert len(tables) <= 1

    def test_specific_migration(self, alembic_config: Config, database_url: str):
        """Test a specific migration"""
        engine = create_engine(database_url)

        # Go to revision before the one we want to test
        downgrade(alembic_config, "abc123def456")  # Previous revision

        # Apply the migration we want to test
        upgrade(alembic_config, "def456ghi789")  # Target revision

        # Verify the migration worked
        with engine.connect() as conn:
            # Test that the new table/column exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'new_column'
            """))
            assert result.fetchone() is not None
```

### 2. Data Migration Testing

```python
def test_data_migration(self, alembic_config: Config, database_url: str):
    """Test data migration correctness"""
    engine = create_engine(database_url)

    # Set up initial state
    downgrade(alembic_config, "before_data_migration")

    # Insert test data
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO old_table (old_column1, old_column2)
            VALUES ('value1', 'value2'), ('value3', 'value4')
        """))
        conn.commit()

    # Apply data migration
    upgrade(alembic_config, "after_data_migration")

    # Verify data was migrated correctly
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM new_table"))
        rows = result.fetchall()

        assert len(rows) == 2
        assert rows[0].new_column == 'expected_value1'
        assert rows[1].new_column == 'expected_value2'
```

## Production Migration Strategies

### 1. Zero-Downtime Migrations

**Multi-Phase Approach**:

**Phase 1**: Add new column (backward compatible)
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('new_status', sa.String(20), nullable=True))
```

**Phase 2**: Deploy application code that writes to both columns

**Phase 3**: Backfill data
```python
def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE users
        SET new_status = CASE
            WHEN old_status = 'A' THEN 'active'
            WHEN old_status = 'I' THEN 'inactive'
            ELSE 'unknown'
        END
        WHERE new_status IS NULL
    """))
```

**Phase 4**: Make new column non-nullable
```python
def upgrade() -> None:
    op.alter_column('users', 'new_status', nullable=False)
```

**Phase 5**: Deploy code that only uses new column

**Phase 6**: Remove old column
```python
def upgrade() -> None:
    op.drop_column('users', 'old_status')
```

### 2. Blue-Green Deployment Migrations

```bash
# Create migration SQL for review
uv run alembic upgrade --sql head > migration.sql

# Review SQL before applying
cat migration.sql

# Apply to blue environment
psql $BLUE_DATABASE_URL -f migration.sql

# Test blue environment
curl -f $BLUE_API_URL/health

# Switch traffic to blue
# Apply to green environment when ready
```

### 3. Monitoring Migration Performance

```python
import time
from alembic import op
from sqlalchemy import text

def upgrade() -> None:
    start_time = time.time()

    print("Starting large table migration...")

    # Perform migration
    op.add_column('large_table', sa.Column('new_column', sa.String(50)))

    # Monitor progress for large updates
    connection = op.get_bind()
    result = connection.execute(text("SELECT COUNT(*) FROM large_table"))
    total_rows = result.scalar()

    print(f"Updating {total_rows} rows...")

    # Batch update with progress
    batch_size = 10000
    updated = 0

    while updated < total_rows:
        result = connection.execute(text(f"""
            UPDATE large_table
            SET new_column = 'default_value'
            WHERE new_column IS NULL
            AND id IN (
                SELECT id FROM large_table
                WHERE new_column IS NULL
                ORDER BY id
                LIMIT {batch_size}
            )
        """))

        updated += result.rowcount
        progress = (updated / total_rows) * 100
        print(f"Progress: {progress:.1f}% ({updated}/{total_rows})")

    elapsed = time.time() - start_time
    print(f"Migration completed in {elapsed:.2f} seconds")
```

## Troubleshooting Common Issues

### 1. Migration Conflicts

**Merge Conflicts**:
```bash
# When multiple developers create migrations
# Alembic will detect branch conflicts

# List current heads
uv run alembic heads

# Merge branches
uv run alembic merge -m "Merge migration branches" <rev1> <rev2>
```

**Manual Conflict Resolution**:
```python
# Edit the merge migration to resolve conflicts
def upgrade() -> None:
    # Apply changes from both branches carefully
    # Ensure no duplicate operations
    pass
```

### 2. Failed Migrations

**Recovery Steps**:
```bash
# Check current state
uv run alembic current

# Mark migration as completed (if manually fixed)
uv run alembic stamp <revision_id>

# Rollback and retry
uv run alembic downgrade -1
uv run alembic upgrade +1
```

### 3. Database Locks

**PostgreSQL Lock Issues**:
```sql
-- Check for locks
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Kill blocking queries if necessary
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <blocking_pid>;
```

**Migration with Locks**:
```python
def upgrade() -> None:
    # Set lock timeout for long operations
    op.execute("SET lock_timeout = '5min'")

    # Use concurrent operations when possible
    op.create_index(
        'ix_large_table_column',
        'large_table',
        ['column'],
        postgresql_concurrently=True
    )
```

This comprehensive guide provides everything needed to effectively manage database migrations in a production FastAPI application using Alembic.
