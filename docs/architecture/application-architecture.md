# Application Architecture

## Overview

The FastAPI Enterprise application follows **Layered Architecture** (Spring Boot style) principles, promoting separation of concerns, testability, and maintainability. This architectural pattern organizes code by technical layers rather than features, with clear dependency flow from top to bottom.

## Architecture Principles

### 1. Layered Architecture (Spring Boot Style)

```
┌─────────────────────────────────────────────────────────────────┐
│                    HTTP Requests / Responses                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│          Controller Layer (@RestController)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Pricing    │  │    Health    │  │    Other     │          │
│  │  Controller  │  │  Controller  │  │ Controllers  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP → DTO
┌─────────────────────────────────────────────────────────────────┐
│             Service Layer (@Service)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Pricing    │  │     Cost     │  │    Other     │          │
│  │   Service    │  │   Service    │  │  Services    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Orchestration
┌─────────────────────────────────────────────────────────────────┐
│           Repository Layer (@Repository)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     Cost     │  │    Config    │  │   Metrics    │          │
│  │  Repository  │  │  Repository  │  │  Repository  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Data Access
┌─────────────────────────────────────────────────────────────────┐
│                   Domain Layer                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Domain Models                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │ Cost Models  │  │Pricing Models│  │    Enums     │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │            Functional Core (Pure Functions)             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │     Cost     │  │    Pricing   │  │   Discount   │  │    │
│  │  │ Calculations │  │ Calculations │  │ Calculations │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 2. SOLID Principles

**Single Responsibility**:
- Each layer has one reason to change
- Controllers: HTTP changes
- Services: Business logic changes
- Repositories: Data access changes
- Domain: Business rules changes

**Open/Closed**:
- Services are open for extension via new methods
- Domain core functions are pure and composable

**Liskov Substitution**:
- Repository implementations are interchangeable
- Service implementations can be swapped

**Interface Segregation**:
- Repository interfaces are focused and specific
- Services only depend on what they need

**Dependency Inversion**:
- Services depend on repository abstractions
- Services depend on domain models, not infrastructure

### 3. Functional Core, Imperative Shell

**Functional Core** (`domain/core/`):
- Pure functions (no side effects)
- All business calculations
- Completely testable without mocks
- NO I/O, NO database, NO HTTP, NO logging

**Imperative Shell** (Everything else):
- Controllers: HTTP I/O
- Services: Orchestration
- Repositories: Database I/O
- All side effects happen here

## Directory Structure Deep Dive

### Complete Application Structure

```
app/
├── __init__.py                    # Application package
├── main.py                        # FastAPI application entry point
│
├── controller/                    # Controller Layer (HTTP endpoints)
│   ├── __init__.py
│   ├── pricing_controller.py      # Pricing REST endpoints
│   └── health_controller.py       # Health check endpoints
│
├── service/                       # Service Layer (Business orchestration)
│   ├── __init__.py
│   └── pricing_service.py         # Pricing business logic
│
├── repository/                    # Repository Layer (Data access)
│   ├── __init__.py
│   ├── cost_repository.py         # Cost data access
│   ├── config_repository.py       # Configuration data access
│   ├── pricing_repository.py      # Pricing persistence
│   └── metrics_repository.py      # Metrics and telemetry
│
├── domain/                        # Domain Layer (Core business)
│   ├── __init__.py
│   ├── model/                     # Domain models
│   │   ├── __init__.py
│   │   ├── enums.py               # Domain enumerations
│   │   ├── cost_models.py         # Cost entities
│   │   └── pricing_models.py      # Pricing entities
│   │
│   └── core/                      # Functional Core (pure functions)
│       ├── __init__.py
│       ├── cost/                  # Cost calculations
│       │   ├── __init__.py
│       │   └── calculations.py    # Pure cost functions
│       │
│       └── pricing/               # Pricing calculations
│           ├── __init__.py
│           ├── calculations.py           # Base pricing functions
│           ├── tier_calculations.py      # Tier-specific pricing
│           ├── discount_calculations.py  # Discount logic
│           └── margin_calculations.py    # Margin calculations
│
├── dto/                           # Data Transfer Objects
│   ├── __init__.py
│   ├── request/                   # API request schemas
│   │   ├── __init__.py
│   │   └── pricing_request.py
│   │
│   └── response/                  # API response schemas
│       ├── __init__.py
│       └── pricing_response.py
│
├── exception/                     # Exception handling
│   ├── __init__.py
│   ├── domain_exceptions.py       # Domain exceptions
│   └── handler.py                 # Global exception handlers
│
├── config/                        # Configuration
│   ├── __init__.py
│   ├── settings.py                # Application settings (from core/)
│   └── dependencies.py            # Dependency injection
│
├── infrastructure/                # Infrastructure (cross-cutting)
│   ├── __init__.py
│   ├── database.py                # Database connections
│   ├── logging.py                 # Logging setup
│   ├── telemetry.py               # OpenTelemetry
│   └── celery_app.py              # Background tasks
│
└── util/                          # Utilities
    ├── __init__.py
    └── validators.py              # Common validators
```

## Layer Responsibilities

### Controller Layer (`controller/`)

**Purpose**: Handle HTTP requests and responses

**Analogous to**: Spring `@RestController`

**Responsibilities**:
- Route HTTP requests to service methods
- Validate requests (Pydantic handles this)
- Convert DTOs to/from HTTP
- Handle HTTP-specific concerns (status codes, headers)
- Exception handling → HTTP errors

**Example**:
```python
@router.post("/calculate", response_model=PricingResponseDTO)
async def calculate_pricing(
    request: PricingRequestDTO,
    pricing_service: PricingService = Depends(get_pricing_service)
) -> PricingResponseDTO:
    """Delegate to service layer."""
    return await pricing_service.calculate_pricing(request)
```

**Rules**:
- ✅ Thin controllers (< 50 lines per endpoint)
- ✅ Use dependency injection
- ✅ Convert exceptions to HTTP responses
- ❌ NO business logic
- ❌ NO database queries
- ❌ NO complex calculations

### Service Layer (`service/`)

**Purpose**: Business logic orchestration

**Analogous to**: Spring `@Service`

**Responsibilities**:
- Orchestrate business workflows
- Coordinate between repositories
- Call domain core functions for calculations
- Handle business validation
- Transaction boundaries
- Record metrics

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
        tier_configs = await self.config_repository.get_tier_configurations()

        # 2. Call domain core (pure functions)
        cost_breakdown = calculate_manufacturing_cost(...)
        tier_pricing = calculate_tier_pricing(...)

        # 3. Persist results
        await self.pricing_repository.save_pricing_result(...)

        # 4. Record metrics
        await self.metrics_repository.record_pricing_metrics(...)

        return response_dto
```

**Rules**:
- ✅ Constructor injection for dependencies
- ✅ Business logic in domain core
- ✅ Async/await for I/O
- ❌ NO HTTP concerns
- ❌ NO database queries (use repositories)
- ❌ NO Request/Response objects

### Repository Layer (`repository/`)

**Purpose**: Data access and persistence

**Analogous to**: Spring `@Repository`

**Responsibilities**:
- Abstract database access
- Execute queries
- Map database results to domain models
- Handle transactions
- Cache management

**Example**:
```python
class CostRepository:
    async def get_material_costs(self) -> dict[Material, MaterialCost]:
        """Fetch material costs from database."""
        return await self._fetch_from_database()

    async def save_material_cost(self, material: Material, cost: MaterialCost):
        """Save material cost to database."""
        await self._save_to_database(material, cost)
```

**Rules**:
- ✅ Return domain models
- ✅ Async/await for database operations
- ✅ Handle connection pooling
- ❌ NO business logic
- ❌ NO business validation
- ❌ NO calling other services

### Domain Layer (`domain/`)

**Purpose**: Core business domain

**Two sub-layers**:

#### Domain Models (`domain/model/`)
- Entities (dataclasses)
- Value objects
- Enums
- Domain events

```python
@dataclass(frozen=True)
class PricingConfiguration:
    """Immutable pricing configuration."""
    margin_percentage: float
    volume_discount_thresholds: dict[int, float]
    complexity_surcharge_threshold: float
    complexity_surcharge_rate: float
```

#### Functional Core (`domain/core/`)
- Pure functions (no side effects)
- Core business calculations
- Business rules
- Completely testable without mocks

```python
def calculate_margin(
    base_cost: Decimal,
    config: PricingConfiguration
) -> Decimal:
    """Pure function - same input always produces same output."""
    return base_cost * Decimal(str(config.margin_percentage))
```

**Rules**:
- ✅ Immutable dataclasses (`frozen=True`)
- ✅ All inputs as parameters
- ✅ No side effects
- ❌ NO I/O operations
- ❌ NO database calls
- ❌ NO logging
- ❌ NO current time/random

## Dependency Flow

```
Controller → Service → Repository → Domain
     ↓          ↓           ↓
    DTO     Domain/Core   Domain/Model
```

**Rules**:
1. Controllers depend on Services and DTOs
2. Services depend on Repositories and Domain
3. Repositories depend on Domain Models
4. Domain has NO dependencies
5. DTOs are independent

## Design Patterns

### Dependency Injection

Using `functools.lru_cache` for singleton pattern:

```python
# config/dependencies.py
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

### Repository Pattern

Abstract data access:

```python
class CostRepository:
    async def get_material_costs(self) -> dict[Material, MaterialCost]:
        """Interface method - implementation can change."""
        pass
```

### Service Pattern

Business orchestration:

```python
class PricingService:
    async def calculate_pricing(self, request: PricingRequestDTO):
        """Orchestrate the pricing calculation workflow."""
        # Coordinate repositories and domain core
```

## Testing Strategy

### Domain Core Tests
- Test pure functions directly
- NO mocks needed!
- Fast and reliable

```python
def test_calculate_margin():
    result = calculate_margin(Decimal("100"), config)
    assert result == Decimal("45.00")
```

### Service Tests
- Mock repositories
- Use real domain core

```python
async def test_pricing_service():
    mock_repo = Mock(spec=CostRepository)
    service = PricingService(mock_repo, ...)
    result = await service.calculate_pricing(request)
    assert result.final_price > 0
```

### Controller Tests
- Mock services
- Test HTTP concerns

```python
async def test_pricing_endpoint(client):
    response = client.post("/api/v1/pricing/calculate", json=data)
    assert response.status_code == 200
```

## Key Benefits

1. **Familiar**: Spring Boot developers understand immediately
2. **Simple**: Clear dependency flow (top → bottom)
3. **Testable**: Each layer tested independently
4. **Maintainable**: Clear separation of concerns
5. **SOLID**: All principles followed
6. **Functional Core**: Pure business logic
7. **Standard**: Industry-standard pattern

## Migration from Clean Architecture

The application was migrated from Hexagonal Architecture (Ports & Adapters) to Layered Architecture while maintaining the functional core:

**Before**:
- Feature-first organization (vertical slices)
- Ports & Adapters pattern
- Use cases + Gateways

**After**:
- Layer-first organization (horizontal layers)
- Spring Boot pattern
- Services + Repositories

**What stayed the same**:
- ✅ Functional core (pure functions)
- ✅ Domain models
- ✅ Business logic
- ✅ Tests (only imports changed)

## References

- [Spring Boot Documentation](https://spring.io/guides)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)
- [Functional Core, Imperative Shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell)
- [Layered Architecture](https://www.oreilly.com/library/view/software-architecture-patterns/9781491971437/ch01.html)
