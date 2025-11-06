"""
Global Exception Handlers

Handles exceptions globally across the application.
"""

import uuid

import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.shared.exceptions import DomainException

logger = structlog.get_logger(__name__)


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """
    Handle domain-specific business logic exceptions.

    These are expected exceptions that occur during normal business operations.
    """
    logger.warning(
        "Domain exception occurred",
        exception_type=type(exc).__name__,
        message=str(exc),
        url=str(request.url),
        method=request.method,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"type": type(exc).__name__, "message": str(exc)}},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Returns detailed validation errors to help clients fix their requests.
    """
    logger.warning(
        "Request validation failed",
        errors=exc.errors(),
        url=str(request.url),
        method=request.method,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions securely.

    Never exposes internal exception details to clients.
    All details are logged server-side for debugging.
    """
    # Generate unique error ID for tracking
    error_id = str(uuid.uuid4())

    # Log full exception details server-side (safe)
    logger.error(
        "Unexpected exception occurred",
        error_id=error_id,
        exception_type=type(exc).__name__,
        message=str(exc),
        url=str(request.url),
        method=request.method,
        exc_info=True,
    )

    # Return generic error to client (secure)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "error_id": error_id,
            }
        },
    )
