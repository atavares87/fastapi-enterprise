# FastAPI Enterprise Application - Overview

## Project Overview

Enterprise-grade FastAPI application implementing **Layered Architecture** (Spring Boot style) with **Functional Core** for business logic. Manufacturing pricing calculations and cost management for custom parts.

## 🚨 CRITICAL: Standard Practices First

**ALWAYS follow standard, documented patterns.** If you need to deviate from:
- Framework conventions (FastAPI, SQLAlchemy, Pydantic)
- Architectural patterns (Layered Architecture, Spring Boot patterns)
- Python standards (PEP 8, type hints)
- Industry best practices (REST API, security)

**Stop and check with the project owner first. Do not reinvent the wheel.**

## Stack

- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Databases**: PostgreSQL, MongoDB, Redis
- **ORM**: SQLAlchemy (async), Beanie (MongoDB)
- **Validation**: Pydantic v2
- **Testing**: pytest
- **Observability**: OpenTelemetry, Prometheus, Grafana
- **Background**: Celery
- **Migrations**: Alembic

## Documentation

For detailed information:
- [Layered Architecture](docs/architecture/layered-architecture.md) - Complete architecture guide
- [Folder Structure](docs/architecture/folder-structure.md) - Detailed file organization
- [Development Guide](docs/development/README.md) - Feature development workflow
- [Operations Guide](docs/operations/README.md) - Deployment & monitoring
