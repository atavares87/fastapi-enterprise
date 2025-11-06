# Development Workflow

## Common Commands

```bash
make install        # Install dependencies with uv
make start-dev      # Run development server
make test           # Run all tests
make test-unit      # Fast tests (pure functions)
make format         # Format code
make lint           # Check code quality
make check-all      # Run all checks
make db-upgrade     # Run migrations
```

## Adding a New Feature

Follow the layered architecture pattern:

### 1. Domain Layer (Bottom-Up)

Start with pure business logic (no I/O).

```bash
# Create domain models
touch app/domain/model/new_feature_models.py

# Create pure functions
touch app/domain/core/new_feature/calculations.py
```

**Test immediately** (no mocks needed!):
```bash
pytest tests/unit/domains/test_new_feature_calculations.py -v
```

### 2. Repository Layer

Create data access abstraction.

```bash
touch app/repository/new_feature_repository.py
```

Implement:
- `get_*()` methods for queries
- `save()`, `update()`, `delete()` for mutations
- Return domain models, not database entities

### 3. Service Layer

Create business orchestration.

```bash
touch app/service/new_feature_service.py
```

Pattern:
1. Constructor injection (repositories)
2. Async methods for business operations
3. Call domain core functions
4. Use repositories for data
5. Return DTOs

### 4. DTO Layer

Create API contracts.

```bash
touch app/dto/request/new_feature_request.py
touch app/dto/response/new_feature_response.py
```

Use Pydantic models with validation.

### 5. Controller Layer

Create HTTP endpoints.

```bash
touch app/controller/new_feature_controller.py
```

Pattern:
- Create router with `APIRouter()`
- Define endpoints with `@router.post()`, etc.
- Inject service via `Depends()`
- Handle exceptions → HTTP errors
- Minimal logic (delegate to service)

### 6. Dependency Injection

Wire everything together.

```python
# In app/config/dependencies.py

@lru_cache()
def get_new_feature_repository() -> NewFeatureRepository:
    return NewFeatureRepository()

@lru_cache()
def get_new_feature_service() -> NewFeatureService:
    return NewFeatureService(
        repository=get_new_feature_repository()
    )
```

### 7. Register Controller

```python
# In app/main.py
from app.controller.new_feature_controller import router as new_feature_router

app.include_router(new_feature_router)
```

### 8. Write Tests

```bash
# Domain tests (pure functions, no mocks)
tests/unit/domains/test_new_feature_calculations.py

# Service tests (mock repositories)
tests/unit/test_new_feature_service.py

# Controller tests (mock services)
tests/integration/test_new_feature_api.py
```

### 9. Verify

```bash
make check-all      # Format, lint, type-check
make test           # All tests
make start-dev      # Test manually
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes, test, commit frequently
git add .
git commit -m "feat: add new feature"

# Before pushing
make check-all
make test

# Push and create PR
git push origin feature/new-feature
```

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(pricing): add bulk discount calculation

Implement volume-based discounts for quantities > 100.
Uses tiered discount rates from configuration.

Closes #123
```

## Pull Request Checklist

- [ ] All tests pass
- [ ] No linter errors
- [ ] Type hints on all new code
- [ ] Docstrings on public functions/classes
- [ ] Tests for new functionality
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
