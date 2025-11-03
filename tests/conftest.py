"""
Pytest configuration and shared fixtures.

This module provides common fixtures and configuration for all tests,
including database setup, test clients, and mock objects.

Following pytest best practices:
- Set environment variables BEFORE imports that depend on them
- Use standard pytest fixtures and patterns
- Isolate tests with proper setup/teardown
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

# CRITICAL: Set test environment variables BEFORE any app imports
# This must happen before Settings() is instantiated during import
os.environ["TESTING"] = "true"
os.environ["DEBUG"] = "true"  # Enable debug for tests
os.environ["ENVIRONMENT"] = "test"  # Set environment to test

# Test database URLs - use in-memory SQLite for tests (STANDARD pytest pattern)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_MONGO_URL = "mongodb://test_host"
TEST_REDIS_URL = "redis://test_host"

# Set database URLs before imports
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["MONGODB_URL"] = TEST_MONGO_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL

# Override production validation - use test password for tests
os.environ["POSTGRES_PASSWORD"] = "test_password_not_production"

# Imports must come after environment variables are set
# noqa: E402 is required because environment variables must be set before imports
import fakeredis.aioredis  # noqa: E402
import httpx  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from httpx import AsyncClient  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import (  # noqa: E402
    Base,
    get_cache_client,
    get_db_session,
    get_mongo_client,
)
from app.main import app  # noqa: E402

# Auth module has been removed from the application


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the test session.

    This fixture ensures all async tests run in the same event loop,
    which is important for database connection management.

    Yields:
        Event loop for the test session
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db_engine():
    """
    Create a test database engine.

    Uses SQLite in-memory database for fast, isolated testing.

    Returns:
        SQLAlchemy async engine for testing
    """
    # Create test engine with SQLite
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with transaction rollback.

    Each test gets a fresh session that is rolled back after the test
    to ensure test isolation.

    Args:
        test_db_engine: Test database engine

    Yields:
        Database session for testing
    """
    # Create session factory
    session_factory = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        # Begin transaction
        trans = await session.begin()

        yield session

        # Rollback transaction to maintain test isolation
        await trans.rollback()


@pytest.fixture
def test_mongodb():
    """
    Create a mock MongoDB client for testing.

    Uses mongomock for in-memory MongoDB simulation.

    Returns:
        Mock MongoDB database instance
    """
    client = AsyncMongoMockClient()
    database = client["test_fastapi_enterprise"]
    return database


@pytest.fixture
def test_redis():
    """
    Create a fake Redis client for testing.

    Uses fakeredis for in-memory Redis simulation.

    Returns:
        Fake Redis client instance
    """
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def override_dependencies(test_db_session, test_mongodb, test_redis):
    """
    Override FastAPI dependencies for testing.

    This fixture replaces the real database connections with test versions.

    Args:
        test_db_session: Test database session
        test_mongodb: Mock MongoDB database
        test_redis: Fake Redis client

    Returns:
        Context manager for dependency overrides
    """
    app.dependency_overrides[get_db_session] = lambda: test_db_session
    app.dependency_overrides[get_mongo_client] = lambda: test_mongodb
    app.dependency_overrides[get_cache_client] = lambda: test_redis

    yield

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(override_dependencies) -> TestClient:  # noqa: ARG001
    """
    Create a test client for the FastAPI application.

    This client can be used for synchronous API testing.

    Args:
        override_dependencies: Dependency overrides fixture

    Returns:
        FastAPI test client
    """
    return TestClient(app)


@pytest_asyncio.fixture
async def async_test_client(
    override_dependencies,  # noqa: ARG001
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for the FastAPI application.

    This client can be used for asynchronous API testing.

    Args:
        override_dependencies: Dependency overrides fixture

    Yields:
        Async HTTP client for testing
    """
    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# Auth module has been removed - user and authentication fixtures are no longer available
# Celery fixtures
@pytest.fixture
def celery_app():
    """
    Create a Celery app for testing.

    Configures Celery to execute tasks eagerly (synchronously)
    for easier testing.

    Returns:
        Celery app configured for testing
    """
    from app.core.celery_app import celery_app

    # Configure for testing
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url="memory://",
        result_backend="cache+memory://",
    )

    return celery_app


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "slow: Slow tests")
