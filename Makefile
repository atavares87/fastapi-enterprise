# FastAPI Enterprise Application Makefile
# This Makefile provides common development tasks using uv as the package manager

# Variables
PYTHON = python3.13
UV = uv
PROJECT_NAME = fastapi-enterprise
SRC_DIR = app
TEST_DIR = tests
DOCKER_IMAGE = $(PROJECT_NAME):latest
DOCKER_REGISTRY = your-registry.com

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)FastAPI Enterprise Application$(NC)"
	@echo "$(BLUE)==============================$(NC)"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment setup
.PHONY: install
install: ## Install all dependencies using uv
	@echo "$(BLUE)Installing dependencies with uv...$(NC)"
	$(UV) sync
	$(UV) run pre-commit install
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

.PHONY: install-dev
install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(UV) sync --dev
	$(UV) run pre-commit install
	@echo "$(GREEN)Development dependencies installed successfully!$(NC)"

.PHONY: update-deps
update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(UV) lock --upgrade
	$(UV) sync
	@echo "$(GREEN)Dependencies updated successfully!$(NC)"

# Development server
.PHONY: start-dev
start-dev: ## Run the development server with auto-reload
	@echo "$(BLUE)Starting development server...$(NC)"
	$(UV) run uvicorn $(SRC_DIR).main:app --reload --host 0.0.0.0 --port 8000

.PHONY: start-prod
start-prod: ## Run the production server
	@echo "$(BLUE)Starting production server...$(NC)"
	$(UV) run gunicorn $(SRC_DIR).main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Code quality
.PHONY: format
format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	$(UV) run black $(SRC_DIR) $(TEST_DIR)
	$(UV) run isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Code formatted successfully!$(NC)"

.PHONY: lint
lint: ## Run linting with ruff
	@echo "$(BLUE)Running linting checks...$(NC)"
	$(UV) run ruff check $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Linting completed!$(NC)"

.PHONY: lint-fix
lint-fix: ## Run linting with auto-fix
	@echo "$(BLUE)Running linting with auto-fix...$(NC)"
	$(UV) run ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Linting with auto-fix completed!$(NC)"

.PHONY: type-check
type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	$(UV) run mypy $(SRC_DIR)
	@echo "$(GREEN)Type checking completed!$(NC)"

.PHONY: security-check
security-check: ## Run security checks with bandit
	@echo "$(BLUE)Running security checks...$(NC)"
	$(UV) run bandit -r $(SRC_DIR) -f json -o security-report.json || true
	$(UV) run bandit -r $(SRC_DIR)
	@echo "$(GREEN)Security check completed!$(NC)"

.PHONY: check-all
check-all: format lint type-check security-check ## Run all code quality checks
	@echo "$(GREEN)All checks completed successfully!$(NC)"

# Testing
.PHONY: test
test: ## Run all tests (unit, integration, api)
	@echo "$(BLUE)Running all tests...$(NC)"
	$(UV) run pytest $(TEST_DIR) -v --ignore=$(TEST_DIR)/contract
	@echo "$(GREEN)Tests completed!$(NC)"

.PHONY: test-all
test-all: test test-contract-consumer ## Run all tests including contract tests
	@echo "$(GREEN)All tests completed!$(NC)"

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/unit -v -m "not integration and not api"
	@echo "$(GREEN)Unit tests completed!$(NC)"

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/integration -v -m integration
	@echo "$(GREEN)Integration tests completed!$(NC)"

.PHONY: test-api
test-api: ## Run API tests only
	@echo "$(BLUE)Running API tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/api -v -m api
	@echo "$(GREEN)API tests completed!$(NC)"

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(UV) run pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

.PHONY: test-contract
test-contract: ## Run contract tests (consumer-driven)
	@echo "$(BLUE)Running contract tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/contract -v -m contract
	@echo "$(GREEN)Contract tests completed!$(NC)"

.PHONY: test-contract-consumer
test-contract-consumer: ## Run consumer contract tests only
	@echo "$(BLUE)Running consumer contract tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/contract -v -m "contract and not provider"
	@echo "$(GREEN)Consumer contract tests completed!$(NC)"

.PHONY: test-contract-provider
test-contract-provider: ## Run provider verification tests
	@echo "$(BLUE)Running provider verification tests...$(NC)"
	@echo "$(YELLOW)Note: Ensure the application is running on localhost:8000$(NC)"
	$(UV) run pytest $(TEST_DIR)/contract -v -m "contract and provider"
	@echo "$(GREEN)Provider verification tests completed!$(NC)"

.PHONY: test-contract-full
test-contract-full: start-dev-background test-contract-consumer test-contract-provider stop-dev-background ## Run full contract testing workflow
	@echo "$(GREEN)Full contract testing workflow completed!$(NC)"

# Database management
.PHONY: db-upgrade
db-upgrade: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	$(UV) run alembic upgrade head
	@echo "$(GREEN)Database migrations completed!$(NC)"

.PHONY: db-downgrade
db-downgrade: ## Downgrade database by one migration
	@echo "$(BLUE)Downgrading database...$(NC)"
	$(UV) run alembic downgrade -1
	@echo "$(GREEN)Database downgrade completed!$(NC)"

.PHONY: db-revision
db-revision: ## Create a new database migration
	@echo "$(BLUE)Creating new database migration...$(NC)"
	@read -p "Enter migration message: " message; \
	$(UV) run alembic revision --autogenerate -m "$$message"
	@echo "$(GREEN)Migration created successfully!$(NC)"

.PHONY: db-reset
db-reset: ## Reset database (WARNING: This will drop all data)
	@echo "$(RED)WARNING: This will drop all data in the database!$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		$(UV) run alembic downgrade base; \
		$(UV) run alembic upgrade head; \
		echo "$(GREEN)Database reset completed!$(NC)"; \
	else \
		echo "$(YELLOW)Database reset cancelled.$(NC)"; \
	fi

# Docker commands
.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)Docker image built successfully!$(NC)"

.PHONY: docker-up
docker-up: ## 🚀 Start complete development environment (app + observability)
	@echo "$(BLUE)🚀 Starting FastAPI Enterprise complete environment...$(NC)"
	@echo "$(YELLOW)📊 Starting application + observability stack...$(NC)"
	@docker-compose up -d
	@echo "$(YELLOW)⏳ Waiting for services to initialize...$(NC)"
	@sleep 15
	@echo "$(BLUE)🔍 Initializing MongoDB indexes...$(NC)"
	@docker exec -i mongodb mongosh pricing --quiet --eval "db.pricing_explanations.createIndex({'calculation_id': 1}, {unique: true}); db.pricing_explanations.createIndex({'timestamp': -1}); print('Indexes created successfully');" || true
	@echo ""
	@echo "$(GREEN)✅ Environment ready!$(NC)"
	@echo ""
	@echo "$(BLUE)🎯 Main Services:$(NC)"
	@echo "  🌐 FastAPI App:          http://localhost:8000"
	@echo "  📖 API Documentation:    http://localhost:8000/docs"
	@echo "  📊 App Metrics:          http://localhost:8000/metrics"
	@echo "  🌸 Flower (Celery):      http://localhost:5555"
	@echo ""
	@echo "$(BLUE)🔍 Observability:$(NC)"
	@echo "  📊 Grafana Dashboard:    http://localhost:3000 (admin/admin)"
	@echo "  🔍 Jaeger Tracing:       http://localhost:16686"
	@echo "  📈 Prometheus Metrics:   http://localhost:9090"
	@echo "  🚨 AlertManager:         http://localhost:9093"
	@echo ""
	@echo "$(BLUE)💾 Data Storage:$(NC)"
	@echo "  🗄️  MongoDB:              mongodb://admin:password@localhost:27017/pricing"
	@echo "  🐘 PostgreSQL:           postgresql://postgres:postgres@localhost:5432/fastapi_enterprise"
	@echo "  📦 Redis:                redis://localhost:6379"
	@echo ""
	@echo "$(BLUE)🔧 Optional Admin Tools:$(NC)"
	@echo "  Use 'make docker-up-tools' to start pgAdmin, Mongo Express, Redis Commander"
	@echo ""
	@echo "$(BLUE)🔧 Next Steps:$(NC)"
	@echo "  1. Install dependencies:  make install"
	@echo "  2. Run pricing demo:     make pricing-demo"
	@echo "  3. Run tests:            make test-pricing"
	@echo "  4. View logs:            make docker-logs"
	@echo ""

.PHONY: docker-down
docker-down: ## 🛑 Stop all services
	@echo "$(RED)🛑 Stopping all services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✅ All services stopped$(NC)"

# Database operations
.PHONY: db-init
db-init: ## 🗄️ Initialize MongoDB collections and indexes
	@echo "$(BLUE)🗄️ Initializing MongoDB...$(NC)"
	@docker exec -i mongodb mongosh pricing --eval "load('/docker-entrypoint-initdb.d/mongo-init.js')"
	@echo "$(GREEN)✅ MongoDB initialized$(NC)"

.PHONY: db-pricing-reset
db-pricing-reset: ## 🔄 Reset MongoDB pricing data (WARNING: Deletes all data)
	@echo "$(RED)⚠️  WARNING: This will delete all MongoDB pricing data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@docker exec mongodb mongosh pricing --eval "db.dropDatabase()"
	@make db-init
	@echo "$(GREEN)✅ MongoDB reset completed$(NC)"

.PHONY: grafana-import
grafana-import: ## 📈 Import Grafana dashboards
	@echo "$(BLUE)📈 Importing Grafana dashboards...$(NC)"
	@sleep 5  # Wait for Grafana to be ready
	@curl -X POST \
		-H "Content-Type: application/json" \
		-u admin:admin \
		-d @observability/grafana/dashboards/pricing-dashboard.json \
		http://localhost:3000/api/dashboards/db || echo "$(YELLOW)⚠️  Dashboard import failed, may already exist$(NC)"
	@echo "$(GREEN)✅ Dashboard import completed$(NC)"

.PHONY: pricing-demo
pricing-demo: ## 🎬 Run pricing demo with explainability
	@echo "$(BLUE)🎬 Running pricing demo...$(NC)"
	@$(UV) run python scripts/pricing_demo.py || echo "$(RED)❌ Demo failed - make sure dependencies are installed$(NC)"

.PHONY: test-pricing
test-pricing: ## 🧪 Run pricing-specific tests
	@echo "$(BLUE)🧪 Running pricing tests...$(NC)"
	@$(UV) run pytest tests/test_pricing_limits.py -v
	@echo "$(GREEN)✅ Pricing tests completed$(NC)"

.PHONY: full-setup
full-setup: docker-up install db-init grafana-import ## 🚀 Complete setup with dashboard import

# Cleanup commands
.PHONY: clean
clean: ## Clean up cache files and build artifacts
	@echo "$(BLUE)Cleaning up cache files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	@echo "$(GREEN)Cleanup completed!$(NC)"

# CI/CD helpers
.PHONY: ci
ci: install-dev check-all test-coverage test-contract-consumer ## Run all CI checks
	@echo "$(GREEN)All CI checks passed!$(NC)"

.PHONY: ci-full
ci-full: install-dev check-all test-coverage test-contract-full ## Run full CI pipeline with contract verification
	@echo "$(GREEN)Full CI pipeline completed!$(NC)"

.PHONY: pre-commit-all
pre-commit-all: ## Run pre-commit on all files
	@echo "$(BLUE)Running pre-commit on all files...$(NC)"
	$(UV) run pre-commit run --all-files
	@echo "$(GREEN)Pre-commit checks completed!$(NC)"
