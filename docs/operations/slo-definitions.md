# Service Level Objectives (SLO), Indicators (SLI), and Agreements (SLA)

This document defines the Service Level Objectives (SLOs), Service Level Indicators (SLIs), and Service Level Agreements (SLAs) for the FastAPI Enterprise application.

## Overview

**SLO** (Service Level Objective): A target value or range of values for a service level that is measured by an SLI.

**SLI** (Service Level Indicator): A carefully defined quantitative measure of some aspect of the level of service that is provided.

**SLA** (Service Level Agreement): A business contract that defines service commitments, typically with financial or business consequences for missing them.

## Defined SLOs

### 1. Availability SLO

**SLO Target:** 99.9% availability (3 nines)

**SLI:** Percentage of successful HTTP requests (status 2xx) out of total requests over a 30-day rolling window.

**SLI Formula:**
```
SLI = (sum of 2xx requests over 30 days) / (sum of total requests over 30 days) * 100
```

**Error Budget:** 0.1% (allows for 43.2 minutes of downtime per month)

**Calculation Window:** 30-day rolling window

**Compliance Criteria:**
- ✅ Compliant: SLI >= 99.9%
- ❌ Non-Compliant: SLI < 99.9%

**SLA:** If availability falls below 99.9% for more than 30 minutes in a calendar month, service credits or compensation may apply per customer contract.

### 2. Latency SLO (p95)

**SLO Target:** 95% of requests complete within 500ms

**SLI:** Percentage of requests with response time <= 500ms over a 7-day rolling window.

**SLI Formula:**
```
SLI = (sum of requests with duration <= 500ms over 7 days) / (sum of total requests over 7 days) * 100
```

**Error Budget:** 5% of requests can exceed 500ms

**Calculation Window:** 7-day rolling window

**Compliance Criteria:**
- ✅ Compliant: SLI >= 95%
- ❌ Non-Compliant: SLI < 95%

**SLA:** If more than 5% of requests exceed 500ms for more than 1 hour, notification alerts will be triggered.

### 3. Latency SLO (p99)

**SLO Target:** 99% of requests complete within 1 second

**SLI:** Percentage of requests with response time <= 1000ms over a 7-day rolling window.

**SLI Formula:**
```
SLI = (sum of requests with duration <= 1000ms over 7 days) / (sum of total requests over 7 days) * 100
```

**Error Budget:** 1% of requests can exceed 1000ms

**Calculation Window:** 7-day rolling window

**Compliance Criteria:**
- ✅ Compliant: SLI >= 99%
- ❌ Non-Compliant: SLI < 99%

**SLA:** Critical alerts triggered if more than 1% of requests exceed 1 second for more than 15 minutes.

### 4. Pricing Calculation Success SLO

**SLO Target:** 95% of pricing calculations succeed without errors

**SLI:** Percentage of successful pricing calculations out of total pricing calculations over a 7-day rolling window.

**SLI Formula:**
```
SLI = (sum of successful pricing calculations over 7 days) / (sum of total pricing calculations over 7 days) * 100
```

**Error Budget:** 5% of pricing calculations can fail

**Calculation Window:** 7-day rolling window

**Compliance Criteria:**
- ✅ Compliant: SLI >= 95%
- ❌ Non-Compliant: SLI < 95%

**SLA:** If pricing calculation success rate falls below 95% for more than 30 minutes, on-call engineers are notified.

## Error Budget

### Availability Error Budget

- **Total Budget:** 0.1% of requests can fail (99.9% availability target)
- **Monthly Budget:** ~43.2 minutes of downtime or equivalent error rate
- **Burn Rate Alerts:**
  - **Warning:** Error budget burning at 1x rate (on track to exhaust in 30 days)
  - **Critical:** Error budget burning at 6x rate (on track to exhaust in 5 days)

### Latency Error Budget

- **p95 Budget:** 5% of requests can exceed 500ms
- **p99 Budget:** 1% of requests can exceed 1000ms
- **Burn Rate Alerts:** Similar to availability - tracks how quickly error budget is consumed

## Monitoring and Alerting

### SLO Compliance Dashboards

The SLO Dashboard in Grafana (`slo-dashboard.json`) provides:

1. **Real-time SLI values** compared to SLO targets
2. **Error budget remaining** as a percentage
3. **Error budget burn rate** to predict budget exhaustion
4. **Compliance status** for each SLO
5. **Historical trends** showing SLI performance over time

### Alerting Rules

Error budget burn rate alerts are configured in Prometheus (`pricing_alerts.yml`):

- **Warning:** Burn rate > 1x (error budget will be exhausted in 30 days)
- **Critical:** Burn rate > 6x (error budget will be exhausted in 5 days)

When burn rate alerts fire:
1. Investigation begins to identify root cause
2. Appropriate incident response procedures are followed
3. Error budget is tracked to determine if SLO will be met

## SLO Review Process

### Regular Reviews

- **Weekly:** Review error budget consumption and burn rates
- **Monthly:** Review SLO compliance and adjust targets if needed
- **Quarterly:** Comprehensive SLO review with stakeholders

### SLO Adjustment

SLOs may be adjusted if:
- Historical data shows consistent over-performance (can raise target)
- Business requirements change
- Infrastructure changes affect achievable targets
- Customer feedback indicates need for different targets

Any SLO changes require:
1. Stakeholder approval
2. SLA contract updates (if applicable)
3. Dashboard and alert updates
4. Team communication

## Best Practices

### Error Budget Usage

1. **Normal Operations:** Use error budget conservatively for planned maintenance
2. **Incidents:** Error budget consumed during incidents should trigger post-mortem
3. **Rollouts:** Reserve error budget for new deployments
4. **Balancing:** Balance reliability work with feature development using error budget

### SLI Selection

SLIs are chosen to:
- **Measure what matters:** Track metrics that directly impact user experience
- **Be measurable:** Can be accurately measured with available tooling
- **Be actionable:** Changes to SLI values can drive meaningful improvements
- **Avoid gaming:** Cannot be easily manipulated without improving actual service quality

### SLO Target Selection

SLO targets are set to:
- **Be achievable:** Based on historical performance data
- **Have business value:** Aligned with customer expectations and SLA commitments
- **Include buffer:** Account for expected variation and planned work
- **Be reviewed regularly:** Adjusted based on actual performance and business needs

## References

- [Google SRE Book - SLOs](https://sre.google/sre-book/service-level-objectives/)
- [Prometheus SLO Examples](https://github.com/slo-generator/slo-generator)
- [Error Budget Policy](https://sre.google/workbook/error-budget-policy/)

## Dashboard Access

- **SLO Dashboard:** `http://localhost:3000/d/slo-dashboard`
- **Golden 4 Metrics Dashboard:** `http://localhost:3000/d/enterprise-metrics`
- **Prometheus:** `http://localhost:9090`
- **Grafana:** `http://localhost:3000` (admin/admin)

## Metrics Reference

All SLO calculations use Prometheus metrics:

- **Availability:** `http_server_request_duration_seconds_count{status=~"2.."}` / `http_server_request_duration_seconds_count`
- **Latency:** `http_server_request_duration_seconds_bucket{le="0.5"}` / `http_server_request_duration_seconds_count`
- **Pricing Success:** `pricing_calculations_total{status="success"}` / `pricing_calculations_total`

Query examples can be found in the SLO dashboard JSON configuration.
