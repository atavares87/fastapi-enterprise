# Code Standards

## Python Standards

- Python 3.11+ with type hints everywhere
- Black formatting (line length: 88)
- Use `uv` for package management
- Pydantic for validation
- Async/await where needed (not in pure domain core)

## Type Hints

**Required everywhere!**

```python
# Good
def calculate_margin(base_cost: Decimal, config: PricingConfiguration) -> Decimal:
    return base_cost * Decimal(str(config.margin_percentage))

# Bad - missing type hints
def calculate_margin(base_cost, config):
    return base_cost * config.margin_percentage
```

## Naming Conventions

### Files
- `snake_case.py` for all files
- Descriptive names: `pricing_service.py`, not `service.py`

### Classes
- `PascalCase` for classes
- Suffix with type: `PricingService`, `CostRepository`, `PricingRequestDTO`

### Functions
- `snake_case` for functions
- Verb-noun pattern: `calculate_margin`, `get_material_costs`, `save_pricing_result`

### Constants
- `UPPER_SNAKE_CASE` for constants
- Module-level: `MAX_COMPLEXITY_SCORE = 5.0`

### Private Methods
- Prefix with `_`: `_calculate_internal`, `_fetch_from_database`

## Documentation

### Docstrings (Required)

```python
def calculate_complexity_surcharge(
    cost_plus_margin: Decimal,
    complexity_score: float,
    config: PricingConfiguration,
) -> Decimal:
    """
    Calculate complexity surcharge based on score and configuration.

    Pure function - same input always produces same output.

    Args:
        cost_plus_margin: Base cost plus calculated margin
        complexity_score: Geometric complexity score (1.0-5.0)
        config: Pricing configuration with thresholds

    Returns:
        Complexity surcharge amount (0 if below threshold)

    Examples:
        >>> calculate_complexity_surcharge(Decimal("100"), 4.5, config)
        Decimal("20.00")
    """
    if complexity_score >= config.complexity_surcharge_threshold:
        return cost_plus_margin * Decimal(str(config.complexity_surcharge_rate))
    return Decimal("0")
```

### Comments

- Use sparingly (code should be self-documenting)
- Explain WHY, not WHAT
- Document business rules and non-obvious logic

```python
# Good - explains WHY
# Apply buffer factor to account for manufacturing features
weight = volume * density * 1.15

# Bad - explains WHAT (obvious from code)
# Multiply volume by density and 1.15
weight = volume * density * 1.15
```

## Error Handling

### Exceptions

```python
# Domain exceptions
class DomainException(Exception):
    """Base exception for domain errors."""
    pass

class ValidationException(DomainException):
    """Validation error."""
    pass

# Usage
if quantity <= 0:
    raise ValidationException("Quantity must be positive")
```

### Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Good - structured logging
logger.info(
    "Pricing calculation completed",
    calculation_id=str(calculation_id),
    duration_ms=duration_ms,
    material=material,
)

# Bad - string concatenation
logger.info(f"Completed calculation {calculation_id} in {duration_ms}ms")
```

## Best Practices

### Use Decimal for Money

```python
# Good
from decimal import Decimal
price = Decimal("99.99")

# Bad
price = 99.99  # Float precision issues!
```

### Immutable Data Structures

```python
# Good - immutable
@dataclass(frozen=True)
class PricingConfiguration:
    margin_percentage: float

# Bad - mutable
@dataclass
class PricingConfiguration:
    margin_percentage: float
```

### Explicit is Better Than Implicit

```python
# Good - explicit
material = Material.ALUMINUM

# Bad - magic strings
material = "aluminum"
```

## Before Committing

```bash
make format         # Format code with Black
make lint           # Check with Ruff
make type-check     # MyPy type checking
make check-all      # All of the above
make test           # Run all tests
```

## Import Organization

```python
# Standard library
from datetime import datetime
from decimal import Decimal

# Third-party
from fastapi import APIRouter
from pydantic import BaseModel

# Local application
from app.domain.model import Material
from app.service.pricing_service import PricingService
```

## Anti-Patterns to Avoid

- ❌ Global variables for state
- ❌ Mutable global constants
- ❌ God classes (classes doing too much)
- ❌ Long functions (> 50 lines)
- ❌ Deep nesting (> 3 levels)
- ❌ Magic numbers (use named constants)
- ❌ String typing (use Enums)
- ❌ Catching generic Exception
