"""
Comprehensive unit tests for sanitize_url function.

Tests URL sanitization with various edge cases.
"""

from app.main import sanitize_url


class TestSanitizeUrl:
    """Test cases for sanitize_url function."""

    def test_sanitize_url_no_query_params(self):
        """Test sanitize_url with no query parameters."""
        url = "https://example.com/api/pricing"
        result = sanitize_url(url)
        assert result == url

    def test_sanitize_url_no_sensitive_params(self):
        """Test sanitize_url with non-sensitive query parameters."""
        url = "https://example.com/api/pricing?material=aluminum&quantity=10"
        result = sanitize_url(url)
        assert result == url

    def test_sanitize_url_password_param(self):
        """Test sanitize_url masks password parameter."""
        url = "https://example.com/api/pricing?material=aluminum&password=secret123"
        result = sanitize_url(url)
        # The function masks the value, check that password param is there but value is masked
        assert "password=" in result
        assert "secret123" not in result
        # Should contain the masked value
        assert "REDACTED" in result or "***" in result

    def test_sanitize_url_token_param(self):
        """Test sanitize_url masks token parameter."""
        url = "https://example.com/api/pricing?token=abc123xyz"
        result = sanitize_url(url)
        assert "token=" in result
        assert "abc123xyz" not in result
        assert "REDACTED" in result or "***" in result

    def test_sanitize_url_multiple_sensitive_params(self):
        """Test sanitize_url masks multiple sensitive parameters."""
        url = "https://example.com/api/pricing?password=secret&token=abc123&api_key=xyz789"
        result = sanitize_url(url)
        assert "password=" in result
        assert "token=" in result
        assert "api_key=" in result
        assert "secret" not in result
        assert "abc123" not in result
        assert "xyz789" not in result

    def test_sanitize_url_case_insensitive(self):
        """Test sanitize_url is case insensitive for parameter names."""
        url = "https://example.com/api/pricing?PASSWORD=secret&Token=abc123"
        result = sanitize_url(url)
        assert "PASSWORD=" in result
        assert "Token=" in result
        assert "secret" not in result
        assert "abc123" not in result

    def test_sanitize_url_mixed_params(self):
        """Test sanitize_url masks sensitive params but keeps others."""
        url = "https://example.com/api/pricing?material=aluminum&quantity=10&password=secret&process=cnc"
        result = sanitize_url(url)
        assert "material=aluminum" in result
        assert "quantity=10" in result
        assert "process=cnc" in result
        assert "password=" in result
        assert "secret" not in result

    def test_sanitize_url_multiple_values(self):
        """Test sanitize_url handles parameters with multiple values."""
        url = "https://example.com/api/pricing?password=secret1&password=secret2"
        result = sanitize_url(url)
        # Should mask all values
        assert "password=" in result
        assert "secret1" not in result
        assert "secret2" not in result

    def test_sanitize_url_all_sensitive_keywords(self):
        """Test sanitize_url recognizes all sensitive keywords."""
        sensitive_params = [
            "password",
            "token",
            "secret",
            "key",
            "api_key",
            "apikey",
            "access_token",
            "refresh_token",
            "auth",
            "authorization",
            "credit_card",
            "ssn",
            "pin",
        ]

        for param in sensitive_params:
            url = f"https://example.com/api/pricing?{param}=sensitive_value"
            result = sanitize_url(url)
            assert f"{param}=" in result
            assert "sensitive_value" not in result

    def test_sanitize_url_empty_param_values(self):
        """Test sanitize_url handles empty parameter values."""
        url = "https://example.com/api/pricing?password=&token="
        result = sanitize_url(url)
        assert "password=" in result
        assert "token=" in result

    def test_sanitize_url_partial_match(self):
        """Test sanitize_url matches partial sensitive keywords."""
        url = "https://example.com/api/pricing?api_key=secret&auth_token=abc"
        result = sanitize_url(url)
        assert "api_key=" in result
        assert (
            "auth_token=" in result or "auth" in result
        )  # auth_token contains "auth" and "token"
        assert "secret" not in result
        assert "abc" not in result
