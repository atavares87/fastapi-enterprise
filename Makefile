# FastAPI Enterprise Application Makefile
# Simplified and organized for maintainability

# Variables
UV = uv
SRC_DIR = app
TEST_DIR = tests

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)FastAPI Enterprise Application$(NC)"
	@echo "$(BLUE)==============================$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

#=============================================================================
# 🔧 SETUP & INSTALLATION
#=============================================================================

.PHONY: install
install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(UV) sync
	$(UV) run pre-commit install
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

.PHONY: update-deps
update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(UV) lock --upgrade
	$(UV) sync
	@echo "$(GREEN)✅ Dependencies updated!$(NC)"

#=============================================================================
# 🚀 DEVELOPMENT
#=============================================================================

.PHONY: start-dev
start-dev: ## Start development server with auto-reload
	@echo "$(BLUE)Starting development server...$(NC)"
	$(UV) run uvicorn $(SRC_DIR).main:app --reload --host 0.0.0.0 --port 8000

.PHONY: start-prod
start-prod: ## Start production server
	@echo "$(BLUE)Starting production server...$(NC)"
	$(UV) run gunicorn $(SRC_DIR).main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

#=============================================================================
# ✅ CODE QUALITY
#=============================================================================

.PHONY: format
format: ## Format code (black + isort)
	@echo "$(BLUE)Formatting code...$(NC)"
	$(UV) run black $(SRC_DIR) $(TEST_DIR)
	$(UV) run isort $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Code formatted!$(NC)"

.PHONY: lint
lint: ## Run linting (ruff)
	@echo "$(BLUE)Running linting...$(NC)"
	$(UV) run ruff check $(SRC_DIR) $(TEST_DIR)

.PHONY: lint-fix
lint-fix: ## Run linting with auto-fix
	@echo "$(BLUE)Fixing lint issues...$(NC)"
	$(UV) run ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Lint issues fixed!$(NC)"

.PHONY: type-check
type-check: ## Run type checking (mypy)
	@echo "$(BLUE)Running type checks...$(NC)"
	$(UV) run mypy $(SRC_DIR)

.PHONY: check-all
check-all: format lint type-check ## Run all code quality checks
	@echo "$(GREEN)✅ All checks passed!$(NC)"

#=============================================================================
# 🧪 TESTING
#=============================================================================

.PHONY: test
test: ## Run all tests (unit + integration + api)
	@echo "$(BLUE)Running all tests...$(NC)"
	$(UV) run pytest $(TEST_DIR) -v --ignore=$(TEST_DIR)/contract

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/integration -v

.PHONY: test-api
test-api: ## Run API tests only
	@echo "$(BLUE)Running API tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/api -v

.PHONY: test-contract
test-contract: ## Run contract tests
	@echo "$(BLUE)Running contract tests...$(NC)"
	$(UV) run pytest $(TEST_DIR)/contract -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(UV) run pytest $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Coverage report: htmlcov/index.html$(NC)"

#=============================================================================
# 🗄️ DATABASE
#=============================================================================

.PHONY: db-upgrade
db-upgrade: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	$(UV) run alembic upgrade head
	@echo "$(GREEN)✅ Migrations completed!$(NC)"

.PHONY: db-downgrade
db-downgrade: ## Downgrade database by one migration
	@echo "$(BLUE)Downgrading database...$(NC)"
	$(UV) run alembic downgrade -1

.PHONY: db-revision
db-revision: ## Create a new migration (usage: make db-revision)
	@echo "$(BLUE)Creating migration...$(NC)"
	@read -p "Migration message: " msg; \
	$(UV) run alembic revision --autogenerate -m "$$msg"
	@echo "$(GREEN)✅ Migration created!$(NC)"

.PHONY: db-reset
db-reset: ## Reset database (WARNING: deletes all data)
	@echo "$(RED)⚠️  WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		$(UV) run alembic downgrade base; \
		$(UV) run alembic upgrade head; \
		echo "$(GREEN)✅ Database reset!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

#=============================================================================
# 🐳 DOCKER
#=============================================================================

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t fastapi-enterprise:latest .
	@echo "$(GREEN)✅ Docker image built!$(NC)"

.PHONY: docker-up
docker-up: ## Start all services (app + observability)
	@echo "$(BLUE)🚀 Starting all services...$(NC)"
	@docker-compose up -d
	@echo "$(YELLOW)⏳ Waiting for services...$(NC)"
	@sleep 15
	@echo ""
	@echo "$(GREEN)✅ Environment ready!$(NC)"
	@echo ""
	@echo "$(BLUE)📍 Services:$(NC)"
	@echo "  🌐 API:          http://localhost:8000"
	@echo "  📖 Docs:         http://localhost:8000/docs"
	@echo "  📊 Metrics:      http://localhost:8000/metrics"
	@echo "  🌸 Flower:       http://localhost:5555"
	@echo "  📊 Grafana:      http://localhost:3000 (admin/admin)"
	@echo "  🔍 Jaeger:       http://localhost:16686"
	@echo "  📈 Prometheus:   http://localhost:9090"
	@echo ""

.PHONY: docker-down
docker-down: ## Stop all services
	@echo "$(RED)🛑 Stopping all services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Services stopped$(NC)"

.PHONY: docker-logs
docker-logs: ## View service logs
	docker-compose logs -f

.PHONY: docker-clean
docker-clean: ## Clean up Docker containers and volumes
	@echo "$(RED)⚠️  WARNING: This will remove all containers and volumes!$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ]; then \
		docker-compose down -v; \
		echo "$(GREEN)✅ Docker cleanup complete!$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled.$(NC)"; \
	fi

#=============================================================================
# 🚀 QUICK START
#=============================================================================

.PHONY: full-setup
full-setup: docker-up install db-upgrade ## Complete setup (one command to rule them all)
	@echo ""
	@echo "$(GREEN)🎉 Setup complete!$(NC)"
	@echo ""
	@echo "$(BLUE)🔧 Next steps:$(NC)"
	@echo "  1. Run tests:     make test"
	@echo "  2. View logs:     make docker-logs"
	@echo "  3. Start coding!  Code is in ./app/"
	@echo ""

#=============================================================================
# 🧹 CLEANUP
#=============================================================================

.PHONY: clean
clean: ## Clean cache files and build artifacts
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ dist/ build/ *.egg-info/
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

#=============================================================================
# 📊 LOAD TESTING
#=============================================================================

.PHONY: load-test
load-test: ## Run k6 load test (requires k6 installed)
	@echo "$(BLUE)Running k6 load test...$(NC)"
	@if ! command -v k6 > /dev/null; then \
		echo "$(RED)❌ k6 is not installed. Install from https://k6.io$(NC)"; \
		exit 1; \
	fi
	k6 run k6-load-test.js

.PHONY: load-test-smoke
load-test-smoke: ## Run k6 smoke test (quick validation)
	@echo "$(BLUE)Running k6 smoke test...$(NC)"
	@if ! command -v k6 > /dev/null; then \
		echo "$(RED)❌ k6 is not installed. Install from https://k6.io$(NC)"; \
		exit 1; \
	fi
	k6 run --vus 1 --duration 30s k6-load-test.js

#=============================================================================
# 🔄 CI/CD
#=============================================================================

.PHONY: ci
ci: check-all test-coverage test-contract ## Run CI pipeline
	@echo "$(GREEN)✅ CI checks passed!$(NC)"

.PHONY: pre-commit
pre-commit: ## Run pre-commit on all files
	@echo "$(BLUE)Running pre-commit...$(NC)"
	$(UV) run pre-commit run --all-files
