"""
Database Management - Multi-database connection manager

This module provides async database connections and session management for:
- PostgreSQL: Primary relational data store (SQLAlchemy + asyncpg)
- MongoDB: Document store for flexible schemas (Motor + Beanie ODM)
- Redis: Caching and session store (redis-py async)

Architecture:
- Follows hexagonal/clean architecture patterns
- Global connection pools for performance
- Dependency injection for FastAPI routes
- Proper async context management and cleanup

Usage:
    # In FastAPI routes
    @app.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db_session)):
        result = await db.execute(select(User))
        return result.scalars().all()

    # Direct access
    from app.core.database import get_postgres_session
    async with get_postgres_session() as session:
        # Use session...
"""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import structlog
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    pass

from app.core.config import get_settings

# Initialize structured logger for database operations
logger = structlog.get_logger(__name__)

# Global database connection pools - initialized at startup, shared across requests
# These are module-level singletons for performance and resource management
_postgres_engine: AsyncEngine | None = (
    None  # SQLAlchemy async engine with connection pooling
)
_postgres_session_maker: async_sessionmaker[AsyncSession] | None = (
    None  # Session factory for database operations
)
_mongodb_client: AsyncIOMotorClient[Any] | None = (
    None  # Motor async client for MongoDB operations
)
_redis_client: Redis | None = None  # Redis async client for caching and sessions


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    This provides common functionality and ensures consistent table naming,
    primary key handling, and other ORM behaviors across all models.

    Example:
        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(255))
    """

    pass


class DatabaseManager:
    """
    Central database connection manager for all database types.

    Handles initialization, configuration, and lifecycle management for:
    - PostgreSQL connections with connection pooling
    - MongoDB connections with automatic reconnection
    - Redis connections for caching and sessions

    This class follows the singleton pattern and is initialized once
    during application startup via the FastAPI lifespan handler.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    async def init_postgres(self) -> None:
        """Initialize PostgreSQL connection pool."""
        global _postgres_engine, _postgres_session_maker

        try:
            # Create async engine with connection pooling
            _postgres_engine = create_async_engine(
                str(self.settings.DATABASE_URL),
                echo=self.settings.DEBUG,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections after 1 hour
            )

            # Create session maker
            _postgres_session_maker = async_sessionmaker(
                _postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info("PostgreSQL connection initialized")

        except Exception as e:
            logger.error("Failed to initialize PostgreSQL", error=str(e))
            raise

    async def init_mongodb(self) -> None:
        """Initialize MongoDB connection."""
        global _mongodb_client

        try:
            # Create MongoDB client
            _mongodb_client = AsyncIOMotorClient(self.settings.MONGODB_URL)
            if _mongodb_client is None:
                raise RuntimeError("Failed to create MongoDB client")

            # Test connection
            await _mongodb_client.admin.command("ping")

            # Initialize Beanie with document models
            # Note: Document models will be added here as they're created
            await init_beanie(
                database=_mongodb_client[self.settings.MONGODB_DATABASE],  # type: ignore[arg-type]
                document_models=[],  # Add models here as they're created
            )

            logger.info("MongoDB connection initialized")

        except Exception as e:
            logger.error("Failed to initialize MongoDB", error=str(e))
            raise

    async def init_redis(self) -> None:
        """Initialize Redis connection."""
        global _redis_client

        try:
            # Create Redis client
            redis_url = self.settings.REDIS_URL
            if redis_url is None:
                raise ValueError("REDIS_URL is not configured")
            _redis_client = Redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

            # Test connection
            await _redis_client.ping()

            logger.info("Redis connection initialized")

        except Exception as e:
            logger.error("Failed to initialize Redis", error=str(e))
            raise

    async def close_postgres(self) -> None:
        """Close PostgreSQL connections."""
        global _postgres_engine, _postgres_session_maker

        if _postgres_engine:
            await _postgres_engine.dispose()
            _postgres_engine = None
            _postgres_session_maker = None
            logger.info("PostgreSQL connections closed")

    async def close_mongodb(self) -> None:
        """Close MongoDB connections."""
        global _mongodb_client

        if _mongodb_client:
            _mongodb_client.close()
            _mongodb_client = None
            logger.info("MongoDB connections closed")

    async def close_redis(self) -> None:
        """Close Redis connections."""
        global _redis_client

        if _redis_client:
            await _redis_client.aclose()
            _redis_client = None
            logger.info("Redis connections closed")


# Global database manager instance
_db_manager = DatabaseManager()


async def init_databases() -> None:
    """
    Initialize all database connections.

    This function should be called during application startup.
    """
    try:
        await _db_manager.init_postgres()
        await _db_manager.init_mongodb()
        await _db_manager.init_redis()
        logger.info("All database connections initialized")
    except Exception as e:
        logger.error("Failed to initialize databases", error=str(e))
        raise


async def close_databases() -> None:
    """
    Close all database connections.

    This function should be called during application shutdown.
    """
    try:
        await _db_manager.close_postgres()
        await _db_manager.close_mongodb()
        await _db_manager.close_redis()
        logger.info("All database connections closed")
    except Exception as e:
        logger.error("Failed to close databases", error=str(e))


async def get_postgres_session() -> AsyncSession:
    """
    Get PostgreSQL database session.

    Returns:
        AsyncSession: Database session for PostgreSQL operations

    Raises:
        RuntimeError: If database connection is not initialized
    """
    if not _postgres_session_maker:
        raise RuntimeError("PostgreSQL connection not initialized")

    return _postgres_session_maker()


def get_mongodb_client() -> AsyncIOMotorClient[Any]:
    """
    Get MongoDB client.

    Returns:
        AsyncIOMotorClient: MongoDB client instance

    Raises:
        RuntimeError: If database connection is not initialized
    """
    if not _mongodb_client:
        raise RuntimeError("MongoDB connection not initialized")

    return _mongodb_client


def get_redis_client() -> Redis:
    """
    Get Redis client.

    Returns:
        Redis: Redis client instance

    Raises:
        RuntimeError: If database connection is not initialized
    """
    if not _redis_client:
        raise RuntimeError("Redis connection not initialized")

    return _redis_client


async def check_database_health() -> dict[str, bool]:
    """
    Check health of all database connections.

    Returns:
        dict[str, bool]: Health status of each database
    """
    health_status = {
        "postgres": False,
        "mongodb": False,
        "redis": False,
    }

    # Check PostgreSQL
    try:
        if _postgres_engine:
            from sqlalchemy import text

            async with _postgres_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["postgres"] = True
    except Exception as e:
        logger.warning("PostgreSQL health check failed", error=str(e))

    # Check MongoDB
    try:
        if _mongodb_client:
            await _mongodb_client.admin.command("ping")
            health_status["mongodb"] = True
    except Exception as e:
        logger.warning("MongoDB health check failed", error=str(e))

    # Check Redis
    try:
        if _redis_client:
            await _redis_client.ping()
            health_status["redis"] = True
    except Exception as e:
        logger.warning("Redis health check failed", error=str(e))

    return health_status


# FastAPI dependency functions
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for PostgreSQL database sessions.

    Yields:
        AsyncSession: Database session that will be automatically closed
    """
    session = await get_postgres_session()
    try:
        yield session
    finally:
        await session.close()


def get_mongo_client() -> AsyncIOMotorClient[Any]:
    """
    FastAPI dependency for MongoDB client.

    Returns:
        AsyncIOMotorClient: MongoDB client instance
    """
    return get_mongodb_client()


def get_cache_client() -> Redis:
    """
    FastAPI dependency for Redis client.

    Returns:
        Redis: Redis client instance
    """
    return get_redis_client()
