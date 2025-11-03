"""
Celery application configuration for background task processing.

This module sets up Celery with Redis as the message broker and result backend,
configures task discovery, and provides the main Celery app instance.
"""

from typing import Any

from celery import Celery

from app.core.config import get_settings
from app.infra.logging import get_logger

# Get settings instance
settings = get_settings()

# Initialize logger
logger = get_logger(__name__)

# Create Celery application instance
celery_app = Celery(
    "fastapi_enterprise",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.core.tasks",  # Core background tasks
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "app.core.tasks.*": {"queue": "default"},
    },
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_max_retries=10,
    result_backend_retry_on_timeout=True,
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Retry settings
    task_default_max_retries=3,
    task_default_retry_delay=60,  # Retry after 60 seconds
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Beat schedule (for periodic tasks) - configurable via environment variables
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "app.core.tasks.cleanup_expired_sessions",
            "schedule": float(settings.CELERY_CLEANUP_SESSIONS_INTERVAL),
        },
        "health-check": {
            "task": "app.core.tasks.periodic_health_check",
            "schedule": float(settings.CELERY_HEALTH_CHECK_INTERVAL),
        },
    },
    beat_schedule_filename="celerybeat-schedule",
    # Security settings
    worker_hijack_root_logger=False,
    worker_log_color=False,
)


@celery_app.task(bind=True)  # type: ignore[misc]
def debug_task(self: Any) -> dict[str, Any]:
    """
    Debug task for testing Celery configuration.

    This task can be used to verify that Celery is working correctly.

    Returns:
        dict: Debug information about the task
    """
    logger.info("Debug task executed", task_id=self.request.id)

    return {
        "task_id": self.request.id,
        "task_name": self.name,
        "args": self.request.args,
        "kwargs": self.request.kwargs,
        "message": "Debug task completed successfully",
    }


# Task discovery and auto-registration
def register_tasks() -> None:
    """
    Register all tasks from different modules.

    This function can be called to ensure all tasks are properly
    registered with the Celery app.
    """
    try:
        # Task modules are imported at module level to register tasks
        logger.info("Task registration completed")

    except Exception as e:
        logger.error("Failed to register tasks", error=str(e))
        raise


# Import task modules at module level to register tasks
try:
    import app.core.tasks  # noqa: F401
except ImportError:
    logger.warning("Core tasks module not found, skipping registration")

# Auth module has been removed from the application


# Configure logging for Celery
def setup_celery_logging() -> None:
    """
    Set up logging for Celery workers.

    This ensures that Celery uses the same structured logging
    configuration as the rest of the application.
    """
    import logging

    from app.infra.logging import get_logger

    # Configure Celery logger
    celery_logger = logging.getLogger("celery")
    celery_logger.handlers = []

    # Use our structured logger
    logger = get_logger("celery")

    class CeleryLogHandler(logging.Handler):
        """Custom log handler for Celery that uses structlog."""

        def emit(self, record: Any) -> None:
            """Emit log record using structlog."""
            try:
                level = record.levelname.lower()
                getattr(logger, level)(
                    record.getMessage(),
                    logger_name=record.name,
                    module=record.module,
                    line_number=record.lineno,
                )
            except Exception:
                self.handleError(record)

    celery_logger.addHandler(CeleryLogHandler())
    celery_logger.setLevel(logging.INFO)


# Initialize Celery logging when module is imported
setup_celery_logging()

# Register tasks when module is imported
register_tasks()


# Export the Celery app
__all__ = ["celery_app"]
