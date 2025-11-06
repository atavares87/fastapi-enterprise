"""
Core background tasks for the application.

This module contains general-purpose background tasks that are not
specific to any particular business module.
"""

import asyncio
from datetime import datetime
from typing import Any

from structlog import get_logger

from app.infrastructure.celery_app import celery_app

# Initialize logger
logger = get_logger(__name__)


async def _cleanup_expired_sessions_async(task_id: str) -> dict[str, Any]:
    """
    Async implementation of session cleanup.

    Args:
        task_id: The Celery task ID for logging

    Returns:
        dict: Summary of cleanup operation
    """
    from app.infrastructure.database import get_postgres_session

    logger.info("Starting session cleanup task", task_id=task_id)

    cleanup_summary = {
        "task_id": task_id,
        "started_at": datetime.utcnow().isoformat(),
        "postgres_cleaned": 0,
        "mongo_cleaned": 0,
        "redis_cleaned": 0,
        "total_cleaned": 0,
        "status": "success",
    }

    # Clean up PostgreSQL sessions
    try:
        session = await get_postgres_session()
        try:
            # Example: Clean up expired sessions (implement based on your session table)
            # result = await session.execute(
            #     text("DELETE FROM user_sessions WHERE expires_at < NOW()")
            # )
            # postgres_cleaned = result.rowcount or 0
            postgres_cleaned = 0  # Placeholder until session table is implemented
            cleanup_summary["postgres_cleaned"] = postgres_cleaned
            await session.commit()
            logger.info(
                "PostgreSQL session cleanup completed",
                count=postgres_cleaned,
                task_id=task_id,
            )
        finally:
            await session.close()
    except Exception as e:
        logger.error(
            "Failed to cleanup PostgreSQL sessions",
            error=str(e),
            task_id=task_id,
        )
        cleanup_summary["status"] = "partial_failure"

    # Clean up MongoDB sessions
    try:
        # Example: Clean up expired sessions from MongoDB
        # mongo_client = get_mongodb_client()
        # result = await mongo_client.sessions.delete_many({
        #     "expires_at": {"$lt": datetime.utcnow()}
        # })
        # mongo_cleaned = result.deleted_count
        mongo_cleaned = 0  # Placeholder until session collection is implemented
        cleanup_summary["mongo_cleaned"] = mongo_cleaned
        logger.info(
            "MongoDB session cleanup completed",
            count=mongo_cleaned,
            task_id=task_id,
        )
    except Exception as e:
        logger.error(
            "Failed to cleanup MongoDB sessions",
            error=str(e),
            task_id=task_id,
        )
        cleanup_summary["status"] = "partial_failure"

    # Clean up Redis sessions
    try:
        # Example: Clean up expired Redis sessions (Redis handles TTL automatically, but we can clean up manually)
        # redis_client = get_redis_client()
        # keys = await redis_client.keys("session:*")
        # expired_keys = []
        # for key in keys:
        #     ttl = await redis_client.ttl(key)
        #     if ttl <= 0:  # Expired or no TTL set
        #         expired_keys.append(key)
        # if expired_keys:
        #     redis_cleaned = await redis_client.delete(*expired_keys)
        # else:
        #     redis_cleaned = 0
        redis_cleaned = 0  # Placeholder - Redis handles TTL automatically
        cleanup_summary["redis_cleaned"] = redis_cleaned
        logger.info(
            "Redis session cleanup completed",
            count=redis_cleaned,
            task_id=task_id,
        )
    except Exception as e:
        logger.error(
            "Failed to cleanup Redis sessions",
            error=str(e),
            task_id=task_id,
        )
        cleanup_summary["status"] = "partial_failure"

    # Calculate totals
    total_cleaned = postgres_cleaned + mongo_cleaned + redis_cleaned
    cleanup_summary["total_cleaned"] = total_cleaned
    cleanup_summary["completed_at"] = datetime.utcnow().isoformat()

    logger.info(
        "Session cleanup task completed",
        total_cleaned=total_cleaned,
        postgres_cleaned=postgres_cleaned,
        mongo_cleaned=mongo_cleaned,
        redis_cleaned=redis_cleaned,
        status=cleanup_summary["status"],
        task_id=task_id,
    )

    return cleanup_summary


@celery_app.task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, retry_jitter=True)  # type: ignore[misc]
def cleanup_expired_sessions(self: Any) -> dict[str, Any]:
    """
    Clean up expired user sessions from database.

    This task removes expired sessions from PostgreSQL, MongoDB, and Redis
    to prevent database bloat and improve performance.

    Uses the standard asyncio.run() pattern to execute async database operations
    within a Celery task context.

    Automatically retries up to 3 times with exponential backoff on failure.

    Returns:
        dict: Summary of cleanup operation
    """
    try:
        # Standard pattern: Use asyncio.run() to execute async code in Celery tasks
        result = asyncio.run(_cleanup_expired_sessions_async(self.request.id))

        # If partial_failure, consider retrying
        if (
            result.get("status") == "partial_failure"
            and self.request.retries < self.max_retries
        ):
            logger.warning(
                "Partial failure in session cleanup, will retry",
                task_id=self.request.id,
                retry_count=self.request.retries,
            )
            # Retry with exponential backoff
            countdown = 2**self.request.retries * 60  # 1min, 2min, 4min
            raise self.retry(countdown=countdown, max_retries=3)

        return result

    except Exception as e:
        logger.error(
            "Unexpected error in session cleanup task",
            error=str(e),
            task_id=self.request.id,
            retry_count=self.request.retries,
            exc_info=True,
        )

        # Retry with exponential backoff if retries remain
        if self.request.retries < self.max_retries:
            countdown = 2**self.request.retries * 60  # 1min, 2min, 4min
            raise self.retry(exc=e, countdown=countdown, max_retries=3)

        # Final failure after all retries exhausted
        return {
            "task_id": self.request.id,
            "started_at": datetime.utcnow().isoformat(),
            "postgres_cleaned": 0,
            "mongo_cleaned": 0,
            "redis_cleaned": 0,
            "total_cleaned": 0,
            "status": "error",
            "error": str(e),
            "retries_exhausted": True,
            "completed_at": datetime.utcnow().isoformat(),
        }


async def _periodic_health_check_async(task_id: str) -> dict[str, Any]:
    """
    Async implementation of periodic health check.

    Args:
        task_id: The Celery task ID for logging

    Returns:
        dict: Health check results
    """
    from app.infrastructure.database import check_database_health

    logger.info("Starting periodic health check", task_id=task_id)

    try:
        # Use the existing async health check function
        health_status = await check_database_health()

        health_summary: dict[str, Any] = {
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy" if all(health_status.values()) else "unhealthy",
            "databases": health_status,
            "alerts": [],
        }

        # Check for unhealthy components and create alerts
        alerts_list: list[dict[str, Any]] = health_summary["alerts"]
        for db_name, db_status in health_status.items():
            if not db_status:
                alert = {
                    "component": db_name,
                    "status": "unhealthy",
                    "error": "Connection failed or unavailable",
                    "severity": "high",
                }
                alerts_list.append(alert)

                logger.warning(
                    "Unhealthy component detected",
                    component=db_name,
                    status="unhealthy",
                )

        # Log overall status
        if health_summary["overall_status"] == "healthy":
            logger.info(
                "Health check completed - all systems healthy",
                task_id=task_id,
                databases=health_status,
            )
        else:
            logger.warning(
                "Health check completed - issues detected",
                task_id=task_id,
                databases=health_status,
                alerts=health_summary["alerts"],
            )

        return health_summary

    except Exception as e:
        logger.error(
            "Health check failed",
            error=str(e),
            task_id=task_id,
            exc_info=True,
        )
        return {
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "databases": {},
            "alerts": [
                {
                    "component": "health_check",
                    "status": "error",
                    "error": str(e),
                    "severity": "critical",
                }
            ],
        }


@celery_app.task(bind=True)  # type: ignore[misc]
def periodic_health_check(self: Any) -> dict[str, Any]:
    """
    Perform periodic health checks on system components.

    This task checks the health of databases and other critical
    components and logs any issues found.

    Uses the standard asyncio.run() pattern to execute async database health checks
    within a Celery task context.

    Returns:
        dict: Health check results
    """
    try:
        # Standard pattern: Use asyncio.run() to execute async code in Celery tasks
        return asyncio.run(_periodic_health_check_async(self.request.id))

    except Exception as e:
        logger.error(
            "Unexpected error in periodic health check task",
            error=str(e),
            task_id=self.request.id,
            exc_info=True,
        )
        return {
            "task_id": self.request.id,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "error": str(e),
            "alerts": [
                {
                    "component": "health_check_task",
                    "status": "error",
                    "error": str(e),
                    "severity": "critical",
                }
            ],
        }
