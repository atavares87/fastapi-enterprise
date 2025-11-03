# Operations Documentation

## Quick Reference

```bash
# Start services
docker-compose up -d

# View metrics
open http://localhost:8000/metrics

# View dashboards
open http://localhost:3000  # Grafana (admin/admin)

# Run migrations
alembic upgrade head

# Background workers
celery -A app.core.celery_app worker --loglevel=info
```

## Guides

1. **[Docker Deployment](docker-deployment.md)** - Container orchestration and production deployment

2. **[Database Migrations](database-migrations.md)** - Alembic migration management

3. **[Golden 4 Metrics](golden4-metrics.md)** - Latency, traffic, errors, saturation monitoring

4. **[SLO Definitions](slo-definitions.md)** - Service level objectives and error budgets

5. **[Celery Workers](celery-workers.md)** - Background task processing

## Monitoring

### Metrics Endpoints

- **Prometheus Metrics**: http://localhost:8000/metrics
- **Health Check**: http://localhost:8000/health
- **Detailed Health**: http://localhost:8000/health/detailed

### Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
  - Enterprise Metrics Dashboard - Golden 4 metrics
  - SLO Dashboard - Service level objectives
  - Pricing Dashboard - Business metrics

- **Prometheus**: http://localhost:9090
  - Query metrics directly
  - View targets and alerts

### Key Metrics

**Golden 4:**
- `http_server_request_duration_seconds` - Latency
- `http_server_requests_total` - Traffic
- `http_server_errors_total` - Errors
- `http_server_active_requests` - Saturation

**SLOs:**
- 99.9% availability (30-day window)
- 95% of requests < 500ms (p95 latency)
- 99% of requests < 1s (p99 latency)

[Full metrics guide →](golden4-metrics.md)

## Deployment

### Local Development

```bash
docker-compose up -d
uvicorn app.main:app --reload
```

### Production

```bash
# Build image
docker build -t fastapi-enterprise:latest .

# Run with gunicorn
gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000
```

[Full deployment guide →](docker-deployment.md)

## Troubleshooting

**Metrics not showing?**
→ [METRICS_DASHBOARD_FIX.md](../../METRICS_DASHBOARD_FIX.md)

**Database connection failed?**
→ `docker-compose ps` to check services

**Migration conflicts?**
→ `alembic downgrade -1` then rerun

**High latency?**
→ Check Grafana p95/p99 latency dashboard

## External Resources

- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Celery](https://docs.celeryq.dev/)
