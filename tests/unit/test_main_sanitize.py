"""
Unit tests for URL sanitization.

Tests sanitize_url function for security.
"""

from app.main import sanitize_url


class TestSanitizeURL:
    """Test cases for sanitize_url function."""

    def test_sanitize_url_with_password(self):
        """Test URL sanitization with password parameter."""
        url = "http://example.com/api?user=test&password=secret123"
        sanitized = sanitize_url(url)

        assert "password=" in sanitized
        assert "secret123" not in sanitized
        assert "***" in sanitized or sanitized != url

    def test_sanitize_url_with_token(self):
        """Test URL sanitization with token parameter."""
        url = "http://example.com/api?token=abc123"
        sanitized = sanitize_url(url)

        assert "token=" in sanitized
        assert "abc123" not in sanitized

    def test_sanitize_url_with_api_key(self):
        """Test URL sanitization with API key."""
        url = "http://example.com/api?api_key=secret123"
        sanitized = sanitize_url(url)

        assert "api_key=" in sanitized
        assert "secret123" not in sanitized

    def test_sanitize_url_with_multiple_sensitive_params(self):
        """Test URL sanitization with multiple sensitive parameters."""
        url = "http://example.com/api?user=test&password=secret&token=abc123"
        sanitized = sanitize_url(url)

        assert "secret" not in sanitized
        assert "abc123" not in sanitized

    def test_sanitize_url_without_sensitive_params(self):
        """Test URL sanitization without sensitive parameters."""
        url = "http://example.com/api?param=value&other=data"
        sanitized = sanitize_url(url)

        assert sanitized == url

    def test_sanitize_url_without_query_string(self):
        """Test URL sanitization without query string."""
        url = "http://example.com/api"
        sanitized = sanitize_url(url)

        assert sanitized == url

    def test_sanitize_url_case_insensitive(self):
        """Test URL sanitization is case insensitive."""
        url = "http://example.com/api?PASSWORD=secret&PASSWORD=secret2"
        sanitized = sanitize_url(url)

        assert "secret" not in sanitized
        assert "secret2" not in sanitized
