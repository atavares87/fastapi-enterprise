# Getting Started

## Overview

This guide will help you set up your development environment and get the FastAPI Enterprise application running locally. Follow these steps to go from zero to a fully functional development setup.

## Prerequisites

### Required Software

- **Python 3.11+**: The application requires Python 3.11 or higher
- **Docker & Docker Compose**: For running services (PostgreSQL, MongoDB, Redis)
- **Git**: For version control
- **uv**: Fast Python package installer and dependency manager

### Optional but Recommended

- **Make**: For running development commands
- **curl or httpx**: For testing API endpoints
- **VS Code/Cursor**: With Python and Docker extensions
- **pgAdmin**: PostgreSQL administration tool
- **MongoDB Compass**: MongoDB administration tool
- **Redis Insight**: Redis administration tool

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/fastapi-enterprise.git
cd fastapi-enterprise
```

### 2. Install uv (if not already installed)

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Via pip
pip install uv
```

### 3. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your configuration
# The default values should work for local development
```

**Key Environment Variables**:

```bash
# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database URLs (defaults work with docker-compose)
POSTGRES_URL=postgresql+asyncpg://postgres:password@localhost:5432/fastapi_enterprise
MONGODB_URL=mongodb://localhost:27017/fastapi_enterprise
REDIS_URL=redis://localhost:6379

# External API Keys (optional for basic functionality)
MATERIAL_API_KEY=your-api-key
SHIPPING_API_KEY=your-api-key
```

### 4. Start Required Services

```bash
# Start all services using docker-compose
make docker-up

# Or manually with docker-compose
docker-compose up -d postgres mongodb redis
```

**Verify services are running**:

```bash
# Check service status
docker-compose ps

# Should show postgres, mongodb, and redis as "Up"
```

### 5. Install Dependencies and Set Up Development Environment

```bash
# Install all dependencies (including dev dependencies)
make install-dev

# Or manually with uv
uv sync --dev
```

### 6. Set Up the Database

```bash
# Run database migrations
make db-upgrade

# Or manually
uv run alembic upgrade head
```

### 7. Verify Installation

```bash
# Run all tests to ensure everything is working
make test-all

# Check code quality
make check-all

# Start the development server
make dev

# Or manually
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Test the Application

Open your browser and navigate to:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

**Test with curl**:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed

# Get available materials
curl http://localhost:8000/api/v1/pricing/materials

# Test pricing calculation
curl -X POST http://localhost:8000/api/v1/pricing \
  -H "Content-Type: application/json" \
  -d '{
    "material": "aluminum",
    "quantity": 10,
    "dimensions": {
      "length_mm": 100,
      "width_mm": 50,
      "height_mm": 25
    },
    "geometric_complexity_score": 2.5,
    "process": "cnc"
  }'
```

## Development Workflow

### Daily Development Commands

```bash
# Start development server with auto-reload
make dev

# Run tests (fast unit tests only)
make test

# Run full test suite
make test-all

# Check code quality (linting, type checking)
make check-all

# Format code
make format

# Clean up and reset environment
make clean
```

### Code Quality Checks

The project uses several tools to maintain code quality:

```bash
# Run individual quality checks
make lint          # Ruff linting
make type-check     # MyPy type checking
make format-check   # Black code formatting check
make security-check # Bandit security scanning

# Fix common issues automatically
make format         # Format code with Black
make lint-fix       # Fix auto-fixable linting issues
```

### Testing

```bash
# Run different types of tests
make test           # Unit tests only (fast)
make test-integration  # Integration tests
make test-api       # API endpoint tests
make test-contract  # Contract tests
make test-all       # All tests

# Run tests with coverage
make test-coverage

# Run tests in parallel (faster)
make test-parallel
```

## Project Structure Overview

Understanding the project structure will help you navigate and contribute effectively:

```
fastapi-enterprise/
├── app/                    # Main application code
│   ├── api/               # FastAPI routes and controllers
│   ├── core/              # Application configuration and utilities
│   ├── domains/           # Business logic (pricing, cost)
│   └── infrastructure/    # Database, external APIs, tasks
├── tests/                 # Test suite
│   ├── unit/             # Fast, isolated tests
│   ├── integration/      # Database and service tests
│   ├── api/              # HTTP endpoint tests
│   └── contract/         # API contract tests
├── docs/                  # Comprehensive documentation
├── migrations/            # Database migration files
└── scripts/              # Utility scripts
```

### Key Directories for Development

- **`app/core/domain/`**: Add new business logic and domain models here
- **`app/adapter/inbound/web/v1/`**: Add new API endpoints here
- **`app/adapter/outbound/`**: Add new database repositories and external integrations
- **`tests/`**: Add tests that mirror your application structure

## Common Development Tasks

### Adding a New API Endpoint

1. **Define the domain model** in `app/core/domain/[domain]/models.py`
2. **Create the service logic** in `app/core/domain/[domain]/services.py`
3. **Add the API endpoint** in `app/adapter/inbound/web/v1/[endpoint].py`
4. **Write tests** in `tests/unit/`, `tests/api/`, etc.
5. **Update documentation** if needed

### Working with Databases

```bash
# Create a new migration
make db-revision MESSAGE="Add new table"

# Apply migrations
make db-upgrade

# Rollback migrations
make db-downgrade

# Reset database (warning: destroys data)
make db-reset
```

### Background Tasks

```bash
# Start Celery worker for background tasks
make celery-worker

# Start Celery beat for scheduled tasks
make celery-beat

# Monitor tasks with Flower
make celery-flower
# Then visit http://localhost:5555
```

## Development Tools Setup

### VS Code/Cursor Configuration

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.testing.unittestEnabled": false,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### Git Hooks Setup

```bash
# Install pre-commit hooks (runs automatically on commit)
make install-hooks

# Run pre-commit hooks manually
make pre-commit

# Skip hooks for emergency commits (use sparingly)
git commit --no-verify -m "Emergency fix"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

```bash
# Check if services are running
docker-compose ps

# Restart services
docker-compose restart postgres mongodb redis

# Check logs
docker-compose logs postgres
```

#### 2. Dependencies Issues

```bash
# Sync dependencies
uv sync --dev

# Clear cache and reinstall
rm -rf .venv
uv sync --dev
```

#### 3. Migration Issues

```bash
# Check migration status
uv run alembic current

# Reset to a specific migration
uv run alembic downgrade <revision>

# Generate a new migration
uv run alembic revision --autogenerate -m "Description"
```

#### 4. Test Failures

```bash
# Run tests with verbose output
make test-verbose

# Run a specific test
uv run pytest tests/unit/domains/test_pricing/test_services.py::test_calculate_pricing -v

# Run tests with debugging
uv run pytest tests/ -v -s --pdb
```

#### 5. Performance Issues

```bash
# Check service health
curl http://localhost:8000/health/detailed

# Monitor database connections
docker-compose exec postgres psql -U postgres -d fastapi_enterprise -c "SELECT * FROM pg_stat_activity;"

# Check Redis memory usage
docker-compose exec redis redis-cli info memory
```

### Environment Debugging

```bash
# Check environment variables
uv run python -c "from app.core.config import settings; print(settings.dict())"

# Test database connections
uv run python -c "
from app.adapter.outbound.persistence.connection import PostgreSQLConnection
from app.core.config import settings
import asyncio

async def test():
    conn = PostgreSQLConnection(settings.postgres_url)
    session = await conn.get_session()
    print('PostgreSQL connection successful')
    await session.close()

asyncio.run(test())
"
```

### Performance Profiling

```bash
# Profile API endpoints
uv run python -m cProfile -o profile.stats scripts/profile_api.py

# Analyze profile
uv run python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"
```

## Next Steps

Once you have the application running locally:

1. **Explore the API Documentation**: Visit http://localhost:8000/docs
2. **Read the Architecture Guide**: See [Application Architecture](../architecture/application-architecture.md)
3. **Learn about Adding Features**: See [Adding New Features](adding-features.md)
4. **Understand the Domain Structure**: See [Domain Development](domain-development.md)
5. **Set up your IDE**: Configure your editor with the project's code style and testing setup

## Getting Help

- **Documentation**: Check the `docs/` directory for comprehensive guides
- **Issues**: Create GitHub issues for bugs or feature requests
- **Architecture Questions**: See the [Architecture Documentation](../architecture/)
- **API Questions**: Use the interactive docs at http://localhost:8000/docs

Welcome to the FastAPI Enterprise project! Happy coding! 🚀
