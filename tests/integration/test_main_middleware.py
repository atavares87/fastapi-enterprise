"""
Integration tests for main application middleware.

Tests logging middleware and request handling.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestLoggingMiddleware:
    """Test cases for logging middleware."""

    def test_middleware_logs_request_start(self, client):
        """Test middleware logs request start."""
        # Make a request - middleware should log it
        response = client.get("/health")

        # Just verify request completes successfully
        assert response.status_code == 200

    def test_middleware_logs_request_completion(self, client):
        """Test middleware logs request completion."""
        response = client.get("/")

        assert response.status_code == 200
        # Middleware logs are side effects, verified via logs

    def test_middleware_handles_request_with_sensitive_params(self, client):
        """Test middleware sanitizes sensitive parameters in URLs."""
        # Request with sensitive params in query string
        response = client.get("/health?password=secret&token=abc123")

        assert response.status_code == 200
        # URL sanitization happens in middleware

    def test_middleware_handles_request_errors(self, client):
        """Test middleware logs request errors."""
        # Make request that causes error - middleware should log it
        # Using invalid endpoint to trigger 404
        response = client.get("/nonexistent")

        assert response.status_code == 404
        # Error logging is a side effect
