# Folder Structure

This document explains the directory layout and file organization for the Layered Architecture pattern.

## Overview

The application follows **Layered Architecture** with clear separation by technical concerns (horizontal layers):

```
app/
├── controller/          # HTTP Layer
├── service/             # Business Logic Layer
├── repository/          # Data Access Layer
├── domain/              # Domain Layer (Models + Core)
├── dto/                 # Data Transfer Objects
├── exception/           # Exception Handling
├── config/              # Configuration & DI
├── infrastructure/      # Cross-cutting Concerns
└── main.py              # Application Entry Point
```

## Complete Structure

```
fastapi-enterprise/
├── app/                             # Application source code
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   │
│   ├── controller/                  # Controller Layer (@RestController)
│   │   ├── __init__.py
│   │   ├── pricing_controller.py   # Pricing REST endpoints
│   │   └── health_controller.py    # Health check endpoints
│   │
│   ├── service/                     # Service Layer (@Service)
│   │   ├── __init__.py
│   │   └── pricing_service.py      # Pricing business orchestration
│   │
│   ├── repository/                  # Repository Layer (@Repository)
│   │   ├── __init__.py
│   │   ├── cost_repository.py      # Cost data access
│   │   ├── config_repository.py    # Configuration data
│   │   ├── pricing_repository.py   # Pricing persistence
│   │   └── metrics_repository.py   # Metrics & telemetry
│   │
│   ├── domain/                      # Domain Layer
│   │   ├── __init__.py
│   │   ├── model/                   # Domain Models
│   │   │   ├── __init__.py
│   │   │   ├── enums.py            # Enumerations
│   │   │   ├── cost_models.py      # Cost entities
│   │   │   └── pricing_models.py   # Pricing entities
│   │   │
│   │   └── core/                    # Functional Core (Pure Functions)
│   │       ├── __init__.py
│   │       ├── cost/
│   │       │   ├── __init__.py
│   │       │   └── calculations.py # Cost calculations
│   │       │
│   │       └── pricing/
│   │           ├── __init__.py
│   │           ├── calculations.py           # Base pricing
│   │           ├── tier_calculations.py      # Tier pricing
│   │           ├── discount_calculations.py  # Discounts
│   │           └── margin_calculations.py    # Margins
│   │
│   ├── dto/                         # Data Transfer Objects
│   │   ├── __init__.py
│   │   ├── request/                 # API Request DTOs
│   │   │   ├── __init__.py
│   │   │   └── pricing_request.py
│   │   │
│   │   └── response/                # API Response DTOs
│   │       ├── __init__.py
│   │       └── pricing_response.py
│   │
│   ├── exception/                   # Exception Handling
│   │   ├── __init__.py
│   │   ├── domain_exceptions.py    # Domain exceptions
│   │   └── handler.py              # Global handlers
│   │
│   ├── config/                      # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py             # App settings (from core/)
│   │   └── dependencies.py         # Dependency injection
│   │
│   ├── infrastructure/              # Infrastructure
│   │   ├── __init__.py
│   │   ├── database.py             # Database setup
│   │   ├── logging.py              # Logging config
│   │   ├── telemetry.py            # OpenTelemetry
│   │   └── celery_app.py           # Background tasks
│   │
│   ├── util/                        # Utilities
│   │   ├── __init__.py
│   │   └── validators.py           # Common validators
│   │
│   └── core/                        # Legacy (being migrated)
│       ├── config.py                # Settings
│       └── tasks.py                 # Celery tasks
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest configuration
│   │
│   ├── unit/                        # Unit tests
│   │   ├── domains/                 # Domain core tests (pure functions)
│   │   │   ├── test_cost_calculations.py
│   │   │   ├── test_pricing_calculations.py
│   │   │   ├── test_discount_calculations.py
│   │   │   └── test_tier_calculations.py
│   │   │
│   │   ├── test_services.py         # Service tests (mock repos)
│   │   └── test_repositories.py     # Repository tests
│   │
│   ├── integration/                 # Integration tests
│   │   ├── test_pricing_api.py      # API endpoint tests
│   │   └── test_pricing_error_paths.py
│   │
│   └── contract/                    # Contract tests
│       └── test_api_contracts.py
│
├── docs/                            # Documentation
│   ├── README.md
│   ├── architecture/                # Architecture docs
│   ├── development/                 # Development guides
│   ├── operations/                  # Operations docs
│   └── features/                    # Feature docs
│
├── .cursor/                         # Cursor IDE rules
│   └── rules/                       # Organized rules
│       ├── 00-overview.md
│       ├── 01-architecture.md
│       ├── 02-controller-layer.md
│       ├── 03-service-layer.md
│       ├── 04-repository-layer.md
│       ├── 05-domain-layer.md
│       ├── 06-testing.md
│       ├── 07-dependency-injection.md
│       ├── 08-code-standards.md
│       ├── 09-development-workflow.md
│       └── 10-anti-patterns.md
│
├── migrations/                      # Alembic migrations
│   └── versions/
│
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── .cursorrules                     # Legacy Cursor rules
├── pyproject.toml                   # Project metadata
├── uv.lock                          # Dependency lock
├── Makefile                         # Build commands
├── Dockerfile                       # Container definition
├── docker-compose.yml               # Local development
└── README.md                        # Project README

```

## Layer Details

### Controller Layer (`controller/`)

**Purpose**: HTTP request/response handling

Files:
- `*_controller.py` - REST endpoint definitions
- One file per resource/domain

Pattern:
```python
# controller/pricing_controller.py
from fastapi import APIRouter, Depends
from app.service.pricing_service import PricingService
from app.dto.request.pricing_request import PricingRequestDTO

router = APIRouter(prefix="/api/v1/pricing", tags=["Pricing"])

@router.post("/calculate")
async def calculate_pricing(
    request: PricingRequestDTO,
    service: PricingService = Depends(get_pricing_service)
):
    return await service.calculate_pricing(request)
```

### Service Layer (`service/`)

**Purpose**: Business logic orchestration

Files:
- `*_service.py` - Business logic classes
- One file per major business domain

Pattern:
```python
# service/pricing_service.py
class PricingService:
    def __init__(
        self,
        cost_repository: CostRepository,
        config_repository: ConfigRepository,
    ):
        self.cost_repository = cost_repository
        self.config_repository = config_repository

    async def calculate_pricing(self, request: PricingRequestDTO):
        # Orchestrate repositories and domain core
        pass
```

### Repository Layer (`repository/`)

**Purpose**: Data access abstraction

Files:
- `*_repository.py` - Data access classes
- One file per data source or aggregate

Pattern:
```python
# repository/cost_repository.py
class CostRepository:
    async def get_material_costs(self):
        # Database access
        return await self._fetch_from_database()
```

### Domain Layer (`domain/`)

**Purpose**: Core business domain

Two sub-packages:

#### Domain Models (`domain/model/`)
- `*_models.py` - Dataclasses for entities
- `enums.py` - Domain enumerations

Pattern:
```python
# domain/model/pricing_models.py
@dataclass(frozen=True)
class PricingConfiguration:
    margin_percentage: float
    volume_discount_thresholds: dict[int, float]
```

#### Functional Core (`domain/core/`)
- `*/calculations.py` - Pure business functions
- Organized by subdomain

Pattern:
```python
# domain/core/pricing/calculations.py
def calculate_margin(
    base_cost: Decimal,
    config: PricingConfiguration
) -> Decimal:
    """Pure function - no side effects."""
    return base_cost * Decimal(str(config.margin_percentage))
```

### DTO Layer (`dto/`)

**Purpose**: API request/response schemas

Files:
- `request/*_request.py` - Request DTOs
- `response/*_response.py` - Response DTOs

Pattern:
```python
# dto/request/pricing_request.py
from pydantic import BaseModel, Field

class PricingRequestDTO(BaseModel):
    material: str = Field(description="Material type")
    quantity: int = Field(gt=0, description="Number of parts")
```

## File Naming Conventions

### Python Files
- `snake_case.py` for all files
- Suffix with layer: `*_controller.py`, `*_service.py`, `*_repository.py`
- Domain core: `calculations.py` (pure functions)
- Models: `*_models.py` (entities)
- DTOs: `*_request.py`, `*_response.py`

### Test Files
- `test_*.py` prefix
- Mirror source structure: `test_pricing_service.py`
- Domain tests: `test_*_calculations.py`

### Classes
- `PascalCase` for classes
- Suffix with type: `PricingService`, `CostRepository`, `PricingRequestDTO`

### Functions
- `snake_case` for functions
- Verb-noun pattern: `calculate_margin`, `get_material_costs`

## Import Conventions

### Absolute Imports (Preferred)

```python
# Good - absolute imports
from app.domain.model import Material, MaterialCost
from app.domain.core.pricing import calculate_margin
from app.service.pricing_service import PricingService
from app.repository.cost_repository import CostRepository
```

### Relative Imports (Avoid)

```python
# Bad - relative imports
from ..model import Material
from ...service import PricingService
```

### Import Order

1. Standard library
2. Third-party packages
3. Local application

```python
# Standard library
from datetime import datetime
from decimal import Decimal

# Third-party
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# Local application
from app.domain.model import Material
from app.service.pricing_service import PricingService
```

## Dependency Flow

```
Controller Layer
    ↓ imports
Service Layer
    ↓ imports
Repository Layer
    ↓ imports
Domain Layer (Models)
    ↓ imports
Domain Layer (Core) ← Pure functions, no imports from app/
```

**Rule**: Each layer only imports from layers below it.

## Adding New Code

### New REST Endpoint
1. Create DTO in `dto/request/` and `dto/response/`
2. Add method to Service
3. Create endpoint in Controller
4. Wire in `config/dependencies.py`

### New Business Logic
1. Write pure function in `domain/core/`
2. Call from Service
3. Test without mocks!

### New Data Access
1. Create Repository class
2. Define interface methods
3. Inject into Service

### New Domain Concept
1. Create model in `domain/model/`
2. Use in repositories and services
3. Keep immutable (`frozen=True`)

## Common Patterns

### Controller Pattern
```
controller/
├── pricing_controller.py    # Pricing endpoints
├── health_controller.py      # Health checks
└── __init__.py
```

### Service Pattern
```
service/
├── pricing_service.py        # Pricing business logic
├── cost_service.py           # Cost business logic
└── __init__.py
```

### Repository Pattern
```
repository/
├── cost_repository.py        # Cost data
├── config_repository.py      # Configuration
├── pricing_repository.py     # Pricing persistence
└── __init__.py
```

### Domain Pattern
```
domain/
├── model/
│   ├── enums.py              # Shared enums
│   ├── cost_models.py        # Cost entities
│   └── pricing_models.py     # Pricing entities
│
└── core/
    ├── cost/calculations.py  # Cost pure functions
    └── pricing/
        ├── calculations.py        # Base pricing
        ├── tier_calculations.py   # Tier-specific
        └── discount_calculations.py
```

## Best Practices

### Organization
- ✅ One class per file
- ✅ Group related functions in modules
- ✅ Keep layers separate
- ❌ Don't mix layers in same file

### Naming
- ✅ Descriptive names
- ✅ Consistent suffixes
- ✅ Clear domain language
- ❌ Abbreviations or acronyms

### Dependencies
- ✅ Import from lower layers only
- ✅ Absolute imports
- ✅ Explicit over implicit
- ❌ Circular dependencies

### Files
- ✅ Small, focused files (< 500 lines)
- ✅ Single responsibility
- ✅ Clear module boundaries
- ❌ God files/classes

## References

- [Spring Boot Project Structure](https://spring.io/guides/gs/spring-boot/)
- [Python Package Structure](https://docs.python.org/3/tutorial/modules.html)
- [FastAPI Project Structure](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
