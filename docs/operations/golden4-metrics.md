# Golden 4 Metrics Implementation

This document describes the complete implementation of the **Four Golden Signals** as described in Google's SRE book, plus **SLO-specific metrics** for monitoring service level objectives.

## Overview

The **Golden 4 metrics** are the four key metrics that matter for monitoring user-facing systems:

1. **Latency** - How long requests take
2. **Traffic** - How much demand is on the system
3. **Errors** - The rate of requests that fail
4. **Saturation** - How "full" the service is

## Architecture

The metrics implementation follows **Hexagonal Architecture** principles:

```
┌─────────────────────────────────────────────────────────────┐
│  INBOUND ADAPTER (Web)                                      │
│  ├── Golden4MetricsMiddleware                               │
│  │   └── Records metrics for every HTTP request             │
│  └── Health Check Endpoints                                 │
│      └── Record availability metrics                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  PORTS (Interfaces)                                         │
│  ├── HTTPMetricsPort        - HTTP request metrics          │
│  ├── SystemMetricsPort      - System resource metrics       │
│  └── SLOMetricsPort         - SLO compliance metrics        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  OUTBOUND ADAPTER (Prometheus)                              │
│  ├── PrometheusHTTPMetricsAdapter                           │
│  ├── PrometheusSystemMetricsAdapter                         │
│  └── PrometheusSLOMetricsAdapter                            │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
                    Prometheus /metrics
```

## File Structure

```
app/
├── adapter/
│   ├── inbound/
│   │   └── web/
│   │       └── metrics_middleware.py          # Golden4MetricsMiddleware
│   └── outbound/
│       └── telemetry/
│           ├── golden4_metrics_adapter.py     # Prometheus adapters
│           └── metrics_adapter.py             # Legacy pricing metrics
├── core/
│   ├── port/
│   │   └── outbound/
│   │       └── metrics_ports.py               # Port interfaces
│   └── background_tasks.py                    # Metrics collectors
└── main.py                                     # Middleware registration
```

## Metrics Catalog

### 1. Latency Metrics (Response Time)

#### `http_server_request_duration_seconds`
**Type:** Histogram
**Labels:** method, route, status
**Buckets:** 5ms, 10ms, 25ms, 50ms, 75ms, 100ms, 250ms, 500ms, 750ms, 1s, 2.5s, 5s, 7.5s, 10s, +Inf

**Description:** Duration of HTTP requests in seconds. Buckets are optimized for calculating p50, p95, and p99 latencies.

**SLO Usage:**
- **p95 SLO (500ms):** 95% of requests should complete within 500ms
- **p99 SLO (1s):** 99% of requests should complete within 1 second

**PromQL Examples:**
```promql
# p95 latency across all endpoints
histogram_quantile(0.95, sum(rate(http_server_request_duration_seconds_bucket[5m])) by (le))

# p99 latency for specific endpoint
histogram_quantile(0.99, sum(rate(http_server_request_duration_seconds_bucket{route="/api/v1/pricing"}[5m])) by (le))

# Requests exceeding 500ms (for SLO calculation)
sum(rate(http_server_request_duration_seconds_bucket{le="0.5"}[7d])) / sum(rate(http_server_request_duration_seconds_count[7d]))
```

### 2. Traffic Metrics (Request Rate)

#### `http_server_requests_total`
**Type:** Counter
**Labels:** method, route, status

**Description:** Total count of all HTTP requests, labeled by method, path, and status code.

**SLO Usage:**
- **Availability SLO (99.9%):** Calculate success rate from status codes

**PromQL Examples:**
```promql
# Total requests per second
rate(http_server_requests_total[5m])

# Requests per second by endpoint
sum(rate(http_server_requests_total[5m])) by (route)

# Success rate (2xx responses)
sum(rate(http_server_requests_total{status=~"2.."}[5m])) / sum(rate(http_server_requests_total[5m]))
```

#### `http_server_active_requests`
**Type:** Gauge

**Description:** Number of HTTP requests currently being processed.

**PromQL Examples:**
```promql
# Current active requests
http_server_active_requests

# Peak concurrent requests in last hour
max_over_time(http_server_active_requests[1h])
```

#### `http_server_request_size_bytes` & `http_server_response_size_bytes`
**Type:** Histogram
**Labels:** method, route
**Buckets:** 100, 1KB, 10KB, 100KB, 1MB, 10MB, +Inf

**Description:** Size of HTTP requests and responses in bytes.

**PromQL Examples:**
```promql
# Average request size
rate(http_server_request_size_bytes_sum[5m]) / rate(http_server_request_size_bytes_count[5m])

# p95 response size
histogram_quantile(0.95, sum(rate(http_server_response_size_bytes_bucket[5m])) by (le))
```

### 3. Error Metrics (Error Rate)

#### `http_server_errors_total`
**Type:** Counter
**Labels:** method, route, status, error_type

**Description:** Total count of HTTP errors (status >= 400), with detailed error type classification.

**Error Types:**
- `bad_request` (400)
- `unauthorized` (401)
- `forbidden` (403)
- `not_found` (404)
- `validation_error` (422)
- `rate_limit` (429)
- `client_error` (4xx)
- `internal_error` (500)
- `bad_gateway` (502)
- `service_unavailable` (503)
- `gateway_timeout` (504)
- `server_error` (5xx)

**SLO Usage:**
- **Availability SLO:** Track 5xx errors for service availability

**PromQL Examples:**
```promql
# Error rate (all errors)
rate(http_server_errors_total[5m])

# Error rate by type
sum(rate(http_server_errors_total[5m])) by (error_type)

# Server error rate (5xx)
sum(rate(http_server_errors_total{status=~"5.."}[5m]))

# Error percentage
sum(rate(http_server_errors_total[5m])) / sum(rate(http_server_requests_total[5m])) * 100
```

### 4. Saturation Metrics (Resource Usage)

#### `system_cpu_usage_percent`
**Type:** Gauge

**Description:** System CPU usage as a percentage (0-100).

**Collection:** Automatically collected every 15 seconds by `SystemMetricsCollector`.

**PromQL Examples:**
```promql
# Current CPU usage
system_cpu_usage_percent

# Average CPU over last hour
avg_over_time(system_cpu_usage_percent[1h])

# Alert if CPU > 80% for 5 minutes
system_cpu_usage_percent > 80
```

#### `system_memory_bytes`
**Type:** Gauge
**Labels:** type (used, available)

**Description:** System memory usage in bytes.

**PromQL Examples:**
```promql
# Memory utilization percentage
(system_memory_bytes{type="used"} / (system_memory_bytes{type="used"} + system_memory_bytes{type="available"})) * 100

# Available memory in GB
system_memory_bytes{type="available"} / 1024 / 1024 / 1024
```

#### `db_connection_pool_connections`
**Type:** Gauge
**Labels:** pool (postgres, mongodb, redis), state (active, idle)

**Description:** Number of database connections in each pool.

**PromQL Examples:**
```promql
# Active connections by pool
db_connection_pool_connections{state="active"}

# Connection pool utilization
(db_connection_pool_connections{state="active"} / db_connection_pool_max_size) * 100

# Idle connections
db_connection_pool_connections{state="idle"}
```

#### `db_connection_pool_max_size`
**Type:** Gauge
**Labels:** pool

**Description:** Maximum size of each database connection pool.

### SLO-Specific Metrics

#### `service_availability`
**Type:** Gauge
**Labels:** service (api, postgres, mongodb, redis)

**Description:** Service availability status (1 = available, 0 = unavailable).

**PromQL Examples:**
```promql
# Current availability status
service_availability

# Services that are down
service_availability == 0

# Uptime percentage (last 30 days)
avg_over_time(service_availability[30d]) * 100
```

#### `slo_compliance`
**Type:** Gauge
**Labels:** slo_name (availability, latency_p95, latency_p99)

**Description:** SLO compliance status (1 = compliant, 0 = non-compliant).

#### `slo_target` & `slo_actual`
**Type:** Gauge
**Labels:** slo_name

**Description:** Target and actual SLO values.

#### `slo_error_budget_consumed_percent`
**Type:** Gauge
**Labels:** slo_name

**Description:** Percentage of error budget consumed (0-100).

#### `slo_error_budget_burn_rate`
**Type:** Gauge
**Labels:** slo_name

**Description:** Error budget burn rate (1x = normal consumption, 6x = rapid burn).

**PromQL Examples:**
```promql
# Error budget remaining
100 - slo_error_budget_consumed_percent

# Alert on rapid burn rate
slo_error_budget_burn_rate{slo_name="availability"} > 6

# Days until error budget exhaustion
(100 - slo_error_budget_consumed_percent) / slo_error_budget_burn_rate
```

### Application Info

#### `application_info`
**Type:** Info

**Description:** Static application metadata (name, version, environment).

**PromQL Examples:**
```promql
# Application version
application_info
```

## SLO Calculations

### Availability SLO (99.9%)

**Target:** 99.9% of requests should succeed (status 2xx)

**Calculation:**
```promql
# SLI (30-day rolling window)
sum(rate(http_server_request_duration_seconds_count{status=~"2.."}[30d]))
/
sum(rate(http_server_request_duration_seconds_count[30d]))
* 100

# Error budget remaining
100 - (
  (1 - (sum(rate(http_server_request_duration_seconds_count{status=~"2.."}[30d])) / sum(rate(http_server_request_duration_seconds_count[30d]))))
  /
  (1 - 0.999)
) * 100
```

### Latency p95 SLO (500ms)

**Target:** 95% of requests should complete within 500ms

**Calculation:**
```promql
# SLI (7-day rolling window)
sum(rate(http_server_request_duration_seconds_bucket{le="0.5"}[7d]))
/
sum(rate(http_server_request_duration_seconds_count[7d]))
* 100
```

### Latency p99 SLO (1s)

**Target:** 99% of requests should complete within 1 second

**Calculation:**
```promql
# SLI (7-day rolling window)
sum(rate(http_server_request_duration_seconds_bucket{le="1.0"}[7d]))
/
sum(rate(http_server_request_duration_seconds_count[7d]))
* 100
```

## Middleware Implementation

The `Golden4MetricsMiddleware` automatically records metrics for every HTTP request:

```python
class Golden4MetricsMiddleware(BaseHTTPMiddleware):
    """
    Records Golden 4 metrics for all requests:

    1. Latency - Request duration histogram
    2. Traffic - Request counter
    3. Errors - Error counter (status >= 400)
    4. Saturation - Active requests gauge
    """
```

**Request Flow:**
1. Increment `http_server_active_requests` (saturation)
2. Record `http_server_request_size_bytes` if available
3. Process request and measure duration
4. Record `http_server_response_size_bytes` if available
5. Record `http_server_request_duration_seconds` (latency)
6. Increment `http_server_requests_total` (traffic)
7. If error, increment `http_server_errors_total` (errors)
8. Decrement `http_server_active_requests`

## Background Collectors

### SystemMetricsCollector

**Interval:** 15 seconds
**Collects:**
- CPU usage (via psutil)
- Memory usage (via psutil)
- Connection pool metrics (on-demand)

**Started:** Application startup
**Stopped:** Application shutdown

### SLOMetricsCollector

**Interval:** 60 seconds
**Collects:**
- Service availability status
- SLO compliance calculations
- Error budget consumption

**Note:** Most SLO calculations are done in Prometheus/Grafana queries using the raw HTTP metrics.

## Accessing Metrics

### Prometheus /metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

### Grafana Dashboards

- **Enterprise Metrics Dashboard:** `http://localhost:3000/d/enterprise-metrics`
- **SLO Dashboard:** `http://localhost:3000/d/slo-dashboard`
- **Pricing Dashboard:** `http://localhost:3000/d/pricing-dashboard`

### Prometheus Console

```bash
# Open Prometheus UI
open http://localhost:9090
```

## Alerting Rules

See `observability/pricing_alerts.yml` for Prometheus alerting rules based on these metrics.

Example alerts:
- High latency (p95 > 500ms)
- High error rate (> 1%)
- SLO error budget burn rate > 6x
- CPU usage > 80%
- Memory usage > 90%
- Database connection pool saturation

## Testing Metrics

### 1. Generate Traffic

```bash
# Single request
curl -X POST http://localhost:8000/api/v1/pricing \
  -H "Content-Type: application/json" \
  -d '{
    "material": "aluminum",
    "process": "cnc",
    "quantity": 100,
    "dimensions": {"length": 100, "width": 50, "height": 25},
    "geometric_complexity_score": 2.5
  }'

# Load test (requires k6)
k6 run k6-load-test.js
```

### 2. Check Metrics

```bash
# View all metrics
curl http://localhost:8000/metrics | grep -E "^(http_|system_|slo_)"

# Check specific metrics
curl -s http://localhost:8000/metrics | grep http_server_request_duration_seconds
```

### 3. Query Prometheus

```bash
# p95 latency
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(http_server_request_duration_seconds_bucket[5m]))'

# Request rate
curl 'http://localhost:9090/api/v1/query?query=rate(http_server_requests_total[5m])'

# Error rate
curl 'http://localhost:9090/api/v1/query?query=rate(http_server_errors_total[5m])'
```

## Troubleshooting

### Metrics Not Showing Up

1. **Check middleware is registered:**
   ```python
   # In app/main.py
   app.add_middleware(Golden4MetricsMiddleware)
   ```

2. **Verify /metrics endpoint:**
   ```bash
   curl http://localhost:8000/metrics
   ```

3. **Check background collectors are running:**
   ```
   # Look for startup logs
   ✅ System metrics collector started
   ✅ SLO metrics collector started
   ```

### High Cardinality Issues

If you see too many unique metric labels:

1. **Path normalization** - UUIDs and IDs are replaced with `{id}` placeholder
2. **Limit label values** - Only standard HTTP methods and status codes
3. **Monitor cardinality:**
   ```promql
   # Count unique label combinations
   count(http_server_requests_total)
   ```

### Missing System Metrics

If CPU/memory metrics aren't showing:

1. **Install psutil:**
   ```bash
   uv pip install psutil
   ```

2. **Check collector logs:**
   ```
   ⚠️ psutil not installed, system metrics will not be collected
   ```

## Best Practices

1. **Query Aggregation:** Always aggregate metrics before visualizing:
   ```promql
   # Good - aggregated
   sum(rate(http_server_requests_total[5m])) by (route)

   # Bad - too granular
   rate(http_server_requests_total[5m])
   ```

2. **Time Windows:** Use appropriate time windows for queries:
   - Real-time monitoring: `[5m]`
   - SLO calculations: `[7d]` or `[30d]`
   - Capacity planning: `[30d]` or `[90d]`

3. **Label Cardinality:** Keep label values bounded to prevent metric explosion

4. **Recording Rules:** Pre-compute expensive queries as recording rules in Prometheus

## References

- [Google SRE Book - The Four Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [SLO Definitions](./slo-definitions.md)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
