# Clean Architecture Implementation

## Overview

This application follows **Clean Architecture** (Uncle Bob's pattern), with **Functional Core, Imperative Shell** (FCIS) principles for maximum testability and maintainability.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    FRAMEWORKS & DRIVERS (Outermost)              │
│                    Web, Database, External Interfaces            │
│                                                                  │
│   ┌────────────────────────────────────────────────────────────┐│
│   │            INTERFACE ADAPTERS                              ││
│   │       Controllers, Gateways, Presenters                    ││
│   │                                                            ││
│   │  ┌──────────────────────────────────────────────────────┐ ││
│   │  │         USE CASES (Application Business Rules)       │ ││
│   │  │     Orchestrates entities with gateways              │ ││
│   │  │                                                      │ ││
│   │  │  ┌────────────────────────────────────────────────┐ │ ││
│   │  │  │      ENTITIES (Enterprise Business Rules)      │ │ ││
│   │  │  │         Pure business logic (Innermost)       │ │ ││
│   │  │  │                                                │ │ ││
│   │  │  │  • Pricing entities (pure functions)          │ │ ││
│   │  │  │  • Cost entities (pure functions)             │ │ ││
│   │  │  │  • No dependencies on outer layers            │ │ ││
│   │  │  └────────────────────────────────────────────────┘ │ ││
│   │  └──────────────────────────────────────────────────────┘ ││
│   └────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
app/
├── features/                          # Feature-first organization
│   ├── pricing/                       # Pricing feature
│   │   ├── entities/                  # Layer 1: Entities (Enterprise Business Rules)
│   │   │   ├── calculations.py        # Pure functions
│   │   │   ├── tier/                  # Tier subdomain
│   │   │   ├── discount/              # Discount subdomain
│   │   │   └── margin/                # Margin subdomain
│   │   │
│   │   ├── use_cases/                 # Layer 2: Use Cases (Application Business Rules)
│   │   │   ├── calculate_pricing/
│   │   │   │   ├── use_case.py        # Orchestration logic
│   │   │   │   ├── input_dto.py       # Use case boundary
│   │   │   │   └── output_dto.py      # Use case boundary
│   │   │   └── interfaces/            # Gateway interfaces
│   │   │       ├── cost_gateway.py
│   │   │       └── pricing_config_gateway.py
│   │   │
│   │   ├── interface_adapters/        # Layer 3: Interface Adapters
│   │   │   ├── controllers/           # Request handling
│   │   │   ├── presenters/            # Response formatting
│   │   │   └── gateways/              # Gateway implementations
│   │   │       ├── cost_data_gateway_impl.py
│   │   │       └── metrics_gateway_impl.py
│   │   │
│   │   └── frameworks/                # Layer 4: Frameworks & Drivers
│   │       └── web/
│   │           ├── routes.py          # FastAPI routes
│   │           ├── schemas.py         # HTTP DTOs
│   │           └── dependencies.py    # Dependency injection
│   │
│   └── cost/                          # Cost feature
│       ├── entities/                  # Pure business logic
│       └── use_cases/                 # Application logic
│
├── shared/                            # Shared kernel
│   ├── entities/                      # Shared value objects
│   └── exceptions.py                  # Domain exceptions
│
└── frameworks/                        # Cross-cutting infrastructure
    ├── database/                      # Database connections
    ├── web/                           # FastAPI app setup
    └── telemetry/                     # Observability
```

## The Four Layers

### 1. Entities (Enterprise Business Rules) - Innermost

**Purpose**: Contains pure business logic with no dependencies.

**Characteristics:**
- ✅ Pure functions (functional core)
- ✅ No side effects
- ✅ No I/O operations
- ✅ No framework dependencies
- ✅ Most stable layer

**Example:**
```python
# app/features/pricing/entities/calculations.py
def calculate_complexity_surcharge(
    cost_plus_margin: Decimal,
    complexity_score: float,
    config: PricingConfiguration,
) -> Decimal:
    """Pure function - no side effects."""
    if complexity_score >= config.complexity_surcharge_threshold:
        return cost_plus_margin * Decimal(str(config.complexity_surcharge_rate))
    return Decimal("0")
```

### 2. Use Cases (Application Business Rules)

**Purpose**: Orchestrate entities with gateways, implement application-specific logic.

**Characteristics:**
- ✅ Coordinates entities and gateways
- ✅ Defines Input/Output DTOs (use case boundaries)
- ✅ No framework dependencies
- ✅ Depends only on entity layer and gateway interfaces

**Example:**
```python
# app/features/pricing/use_cases/calculate_pricing/use_case.py
class CalculatePricingUseCase:
    def __init__(
        self,
        cost_data_gateway: CostDataGateway,
        metrics_gateway: MetricsGateway,
    ):
        self.cost_data_gateway = cost_data_gateway
        self.metrics_gateway = metrics_gateway

    async def execute(self, input_dto: CalculatePricingInputDTO) -> CalculatePricingOutputDTO:
        # 1. Get data via gateways
        costs = await self.cost_data_gateway.get_material_costs()

        # 2. Execute pure business logic
        result = calculate_tier_pricing(...)

        # 3. Record metrics via gateways
        await self.metrics_gateway.record_pricing_metrics(...)

        return CalculatePricingOutputDTO(...)
```

### 3. Interface Adapters

**Purpose**: Convert data between use cases and external interfaces.

**Components:**
- **Controllers**: Handle HTTP requests, call use cases
- **Presenters**: Format use case outputs for presentation
- **Gateways**: Implement gateway interfaces for external systems

**Example:**
```python
# app/features/pricing/interface_adapters/gateways/cost_data_gateway_impl.py
class CostDataGatewayImpl:
    """Implements CostDataGateway interface"""
    async def get_material_costs(self) -> dict[Material, MaterialCost]:
        # Database/API calls here
        return self._fetch_from_database()
```

### 4. Frameworks & Drivers (Outermost)

**Purpose**: External interfaces and framework-specific code.

**Components:**
- FastAPI routes and HTTP schemas
- Database connection managers
- External service clients
- Framework configuration

**Example:**
```python
# app/features/pricing/frameworks/web/routes.py
@router.post("/pricing")
async def calculate_pricing(
    request: PricingRequestSchema,
    use_case: CalculatePricingUseCase = Depends(get_pricing_use_case),
) -> PricingResponseSchema:
    input_dto = convert_to_input_dto(request)
    output_dto = await use_case.execute(input_dto)
    return convert_to_response(output_dto)
```

## Dependency Rule

**Dependencies point INWARD** toward entities:

```
Frameworks → Interface Adapters → Use Cases → Entities
```

- **Entities** depend on nothing
- **Use Cases** depend only on entities and gateway interfaces
- **Interface Adapters** depend on use cases and entities
- **Frameworks** depend on interface adapters

## Functional Core, Imperative Shell

### Functional Core (Entities)

Pure functions with no side effects:

```python
def calculate_margin(base_cost: Decimal, config: PricingConfiguration) -> Decimal:
    """Pure function - deterministic, no side effects"""
    return base_cost * Decimal(str(config.margin_percentage))
```

### Imperative Shell (Gateways, Frameworks)

All side effects isolated:

```python
class MetricsGatewayImpl:
    """All I/O happens here"""
    async def record_pricing_metrics(self, ...) -> None:
        # Side effect: Record to Prometheus
        _pricing_counter.inc()
```

## Benefits

1. **Testability**: Test pure functions without mocks
2. **Independence**: Business logic independent of frameworks
3. **Flexibility**: Swap frameworks without touching business logic
4. **Maintainability**: Clear separation of concerns
5. **Screaming Architecture**: Structure reveals intent

## Feature-First Organization

Features are organized independently with all layers:

```
pricing/
  ├── entities/        (business rules)
  ├── use_cases/       (application logic)
  ├── interface_adapters/  (conversions)
  └── frameworks/      (external interfaces)
```

This makes features cohesive and easy to understand.

## Gateway Pattern

Gateways replace "Ports & Adapters" terminology:

- **Gateway Interface** (use_cases/interfaces/): Defines contract
- **Gateway Implementation** (interface_adapters/gateways/): Implements contract

## Summary

✅ **Clear layering** with dependency rule
✅ **Pure business logic** in entities
✅ **Use case boundaries** with DTOs
✅ **Feature-first** organization
✅ **FCIS pattern** preserved
✅ **Uncle Bob's Clean Architecture** principles
