"""
Unit tests for exception classes.

Tests custom exception classes.
"""

from app.core.exceptions import DomainException, NotFoundError, ValidationError


class TestDomainException:
    """Test cases for DomainException."""

    def test_domain_exception_default(self):
        """Test DomainException with default values."""
        exc = DomainException("Test message")

        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.status_code == 400
        assert exc.details == {}

    def test_domain_exception_with_details(self):
        """Test DomainException with custom details."""
        exc = DomainException("Test message", status_code=404, details={"key": "value"})

        assert exc.message == "Test message"
        assert exc.status_code == 404
        assert exc.details == {"key": "value"}


class TestValidationError:
    """Test cases for ValidationError."""

    def test_validation_error_without_field(self):
        """Test ValidationError without field."""
        exc = ValidationError("Invalid input")

        assert exc.message == "Invalid input"
        assert exc.status_code == 422
        assert exc.details == {}

    def test_validation_error_with_field(self):
        """Test ValidationError with field."""
        exc = ValidationError("Invalid input", field="email")

        assert exc.message == "Invalid input"
        assert exc.status_code == 422
        assert exc.details == {"field": "email"}


class TestNotFoundError:
    """Test cases for NotFoundError."""

    def test_not_found_error(self):
        """Test NotFoundError."""
        exc = NotFoundError("User", "123")

        assert "User" in exc.message
        assert "123" in exc.message
        assert exc.status_code == 404
        assert exc.details == {"resource": "User", "identifier": "123"}
