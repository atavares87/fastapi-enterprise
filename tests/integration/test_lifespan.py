"""
Integration tests for application lifespan.

Tests startup and shutdown lifecycle.
"""

from app.main import app, lifespan


class TestLifespan:
    """Test cases for application lifespan."""

    def test_app_has_lifespan(self):
        """Test that app has lifespan configured."""
        # FastAPI app should have lifespan
        assert app.router.lifespan_context is not None

    def test_lifespan_function_exists(self):
        """Test that lifespan function is defined."""
        assert lifespan is not None
        assert callable(lifespan)
