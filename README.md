# FastAPI Enterprise Application

A production-ready FastAPI application built with hexagonal architecture (ports & adapters) and the Functional Core, Imperative Shell (FCIS) pattern. This project demonstrates enterprise-grade software development practices with comprehensive testing, type safety, and scalable deployment options.

## 🏗️ Architecture

### Hexagonal Architecture + Functional Core

This application implements a clean separation between business logic and infrastructure concerns:

- **Functional Core**: Pure business logic without side effects
- **Imperative Shell**: All I/O operations, database calls, and external integrations
- **Ports**: Interfaces that define contracts for external interactions
- **Adapters**: Concrete implementations of ports for specific technologies

### Feature-Based Organization

The codebase is organized by business domains rather than technical layers:

```
app/
├── core/           # Cross-cutting concerns (config, database, logging)
├── modules/        # Feature-based modules
│   ├── auth/       # Authentication domain
│   ├── users/      # User management domain
│   └── orders/     # Order processing domain (example)
```

Each module contains:

- `domain.py` - Domain models and business entities
- `schemas.py` - Pydantic models for API requests/responses
- `models.py` - Database models (SQLAlchemy/Beanie)
- `repository.py` - Data access interfaces (ports)
- `service.py` - Business logic (functional core)
- `router.py` - FastAPI routes (HTTP adapter)
- `adapters/` - Infrastructure implementations
- `dependencies.py` - FastAPI dependency injection
- `exceptions.py` - Domain-specific exceptions

## 🚀 Features

### Core Features

- ✅ **JWT Authentication** with access and refresh tokens
- ✅ **User Management** with profile and password management
- ✅ **Multi-Database Support** (PostgreSQL + MongoDB)
- ✅ **Redis Caching** for improved performance
- ✅ **Background Tasks** with Celery
- ✅ **Structured Logging** with request tracing
- ✅ **Type Safety** with mypy and Pydantic
- ✅ **Comprehensive Testing** (unit, integration, API)
- ✅ **API Documentation** with OpenAPI/Swagger
- ✅ **Health Checks** for all services

### Development Features

- ✅ **uv Package Management** for fast dependency resolution
- ✅ **Pre-commit Hooks** for code quality
- ✅ **Docker & Docker Compose** for local development
- ✅ **Kubernetes Manifests** for production deployment
- ✅ **Makefile** with common development tasks
- ✅ **Cursor Rules** for AI-assisted development

## 📋 Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker and Docker Compose
- PostgreSQL 15+
- MongoDB 5+
- Redis 7+

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fastapi_enterprise
make setup
```

This will:

- Install all dependencies with uv
- Set up pre-commit hooks
- Create `.env` file from template

### 2. Configure Environment

Update `.env` file with your configuration:

```env
# Database URLs
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fastapi_enterprise
MONGO_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here

# Email settings (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Start Services

```bash
# Start database services
make docker-compose-up

# Run database migrations
make db-upgrade

# Start development server
make dev
```

### 4. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Celery Flower**: http://localhost:5555 (if running)

## 🧪 Testing

The project includes comprehensive testing at multiple levels:

```bash
# Run all tests
make test

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-api          # API tests only

# Run tests with coverage
make test-coverage

# Watch mode for development
make test-watch
```

### Test Structure

```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Tests with real databases
├── api/           # End-to-end API tests
└── conftest.py    # Shared pytest fixtures
```

## 🔧 Development

### Code Quality

The project enforces high code quality standards:

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

### Database Management

```bash
# Create new migration
make db-revision

# Apply migrations
make db-upgrade

# Rollback migration
make db-downgrade

# Reset database (⚠️ destroys data)
make db-reset
```

### Background Tasks

```bash
# Start Celery worker
make celery-worker

# Start Celery beat scheduler
make celery-beat

# Start Flower monitoring
make celery-flower

# Purge all tasks
make celery-purge
```

## 🐳 Docker Deployment

### Local Development

```bash
# Build and run with Docker
make docker-run

# Use Docker Compose for full stack
make docker-compose-up
```

### Production Build

```bash
# Build production image
make docker-build

# Tag for registry
docker tag fastapi-enterprise:latest your-registry.com/fastapi-enterprise:v1.0.0

# Push to registry
docker push your-registry.com/fastapi-enterprise:v1.0.0
```

## ☸️ Kubernetes Deployment

The project includes Kubernetes manifests for production deployment:

```bash
# Deploy to Kubernetes
make k8s-deploy

# Check deployment status
make k8s-status

# Delete resources
make k8s-delete
```

### Kubernetes Resources

- **Deployment**: Web application pods
- **Service**: Internal load balancing
- **Ingress**: External traffic routing
- **ConfigMap**: Application configuration
- **Secret**: Sensitive data (database URLs, API keys)
- **PersistentVolumeClaim**: Database storage

## 📚 API Documentation

The API is fully documented with OpenAPI 3.0. Visit `/docs` for interactive documentation or `/redoc` for alternative documentation.

### Authentication Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - User logout
- `POST /auth/forgot-password` - Password reset request
- `POST /auth/reset-password` - Password reset confirmation

### User Management Endpoints

- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `POST /users/me/change-password` - Change password
- `GET /users/{user_id}` - Get user by ID (admin only)

### Health Check Endpoints

- `GET /health` - Application health status
- `GET /health/db` - Database health status

## 🔒 Security

### Authentication & Authorization

- JWT tokens with configurable expiration
- Secure password hashing with bcrypt
- Role-based access control
- Session management with refresh tokens

### Security Headers

- CORS configuration
- Security headers middleware
- Request rate limiting
- Input validation and sanitization

### Data Protection

- Environment-based configuration
- Secrets management
- Database connection encryption
- Audit logging for sensitive operations

## 📊 Monitoring & Observability

### Logging

- Structured JSON logging
- Request/response logging
- Error tracking with context
- Configurable log levels

### Health Checks

- Application readiness and liveness probes
- Database connectivity checks
- External service health monitoring
- Kubernetes-compatible health endpoints

### Metrics (Future Enhancement)

- Prometheus metrics endpoint
- Custom business metrics
- Performance monitoring
- Alerting integration

## 🔄 CI/CD

### GitHub Actions (Example)

```yaml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: make ci
```

### Pre-commit Hooks

Automatically run on every commit:

- Code formatting (Black, isort)
- Linting (ruff)
- Type checking (mypy)
- Security scanning (bandit)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run quality checks: `make check-all`
5. Run tests: `make test`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Development Guidelines

- Follow the established architecture patterns
- Write tests for all new functionality
- Update documentation as needed
- Use type hints for all functions
- Follow the existing code style

## 📖 Additional Resources

### Architecture References

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Functional Core, Imperative Shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

### FastAPI Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

### Tools Documentation

- [uv Package Manager](https://github.com/astral-sh/uv)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI community for the excellent framework
- Pydantic team for robust data validation
- SQLAlchemy team for the powerful ORM
- All contributors and maintainers

---

**Built with ❤️ using FastAPI, Python, and enterprise-grade development practices.**
