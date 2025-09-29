# Docker Deployment Guide

## Overview

This guide covers containerization and deployment of the FastAPI Enterprise application using Docker and Docker Compose. We provide configurations for development, staging, and production environments with best practices for security, performance, and maintainability.

## Docker Architecture

### Multi-Service Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx/Traefik]
    end

    subgraph "Application Services"
        APP1[FastAPI App 1]
        APP2[FastAPI App 2]
        WORKER1[Celery Worker 1]
        WORKER2[Celery Worker 2]
        BEAT[Celery Beat]
        FLOWER[Flower Monitor]
    end

    subgraph "Data Services"
        POSTGRES[(PostgreSQL)]
        MONGODB[(MongoDB)]
        REDIS[(Redis)]
    end

    subgraph "Monitoring"
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
    end

    LB --> APP1
    LB --> APP2
    APP1 --> POSTGRES
    APP1 --> MONGODB
    APP1 --> REDIS
    APP2 --> POSTGRES
    APP2 --> MONGODB
    APP2 --> REDIS
    WORKER1 --> POSTGRES
    WORKER1 --> MONGODB
    WORKER1 --> REDIS
    WORKER2 --> POSTGRES
    WORKER2 --> MONGODB
    WORKER2 --> REDIS
    BEAT --> REDIS
    FLOWER --> REDIS
```

## Dockerfile Configuration

### Multi-Stage Production Dockerfile

**Dockerfile**:
```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Change ownership of the app directory
RUN chown -R app:app /app

# Switch to app user
USER app

# Development stage
FROM base as development

# Install development dependencies
USER root
RUN uv sync --frozen
USER app

# Set development environment
ENV ENVIRONMENT=development
ENV DEBUG=true

# Expose port
EXPOSE 8000

# Start development server
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Set production environment
ENV ENVIRONMENT=production
ENV DEBUG=false

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start production server
CMD ["uv", "run", "gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

# Worker stage
FROM base as worker

# Set environment
ENV ENVIRONMENT=production

# Start Celery worker
CMD ["uv", "run", "celery", "-A", "app.infrastructure.tasks.celery_app", "worker", "--loglevel=info"]

# Beat stage
FROM base as beat

# Set environment
ENV ENVIRONMENT=production

# Start Celery beat
CMD ["uv", "run", "celery", "-A", "app.infrastructure.tasks.celery_app", "beat", "--loglevel=info"]

# Flower stage
FROM base as flower

# Set environment
ENV ENVIRONMENT=production

# Expose flower port
EXPOSE 5555

# Start Flower
CMD ["uv", "run", "celery", "-A", "app.infrastructure.tasks.celery_app", "flower", "--port=5555"]
```

### Optimized Dockerfile with Caching

**.dockerignore**:
```
# Version control
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.venv
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache
htmlcov
.coverage
.coverage.*

# Development
.env
.env.local
.env.development
.env.test
node_modules
npm-debug.log*

# Documentation
docs/
*.md
!README.md

# IDE
.vscode
.idea
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.log
```

## Docker Compose Configurations

### Development Environment

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  # Application
  app:
    build:
      context: .
      target: development
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - ENVIRONMENT=development
      - POSTGRES_URL=postgresql+asyncpg://postgres:password@postgres:5432/fastapi_enterprise
      - MONGODB_URL=mongodb://mongodb:27017/fastapi_enterprise
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./app:/app/app
      - ./tests:/app/tests
      - ./docs:/app/docs
    depends_on:
      - postgres
      - mongodb
      - redis
    networks:
      - app-network
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    build:
      context: .
      target: worker
    environment:
      - ENVIRONMENT=development
      - POSTGRES_URL=postgresql+asyncpg://postgres:password@postgres:5432/fastapi_enterprise
      - MONGODB_URL=mongodb://mongodb:27017/fastapi_enterprise
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./app:/app/app
    depends_on:
      - postgres
      - mongodb
      - redis
    networks:
      - app-network
    restart: unless-stopped

  # Celery Beat
  celery-beat:
    build:
      context: .
      target: beat
    environment:
      - ENVIRONMENT=development
      - POSTGRES_URL=postgresql+asyncpg://postgres:password@postgres:5432/fastapi_enterprise
      - MONGODB_URL=mongodb://mongodb:27017/fastapi_enterprise
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./app:/app/app
    depends_on:
      - redis
    networks:
      - app-network
    restart: unless-stopped

  # Flower Monitor
  flower:
    build:
      context: .
      target: flower
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    networks:
      - app-network
    restart: unless-stopped

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: fastapi_enterprise
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MongoDB Database
  mongodb:
    image: mongo:6.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Development Tools
  adminer:
    image: adminer
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    networks:
      - app-network
    restart: unless-stopped

  mongo-express:
    image: mongo-express
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: admin
      ME_CONFIG_MONGODB_ADMINPASSWORD: password
      ME_CONFIG_MONGODB_URL: mongodb://admin:password@mongodb:27017/
    ports:
      - "8081:8081"
    depends_on:
      - mongodb
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:
  mongodb_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

### Production Environment

**docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - app1
      - app2
    networks:
      - app-network
    restart: unless-stopped

  # Application Instances
  app1:
    build:
      context: .
      target: production
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - POSTGRES_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/fastapi_enterprise
      - MONGODB_URL=mongodb://admin:${MONGODB_PASSWORD}@mongodb:27017/fastapi_enterprise
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - mongodb
      - redis
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  app2:
    build:
      context: .
      target: production
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - POSTGRES_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/fastapi_enterprise
      - MONGODB_URL=mongodb://admin:${MONGODB_PASSWORD}@mongodb:27017/fastapi_enterprise
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - mongodb
      - redis
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  # Celery Workers
  celery-worker-1:
    build:
      context: .
      target: worker
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/fastapi_enterprise
      - MONGODB_URL=mongodb://admin:${MONGODB_PASSWORD}@mongodb:27017/fastapi_enterprise
      - REDIS_URL=redis://redis:6379
    command: ["uv", "run", "celery", "-A", "app.infrastructure.tasks.celery_app", "worker", "--loglevel=warning", "--concurrency=4", "-Q", "pricing,notifications"]
    depends_on:
      - postgres
      - mongodb
      - redis
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1'

  celery-worker-2:
    build:
      context: .
      target: worker
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@postgres:5432/fastapi_enterprise
      - MONGODB_URL=mongodb://admin:${MONGODB_PASSWORD}@mongodb:27017/fastapi_enterprise
      - REDIS_URL=redis://redis:6379
    command: ["uv", "run", "celery", "-A", "app.infrastructure.tasks.celery_app", "worker", "--loglevel=warning", "--concurrency=2", "-Q", "maintenance,data_processing"]
    depends_on:
      - postgres
      - mongodb
      - redis
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1'

  # Celery Beat
  celery-beat:
    build:
      context: .
      target: beat
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.25'

  # Databases
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: fastapi_enterprise
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1'

  mongodb:
    image: mongo:6.0
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGODB_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - ./backups:/backups
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'

  # Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - app-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  app-network:
    driver: bridge
```

## Nginx Configuration

### Load Balancer Configuration

**nginx/nginx.conf**:
```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log  /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

    # Upstream backend servers
    upstream fastapi_backend {
        least_conn;
        server app1:8000 max_fails=3 fail_timeout=30s;
        server app2:8000 max_fails=3 fail_timeout=30s;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_session_timeout 1d;
        ssl_session_cache shared:MozTLS:10m;
        ssl_session_tickets off;

        # Modern SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;

            proxy_pass http://fastapi_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;

            # Buffering
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }

        # Authentication endpoints (stricter rate limiting)
        location /auth/ {
            limit_req zone=auth burst=10 nodelay;

            proxy_pass http://fastapi_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://fastapi_backend;
            access_log off;
        }

        # Documentation
        location /docs {
            proxy_pass http://fastapi_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files (if any)
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Flower monitoring (restrict access)
        location /flower/ {
            allow 10.0.0.0/8;
            allow 172.16.0.0/12;
            allow 192.168.0.0/16;
            deny all;

            proxy_pass http://flower:5555/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## Environment Configuration

### Environment Variables

**.env.prod**:
```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database passwords
POSTGRES_PASSWORD=secure-postgres-password
MONGODB_PASSWORD=secure-mongodb-password
REDIS_PASSWORD=secure-redis-password

# External services
MATERIAL_API_KEY=your-material-api-key
SHIPPING_API_KEY=your-shipping-api-key

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password

# SSL/TLS
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Backup configuration
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

### Docker Secrets Management

**docker-compose.secrets.yml**:
```yaml
version: '3.8'

services:
  app1:
    secrets:
      - postgres_password
      - mongodb_password
      - redis_password
      - secret_key
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
      - MONGODB_PASSWORD_FILE=/run/secrets/mongodb_password
      - REDIS_PASSWORD_FILE=/run/secrets/redis_password
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  mongodb_password:
    file: ./secrets/mongodb_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

## Deployment Scripts

### Build and Deploy Script

**scripts/deploy.sh**:
```bash
#!/bin/bash

set -e

# Configuration
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

echo "Deploying FastAPI Enterprise - Environment: $ENVIRONMENT, Version: $VERSION"

# Pre-deployment checks
echo "Running pre-deployment checks..."

# Check if required files exist
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: Compose file $COMPOSE_FILE not found"
    exit 1
fi

if [ ! -f ".env.${ENVIRONMENT}" ]; then
    echo "Error: Environment file .env.${ENVIRONMENT} not found"
    exit 1
fi

# Load environment variables
source .env.${ENVIRONMENT}

# Database backup (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Creating database backup..."
    ./scripts/backup-db.sh
fi

# Build images
echo "Building Docker images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Tag images with version
docker tag fastapi-enterprise_app:latest fastapi-enterprise_app:$VERSION
docker tag fastapi-enterprise_worker:latest fastapi-enterprise_worker:$VERSION

# Run database migrations
echo "Running database migrations..."
docker-compose -f $COMPOSE_FILE run --rm app uv run alembic upgrade head

# Deploy services with rolling update
echo "Deploying services..."

# Stop old services gracefully
docker-compose -f $COMPOSE_FILE down --timeout 30

# Start new services
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
./scripts/wait-for-health.sh

# Run smoke tests
echo "Running smoke tests..."
./scripts/smoke-tests.sh $ENVIRONMENT

echo "Deployment completed successfully!"

# Clean up old images
echo "Cleaning up old images..."
docker image prune -f
```

### Health Check Script

**scripts/wait-for-health.sh**:
```bash
#!/bin/bash

set -e

TIMEOUT=300
INTERVAL=5
ELAPSED=0

echo "Waiting for services to be healthy..."

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check application health
    if curl -f http://localhost/health >/dev/null 2>&1; then
        echo "✓ Application is healthy"
        break
    fi

    echo "Waiting for application to be ready... (${ELAPSED}s/${TIMEOUT}s)"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "✗ Timeout waiting for services to be healthy"
    docker-compose logs --tail=50
    exit 1
fi

echo "All services are healthy!"
```

### Smoke Tests

**scripts/smoke-tests.sh**:
```bash
#!/bin/bash

set -e

ENVIRONMENT=${1:-production}
BASE_URL="http://localhost"

if [ "$ENVIRONMENT" = "production" ]; then
    BASE_URL="https://your-domain.com"
fi

echo "Running smoke tests against $BASE_URL..."

# Test health endpoint
echo "Testing health endpoint..."
if ! curl -f "$BASE_URL/health" >/dev/null 2>&1; then
    echo "✗ Health check failed"
    exit 1
fi
echo "✓ Health check passed"

# Test API documentation
echo "Testing API documentation..."
if ! curl -f "$BASE_URL/docs" >/dev/null 2>&1; then
    echo "✗ API docs not accessible"
    exit 1
fi
echo "✓ API docs accessible"

# Test pricing endpoint
echo "Testing pricing endpoint..."
PRICING_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/pricing" \
    -H "Content-Type: application/json" \
    -d '{
        "material": "aluminum",
        "quantity": 10,
        "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
        "geometric_complexity_score": 2.5,
        "process": "cnc"
    }')

if ! echo "$PRICING_RESPONSE" | grep -q "pricing_tiers"; then
    echo "✗ Pricing endpoint failed"
    echo "Response: $PRICING_RESPONSE"
    exit 1
fi
echo "✓ Pricing endpoint working"

echo "All smoke tests passed!"
```

## Monitoring and Logging

### Prometheus Configuration

**monitoring/prometheus.yml**:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'fastapi-app'
    static_configs:
      - targets: ['app1:8000', 'app2:8000']
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'celery'
    static_configs:
      - targets: ['flower:5555']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Docker Logging Configuration

**logging/docker-daemon.json**:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3",
    "labels": "production"
  }
}
```

### Log Aggregation with ELK Stack

**docker-compose.logging.yml**:
```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - logging-network

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch
    networks:
      - logging-network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - logging-network

volumes:
  elasticsearch_data:

networks:
  logging-network:
    driver: bridge
```

## Production Best Practices

### Security Hardening

1. **Use non-root users in containers**
2. **Implement proper secrets management**
3. **Regular security updates**
4. **Network segmentation**
5. **SSL/TLS encryption**
6. **Input validation and rate limiting**

### Performance Optimization

1. **Resource limits and requests**
2. **Connection pooling**
3. **Caching strategies**
4. **Load balancing**
5. **Database optimization**

### Backup and Recovery

1. **Automated database backups**
2. **Configuration backups**
3. **Disaster recovery procedures**
4. **Regular restore testing**

This comprehensive guide provides everything needed to deploy the FastAPI Enterprise application in a production environment using Docker and Docker Compose.
