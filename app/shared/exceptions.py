"""Domain Exceptions - Business rule violations."""


class DomainException(Exception):
    """Base exception for domain-specific errors."""

    pass


class ValidationException(DomainException):
    """Exception for validation errors."""

    pass


class NotFoundException(DomainException):
    """Exception for not found errors."""

    pass


class BusinessRuleViolationException(DomainException):
    """Exception for business rule violations."""

    pass
