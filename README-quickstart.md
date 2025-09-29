# FastAPI Enterprise - Quick Start Guide

Get your complete development environment with observability up and running in minutes!

## 🚀 One-Command Setup

The fastest way to get started:

```bash
make docker-up
```

This single command will:
- ✅ Start MongoDB with pricing database
- ✅ Launch Prometheus for metrics collection
- ✅ Set up Grafana with pricing dashboards
- ✅ Initialize Jaeger for distributed tracing
- ✅ Configure AlertManager for monitoring alerts
- ✅ Start Redis for caching
- ✅ Set up OpenTelemetry collector
- ✅ Create all necessary database indexes

## 📋 Prerequisites

Before running `make docker-up`, ensure you have:

- **Docker** (v20.0+)
- **Docker Compose** (v2.0+)
- **Make** (usually pre-installed)

Check if you have everything:
```bash
make doctor
```

## 🎯 Quick Start Options

### Option 1: Manual Step-by-Step
```bash
# 1. Start all services
make docker-up

# 2. Install Python dependencies
make install

# 3. Run pricing demo
make pricing-demo

# 4. Start your FastAPI app
make start-dev
```

### Option 2: Automated Quick Start
```bash
# Complete setup in one command
make quick-start

# Or even more complete setup with dashboards
make full-setup
```

### Option 3: Use the Quick Start Script
```bash
# Interactive setup with guidance
./scripts/quick-start.sh
```

## 🎯 What You Get

### Observability Dashboard Access
- **📊 Grafana**: http://localhost:3000 (admin/admin)
- **🔍 Jaeger Tracing**: http://localhost:16686
- **📈 Prometheus**: http://localhost:9090
- **🚨 AlertManager**: http://localhost:9093

### Application Endpoints
- **🌐 FastAPI App**: http://localhost:8000
- **📖 API Documentation**: http://localhost:8000/docs
- **📊 Metrics Endpoint**: http://localhost:8000/metrics

### Data Storage
- **🗄️ MongoDB**: `mongodb://admin:password@localhost:27017/pricing`
- **📦 Redis**: `redis://localhost:6379`

## 🔧 Essential Commands

### Service Management
```bash
make docker-up          # Start all services
make docker-down        # Stop all services
make docker-restart     # Restart all services
make docker-status      # Check service health
make docker-logs        # View all logs
```

### Development
```bash
make install            # Install dependencies
make start-dev          # Start FastAPI with hot reload
make test               # Run all tests
make test-pricing       # Run pricing-specific tests
make pricing-demo       # Demo pricing calculations
```

### Monitoring
```bash
make metrics            # View current app metrics
make logs-pricing       # View pricing-specific logs
make logs-errors        # View error logs only
make grafana-import     # Import Grafana dashboards
```

### Database Operations
```bash
make db-init            # Initialize MongoDB indexes
make db-backup          # Backup MongoDB data
make db-pricing-reset   # Reset pricing data (⚠️ destructive)
```

### Diagnostics
```bash
make doctor             # System health check
make urls               # Show all service URLs
```

## 🔍 Verifying Everything Works

### 1. Check Service Status
```bash
make docker-status
```
You should see all services running with ✅ status.

### 2. Run the Pricing Demo
```bash
make pricing-demo
```
This will calculate sample pricing with the new limits system.

### 3. View Grafana Dashboard
1. Go to http://localhost:3000
2. Login with admin/admin
3. Navigate to the pricing dashboard

### 4. Check Application Metrics
```bash
make metrics
```
Should show pricing-related metrics from your app.

## 🧪 Testing Your Setup

### Run All Tests
```bash
make test
```

### Test Pricing Limits System
```bash
make test-pricing
```

### Test with Your FastAPI App
```bash
# In one terminal
make start-dev

# In another terminal
curl http://localhost:8000/docs
```

## 🚨 Troubleshooting

### Services Not Starting
```bash
# Check system status
make doctor

# View detailed logs
make docker-logs

# Check port conflicts
make doctor  # Shows port usage
```

### Common Issues

**MongoDB Connection Failed:**
```bash
# Reset MongoDB
make db-pricing-reset
```

**Grafana Dashboard Not Loading:**
```bash
# Re-import dashboards
make grafana-import
```

**Application Not Connecting to Services:**
```bash
# Check all services are healthy
make docker-status

# Restart if needed
make docker-restart
```

**Permission Issues:**
```bash
# Fix common permission problems
sudo chmod +x scripts/quick-start.sh
sudo chown -R $USER:$USER observability/
```

### Getting Help
```bash
# Show all available commands
make help

# Show service URLs
make urls

# Run comprehensive health check
make doctor
```

## 💡 Tips for Development

### 1. Keep Services Running
Leave the observability stack running during development:
```bash
# Start once
make docker-up

# Develop your app
make start-dev

# Services keep running in background
# Only stop when you're done: make docker-down
```

### 2. Use Real-Time Monitoring
While developing, keep these open in separate tabs:
- **Grafana**: Monitor pricing performance
- **Jaeger**: Trace request flows
- **Logs**: `make docker-logs` for real-time debugging

### 3. Test Pricing Limits
The new pricing limits system prevents negative prices:
```python
# This is automatically available
service = PricingService.with_conservative_limits()

# Pricing will be adjusted if limits are violated
# All adjustments are logged and explained
```

### 4. Access Pricing Explanations
Every calculation is stored with complete explanations:
```python
# Calculate with full explainability
result = await service.calculate_part_pricing_with_explanation(
    part_spec=part_spec,
    user_id="developer",
    save_to_db=True  # Saves to MongoDB
)

# Access step-by-step explanations
explanation = result["explanation"]
```

## 🔄 Daily Workflow

### Starting Work
```bash
make docker-up        # Start observability stack
make start-dev        # Start your FastAPI app
```

### During Development
```bash
make test-pricing     # Test your pricing changes
make metrics          # Check performance
make pricing-demo     # Quick functionality check
```

### Ending Work
```bash
make docker-down      # Stop all services
```

## 🎯 What's Next?

1. **Explore Grafana Dashboards** - See your pricing metrics in real-time
2. **Check Jaeger Traces** - Understand request flows
3. **Review MongoDB Data** - Examine stored pricing explanations
4. **Set Up Alerts** - Configure notifications for pricing issues
5. **Integrate with CI/CD** - Use `make test` and `make check-all`

---

🎉 **You're all set!** Your FastAPI Enterprise environment with complete observability and pricing explainability is ready for development.

Need help? Run `make help` or `make doctor` for diagnostics.
