# Architecture Documentation

This application implements **[Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)** (Ports & Adapters) with **Functional Core, Imperative Shell** principles.

## Core Concepts

### Hexagonal Architecture

Business logic is isolated from external concerns using:
- **Ports** = Interfaces
- **Adapters** = Implementations
- **Core** = Business logic (no I/O, no frameworks)

[Learn more →](https://netflixtechblog.com/ready-for-changes-with-hexagonal-architecture-b315ec967749)

### Functional Core, Imperative Shell

- **Functional Core** (`core/domain/`) = Pure functions, no side effects
- **Imperative Shell** (`adapter/`) = All I/O operations

[Learn more →](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell)

## Documentation

1. **[Hexagonal Architecture](hexagonal-architecture.md)** - Architecture overview, dependency flow, layer responsibilities

2. **[Folder Structure](folder-structure.md)** - Directory layout, file naming, import conventions

3. **[Design Principles](design-principles.md)** - SOLID, DDD, functional programming

4. **[Database Architecture](database-architecture.md)** - PostgreSQL, MongoDB, Redis strategy

## Quick Reference

```
app/
├── adapter/           # I/O (HTTP, database, external APIs)
│   ├── inbound/      # HTTP API, CLI
│   └── outbound/     # Database, external services
├── core/
│   ├── domain/       # Pure business logic (no I/O)
│   ├── application/  # Use cases (orchestration)
│   └── port/         # Interfaces
└── main.py
```

**Dependency Rule**: Dependencies point inward → domain
