# Layered Architecture

## Architecture Overview

Traditional **Layered Architecture** (Spring Boot style) with **Functional Core** for business logic.

## Project Structure

```
app/
├── controller/                  # REST endpoints (@RestController in Spring)
│   ├── pricing_controller.py   # Pricing API endpoints
│   └── health_controller.py    # Health check endpoints
│
├── service/                     # Business logic (@Service in Spring)
│   └── pricing_service.py      # Pricing business orchestration
│
├── repository/                  # Data access (@Repository in Spring)
│   ├── cost_repository.py
│   ├── config_repository.py
│   ├── pricing_repository.py
│   └── metrics_repository.py
│
├── domain/                      # Core domain
│   ├── model/                   # Domain models (entities, value objects)
│   │   ├── enums.py
│   │   ├── cost_models.py
│   │   └── pricing_models.py
│   └── core/                    # Functional Core (pure functions)
│       ├── cost/
│       │   └── calculations.py
│       └── pricing/
│           ├── calculations.py
│           ├── tier_calculations.py
│           ├── discount_calculations.py
│           └── margin_calculations.py
│
├── dto/                         # Data Transfer Objects
│   ├── request/
│   └── response/
│
├── exception/                   # Exception handling
│   ├── domain_exceptions.py
│   └── handler.py
│
├── config/                      # Configuration
│   ├── settings.py
│   └── dependencies.py          # Dependency injection
│
├── infrastructure/              # Cross-cutting infrastructure
│   ├── database.py
│   ├── logging.py
│   └── telemetry.py
│
└── main.py                      # Application entry point
```

## Dependency Flow (Top to Bottom)

```
Controller → Service → Repository → Domain
```

**Rules:**
- Controllers depend on Services and DTOs
- Services depend on Repositories and Domain
- Repositories depend on Domain Models
- Domain has NO external dependencies

## SOLID Principles Adherence

### Single Responsibility Principle (SRP)
- Each layer has one reason to change
- Controllers: HTTP changes
- Services: Business logic changes
- Repositories: Data access changes
- Domain: Business rules changes

### Open/Closed Principle (OCP)
- Services are open for extension via new methods
- Domain core functions are pure and composable

### Liskov Substitution Principle (LSP)
- Repository implementations are interchangeable
- Service implementations can be swapped

### Interface Segregation Principle (ISP)
- Repository interfaces are focused and specific
- Services only depend on what they need

### Dependency Inversion Principle (DIP)
- Services depend on repository abstractions
- Services depend on domain models, not infrastructure
