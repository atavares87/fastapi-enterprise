# Development Guide

This guide provides detailed information for developers working on the FastAPI Enterprise Application.

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose
- Git

### Initial Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd fastapi_enterprise
   ```

2. **Run the setup script:**

   ```bash
   python setup.py setup
   ```

3. **Configure environment:**

   ```bash
   # Edit .env file with your settings
   cp .env.example .env
   # Generate a secret key
   python setup.py secret
   ```

4. **Start services:**

   ```bash
   make docker-compose-up
   ```

5. **Run migrations:**

   ```bash
   make db-upgrade
   ```

6. **Start development server:**
   ```bash
   make dev
   ```

## Development Workflow

### Code Quality

The project enforces strict code quality standards:

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Security checks
make security-check

# Run all checks
make check-all
```

### Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit          # Fast unit tests
make test-integration   # Integration tests with real databases
make test-api          # End-to-end API tests

# Run with coverage
make test-coverage

# Watch mode for TDD
make test-watch
```

### Database Management

```bash
# Create new migration
make db-revision

# Apply migrations
make db-upgrade

# Rollback one migration
make db-downgrade

# Reset database (⚠️ destroys data)
make db-reset
```

## Architecture Guidelines

### Hexagonal Architecture

The application follows hexagonal architecture principles:

- **Core Domain**: Pure business logic in `service.py` files
- **Ports**: Interfaces defined in `repository.py` files
- **Adapters**: Implementations in `adapters/` directories
- **HTTP Layer**: FastAPI routes in `router.py` files

### Directory Structure

```
app/
├── core/              # Cross-cutting concerns
│   ├── config.py      # Application configuration
│   ├── database.py    # Database connections
│   ├── logging.py     # Structured logging
│   ├── security.py    # JWT and password handling
│   └── celery_app.py  # Background task configuration
├── modules/           # Feature modules
│   └── auth/          # Authentication module
│       ├── domain.py      # Domain models
│       ├── schemas.py     # Pydantic DTOs
│       ├── models.py      # Database models
│       ├── repository.py  # Data access interface
│       ├── service.py     # Business logic
│       ├── router.py      # HTTP endpoints
│       ├── adapters/      # Infrastructure implementations
│       ├── dependencies.py # FastAPI dependencies
│       └── exceptions.py  # Domain exceptions
```

### Adding New Features

1. **Create a new module:**

   ```bash
   mkdir -p app/modules/new_feature/{adapters}
   ```

2. **Follow the module pattern:**

   - `domain.py` - Define domain models
   - `schemas.py` - Create Pydantic schemas for API
   - `models.py` - Define database models
   - `repository.py` - Define data access interface
   - `service.py` - Implement business logic
   - `router.py` - Create FastAPI routes
   - `adapters/` - Implement infrastructure adapters
   - `dependencies.py` - Define FastAPI dependencies
   - `exceptions.py` - Define domain-specific exceptions

3. **Add tests:**

   ```bash
   mkdir -p tests/{unit,integration,api}/modules/new_feature
   ```

4. **Register the router:**
   ```python
   # In app/main.py
   from app.modules.new_feature.router import router as new_feature_router
   app.include_router(new_feature_router, prefix="/new-feature", tags=["New Feature"])
   ```

## Development Patterns

### Repository Pattern

Always define repository interfaces as protocols:

```python
# repository.py
from typing import Protocol
from app.modules.feature.domain import Entity

class EntityRepository(Protocol):
    async def create(self, data: EntityCreate) -> Entity:
        ...

    async def get_by_id(self, entity_id: int) -> Optional[Entity]:
        ...
```

Implement concrete adapters:

```python
# adapters/postgres_repo.py
class PostgresEntityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: EntityCreate) -> Entity:
        # Implementation
        pass
```

### Service Layer

Keep business logic in service functions:

```python
# service.py
async def create_entity(
    data: EntityCreate,
    repository: EntityRepository,
) -> Entity:
    # Validate business rules
    if await repository.exists_by_name(data.name):
        raise EntityAlreadyExistsError(data.name)

    # Create entity
    return await repository.create(data)
```

### FastAPI Routes

Keep routes thin - delegate to services:

```python
# router.py
@router.post("/entities", response_model=EntityResponse)
async def create_entity(
    data: EntityCreate,
    repository: EntityRepository = Depends(get_entity_repository),
) -> EntityResponse:
    try:
        entity = await service.create_entity(data, repository)
        return EntityResponse.from_domain(entity)
    except EntityAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Error Handling

Define domain-specific exceptions:

```python
# exceptions.py
class EntityError(Exception):
    """Base exception for entity operations."""
    pass

class EntityNotFoundError(EntityError):
    """Entity not found."""
    pass

class EntityAlreadyExistsError(EntityError):
    """Entity already exists."""
    pass
```

Handle exceptions in routes:

```python
@router.get("/entities/{entity_id}")
async def get_entity(entity_id: int, ...):
    try:
        entity = await service.get_entity(entity_id, repository)
        return EntityResponse.from_domain(entity)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Entity not found")
```

### Testing Strategies

#### Unit Tests

Test business logic in isolation:

```python
@pytest.mark.unit
async def test_create_entity_success():
    # Arrange
    repository = InMemoryEntityRepository()
    entity_data = EntityCreate(name="test")

    # Act
    entity = await service.create_entity(entity_data, repository)

    # Assert
    assert entity.name == "test"
```

#### Integration Tests

Test with real databases:

```python
@pytest.mark.integration
async def test_entity_repository_crud(test_db_session):
    # Test actual database operations
    repository = PostgresEntityRepository(test_db_session)
    # ... test implementation
```

#### API Tests

Test HTTP endpoints:

```python
@pytest.mark.api
def test_create_entity_endpoint(test_client):
    response = test_client.post(
        "/entities",
        json={"name": "test entity"}
    )
    assert response.status_code == 201
```

## Database Development

### Creating Migrations

1. **Make model changes:**

   ```python
   # In models.py
   class NewModel(Base):
       __tablename__ = "new_table"
       id = Column(Integer, primary_key=True)
       name = Column(String, nullable=False)
   ```

2. **Generate migration:**

   ```bash
   make db-revision
   # Enter a descriptive message
   ```

3. **Review generated migration:**

   ```bash
   # Check alembic/versions/*.py
   ```

4. **Apply migration:**
   ```bash
   make db-upgrade
   ```

### Migration Best Practices

- Always review generated migrations
- Test migrations on development data
- Write both upgrade and downgrade functions
- Use descriptive migration messages
- Add indexes for performance
- Consider data migration needs

### Database Connection Management

- Use dependency injection for database sessions
- Always use async operations
- Handle connection errors gracefully
- Use transactions for multi-step operations
- Test with both PostgreSQL and SQLite (for tests)

## Background Tasks

### Creating Celery Tasks

```python
# In modules/feature/tasks.py
from app.core.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def process_data(self, data_id: int):
    try:
        # Process data
        return {"status": "completed", "data_id": data_id}
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Task Best Practices

- Make tasks idempotent
- Handle failures gracefully
- Use retry mechanisms
- Log task progress
- Keep tasks focused and small
- Test tasks in eager mode

## Monitoring and Debugging

### Logging

Use structured logging throughout the application:

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "Entity created",
    entity_id=entity.id,
    entity_name=entity.name,
    user_id=current_user.id,
)
```

### Health Checks

Monitor application health:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
```

### Performance Monitoring

- Monitor response times in logs
- Use database query logging in development
- Profile slow endpoints
- Monitor memory usage
- Track background task performance

## Deployment

### Environment Configuration

Different configurations for each environment:

```bash
# Development
DEBUG=true
DATABASE_URL=postgresql+asyncpg://...

# Production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://prod-db...
```

### Docker Deployment

```bash
# Build production image
make docker-build

# Run with Docker Compose
make docker-compose-up

# Deploy to Kubernetes
make k8s-deploy
```

### CI/CD Integration

The project includes GitHub Actions workflow:

```yaml
# .github/workflows/ci.yml
name: CI/CD
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make ci
```

## Troubleshooting

### Common Issues

1. **Database connection errors:**

   - Check DATABASE_URL in .env
   - Ensure PostgreSQL is running
   - Verify credentials

2. **Migration conflicts:**

   ```bash
   # Reset migrations (⚠️ development only)
   make db-reset
   ```

3. **Import errors:**

   - Check Python path
   - Verify uv environment activation
   - Check circular imports

4. **Test failures:**
   - Run tests individually for debugging
   - Check test database setup
   - Verify test fixtures

### Getting Help

- Check the logs for error details
- Review the .cursorrules file for coding standards
- Use the GitHub issues for bug reports
- Consult the API documentation at `/docs`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the development workflow
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

### Code Review Checklist

- [ ] Follows architectural patterns
- [ ] Includes comprehensive tests
- [ ] Has proper error handling
- [ ] Updates documentation
- [ ] Passes all quality checks
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
