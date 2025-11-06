# Architecture Documentation

This application implements **Layered Architecture** (Spring Boot style) with **Functional Core** for business logic.

## Core Concepts

### Layered Architecture

Traditional layered architecture with clear separation of concerns:
- **Controller** = HTTP/REST endpoints (analogous to Spring `@RestController`)
- **Service** = Business logic orchestration (analogous to Spring `@Service`)
- **Repository** = Data access layer (analogous to Spring `@Repository`)
- **Domain** = Core business domain (models + pure functions)

[Learn more →](https://spring.io/guides)

### Functional Core, Imperative Shell

- **Functional Core** (`domain/core/`) = Pure functions, no side effects
- **Imperative Shell** (Controllers, Services, Repositories) = All I/O operations

[Learn more →](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell)

## Documentation

1. **[Layered Architecture](layered-architecture.md)** - Complete architecture guide, SOLID principles, patterns

2. **[Folder Structure](folder-structure.md)** - Directory layout, file naming, import conventions

3. **[Design Principles](design-principles.md)** - SOLID, DDD, functional programming

4. **[Database Architecture](database-architecture.md)** - PostgreSQL, MongoDB, Redis strategy

## Quick Reference

```
app/
├── controller/        # HTTP endpoints (@RestController)
│   ├── pricing_controller.py
│   └── health_controller.py
├── service/           # Business logic (@Service)
│   └── pricing_service.py
├── repository/        # Data access (@Repository)
│   ├── cost_repository.py
│   ├── config_repository.py
│   ├── pricing_repository.py
│   └── metrics_repository.py
├── domain/            # Core domain
│   ├── model/         # Entities, value objects
│   └── core/          # Pure business logic (functional core)
├── dto/               # Request/response schemas
│   ├── request/
│   └── response/
├── exception/         # Exception handling
├── config/            # Configuration & DI
└── infrastructure/    # Cross-cutting concerns
```

**Dependency Rule**: Dependencies flow downward → `Controller → Service → Repository → Domain`
