# Documentation

## Quick Links

- **[Architecture](architecture/README.md)** - System design, hexagonal architecture, folder structure
- **[Development](development/README.md)** - Getting started, adding features, testing
- **[Operations](operations/README.md)** - Deployment, monitoring, troubleshooting

## Architecture

Learn about the hexagonal architecture pattern and how this application is structured:

- [Hexagonal Architecture](architecture/hexagonal-architecture.md) - Ports & adapters pattern
- [Folder Structure](architecture/folder-structure.md) - Directory layout and conventions
- [Design Principles](architecture/design-principles.md) - Functional core, imperative shell
- [Database Architecture](architecture/database-architecture.md) - Multi-database strategy

## Development

Guides for building features and working with the codebase:

- [Getting Started](development/getting-started.md) - Setup and first steps
- [Adding Features](development/adding-features.md) - Feature development workflow
- [Domain Development](development/domain-development.md) - Creating business domains

## Operations

Production deployment and monitoring:

- [Docker Deployment](operations/docker-deployment.md) - Container setup
- [Database Migrations](operations/database-migrations.md) - Schema evolution
- [Golden 4 Metrics](operations/golden4-metrics.md) - Latency, traffic, errors, saturation
- [SLO Definitions](operations/slo-definitions.md) - Service level objectives
- [Celery Workers](operations/celery-workers.md) - Background task processing

## Features

Feature-specific documentation:

- [Pricing System](features/pricing-system.md) - Manufacturing pricing calculations

## External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
