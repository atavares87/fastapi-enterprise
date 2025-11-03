# ELK Stack Configuration

## Overview

The application uses the **ELK Stack** (Elasticsearch, Filebeat, Kibana) for centralized log aggregation, search, and visualization. This follows industry-standard best practices for log management.

**Reference**: https://www.elastic.co/what-is/elk-stack

## Architecture

```
Application Logs (JSON)
    ↓ (stdout)
Docker Containers
    ↓ (Filebeat collects)
Elasticsearch (Storage & Search)
    ↓ (Kibana queries)
Kibana (Visualization & Dashboards)
```

## Components

### 1. Elasticsearch
- **Purpose**: Search and analytics engine
- **Port**: 9200 (HTTP API)
- **Data**: Stores all application logs with indexing
- **Version**: 8.11.0 (latest stable)

### 2. Filebeat
- **Purpose**: Lightweight log shipper (replaces Logstash for most use cases)
- **Why Filebeat**: Lighter, faster, uses less resources than Logstash
- **Function**: Collects logs from Docker containers and sends to Elasticsearch
- **Version**: 8.11.0

### 3. Kibana
- **Purpose**: Log visualization, search, and dashboards
- **Port**: 5601 (Web UI)
- **Function**: Query Elasticsearch and create visualizations
- **Version**: 8.11.0

## Configuration

### Application Logging

The application automatically outputs JSON logs when `ELK_ENABLED=true`:

```python
# Environment variable
ELK_ENABLED=true
LOG_FORMAT=json  # Automatically set when ELK_ENABLED=true
```

Logs are structured with:
- Timestamp (`timestamp`)
- Log level (`level`)
- Logger name (`logger`)
- Event message (`event`)
- Application context (`app`, `version`)
- Caller info in debug mode (`filename`, `lineno`)

### Filebeat Configuration

Located at: `observability/filebeat.yml`

**Key Features**:
- Collects from Docker containers (stdout)
- Collects from log files in `/app/logs`
- Parses JSON logs automatically
- Adds Docker metadata (container name, labels)
- Enriches with host metadata
- Outputs to Elasticsearch with daily indices

**Index Pattern**: `fastapi-enterprise-logs-YYYY.MM.DD`

### Kibana Configuration

**Index Pattern**: `fastapi-enterprise-logs-*`
**Time Field**: `@timestamp`

## Usage

### Starting the Stack

```bash
# Start all services including ELK
docker-compose up -d elasticsearch filebeat kibana

# Or start everything
docker-compose up -d
```

### Accessing Kibana

1. **Open Kibana**: http://localhost:5601
2. **Create Index Pattern** (if not auto-provisioned):
   - Go to: Stack Management → Index Patterns
   - Pattern: `fastapi-enterprise-logs-*`
   - Time field: `@timestamp`
3. **Explore Logs**: Discover → Select index pattern

### Searching Logs

#### Basic Search
```
event:"HTTP request completed"
```

#### Filter by Level
```
level:error
```

#### Filter by Application
```
app:"FastAPI Enterprise"
```

#### Search with Fields
```
method:POST AND status_code:500
```

#### Time Range
- Use time picker in Kibana UI
- Last 15 minutes, 1 hour, 24 hours, etc.

### Example Queries

#### Find All Errors
```
level:error
```

#### Find Slow Requests (>1s)
```
event:"HTTP request completed" AND duration_seconds:>1.0
```

#### Find Requests by Endpoint
```
handler:"/api/v1/pricing"
```

#### Find Pricing Errors
```
event:"pricing" AND level:error
```

#### Find by Status Code
```
status_code:500 OR status_code:502
```

### Creating Dashboards

1. Go to **Dashboard** in Kibana
2. Create visualization:
   - **Pie Chart**: Error distribution by level
   - **Line Chart**: Request rate over time
   - **Data Table**: Top 10 error messages
   - **Vertical Bar**: Requests by HTTP method
3. Save to dashboard

### Log Fields

Common fields in logs:

| Field | Type | Description |
|-------|------|-------------|
| `@timestamp` | date | Log timestamp (ISO 8601) |
| `level` | keyword | Log level (info, warning, error) |
| `event` | text | Event message |
| `app` | keyword | Application name |
| `version` | keyword | Application version |
| `logger` | keyword | Logger name (module) |
| `method` | keyword | HTTP method |
| `url` | text | Request URL |
| `status_code` | number | HTTP status code |
| `duration_seconds` | number | Request duration |
| `error` | text | Error message |
| `exception_type` | keyword | Exception class name |

## Best Practices

### 1. Use JSON Logging
✅ **Always use JSON format** when ELK is enabled
```python
LOG_FORMAT=json
ELK_ENABLED=true
```

### 2. Structured Logging
✅ **Use structured fields** for better filtering
```python
logger.info(
    "HTTP request completed",
    method="POST",
    url="/api/v1/pricing",
    status_code=200,
    duration_seconds=0.123
)
```

### 3. Index Lifecycle Management
- **Retention**: 30 days default (configurable in Filebeat)
- **Indices**: Daily rotation (`fastapi-enterprise-logs-2024-01-15`)
- **Cleanup**: Old indices auto-deleted after retention period

### 4. Production Considerations

⚠️ **Security**: Enable X-Pack Security in production
```yaml
xpack.security.enabled=true
```

⚠️ **Resource Limits**: Adjust Elasticsearch memory
```yaml
ES_JAVA_OPTS=-Xms2g -Xmx2g  # For production
```

⚠️ **Replication**: Use multiple Elasticsearch nodes
```yaml
discovery.type=multi-node
```

## Troubleshooting

### No Logs in Kibana

1. **Check Elasticsearch**:
   ```bash
   curl http://localhost:9200/_cluster/health
   ```

2. **Check Filebeat**:
   ```bash
   docker logs filebeat
   ```

3. **Check Indices**:
   ```bash
   curl http://localhost:9200/_cat/indices
   ```

4. **Verify Log Format**:
   ```bash
   docker logs web | head -1 | jq .
   ```

### Filebeat Not Collecting

1. **Check Docker Socket**:
   ```bash
   ls -la /var/run/docker.sock
   ```

2. **Check Filebeat Config**:
   ```bash
   docker exec filebeat filebeat test config
   ```

3. **Check Filebeat Logs**:
   ```bash
   docker logs filebeat | tail -50
   ```

### Elasticsearch Not Starting

1. **Check Memory**:
   ```bash
   docker stats elasticsearch
   ```

2. **Increase Memory** (if needed):
   ```yaml
   ES_JAVA_OPTS=-Xms1g -Xmx1g
   ```

3. **Check Logs**:
   ```bash
   docker logs elasticsearch
   ```

## Monitoring

### Elasticsearch Health
```bash
curl http://localhost:9200/_cluster/health?pretty
```

### Index Stats
```bash
curl http://localhost:9200/fastapi-enterprise-logs-*/_stats?pretty
```

### Search Test
```bash
curl -X GET "http://localhost:9200/fastapi-enterprise-logs-*/_search?q=level:error&pretty"
```

## References

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Filebeat Documentation](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [ELK Stack Best Practices](https://www.elastic.co/guide/en/beats/libbeat/current/best-practices.html)
