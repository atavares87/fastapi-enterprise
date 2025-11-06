# Domain Layer

**Location**: `app/domain/`

**Responsibility**: Core business domain

## Two Sub-Layers

### 1. Domain Models (`domain/model/`)

- Entity classes (dataclasses)
- Value objects
- Enums
- Domain events
- **NO I/O operations**

### 2. Functional Core (`domain/core/`)

- **Pure functions** (no side effects)
- Core business calculations
- Business rules
- **NO I/O, NO database, NO HTTP, NO logging**
- **NO mutable state**
- **Completely testable without mocks**

## Example - Domain Model

```python
@dataclass(frozen=True)
class PricingConfiguration:
    """Configuration for pricing calculations."""
    margin_percentage: float
    volume_discount_thresholds: dict[int, float]
    complexity_surcharge_threshold: float
    complexity_surcharge_rate: float

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.margin_percentage < 0:
            raise ValueError("Margin percentage must be non-negative")
```

## Example - Functional Core

```python
def calculate_complexity_surcharge(
    cost_plus_margin: Decimal,
    complexity_score: float,
    config: PricingConfiguration,
) -> Decimal:
    """Pure function - same input always produces same output."""
    if complexity_score >= config.complexity_surcharge_threshold:
        return cost_plus_margin * Decimal(str(config.complexity_surcharge_rate))
    return Decimal("0")
```

## Functional Core Principles

### What Makes a Function Pure?

1. **Deterministic**: Same input → same output, always
2. **No side effects**: No I/O, no mutations, no global state
3. **Referentially transparent**: Can be replaced with its return value
4. **Easily testable**: No mocks needed!

### Pure Function Checklist

- ✅ All inputs passed as parameters
- ✅ Returns a value (not modifying parameters)
- ✅ No I/O operations (database, network, file system)
- ✅ No logging or metrics
- ✅ No `datetime.now()` or `random()`
- ✅ No mutable global state
- ✅ No exceptions for control flow (use Result types or return values)

## Anti-Patterns to Avoid

### Domain Models
- ❌ Database-specific annotations
- ❌ HTTP-specific fields
- ❌ Framework dependencies

### Functional Core
- ❌ Database calls
- ❌ API calls
- ❌ Logging statements
- ❌ Using current time (pass as parameter)
- ❌ Reading environment variables
- ❌ Global variables or singletons
- ❌ Mocking in tests (if you need mocks, it's not pure!)

## Best Practices

- ✅ Use immutable dataclasses (`frozen=True`)
- ✅ Type hints on everything
- ✅ Validation in `__post_init__`
- ✅ Use `Decimal` for money calculations
- ✅ Document business rules in docstrings
- ✅ Keep functions small (< 20 lines)
- ✅ Compose small functions into larger ones
- ✅ Test pure functions directly (no setup needed!)
