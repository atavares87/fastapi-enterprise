#!/bin/bash

# FastAPI Enterprise - Quick Start Script
# This script sets up the complete development environment with observability

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logo
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  FastAPI Enterprise                         ║"
echo "║         Complete Observability & Pricing Setup             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Start the observability stack
echo ""
echo -e "${YELLOW}🚀 Starting FastAPI Enterprise environment...${NC}"
make docker-up

# Wait for services to be ready
echo ""
echo -e "${BLUE}⏳ Waiting for services to be fully ready...${NC}"
sleep 15

# Check service health
echo ""
echo -e "${CYAN}🏥 Checking service health...${NC}"

services=("Grafana:3000" "Jaeger:16686" "Prometheus:9090" "AlertManager:9093")
all_healthy=true

for service in "${services[@]}"; do
    name=${service%%:*}
    port=${service##*:}

    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port | grep -q 200; then
        echo -e "  $name: ${GREEN}✅ Running${NC}"
    else
        echo -e "  $name: ${RED}❌ Not ready${NC}"
        all_healthy=false
    fi
done

# Check MongoDB
if docker exec mongodb mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    echo -e "  MongoDB: ${GREEN}✅ Running${NC}"
else
    echo -e "  MongoDB: ${RED}❌ Not ready${NC}"
    all_healthy=false
fi

# Check Redis
if docker exec redis redis-cli ping >/dev/null 2>&1; then
    echo -e "  Redis: ${GREEN}✅ Running${NC}"
else
    echo -e "  Redis: ${RED}❌ Not ready${NC}"
    all_healthy=false
fi

if [ "$all_healthy" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Some services are not ready yet. You can check again with: make docker-status${NC}"
else
    echo ""
    echo -e "${GREEN}🎉 All services are running successfully!${NC}"
fi

# Display access information
echo ""
echo -e "${CYAN}🎯 Your FastAPI Enterprise environment is ready!${NC}"
echo ""
echo -e "${BLUE}📊 Observability Dashboard Access:${NC}"
echo "  📊 Grafana:           http://localhost:3000 (admin/admin)"
echo "  🔍 Jaeger Tracing:    http://localhost:16686"
echo "  📈 Prometheus:        http://localhost:9090"
echo "  🚨 AlertManager:      http://localhost:9093"
echo ""
echo -e "${BLUE}💾 Data Storage:${NC}"
echo "  🗄️  MongoDB:          mongodb://admin:password@localhost:27017/pricing"
echo "  📦 Redis:            redis://localhost:6379"
echo ""
echo -e "${BLUE}🔧 Next Steps:${NC}"
echo "  1. Install Python dependencies:"
echo "     ${CYAN}make install${NC}"
echo ""
echo "  2. Run the pricing demo:"
echo "     ${CYAN}make pricing-demo${NC}"
echo ""
echo "  3. Start your FastAPI application:"
echo "     ${CYAN}make start-dev${NC}"
echo "     Then access: http://localhost:8000"
echo ""
echo "  4. Run tests:"
echo "     ${CYAN}make test-pricing${NC}"
echo ""
echo "  5. View real-time logs:"
echo "     ${CYAN}make docker-logs${NC}"
echo ""
echo -e "${BLUE}🏥 Troubleshooting:${NC}"
echo "  • Check service status: ${CYAN}make docker-status${NC}"
echo "  • Run diagnostics:     ${CYAN}make doctor${NC}"
echo "  • View error logs:     ${CYAN}make logs-errors${NC}"
echo "  • Restart services:    ${CYAN}make docker-restart${NC}"
echo ""
echo -e "${GREEN}✨ Happy coding with FastAPI Enterprise!${NC}"
echo ""

# Optionally install dependencies if requested
read -p "Would you like to install Python dependencies now? (y/N): " install_deps
if [[ $install_deps =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
    make install

    echo ""
    echo -e "${BLUE}🎬 Running pricing demo...${NC}"
    make pricing-demo || echo -e "${YELLOW}⚠️  Demo requires the application to be running. Start it with: make start-dev${NC}"
fi
