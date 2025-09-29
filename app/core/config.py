"""
Application Configuration

This module handles all application configuration using Pydantic Settings.
It provides type-safe configuration management with environment variable support
and automatic validation.
"""

import secrets
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden using environment variables.
    For nested settings, use double underscores (e.g., DATABASE__HOST).

    Example:
        # Set via environment variables
        export APP_NAME="My Custom App"
        export DEBUG=true
        export POSTGRES_PORT=5432

        # Or use .env file
        DEBUG=true
        DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
    """

    model_config = SettingsConfigDict(extra="ignore")

    # Application Settings - Core app metadata and behavior
    APP_NAME: str = "FastAPI Enterprise"  # Used in API docs and logging
    APP_VERSION: str = "0.1.0"  # Semantic version for API versioning
    DEBUG: bool = False  # Enables debug logging and error details in responses
    TESTING: bool = False  # Automatically set during test runs

    # Server Settings - HTTP server configuration
    HOST: str = "0.0.0.0"  # nosec B104 - Bind to all interfaces (container-friendly)
    PORT: int = 8000  # HTTP server port
    RELOAD: bool = True  # Auto-reload on code changes (development only)

    # Security Settings - JWT tokens and authentication
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32)
    )  # Auto-generated if not set
    ALGORITHM: str = "HS256"  # JWT signing algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Short-lived tokens for API access
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # Long-lived tokens (7 days) for renewal

    # Database Settings - PostgreSQL (primary data store)
    POSTGRES_SERVER: str = "localhost"  # PostgreSQL hostname
    POSTGRES_USER: str = "postgres"  # Database username
    POSTGRES_PASSWORD: str = (
        "postgres"  # Database password (use env var in production!)
    )
    POSTGRES_DB: str = "fastapi_enterprise"  # Database name
    POSTGRES_PORT: int = 5432  # Port 5432 for local install, 5433 for Docker Compose
    DATABASE_URL: str | None = (
        None  # Complete URL (overrides individual settings if provided)
    )

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: Any) -> str:
        """
        Auto-construct PostgreSQL URL from individual components if not provided.

        This allows flexible configuration: either set DATABASE_URL directly or
        set individual POSTGRES_* variables. The URL takes precedence if both are set.

        Args:
            v: Complete database URL if provided (e.g., "postgresql+asyncpg://user:pass@host:port/db")
            info: Pydantic field validation context with other field values

        Returns:
            Complete PostgreSQL connection string with asyncpg driver

        Example:
            # Using individual components
            POSTGRES_SERVER=localhost
            POSTGRES_PORT=5432
            -> postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_enterprise

            # Using complete URL (overrides components)
            DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/myapp
        """
        if isinstance(v, str) and v:
            return v

        # Build URL from individual components
        values = info.data
        host = values.get("POSTGRES_SERVER", "localhost")
        port = values.get("POSTGRES_PORT", 5432)
        user = values.get("POSTGRES_USER", "postgres")
        password = values.get("POSTGRES_PASSWORD", "postgres")
        db = values.get("POSTGRES_DB", "fastapi_enterprise")

        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    # Database Settings - MongoDB (document store for flexible data)
    MONGO_SERVER: str = "localhost"  # MongoDB hostname
    MONGO_PORT: int = 27017  # Port 27017 for Docker Compose, 27017 for local install
    MONGO_DB: str = "fastapi_enterprise"  # Database name (legacy, use MONGODB_DATABASE)
    MONGO_USER: str | None = None  # MongoDB username (optional for local dev)
    MONGO_PASSWORD: str | None = None  # MongoDB password (optional for local dev)
    MONGODB_URL: str | None = (
        None  # Complete MongoDB URL (overrides individual settings)
    )
    MONGODB_DATABASE: str = "fastapi_enterprise"  # Database name for Beanie ODM

    @field_validator("MONGODB_URL", mode="after")
    @classmethod
    def assemble_mongodb_connection(cls, v: str | None, info: Any) -> str:
        """
        Construct MongoDB URL from individual components if not provided.

        Args:
            v: MongoDB URL if provided
            info: Field validation info containing other field values

        Returns:
            Complete MongoDB connection string
        """
        if isinstance(v, str) and v:
            return v

        # Get values from the current instance
        values = info.data
        host = values.get("MONGO_SERVER", "localhost")
        port = values.get("MONGO_PORT", 27017)
        user = values.get("MONGO_USER")
        password = values.get("MONGO_PASSWORD")

        # Build URL with authentication if provided
        if user and password:
            return f"mongodb://{user}:{password}@{host}:{port}"
        return f"mongodb://{host}:{port}"

    # Database Settings - Redis (caching and session store)
    REDIS_HOST: str = "localhost"  # Redis hostname
    REDIS_PORT: int = 6379  # Port 6379 for Docker Compose, 6379 for local install
    REDIS_DB: int = 0  # Redis database number (0-15)
    REDIS_PASSWORD: str | None = None  # Redis password (optional for local dev)
    REDIS_URL: str | None = None  # Complete Redis URL (overrides individual settings)

    @field_validator("REDIS_URL", mode="after")
    @classmethod
    def assemble_redis_connection(cls, v: str | None, info: Any) -> str:
        """
        Construct Redis URL from individual components if not provided.

        Args:
            v: Redis URL if provided
            info: Field validation info containing other field values

        Returns:
            Complete Redis connection string
        """
        if isinstance(v, str) and v:
            return v

        # Get values from the current instance
        values = info.data
        host = values.get("REDIS_HOST", "localhost")
        port = values.get("REDIS_PORT", 6379)
        db = values.get("REDIS_DB", 0)
        password = values.get("REDIS_PASSWORD")

        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    # Background Tasks - Celery configuration for async processing
    CELERY_BROKER_URL: str | None = (
        None  # Message broker URL (uses Redis URL if not set)
    )
    CELERY_RESULT_BACKEND: str | None = (
        None  # Result backend URL (uses Redis URL if not set)
    )

    @field_validator("CELERY_BROKER_URL", mode="after")
    @classmethod
    def set_celery_broker_url(cls, v: str | None, info: Any) -> str:
        """Set Celery broker URL to Redis URL if not provided."""
        if v:
            return v
        redis_url = info.data.get("REDIS_URL")
        if redis_url:
            return str(redis_url)
        # Build from Redis components
        host = info.data.get("REDIS_HOST", "localhost")
        port = info.data.get("REDIS_PORT", 6379)
        db = info.data.get("REDIS_DB", 0)
        password = info.data.get("REDIS_PASSWORD")
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    @field_validator("CELERY_RESULT_BACKEND", mode="after")
    @classmethod
    def set_celery_result_backend(cls, v: str | None, info: Any) -> str:
        """Set Celery result backend to Redis URL if not provided."""
        if v:
            return v
        redis_url = info.data.get("REDIS_URL")
        if redis_url:
            return str(redis_url)
        # Build from Redis components
        host = info.data.get("REDIS_HOST", "localhost")
        port = info.data.get("REDIS_PORT", 6379)
        db = info.data.get("REDIS_DB", 0)
        password = info.data.get("REDIS_PASSWORD")
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    # Logging Settings - Structured logging configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # "json" for production, "console" for development

    # CORS Settings - Cross-Origin Resource Sharing for web browsers
    ALLOWED_HOSTS: list[str] = [
        "*"
    ]  # Allowed origins (use specific domains in production!)
    ALLOW_CREDENTIALS: bool = True  # Allow cookies/auth headers in CORS requests
    ALLOWED_METHODS: list[str] = ["*"]  # Allowed HTTP methods (GET, POST, etc.)
    ALLOWED_HEADERS: list[str] = ["*"]  # Allowed request headers

    # Rate Limiting - API rate limiting to prevent abuse
    RATE_LIMIT_ENABLED: bool = True  # Enable/disable rate limiting
    RATE_LIMIT_CALLS: int = 100  # Max requests per period
    RATE_LIMIT_PERIOD: int = 60  # Time period in seconds

    # Email Settings - SMTP configuration for notifications (optional)
    SMTP_HOST: str | None = None  # SMTP server hostname (e.g., smtp.gmail.com)
    SMTP_PORT: int = 587  # SMTP port (587 for TLS, 465 for SSL, 25 for plain)
    SMTP_USER: str | None = None  # SMTP username
    SMTP_PASSWORD: str | None = (
        None  # SMTP password (use app-specific password for Gmail)
    )
    EMAIL_FROM: str | None = None  # Default sender email address

    # External API Settings - Timeouts and retries for HTTP clients
    EXTERNAL_API_TIMEOUT: int = 30  # Request timeout in seconds
    EXTERNAL_API_RETRIES: int = 3  # Number of retry attempts

    # Environment detection properties
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.DEBUG

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG and not self.TESTING

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.TESTING

    # Alias property for backward compatibility with tests
    @property
    def MONGO_URL(self) -> str:
        """Get MongoDB URL (alias for MONGODB_URL)."""
        return self.MONGODB_URL or ""


# Global settings instance - singleton pattern for configuration
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get application settings singleton instance.

    This function implements the singleton pattern to ensure configuration
    is loaded once and reused throughout the application lifecycle.

    Returns:
        Settings: Application configuration instance with all environment
                 variables loaded and validated

    Example:
        from app.core.config import get_settings

        settings = get_settings()
        print(f"Running {settings.APP_NAME} on port {settings.PORT}")

        # Database connection
        engine = create_async_engine(settings.DATABASE_URL)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
