# Development Documentation

## Quick Start

```bash
make full-setup    # Complete setup
make start-dev     # Start app
make test          # Run tests
make check-all     # Format & lint
```

## Guides

1. **[Getting Started](getting-started.md)** - Project setup, IDE configuration, first run

2. **[Adding Features](adding-features.md)** - Step-by-step feature development workflow

3. **[Domain Development](domain-development.md)** - Creating business logic with pure functions

## Development Workflow

### 1. Create Domain Models

```python
# app/domain/model/your_feature_models.py
@dataclass(frozen=True)
class YourEntity:
    """Immutable domain entity."""
    id: UUID
    name: str
    value: Decimal
```

### 2. Create Pure Business Logic (Functional Core)

```python
# app/domain/core/your_feature/calculations.py
def calculate_something(input_data: InputData, config: Config) -> Result:
    """Pure function - no I/O, deterministic, testable without mocks."""
    return Result(...)
```

### 3. Create Repository (Data Access)

```python
# app/repository/your_feature_repository.py
class YourFeatureRepository:
    """Data access layer - analogous to Spring @Repository."""

    async def get_data(self) -> list[YourEntity]:
        """Fetch data from database."""
        return await self._fetch_from_database()

    async def save(self, entity: YourEntity) -> None:
        """Save entity to database."""
        await self._save_to_database(entity)
```

### 4. Create Service (Business Orchestration)

```python
# app/service/your_feature_service.py
class YourFeatureService:
    """Business logic orchestration - analogous to Spring @Service."""

    def __init__(
        self,
        your_feature_repository: YourFeatureRepository,
        other_repository: OtherRepository,
    ):
        self.your_feature_repository = your_feature_repository
        self.other_repository = other_repository

    async def process(self, request: RequestDTO) -> ResponseDTO:
        # 1. Fetch data from repositories
        data = await self.your_feature_repository.get_data()
        config = await self.other_repository.get_config()

        # 2. Execute business logic (functional core)
        result = calculate_something(data, config)

        # 3. Persist results
        await self.your_feature_repository.save(result)

        # 4. Return response
        return ResponseDTO.from_domain(result)
```

### 5. Create Controller (HTTP Endpoints)

```python
# app/controller/your_feature_controller.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/your-feature", tags=["YourFeature"])

@router.post("/process")
async def process(
    request: RequestDTO,
    service: YourFeatureService = Depends(get_your_feature_service)
) -> ResponseDTO:
    """HTTP endpoint - analogous to Spring @RestController."""
    return await service.process(request)
```

### 6. Wire Dependencies (Dependency Injection)

```python
# app/config/dependencies.py
from functools import lru_cache

@lru_cache()
def get_your_feature_repository() -> YourFeatureRepository:
    return YourFeatureRepository()

@lru_cache()
def get_your_feature_service() -> YourFeatureService:
    return YourFeatureService(
        your_feature_repository=get_your_feature_repository(),
        other_repository=get_other_repository(),
    )
```

### 7. Register Controller

```python
# app/main.py
from app.controller.your_feature_controller import router as your_feature_router

app.include_router(your_feature_router)
```

### 8. Write Tests

```python
# tests/unit/domains/test_your_feature_calculations.py
def test_calculate_something():
    """Test pure function - no mocks needed!"""
    result = calculate_something(input_data, config)
    assert result.value == expected_value

# tests/unit/test_your_feature_service.py
async def test_service():
    """Test service - mock repositories."""
    mock_repo = Mock(spec=YourFeatureRepository)
    service = YourFeatureService(mock_repo)

    result = await service.process(request)

    assert result.success
    mock_repo.get_data.assert_called_once()

# tests/integration/test_your_feature_api.py
async def test_endpoint(client):
    """Test HTTP endpoint - test full flow."""
    response = await client.post("/api/v1/your-feature/process", json={...})
    assert response.status_code == 200
```

## Architecture Overview

### Layered Architecture (Spring Boot Style)

```
Controller → Service → Repository → Domain
```

**Controller**: HTTP endpoints (@RestController)
- Handle HTTP requests/responses
- Convert DTOs
- Delegate to services

**Service**: Business orchestration (@Service)
- Coordinate repositories
- Execute business workflows
- Call domain core functions

**Repository**: Data access (@Repository)
- Abstract database access
- Query and persist data
- Return domain models

**Domain**: Core business logic
- **Models**: Entities, value objects, enums
- **Core**: Pure functions (functional core)

### Functional Core Principles

Pure functions in `domain/core/`:
- ✅ Same input → same output (deterministic)
- ✅ No side effects
- ✅ No I/O (no database, no HTTP, no logging)
- ✅ All data passed as parameters
- ✅ Testable without mocks!

## Common Commands

### Development
```bash
make start-dev        # Run development server
make format           # Format code with Black
make lint             # Lint with Ruff
make type-check       # Type check with MyPy
make check-all        # Run all checks
```

### Testing
```bash
make test             # Run all tests
make test-unit        # Run unit tests (fast!)
make test-integration # Run integration tests
make test-watch       # Watch mode
```

### Database
```bash
make db-upgrade       # Run migrations
make db-downgrade     # Rollback migrations
make db-revision      # Create migration
```

## Best Practices

### Code Organization
- ✅ One class per file
- ✅ Small, focused modules
- ✅ Clear layer boundaries
- ❌ Don't mix layers

### Testing
- ✅ Test pure functions directly (no mocks!)
- ✅ Mock repositories in service tests
- ✅ Test HTTP in integration tests
- ❌ Don't mock domain core functions

### Dependencies
- ✅ Dependencies flow downward
- ✅ Use dependency injection
- ✅ Inject interfaces, not implementations
- ❌ No circular dependencies

## Resources

- [Adding Features Guide](adding-features.md) - Detailed feature development
- [Domain Development Guide](domain-development.md) - Creating business logic
- [Architecture Docs](../architecture/README.md) - Complete architecture reference
- [Cursor Rules](../../.cursor/rules/) - Development guidelines
