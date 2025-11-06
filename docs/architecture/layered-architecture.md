# Layered Architecture

This application implements a **traditional Layered Architecture** inspired by **Spring Boot** while maintaining a **Functional Core** for business logic.

## Overview

The layered architecture organizes code by technical concerns (horizontal layers) rather than features (vertical slices). Each layer has clear responsibilities and dependencies flow downward.

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│  Controller Layer (REST Endpoints)              │  ← HTTP/API Layer
├─────────────────────────────────────────────────┤
│  Service Layer (Business Logic Orchestration)   │  ← Business Logic
├─────────────────────────────────────────────────┤
│  Repository Layer (Data Access)                 │  ← Data Access
├─────────────────────────────────────────────────┤
│  Domain Layer (Entities & Pure Functions)       │  ← Core Domain
└─────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. Controller Layer (`app/controller/`)

**Responsibility**: Handle HTTP requests and responses

**Analogous to**: Spring `@RestController` classes

**Key Points**:
- Route HTTP requests to service methods
- Validate request parameters (basic validation via Pydantic)
- Convert HTTP requests to DTOs
- Convert service responses to HTTP responses
- Handle HTTP-specific concerns (status codes, headers)
- **NO business logic**

**Example**:
```python
@router.post("/calculate", response_model=PricingResponseDTO)
async def calculate_pricing(
    request: PricingRequestDTO,
    pricing_service: PricingService = Depends(get_pricing_service)
) -> PricingResponseDTO:
    return await pricing_service.calculate_pricing(request)
```

### 2. Service Layer (`app/service/`)

**Responsibility**: Business logic orchestration

**Analogous to**: Spring `@Service` classes

**Key Points**:
- Orchestrate business workflows
- Coordinate between repositories
- Call domain core functions for business logic
- Handle business rules and validation
- Transaction management
- **NO HTTP concerns**
- **NO database implementation details**

**Example**:
```python
class PricingService:
    def __init__(
        self,
        cost_repository: CostRepository,
        config_repository: ConfigRepository,
        pricing_repository: PricingRepository,
        metrics_repository: MetricsRepository,
    ):
        self.cost_repository = cost_repository
        self.config_repository = config_repository
        self.pricing_repository = pricing_repository
        self.metrics_repository = metrics_repository

    async def calculate_pricing(self, request: PricingRequestDTO):
        # 1. Fetch data from repositories
        material_costs = await self.cost_repository.get_material_costs()

        # 2. Call domain core (pure functions)
        tier_pricing = calculate_tier_pricing(...)

        # 3. Persist results
        await self.pricing_repository.save(tier_pricing)

        return response_dto
```

### 3. Repository Layer (`app/repository/`)

**Responsibility**: Data access and persistence

**Analogous to**: Spring `@Repository` classes

**Key Points**:
- Abstract database access
- Execute database queries
- Map database results to domain models
- Handle database transactions
- Cache management
- **NO business logic**

**Example**:
```python
class CostRepository:
    async def get_material_costs(self) -> dict[Material, MaterialCost]:
        # Database access implementation
        return await self._fetch_from_database()
```

### 4. Domain Layer (`app/domain/`)

**Responsibility**: Core business domain

**Analogous to**: Spring domain models + business logic

**Two sub-layers**:

#### Domain Models (`app/domain/model/`)
- Entity classes
- Value objects
- Enums
- Domain events
- **NO I/O operations**

#### Functional Core (`app/domain/core/`)
- **Pure functions** (no side effects)
- Core business calculations
- Business rules
- **Completely testable without mocks**
- **NO I/O, NO database, NO HTTP, NO logging**
- **NO mutable state**

**Example**:
```python
def calculate_complexity_surcharge(
    cost_plus_margin: Decimal,
    complexity_score: float,
    config: PricingConfiguration,
) -> Decimal:
    """Pure function - same input always produces same output"""
    if complexity_score >= config.complexity_surcharge_threshold:
        return cost_plus_margin * Decimal(str(config.complexity_surcharge_rate))
    return Decimal("0")
```

## Dependency Flow

```
Controller → Service → Repository → Domain
     ↓          ↓           ↓
    DTO     Domain/Core   Domain/Model
```

**Rules**:
1. Controllers depend on Services and DTOs
2. Services depend on Repositories and Domain (core + models)
3. Repositories depend on Domain Models
4. Domain has NO dependencies (especially Functional Core)
5. DTOs are independent (only used by Controllers and Services)

## Directory Structure

```
app/
├── controller/           # REST endpoints (analogous to @RestController)
│   ├── pricing_controller.py
│   └── health_controller.py
│
├── service/              # Business logic (analogous to @Service)
│   └── pricing_service.py
│
├── repository/           # Data access (analogous to @Repository)
│   ├── cost_repository.py
│   ├── config_repository.py
│   ├── pricing_repository.py
│   └── metrics_repository.py
│
├── domain/               # Core domain
│   ├── model/            # Domain models
│   │   ├── enums.py
│   │   ├── cost_models.py
│   │   └── pricing_models.py
│   │
│   └── core/             # Pure functions (functional core)
│       ├── cost/
│       │   └── calculations.py
│       └── pricing/
│           ├── calculations.py
│           ├── tier_calculations.py
│           ├── discount_calculations.py
│           └── margin_calculations.py
│
├── dto/                  # Data Transfer Objects
│   ├── request/
│   │   └── pricing_request.py
│   └── response/
│       └── pricing_response.py
│
├── exception/            # Exception handling
│   ├── domain_exceptions.py
│   └── handler.py
│
├── config/               # Configuration
│   ├── settings.py
│   └── dependencies.py   # Dependency injection
│
├── infrastructure/       # Cross-cutting infrastructure
│   ├── database.py
│   ├── logging.py
│   ├── telemetry.py
│   └── celery_app.py
│
└── main.py               # Application entry point
```

## SOLID Principles

### Single Responsibility Principle (SRP)
- Each layer has one reason to change
- Controllers: HTTP changes
- Services: Business logic changes
- Repositories: Data access changes
- Domain: Business rules changes

### Open/Closed Principle (OCP)
- Services are open for extension via new methods
- Domain core functions are pure and composable
- Repository interfaces can have multiple implementations

### Liskov Substitution Principle (LSP)
- Repository implementations are interchangeable
- Service implementations can be swapped

### Interface Segregation Principle (ISP)
- Repository interfaces are focused and specific
- Services only depend on what they need

### Dependency Inversion Principle (DIP)
- High-level services depend on repository abstractions
- Services depend on domain models, not infrastructure

## Dependency Injection

Using `functools.lru_cache` for singleton pattern (analogous to Spring `@Bean`):

```python
# app/config/dependencies.py
from functools import lru_cache

@lru_cache()
def get_cost_repository() -> CostRepository:
    return CostRepository()

@lru_cache()
def get_pricing_service() -> PricingService:
    return PricingService(
        cost_repository=get_cost_repository(),
        config_repository=get_config_repository(),
        pricing_repository=get_pricing_repository(),
        metrics_repository=get_metrics_repository(),
    )
```

## Testing Strategy

### Domain Core Tests
- Test pure functions directly
- **NO mocks needed**
- Fast and simple

```python
def test_calculate_margin():
    result = calculate_margin(Decimal("100"), config)
    assert result == Decimal("45.00")
```

### Service Tests
- Mock repositories
- Test business orchestration
- Use real domain core functions

```python
async def test_pricing_service():
    mock_repo = Mock(spec=CostRepository)
    service = PricingService(mock_repo, ...)
    result = await service.calculate_pricing(request_dto)
    assert result.pricing_tiers.standard.final_price > 0
```

### Controller Tests
- Mock services
- Test HTTP concerns only

```python
async def test_pricing_endpoint(client):
    response = client.post("/api/v1/pricing/calculate", json=request_data)
    assert response.status_code == 200
```

## Benefits

1. **Familiar**: Spring Boot developers immediately understand the structure
2. **Simple**: Straightforward dependency flow (top to bottom)
3. **Testable**: Each layer can be tested independently
4. **Maintainable**: Clear separation of concerns
5. **SOLID**: Adheres to all SOLID principles
6. **Functional Core**: Maintains pure business logic (best of both worlds)
7. **Standard**: Industry-standard pattern, well-documented
8. **Scalable**: Easy to add new features following the same pattern

## Comparison with Clean Architecture

| Aspect | Clean Architecture | Layered Architecture |
|--------|-------------------|---------------------|
| Organization | Feature-first, vertical | Horizontal technical layers |
| Dependency Flow | Inward toward entities | Downward toward domain |
| Testing | Ports & Adapters, more complex | Layer-by-layer, simpler |
| Learning Curve | Higher (hexagonal concepts) | Lower (familiar to Spring devs) |
| Industry Adoption | Modern, microservices | Traditional, enterprise Java |

## Migration from Clean Architecture

The migration maintained the functional core but reorganized around technical layers:

**Before (Clean Architecture)**:
```
features/
└── pricing/
    ├── entities/              (functional core)
    ├── use_cases/             (orchestration)
    ├── interface_adapters/    (gateways)
    └── frameworks/            (web routes)
```

**After (Layered Architecture)**:
```
controller/    (was frameworks/web)
service/       (was use_cases)
repository/    (was interface_adapters/gateways)
domain/
├── model/     (was entities/models)
└── core/      (was entities/calculations)
```

## References

- [Spring Boot Best Practices](https://spring.io/guides)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)
- [Functional Core, Imperative Shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell)
