"""
Custom Exception Classes

This module defines custom exception classes used throughout the application.
Following the hexagonal architecture pattern, these exceptions represent
domain-level errors that can be handled appropriately by the application.
"""

from typing import Any


class DomainException(Exception):
    """
    Base exception class for domain-specific errors.

    This is the base class for all business logic exceptions.
    It provides a consistent interface for error handling across the application.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize domain exception.

        Args:
            message: Human-readable error message
            status_code: HTTP status code to return
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ValidationError(DomainException):
    """Exception raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        details = {"field": field} if field else {}
        super().__init__(message, status_code=422, details=details)


class NotFoundError(DomainException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: Any) -> None:
        message = f"{resource} with identifier '{identifier}' not found"
        details = {"resource": resource, "identifier": str(identifier)}
        super().__init__(message, status_code=404, details=details)
