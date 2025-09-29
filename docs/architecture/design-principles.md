# Design Principles

## Overview

This document outlines the core design principles and patterns that guide the FastAPI Enterprise application. These principles ensure consistency, maintainability, and scalability across the entire codebase.

## Architectural Principles

### 1. Hexagonal Architecture (Ports and Adapters)

**Principle**: Isolate core business logic from external concerns through well-defined interfaces.

**Implementation**:
- **Ports**: Abstract interfaces in the domain layer
- **Adapters**: Concrete implementations in the infrastructure layer
- **Core**: Business logic that doesn't depend on external systems

```python
# Port (interface in domain layer)
class PricingRepository(ABC):
    @abstractmethod
    async def save_calculation(self, calculation: PricingCalculation) -> None:
        pass

# Adapter (implementation in infrastructure layer)
class PostgresPricingRepository(PricingRepository):
    async def save_calculation(self, calculation: PricingCalculation) -> None:
        # PostgreSQL-specific implementation
```

**Benefits**:
- Easy to test with mock implementations
- Database technology can be changed without affecting business logic
- Clear separation of concerns

### 2. Domain-Driven Design (DDD)

**Principle**: Model the software to match the business domain and its processes.

**Implementation**:
- **Bounded Contexts**: Separate domains (pricing, cost, health)
- **Ubiquitous Language**: Use business terminology in code
- **Value Objects**: Immutable objects representing domain concepts
- **Entities**: Objects with identity and lifecycle
- **Domain Services**: Stateless operations on domain objects

```python
# Value Object
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

# Entity
class PricingCalculation:
    def __init__(self, specification: PartSpecification):
        self.id = UUID4()
        self.specification = specification
        self.created_at = datetime.utcnow()
        self._result: Optional[PricingResult] = None
```

### 3. Dependency Inversion Principle

**Principle**: High-level modules should not depend on low-level modules. Both should depend on abstractions.

**Implementation**:
- Use abstract base classes for repository interfaces
- Inject dependencies through FastAPI's dependency injection system
- Configuration drives concrete implementations

```python
# High-level module depends on abstraction
class PricingService:
    def __init__(self, repository: PricingRepository):  # ← Abstract interface
        self._repository = repository

# Dependency injection configuration
def get_pricing_repository() -> PricingRepository:
    if settings.database_type == "postgres":
        return PostgresPricingRepository()
    elif settings.database_type == "mongodb":
        return MongoPricingRepository()
```

### 4. Single Responsibility Principle (SRP)

**Principle**: Each class should have only one reason to change.

**Implementation**:
- Small, focused classes and functions
- Clear separation of business logic, data access, and presentation
- Domain services handle specific business operations

```python
# Good: Single responsibility
class PricingCalculator:
    """Handles pricing calculations only"""
    def calculate_base_price(self, specification: PartSpecification) -> Money:
        # Only pricing logic here

class PricingValidator:
    """Handles pricing validation only"""
    def validate_specification(self, spec: PartSpecification) -> ValidationResult:
        # Only validation logic here

class PricingRepository:
    """Handles data persistence only"""
    async def save_calculation(self, calculation: PricingCalculation) -> None:
        # Only persistence logic here
```

### 5. Open-Closed Principle (OCP)

**Principle**: Software entities should be open for extension but closed for modification.

**Implementation**:
- Use interfaces and polymorphism for extensibility
- Strategy pattern for different pricing algorithms
- Plugin architecture for new features

```python
# Base strategy interface
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, specification: PartSpecification) -> Money:
        pass

# Concrete strategies
class StandardPricingStrategy(PricingStrategy):
    def calculate_price(self, specification: PartSpecification) -> Money:
        # Standard pricing logic

class PremiumPricingStrategy(PricingStrategy):
    def calculate_price(self, specification: PartSpecification) -> Money:
        # Premium pricing logic

# Context that uses strategies
class PricingService:
    def __init__(self, strategy: PricingStrategy):
        self._strategy = strategy

    def calculate_price(self, specification: PartSpecification) -> Money:
        return self._strategy.calculate_price(specification)
```

## Code Organization Principles

### 1. Layered Architecture

**Principle**: Organize code into distinct layers with clear dependencies.

**Layer Hierarchy** (dependencies flow downward):
```
Interface Layer (API)
    ↓
Application Layer (Core)
    ↓
Domain Layer (Business Logic)
    ↑
Infrastructure Layer (External Adapters)
```

**Rules**:
- Lower layers never depend on higher layers
- Infrastructure layer is an exception - it implements domain interfaces
- Cross-cutting concerns (logging, security) can span layers

### 2. Package by Feature

**Principle**: Organize code by business features rather than technical concerns.

```
# Good: Package by feature
app/domains/pricing/
├── models.py      # Pricing entities and value objects
├── services.py    # Pricing business logic
└── repositories.py # Pricing data access interfaces

app/domains/cost/
├── models.py      # Cost entities and value objects
├── services.py    # Cost calculation logic
└── repositories.py # Cost data access interfaces

# Bad: Package by layer
app/models/        # All models mixed together
app/services/      # All services mixed together
app/repositories/  # All repositories mixed together
```

### 3. Explicit Dependencies

**Principle**: Make all dependencies explicit and visible.

**Implementation**:
- Constructor injection for dependencies
- No global state or singletons
- Clear dependency graphs

```python
# Good: Explicit dependencies
class PricingService:
    def __init__(
        self,
        cost_service: CostService,
        repository: PricingRepository,
        logger: Logger
    ):
        self._cost_service = cost_service
        self._repository = repository
        self._logger = logger

# Bad: Hidden dependencies
class PricingService:
    def calculate_price(self, specification: PartSpecification) -> Money:
        cost_service = get_global_cost_service()  # ← Hidden dependency
        logger = get_global_logger()  # ← Hidden dependency
```

## Data Modeling Principles

### 1. Immutable Value Objects

**Principle**: Use immutable objects for values that don't have identity.

```python
@dataclass(frozen=True)
class Dimensions:
    length_mm: float
    width_mm: float
    height_mm: float

    def volume_cm3(self) -> float:
        return (self.length_mm * self.width_mm * self.height_mm) / 1000

    def scale(self, factor: float) -> "Dimensions":
        return Dimensions(
            self.length_mm * factor,
            self.width_mm * factor,
            self.height_mm * factor
        )
```

### 2. Rich Domain Models

**Principle**: Put behavior where the data is.

```python
# Good: Rich model with behavior
class PricingCalculation:
    def __init__(self, specification: PartSpecification):
        self.id = UUID4()
        self.specification = specification
        self.created_at = datetime.utcnow()
        self._tiers: Dict[str, PricingTier] = {}

    def add_tier(self, tier_name: str, tier: PricingTier) -> None:
        if tier.price.amount <= 0:
            raise ValueError("Tier price must be positive")
        self._tiers[tier_name] = tier

    def get_best_price(self) -> Money:
        if not self._tiers:
            raise ValueError("No pricing tiers available")
        return min(tier.price for tier in self._tiers.values())

# Bad: Anemic model without behavior
class PricingCalculation:
    def __init__(self):
        self.id = None
        self.specification = None
        self.tiers = []
```

### 3. Type Safety

**Principle**: Use type hints and validation to catch errors early.

```python
from typing import Optional, List, Dict
from pydantic import BaseModel, validator

class PartSpecification(BaseModel):
    material: str
    quantity: int
    dimensions: Dimensions
    geometric_complexity_score: float

    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

    @validator('geometric_complexity_score')
    def complexity_score_range(cls, v):
        if not 1.0 <= v <= 5.0:
            raise ValueError('Complexity score must be between 1.0 and 5.0')
        return v
```

## Error Handling Principles

### 1. Fail Fast

**Principle**: Detect and report errors as early as possible.

```python
class PricingService:
    def calculate_pricing(self, specification: PartSpecification) -> PricingResult:
        # Validate inputs immediately
        self._validate_specification(specification)

        # Continue with calculation
        base_cost = self._calculate_base_cost(specification)
        return self._apply_pricing_tiers(base_cost, specification)

    def _validate_specification(self, spec: PartSpecification) -> None:
        if spec.quantity <= 0:
            raise InvalidSpecificationError("Quantity must be positive")
        if spec.dimensions.volume_cm3() <= 0:
            raise InvalidSpecificationError("Dimensions must be positive")
```

### 2. Specific Exceptions

**Principle**: Use specific exception types for different error conditions.

```python
# Domain-specific exceptions
class PricingError(Exception):
    """Base exception for pricing-related errors"""
    pass

class InvalidSpecificationError(PricingError):
    """Raised when part specification is invalid"""
    pass

class PricingCalculationError(PricingError):
    """Raised when pricing calculation fails"""
    pass

class MaterialNotFoundError(PricingError):
    """Raised when specified material is not available"""
    pass
```

### 3. Error Boundaries

**Principle**: Handle errors at appropriate levels.

```python
# Domain layer: Raise domain-specific exceptions
class PricingService:
    def calculate_pricing(self, spec: PartSpecification) -> PricingResult:
        if not self._material_available(spec.material):
            raise MaterialNotFoundError(f"Material '{spec.material}' not available")

# Application layer: Convert to application errors
class PricingUseCase:
    def calculate_pricing(self, request: PricingRequest) -> PricingResponse:
        try:
            result = self._pricing_service.calculate_pricing(request.specification)
            return PricingResponse.from_result(result)
        except MaterialNotFoundError as e:
            raise ApplicationError(f"Pricing failed: {e}")

# Interface layer: Convert to HTTP responses
@router.post("/pricing")
async def calculate_pricing(request: PricingRequest):
    try:
        response = await pricing_use_case.calculate_pricing(request)
        return response
    except ApplicationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Testing Principles

### 1. Test Pyramid

**Principle**: Have many fast unit tests, fewer integration tests, and minimal end-to-end tests.

```
     ┌─────────────┐
     │     E2E     │ ← Few, slow, high-confidence
     └─────────────┘
   ┌─────────────────┐
   │  Integration    │ ← Some, medium speed
   └─────────────────┘
 ┌─────────────────────┐
 │      Unit           │ ← Many, fast, focused
 └─────────────────────┘
```

### 2. Test Isolation

**Principle**: Tests should not depend on each other or external state.

```python
# Good: Isolated test with mocks
def test_pricing_calculation():
    # Arrange
    mock_repository = Mock(spec=PricingRepository)
    mock_cost_service = Mock(spec=CostService)
    service = PricingService(mock_cost_service, mock_repository)

    specification = PartSpecification(
        material="aluminum",
        quantity=10,
        dimensions=Dimensions(100, 50, 25)
    )

    # Act
    result = service.calculate_pricing(specification)

    # Assert
    assert result.total_price.amount > 0
    mock_repository.save_calculation.assert_called_once()
```

### 3. Behavior-Driven Tests

**Principle**: Test behavior, not implementation details.

```python
# Good: Tests behavior
def test_pricing_service_applies_volume_discount():
    """When quantity is over 100, a volume discount should be applied"""
    # Given a large quantity order
    large_order = PartSpecification(material="steel", quantity=150, ...)

    # When calculating pricing
    result = pricing_service.calculate_pricing(large_order)

    # Then a volume discount should be applied
    assert result.volume_discount_applied is True
    assert result.discount_percentage > 0

# Bad: Tests implementation
def test_pricing_service_calls_volume_discount_calculator():
    """Tests internal implementation details"""
    result = pricing_service.calculate_pricing(specification)
    mock_volume_calculator.calculate_discount.assert_called_once()
```

## Performance Principles

### 1. Asynchronous by Default

**Principle**: Use async/await for I/O operations to improve concurrency.

```python
# Good: Async operations
class PricingService:
    async def calculate_pricing(self, spec: PartSpecification) -> PricingResult:
        # Run I/O operations concurrently
        material_cost, labor_cost = await asyncio.gather(
            self._get_material_cost(spec.material),
            self._get_labor_cost(spec.process)
        )

        return self._calculate_final_price(material_cost, labor_cost, spec)

# Repository operations are async
class PostgresPricingRepository:
    async def save_calculation(self, calculation: PricingCalculation) -> None:
        async with self._session() as session:
            session.add(calculation)
            await session.commit()
```

### 2. Caching Strategy

**Principle**: Cache expensive operations with appropriate TTL.

```python
from functools import lru_cache
from app.infrastructure.redis.cache import cache

class MaterialService:
    @cache(ttl=3600)  # Cache for 1 hour
    async def get_material_properties(self, material: str) -> MaterialProperties:
        # Expensive external API call
        return await self._external_api.get_material_data(material)

    @lru_cache(maxsize=128)  # In-memory cache for computed values
    def calculate_density(self, material: str, temperature: float) -> float:
        # Expensive calculation
        return self._physics_calculation(material, temperature)
```

### 3. Database Optimization

**Principle**: Optimize database queries and use appropriate indexing.

```python
# Use efficient queries with proper indexing
class PostgresPricingRepository:
    async def find_recent_calculations(
        self,
        material: str,
        limit: int = 10
    ) -> List[PricingCalculation]:
        query = """
        SELECT * FROM pricing_calculations
        WHERE material = $1
        ORDER BY created_at DESC
        LIMIT $2
        """
        # Ensure index on (material, created_at)
        return await self._execute_query(query, material, limit)
```

## Security Principles

### 1. Defense in Depth

**Principle**: Multiple layers of security controls.

```python
# Input validation at multiple layers
class PricingController:
    async def calculate_pricing(
        self,
        request: PricingRequest,  # ← Pydantic validation
        current_user: User = Depends(get_current_user),  # ← Authentication
        _: None = Depends(rate_limiter),  # ← Rate limiting
    ):
        # Authorization check
        if not current_user.has_permission("pricing:calculate"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Business logic validation
        validated_spec = self._pricing_service.validate_specification(request.specification)

        return await self._pricing_service.calculate_pricing(validated_spec)
```

### 2. Principle of Least Privilege

**Principle**: Grant minimum necessary permissions.

```python
# Role-based access control
class User:
    def __init__(self, roles: List[str]):
        self.roles = roles

    def has_permission(self, permission: str) -> bool:
        required_role = PERMISSION_ROLE_MAPPING.get(permission)
        return required_role in self.roles

# Fine-grained permissions
PERMISSION_ROLE_MAPPING = {
    "pricing:calculate": "user",
    "pricing:admin": "admin",
    "system:health": "monitor",
}
```

### 3. Secure by Default

**Principle**: Default configurations should be secure.

```python
class SecuritySettings(BaseSettings):
    # Secure defaults
    jwt_expire_minutes: int = 15  # Short token lifetime
    max_requests_per_minute: int = 60  # Rate limiting
    require_https: bool = True  # Force HTTPS
    password_min_length: int = 12  # Strong passwords

    # Environment-specific overrides
    class Config:
        env_prefix = "SECURITY_"
```

## Monitoring and Observability Principles

### 1. Structured Logging

**Principle**: Use structured logging for better observability.

```python
import structlog

logger = structlog.get_logger(__name__)

class PricingService:
    async def calculate_pricing(self, spec: PartSpecification) -> PricingResult:
        logger.info(
            "pricing_calculation_started",
            material=spec.material,
            quantity=spec.quantity,
            customer_id=spec.customer_id
        )

        try:
            result = await self._perform_calculation(spec)

            logger.info(
                "pricing_calculation_completed",
                calculation_id=result.id,
                total_price=float(result.total_price.amount),
                duration_ms=result.calculation_time_ms
            )

            return result
        except Exception as e:
            logger.error(
                "pricing_calculation_failed",
                error=str(e),
                material=spec.material,
                quantity=spec.quantity
            )
            raise
```

### 2. Health Checks

**Principle**: Implement comprehensive health monitoring.

```python
class HealthService:
    async def check_detailed_health(self) -> HealthStatus:
        checks = await asyncio.gather(
            self._check_database_connectivity(),
            self._check_external_api_availability(),
            self._check_cache_connectivity(),
            return_exceptions=True
        )

        return HealthStatus(
            overall_status="healthy" if all(checks) else "unhealthy",
            service_checks=dict(zip(self.SERVICE_NAMES, checks)),
            timestamp=datetime.utcnow()
        )
```

These design principles work together to create a maintainable, scalable, and robust FastAPI application that can evolve with changing business requirements while maintaining code quality and system reliability.
