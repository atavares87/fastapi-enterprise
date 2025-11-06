"""
Unit tests for database module.

Tests database connection management and lifecycle.
"""


class TestDatabaseManager:
    """Test cases for DatabaseManager."""

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization."""
        # DatabaseManager is initialized as singleton
        # Just verify it exists and has settings
        from app.infrastructure.database import _db_manager

        assert _db_manager is not None
        assert _db_manager.settings is not None
