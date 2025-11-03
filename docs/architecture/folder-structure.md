# Folder Structure Guide

## Overview

This document describes the FastAPI Enterprise project structure, implementing **Hexagonal Architecture** with **Functional Core, Imperative Shell** principles.

## Root Directory Structure

```
fastapi_enterprise/
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Multi-service Docker configuration
├── Dockerfile                   # Application container definition
├── Makefile                     # Build and development commands
├── pyproject.toml               # Python project configuration
├── README.md                    # Project overview and quick start
├── DEVELOPMENT.md               # Development guide
├── README-quickstart.md         # Quick start guide
├── README-LOAD-TESTING.md       # Load testing guide
├── README-observability.md      # Observability guide
├── GOLDEN4_METRICS_COMPLETE.md  # Golden 4 metrics reference
├── METRICS_DASHBOARD_FIX.md     # Dashboard troubleshooting
├── app/                         # Main application code
├── tests/                       # Test suite
├── docs/                        # Comprehensive documentation
├── observability/               # Grafana, Prometheus, OTEL configs
├── scripts/                     # Utility and deployment scripts
├── alembic/                     # Database migrations
└── k6-load-test.js              # Load testing script
```

## Application Structure (`app/`)

Following hexagonal architecture with clear adapter/core separation:

```
app/
├── adapter/                     # ADAPTERS (External interfaces)
│   ├── inbound/                # PRIMARY Adapters (drive the app)
│   │   └── web/                # HTTP/REST interface
│   │       ├── dependencies.py     # Dependency injection
│   │       ├── metrics_middleware.py  # Golden 4 metrics
│   │       ├── pricing.py          # API endpoints/controllers
│   │       └── schemas.py          # HTTP DTOs (request/response)
│   │
│   └── outbound/               # SECONDARY Adapters (driven by app)
│       ├── persistence/        # Data access
│       │   ├── cost_data_adapter.py
│       │   └── pricing_config_adapter.py
│       │
│       └── telemetry/          # Monitoring & metrics
│           ├── metrics_adapter.py
│           └── golden4_metrics_adapter.py
│
├── core/                        # CORE (The Hexagon)
│   ├── domain/                 # DOMAIN (Functional Core)
│   │   ├── cost/              # Cost domain
│   │   │   ├── models.py          # Value objects, entities
│   │   │   └── calculations.py    # Pure business functions
│   │   │
│   │   └── pricing/            # Pricing domain
│   │       ├── models.py          # Value objects, entities
│   │       └── calculations.py    # Pure business functions
│   │
│   ├── application/            # APPLICATION (Use Cases)
│   │   ├── cost/              # Cost use cases
│   │   └── pricing/            # Pricing use cases
│   │       └── use_cases.py       # CalculatePricingUseCase
│   │
│   ├── port/                   # PORTS (Interfaces)
│   │   ├── inbound/           # Input port interfaces (empty for now)
│   │   └── outbound/           # Output port interfaces
│   │       ├── cost_ports.py      # CostDataPort
│   │       ├── pricing_ports.py   # PricingConfigPort, TelemetryPort
│   │       └── metrics_ports.py   # HTTPMetricsPort, SystemMetricsPort
│   │
│   ├── config.py               # Application configuration
│   ├── database.py             # Database connections
│   ├── telemetry.py            # OpenTelemetry setup
│   ├── logging.py              # Structured logging
│   ├── security.py             # Security utilities (REMOVED - not used)
│   ├── exceptions.py           # Application exceptions
│   ├── repository.py           # Base repository interfaces
│   ├── tasks.py                # Celery task definitions
│   ├── celery_app.py           # Celery application
│   └── background_tasks.py     # Background metric collectors
│
└── main.py                      # FastAPI application entry point
```

## Layer Responsibilities

### Adapter Layer (`app/adapter/`)

External interfaces that **translate** between the outside world and the core.

#### Inbound Adapters (`adapter/inbound/`)

**Drive the application** - convert external input into use case calls.

```
adapter/inbound/web/
├── pricing.py              # FastAPI endpoints (REST API)
├── schemas.py              # Pydantic models for HTTP (DTOs)
├── dependencies.py         # FastAPI dependency injection
└── metrics_middleware.py   # Golden 4 metrics middleware
```

**Responsibilities:**

- HTTP request/response handling
- Input validation (Pydantic)
- Error translation to HTTP responses
- Dependency injection setup
- Metrics recording (latency, traffic, errors)

#### Outbound Adapters (`adapter/outbound/`)

**Driven by the application** - implement port interfaces for external services.

```
adapter/outbound/
├── persistence/
│   ├── cost_data_adapter.py        # Implements CostDataPort
│   └── pricing_config_adapter.py   # Implements PricingConfigPort
│
└── telemetry/
    ├── metrics_adapter.py           # Pricing-specific metrics
    └── golden4_metrics_adapter.py   # HTTP metrics (latency, traffic, errors, saturation)
```

**Responsibilities:**

- Database access
- External API calls
- File system operations
- Message queue operations
- Metrics recording

### Core Layer (`app/core/`)

The **hexagon** - business logic independent of external concerns.

#### Domain Layer (`core/domain/`)

**FUNCTIONAL CORE** - Pure business logic with NO side effects.

```
core/domain/
├── cost/
│   ├── models.py           # CostBreakdown, MaterialCost, ProcessCost
│   └── calculations.py     # calculate_manufacturing_cost() - PURE FUNCTION
│
└── pricing/                # Pricing domain with subdomains
    ├── models.py           # Base pricing models (PricingRequest, PriceBreakdown, etc.)
    ├── calculations.py     # Base calculations (complexity_surcharge, weight_estimation)
    ├── tier/               # Tier subdomain
    │   ├── models.py       # PricingTier, TierPricing
    │   └── calculations.py # calculate_tier_pricing() - PURE FUNCTION
    ├── discount/           # Discount subdomain
    │   └── calculations.py # calculate_volume_discount(), calculate_final_discount()
    └── margin/             # Margin subdomain
        └── calculations.py # calculate_margin() - PURE FUNCTION
```

**Rules:**

- ✅ Pure functions only
- ✅ No I/O operations
- ✅ No database access
- ✅ No HTTP calls
- ✅ No current time access (pass as parameter)
- ✅ No logging
- ✅ Deterministic behavior

#### Application Layer (`core/application/`)

**ORCHESTRATION** - coordinates functional core with imperative shell.

```
core/application/
├── cost/
│   └── __init__.py
└── pricing/
    └── use_cases.py        # CalculatePricingUseCase
```

**Responsibilities:**

- Orchestrate domain logic
- Call adapters via ports
- Transaction management
- Error handling and conversion

#### Port Layer (`core/port/`)

**INTERFACES** - contracts between core and adapters.

```
core/port/
├── inbound/                # Input port interfaces (currently empty)
└── outbound/               # Output port interfaces
    ├── cost_ports.py       # CostDataPort
    ├── pricing_ports.py    # PricingConfigPort, PricingPersistencePort, TelemetryPort
    └── metrics_ports.py    # HTTPMetricsPort, SystemMetricsPort, SLOMetricsPort
```

**Types:**

- **Inbound Ports**: Interfaces for primary adapters (use case interfaces)
- **Outbound Ports**: Interfaces for secondary adapters (repository interfaces, external service interfaces)

#### Infrastructure (`core/`)

Core infrastructure services (not in adapter/ because they're shared):

```
core/
├── config.py              # Settings management (Pydantic)
├── database.py            # PostgreSQL, MongoDB, Redis connections
├── telemetry.py           # OpenTelemetry setup
├── logging.py             # Structured logging (structlog)
├── security.py            # Security utilities (REMOVED - not used)
├── exceptions.py          # Application-level exceptions
├── repository.py          # Base repository interfaces
├── tasks.py               # Celery task definitions
├── celery_app.py          # Celery configuration
└── background_tasks.py    # System metrics collectors
```

## Test Structure (`tests/`)

Tests mirror the application structure:

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── unit/                          # Unit tests (fast, no I/O)
│   ├── domains/                   # Domain logic tests
│   │   ├── test_cost_calculations.py
│   │   └── test_pricing_calculations.py
│   └── modules/
│       └── auth/
├── integration/                   # Integration tests (with databases)
│   ├── test_api_integration.py
│   ├── test_data_factory.py
│   └── test_pricing_api.py
├── api/                           # API endpoint tests
│   └── test_health.py
├── contract/                      # API contract tests
│   ├── README.md
│   ├── schemas.py
│   └── test_api_contracts.py
└── test_pricing_limits.py
```

**Test Categories:**

- **Unit Tests** (`unit/`): Test pure functions directly, no mocks needed
- **Integration Tests** (`integration/`): Test adapters with real databases
- **API Tests** (`api/`): Test HTTP endpoints
- **Contract Tests** (`contract/`): Validate API contracts

## Documentation Structure (`docs/`)

```
docs/
├── README.md                           # Documentation hub
├── architecture/                       # Architecture documentation
│   ├── application-architecture.md    # Overall system design
│   ├── folder-structure.md            # This document
│   ├── hexagonal-architecture.md      # Hexagonal architecture details
│   ├── design-principles.md           # Guiding principles
│   └── database-architecture.md       # Multi-database strategy
├── development/                        # Development guides
│   ├── getting-started.md             # Project setup
│   ├── adding-features.md             # Feature development workflow
│   └── domain-development.md          # Creating new domains
├── operations/                         # Operations documentation
│   ├── celery-workers.md              # Background task management
│   ├── database-migrations.md         # Alembic migrations
│   ├── docker-deployment.md           # Container deployment
│   ├── golden4-metrics.md             # Golden 4 metrics guide
│   └── slo-definitions.md             # SLO targets and definitions
└── features/                           # Feature documentation
    └── pricing-system.md              # Manufacturing pricing system
```

## Observability Structure (`observability/`)

Monitoring, metrics, and alerting configuration:

```
observability/
├── prometheus.yml                      # Prometheus configuration
├── alertmanager.yml                    # Alertmanager configuration
├── pricing_alerts.yml                  # Pricing-specific alerts
├── otel-collector-config.yaml          # OpenTelemetry collector config
├── mongo-init.js                       # MongoDB initialization
├── grafana/
│   ├── dashboards/
│   │   ├── enterprise-metrics-dashboard.json  # Golden 4 metrics
│   │   ├── pricing-dashboard.json            # Pricing-specific
│   │   └── slo-dashboard.json                # SLO tracking
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yml
│       └── datasources/
│           └── datasources.yml
```

## Configuration Files

### Root Configuration

- **`pyproject.toml`**: Python dependencies, tool configuration (pytest, black, ruff, mypy)
- **`Makefile`**: Development commands (format, lint, test, run)
- **`docker-compose.yml`**: PostgreSQL, MongoDB, Redis, Prometheus, Grafana, Jaeger
- **`Dockerfile`**: Production container image
- **`.env.example`**: Environment variables template

### Database Migrations (`alembic/`)

```
alembic/
├── alembic.ini                         # Alembic configuration
├── env.py                              # Migration environment
├── script.py.mako                      # Migration template
└── versions/
    └── 20250928_1614_554483b016d0_initial_migration.py
```

## Scripts Directory (`scripts/`)

Utility scripts:

```
scripts/
├── init-mongo.js                # MongoDB initialization
├── init-postgres.sql            # PostgreSQL initialization
├── pricing_demo.py              # Pricing API demo/testing script
└── quick-start.sh               # Quick start automation
```

## File Naming Conventions

### Python Files

- **Snake case**: `pricing_service.py`, `database_connection.py`
- **Descriptive names**: Files clearly indicate purpose
- **Module initialization**: `__init__.py` in every package

### Test Files

- **Test prefix**: `test_pricing_calculation.py`
- **Mirror structure**: Tests mirror application structure
- **Descriptive names**: Clearly indicate what's being tested

### Documentation Files

- **Kebab case**: `application-architecture.md`, `getting-started.md`
- **Descriptive names**: Clear indication of content
- **Consistent structure**: Similar files follow same pattern

## Import Conventions

### Absolute Imports

Always use absolute imports from app root:

```python
# ✅ Good
from app.core.domain.pricing.calculations import calculate_tier_pricing
from app.adapter.outbound.persistence.cost_data_adapter import CostDataAdapter

# ❌ Bad
from ..calculations import calculate_tier_pricing
from ...adapter.outbound.persistence.cost_data_adapter import CostDataAdapter
```

### Respect Layer Boundaries

```python
# ✅ Domain layer - no external dependencies
from app.core.domain.pricing.models import PricingRequest

# ✅ Application layer - can import from domain
from app.core.domain.pricing.calculations import calculate_tier_pricing

# ✅ Adapters - can import from ports and domain
from app.core.port.outbound.pricing_ports import PricingConfigPort
from app.core.domain.pricing.models import PricingRequest

# ❌ Domain importing from adapter - NEVER DO THIS
from app.adapter.outbound.persistence.pricing_adapter import PricingAdapter
```

## Directory Purpose Summary

| Directory               | Purpose                        | Dependencies        | Side Effects          |
| ----------------------- | ------------------------------ | ------------------- | --------------------- |
| `app/core/domain/`      | Pure business logic            | None                | No                    |
| `app/core/application/` | Use case orchestration         | Domain, Ports       | No                    |
| `app/core/port/`        | Interface definitions          | Domain types        | No                    |
| `app/adapter/inbound/`  | HTTP, CLI interfaces           | Application, Domain | Yes (HTTP I/O)        |
| `app/adapter/outbound/` | Database, external APIs        | Ports, Domain       | Yes (DB, API I/O)     |
| `app/core/` (other)     | Configuration, shared services | Various             | Yes (depends on file) |
| `tests/`                | Test coverage                  | All layers          | Depends on test type  |
| `docs/`                 | Documentation                  | None                | No                    |
| `observability/`        | Monitoring configs             | None                | No                    |

## Key Principles

1. **Dependencies Point Inward**: Domain → Application → Ports → Adapters
2. **Functional Core**: Domain layer has pure functions, no side effects
3. **Imperative Shell**: All I/O happens in adapters
4. **Interface Segregation**: Ports define minimal interfaces
5. **Dependency Inversion**: Core depends on interfaces, not implementations

This structure provides:

- ✅ Clear separation of concerns
- ✅ Testable business logic (no mocks needed for domain)
- ✅ Flexible architecture (easy to swap adapters)
- ✅ Domain-focused design (business logic is explicit)
- ✅ Standard hexagonal architecture pattern
