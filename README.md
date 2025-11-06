# FastAPI Enterprise - Manufacturing Pricing API

> Production-ready FastAPI application implementing [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) with pricing calculations for custom manufactured parts.

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd fastapi_enterprise
cp .env.example .env

# 2. One command to rule them all 🚀
make full-setup

# 3. Start the app
make start-dev

# Open http://localhost:8000/docs
```

**What `make full-setup` does:**

- Starts all services (PostgreSQL, MongoDB, Redis, Prometheus, Grafana, Jaeger)
- Installs dependencies with uv
- Runs database migrations
- Initializes MongoDB indexes
- Imports Grafana dashboards

**Or do it step by step:**

```bash
make docker-up      # Start services
make install        # Install dependencies
make db-upgrade     # Run migrations
make start-dev      # Start app
```

## Development

### Running Tests

```bash
make test              # All tests
make test-unit         # Unit tests only (fast)
make test-integration  # Integration tests
make test-coverage     # With coverage report
```

### Code Quality

```bash
make format      # Format with black/isort
make lint        # Check with ruff
make type-check  # Run mypy
make check-all   # Run all checks
```

### Database Migrations

```bash
make db-revision   # Create migration (prompts for message)
make db-upgrade    # Apply migrations
make db-downgrade  # Rollback one migration
```

## Architecture

This project uses **Clean Architecture** (Uncle Bob's pattern) with **Functional Core, Imperative Shell**:

```
app/
├── features/
│   ├── pricing/
│   │   ├── entities/             # Pure business logic (innermost)
│   │   ├── use_cases/            # Application business rules
│   │   ├── interface_adapters/   # Controllers, gateways, presenters
│   │   └── frameworks/           # FastAPI routes (outermost)
│   └── cost/
│       ├── entities/
│       └── use_cases/
├── shared/                       # Shared kernel
└── frameworks/                   # Cross-cutting infrastructure
```

**Key Principles:**

- **Entities** = Pure functions, no side effects, no I/O (innermost)
- **Use Cases** = Orchestrate entities with gateways
- **Interface Adapters** = Convert data between layers
- **Frameworks** = External interfaces (HTTP, database) (outermost)

[Full architecture docs →](docs/architecture/README.md)

## Project Structure

```
fastapi_enterprise/
├── app/                  # Application code
├── tests/               # Unit, integration, API tests
├── docs/                # Documentation
├── observability/       # Prometheus, Grafana configs
├── alembic/            # Database migrations
└── docker-compose.yml   # Local development stack
```

## API Examples

### Calculate Pricing

```bash
curl -X POST http://localhost:8000/api/v1/pricing \
  -H "Content-Type: application/json" \
  -d '{
    "material": "aluminum",
    "process": "cnc",
    "quantity": 100,
    "dimensions": {"length": 100, "width": 50, "height": 25},
    "geometric_complexity_score": 2.5
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Monitoring

- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics (Prometheus format)
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

[Observability guide →](docs/operations/README.md)

## Key Features

- ✅ **Clean Architecture** - Four layers with dependency rule
- ✅ **Functional Core** - Pure business logic, easily testable
- ✅ **Multi-Database** - PostgreSQL, MongoDB, Redis
- ✅ **OpenTelemetry** - Distributed tracing and metrics
- ✅ **Golden 4 Metrics** - Latency, Traffic, Errors, Saturation
- ✅ **SLO Monitoring** - 99.9% availability, p95 < 500ms
- ✅ **Background Tasks** - Celery for async processing
- ✅ **Type Safety** - Full type hints with mypy
- ✅ **Production Ready** - Docker, migrations, monitoring

## Adding Features

1. **Create entities** in `app/features/your_feature/entities/`

   - Pure functions (no I/O)
   - Domain models (immutable)

2. **Create use cases** in `app/features/your_feature/use_cases/`

   - Use case orchestration
   - Input/Output DTOs
   - Gateway interfaces

3. **Create interface adapters** in `app/features/your_feature/interface_adapters/`

   - Gateway implementations
   - Controllers and presenters

4. **Create frameworks** in `app/features/your_feature/frameworks/web/`

   - FastAPI routes
   - HTTP schemas
   - Dependencies

[Feature development guide →](docs/development/README.md)

## Environment Variables

```bash
# Database
POSTGRES_URL=postgresql+asyncpg://user:pass@localhost/db
MONGODB_URL=mongodb://localhost:27017/db
REDIS_URL=redis://localhost:6379

# Application
APP_NAME=fastapi-enterprise
DEBUG=false
SECRET_KEY=your-secret-key

# Observability
OTLP_ENDPOINT=http://localhost:4317
ENABLE_PROMETHEUS=true
```

See [.env.example](.env.example) for all options.

## Common Tasks

```bash
make full-setup          # Complete environment setup
make pricing-demo        # Run pricing demo
make load-test           # Run k6 load test
make db-reset            # Reset database (WARNING: deletes data)
make clean               # Clean cache files
make help                # Show all available commands
```

## Stack

- **Package Manager**: [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Databases**: PostgreSQL, MongoDB, Redis
- **ORM**: SQLAlchemy (async), Beanie (MongoDB)
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio
- **Observability**: OpenTelemetry, Prometheus, Grafana
- **Background Tasks**: Celery
- **Migrations**: Alembic

## Documentation

- [Architecture](docs/architecture/README.md) - Clean Architecture, design principles
- [Development](docs/development/README.md) - Feature development, testing, best practices
- [Operations](docs/operations/README.md) - Deployment, monitoring, troubleshooting
- [API Reference](http://localhost:8000/docs) - Interactive OpenAPI docs

## Troubleshooting

**Metrics not showing in Grafana?**
→ Check [METRICS_DASHBOARD_FIX.md](METRICS_DASHBOARD_FIX.md)

**Database connection failed?**
→ Ensure docker-compose services are running: `docker-compose ps`

**Import errors?**
→ Reinstall: `make install`

**Tests failing?**
→ Reset database: `make db-reset`

## Contributing

1. Create feature branch
2. Write tests (domain tests don't need mocks!)
3. Ensure `make lint` and `make test` pass
4. Update docs if needed
5. Submit PR

## License

[Your License]
