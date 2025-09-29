# FastAPI Enterprise - Observability & Pricing Explainability

This document describes the comprehensive observability and pricing explainability system implemented for the FastAPI Enterprise application.

## Overview

The system provides three key capabilities:

1. **Pricing Explainability** - Detailed explanations of how pricing calculations are performed
2. **MongoDB Storage** - Persistent storage of pricing explanations and audit trails
3. **OpenTelemetry Observability** - Complete observability with traces, metrics, and dashboards

## Architecture

```mermaid
graph TB
    subgraph "FastAPI Application"
        API[FastAPI Routes]
        PS[Pricing Service]
        PE[Pricing Explainer]
        PR[Pricing Repository]
    end

    subgraph "Storage Layer"
        MongoDB[(MongoDB)]
        Redis[(Redis Cache)]
    end

    subgraph "Observability Stack"
        OC[OpenTelemetry Collector]
        Jaeger[Jaeger Tracing]
        Prometheus[Prometheus Metrics]
        Grafana[Grafana Dashboards]
        AM[AlertManager]
    end

    API --> PS
    PS --> PE
    PS --> PR
    PR --> MongoDB
    PS --> OC
    OC --> Jaeger
    OC --> Prometheus
    Prometheus --> Grafana
    Prometheus --> AM
```

## Quick Start

### 1. Start the Observability Stack

```bash
# Start all observability services
docker-compose -f docker-compose.observability.yml up -d

# Check services are running
docker-compose -f docker-compose.observability.yml ps
```

### 2. Initialize Your FastAPI Application

```python
from app.core.telemetry import initialize_telemetry
from app.modules.pricing.service import PricingService
from app.modules.pricing.repository import PricingRepository
from motor.motor_asyncio import AsyncIOMotorClient

# Initialize telemetry
telemetry_manager = initialize_telemetry()

# Set up MongoDB connection
mongo_client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017")
database = mongo_client.pricing

# Initialize services
repository = PricingRepository(database)
pricing_service = PricingService.with_conservative_limits()
pricing_service.repository = repository

# Instrument your FastAPI app
telemetry_manager.instrument_fastapi(app)
```

### 3. Use the Pricing Service with Explainability

```python
from app.modules.cost.domain import PartSpecification, Material, Process, Dimensions

# Create a part specification
part_spec = PartSpecification(
    material=Material.ALUMINUM,
    process=Process.CNC,
    dimensions=Dimensions(length_mm=100, width_mm=50, height_mm=25),
    geometric_complexity_score=3.5,
    quantity=50
)

# Calculate pricing with full explainability
result = await pricing_service.calculate_part_pricing_with_explanation(
    part_spec=part_spec,
    part_weight_kg=0.3,
    quantity=50,
    customer_tier="premium",
    user_id="user123",
    ip_address="192.168.1.100"
)

# Access results
pricing = result["pricing"]
explanation = result["explanation"]
metadata = result["metadata"]

print(f"Calculation ID: {result['calculation_id']}")
print(f"Best price: ${pricing.standard.final_price}")
print(f"Limits applied: {explanation.limits_applied}")
```

## Pricing Explainability Features

### Detailed Calculation Steps

The explainability system provides step-by-step breakdowns:

```python
# Cost calculation steps
for step in explanation.cost_calculation_steps:
    print(f"{step.step_name}: {step.description}")
    print(f"Formula: {step.calculation_formula}")
    print(f"Result: ${step.output_value}")
    print(f"Reasoning: {step.reasoning}")

# Tier-specific explanations
for tier_name, tier_explanation in explanation.tier_explanations.items():
    print(f"\n{tier_name.upper()} TIER:")
    print(f"Margin: {tier_explanation.margin_percentage*100:.1f}%")
    print(f"Reasoning: {tier_explanation.margin_reasoning}")

    # Discount applications
    for discount in tier_explanation.discount_applications:
        if discount.condition_met:
            print(f"Applied: {discount.rule_name} - {discount.reasoning}")
```

### Business Rule Documentation

Every pricing decision is documented:

- **Volume Discounts**: Threshold-based discounts with explanations
- **Complexity Surcharges**: When and why they're applied
- **Customer Tier Benefits**: Tier-specific advantages
- **Limit Adjustments**: How pricing limits affected final prices

### Audit Trail

Complete audit trail for compliance:

```python
# Search pricing history
history = await pricing_service.search_pricing_history(
    material="aluminum",
    customer_tier="premium",
    date_from=datetime.now() - timedelta(days=30)
)

# Get audit trail
audit_trail = await repository.get_audit_trail(
    user_id="user123",
    date_from=datetime.now() - timedelta(days=7)
)
```

## Observability Features

### Access Points

- **Grafana Dashboards**: http://localhost:3000 (admin/admin)
- **Jaeger Tracing**: http://localhost:16686
- **Prometheus Metrics**: http://localhost:9090
- **AlertManager**: http://localhost:9093

### Key Metrics Tracked

#### Pricing Metrics
- `pricing_calculations_total` - Total calculations performed
- `pricing_errors_total` - Calculation errors
- `pricing_limit_violations_total` - Limit violations
- `pricing_calculation_duration_seconds` - Calculation duration
- `pricing_final_prices` - Distribution of final prices
- `pricing_margins` - Distribution of margins
- `active_pricing_calculations` - Currently active calculations

#### Application Metrics
- HTTP request metrics (duration, status codes)
- Database operation metrics
- System resource metrics

### Distributed Tracing

Every pricing calculation creates a trace showing:

1. **Cost Calculation Span** - Material, labor, setup costs
2. **Pricing Engine Span** - Margin and discount calculations
3. **Limit Enforcement Span** - Limit checking and adjustments
4. **Explanation Generation Span** - Documentation creation
5. **Database Operations** - MongoDB storage operations

### Alerting Rules

Comprehensive alerting for:

- High error rates in pricing calculations
- Excessive pricing limit violations
- Slow or very slow calculations
- Service availability issues
- Database connection problems

## MongoDB Storage Schema

### Pricing Explanations Collection

```javascript
{
  "calculation_id": "uuid",
  "timestamp": "ISO 8601",
  "part_specification": {
    "material": "aluminum",
    "process": "cnc",
    "dimensions": { "length_mm": 100, "width_mm": 50, "height_mm": 25 },
    "geometric_complexity_score": 3.5,
    "quantity": 50
  },
  "cost_calculation_steps": [...],
  "tier_explanations": {
    "standard": {
      "tier_name": "standard",
      "margin_percentage": 0.35,
      "margin_reasoning": "Applied 35% margin for standard service tier",
      "discount_applications": [...],
      "limit_adjustments": [...]
    }
  },
  "limits_applied": false,
  "calculation_duration_ms": 150
}
```

### Audit Log Collection

```javascript
{
  "calculation_id": "uuid",
  "user_id": "user123",
  "action": "pricing_calculation",
  "details": {
    "material": "aluminum",
    "quantity": 50,
    "limits_applied": false
  },
  "ip_address": "192.168.1.100",
  "timestamp": "ISO 8601"
}
```

## Configuration

### Environment Variables

```bash
# Service Configuration
SERVICE_NAME=fastapi-enterprise
SERVICE_VERSION=1.0.0
DEPLOYMENT_ENVIRONMENT=production

# OpenTelemetry Configuration
OTLP_ENDPOINT=http://localhost:4317
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=8000
TRACE_SAMPLE_RATE=0.1

# MongoDB Configuration
MONGODB_URL=mongodb://admin:password@localhost:27017
MONGODB_DATABASE=pricing

# Alerting Configuration
ENABLE_ALERTS=true
ALERT_EMAIL=ops-team@fastapi-enterprise.com
```

### Pricing Limits Configuration

```python
# Conservative limits for business protection
service = PricingService.with_conservative_limits()

# Aggressive limits for competitive pricing
service = PricingService.with_aggressive_limits()

# Custom limits
service = PricingService.with_custom_limits(
    min_price_per_unit=Decimal("2.00"),
    min_total_price=Decimal("50.00"),
    min_margin_pct=0.15,  # 15%
    max_discount_pct=0.25  # 25%
)
```

## Business Benefits

### For Finance Teams
- Complete transparency into pricing calculations
- Audit trail for compliance and analysis
- Margin analysis and optimization insights
- Real-time pricing performance monitoring

### For Operations Teams
- Comprehensive system monitoring
- Proactive alerting for issues
- Performance optimization insights
- Service availability tracking

### For Business Teams
- Pricing decision documentation
- Customer tier analysis
- Market competitiveness tracking
- Pricing strategy validation

## Maintenance

### Regular Tasks

```bash
# Check system health
docker-compose -f docker-compose.observability.yml ps

# View logs
docker-compose -f docker-compose.observability.yml logs -f

# Backup MongoDB data
docker exec mongodb mongodump --host localhost --db pricing --out /backup

# Clean up old data (automated via repository)
python -c "
from app.modules.pricing.repository import PricingRepository
repository = PricingRepository(database)
stats = await repository.cleanup_old_data(retention_days=365)
print(f'Cleaned up: {stats}')
"
```

### Scaling Considerations

- **MongoDB**: Use replica sets for high availability
- **Prometheus**: Consider federation for large deployments
- **Grafana**: Use external database for dashboard persistence
- **Application**: Scale horizontally with load balancer

## Troubleshooting

### Common Issues

1. **High Memory Usage**: Adjust OTEL collector memory limits
2. **Missing Metrics**: Check Prometheus scrape configuration
3. **Slow Dashboards**: Optimize Grafana queries and timeranges
4. **MongoDB Connection**: Verify authentication and network access

### Debug Commands

```bash
# Check OTEL collector logs
docker logs otel-collector

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test MongoDB connection
docker exec mongodb mongo --eval "db.adminCommand('ismaster')"

# Check application metrics endpoint
curl http://localhost:8000/metrics
```

This comprehensive system provides full visibility into your pricing operations while ensuring business transparency and compliance.
