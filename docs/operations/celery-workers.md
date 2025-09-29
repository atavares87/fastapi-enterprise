# Celery Workers and Background Tasks

## Overview

This guide covers the setup, management, and best practices for using Celery with Redis as a message broker for background task processing in the FastAPI Enterprise application.

## Celery Architecture

### System Components

```mermaid
graph TB
    subgraph "FastAPI Application"
        API[API Endpoints]
        Services[Domain Services]
    end

    subgraph "Celery Infrastructure"
        Producer[Task Producer]
        Broker[Redis Broker]
        Worker[Celery Worker]
        Beat[Celery Beat Scheduler]
        Monitor[Flower Monitor]
    end

    subgraph "Storage"
        ResultBackend[Redis Result Backend]
        Database[(PostgreSQL)]
    end

    API --> Producer
    Producer --> Broker
    Broker --> Worker
    Worker --> ResultBackend
    Worker --> Database
    Beat --> Broker
    Monitor --> Broker
    Monitor --> ResultBackend
```

### Task Flow

1. **Task Creation**: FastAPI endpoints or services create tasks
2. **Task Queuing**: Tasks are sent to Redis broker
3. **Task Processing**: Celery workers pick up and execute tasks
4. **Result Storage**: Results are stored in Redis backend
5. **Monitoring**: Flower provides web-based monitoring

## Celery Configuration

### Application Setup

**Celery Application** (`app/infrastructure/tasks/celery_app.py`):

```python
from celery import Celery
from kombu import Queue
from app.core.config.settings import settings

# Create Celery application
celery_app = Celery("fastapi_enterprise")

# Configure broker and result backend
celery_app.conf.update(
    # Broker settings
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,

    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.infrastructure.tasks.pricing_tasks.*": {"queue": "pricing"},
        "app.infrastructure.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.infrastructure.tasks.data_tasks.*": {"queue": "data_processing"},
        "app.infrastructure.tasks.maintenance_tasks.*": {"queue": "maintenance"},
    },

    # Queue definitions
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("pricing", routing_key="pricing"),
        Queue("notifications", routing_key="notifications"),
        Queue("data_processing", routing_key="data_processing"),
        Queue("maintenance", routing_key="maintenance"),
    ),

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=True,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Error handling
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,

    # Beat scheduler settings (for periodic tasks)
    beat_schedule={
        "expire-old-quotes": {
            "task": "app.infrastructure.tasks.maintenance_tasks.expire_old_quotes",
            "schedule": 3600.0,  # Every hour
        },
        "cleanup-expired-reservations": {
            "task": "app.infrastructure.tasks.maintenance_tasks.cleanup_expired_reservations",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "generate-daily-reports": {
            "task": "app.infrastructure.tasks.data_tasks.generate_daily_reports",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "backup-pricing-data": {
            "task": "app.infrastructure.tasks.data_tasks.backup_pricing_data",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Weekly Sunday 3 AM
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "app.infrastructure.tasks.pricing_tasks",
    "app.infrastructure.tasks.notification_tasks",
    "app.infrastructure.tasks.data_tasks",
    "app.infrastructure.tasks.maintenance_tasks",
])

# Task base class for dependency injection
class BaseTask(celery_app.Task):
    """Base task class with dependency injection"""

    def __init__(self):
        self._pricing_service = None
        self._notification_service = None
        self._analytics_service = None

    @property
    def pricing_service(self):
        if self._pricing_service is None:
            from app.api.dependencies import get_pricing_service
            self._pricing_service = get_pricing_service()
        return self._pricing_service

    @property
    def notification_service(self):
        if self._notification_service is None:
            from app.api.dependencies import get_notification_service
            self._notification_service = get_notification_service()
        return self._notification_service

    @property
    def analytics_service(self):
        if self._analytics_service is None:
            from app.api.dependencies import get_analytics_service
            self._analytics_service = get_analytics_service()
        return self._analytics_service

# Set base task class
celery_app.Task = BaseTask
```

### Task Implementation

**Pricing Tasks** (`app/infrastructure/tasks/pricing_tasks.py`):

```python
import asyncio
from typing import Dict, List, Any
from uuid import UUID
from celery import shared_task
from app.infrastructure.tasks.celery_app import celery_app

@shared_task(bind=True, name="pricing.calculate_bulk_pricing")
def calculate_bulk_pricing(self, specifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate pricing for multiple specifications in background"""
    try:
        # Convert to domain objects
        from app.domains.pricing.models import PartSpecification

        results = []
        for spec_data in specifications:
            specification = PartSpecification.from_dict(spec_data)

            # Use async service in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                pricing_result = loop.run_until_complete(
                    self.pricing_service.calculate_pricing(specification)
                )
                results.append({
                    "specification": spec_data,
                    "result": pricing_result.to_dict(),
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "specification": spec_data,
                    "error": str(e),
                    "status": "error"
                })
            finally:
                loop.close()

        return {
            "total_processed": len(specifications),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results
        }

    except Exception as e:
        # Log error and reraise
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("bulk_pricing_calculation_failed", error=str(e))
        raise

@shared_task(bind=True, name="pricing.update_material_costs")
def update_material_costs(self, material_updates: Dict[str, float]) -> Dict[str, Any]:
    """Update material costs from external API"""
    try:
        updated_materials = []
        failed_materials = []

        for material_code, new_cost in material_updates.items():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                loop.run_until_complete(
                    self.pricing_service.update_material_cost(material_code, new_cost)
                )

                updated_materials.append(material_code)
                loop.close()

            except Exception as e:
                failed_materials.append({
                    "material": material_code,
                    "error": str(e)
                })

        return {
            "updated": updated_materials,
            "failed": failed_materials,
            "total_updated": len(updated_materials),
            "total_failed": len(failed_materials)
        }

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("material_cost_update_failed", error=str(e))
        raise

@shared_task(bind=True, name="pricing.recalculate_customer_quotes")
def recalculate_customer_quotes(self, customer_id: str, material_code: str) -> Dict[str, Any]:
    """Recalculate all active quotes for a customer when material costs change"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Get customer's active quotes
            from app.domains.quotes.models import QuoteStatus

            quotes = loop.run_until_complete(
                self.pricing_service.get_customer_quotes(
                    UUID(customer_id),
                    status=QuoteStatus.DRAFT
                )
            )

            updated_quotes = []
            failed_quotes = []

            for quote in quotes:
                # Check if quote uses the updated material
                if quote.specification.material == material_code:
                    try:
                        # Recalculate pricing
                        new_pricing = loop.run_until_complete(
                            self.pricing_service.calculate_pricing(quote.specification)
                        )

                        # Update quote with new pricing
                        quote.add_version(new_pricing, f"Auto-update due to {material_code} cost change")

                        updated_quotes.append(str(quote.id))

                    except Exception as e:
                        failed_quotes.append({
                            "quote_id": str(quote.id),
                            "error": str(e)
                        })

            return {
                "customer_id": customer_id,
                "material_code": material_code,
                "quotes_updated": updated_quotes,
                "quotes_failed": failed_quotes,
                "total_updated": len(updated_quotes),
                "total_failed": len(failed_quotes)
            }

        finally:
            loop.close()

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("quote_recalculation_failed", customer_id=customer_id, error=str(e))
        raise
```

**Notification Tasks** (`app/infrastructure/tasks/notification_tasks.py`):

```python
from typing import Dict, List, Any
from celery import shared_task
from app.infrastructure.tasks.celery_app import celery_app

@shared_task(bind=True, name="notifications.send_quote_email")
def send_quote_email(self, quote_id: str, customer_email: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send quote email to customer"""
    try:
        import asyncio
        from app.domains.notifications.services import EmailService

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            email_service = EmailService()

            # Generate PDF quote
            pdf_content = loop.run_until_complete(
                email_service.generate_quote_pdf(quote_id, template_data)
            )

            # Send email with attachment
            result = loop.run_until_complete(
                email_service.send_email(
                    to_email=customer_email,
                    subject=f"Quote #{template_data.get('quote_number', quote_id)}",
                    template="quote_email.html",
                    template_data=template_data,
                    attachments=[{
                        "filename": f"quote_{quote_id}.pdf",
                        "content": pdf_content,
                        "content_type": "application/pdf"
                    }]
                )
            )

            return {
                "quote_id": quote_id,
                "customer_email": customer_email,
                "email_sent": True,
                "message_id": result.get("message_id"),
                "status": "success"
            }

        finally:
            loop.close()

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("quote_email_failed", quote_id=quote_id, error=str(e))

        return {
            "quote_id": quote_id,
            "customer_email": customer_email,
            "email_sent": False,
            "error": str(e),
            "status": "failed"
        }

@shared_task(bind=True, name="notifications.send_low_stock_alerts")
def send_low_stock_alerts(self, low_stock_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Send low stock alerts to procurement team"""
    try:
        import asyncio
        from app.domains.notifications.services import EmailService

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            email_service = EmailService()

            # Prepare email content
            template_data = {
                "low_stock_items": low_stock_items,
                "alert_date": datetime.utcnow().isoformat(),
                "total_items": len(low_stock_items)
            }

            # Send to procurement team
            procurement_emails = ["procurement@company.com", "inventory@company.com"]

            results = []
            for email in procurement_emails:
                result = loop.run_until_complete(
                    email_service.send_email(
                        to_email=email,
                        subject=f"Low Stock Alert - {len(low_stock_items)} items need attention",
                        template="low_stock_alert.html",
                        template_data=template_data
                    )
                )
                results.append(result)

            return {
                "alerts_sent": len(results),
                "recipients": procurement_emails,
                "low_stock_count": len(low_stock_items),
                "status": "success"
            }

        finally:
            loop.close()

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("low_stock_alert_failed", error=str(e))
        raise

@shared_task(bind=True, name="notifications.send_bulk_notifications")
def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Send multiple notifications in batch"""
    successful = 0
    failed = 0
    results = []

    for notification in notifications:
        try:
            if notification["type"] == "email":
                result = send_quote_email.delay(
                    notification["quote_id"],
                    notification["customer_email"],
                    notification["template_data"]
                )
                results.append({"id": str(result.id), "type": "email", "status": "queued"})
                successful += 1

            elif notification["type"] == "sms":
                # Implement SMS sending
                pass

        except Exception as e:
            results.append({
                "notification": notification,
                "error": str(e),
                "status": "failed"
            })
            failed += 1

    return {
        "total_processed": len(notifications),
        "successful": successful,
        "failed": failed,
        "results": results
    }
```

**Maintenance Tasks** (`app/infrastructure/tasks/maintenance_tasks.py`):

```python
import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from app.infrastructure.tasks.celery_app import celery_app

@shared_task(bind=True, name="maintenance.expire_old_quotes")
def expire_old_quotes(self) -> Dict[str, Any]:
    """Expire quotes that have passed their validity date"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            expired_count = loop.run_until_complete(
                self.pricing_service.expire_old_quotes()
            )

            return {
                "expired_quotes": expired_count,
                "execution_time": datetime.utcnow().isoformat(),
                "status": "success"
            }

        finally:
            loop.close()

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("expire_quotes_failed", error=str(e))
        raise

@shared_task(bind=True, name="maintenance.cleanup_expired_reservations")
def cleanup_expired_reservations(self) -> Dict[str, Any]:
    """Clean up expired stock reservations"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            from app.api.dependencies import get_inventory_service
            inventory_service = get_inventory_service()

            cleaned_count = loop.run_until_complete(
                inventory_service.expire_old_reservations()
            )

            return {
                "cleaned_reservations": cleaned_count,
                "execution_time": datetime.utcnow().isoformat(),
                "status": "success"
            }

        finally:
            loop.close()

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("cleanup_reservations_failed", error=str(e))
        raise

@shared_task(bind=True, name="maintenance.check_system_health")
def check_system_health(self) -> Dict[str, Any]:
    """Perform comprehensive system health check"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            from app.api.dependencies import get_health_service
            health_service = get_health_service()

            health_status = loop.run_until_complete(
                health_service.check_detailed_health()
            )

            # If any critical services are down, send alerts
            if health_status.overall_status == "unhealthy":
                # Send alert to operations team
                send_system_alert.delay({
                    "alert_type": "system_health",
                    "status": health_status.dict(),
                    "timestamp": datetime.utcnow().isoformat()
                })

            return {
                "health_status": health_status.dict(),
                "execution_time": datetime.utcnow().isoformat(),
                "status": "success"
            }

        finally:
            loop.close()

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("health_check_failed", error=str(e))
        raise

@shared_task(bind=True, name="maintenance.database_maintenance")
def database_maintenance(self) -> Dict[str, Any]:
    """Perform database maintenance tasks"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        maintenance_results = {}

        try:
            # Clean up old log entries
            from app.infrastructure.database.postgres.connection import PostgreSQLConnection
            from app.core.config.settings import settings

            db_connection = PostgreSQLConnection(settings.postgres_url)

            async with db_connection.get_session() as session:
                # Remove old logs (older than 30 days)
                cutoff_date = datetime.utcnow() - timedelta(days=30)

                result = await session.execute(text("""
                    DELETE FROM application_logs
                    WHERE created_at < :cutoff_date
                """), {"cutoff_date": cutoff_date})

                maintenance_results["deleted_logs"] = result.rowcount

                # Update database statistics
                await session.execute(text("ANALYZE"))
                maintenance_results["statistics_updated"] = True

                await session.commit()

            return {
                "maintenance_results": maintenance_results,
                "execution_time": datetime.utcnow().isoformat(),
                "status": "success"
            }

        finally:
            loop.close()

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("database_maintenance_failed", error=str(e))
        raise

@shared_task(bind=True, name="maintenance.send_system_alert")
def send_system_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send system alert to operations team"""
    try:
        import asyncio
        from app.domains.notifications.services import EmailService

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            email_service = EmailService()

            # Send to operations team
            operations_emails = ["ops@company.com", "devops@company.com"]

            for email in operations_emails:
                loop.run_until_complete(
                    email_service.send_email(
                        to_email=email,
                        subject=f"System Alert - {alert_data['alert_type']}",
                        template="system_alert.html",
                        template_data=alert_data
                    )
                )

            return {
                "alert_sent": True,
                "recipients": operations_emails,
                "alert_type": alert_data["alert_type"],
                "status": "success"
            }

        finally:
            loop.close()

    except Exception as e:
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("system_alert_failed", error=str(e))
        raise
```

## Running Celery Workers

### Development Environment

**Start Celery Worker**:
```bash
# Start worker for all queues
make celery-worker

# Or manually
uv run celery -A app.infrastructure.tasks.celery_app worker --loglevel=info

# Start worker for specific queue
uv run celery -A app.infrastructure.tasks.celery_app worker --loglevel=info -Q pricing

# Start multiple workers for different queues
uv run celery -A app.infrastructure.tasks.celery_app worker --loglevel=info -Q pricing,notifications
```

**Start Celery Beat (Scheduler)**:
```bash
# Start beat scheduler
make celery-beat

# Or manually
uv run celery -A app.infrastructure.tasks.celery_app beat --loglevel=info
```

**Start Flower (Monitoring)**:
```bash
# Start flower monitoring
make celery-flower

# Or manually
uv run celery -A app.infrastructure.tasks.celery_app flower --port=5555
```

### Production Environment

**Production Worker Configuration**:
```bash
# Start production worker with optimized settings
uv run celery -A app.infrastructure.tasks.celery_app worker \
    --loglevel=warning \
    --concurrency=4 \
    --max-tasks-per-child=1000 \
    --time-limit=3600 \
    --soft-time-limit=3000 \
    --queues=pricing,notifications \
    --hostname=worker1@%h
```

**Systemd Service Configuration** (`/etc/systemd/system/celery-worker.service`):
```ini
[Unit]
Description=Celery Worker Service
After=network.target redis.service postgresql.service

[Service]
Type=notify
User=celery
Group=celery
EnvironmentFile=/etc/celery/celery.conf
WorkingDirectory=/opt/fastapi-enterprise
ExecStart=/opt/fastapi-enterprise/.venv/bin/celery -A app.infrastructure.tasks.celery_app worker \
    --loglevel=warning \
    --pidfile=/var/run/celery/worker.pid \
    --logfile=/var/log/celery/worker.log
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Docker Configuration** (`docker-compose.yml`):
```yaml
services:
  celery-worker:
    build: .
    command: uv run celery -A app.infrastructure.tasks.celery_app worker --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql+asyncpg://postgres:password@postgres:5432/fastapi_enterprise
    volumes:
      - ./app:/app/app
    restart: unless-stopped

  celery-beat:
    build: .
    command: uv run celery -A app.infrastructure.tasks.celery_app beat --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql+asyncpg://postgres:password@postgres:5432/fastapi_enterprise
    volumes:
      - ./app:/app/app
    restart: unless-stopped

  flower:
    build: .
    command: uv run celery -A app.infrastructure.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
    restart: unless-stopped
```

## Task Management

### Creating and Executing Tasks

**From FastAPI Endpoints**:
```python
from app.infrastructure.tasks.pricing_tasks import calculate_bulk_pricing
from app.infrastructure.tasks.notification_tasks import send_quote_email

@router.post("/bulk-pricing")
async def create_bulk_pricing_job(specifications: List[Dict[str, Any]]):
    """Create bulk pricing calculation job"""
    # Start background task
    task = calculate_bulk_pricing.delay(specifications)

    return {
        "job_id": task.id,
        "status": "queued",
        "message": "Bulk pricing calculation started"
    }

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and results"""
    from app.infrastructure.tasks.celery_app import celery_app

    task = celery_app.AsyncResult(job_id)

    if task.state == "PENDING":
        return {"job_id": job_id, "status": "pending"}
    elif task.state == "SUCCESS":
        return {
            "job_id": job_id,
            "status": "completed",
            "result": task.result
        }
    elif task.state == "FAILURE":
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(task.info)
        }
    else:
        return {
            "job_id": job_id,
            "status": task.state,
            "progress": task.info
        }
```

**Task Chaining and Groups**:
```python
from celery import chain, group, chord

# Sequential task execution
pricing_pipeline = chain(
    calculate_bulk_pricing.s(specifications),
    send_quote_email.s(),
    update_analytics.s()
)
result = pricing_pipeline.apply_async()

# Parallel task execution
parallel_calculations = group(
    calculate_bulk_pricing.s(batch1),
    calculate_bulk_pricing.s(batch2),
    calculate_bulk_pricing.s(batch3)
)
result = parallel_calculations.apply_async()

# Callback after group completion
calculation_with_callback = chord(
    group(
        calculate_bulk_pricing.s(batch1),
        calculate_bulk_pricing.s(batch2)
    )
)(send_completion_notification.s())
```

### Error Handling and Retries

**Task Retry Configuration**:
```python
@shared_task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_jitter=True
)
def external_api_task(self, data):
    """Task with automatic retry on specific exceptions"""
    try:
        # Call external API
        result = external_api.call(data)
        return result
    except (ConnectionError, TimeoutError) as exc:
        # These will be automatically retried
        raise
    except ValueError as exc:
        # Manual retry with custom logic
        if self.request.retries < 2:
            raise self.retry(countdown=30)
        else:
            # Give up after 2 retries for ValueError
            raise
```

**Custom Error Handling**:
```python
@shared_task(bind=True)
def resilient_task(self, data):
    """Task with comprehensive error handling"""
    try:
        # Task logic here
        result = process_data(data)
        return {"status": "success", "result": result}

    except TemporaryError as exc:
        # Retry temporary errors
        logger.warning(f"Temporary error in task {self.request.id}: {exc}")
        raise self.retry(countdown=60, max_retries=5)

    except PermanentError as exc:
        # Don't retry permanent errors
        logger.error(f"Permanent error in task {self.request.id}: {exc}")
        return {"status": "failed", "error": str(exc)}

    except Exception as exc:
        # Log unexpected errors and fail
        logger.exception(f"Unexpected error in task {self.request.id}")
        return {"status": "error", "error": str(exc)}
```

## Monitoring and Management

### Flower Web Interface

Access Flower at `http://localhost:5555` to monitor:
- Active tasks and workers
- Task history and results
- Worker statistics
- Queue lengths
- Task execution times

### Command Line Monitoring

```bash
# Monitor active workers
uv run celery -A app.infrastructure.tasks.celery_app status

# Monitor events in real-time
uv run celery -A app.infrastructure.tasks.celery_app events

# Show active tasks
uv run celery -A app.infrastructure.tasks.celery_app inspect active

# Show scheduled tasks
uv run celery -A app.infrastructure.tasks.celery_app inspect scheduled

# Show worker statistics
uv run celery -A app.infrastructure.tasks.celery_app inspect stats

# Purge all tasks from queue
uv run celery -A app.infrastructure.tasks.celery_app purge

# Revoke a specific task
uv run celery -A app.infrastructure.tasks.celery_app revoke <task_id>
```

### Health Checks

**Worker Health Check**:
```python
@shared_task(bind=True, name="maintenance.worker_health_check")
def worker_health_check(self):
    """Health check task for worker monitoring"""
    import time
    start_time = time.time()

    # Perform health checks
    checks = {
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }

    execution_time = time.time() - start_time

    return {
        "worker_id": self.request.hostname,
        "timestamp": datetime.utcnow().isoformat(),
        "execution_time": execution_time,
        "checks": checks,
        "healthy": all(checks.values())
    }
```

**Queue Length Monitoring**:
```python
from app.infrastructure.tasks.celery_app import celery_app

def get_queue_lengths():
    """Get current queue lengths"""
    inspect = celery_app.control.inspect()

    # Get active tasks by queue
    active_tasks = inspect.active()
    scheduled_tasks = inspect.scheduled()
    reserved_tasks = inspect.reserved()

    queue_stats = {}
    for worker, tasks in active_tasks.items():
        for task in tasks:
            queue = task.get('delivery_info', {}).get('routing_key', 'default')
            if queue not in queue_stats:
                queue_stats[queue] = {'active': 0, 'scheduled': 0, 'reserved': 0}
            queue_stats[queue]['active'] += 1

    return queue_stats
```

## Performance Optimization

### Worker Scaling

**Horizontal Scaling**:
```bash
# Multiple workers on same machine
uv run celery -A app.infrastructure.tasks.celery_app worker --concurrency=8 -n worker1@%h
uv run celery -A app.infrastructure.tasks.celery_app worker --concurrency=8 -n worker2@%h

# Workers on different machines
# Machine 1:
uv run celery -A app.infrastructure.tasks.celery_app worker -n worker@machine1

# Machine 2:
uv run celery -A app.infrastructure.tasks.celery_app worker -n worker@machine2
```

**Queue-Based Scaling**:
```bash
# Dedicated workers for different queues
uv run celery -A app.infrastructure.tasks.celery_app worker -Q pricing --concurrency=4
uv run celery -A app.infrastructure.tasks.celery_app worker -Q notifications --concurrency=8
uv run celery -A app.infrastructure.tasks.celery_app worker -Q maintenance --concurrency=2
```

### Memory Management

**Worker Memory Limits**:
```python
# In celery configuration
celery_app.conf.update(
    worker_max_memory_per_child=1000000,  # 1GB in KB
    worker_max_tasks_per_child=1000,      # Restart after 1000 tasks
)
```

**Task Memory Optimization**:
```python
@shared_task
def memory_efficient_task(large_data_id):
    """Process large data without keeping it all in memory"""
    # Process data in chunks instead of loading all at once
    for chunk in get_data_chunks(large_data_id):
        process_chunk(chunk)
        # Explicitly clean up
        del chunk
        gc.collect()
```

### Performance Monitoring

**Task Performance Tracking**:
```python
import time
from functools import wraps

def track_performance(func):
    """Decorator to track task performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Log performance metrics
            logger.info(
                "task_completed",
                task_name=func.__name__,
                execution_time=execution_time,
                status="success"
            )
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "task_failed",
                task_name=func.__name__,
                execution_time=execution_time,
                error=str(e),
                status="failed"
            )
            raise

    return wrapper

@shared_task
@track_performance
def monitored_task(data):
    """Task with performance monitoring"""
    # Task logic here
    pass
```

## Troubleshooting

### Common Issues

**Worker Not Processing Tasks**:
```bash
# Check worker status
uv run celery -A app.infrastructure.tasks.celery_app inspect ping

# Check if worker is consuming from correct queues
uv run celery -A app.infrastructure.tasks.celery_app inspect active_queues

# Restart worker
sudo systemctl restart celery-worker
```

**Memory Issues**:
```bash
# Monitor worker memory usage
uv run celery -A app.infrastructure.tasks.celery_app inspect memdump

# Check for memory leaks
ps aux | grep celery
```

**Task Stuck in Pending**:
```python
# Check task status
from app.infrastructure.tasks.celery_app import celery_app
task = celery_app.AsyncResult('task-id')
print(task.state, task.info)

# Check if task is in queue
inspect = celery_app.control.inspect()
print(inspect.scheduled())
print(inspect.reserved())
```

**Connection Issues**:
```bash
# Test Redis connection
redis-cli ping

# Check Redis memory usage
redis-cli info memory

# Monitor Redis connections
redis-cli client list
```

This comprehensive guide provides everything needed to effectively use Celery for background task processing in a production FastAPI application.
