"""
Alembic environment configuration.

This module configures Alembic for database migrations, including
async support and automatic model discovery.
"""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Set default environment variables for migrations if not already set
# This prevents validation errors when running migrations locally
# CRITICAL: Set these BEFORE importing Settings to avoid production validation errors
if "ENVIRONMENT" not in os.environ:
    os.environ["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "development")
if "DEPLOYMENT_ENVIRONMENT" not in os.environ:
    os.environ["DEPLOYMENT_ENVIRONMENT"] = os.getenv(
        "DEPLOYMENT_ENVIRONMENT", "development"
    )
if "DEBUG" not in os.environ:
    os.environ["DEBUG"] = os.getenv(
        "DEBUG", "true"
    )  # Default to debug mode for migrations
if "TESTING" not in os.environ:
    os.environ["TESTING"] = os.getenv("TESTING", "false")
# Only set POSTGRES_PASSWORD if not already set, and only if we're not in production
if "POSTGRES_PASSWORD" not in os.environ:
    env = os.getenv("ENVIRONMENT", "development")
    if env != "production":
        os.environ["POSTGRES_PASSWORD"] = "postgres"  # Safe default for non-production

# Import application components (must come after environment variables are set)
from app.core.config import get_settings  # noqa: E402

settings = get_settings()
from app.core.database import Base  # noqa

# Import all models to ensure they're registered with SQLAlchemy
# Auth models have been removed from the application

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Configure database URL from application settings
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # For SQLite compatibility
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with a database connection.

    Args:
        connection: Database connection to use for migrations
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # For SQLite compatibility
        # Include additional configuration for better migrations
        include_schemas=True,
        version_table_schema=target_metadata.schema,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in async mode.

    This is the main function called when running migrations
    in an async environment with PostgreSQL.
    """
    # Create async engine
    connectable = create_async_engine(
        str(settings.DATABASE_URL),
        poolclass=pool.NullPool,  # Don't use connection pooling for migrations
        echo=settings.DEBUG,  # Log SQL in debug mode
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate
    a connection with the context.
    """
    # Check if we're in an async context
    try:
        # Try to get the current event loop
        asyncio.get_running_loop()
        # If we're in an async context, use async migrations
        asyncio.create_task(run_async_migrations())
    except RuntimeError:
        # No event loop running, use sync approach
        asyncio.run(run_async_migrations())


# Determine if we're running offline or online
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
