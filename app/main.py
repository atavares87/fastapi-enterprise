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
from fastapi.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.database import close_databases, init_databases
from app.core.exceptions import DomainException
from app.core.logging import setup_logging
from app.core.telemetry import initialize_telemetry, shutdown_telemetry
from app.modules.pricing.router import router as pricing_router

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
        # Initialize telemetry first
        telemetry_manager = initialize_telemetry()
        telemetry_manager.instrument_fastapi(_app)
        logger.info("✅ Telemetry initialized and FastAPI instrumented successfully")

        # Initialize all database connections (PostgreSQL, MongoDB, Redis)
        await init_databases()
        logger.info("✅ Database connections established successfully")

        # Additional startup tasks can be added here:
        # - Warm up caches
        # - Verify external service connectivity
        # - Load initial data

    except Exception as e:
        logger.error("❌ Failed to start application", error=str(e), exc_info=True)
        raise  # Prevent startup if critical services are unavailable

    # === RUNTIME PHASE ===
    # Application is now ready to serve requests
    yield

    # === SHUTDOWN PHASE ===
    logger.info("🛑 Application shutting down gracefully")
    try:
        # Close all database connections and clean up resources
        await close_databases()
        logger.info("✅ All database connections closed successfully")

        # Shutdown telemetry
        shutdown_telemetry()
        logger.info("✅ Telemetry shutdown completed")
    except Exception as e:
        logger.error("⚠️ Error during shutdown", error=str(e), exc_info=True)

    logger.info("👋 Application shutdown complete")


# Setup logging first
setup_logging()

# Create FastAPI application using standard pattern
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade FastAPI application with hexagonal architecture",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    tags_metadata=[
        {
            "name": "Health",
            "description": "Health check endpoints for monitoring application status and connectivity.",
        },
        {
            "name": "Pricing",
            "description": "Manufacturing pricing calculations across multiple service tiers. Includes cost breakdown, shipping calculations, volume discounts, and complexity surcharges.",
        },
    ],
)


def add_middleware(app: FastAPI) -> None:
    """Add middleware to the FastAPI application."""

    # CORS middleware
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
        """Log all HTTP requests with timing information."""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Log request
        logger.info(
            "HTTP request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            request_id=request_id,
        )

        try:
            response = await call_next(request)

            # Calculate request duration
            process_time = time.time() - start_time

            # Log response
            logger.info(
                "HTTP request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=round(process_time, 4),
                request_id=request_id,
            )

            # Add timing and request ID headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "HTTP request failed",
                method=request.method,
                url=str(request.url),
                process_time=round(process_time, 4),
                error=str(e),
                request_id=request_id,
                exc_info=True,
            )
            raise


def add_exception_handlers(app: FastAPI) -> None:
    """Add custom exception handlers to the FastAPI application."""

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> Any:
        """Handle domain-specific exceptions."""
        logger.warning(
            "Domain exception occurred",
            exception_type=type(exc).__name__,
            message=str(exc),
            url=str(request.url),
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "details": exc.details if hasattr(exc, "details") else None,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle request validation errors."""
        logger.warning(
            "Validation error occurred",
            errors=exc.errors(),
            url=str(request.url),
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
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(
            "Unexpected exception occurred",
            exception_type=type(exc).__name__,
            message=str(exc),
            url=str(request.url),
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": (
                        "An unexpected error occurred"
                        if not settings.DEBUG
                        else str(exc)
                    ),
                }
            },
        )


def include_routers(app: FastAPI) -> None:
    """Include API routers in the FastAPI application."""

    # Root endpoint
    @app.get("/", tags=["Health"])
    async def root() -> dict[str, Any]:
        """Root endpoint with basic API information."""
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "environment": "development" if settings.DEBUG else "production",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "health_check": "/health",
        }

    # Health check endpoints
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, Any]:
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": "development" if settings.DEBUG else "production",
        }

    @app.get("/health/detailed", tags=["Health"])
    async def detailed_health_check() -> dict[str, Any]:
        """Detailed health check with database connectivity."""
        from app.core.database import check_database_health

        db_health = await check_database_health()

        # Add application health check
        all_checks = {
            "application": {
                "status": "healthy"
            },  # Application is running if we reach this point
            **{
                k: {"status": "healthy" if v else "unhealthy"}
                for k, v in db_health.items()
            },
        }

        return {
            "status": (
                "healthy"
                if all(check["status"] == "healthy" for check in all_checks.values())
                else "unhealthy"
            ),
            "timestamp": time.time(),
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": "development" if settings.DEBUG else "production",
            "services": db_health,
            "checks": all_checks,  # Include application check for tests
        }

    # Metrics endpoint for Prometheus
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    @app.get("/metrics", tags=["Health"])
    async def get_metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Include module routers
    # Include pricing router
    app.include_router(pricing_router, prefix="/api/v1")


# Add middleware, exception handlers, and routers to the app
add_middleware(app)
add_exception_handlers(app)
include_routers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # nosec B104 - Intentional binding for container deployment
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
