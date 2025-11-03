# Hexagonal Architecture Implementation

## Overview

This application follows **Hexagonal Architecture** (also known as **Ports and Adapters**), with **Functional Core, Imperative Shell** (FCIS) principles for maximum testability and maintainability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRIMARY ADAPTERS (INBOUND)                  │
│                    Who DRIVES the application                    │
│                                                                  │
│    ┌──────────────────┐         ┌──────────────────┐           │
│    │   Web (REST)     │         │  Metrics/Health  │           │
│    │  adapter/inbound/│         │  adapter/inbound/│           │
│    │      web/        │         │      web/        │           │
│    └────────┬─────────┘         └────────┬─────────┘           │
│             │                            │                      │
└─────────────┼────────────────────────────┼──────────────────────┘
              │                            │
              └────────────┬───────────────┘
                           │
              ┌────────────▼────────────┐
              │    INPUT PORTS          │
              │ core/port/inbound/      │
              │  (interfaces)           │
              └────────────┬────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│                         THE HEXAGON                             │
│                        (CORE LOGIC)                             │
│                                                                 │
│    ┌──────────────────────────────────────────────────┐        │
│    │         APPLICATION LAYER                         │        │
│    │        core/application/                          │        │
│    │      (Use Cases / Orchestration)                  │        │
│    │                                                   │        │
│    │  • CalculatePricingUseCase                       │        │
│    │    - Gather data (via output ports)              │        │
│    │    - Execute domain logic (pure functions)       │        │
│    │    - Persist results (via output ports)          │        │
│    └─────────────────┬────────────────────────────────┘        │
│                      │                                          │
│    ┌─────────────────▼───────────────────────────────┐         │
│    │         DOMAIN LAYER (FUNCTIONAL CORE)           │         │
│    │          core/domain/                            │         │
│    │        (Pure Business Logic)                     │         │
│    │                                                  │         │
│    │  • Cost Domain (pure functions)                 │         │
│    │    - calculate_manufacturing_cost()             │         │
│    │    - estimate_cost_range()                      │         │
│    │                                                  │         │
│    │  • Pricing Domain (pure functions)              │         │
│    │    - calculate_tier_pricing()                   │         │
│    │    - calculate_margin()                         │         │
│    │                                                  │         │
│    │  NO SIDE EFFECTS! Pure calculations only.       │         │
│    └──────────────────────────────────────────────────┘         │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
              ┌──────────▼───────────┐
              │    OUTPUT PORTS       │
              │  core/port/outbound/  │
              │   (interfaces)        │
              │                       │
              │  • CostDataPort       │
              │  • PricingConfigPort  │
              │  • TelemetryPort      │
              │  • HTTPMetricsPort    │
              └──────────┬────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                  SECONDARY ADAPTERS (OUTBOUND)                   │
│                  DRIVEN by the application                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Persistence  │  │  Telemetry   │  │   External   │         │
│  │ adapter/     │  │ adapter/     │  │   Services   │         │
│  │ outbound/    │  │ outbound/    │  │ adapter/     │         │
│  │ persistence/ │  │  telemetry/  │  │ outbound/    │         │
│  │              │  │              │  │              │         │
│  │ • Database   │  │ • Metrics    │  │ • 3rd party  │         │
│  │ • Repos      │  │ • Tracing    │  │   services   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
app/
├── adapter/                    # ADAPTERS (External interfaces)
│   ├── inbound/               # PRIMARY/DRIVING Adapters (who drives the app)
│   │   └── web/               # REST API / HTTP interface
│   │       ├── dependencies.py    # Dependency injection
│   │       ├── metrics_middleware.py  # Golden 4 metrics
│   │       ├── pricing.py         # API endpoints/controllers
│   │       └── schemas.py         # Request/Response DTOs
│   │
│   └── outbound/              # SECONDARY/DRIVEN Adapters (driven by the app)
│       ├── persistence/       # Database / Data access
│       │   ├── cost_data_adapter.py
│       │   └── pricing_config_adapter.py
│       │
│       └── telemetry/         # Metrics / Monitoring
│           ├── metrics_adapter.py
│           └── golden4_metrics_adapter.py
│
├── core/                      # CORE (The Hexagon - Business Logic)
│   ├── domain/                # DOMAIN - Business entities & logic
│   │   ├── cost/             # Cost domain
│   │   │   ├── models.py         # Value objects, entities
│   │   │   └── calculations.py   # Pure business functions
│   │   │
│   │   └── pricing/           # Pricing domain
│   │       ├── models.py         # Value objects, entities
│   │       └── calculations.py   # Pure business functions
│   │
│   ├── application/           # APPLICATION - Use cases / Orchestration
│   │   └── pricing/
│   │       └── use_cases.py      # CalculatePricingUseCase
│   │
│   └── port/                  # PORTS - Interfaces
│       ├── inbound/           # Input ports (for primary adapters)
│       │                      # (currently empty - can add when needed)
│       │
│       └── outbound/          # Output ports (for secondary adapters)
│           ├── cost_ports.py     # CostDataPort
│           ├── pricing_ports.py  # PricingConfigPort, TelemetryPort
│           └── metrics_ports.py  # HTTPMetricsPort, SystemMetricsPort
│
├── config.py                  # Configuration management
├── database.py                # Database connections
├── telemetry.py               # OpenTelemetry setup
├── background_tasks.py        # Background collectors
└── main.py                    # Application entry point
```

## Layer Responsibilities

### 1. Domain Layer (`core/domain/`)

**FUNCTIONAL CORE** - Pure business logic with no side effects.

**Responsibilities:**

- Domain models (entities, value objects)
- Pure business functions
- Business rules and calculations
- Domain events

**Rules:**

- ✅ No I/O operations
- ✅ No database access
- ✅ No HTTP calls
- ✅ No external dependencies
- ✅ Pure functions only
- ✅ Deterministic behavior

**Example:**

```python
# Pure function - always returns same output for same input
def calculate_tier_pricing(
    cost_breakdown: CostBreakdown,
    config: PricingConfiguration,
    current_time: datetime,  # Passed as parameter, not accessed directly
) -> TierPricing:
    """Pure pricing calculation - no side effects."""
    # All calculations are pure
    base_price = cost_breakdown.total_cost
    margin = _calculate_margin(base_price, config.margin_percent)
    return TierPricing(...)
```

### 2. Application Layer (`core/application/`)

**ORCHESTRATION LAYER** - Coordinates functional core with imperative shell.

**Responsibilities:**

- Use case implementation
- Transaction management
- Orchestrate domain logic
- Call adapters via ports
- Convert exceptions

**Example:**

```python
class CalculatePricingUseCase:
    """Orchestrates functional core with imperative shell."""

    def __init__(
        self,
        cost_port: CostDataPort,         # Imperative shell
        pricing_port: PricingConfigPort, # Imperative shell
        telemetry_port: TelemetryPort,   # Imperative shell
    ):
        self._cost_port = cost_port
        self._pricing_port = pricing_port
        self._telemetry_port = telemetry_port

    async def execute(self, request: PricingRequest) -> PricingResult:
        # 1. IMPERATIVE SHELL: Gather data
        costs = await self._cost_port.get_current_costs()
        config = await self._pricing_port.get_config()

        # 2. FUNCTIONAL CORE: Pure calculation
        result = calculate_tier_pricing(
            cost_breakdown=costs,
            config=config,
            current_time=datetime.utcnow(),
        )

        # 3. IMPERATIVE SHELL: Persist & record metrics
        await self._telemetry_port.record_metrics(result)

        return result
```

### 3. Ports (`core/port/`)

**INTERFACES** - Define contracts between core and adapters.

**Inbound Ports** (`core/port/inbound/`):

- Interfaces that primary adapters call
- Define use case contracts
- Currently empty (use cases called directly)

**Outbound Ports** (`core/port/outbound/`):

- Interfaces that secondary adapters implement
- Define external capabilities needed by core
- Repository interfaces, external service interfaces

**Example:**

```python
# Output port - interface for imperative shell
class CostDataPort(Protocol):
    """Interface for cost data access."""

    async def get_current_costs(self) -> Dict[str, Decimal]:
        """Get current material and labor costs."""
        ...

    async def get_labor_rates(self) -> Dict[str, Decimal]:
        """Get labor rates by process."""
        ...
```

### 4. Adapters (`adapter/`)

**IMPERATIVE SHELL** - All side effects happen here.

**Inbound Adapters** (`adapter/inbound/`):

- Drive the application
- Convert external input → use cases
- Examples: REST API, CLI, GraphQL

**Outbound Adapters** (`adapter/outbound/`):

- Driven by the application
- Implement ports (interfaces)
- Examples: Databases, external APIs, message queues

**Example:**

```python
# Outbound adapter - implements port interface
class CostDataAdapter:
    """PostgreSQL implementation of CostDataPort."""

    async def get_current_costs(self) -> Dict[str, Decimal]:
        # IMPERATIVE SHELL: Database I/O
        async with self._session() as session:
            result = await session.execute(select(MaterialCost))
            return {row.material: row.cost for row in result.scalars()}
```

## Dependency Flow

**The Dependency Rule:** Dependencies point **INWARD** toward the core!

```
adapter/inbound/  ──→  core/application/  ──→  core/domain/
                              ↓
                       core/port/outbound/
                              ↓
                       adapter/outbound/
```

**What this means:**

1. **Domain** depends on nothing
2. **Application** depends only on domain
3. **Ports** define interfaces (depend on domain types)
4. **Adapters** depend on ports and application
5. **External frameworks** stay in adapters

## Functional Core, Imperative Shell

### Functional Core (Domain)

**Pure functions** with no side effects:

```python
def calculate_manufacturing_cost(
    specification: PartSpecification,
    material_costs: Dict[str, Decimal],
    labor_rates: Dict[str, Decimal],
) -> CostBreakdown:
    """
    Pure function - deterministic, no side effects.

    ✅ Always returns same output for same input
    ✅ No database calls
    ✅ No HTTP requests
    ✅ No current time access
    ✅ No logging
    ✅ Easily testable without mocks
    """
    volume = specification.calculate_volume()
    material_cost = material_costs[specification.material] * volume
    labor_cost = labor_rates[specification.process] * specification.complexity

    return CostBreakdown(
        material_cost=material_cost,
        labor_cost=labor_cost,
        total_cost=material_cost + labor_cost,
    )
```

### Imperative Shell (Adapters)

**All side effects** isolated here:

```python
class PostgresCostAdapter:
    """Imperative shell - handles all I/O."""

    async def get_current_costs(self) -> Dict[str, Decimal]:
        # SIDE EFFECT: Database I/O
        async with self._session() as session:
            result = await session.execute(select(MaterialCost))
            return {row.material: row.cost for row in result.scalars()}
```

## Benefits

### 1. Testability

- **Domain**: Test pure functions directly, no mocks needed
- **Application**: Mock only ports, test orchestration
- **Adapters**: Integration tests with real external systems

### 2. Maintainability

- Clear separation of concerns
- Business logic isolated from frameworks
- Easy to understand data flow

### 3. Flexibility

- Swap adapters without touching core
- Add new adapters easily
- Change frameworks without changing business logic

### 4. Domain Focus

- Business logic is pure and explicit
- No framework leakage into domain
- Domain experts can read the code

## Adding New Features

### Add a New Domain

```
1. Create domain models and pure functions:
   app/core/domain/inventory/
   ├── models.py          # Entities and value objects
   └── calculations.py    # Pure business logic

2. Create output ports:
   app/core/port/outbound/
   └── inventory_ports.py  # InventoryRepository interface

3. Create adapters:
   app/adapter/outbound/persistence/
   └── inventory_adapter.py  # Database implementation
```

### Add a New Adapter

**Primary Adapter (drives the app):**

```
app/adapter/inbound/cli/
└── commands.py        # CLI commands that use use cases
```

**Secondary Adapter (driven by the app):**

```
app/adapter/outbound/messaging/
└── event_publisher.py  # Publishes domain events to message queue
```

## References

- **Hexagonal Architecture** - Alistair Cockburn
- **Clean Architecture** - Robert Martin
- **Functional Core, Imperative Shell** - Gary Bernhardt
- **Domain-Driven Design** - Eric Evans
- **Implementing Domain-Driven Design** - Vaughn Vernon

## Summary

✅ **Clear separation** between functional core and imperative shell
✅ **Dependencies point inward** toward the domain
✅ **Pure business logic** in the domain layer
✅ **All side effects** in adapters
✅ **Testable** without mocks
✅ **Maintainable** and flexible
✅ **Industry-standard** hexagonal architecture

Your application follows these principles rigorously! 🎉
