"""
Pytest configuration and shared fixtures.

This module provides common fixtures and configuration for all tests,
including database setup, test clients, and mock objects.
"""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import fakeredis.aioredis
import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_cache_client, get_db_session, get_mongo_client
from app.main import app

# Auth module has been removed from the application

# Test database URLs
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_MONGO_URL = "mongodb://test_host"
TEST_REDIS_URL = "redis://test_host"


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


# Mock fixtures
@pytest.fixture
def mock_email_service(monkeypatch):
    """
    Mock email service for testing.

    Prevents actual emails from being sent during tests.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    sent_emails = []

    def mock_send_email(to: str, subject: str, body: str, **kwargs):
        """Mock email sending function."""
        sent_emails.append({"to": to, "subject": subject, "body": body, **kwargs})
        return {"status": "sent", "message_id": str(uuid4())}

    # Patch email sending function
    monkeypatch.setattr("app.core.tasks.send_email", mock_send_email)

    return sent_emails


# Utility functions for tests
def create_test_user_data(**overrides) -> dict:
    """
    Create test user data with optional overrides.

    Args:
        **overrides: Fields to override in the default user data

    Returns:
        Dictionary with user data for testing
    """
    default_data = {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "username": f"testuser_{uuid4().hex[:8]}",
        "password": "testpassword123",
        "full_name": "Test User",
    }

    default_data.update(overrides)
    return default_data


def assert_user_data_matches(user_dict: dict, expected_data: dict, exclude_fields=None):
    """
    Assert that user data matches expected values.

    Args:
        user_dict: User data dictionary to check
        expected_data: Expected user data
        exclude_fields: Fields to exclude from comparison
    """
    exclude_fields = exclude_fields or ["id", "created_at", "updated_at", "last_login"]

    for field, expected_value in expected_data.items():
        if field not in exclude_fields:
            assert user_dict[field] == expected_value, f"Field {field} mismatch"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "slow: Slow tests")


# Set test environment
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["MONGO_URL"] = TEST_MONGO_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL
