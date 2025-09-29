# Folder Structure Guide

## Overview

This document provides a comprehensive guide to the FastAPI Enterprise project structure, explaining the purpose of each directory and file, and how they work together to implement hexagonal architecture principles.

## Root Directory Structure

```
fastapi_enterprise/
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── .pre-commit-config.yaml      # Pre-commit hooks configuration
├── .cursorrules                 # Cursor AI assistant rules
├── docker-compose.yml           # Multi-service Docker configuration
├── Dockerfile                   # Application container definition
├── Makefile                     # Build and development commands
├── pyproject.toml               # Python project configuration
├── README.md                    # Project overview and quick start
├── app/                         # Main application code
├── tests/                       # Test suite
├── docs/                        # Comprehensive documentation
├── migrations/                  # Database migration files
├── scripts/                     # Utility and deployment scripts
└── .pytest_cache/               # Pytest cache (auto-generated)
```

## Application Structure (`app/`)

The `app/` directory follows hexagonal architecture principles with clear layer separation:

```
app/
├── __init__.py                  # Application package marker
├── main.py                      # FastAPI application entry point
├── api/                         # Interface Layer (Controllers & Routes)
├── core/                        # Application Layer (Use Cases & Config)
├── domains/                     # Domain Layer (Business Logic)
└── infrastructure/              # Infrastructure Layer (External Adapters)
```

### Interface Layer (`app/api/`)

The interface layer handles HTTP requests and responses, input validation, and error handling.

```
app/api/
├── __init__.py                  # Package initialization
├── dependencies.py              # FastAPI dependency injection setup
├── middleware.py                # HTTP middleware (logging, CORS, etc.)
├── errors.py                    # Global error handlers
└── v1/                          # API version 1
    ├── __init__.py              # Version package initialization
    ├── health.py                # Health check endpoints
    └── pricing.py               # Pricing calculation endpoints
```

**Key Files:**

- **`dependencies.py`**: Configures FastAPI dependency injection for repositories, services, and configuration
- **`middleware.py`**: Request/response middleware for logging, timing, CORS, and security headers
- **`errors.py`**: Global exception handlers that convert domain exceptions to HTTP responses
- **`v1/`**: Versioned API endpoints following REST conventions

### Application Layer (`app/core/`)

The application layer orchestrates use cases, manages configuration, and handles cross-cutting concerns.

```
app/core/
├── __init__.py                  # Package initialization
├── exceptions.py                # Application-level exceptions
├── config/                      # Configuration management
│   ├── __init__.py              # Config package initialization
│   ├── settings.py              # Pydantic settings and environment management
│   └── database.py              # Database connection configuration
└── security/                    # Authentication and authorization
    ├── __init__.py              # Security package initialization
    ├── auth.py                  # JWT token handling and validation
    └── permissions.py           # Role-based access control
```

**Key Files:**

- **`config/settings.py`**: Centralized configuration using Pydantic BaseSettings
- **`config/database.py`**: Database connection pooling and session management
- **`security/auth.py`**: JWT authentication, token generation and validation
- **`security/permissions.py`**: Authorization decorators and permission checking
- **`exceptions.py`**: Application-specific exceptions that don't belong to domains

### Domain Layer (`app/domains/`)

The domain layer contains pure business logic, free from external dependencies.

```
app/domains/
├── __init__.py                  # Package initialization
├── shared/                      # Shared domain concepts
│   ├── __init__.py              # Shared package initialization
│   ├── base.py                  # Base domain classes and interfaces
│   └── value_objects.py         # Common value objects (Money, Dimensions, etc.)
├── pricing/                     # Pricing domain
│   ├── __init__.py              # Pricing package initialization
│   ├── models.py                # Domain entities and value objects
│   ├── services.py              # Domain services and business logic
│   ├── repositories.py          # Repository interfaces (ports)
│   └── exceptions.py            # Domain-specific exceptions
└── cost/                        # Cost calculation domain
    ├── __init__.py              # Cost package initialization
    ├── models.py                # Cost-related domain models
    ├── services.py              # Cost calculation business logic
    ├── repositories.py          # Cost repository interfaces
    └── exceptions.py            # Cost-specific exceptions
```

**Domain Structure Pattern:**

Each domain follows a consistent structure:

- **`models.py`**: Domain entities, value objects, and aggregates
- **`services.py`**: Stateless domain services that implement business rules
- **`repositories.py`**: Abstract repository interfaces (ports in hexagonal architecture)
- **`exceptions.py`**: Domain-specific exceptions and error conditions

### Infrastructure Layer (`app/infrastructure/`)

The infrastructure layer implements external adapters and integrations.

```
app/infrastructure/
├── __init__.py                  # Package initialization
├── database/                    # Database adapters and implementations
│   ├── __init__.py              # Database package initialization
│   ├── postgres/                # PostgreSQL adapter
│   │   ├── __init__.py          # Postgres package initialization
│   │   ├── connection.py        # PostgreSQL connection management
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── repositories/        # Repository implementations
│   │       ├── __init__.py      # Repository package initialization
│   │       ├── pricing.py       # Pricing repository implementation
│   │       └── cost.py          # Cost repository implementation
│   ├── mongodb/                 # MongoDB adapter
│   │   ├── __init__.py          # MongoDB package initialization
│   │   ├── connection.py        # MongoDB connection management
│   │   ├── models.py            # Beanie ODM models
│   │   └── repositories/        # MongoDB repository implementations
│   │       ├── __init__.py      # Repository package initialization
│   │       └── analytics.py     # Analytics repository implementation
│   └── redis/                   # Redis adapter
│       ├── __init__.py          # Redis package initialization
│       ├── connection.py        # Redis connection management
│       └── cache.py             # Caching service implementation
├── external/                    # External service adapters
│   ├── __init__.py              # External package initialization
│   ├── material_api.py          # Material data service adapter
│   └── shipping_api.py          # Shipping calculation service adapter
└── tasks/                       # Background task implementations
    ├── __init__.py              # Tasks package initialization
    ├── celery_app.py            # Celery configuration and setup
    ├── pricing_tasks.py         # Pricing-related background tasks
    └── notification_tasks.py    # Notification background tasks
```

**Infrastructure Patterns:**

- **Database Adapters**: Each database technology has its own adapter with connection management
- **Repository Implementations**: Concrete implementations of domain repository interfaces
- **External Service Adapters**: HTTP clients and integrations with external APIs
- **Background Tasks**: Celery task definitions for asynchronous processing

## Test Structure (`tests/`)

The test suite mirrors the application structure with additional test-specific organization:

```
tests/
├── __init__.py                  # Test package initialization
├── conftest.py                  # Pytest configuration and fixtures
├── unit/                        # Unit tests (fast, isolated)
│   ├── __init__.py              # Unit test package initialization
│   ├── domains/                 # Domain logic tests
│   │   ├── __init__.py          # Domain test package initialization
│   │   ├── test_pricing/        # Pricing domain tests
│   │   │   ├── __init__.py      # Pricing test package initialization
│   │   │   ├── test_models.py   # Pricing model tests
│   │   │   └── test_services.py # Pricing service tests
│   │   └── test_cost/           # Cost domain tests
│   │       ├── __init__.py      # Cost test package initialization
│   │       ├── test_models.py   # Cost model tests
│   │       └── test_services.py # Cost service tests
│   └── core/                    # Core application tests
│       ├── __init__.py          # Core test package initialization
│       ├── test_config.py       # Configuration tests
│       └── test_security.py     # Security component tests
├── integration/                 # Integration tests (database, external APIs)
│   ├── __init__.py              # Integration test package initialization
│   ├── test_database.py         # Database integration tests
│   ├── test_repositories.py     # Repository implementation tests
│   └── test_external_apis.py    # External API integration tests
├── api/                         # API endpoint tests
│   ├── __init__.py              # API test package initialization
│   ├── test_health.py           # Health endpoint tests
│   └── test_pricing.py          # Pricing endpoint tests
└── contract/                    # Contract tests using JSON Schema
    ├── __init__.py              # Contract test package initialization
    ├── schemas.py               # JSON Schema definitions
    ├── test_api_contracts.py    # API contract validation tests
    └── README.md                # Contract testing documentation
```

**Test Categories:**

- **Unit Tests**: Fast, isolated tests for business logic and utilities
- **Integration Tests**: Tests that involve databases and external services
- **API Tests**: HTTP endpoint testing with real request/response cycles
- **Contract Tests**: JSON Schema validation for API contracts

## Documentation Structure (`docs/`)

Comprehensive documentation organized by concern:

```
docs/
├── README.md                    # Documentation hub and navigation
├── architecture/                # Architecture documentation
│   ├── application-architecture.md  # Overall system design
│   ├── folder-structure.md      # This document
│   ├── design-principles.md     # Guiding principles and patterns
│   └── database-architecture.md # Multi-database strategy
├── development/                 # Development guides
│   ├── getting-started.md       # Project setup and first steps
│   ├── adding-features.md       # Feature development workflow
│   ├── domain-development.md    # Creating new business domains
│   ├── api-development.md       # Building and testing APIs
│   └── testing.md               # Comprehensive testing strategy
├── operations/                  # Operations and deployment
│   ├── database-migrations.md   # Alembic migration management
│   ├── celery-workers.md        # Background task management
│   ├── docker-deployment.md     # Containerization and deployment
│   ├── environment-config.md    # Settings and environment management
│   └── monitoring-logging.md    # Observability and debugging
└── features/                    # Feature-specific documentation
    ├── pricing-system.md        # Manufacturing pricing calculations
    ├── cost-management.md       # Cost calculation and optimization
    └── health-checks.md         # System monitoring and diagnostics
```

## Configuration Files

### Root Configuration Files

- **`.env.example`**: Template for environment variables with documentation
- **`pyproject.toml`**: Python project metadata, dependencies, and tool configuration
- **`Makefile`**: Development commands and build automation
- **`docker-compose.yml`**: Multi-service container orchestration
- **`Dockerfile`**: Production container definition
- **`.pre-commit-config.yaml`**: Code quality checks and formatting
- **`.cursorrules`**: AI assistant guidelines for the project

### Database Migrations (`migrations/`)

```
migrations/
├── alembic.ini                  # Alembic configuration
├── env.py                       # Migration environment setup
├── script.py.mako               # Migration script template
└── versions/                    # Migration version files
    ├── 001_initial_schema.py    # Initial database schema
    ├── 002_add_pricing_tables.py # Pricing feature tables
    └── 003_add_cost_tables.py   # Cost calculation tables
```

## Scripts Directory (`scripts/`)

Utility scripts for development and deployment:

```
scripts/
├── setup_dev.sh                # Development environment setup
├── run_tests.sh                # Comprehensive test runner
├── deploy.sh                    # Deployment automation
├── backup_db.sh                # Database backup utility
└── check_health.sh             # Health check script
```

## File Naming Conventions

### Python Files

- **Snake case**: `pricing_service.py`, `database_connection.py`
- **Descriptive names**: Files should clearly indicate their purpose
- **Module initialization**: `__init__.py` in every package directory

### Test Files

- **Test prefix**: `test_` prefix for all test files
- **Mirror structure**: Test files mirror the application structure
- **Descriptive names**: `test_pricing_calculation.py`, `test_database_connection.py`

### Documentation Files

- **Kebab case**: `application-architecture.md`, `getting-started.md`
- **Descriptive names**: Files should clearly indicate their content
- **Consistent structure**: Similar files follow the same organization pattern

## Import Conventions

### Absolute Imports

Always use absolute imports from the app root:

```python
# Good
from app.domains.pricing.models import PricingCalculation
from app.infrastructure.database.postgres.repositories.pricing import PostgresPricingRepository

# Bad
from ..models import PricingCalculation
from ...infrastructure.database.postgres.repositories.pricing import PostgresPricingRepository
```

### Layer Dependencies

Respect architectural boundaries in imports:

```python
# Domain layer - no external dependencies
from app.domains.shared.value_objects import Money

# Application layer - can import from domain
from app.domains.pricing.services import PricingService

# Infrastructure layer - can import from domain and application
from app.domains.pricing.repositories import PricingRepository
from app.core.config.settings import Settings

# Interface layer - can import from all layers
from app.domains.pricing.models import PricingRequest
from app.infrastructure.database.postgres.repositories.pricing import PostgresPricingRepository
```

## Directory Purpose Summary

| Directory | Purpose | Dependencies | Examples |
|-----------|---------|--------------|----------|
| `app/api/` | HTTP interface, routing, validation | FastAPI, Pydantic | Controllers, middleware |
| `app/core/` | Application orchestration, config | Domain layer | Settings, use cases |
| `app/domains/` | Business logic, rules | None (pure Python) | Models, services |
| `app/infrastructure/` | External integrations | Database drivers, HTTP clients | Repositories, adapters |
| `tests/` | Test coverage | Pytest, test fixtures | Unit, integration tests |
| `docs/` | Documentation | Markdown | Architecture, guides |
| `migrations/` | Database schema evolution | Alembic | Schema changes |
| `scripts/` | Automation and utilities | Shell scripts | Setup, deployment |

This folder structure provides clear separation of concerns, makes the codebase navigable, and supports the hexagonal architecture pattern while maintaining consistency and predictability across the entire project.
