# FAStAPI Enterprise Application Dockerfile
# Multi-stage build for optimized production image

# Build stage - install dependencies and build application
FROM python:3.11-slim AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fASter dependency resolution
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files and README (needed for package build)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Production stage - create minimal runtime image
FROM python:3.11-slim AS production

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    ENV=production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini ./

# Create necessary directories and set permissions
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run production server
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]


# Development stage - includes dev dependencies and debugging tools
FROM builder AS development

# Install development dependencies
RUN uv sync --frozen

# Install additional development tools
RUN apt-get update && apt-get install -y \
    git \
    htop \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set development environment
ENV ENV=development

# Copy application code
COPY app/ ./app/
COPY tests/ ./tests/
COPY alembic/ ./alembic/
COPY alembic.ini Makefile ./

# Create directories for development
RUN mkdir -p logs

# Expose port and debugger port
EXPOSE 8000 5678

# Development command - run with reload
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]


# Testing stage - for running tests in CI/CD
FROM development AS testing

# Set testing environment
ENV ENV=testing

# Run tests by default (pytest config is in pyproject.toml)
CMD ["pytest", "tests/", "-v", "--cov=app", "--cov-report=term-missing"]
