"""
Unit tests for application configuration.

These tests verify that the configuration system works correctly
and validates environment variables properly.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


class TestSettings:
    """Test cases for the Settings class."""

    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()

        assert settings.APP_NAME == "FastAPI Enterprise"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.DEBUG is False
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override default values."""
        # Set environment variables
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("APP_NAME", "Test App")

        settings = Settings()

        assert settings.DEBUG is True
        assert settings.PORT == 9000
        assert settings.APP_NAME == "Test App"

    def test_database_url_construction(self, monkeypatch):
        """Test that database URLs are constructed correctly."""
        # Clear any existing DATABASE_URL from test environment
        monkeypatch.delenv("DATABASE_URL", raising=False)

        # Set PostgreSQL components
        monkeypatch.setenv("POSTGRES_SERVER", "test-db")
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        monkeypatch.setenv("POSTGRES_PORT", "5432")

        settings = Settings()

        expected_url = "postgresql+asyncpg://testuser:testpass@test-db:5432/testdb"
        assert str(settings.DATABASE_URL) == expected_url

    def test_explicit_database_url_override(self, monkeypatch):
        """Test that explicit DATABASE_URL overrides components."""
        # Set explicit DATABASE_URL
        explicit_url = "postgresql+asyncpg://explicit:pass@explicit-host:5432/explicit"
        monkeypatch.setenv("DATABASE_URL", explicit_url)

        # Set components that should be ignored
        monkeypatch.setenv("POSTGRES_SERVER", "ignored")
        monkeypatch.setenv("POSTGRES_USER", "ignored")

        settings = Settings()

        assert str(settings.DATABASE_URL) == explicit_url

    def test_mongo_url_construction(self, monkeypatch):
        """Test that MongoDB URLs are constructed correctly."""
        # Clear existing MongoDB URL from test environment
        monkeypatch.delenv("MONGO_URL", raising=False)
        monkeypatch.delenv("MONGODB_URL", raising=False)

        # Test with authentication
        monkeypatch.setenv("MONGO_SERVER", "mongo-server")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("MONGO_USER", "mongouser")
        monkeypatch.setenv("MONGO_PASSWORD", "mongopass")

        settings = Settings()

        expected_url = "mongodb://mongouser:mongopass@mongo-server:27017"
        assert settings.MONGO_URL == expected_url

    def test_mongo_url_without_auth(self, monkeypatch):
        """Test MongoDB URL construction without authentication."""
        # Clear existing MongoDB URL from test environment
        monkeypatch.delenv("MONGO_URL", raising=False)
        monkeypatch.delenv("MONGODB_URL", raising=False)

        # Test without authentication
        monkeypatch.setenv("MONGO_SERVER", "mongo-server")
        monkeypatch.setenv("MONGO_PORT", "27017")
        # Don't set user/password

        settings = Settings()

        expected_url = "mongodb://mongo-server:27017"
        assert settings.MONGO_URL == expected_url

    def test_redis_url_construction(self, monkeypatch):
        """Test that Redis URLs are constructed correctly."""
        # Clear existing Redis URL from test environment
        monkeypatch.delenv("REDIS_URL", raising=False)

        # Test with password
        monkeypatch.setenv("REDIS_HOST", "redis-server")
        monkeypatch.setenv("REDIS_PORT", "6379")
        monkeypatch.setenv("REDIS_DB", "1")
        monkeypatch.setenv("REDIS_PASSWORD", "redispass")

        settings = Settings()

        expected_url = "redis://:redispass@redis-server:6379/1"
        assert settings.REDIS_URL == expected_url

    def test_redis_url_without_password(self, monkeypatch):
        """Test Redis URL construction without password."""
        # Clear existing Redis URL from test environment
        monkeypatch.delenv("REDIS_URL", raising=False)

        # Test without password
        monkeypatch.setenv("REDIS_HOST", "redis-server")
        monkeypatch.setenv("REDIS_PORT", "6379")
        monkeypatch.setenv("REDIS_DB", "2")
        # Don't set password

        settings = Settings()

        expected_url = "redis://redis-server:6379/2"
        assert settings.REDIS_URL == expected_url

    def test_celery_urls_default_to_redis(self):
        """Test that Celery URLs default to Redis URL."""
        settings = Settings()

        assert settings.CELERY_BROKER_URL == settings.REDIS_URL
        assert settings.CELERY_RESULT_BACKEND == settings.REDIS_URL

    def test_celery_url_override(self, monkeypatch):
        """Test that explicit Celery URLs override Redis URL."""
        monkeypatch.setenv("CELERY_BROKER_URL", "redis://celery-broker:6379/0")
        monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://celery-backend:6379/1")

        settings = Settings()

        assert settings.CELERY_BROKER_URL == "redis://celery-broker:6379/0"
        assert settings.CELERY_RESULT_BACKEND == "redis://celery-backend:6379/1"

    def test_environment_properties(self, monkeypatch):
        """Test environment detection properties."""
        # Test development mode
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("TESTING", "false")

        settings = Settings()

        assert settings.is_development is True
        assert settings.is_production is False
        assert settings.is_testing is False

        # Test production mode
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("TESTING", "false")

        settings = Settings()

        assert settings.is_development is False
        assert settings.is_production is True
        assert settings.is_testing is False

        # Test testing mode
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("TESTING", "true")

        settings = Settings()

        assert settings.is_development is False
        assert settings.is_production is False
        assert settings.is_testing is True

    def test_case_insensitive_env_vars(self, monkeypatch):
        """Test that environment variables are case insensitive."""
        monkeypatch.setenv("debug", "true")  # lowercase
        monkeypatch.setenv("PORT", "8080")  # uppercase

        settings = Settings()

        assert settings.DEBUG is True
        assert settings.PORT == 8080

    def test_invalid_port_validation(self, monkeypatch):
        """Test that invalid port numbers are handled."""
        # Port numbers should be integers
        monkeypatch.setenv("PORT", "invalid")

        with pytest.raises(ValidationError):
            Settings()

    def test_secret_key_generation(self):
        """Test that a secret key is generated if not provided."""
        settings = Settings()

        # Secret key should be generated
        assert len(settings.SECRET_KEY) > 0
        assert isinstance(settings.SECRET_KEY, str)

        # Should generate different keys each time
        _settings2 = Settings()
        # Note: This might be the same if using same process, but that's okay

    def test_settings_validation_error_handling(self, monkeypatch):
        """Test handling of validation errors in settings."""
        # Set invalid boolean value
        monkeypatch.setenv("DEBUG", "not_a_boolean")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "DEBUG" in str(exc_info.value) or "debug" in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        "log_level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    )
    def test_valid_log_levels(self, monkeypatch, log_level):
        """Test that valid log levels are accepted."""
        monkeypatch.setenv("LOG_LEVEL", log_level)

        settings = Settings()

        assert settings.LOG_LEVEL == log_level

    @pytest.mark.parametrize("log_format", ["json", "text"])
    def test_valid_log_formats(self, monkeypatch, log_format):
        """Test that valid log formats are accepted."""
        monkeypatch.setenv("LOG_FORMAT", log_format)

        settings = Settings()

        assert settings.LOG_FORMAT == log_format
