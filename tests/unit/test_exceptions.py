"""
Unit tests for exception classes.

Tests custom exception classes.
"""

from app.shared.exceptions import (
    DomainException,
    NotFoundException,
    ValidationException,
)


class TestDomainException:
    """Test cases for DomainException."""

    def test_domain_exception_basic(self):
        """Test DomainException with message."""
        exc = DomainException("Test message")
        assert str(exc) == "Test message"
        assert isinstance(exc, Exception)


class TestValidationException:
    """Test cases for ValidationException."""

    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException("Invalid input")
        assert str(exc) == "Invalid input"
        assert isinstance(exc, DomainException)


class TestNotFoundException:
    """Test cases for NotFoundException."""

    def test_not_found_exception(self):
        """Test NotFoundException."""
        exc = NotFoundException("Resource not found")
        assert str(exc) == "Resource not found"
        assert isinstance(exc, DomainException)
