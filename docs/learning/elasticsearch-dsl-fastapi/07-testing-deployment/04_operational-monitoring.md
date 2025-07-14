# Operational Monitoring

Production monitoring, alerting, and observability for FastAPI + Elasticsearch-DSL applications with comprehensive metrics and incident response.

## Table of Contents
- [Monitoring Stack Setup](#monitoring-stack-setup)
- [Application Metrics](#application-metrics)
- [Infrastructure Monitoring](#infrastructure-monitoring)
- [Log Management](#log-management)
- [Alerting and Notifications](#alerting-and-notifications)
- [SLA Monitoring](#sla-monitoring)
- [Incident Response](#incident-response)
- [Next Steps](#next-steps)

## Monitoring Stack Setup

### Prometheus + Grafana Stack
```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana/datasources:/etc/grafana/provisioning/datasources:ro
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring

  elasticsearch-exporter:
    image: quay.io/prometheuscommunity/elasticsearch-exporter:latest
    container_name: elasticsearch-exporter
    restart: unless-stopped
    ports:
      - "9114:9114"
    environment:
      - ES_URI=http://elasticsearch:9200
    command:
      - '--es.uri=http://elasticsearch:9200'
      - '--es.all'
      - '--es.indices'
      - '--es.shards'
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:

networks:
  monitoring:
    driver: bridge
```

### Prometheus Configuration
```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # FastAPI Application
  - job_name: 'fastapi-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # Elasticsearch
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch-exporter:9114']
    scrape_interval: 30s

  # Node metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  # Redis (if using redis-exporter)
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 15s

  # Kubernetes pods (for K8s deployment)
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
```

### Alert Rules
```yaml
# monitoring/prometheus/rules/app-alerts.yml
groups:
  - name: fastapi-app
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          (
            rate(http_requests_total{status=~"5.."}[5m]) /
            rate(http_requests_total[5m])
          ) > 0.05
        for: 2m
        labels:
          severity: critical
          service: fastapi-app
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      # High response time
      - alert: HighResponseTime
        expr: |
          histogram_quantile(0.95, 
            rate(http_request_duration_seconds_bucket[5m])
          ) > 2
        for: 3m
        labels:
          severity: warning
          service: fastapi-app
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      # Low request rate (potential service down)
      - alert: LowRequestRate
        expr: rate(http_requests_total[5m]) < 1
        for: 5m
        labels:
          severity: warning
          service: fastapi-app
        annotations:
          summary: "Low request rate detected"
          description: "Request rate is {{ $value }} requests/second"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (
            process_resident_memory_bytes{job="fastapi-app"} /
            node_memory_MemTotal_bytes
          ) > 0.8
        for: 5m
        labels:
          severity: warning
          service: fastapi-app
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

  - name: elasticsearch
    rules:
      # Elasticsearch cluster health
      - alert: ElasticsearchClusterNotHealthy
        expr: elasticsearch_cluster_health_status{color="red"} == 1
        for: 1m
        labels:
          severity: critical
          service: elasticsearch
        annotations:
          summary: "Elasticsearch cluster is not healthy"
          description: "Elasticsearch cluster health is RED"

      # High search latency
      - alert: ElasticsearchHighSearchLatency
        expr: elasticsearch_indices_search_query_time_seconds > 5
        for: 2m
        labels:
          severity: warning
          service: elasticsearch
        annotations:
          summary: "Elasticsearch high search latency"
          description: "Search latency is {{ $value }}s"

      # Low disk space
      - alert: ElasticsearchLowDiskSpace
        expr: |
          (
            elasticsearch_filesystem_data_available_bytes /
            elasticsearch_filesystem_data_size_bytes
          ) < 0.1
        for: 1m
        labels:
          severity: critical
          service: elasticsearch
        annotations:
          summary: "Elasticsearch low disk space"
          description: "Available disk space is {{ $value | humanizePercentage }}"
```

## Application Metrics

### Enhanced Metrics Collection
```python
# app/core/metrics.py
import time
import psutil
from typing import Dict, Any
from prometheus_client import (
    Counter, Histogram, Gauge, Info, generate_latest,
    CollectorRegistry, multiprocess, CONTENT_TYPE_LATEST
)
from fastapi import Request, Response
from functools import wraps

class ApplicationMetrics:
    """Comprehensive application metrics collection."""
    
    def __init__(self):
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        # Business metrics
        self.search_requests_total = Counter(
            'search_requests_total',
            'Total search requests',
            ['query_type', 'has_filters']
        )
        
        self.search_results_count = Histogram(
            'search_results_count',
            'Number of search results returned',
            buckets=(0, 1, 5, 10, 25, 50, 100, 250, 500, 1000)
        )
        
        self.elasticsearch_operations = Counter(
            'elasticsearch_operations_total',
            'Total Elasticsearch operations',
            ['operation', 'index', 'status']
        )
        
        self.elasticsearch_query_duration = Histogram(
            'elasticsearch_query_duration_seconds',
            'Elasticsearch query duration',
            ['operation', 'index']
        )
        
        # Cache metrics
        self.cache_operations = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'cache_type', 'status']
        )
        
        # System metrics
        self.active_connections = Gauge(
            'active_database_connections',
            'Number of active database connections'
        )
        
        self.memory_usage_bytes = Gauge(
            'process_memory_usage_bytes',
            'Process memory usage in bytes'
        )
        
        self.cpu_usage_percent = Gauge(
            'process_cpu_usage_percent',
            'Process CPU usage percentage'
        )
        
        # Application info
        self.app_info = Info(
            'fastapi_app_info',
            'FastAPI application information'
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_search_request(self, query_type: str, has_filters: bool, results_count: int):
        """Record search-specific metrics."""
        self.search_requests_total.labels(
            query_type=query_type,
            has_filters=str(has_filters).lower()
        ).inc()
        
        self.search_results_count.observe(results_count)
    
    def record_elasticsearch_operation(
        self,
        operation: str,
        index: str,
        status: str,
        duration: float
    ):
        """Record Elasticsearch operation metrics."""
        self.elasticsearch_operations.labels(
            operation=operation,
            index=index,
            status=status
        ).inc()
        
        self.elasticsearch_query_duration.labels(
            operation=operation,
            index=index
        ).observe(duration)
    
    def record_cache_operation(self, operation: str, cache_type: str, status: str):
        """Record cache operation metrics."""
        self.cache_operations.labels(
            operation=operation,
            cache_type=cache_type,
            status=status
        ).inc()
    
    def update_system_metrics(self):
        """Update system-level metrics."""
        # Memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        self.memory_usage_bytes.set(memory_info.rss)
        
        # CPU usage
        cpu_percent = process.cpu_percent()
        self.cpu_usage_percent.set(cpu_percent)
    
    def set_app_info(self, version: str, environment: str):
        """Set application information."""
        self.app_info.info({
            'version': version,
            'environment': environment,
            'python_version': f"{psutil.PYTHON_VERSION[0]}.{psutil.PYTHON_VERSION[1]}",
        })

# Global metrics instance
metrics = ApplicationMetrics()

def track_elasticsearch_operation(operation: str, index: str):
    """Decorator to track Elasticsearch operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                metrics.record_elasticsearch_operation(
                    operation=operation,
                    index=index,
                    status=status,
                    duration=duration
                )
        
        return wrapper
    return decorator

def track_cache_operation(cache_type: str):
    """Decorator to track cache operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            operation = func.__name__
            status = "hit" if "get" in operation else "operation"
            
            try:
                result = await func(*args, **kwargs)
                if operation.startswith("get") and result is None:
                    status = "miss"
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                metrics.record_cache_operation(
                    operation=operation,
                    cache_type=cache_type,
                    status=status
                )
        
        return wrapper
    return decorator
```

### Custom Business Metrics
```python
# app/services/metrics_service.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from elasticsearch_dsl import AsyncSearch
from app.core.metrics import metrics

class BusinessMetricsCollector:
    """Collect business-specific metrics."""
    
    def __init__(self):
        self.collection_interval = 300  # 5 minutes
        self.running = False
    
    async def start_collection(self):
        """Start background metrics collection."""
        self.running = True
        while self.running:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def stop_collection(self):
        """Stop metrics collection."""
        self.running = False
    
    async def collect_all_metrics(self):
        """Collect all business metrics."""
        tasks = [
            self.collect_search_volume_metrics(),
            self.collect_user_behavior_metrics(),
            self.collect_content_metrics(),
            self.collect_performance_metrics()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def collect_search_volume_metrics(self):
        """Collect search volume and patterns."""
        # Get search volume for last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        search = AsyncSearch(index='search_logs')
        search = search.filter('range', timestamp={
            'gte': start_time.isoformat(),
            'lte': end_time.isoformat()
        })
        
        # Aggregate by query type
        search.aggs.bucket('query_types', 'terms', field='query_type')
        search.aggs.bucket('result_counts', 'histogram', field='results_count', interval=10)
        
        response = await search.execute()
        
        # Update custom metrics (you'd implement custom Prometheus metrics)
        for bucket in response.aggregations.query_types.buckets:
            # Record query type distribution
            pass
    
    async def collect_user_behavior_metrics(self):
        """Collect user behavior patterns."""
        # Track user session metrics
        search = AsyncSearch(index='user_sessions')
        search = search.filter('range', session_start={
            'gte': 'now-1h'
        })
        
        search.aggs.metric('avg_session_duration', 'avg', field='duration_seconds')
        search.aggs.metric('avg_searches_per_session', 'avg', field='search_count')
        
        response = await search.execute()
        
        # Update user behavior metrics
        avg_duration = response.aggregations.avg_session_duration.value
        avg_searches = response.aggregations.avg_searches_per_session.value
        
        # You'd update custom Prometheus gauges here
    
    async def collect_content_metrics(self):
        """Collect content-related metrics."""
        # Track content popularity
        search = AsyncSearch(index='content_views')
        search = search.filter('range', view_time={
            'gte': 'now-24h'
        })
        
        search.aggs.bucket('popular_content', 'terms', field='content_id', size=100)
        search.aggs.bucket('category_views', 'terms', field='category')
        
        response = await search.execute()
        
        # Track content metrics
        for bucket in response.aggregations.popular_content.buckets:
            content_id = bucket.key
            view_count = bucket.doc_count
            # Update content popularity metrics
    
    async def collect_performance_metrics(self):
        """Collect application performance metrics."""
        # Update system metrics
        metrics.update_system_metrics()
        
        # Track custom performance indicators
        search = AsyncSearch(index='performance_logs')
        search = search.filter('range', timestamp={
            'gte': 'now-5m'
        })
        
        search.aggs.metric('avg_response_time', 'avg', field='response_time_ms')
        search.aggs.metric('error_rate', 'terms', field='status_code')
        
        response = await search.execute()
        
        # Update performance metrics
        if hasattr(response.aggregations, 'avg_response_time'):
            avg_response = response.aggregations.avg_response_time.value
            # Update custom response time metric

# Usage in FastAPI app
business_metrics = BusinessMetricsCollector()

@app.on_event("startup")
async def start_metrics_collection():
    asyncio.create_task(business_metrics.start_collection())

@app.on_event("shutdown")
async def stop_metrics_collection():
    await business_metrics.stop_collection()
```

## Infrastructure Monitoring

### Kubernetes Monitoring
```yaml
# monitoring/k8s/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: fastapi-app
  namespace: monitoring
  labels:
    app: fastapi-app
spec:
  selector:
    matchLabels:
      app: fastapi-app
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s

---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: elasticsearch
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: elasticsearch
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s

---
# Pod Monitor for broader pod discovery
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: search-api-pods
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: search-api
  podMetricsEndpoints:
  - port: metrics
    path: /metrics
    interval: 15s
```

### Infrastructure Dashboards
```json
# monitoring/grafana/dashboards/infrastructure.json
{
  "dashboard": {
    "title": "FastAPI + Elasticsearch Infrastructure",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ method }} {{ endpoint }}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Elasticsearch Query Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(elasticsearch_query_duration_seconds_sum[5m]) / rate(elasticsearch_query_duration_seconds_count[5m])",
            "legendFormat": "{{ index }} - {{ operation }}"
          }
        ]
      }
    ]
  }
}
```

## Log Management

### Structured Logging with ELK
```python
# app/core/logging_config.py
import logging
import json
from datetime import datetime
from typing import Dict, Any
from pythonjsonlogger import jsonlogger

class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = 'fastapi-app'
        log_record['environment'] = getattr(record, 'environment', 'unknown')
        log_record['request_id'] = getattr(record, 'request_id', None)
        log_record['user_id'] = getattr(record, 'user_id', None)
        
        # Add severity level
        if record.levelno >= logging.ERROR:
            log_record['severity'] = 'ERROR'
        elif record.levelno >= logging.WARNING:
            log_record['severity'] = 'WARNING'
        else:
            log_record['severity'] = 'INFO'

def setup_logging(log_level: str = "INFO", environment: str = "development"):
    """Setup structured logging configuration."""
    
    # Create formatter
    formatter = CustomJSONFormatter(
        fmt='%(timestamp)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # Set environment for all log records
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.environment = environment
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    # Configure specific loggers
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('elasticsearch').setLevel(logging.WARNING)

class StructuredLogger:
    """Structured logger with context support."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context for all subsequent log messages."""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear the current context."""
        self.context.clear()
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with context."""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, **kwargs)

# Usage in application
app_logger = StructuredLogger('app')

async def log_search_request(request_id: str, user_id: str, query: str, results_count: int):
    """Log search request with structured data."""
    app_logger.set_context(request_id=request_id, user_id=user_id)
    app_logger.info(
        "Search request processed",
        query=query,
        results_count=results_count,
        operation="search"
    )
```

### Log Aggregation Configuration
```yaml
# monitoring/filebeat/filebeat.yml
filebeat.inputs:
- type: container
  paths:
    - '/var/lib/docker/containers/*/*.log'
  processors:
    - add_docker_metadata:
        host: "unix:///var/run/docker.sock"
    - decode_json_fields:
        fields: ["message"]
        target: ""
        overwrite_keys: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  template.name: "filebeat"
  template.pattern: "filebeat-*"
  template.settings:
    index.number_of_shards: 1
    index.number_of_replicas: 0

setup.kibana:
  host: "kibana:5601"

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

## Alerting and Notifications

### AlertManager Configuration
```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@company.com'
  smtp_auth_username: 'alerts@company.com'
  smtp_auth_password: 'app_password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 1h
  receiver: 'default'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
    group_wait: 5s
    repeat_interval: 30m
  - match:
      service: elasticsearch
    receiver: 'elasticsearch-team'
  - match:
      alertname: HighErrorRate
    receiver: 'oncall-team'

receivers:
- name: 'default'
  email_configs:
  - to: 'team@company.com'
    subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.SortedPairs.Values | join " " }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

- name: 'critical-alerts'
  email_configs:
  - to: 'oncall@company.com'
    subject: '[CRITICAL] {{ .GroupLabels.alertname }}'
    body: |
      CRITICAL ALERT
      
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      Time: {{ .StartsAt }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/...'
    channel: '#alerts'
    title: 'Critical Alert: {{ .GroupLabels.alertname }}'
    text: |
      {{ range .Alerts }}
      {{ .Annotations.summary }}
      {{ .Annotations.description }}
      {{ end }}

- name: 'elasticsearch-team'
  email_configs:
  - to: 'elasticsearch-team@company.com'
    subject: '[Elasticsearch] {{ .GroupLabels.alertname }}'

- name: 'oncall-team'
  pagerduty_configs:
  - routing_key: 'your-pagerduty-integration-key'
    description: '{{ .GroupLabels.alertname }}: {{ .GroupLabels.instance }}'
```

### Custom Alert Webhooks
```python
# monitoring/webhook_handler.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import aiohttp
import asyncio

app = FastAPI(title="Alert Webhook Handler")

class Alert(BaseModel):
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: str = None

class AlertManagerPayload(BaseModel):
    receiver: str
    status: str
    alerts: List[Alert]
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]

class AlertProcessor:
    """Process and route alerts to various systems."""
    
    def __init__(self):
        self.handlers = {
            'slack': self.send_slack_alert,
            'teams': self.send_teams_alert,
            'discord': self.send_discord_alert,
            'custom': self.send_custom_alert
        }
    
    async def process_alerts(self, payload: AlertManagerPayload):
        """Process incoming alerts."""
        
        for alert in payload.alerts:
            severity = alert.labels.get('severity', 'info')
            service = alert.labels.get('service', 'unknown')
            
            # Route based on severity and service
            if severity == 'critical':
                await self.send_critical_alert(alert)
            elif service == 'elasticsearch':
                await self.send_elasticsearch_alert(alert)
            else:
                await self.send_general_alert(alert)
    
    async def send_critical_alert(self, alert: Alert):
        """Handle critical alerts with multiple channels."""
        tasks = [
            self.send_slack_alert(alert, urgent=True),
            self.send_teams_alert(alert),
            self.trigger_pagerduty(alert)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_slack_alert(self, alert: Alert, urgent: bool = False):
        """Send alert to Slack."""
        webhook_url = "https://hooks.slack.com/services/..."
        
        color = "danger" if alert.labels.get('severity') == 'critical' else "warning"
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"Alert: {alert.annotations.get('summary', 'Unknown')}",
                    "text": alert.annotations.get('description', ''),
                    "fields": [
                        {
                            "title": "Service",
                            "value": alert.labels.get('service', 'unknown'),
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": alert.labels.get('severity', 'info'),
                            "short": True
                        }
                    ],
                    "ts": int(alert.startsAt.timestamp()) if hasattr(alert.startsAt, 'timestamp') else None
                }
            ]
        }
        
        if urgent:
            payload["text"] = "<!channel> Critical Alert"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    print(f"Failed to send Slack alert: {response.status}")
    
    async def send_teams_alert(self, alert: Alert):
        """Send alert to Microsoft Teams."""
        webhook_url = "https://outlook.office.com/webhook/..."
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000" if alert.labels.get('severity') == 'critical' else "FFA500",
            "summary": alert.annotations.get('summary', 'Alert'),
            "sections": [
                {
                    "activityTitle": f"Alert: {alert.annotations.get('summary', 'Unknown')}",
                    "activitySubtitle": alert.annotations.get('description', ''),
                    "facts": [
                        {
                            "name": "Service",
                            "value": alert.labels.get('service', 'unknown')
                        },
                        {
                            "name": "Severity",
                            "value": alert.labels.get('severity', 'info')
                        }
                    ]
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    print(f"Failed to send Teams alert: {response.status}")
    
    async def trigger_pagerduty(self, alert: Alert):
        """Trigger PagerDuty incident."""
        api_url = "https://events.pagerduty.com/v2/enqueue"
        routing_key = "your-pagerduty-routing-key"
        
        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "dedup_key": f"{alert.labels.get('alertname', 'unknown')}-{alert.labels.get('instance', 'unknown')}",
            "payload": {
                "summary": alert.annotations.get('summary', 'Critical Alert'),
                "source": alert.labels.get('instance', 'unknown'),
                "severity": "critical",
                "custom_details": {
                    "description": alert.annotations.get('description', ''),
                    "service": alert.labels.get('service', 'unknown')
                }
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status != 202:
                    print(f"Failed to trigger PagerDuty: {response.status}")

alert_processor = AlertProcessor()

@app.post("/webhook/alertmanager")
async def handle_alertmanager_webhook(payload: AlertManagerPayload):
    """Handle AlertManager webhooks."""
    try:
        await alert_processor.process_alerts(payload)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## SLA Monitoring

### SLA Metrics Tracking
```python
# app/monitoring/sla_monitor.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class SLAStatus(Enum):
    HEALTHY = "healthy"
    AT_RISK = "at_risk"
    BREACHED = "breached"

@dataclass
class SLATarget:
    name: str
    metric_name: str
    threshold: float
    time_window: int  # minutes
    measurement_type: str  # "availability", "latency", "error_rate"

@dataclass
class SLAMeasurement:
    timestamp: datetime
    value: float
    status: SLAStatus

class SLAMonitor:
    """Monitor SLA compliance for critical services."""
    
    def __init__(self):
        self.sla_targets = {
            'api_availability': SLATarget(
                name="API Availability",
                metric_name="http_requests_total",
                threshold=99.9,  # 99.9% availability
                time_window=60,
                measurement_type="availability"
            ),
            'search_latency': SLATarget(
                name="Search Response Time",
                metric_name="search_request_duration",
                threshold=500,  # 500ms
                time_window=15,
                measurement_type="latency"
            ),
            'error_rate': SLATarget(
                name="Error Rate",
                metric_name="http_requests_error_rate",
                threshold=1.0,  # 1% error rate
                time_window=30,
                measurement_type="error_rate"
            )
        }
        
        self.measurements: Dict[str, List[SLAMeasurement]] = {
            target: [] for target in self.sla_targets.keys()
        }
        
        self.running = False
    
    async def start_monitoring(self):
        """Start SLA monitoring."""
        self.running = True
        while self.running:
            try:
                await self.collect_sla_measurements()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"SLA monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def stop_monitoring(self):
        """Stop SLA monitoring."""
        self.running = False
    
    async def collect_sla_measurements(self):
        """Collect SLA measurements for all targets."""
        current_time = datetime.utcnow()
        
        for target_id, target in self.sla_targets.items():
            try:
                measurement = await self.measure_sla_target(target)
                self.measurements[target_id].append(
                    SLAMeasurement(current_time, measurement, self.calculate_status(target, measurement))
                )
                
                # Keep only measurements within time window
                cutoff_time = current_time - timedelta(hours=24)
                self.measurements[target_id] = [
                    m for m in self.measurements[target_id] 
                    if m.timestamp > cutoff_time
                ]
                
            except Exception as e:
                print(f"Failed to measure SLA for {target_id}: {e}")
    
    async def measure_sla_target(self, target: SLATarget) -> float:
        """Measure a specific SLA target."""
        if target.measurement_type == "availability":
            return await self.measure_availability(target)
        elif target.measurement_type == "latency":
            return await self.measure_latency(target)
        elif target.measurement_type == "error_rate":
            return await self.measure_error_rate(target)
        else:
            raise ValueError(f"Unknown measurement type: {target.measurement_type}")
    
    async def measure_availability(self, target: SLATarget) -> float:
        """Measure service availability."""
        # Query Prometheus for availability metrics
        query = f"""
        (
          sum(rate(http_requests_total[{target.time_window}m])) -
          sum(rate(http_requests_total{{status_code=~"5.."}}[{target.time_window}m]))
        ) / sum(rate(http_requests_total[{target.time_window}m])) * 100
        """
        
        # This would be replaced with actual Prometheus query
        # For now, return mock data
        return 99.95
    
    async def measure_latency(self, target: SLATarget) -> float:
        """Measure service latency."""
        query = f"""
        histogram_quantile(0.95, 
          rate(http_request_duration_seconds_bucket{{endpoint="/api/search"}}[{target.time_window}m])
        ) * 1000
        """
        
        # Mock data - replace with actual Prometheus query
        return 450.0
    
    async def measure_error_rate(self, target: SLATarget) -> float:
        """Measure error rate."""
        query = f"""
        sum(rate(http_requests_total{{status_code=~"5.."}}[{target.time_window}m])) /
        sum(rate(http_requests_total[{target.time_window}m])) * 100
        """
        
        # Mock data - replace with actual Prometheus query
        return 0.5
    
    def calculate_status(self, target: SLATarget, measurement: float) -> SLAStatus:
        """Calculate SLA status based on measurement."""
        if target.measurement_type == "availability":
            if measurement >= target.threshold:
                return SLAStatus.HEALTHY
            elif measurement >= target.threshold - 1.0:
                return SLAStatus.AT_RISK
            else:
                return SLAStatus.BREACHED
        
        elif target.measurement_type in ["latency", "error_rate"]:
            if measurement <= target.threshold:
                return SLAStatus.HEALTHY
            elif measurement <= target.threshold * 1.5:
                return SLAStatus.AT_RISK
            else:
                return SLAStatus.BREACHED
        
        return SLAStatus.HEALTHY
    
    def get_sla_report(self, hours: int = 24) -> Dict[str, Dict]:
        """Generate SLA report for the specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        report = {}
        
        for target_id, measurements in self.measurements.items():
            recent_measurements = [
                m for m in measurements if m.timestamp > cutoff_time
            ]
            
            if not recent_measurements:
                continue
            
            target = self.sla_targets[target_id]
            
            # Calculate compliance percentage
            total_measurements = len(recent_measurements)
            compliant_measurements = sum(
                1 for m in recent_measurements 
                if m.status == SLAStatus.HEALTHY
            )
            
            compliance_percentage = (compliant_measurements / total_measurements) * 100
            
            # Calculate average value
            avg_value = sum(m.value for m in recent_measurements) / total_measurements
            
            # Find breaches
            breaches = [m for m in recent_measurements if m.status == SLAStatus.BREACHED]
            
            report[target_id] = {
                'target_name': target.name,
                'threshold': target.threshold,
                'compliance_percentage': round(compliance_percentage, 2),
                'average_value': round(avg_value, 2),
                'current_status': recent_measurements[-1].status.value,
                'breach_count': len(breaches),
                'measurement_count': total_measurements
            }
        
        return report

# Global SLA monitor
sla_monitor = SLAMonitor()

@app.on_event("startup")
async def start_sla_monitoring():
    asyncio.create_task(sla_monitor.start_monitoring())

@app.on_event("shutdown")
async def stop_sla_monitoring():
    await sla_monitor.stop_monitoring()

@app.get("/admin/sla-report")
async def get_sla_report(hours: int = 24):
    """Get SLA compliance report."""
    return sla_monitor.get_sla_report(hours)
```

## Incident Response

### Automated Incident Response
```python
# app/monitoring/incident_response.py
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"

@dataclass
class Incident:
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    alerts: List[str] = None

class IncidentManager:
    """Automated incident response and management."""
    
    def __init__(self):
        self.active_incidents: Dict[str, Incident] = {}
        self.incident_counter = 0
        
        # Auto-mitigation strategies
        self.mitigation_strategies = {
            'high_error_rate': self.mitigate_high_error_rate,
            'high_response_time': self.mitigate_high_response_time,
            'elasticsearch_down': self.mitigate_elasticsearch_down,
            'memory_leak': self.mitigate_memory_leak
        }
    
    async def create_incident(
        self,
        alert_name: str,
        description: str,
        severity: IncidentSeverity,
        labels: Dict[str, str]
    ) -> str:
        """Create a new incident from an alert."""
        
        self.incident_counter += 1
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{self.incident_counter:04d}"
        
        incident = Incident(
            id=incident_id,
            title=alert_name,
            description=description,
            severity=severity,
            status=IncidentStatus.OPEN,
            created_at=datetime.utcnow(),
            alerts=[alert_name]
        )
        
        self.active_incidents[incident_id] = incident
        
        # Auto-assign based on severity and service
        await self.auto_assign_incident(incident, labels)
        
        # Trigger auto-mitigation if available
        await self.attempt_auto_mitigation(incident, alert_name)
        
        # Notify stakeholders
        await self.notify_incident_created(incident)
        
        return incident_id
    
    async def auto_assign_incident(self, incident: Incident, labels: Dict[str, str]):
        """Auto-assign incident based on service and severity."""
        service = labels.get('service', 'unknown')
        
        if incident.severity == IncidentSeverity.CRITICAL:
            incident.assigned_to = "oncall-lead"
        elif service == "elasticsearch":
            incident.assigned_to = "elasticsearch-team"
        elif service == "fastapi-app":
            incident.assigned_to = "backend-team"
        else:
            incident.assigned_to = "general-oncall"
    
    async def attempt_auto_mitigation(self, incident: Incident, alert_name: str):
        """Attempt automatic mitigation strategies."""
        
        # Map alert names to mitigation strategies
        alert_to_strategy = {
            'HighErrorRate': 'high_error_rate',
            'HighResponseTime': 'high_response_time',
            'ElasticsearchDown': 'elasticsearch_down',
            'HighMemoryUsage': 'memory_leak'
        }
        
        strategy = alert_to_strategy.get(alert_name)
        if strategy and strategy in self.mitigation_strategies:
            incident.status = IncidentStatus.MITIGATING
            
            try:
                await self.mitigation_strategies[strategy](incident)
            except Exception as e:
                print(f"Auto-mitigation failed for {incident.id}: {e}")
                incident.status = IncidentStatus.INVESTIGATING
    
    async def mitigate_high_error_rate(self, incident: Incident):
        """Mitigation strategy for high error rate."""
        # 1. Scale up application instances
        await self.scale_application(replicas=6)
        
        # 2. Enable circuit breaker
        await self.enable_circuit_breaker()
        
        # 3. Redirect traffic to healthy instances
        await self.update_load_balancer_health_checks()
        
        print(f"Auto-mitigation applied for {incident.id}: scaled up and enabled circuit breaker")
    
    async def mitigate_high_response_time(self, incident: Incident):
        """Mitigation strategy for high response time."""
        # 1. Increase cache TTL
        await self.adjust_cache_settings(ttl_multiplier=2)
        
        # 2. Scale up Elasticsearch
        await self.scale_elasticsearch()
        
        # 3. Enable query optimization
        await self.enable_query_optimization()
        
        print(f"Auto-mitigation applied for {incident.id}: optimized caching and scaling")
    
    async def mitigate_elasticsearch_down(self, incident: Incident):
        """Mitigation strategy for Elasticsearch outage."""
        # 1. Enable fallback search
        await self.enable_fallback_search()
        
        # 2. Restart Elasticsearch service
        await self.restart_elasticsearch_service()
        
        # 3. Activate read-only mode
        await self.activate_readonly_mode()
        
        print(f"Auto-mitigation applied for {incident.id}: enabled fallback search")
    
    async def mitigate_memory_leak(self, incident: Incident):
        """Mitigation strategy for memory leak."""
        # 1. Rolling restart of application pods
        await self.rolling_restart_application()
        
        # 2. Reduce cache size
        await self.adjust_cache_settings(size_multiplier=0.5)
        
        print(f"Auto-mitigation applied for {incident.id}: performed rolling restart")
    
    async def scale_application(self, replicas: int):
        """Scale application instances."""
        # Kubernetes scaling command
        command = f"kubectl scale deployment fastapi-app --replicas={replicas}"
        # Execute scaling command
        print(f"Scaling application to {replicas} replicas")
    
    async def enable_circuit_breaker(self):
        """Enable circuit breaker protection."""
        # Update configuration to enable circuit breaker
        print("Circuit breaker enabled")
    
    async def update_load_balancer_health_checks(self):
        """Update load balancer health check configuration."""
        print("Load balancer health checks updated")
    
    async def adjust_cache_settings(self, ttl_multiplier: float = 1.0, size_multiplier: float = 1.0):
        """Adjust cache settings."""
        print(f"Cache settings adjusted: TTL x{ttl_multiplier}, Size x{size_multiplier}")
    
    async def scale_elasticsearch(self):
        """Scale Elasticsearch cluster."""
        print("Elasticsearch cluster scaled up")
    
    async def enable_query_optimization(self):
        """Enable query optimization features."""
        print("Query optimization enabled")
    
    async def enable_fallback_search(self):
        """Enable fallback search mechanism."""
        print("Fallback search enabled")
    
    async def restart_elasticsearch_service(self):
        """Restart Elasticsearch service."""
        print("Elasticsearch service restarted")
    
    async def activate_readonly_mode(self):
        """Activate read-only mode for the application."""
        print("Read-only mode activated")
    
    async def rolling_restart_application(self):
        """Perform rolling restart of application."""
        command = "kubectl rollout restart deployment/fastapi-app"
        print("Rolling restart initiated")
    
    async def notify_incident_created(self, incident: Incident):
        """Notify relevant teams about incident creation."""
        # Send notifications via Slack, email, PagerDuty, etc.
        print(f"Incident {incident.id} created and assigned to {incident.assigned_to}")
    
    async def resolve_incident(self, incident_id: str, resolution_note: str):
        """Resolve an incident."""
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = datetime.utcnow()
            
            # Calculate resolution time
            resolution_time = incident.resolved_at - incident.created_at
            
            print(f"Incident {incident_id} resolved in {resolution_time}")
            
            # Remove from active incidents
            del self.active_incidents[incident_id]
    
    def get_incident_metrics(self) -> Dict[str, any]:
        """Get incident response metrics."""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        # This would typically query a database
        # For now, return mock metrics
        return {
            'active_incidents': len(self.active_incidents),
            'incidents_last_24h': 5,
            'avg_resolution_time_minutes': 45,
            'critical_incidents_open': sum(
                1 for i in self.active_incidents.values() 
                if i.severity == IncidentSeverity.CRITICAL
            )
        }

# Global incident manager
incident_manager = IncidentManager()

@app.post("/webhook/create-incident")
async def create_incident_webhook(
    alert_name: str,
    description: str,
    severity: str,
    labels: Dict[str, str]
):
    """Create incident from external alert."""
    severity_enum = IncidentSeverity(severity.lower())
    incident_id = await incident_manager.create_incident(
        alert_name, description, severity_enum, labels
    )
    return {"incident_id": incident_id}

@app.get("/admin/incidents/metrics")
async def get_incident_metrics():
    """Get incident response metrics."""
    return incident_manager.get_incident_metrics()
```

## Next Steps

1. **[Basic Patterns](../examples/01_basic-patterns.md)** - Essential implementation examples
2. **[Security & Authentication](../06-production-patterns/02_security-authentication.md)** - API security patterns
3. **[Performance Optimization](../06-production-patterns/03_performance-optimization.md)** - Scaling and efficiency

## Additional Resources

- **Prometheus Documentation**: [prometheus.io/docs](https://prometheus.io/docs/)
- **Grafana Documentation**: [grafana.com/docs](https://grafana.com/docs/)
- **ELK Stack Guide**: [elastic.co/what-is/elk-stack](https://www.elastic.co/what-is/elk-stack)
- **SLO/SLI Best Practices**: [sre.google/sre-book](https://sre.google/sre-book/)