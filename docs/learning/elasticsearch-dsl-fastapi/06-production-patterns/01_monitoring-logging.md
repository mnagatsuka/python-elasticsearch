# Monitoring & Logging

Comprehensive monitoring and logging strategies for production FastAPI + Elasticsearch-DSL applications with observability and performance tracking.

## Table of Contents
- [Structured Logging](#structured-logging)
- [Performance Monitoring](#performance-monitoring)
- [Health Checks](#health-checks)
- [Application Performance Monitoring](#application-performance-monitoring)
- [Log Aggregation](#log-aggregation)
- [Alerting Systems](#alerting-systems)
- [Production Metrics](#production-metrics)
- [Next Steps](#next-steps)

## Structured Logging

### FastAPI Application Logging
```python
import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import structlog
from pythonjsonlogger import jsonlogger

# Configure structured logging
def configure_logging():
    """Configure structured JSON logging for production."""
    
    # Create JSON formatter
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logHandler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with performance metrics."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Generate request ID
        request_id = f"req_{int(time.time() * 1000)}"
        
        # Create logger with context
        logger = structlog.get_logger("api")
        logger = logger.bind(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host,
            user_agent=request.headers.get("user-agent", "")
        )
        
        # Log request
        logger.info("Request started")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate metrics
            process_time = time.time() - start_time
            
            # Log response
            logger.bind(
                status_code=response.status_code,
                process_time=process_time,
                response_size=response.headers.get("content-length", 0)
            ).info("Request completed")
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.bind(
                error=str(e),
                error_type=type(e).__name__,
                process_time=process_time
            ).error("Request failed")
            
            raise

# Configure app with logging
configure_logging()
app = FastAPI(title="Search API")
app.add_middleware(LoggingMiddleware)

# Elasticsearch operation logging
class ElasticsearchLogger:
    """Logger for Elasticsearch operations with performance tracking."""
    
    def __init__(self):
        self.logger = structlog.get_logger("elasticsearch")
    
    async def log_search_operation(
        self,
        index: str,
        query: Dict[str, Any],
        results_count: int,
        took_ms: int,
        user_id: Optional[str] = None
    ):
        """Log search operations with detailed metrics."""
        
        self.logger.info(
            "Search operation completed",
            operation="search",
            index=index,
            query_type=self._extract_query_type(query),
            results_count=results_count,
            took_ms=took_ms,
            user_id=user_id,
            has_filters=self._has_filters(query),
            has_aggregations=self._has_aggregations(query)
        )
    
    async def log_index_operation(
        self,
        operation: str,
        index: str,
        document_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log index operations (create, update, delete)."""
        
        log_data = {
            "operation": operation,
            "index": index,
            "success": success
        }
        
        if document_id:
            log_data["document_id"] = document_id
        
        if error:
            log_data["error"] = error
            self.logger.error("Index operation failed", **log_data)
        else:
            self.logger.info("Index operation completed", **log_data)
    
    def _extract_query_type(self, query: Dict[str, Any]) -> str:
        """Extract primary query type from Elasticsearch query."""
        if "query" in query:
            query_obj = query["query"]
            if isinstance(query_obj, dict):
                return list(query_obj.keys())[0] if query_obj else "match_all"
        return "unknown"
    
    def _has_filters(self, query: Dict[str, Any]) -> bool:
        """Check if query contains filters."""
        return "filter" in str(query) or "must" in str(query)
    
    def _has_aggregations(self, query: Dict[str, Any]) -> bool:
        """Check if query contains aggregations."""
        return "aggs" in query or "aggregations" in query

es_logger = ElasticsearchLogger()
```

### Business Logic Logging
```python
from functools import wraps
import inspect

def log_business_operation(operation_name: str):
    """Decorator for logging business operations."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = structlog.get_logger("business")
            
            # Extract function info
            func_name = func.__name__
            module_name = func.__module__
            
            # Start logging
            start_time = time.time()
            
            logger.info(
                "Business operation started",
                operation=operation_name,
                function=func_name,
                module=module_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                # Execute function
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Log success
                duration = time.time() - start_time
                logger.info(
                    "Business operation completed",
                    operation=operation_name,
                    function=func_name,
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Log error
                duration = time.time() - start_time
                logger.error(
                    "Business operation failed",
                    operation=operation_name,
                    function=func_name,
                    duration=duration,
                    error=str(e),
                    error_type=type(e).__name__,
                    success=False
                )
                raise
        
        return wrapper
    return decorator

# Usage in service classes
class SearchService:
    def __init__(self):
        self.logger = structlog.get_logger("search_service")
    
    @log_business_operation("product_search")
    async def search_products(self, query: str, filters: Dict[str, Any]):
        """Search products with comprehensive logging."""
        
        try:
            # Log search parameters
            self.logger.info(
                "Starting product search",
                query=query,
                filter_count=len(filters),
                filters=filters
            )
            
            # Perform search
            search_results = await self._execute_search(query, filters)
            
            # Log search metrics
            await es_logger.log_search_operation(
                index="products",
                query=search_results.query_dict,
                results_count=search_results.hits.total.value,
                took_ms=search_results.took
            )
            
            return search_results
            
        except Exception as e:
            self.logger.error(
                "Product search failed",
                query=query,
                filters=filters,
                error=str(e)
            )
            raise
```

## Performance Monitoring

### Metrics Collection
```python
import psutil
import asyncio
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
from typing import Dict

class MetricsCollector:
    """Collect and expose application metrics."""
    
    def __init__(self):
        # Request metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        # Elasticsearch metrics
        self.es_operations = Counter(
            'elasticsearch_operations_total',
            'Total Elasticsearch operations',
            ['operation', 'index', 'status']
        )
        
        self.es_query_duration = Histogram(
            'elasticsearch_query_duration_seconds',
            'Elasticsearch query duration',
            ['index', 'query_type']
        )
        
        # System metrics
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes'
        )
        
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )
        
        self.active_connections = Gauge(
            'active_connections',
            'Active database connections'
        )
    
    async def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        """Record HTTP request metrics."""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    async def record_elasticsearch_operation(
        self,
        operation: str,
        index: str,
        status: str,
        duration: float,
        query_type: str = "unknown"
    ):
        """Record Elasticsearch operation metrics."""
        self.es_operations.labels(
            operation=operation,
            index=index,
            status=status
        ).inc()
        
        if operation == "search":
            self.es_query_duration.labels(
                index=index,
                query_type=query_type
            ).observe(duration)
    
    async def update_system_metrics(self):
        """Update system-level metrics."""
        # Memory usage
        memory = psutil.virtual_memory()
        self.memory_usage.set(memory.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_usage.set(cpu_percent)
        
        # Connection count (mock - replace with actual connection pool)
        # self.active_connections.set(connection_pool.active_count)

# Global metrics collector
metrics = MetricsCollector()

# Metrics middleware
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        await metrics.record_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )
        
        return response

app.add_middleware(MetricsMiddleware)

@app.get("/metrics")
async def get_metrics():
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )

# Background task for system metrics
async def system_metrics_task():
    """Background task to collect system metrics."""
    while True:
        await metrics.update_system_metrics()
        await asyncio.sleep(30)  # Update every 30 seconds

@app.on_event("startup")
async def start_metrics_collection():
    asyncio.create_task(system_metrics_task())
```

## Health Checks

### Comprehensive Health Monitoring
```python
from enum import Enum
from typing import List, Optional
import aiohttp

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class ComponentHealth(BaseModel):
    name: str
    status: HealthStatus
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

class SystemHealth(BaseModel):
    status: HealthStatus
    timestamp: datetime
    version: str
    components: List[ComponentHealth]
    uptime_seconds: int

class HealthChecker:
    """Comprehensive health checking for all system components."""
    
    def __init__(self):
        self.start_time = time.time()
        self.logger = structlog.get_logger("health")
    
    async def check_elasticsearch_health(self) -> ComponentHealth:
        """Check Elasticsearch cluster health."""
        start_time = time.time()
        
        try:
            from elasticsearch_dsl.connections import connections
            client = connections.get_connection()
            
            # Check basic connectivity
            await client.ping()
            
            # Check cluster health
            cluster_health = await client.cluster.health()
            
            response_time = (time.time() - start_time) * 1000
            
            if cluster_health["status"] == "green":
                status = HealthStatus.HEALTHY
                message = "Elasticsearch cluster is healthy"
            elif cluster_health["status"] == "yellow":
                status = HealthStatus.DEGRADED
                message = "Elasticsearch cluster has some issues"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Elasticsearch cluster is unhealthy"
            
            return ComponentHealth(
                name="elasticsearch",
                status=status,
                message=message,
                response_time_ms=response_time,
                details={
                    "cluster_name": cluster_health["cluster_name"],
                    "number_of_nodes": cluster_health["number_of_nodes"],
                    "active_primary_shards": cluster_health["active_primary_shards"],
                    "active_shards": cluster_health["active_shards"]
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return ComponentHealth(
                name="elasticsearch",
                status=HealthStatus.UNHEALTHY,
                message=f"Elasticsearch connection failed: {str(e)}",
                response_time_ms=response_time
            )
    
    async def check_memory_health(self) -> ComponentHealth:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent < 80:
                status = HealthStatus.HEALTHY
                message = "Memory usage is normal"
            elif usage_percent < 90:
                status = HealthStatus.DEGRADED
                message = "Memory usage is high"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Memory usage is critical"
            
            return ComponentHealth(
                name="memory",
                status=status,
                message=message,
                details={
                    "usage_percent": usage_percent,
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}"
            )
    
    async def check_disk_health(self) -> ComponentHealth:
        """Check disk usage."""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent < 80:
                status = HealthStatus.HEALTHY
                message = "Disk usage is normal"
            elif usage_percent < 90:
                status = HealthStatus.DEGRADED
                message = "Disk usage is high"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Disk usage is critical"
            
            return ComponentHealth(
                name="disk",
                status=status,
                message=message,
                details={
                    "usage_percent": round(usage_percent, 2),
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {str(e)}"
            )
    
    async def get_system_health(self) -> SystemHealth:
        """Get comprehensive system health status."""
        
        # Check all components
        checks = await asyncio.gather(
            self.check_elasticsearch_health(),
            self.check_memory_health(),
            self.check_disk_health(),
            return_exceptions=True
        )
        
        components = []
        for check in checks:
            if isinstance(check, ComponentHealth):
                components.append(check)
            else:
                # Handle exceptions
                components.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(check)}"
                ))
        
        # Determine overall status
        if all(c.status == HealthStatus.HEALTHY for c in components):
            overall_status = HealthStatus.HEALTHY
        elif any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        return SystemHealth(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",  # Replace with actual version
            components=components,
            uptime_seconds=int(time.time() - self.start_time)
        )

health_checker = HealthChecker()

@app.get("/health", response_model=SystemHealth)
async def health_endpoint():
    """Health check endpoint for load balancers and monitoring."""
    return await health_checker.get_system_health()

@app.get("/health/live")
async def liveness_probe():
    """Simple liveness probe for Kubernetes."""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_probe():
    """Readiness probe - check if app can serve traffic."""
    health = await health_checker.get_system_health()
    
    if health.status == HealthStatus.UNHEALTHY:
        return Response(
            content=json.dumps({"status": "not ready"}),
            status_code=503
        )
    
    return {"status": "ready"}
```

## Application Performance Monitoring

### Custom APM Integration
```python
class APMTracer:
    """Custom APM tracing for performance monitoring."""
    
    def __init__(self):
        self.traces = {}
        self.logger = structlog.get_logger("apm")
    
    def start_trace(self, trace_id: str, operation: str) -> Dict[str, Any]:
        """Start a new trace."""
        trace = {
            "trace_id": trace_id,
            "operation": operation,
            "start_time": time.time(),
            "spans": [],
            "metadata": {}
        }
        
        self.traces[trace_id] = trace
        return trace
    
    def add_span(self, trace_id: str, span_name: str, metadata: Dict[str, Any] = None):
        """Add a span to an existing trace."""
        if trace_id not in self.traces:
            return
        
        span = {
            "name": span_name,
            "start_time": time.time(),
            "metadata": metadata or {}
        }
        
        self.traces[trace_id]["spans"].append(span)
        return span
    
    def end_span(self, trace_id: str, span_name: str):
        """End a span and calculate duration."""
        if trace_id not in self.traces:
            return
        
        trace = self.traces[trace_id]
        for span in trace["spans"]:
            if span["name"] == span_name and "end_time" not in span:
                span["end_time"] = time.time()
                span["duration"] = span["end_time"] - span["start_time"]
                break
    
    def end_trace(self, trace_id: str, success: bool = True):
        """End a trace and log performance data."""
        if trace_id not in self.traces:
            return
        
        trace = self.traces[trace_id]
        trace["end_time"] = time.time()
        trace["duration"] = trace["end_time"] - trace["start_time"]
        trace["success"] = success
        
        # Log trace data
        self.logger.info(
            "Trace completed",
            trace_id=trace_id,
            operation=trace["operation"],
            duration=trace["duration"],
            success=success,
            span_count=len(trace["spans"])
        )
        
        # Clean up
        del self.traces[trace_id]

apm_tracer = APMTracer()

# APM middleware
class APMMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = f"trace_{int(time.time() * 1000)}"
        
        # Start trace
        apm_tracer.start_trace(trace_id, f"{request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            apm_tracer.end_trace(trace_id, success=True)
            response.headers["X-Trace-ID"] = trace_id
            return response
        except Exception as e:
            apm_tracer.end_trace(trace_id, success=False)
            raise

app.add_middleware(APMMiddleware)
```

## Log Aggregation

### Centralized Logging Setup
```python
import logging.handlers
from pythonjsonlogger import jsonlogger

class LogAggregationSetup:
    """Setup for centralized log aggregation."""
    
    @staticmethod
    def configure_elk_logging(
        elasticsearch_host: str = "localhost:9200",
        log_index_prefix: str = "app-logs"
    ):
        """Configure logging to send to ELK stack."""
        
        # Create Elasticsearch handler
        from elasticsearch import Elasticsearch
        
        class ElasticsearchHandler(logging.Handler):
            def __init__(self, es_host, index_prefix):
                super().__init__()
                self.es = Elasticsearch([es_host])
                self.index_prefix = index_prefix
            
            def emit(self, record):
                try:
                    log_entry = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'level': record.levelname,
                        'logger': record.name,
                        'message': record.getMessage(),
                        'module': record.module,
                        'function': record.funcName,
                        'line': record.lineno,
                        'process': record.process,
                        'thread': record.thread
                    }
                    
                    # Add exception info if present
                    if record.exc_info:
                        log_entry['exception'] = self.format(record)
                    
                    # Send to Elasticsearch
                    index_name = f"{self.index_prefix}-{datetime.utcnow().strftime('%Y.%m.%d')}"
                    self.es.index(index=index_name, body=log_entry)
                    
                except Exception:
                    self.handleError(record)
        
        # Add Elasticsearch handler
        es_handler = ElasticsearchHandler(elasticsearch_host, log_index_prefix)
        es_handler.setLevel(logging.INFO)
        
        logger = logging.getLogger()
        logger.addHandler(es_handler)
    
    @staticmethod
    def configure_file_rotation():
        """Configure rotating file logs."""
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename='app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger = logging.getLogger()
        logger.addHandler(file_handler)
```

## Alerting Systems

### Alert Configuration
```python
from typing import Callable, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertManager:
    """Manage alerts for various system conditions."""
    
    def __init__(self, smtp_config: Dict[str, str]):
        self.smtp_config = smtp_config
        self.alert_rules = []
        self.logger = structlog.get_logger("alerts")
    
    def add_alert_rule(
        self,
        name: str,
        condition: Callable,
        message_template: str,
        severity: str = "warning",
        recipients: List[str] = None
    ):
        """Add an alert rule."""
        rule = {
            "name": name,
            "condition": condition,
            "message_template": message_template,
            "severity": severity,
            "recipients": recipients or [],
            "last_triggered": None
        }
        self.alert_rules.append(rule)
    
    async def check_alerts(self, metrics: Dict[str, Any]):
        """Check all alert rules against current metrics."""
        for rule in self.alert_rules:
            try:
                if rule["condition"](metrics):
                    await self._trigger_alert(rule, metrics)
            except Exception as e:
                self.logger.error(
                    "Alert rule check failed",
                    rule_name=rule["name"],
                    error=str(e)
                )
    
    async def _trigger_alert(self, rule: Dict[str, Any], metrics: Dict[str, Any]):
        """Trigger an alert."""
        
        # Check if recently triggered (avoid spam)
        if rule["last_triggered"]:
            time_since_last = time.time() - rule["last_triggered"]
            if time_since_last < 300:  # 5 minutes
                return
        
        rule["last_triggered"] = time.time()
        
        # Format message
        message = rule["message_template"].format(**metrics)
        
        # Log alert
        self.logger.warning(
            "Alert triggered",
            rule_name=rule["name"],
            severity=rule["severity"],
            message=message
        )
        
        # Send notifications
        await self._send_email_alert(rule, message)
    
    async def _send_email_alert(self, rule: Dict[str, Any], message: str):
        """Send email alert."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from']
            msg['To'] = ", ".join(rule["recipients"])
            msg['Subject'] = f"[{rule['severity'].upper()}] {rule['name']}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
            if self.smtp_config.get('use_tls'):
                server.starttls()
            
            if self.smtp_config.get('username'):
                server.login(
                    self.smtp_config['username'],
                    self.smtp_config['password']
                )
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(
                "Failed to send email alert",
                error=str(e),
                rule_name=rule["name"]
            )

# Configure alerts
alert_manager = AlertManager({
    'host': 'smtp.gmail.com',
    'port': 587,
    'use_tls': True,
    'username': 'alerts@company.com',
    'password': 'app_password',
    'from': 'alerts@company.com'
})

# Add alert rules
alert_manager.add_alert_rule(
    name="High Error Rate",
    condition=lambda m: m.get('error_rate', 0) > 0.05,  # 5% error rate
    message_template="Error rate is {error_rate:.2%}",
    severity="critical",
    recipients=["oncall@company.com"]
)

alert_manager.add_alert_rule(
    name="Slow Response Time",
    condition=lambda m: m.get('avg_response_time', 0) > 2.0,  # 2 seconds
    message_template="Average response time is {avg_response_time:.2f} seconds",
    severity="warning",
    recipients=["team@company.com"]
)

# Background task to check alerts
async def alert_monitoring_task():
    """Background task to monitor and trigger alerts."""
    while True:
        try:
            # Collect current metrics
            current_metrics = {
                'error_rate': 0.02,  # Replace with actual metric calculation
                'avg_response_time': 1.5,  # Replace with actual metric
                'memory_usage': psutil.virtual_memory().percent / 100
            }
            
            await alert_manager.check_alerts(current_metrics)
            
        except Exception as e:
            logging.error(f"Alert monitoring failed: {e}")
        
        await asyncio.sleep(60)  # Check every minute

@app.on_event("startup")
async def start_alert_monitoring():
    asyncio.create_task(alert_monitoring_task())
```

## Production Metrics

### Key Performance Indicators
```python
class ProductionMetrics:
    """Track key production metrics."""
    
    def __init__(self):
        self.metrics_history = []
        self.logger = structlog.get_logger("production_metrics")
    
    async def collect_business_metrics(self) -> Dict[str, Any]:
        """Collect business-relevant metrics."""
        
        # Search metrics
        search_volume = await self._get_search_volume()
        user_engagement = await self._get_user_engagement()
        
        # System metrics
        system_performance = await self._get_system_performance()
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'search_volume_per_hour': search_volume,
            'average_session_duration': user_engagement['avg_session'],
            'unique_users_per_hour': user_engagement['unique_users'],
            'system_cpu_percent': system_performance['cpu'],
            'system_memory_percent': system_performance['memory'],
            'elasticsearch_health': system_performance['es_health']
        }
        
        self.metrics_history.append(metrics)
        
        # Keep only last 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        return metrics
    
    async def _get_search_volume(self) -> int:
        """Get search volume for the last hour."""
        # Implementation would query actual metrics
        return 1500  # Mock value
    
    async def _get_user_engagement(self) -> Dict[str, Any]:
        """Get user engagement metrics."""
        return {
            'avg_session': 15.5,  # minutes
            'unique_users': 450
        }
    
    async def _get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        return {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'es_health': 'green'  # From actual Elasticsearch health check
        }

production_metrics = ProductionMetrics()

@app.get("/admin/metrics")
async def get_production_metrics():
    """Get current production metrics."""
    return await production_metrics.collect_business_metrics()
```

## Next Steps

1. **[Security & Authentication](02_security-authentication.md)** - API security patterns
2. **[Performance Optimization](03_performance-optimization.md)** - Scaling and efficiency
3. **[Testing Strategies](../07-testing-deployment/01_testing-strategies.md)** - Comprehensive testing

## Additional Resources

- **Structlog Documentation**: [structlog.org](https://structlog.org)
- **Prometheus Monitoring**: [prometheus.io](https://prometheus.io)
- **ELK Stack**: [elastic.co/what-is/elk-stack](https://www.elastic.co/what-is/elk-stack)
- **FastAPI Monitoring**: [fastapi.tiangolo.com/advanced/middleware](https://fastapi.tiangolo.com/advanced/middleware/)