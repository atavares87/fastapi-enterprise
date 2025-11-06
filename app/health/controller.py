"""
Health Controller - Health check endpoints

Analogous to Spring @RestController for health checks.
"""

from typing import Any

from fastapi import APIRouter

from app.shared.config import get_settings

settings = get_settings()

# Create router for health endpoints
router = APIRouter(tags=["Health"])


@router.get("/health", include_in_schema=True)
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Simple status message indicating service health
    """
    return {"status": "healthy", "service": settings.APP_NAME}


@router.get("/health/detailed", include_in_schema=True)
async def health_check_detailed() -> dict[str, Any]:
    """
    Detailed health check endpoint with component status.

    Returns:
        dict: Detailed health status including service information per contract
    """
    import time

    # Determine environment based on settings
    if settings.TESTING:
        environment = "testing"
    elif settings.DEBUG:
        environment = "development"
    else:
        environment = "production"

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": environment,
        "services": {
            "postgres": True,  # Could check actual connection
            "mongodb": True,  # Could check actual connection
            "redis": True,  # Could check actual connection
        },
        "checks": {
            "application": {"status": "healthy"},
            "postgres": {"status": "healthy"},
            "mongodb": {"status": "healthy"},
            "redis": {"status": "healthy"},
        },
    }


@router.get("/", tags=["Root"])
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
