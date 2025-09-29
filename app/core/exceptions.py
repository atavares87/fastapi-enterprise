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


class ConflictError(DomainException):
    """Exception raised when a resource conflict occurs."""

    def __init__(self, message: str, resource: str | None = None) -> None:
        details = {"resource": resource} if resource else {}
        super().__init__(message, status_code=409, details=details)


class UnauthorizedError(DomainException):
    """Exception raised when authentication fails."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, status_code=401)


class ForbiddenError(DomainException):
    """Exception raised when authorization fails."""

    def __init__(self, message: str = "Access forbidden") -> None:
        super().__init__(message, status_code=403)


class BusinessLogicError(DomainException):
    """Exception raised when business logic constraints are violated."""

    def __init__(self, message: str, constraint: str | None = None) -> None:
        details = {"constraint": constraint} if constraint else {}
        super().__init__(message, status_code=422, details=details)


class ExternalServiceError(DomainException):
    """Exception raised when external service calls fail."""

    def __init__(self, service: str, message: str) -> None:
        details = {"service": service}
        super().__init__(
            f"External service error ({service}): {message}",
            status_code=502,
            details=details,
        )


class RateLimitError(DomainException):
    """Exception raised when rate limits are exceeded."""

    def __init__(self, limit: int, window: str) -> None:
        message = f"Rate limit exceeded: {limit} requests per {window}"
        details = {"limit": limit, "window": window}
        super().__init__(message, status_code=429, details=details)
