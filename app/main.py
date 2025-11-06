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
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config.dependencies import get_pricing_service  # noqa: F401
from app.controller.health_controller import router as health_router
from app.controller.pricing_controller import router as pricing_router
from app.core.config import get_settings
from app.exception.domain_exceptions import DomainException
from app.exception.handler import (
    domain_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)
from app.infrastructure.database import close_databases, init_databases
from app.infrastructure.logging import setup_logging
from app.infrastructure.telemetry import initialize_telemetry, shutdown_telemetry

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
    description="Enterprise-grade FastAPI application with Layered Architecture (Spring Boot style)",
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
# Register global exception handlers
app.add_exception_handler(DomainException, domain_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, general_exception_handler)


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


# === REGISTER ROUTERS ===
# Register all controllers (analogous to Spring Boot component scanning)
app.include_router(health_router)  # Health and root endpoints
app.include_router(pricing_router)  # Pricing endpoints at /api/v1/pricing

logger.info("✅ All controllers registered")
