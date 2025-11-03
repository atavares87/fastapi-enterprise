"""
FastAPI Enterprise Application - Production-Ready API Server

This is the main application entry point that configures and runs the FastAPI server.
Built following hexagonal/clean architecture principles for maintainability and testability.

Features:
- ✅ Async-first design with proper database connection pooling
- ✅ Structured logging with request tracing
- ✅ Comprehensive error handling and validation
- ✅ CORS middleware for cross-origin requests
- ✅ Health check endpoints for monitoring
- ✅ OpenAPI documentation at /docs and /redoc

Architecture:
- Controllers (FastAPI routers) handle HTTP requests/responses
- Services contain business logic and orchestration
- Repositories manage data access and persistence
- Domain models define core business entities
- Configuration is environment-based and type-safe

Quick Start:
    # Development mode
    python -m uvicorn app.main:app --reload --port 8000

    # Production mode
    python -m gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

    # Using Docker
    docker run -p 8000:8000 your-app
"""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.adapter.inbound.web.pricing import router as pricing_router
from app.core.config import get_settings
from app.core.database import close_databases, init_databases
from app.core.exceptions import DomainException
from app.core.logging import setup_logging
from app.core.telemetry import initialize_telemetry, shutdown_telemetry

# Initialize structured logging for the application
logger = structlog.get_logger(__name__)

# Load configuration from environment variables and .env file
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager - handles startup and shutdown.

    This function is called by FastAPI to manage the application lifecycle:
    - Startup: Initialize database connections, load configurations
    - Shutdown: Clean up resources, close connections gracefully

    The context manager pattern ensures proper cleanup even if errors occur.

    Args:
        _app: FastAPI application instance (not used but required by interface)

    Yields:
        None: Control back to FastAPI during normal operation

    Raises:
        Exception: Any startup errors are propagated to prevent incomplete initialization
    """
    # === STARTUP PHASE ===
    logger.info(
        "🚀 Application starting up",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )

    try:
        # Initialize OpenTelemetry for distributed tracing
        telemetry_manager = initialize_telemetry()
        telemetry_manager.instrument_fastapi(_app)
        logger.info("✅ OpenTelemetry initialized (distributed tracing)")

        # Initialize all database connections (PostgreSQL, MongoDB, Redis)
        await init_databases()
        logger.info("✅ Database connections established successfully")

        # System metrics are automatically collected by OTEL SystemMetricsInstrumentor
        logger.info("✅ System metrics (CPU, memory, disk) auto-collected by OTEL")

        # Note: HTTP metrics are automatically handled by OpenTelemetry FastAPI instrumentation
        # Business metrics are recorded using OTEL Meters in use cases

    except Exception as e:
        logger.error("❌ Failed to start application", error=str(e), exc_info=True)
        raise  # Prevent startup if critical services are unavailable

    # === RUNTIME PHASE ===
    # Application is now ready to serve requests
    yield

    # === SHUTDOWN PHASE ===
    logger.info("🛑 Application shutting down gracefully")
    try:
        # System metrics automatically stopped by OTEL
        logger.info("✅ System metrics stopped")

        # Close all database connections
        await close_databases()
        logger.info("✅ Database connections closed")

        # Shutdown telemetry
        await shutdown_telemetry()
        logger.info("✅ Telemetry shutdown complete")

    except Exception as e:
        logger.error("❌ Error during shutdown", error=str(e), exc_info=True)
        raise


# === APPLICATION SETUP ===
# Configure structured logging
setup_logging()

# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-grade FastAPI application with hexagonal architecture",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# === OPENTELEMETRY METRICS (INDUSTRY STANDARD) ===
# OpenTelemetry automatically instruments FastAPI and exposes /metrics endpoint
# OTEL handles tracing, prometheus-fastapi-instrumentator handles metrics (standard approach)
logger.info("✅ Observability configured (OTEL tracing + Prometheus metrics)")


# === MIDDLEWARE ===
def add_middleware(app: FastAPI) -> None:
    """
    Add middleware to the FastAPI application.

    Middleware is executed for every request in the order it's added (top to bottom).
    Each middleware can process the request, call the next middleware, then process the response.

    Current middleware:
    - CORS: Allow cross-origin requests from specified domains
    - Request logging: Log all HTTP requests with timing information
    """
    # CORS middleware - allow cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Any) -> Any:
        """
        Log all HTTP requests with timing, status code, and sanitized URLs.

        Masks sensitive parameters in URLs (passwords, tokens, etc.).
        """
        start_time = time.time()

        # Sanitize URL to mask sensitive parameters
        sanitized_url = sanitize_url(str(request.url))

        logger.info(
            "HTTP request started",
            method=request.method,
            url=sanitized_url,
            client_host=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            logger.info(
                "HTTP request completed",
                method=request.method,
                url=sanitized_url,
                status_code=response.status_code,
                duration_seconds=round(duration, 3),
            )
            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "HTTP request failed",
                method=request.method,
                url=sanitized_url,
                duration_seconds=round(duration, 3),
                error=str(e),
                exc_info=True,
            )
            raise


def sanitize_url(url: str) -> str:
    """
    Sanitize URL by masking sensitive query parameters.

    Masks common sensitive parameters like passwords, tokens, keys, secrets.
    """
    from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

    parsed = urlparse(url)
    if not parsed.query:
        return url

    # Sensitive parameter names to mask
    sensitive_params = {
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
    }

    # Parse query parameters
    params = parse_qs(parsed.query, keep_blank_values=True)

    # Mask sensitive parameters
    sanitized_params = {}
    for key, values in params.items():
        if any(sensitive in key.lower() for sensitive in sensitive_params):
            sanitized_params[key] = ["***REDACTED***"] * len(values)
        else:
            sanitized_params[key] = values

    # Rebuild URL
    new_query = urlencode(sanitized_params, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


# Register middleware
add_middleware(app)


# === EXCEPTION HANDLERS ===
@app.exception_handler(DomainException)
async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """
    Handle domain-specific business logic exceptions.

    These are expected exceptions that occur during normal business operations
    (e.g., invalid input, business rule violations). They're logged as warnings
    and return appropriate HTTP 400 status codes with detailed error messages.

    Args:
        request: The HTTP request that caused the exception
        exc: The domain exception that was raised

    Returns:
        JSONResponse: A 400 Bad Request response with error details
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    These occur when request data doesn't match the expected schema.
    Returns detailed validation errors to help clients fix their requests.

    Args:
        request: The HTTP request that failed validation
        exc: The validation exception with detailed error information

    Returns:
        JSONResponse: A 422 Unprocessable Entity response with validation errors
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


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions securely.

    Never exposes internal exception details to clients, even in debug mode.
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
        exc_info=True,  # Includes full stack trace in logs
    )

    # Return generic error to client (secure)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "error_id": error_id,  # For support team to correlate with logs
            }
        },
    )


# === PROMETHEUS METRICS (STANDARD prometheus-fastapi-instrumentator) ===
# This is the STANDARD, documented approach for FastAPI + Prometheus
# Reference: https://github.com/trallnag/prometheus-fastapi-instrumentator
# Standard configuration with all built-in metrics
# This follows the library's documented API - NO custom code!
instrumentator = Instrumentator(
    should_instrument_requests_inprogress=True,  # Enables http_requests_in_progress gauge
    should_respect_env_var=False,  # Always enable metrics
    inprogress_name="http_requests_in_progress",  # Standard metric name
    inprogress_labels=True,  # Include labels on in-progress gauge
)

# Instrument app and expose /metrics endpoint (standard method)
instrumentator.instrument(app).expose(app)


# Health check endpoint
@app.get("/health", tags=["Health"], include_in_schema=True)
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Simple status message indicating service health
    """
    return {"status": "healthy", "service": settings.APP_NAME}


# Register API routers
app.include_router(pricing_router, prefix="/api/v1", tags=["Pricing"])


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """
    Root endpoint with API information.

    Returns:
        dict: Welcome message and links to documentation
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
