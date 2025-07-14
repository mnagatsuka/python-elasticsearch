# Error Handling

Advanced error handling and resilience patterns for production FastAPI + Elasticsearch-DSL applications with enterprise-grade reliability.

## Table of Contents
- [Circuit Breaker Patterns](#circuit-breaker-patterns)
- [Retry Logic](#retry-logic)
- [Graceful Degradation](#graceful-degradation)
- [Error Monitoring](#error-monitoring)
- [Recovery Procedures](#recovery-procedures)
- [Resilience Patterns](#resilience-patterns)
- [Fault Tolerance](#fault-tolerance)
- [Next Steps](#next-steps)

## Circuit Breaker Patterns

### Advanced Circuit Breaker Implementation
```python
import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
import random
from functools import wraps

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: int = 60          # Seconds before trying half-open
    success_threshold: int = 3          # Successes needed to close
    timeout_seconds: float = 30.0       # Request timeout
    expected_exception: type = Exception # Exception type to track

class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass

class CircuitBreaker:
    """Advanced circuit breaker with multiple failure modes."""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_success_time = 0
        self.total_requests = 0
        self.total_failures = 0
        
        # Statistics
        self.stats = {
            "state_changes": [],
            "recent_failures": [],
            "recent_successes": []
        }
    
    async def call(self, func: Callable[..., Awaitable], *args, **kwargs):
        """Execute function with circuit breaker protection."""
        
        self.total_requests += 1
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is open"
                )
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout_seconds
            )
            
            await self._on_success()
            return result
            
        except self.config.expected_exception as e:
            await self._on_failure(e)
            raise
        except asyncio.TimeoutError as e:
            await self._on_failure(e)
            raise CircuitBreakerError(f"Request timeout in circuit '{self.name}'")
    
    async def _on_success(self):
        """Handle successful request."""
        
        self.success_count += 1
        self.last_success_time = time.time()
        
        # Track recent successes
        self.stats["recent_successes"].append(time.time())
        self._cleanup_old_stats()
        
        # Transition logic based on state
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.OPEN:
            # Should not happen, but reset if it does
            self._transition_to_closed()
    
    async def _on_failure(self, exception: Exception):
        """Handle failed request."""
        
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = time.time()
        
        # Track recent failures
        self.stats["recent_failures"].append({
            "time": time.time(),
            "exception": str(exception),
            "type": type(exception).__name__
        })
        self._cleanup_old_stats()
        
        # Transition logic based on state
        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from open to half-open."""
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _transition_to_closed(self):
        """Transition to closed state."""
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self._record_state_change("closed")
    
    def _transition_to_open(self):
        """Transition to open state."""
        
        self.state = CircuitState.OPEN
        self.success_count = 0
        self._record_state_change("open")
    
    def _transition_to_half_open(self):
        """Transition to half-open state."""
        
        self.state = CircuitState.HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        self._record_state_change("half_open")
    
    def _record_state_change(self, new_state: str):
        """Record state change for monitoring."""
        
        self.stats["state_changes"].append({
            "time": time.time(),
            "from_state": self.state.value if hasattr(self, 'state') else 'unknown',
            "to_state": new_state
        })
        
        logger.info(
            f"Circuit breaker '{self.name}' changed state",
            from_state=self.state.value if hasattr(self, 'state') else 'unknown',
            to_state=new_state,
            failure_count=self.failure_count
        )
    
    def _cleanup_old_stats(self):
        """Clean up old statistics to prevent memory bloat."""
        
        cutoff_time = time.time() - 3600  # Keep last hour
        
        self.stats["recent_failures"] = [
            f for f in self.stats["recent_failures"]
            if f["time"] > cutoff_time
        ]
        
        self.stats["recent_successes"] = [
            s for s in self.stats["recent_successes"]
            if s > cutoff_time
        ]
        
        self.stats["state_changes"] = [
            sc for sc in self.stats["state_changes"]
            if sc["time"] > cutoff_time
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        
        recent_failure_rate = 0
        if self.total_requests > 0:
            recent_failures = len([
                f for f in self.stats["recent_failures"]
                if f["time"] > time.time() - 300  # Last 5 minutes
            ])
            recent_requests = len([
                s for s in self.stats["recent_successes"]
                if s > time.time() - 300
            ]) + recent_failures
            
            if recent_requests > 0:
                recent_failure_rate = recent_failures / recent_requests
        
        return {
            "name": self.name,
            "state": self.state.value,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "current_failure_count": self.failure_count,
            "current_success_count": self.success_count,
            "failure_rate": self.total_failures / max(self.total_requests, 1),
            "recent_failure_rate": recent_failure_rate,
            "last_failure_time": self.last_failure_time,
            "time_since_last_failure": time.time() - self.last_failure_time,
            "state_changes_count": len(self.stats["state_changes"])
        }

class CircuitBreakerManager:
    """Manage multiple circuit breakers."""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        
    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker."""
        
        if name not in self.breakers:
            config = config or CircuitBreakerConfig()
            self.breakers[name] = CircuitBreaker(name, config)
        
        return self.breakers[name]
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        
        return {
            name: breaker.get_metrics()
            for name, breaker in self.breakers.items()
        }

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

def circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """Decorator to add circuit breaker protection."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = circuit_breaker_manager.get_or_create(name, config)
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

# Elasticsearch-specific circuit breaker
@circuit_breaker(
    "elasticsearch",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        timeout_seconds=10.0
    )
)
async def safe_elasticsearch_search(es_client, **kwargs):
    """Elasticsearch search with circuit breaker protection."""
    return await es_client.search(**kwargs)
```

## Retry Logic

### Sophisticated Retry Mechanisms
```python
import asyncio
import random
from typing import Union, List, Type, Callable, Any
from dataclasses import dataclass
import math

@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[Type[Exception]] = None

class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, message: str, attempts: int, last_exception: Exception):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception

class RetryStrategy:
    """Base class for retry strategies."""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        raise NotImplementedError

class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff with optional jitter."""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            # Add random jitter (±20%)
            jitter_range = delay * 0.2
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay)
        
        return delay

class LinearBackoffStrategy(RetryStrategy):
    """Linear backoff strategy."""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        delay = config.base_delay * attempt
        return min(delay, config.max_delay)

class FixedDelayStrategy(RetryStrategy):
    """Fixed delay between attempts."""
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        return config.base_delay

class AdaptiveRetryStrategy(RetryStrategy):
    """Adaptive retry based on error type and system load."""
    
    def __init__(self):
        self.error_history = {}
        self.system_load_factor = 1.0
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        base_delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        
        # Adjust based on system load
        adjusted_delay = base_delay * self.system_load_factor
        
        # Cap at max delay
        delay = min(adjusted_delay, config.max_delay)
        
        if config.jitter:
            jitter_range = delay * 0.3
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay)
        
        return delay
    
    def update_system_load(self, load_factor: float):
        """Update system load factor (1.0 = normal, >1.0 = high load)."""
        self.system_load_factor = max(0.1, min(5.0, load_factor))

class RetryManager:
    """Advanced retry manager with multiple strategies."""
    
    def __init__(self, strategy: RetryStrategy = None):
        self.strategy = strategy or ExponentialBackoffStrategy()
        self.attempt_history = []
        
    async def execute_with_retry(
        self,
        func: Callable,
        config: RetryConfig,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        
        # Set default retryable exceptions
        if config.retryable_exceptions is None:
            config.retryable_exceptions = [
                ConnectionError,
                TimeoutError,
                asyncio.TimeoutError
            ]
        
        last_exception = None
        attempt_details = []
        
        for attempt in range(1, config.max_attempts + 1):
            attempt_start = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Record successful attempt
                attempt_details.append({
                    "attempt": attempt,
                    "success": True,
                    "duration": time.time() - attempt_start
                })
                
                self.attempt_history.append({
                    "function": func.__name__,
                    "attempts": attempt_details,
                    "total_attempts": attempt,
                    "success": True,
                    "timestamp": time.time()
                })
                
                return result
                
            except Exception as e:
                last_exception = e
                duration = time.time() - attempt_start
                
                attempt_details.append({
                    "attempt": attempt,
                    "success": False,
                    "exception": str(e),
                    "exception_type": type(e).__name__,
                    "duration": duration
                })
                
                # Check if exception is retryable
                if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                    logger.error(
                        f"Non-retryable exception in {func.__name__}",
                        exception=str(e),
                        attempt=attempt
                    )
                    break
                
                # Don't delay after the last attempt
                if attempt < config.max_attempts:
                    delay = self.strategy.calculate_delay(attempt, config)
                    
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, retrying in {delay:.2f}s",
                        exception=str(e),
                        delay=delay
                    )
                    
                    await asyncio.sleep(delay)
        
        # Record failed execution
        self.attempt_history.append({
            "function": func.__name__,
            "attempts": attempt_details,
            "total_attempts": config.max_attempts,
            "success": False,
            "timestamp": time.time()
        })
        
        # Raise retry error with details
        raise RetryError(
            f"All {config.max_attempts} attempts failed for {func.__name__}",
            config.max_attempts,
            last_exception
        )
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get retry statistics."""
        
        if not self.attempt_history:
            return {"message": "No retry history available"}
        
        successful_executions = [h for h in self.attempt_history if h["success"]]
        failed_executions = [h for h in self.attempt_history if not h["success"]]
        
        avg_attempts_success = 0
        if successful_executions:
            avg_attempts_success = sum(h["total_attempts"] for h in successful_executions) / len(successful_executions)
        
        return {
            "total_executions": len(self.attempt_history),
            "successful_executions": len(successful_executions),
            "failed_executions": len(failed_executions),
            "success_rate": len(successful_executions) / len(self.attempt_history),
            "average_attempts_on_success": avg_attempts_success,
            "most_common_failures": self._get_common_failures()
        }
    
    def _get_common_failures(self) -> Dict[str, int]:
        """Get most common failure types."""
        
        failure_counts = {}
        
        for execution in self.attempt_history:
            if not execution["success"]:
                for attempt in execution["attempts"]:
                    if not attempt["success"]:
                        exc_type = attempt["exception_type"]
                        failure_counts[exc_type] = failure_counts.get(exc_type, 0) + 1
        
        return dict(sorted(failure_counts.items(), key=lambda x: x[1], reverse=True))

# Global retry manager
retry_manager = RetryManager(AdaptiveRetryStrategy())

def retry_with_backoff(config: RetryConfig = None):
    """Decorator for automatic retry with backoff."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_config = config or RetryConfig()
            return await retry_manager.execute_with_retry(
                func, retry_config, *args, **kwargs
            )
        return wrapper
    return decorator

# Elasticsearch-specific retry configurations
ELASTICSEARCH_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True,
    retryable_exceptions=[
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
        # Add Elasticsearch-specific exceptions
    ]
)

@retry_with_backoff(ELASTICSEARCH_RETRY_CONFIG)
async def resilient_elasticsearch_search(es_client, **kwargs):
    """Elasticsearch search with retry logic."""
    return await es_client.search(**kwargs)

@retry_with_backoff(ELASTICSEARCH_RETRY_CONFIG)
async def resilient_elasticsearch_index(es_client, **kwargs):
    """Elasticsearch index operation with retry logic."""
    return await es_client.index(**kwargs)
```

## Graceful Degradation

### Service Degradation Strategies
```python
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
import asyncio

class ServiceLevel(Enum):
    FULL = "full"           # All features available
    DEGRADED = "degraded"   # Limited features
    MINIMAL = "minimal"     # Basic features only
    OFFLINE = "offline"     # Service unavailable

class DegradationStrategy:
    """Base class for degradation strategies."""
    
    async def should_degrade(self, metrics: Dict[str, Any]) -> ServiceLevel:
        raise NotImplementedError
    
    async def get_fallback_response(self, context: Dict[str, Any]) -> Any:
        raise NotImplementedError

class PerformanceDegradationStrategy(DegradationStrategy):
    """Degrade based on performance metrics."""
    
    def __init__(self):
        self.thresholds = {
            ServiceLevel.FULL: {
                "response_time_ms": 500,
                "error_rate": 0.01,
                "cpu_percent": 70
            },
            ServiceLevel.DEGRADED: {
                "response_time_ms": 2000,
                "error_rate": 0.05,
                "cpu_percent": 85
            },
            ServiceLevel.MINIMAL: {
                "response_time_ms": 5000,
                "error_rate": 0.15,
                "cpu_percent": 95
            }
        }
    
    async def should_degrade(self, metrics: Dict[str, Any]) -> ServiceLevel:
        """Determine service level based on metrics."""
        
        response_time = metrics.get("avg_response_time_ms", 0)
        error_rate = metrics.get("error_rate", 0)
        cpu_percent = metrics.get("cpu_percent", 0)
        
        # Check from most restrictive to least restrictive
        for level in [ServiceLevel.MINIMAL, ServiceLevel.DEGRADED, ServiceLevel.FULL]:
            thresholds = self.thresholds[level]
            
            if (response_time <= thresholds["response_time_ms"] and
                error_rate <= thresholds["error_rate"] and
                cpu_percent <= thresholds["cpu_percent"]):
                return level
        
        return ServiceLevel.OFFLINE
    
    async def get_fallback_response(self, context: Dict[str, Any]) -> Any:
        """Get fallback response based on service level."""
        
        service_level = context.get("service_level", ServiceLevel.OFFLINE)
        
        if service_level == ServiceLevel.DEGRADED:
            return self._get_degraded_response(context)
        elif service_level == ServiceLevel.MINIMAL:
            return self._get_minimal_response(context)
        else:
            return self._get_offline_response(context)
    
    def _get_degraded_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate degraded service response."""
        return {
            "status": "degraded",
            "message": "Service is operating with limited functionality",
            "data": context.get("cached_data", {}),
            "features_disabled": ["advanced_search", "aggregations", "sorting"]
        }
    
    def _get_minimal_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate minimal service response."""
        return {
            "status": "minimal",
            "message": "Service is operating with basic functionality only",
            "data": context.get("basic_data", {}),
            "features_disabled": ["search", "advanced_search", "aggregations", "sorting", "filtering"]
        }
    
    def _get_offline_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate offline service response."""
        return {
            "status": "offline",
            "message": "Service is temporarily unavailable",
            "retry_after": 60
        }

class GracefulDegradationManager:
    """Manage graceful degradation across services."""
    
    def __init__(self):
        self.current_level = ServiceLevel.FULL
        self.strategies: Dict[str, DegradationStrategy] = {}
        self.fallback_cache = {}
        self.degradation_history = []
        
    def register_strategy(self, name: str, strategy: DegradationStrategy):
        """Register a degradation strategy."""
        self.strategies[name] = strategy
    
    async def evaluate_service_level(self, metrics: Dict[str, Any]) -> ServiceLevel:
        """Evaluate current service level based on all strategies."""
        
        levels = []
        
        for name, strategy in self.strategies.items():
            try:
                level = await strategy.should_degrade(metrics)
                levels.append(level)
            except Exception as e:
                logger.error(f"Degradation strategy {name} failed: {e}")
                levels.append(ServiceLevel.MINIMAL)
        
        # Use the most restrictive level
        if not levels:
            return ServiceLevel.FULL
        
        level_priority = {
            ServiceLevel.OFFLINE: 0,
            ServiceLevel.MINIMAL: 1,
            ServiceLevel.DEGRADED: 2,
            ServiceLevel.FULL: 3
        }
        
        chosen_level = min(levels, key=lambda l: level_priority[l])
        
        # Update current level and record change
        if chosen_level != self.current_level:
            self._record_level_change(self.current_level, chosen_level)
            self.current_level = chosen_level
        
        return chosen_level
    
    def _record_level_change(self, old_level: ServiceLevel, new_level: ServiceLevel):
        """Record service level change."""
        
        change_record = {
            "timestamp": time.time(),
            "from_level": old_level.value,
            "to_level": new_level.value
        }
        
        self.degradation_history.append(change_record)
        
        # Keep only last 24 hours
        cutoff_time = time.time() - 86400
        self.degradation_history = [
            record for record in self.degradation_history
            if record["timestamp"] > cutoff_time
        ]
        
        logger.warning(
            "Service level changed",
            from_level=old_level.value,
            to_level=new_level.value
        )
    
    async def get_fallback_response(
        self,
        strategy_name: str,
        context: Dict[str, Any]
    ) -> Any:
        """Get fallback response from specific strategy."""
        
        if strategy_name not in self.strategies:
            return {"error": "Strategy not found"}
        
        context["service_level"] = self.current_level
        strategy = self.strategies[strategy_name]
        
        return await strategy.get_fallback_response(context)
    
    def cache_fallback_data(self, key: str, data: Any, ttl: int = 3600):
        """Cache data for fallback use."""
        
        self.fallback_cache[key] = {
            "data": data,
            "cached_at": time.time(),
            "ttl": ttl
        }
    
    def get_cached_fallback_data(self, key: str) -> Optional[Any]:
        """Get cached fallback data."""
        
        if key not in self.fallback_cache:
            return None
        
        cached_item = self.fallback_cache[key]
        
        # Check if expired
        if time.time() - cached_item["cached_at"] > cached_item["ttl"]:
            del self.fallback_cache[key]
            return None
        
        return cached_item["data"]

# Global degradation manager
degradation_manager = GracefulDegradationManager()

# Register strategies
degradation_manager.register_strategy(
    "performance",
    PerformanceDegradationStrategy()
)

def graceful_degradation(
    strategy_name: str = "performance",
    cache_key: Optional[str] = None
):
    """Decorator for graceful degradation."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Try normal execution
                result = await func(*args, **kwargs)
                
                # Cache successful result for fallback
                if cache_key:
                    degradation_manager.cache_fallback_data(cache_key, result)
                
                return result
                
            except Exception as e:
                logger.warning(f"Function {func.__name__} failed, checking degradation", error=str(e))
                
                # Get current service level
                current_level = degradation_manager.current_level
                
                if current_level == ServiceLevel.FULL:
                    # Re-raise exception if we're supposed to be at full service
                    raise
                
                # Get fallback response
                context = {
                    "function_name": func.__name__,
                    "exception": str(e),
                    "args": args,
                    "kwargs": kwargs
                }
                
                # Add cached data if available
                if cache_key:
                    cached_data = degradation_manager.get_cached_fallback_data(cache_key)
                    if cached_data:
                        context["cached_data"] = cached_data
                
                return await degradation_manager.get_fallback_response(
                    strategy_name, context
                )
        
        return wrapper
    return decorator

# Example usage with search
@graceful_degradation(strategy_name="performance", cache_key="search_results")
async def search_with_degradation(es_client, query: str, filters: Dict[str, Any]):
    """Search with graceful degradation."""
    
    service_level = degradation_manager.current_level
    
    if service_level == ServiceLevel.FULL:
        # Full search with all features
        search_body = {
            "query": {
                "bool": {
                    "must": [{"match": {"content": query}}],
                    "filter": [{"term": {k: v}} for k, v in filters.items()]
                }
            },
            "aggs": {
                "categories": {"terms": {"field": "category.keyword"}},
                "date_range": {"date_histogram": {"field": "created_date", "interval": "day"}}
            },
            "sort": [{"_score": {"order": "desc"}}, {"created_date": {"order": "desc"}}],
            "size": 50
        }
    elif service_level == ServiceLevel.DEGRADED:
        # Limited search without aggregations and sorting
        search_body = {
            "query": {"match": {"content": query}},
            "size": 20
        }
    elif service_level == ServiceLevel.MINIMAL:
        # Basic search only
        search_body = {
            "query": {"match_all": {}},
            "size": 10
        }
    else:
        # Offline - will trigger fallback
        raise ConnectionError("Elasticsearch unavailable")
    
    return await es_client.search(body=search_body)
```

## Error Monitoring

### Comprehensive Error Tracking
```python
import traceback
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
import json

@dataclass
class ErrorDetails:
    error_id: str
    timestamp: datetime
    exception_type: str
    exception_message: str
    function_name: str
    module_name: str
    file_name: str
    line_number: int
    stack_trace: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    system_context: Optional[Dict[str, Any]] = None

class ErrorAggregator:
    """Aggregate and analyze errors for patterns."""
    
    def __init__(self):
        self.error_patterns = {}
        self.error_history = []
        self.alert_thresholds = {
            "error_rate_per_minute": 10,
            "unique_errors_per_hour": 5,
            "critical_error_rate": 0.1
        }
    
    def add_error(self, error: ErrorDetails):
        """Add error to aggregation."""
        
        self.error_history.append(error)
        
        # Create pattern key for grouping similar errors
        pattern_key = self._create_pattern_key(error)
        
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = {
                "first_seen": error.timestamp,
                "last_seen": error.timestamp,
                "count": 0,
                "recent_occurrences": [],
                "sample_error": error
            }
        
        pattern = self.error_patterns[pattern_key]
        pattern["count"] += 1
        pattern["last_seen"] = error.timestamp
        pattern["recent_occurrences"].append(error.timestamp)
        
        # Keep only recent occurrences (last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        pattern["recent_occurrences"] = [
            ts for ts in pattern["recent_occurrences"]
            if ts > cutoff_time
        ]
        
        # Clean old errors from history
        self._cleanup_old_errors()
        
        # Check for alert conditions
        self._check_alert_conditions()
    
    def _create_pattern_key(self, error: ErrorDetails) -> str:
        """Create a key for grouping similar errors."""
        
        # Group by exception type, function, and line number
        pattern_data = f"{error.exception_type}:{error.function_name}:{error.line_number}"
        return hashlib.md5(pattern_data.encode()).hexdigest()[:16]
    
    def _cleanup_old_errors(self):
        """Remove old errors to prevent memory bloat."""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.error_history = [
            error for error in self.error_history
            if error.timestamp > cutoff_time
        ]
    
    def _check_alert_conditions(self):
        """Check if any alert conditions are met."""
        
        current_time = datetime.utcnow()
        
        # Check error rate per minute
        minute_ago = current_time - timedelta(minutes=1)
        recent_errors = [
            error for error in self.error_history
            if error.timestamp > minute_ago
        ]
        
        if len(recent_errors) > self.alert_thresholds["error_rate_per_minute"]:
            self._trigger_alert("high_error_rate", {
                "error_count": len(recent_errors),
                "threshold": self.alert_thresholds["error_rate_per_minute"],
                "timeframe": "1 minute"
            })
        
        # Check unique errors per hour
        hour_ago = current_time - timedelta(hours=1)
        recent_patterns = set()
        
        for error in self.error_history:
            if error.timestamp > hour_ago:
                pattern_key = self._create_pattern_key(error)
                recent_patterns.add(pattern_key)
        
        if len(recent_patterns) > self.alert_thresholds["unique_errors_per_hour"]:
            self._trigger_alert("many_unique_errors", {
                "unique_error_count": len(recent_patterns),
                "threshold": self.alert_thresholds["unique_errors_per_hour"],
                "timeframe": "1 hour"
            })
    
    def _trigger_alert(self, alert_type: str, context: Dict[str, Any]):
        """Trigger error monitoring alert."""
        
        logger.critical(
            f"Error monitoring alert: {alert_type}",
            **context
        )
        
        # Here you could integrate with external alerting systems
        # like PagerDuty, Slack, email, etc.
    
    def get_error_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get error summary for specified time period."""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            error for error in self.error_history
            if error.timestamp > cutoff_time
        ]
        
        if not recent_errors:
            return {"message": "No errors in specified time period"}
        
        # Group by exception type
        by_type = {}
        by_function = {}
        by_endpoint = {}
        
        for error in recent_errors:
            # By exception type
            exc_type = error.exception_type
            by_type[exc_type] = by_type.get(exc_type, 0) + 1
            
            # By function
            func_name = error.function_name
            by_function[func_name] = by_function.get(func_name, 0) + 1
            
            # By endpoint
            if error.endpoint:
                by_endpoint[error.endpoint] = by_endpoint.get(error.endpoint, 0) + 1
        
        return {
            "time_period_hours": hours,
            "total_errors": len(recent_errors),
            "unique_patterns": len(set(self._create_pattern_key(e) for e in recent_errors)),
            "by_exception_type": dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
            "by_function": dict(sorted(by_function.items(), key=lambda x: x[1], reverse=True)),
            "by_endpoint": dict(sorted(by_endpoint.items(), key=lambda x: x[1], reverse=True)),
            "most_recent_error": asdict(recent_errors[-1]) if recent_errors else None
        }

class ErrorTracker:
    """Advanced error tracking and reporting."""
    
    def __init__(self):
        self.aggregator = ErrorAggregator()
        self.error_handlers = {}
        self.error_processors = []
    
    def register_error_handler(self, exception_type: type, handler: Callable):
        """Register custom error handler for specific exception type."""
        self.error_handlers[exception_type] = handler
    
    def add_error_processor(self, processor: Callable):
        """Add error processor for custom processing."""
        self.error_processors.append(processor)
    
    async def track_error(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track an error with full context."""
        
        # Extract error details
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_traceback is None:
            # Create traceback from current stack
            exc_traceback = exception.__traceback__
        
        # Get traceback details
        tb_list = traceback.extract_tb(exc_traceback)
        last_frame = tb_list[-1] if tb_list else None
        
        # Generate unique error ID
        error_id = self._generate_error_id(exception, last_frame)
        
        # Create error details
        error_details = ErrorDetails(
            error_id=error_id,
            timestamp=datetime.utcnow(),
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            function_name=last_frame.name if last_frame else "unknown",
            module_name=getattr(exception, '__module__', 'unknown'),
            file_name=last_frame.filename if last_frame else "unknown",
            line_number=last_frame.lineno if last_frame else 0,
            stack_trace=traceback.format_exc(),
            request_id=context.get("request_id") if context else None,
            user_id=context.get("user_id") if context else None,
            endpoint=context.get("endpoint") if context else None,
            request_data=context.get("request_data") if context else None,
            system_context=self._get_system_context()
        )
        
        # Process with custom processors
        for processor in self.error_processors:
            try:
                await processor(error_details, context)
            except Exception as e:
                logger.error(f"Error processor failed: {e}")
        
        # Add to aggregator
        self.aggregator.add_error(error_details)
        
        # Handle with custom handler if available
        if type(exception) in self.error_handlers:
            try:
                await self.error_handlers[type(exception)](error_details, context)
            except Exception as e:
                logger.error(f"Custom error handler failed: {e}")
        
        return error_id
    
    def _generate_error_id(self, exception: Exception, frame) -> str:
        """Generate unique error ID."""
        
        components = [
            type(exception).__name__,
            str(exception),
            frame.filename if frame else "",
            str(frame.lineno) if frame else "",
            str(time.time())
        ]
        
        error_data = "|".join(components)
        return hashlib.sha256(error_data.encode()).hexdigest()[:16]
    
    def _get_system_context(self) -> Dict[str, Any]:
        """Get current system context."""
        
        try:
            import psutil
            
            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "active_connections": len(psutil.net_connections()),
                "python_version": sys.version,
                "platform": sys.platform
            }
        except Exception:
            return {"error": "Failed to collect system context"}
    
    def get_error_by_id(self, error_id: str) -> Optional[ErrorDetails]:
        """Get error details by ID."""
        
        for error in self.aggregator.error_history:
            if error.error_id == error_id:
                return error
        
        return None
    
    def get_similar_errors(self, error_id: str, limit: int = 5) -> List[ErrorDetails]:
        """Get similar errors to the specified error."""
        
        target_error = self.get_error_by_id(error_id)
        if not target_error:
            return []
        
        target_pattern = self.aggregator._create_pattern_key(target_error)
        
        similar_errors = []
        for error in self.aggregator.error_history:
            if (self.aggregator._create_pattern_key(error) == target_pattern and
                error.error_id != error_id):
                similar_errors.append(error)
        
        # Sort by timestamp (most recent first)
        similar_errors.sort(key=lambda e: e.timestamp, reverse=True)
        
        return similar_errors[:limit]

# Global error tracker
error_tracker = ErrorTracker()

# Error tracking decorator
def track_errors(context_func: Optional[Callable] = None):
    """Decorator to automatically track errors."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Build context
                context = {
                    "function_name": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
                
                # Add custom context if provided
                if context_func:
                    try:
                        custom_context = await context_func(*args, **kwargs)
                        context.update(custom_context)
                    except Exception:
                        pass  # Don't fail if context function fails
                
                # Track the error
                error_id = await error_tracker.track_error(e, context)
                
                # Add error ID to exception for reference
                e.error_id = error_id
                
                raise
        
        return wrapper
    return decorator

# Error monitoring endpoints
@app.get("/admin/errors/summary")
async def get_error_summary(hours: int = 1):
    """Get error summary for specified hours."""
    return error_tracker.aggregator.get_error_summary(hours)

@app.get("/admin/errors/{error_id}")
async def get_error_details(error_id: str):
    """Get detailed error information."""
    error = error_tracker.get_error_by_id(error_id)
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    similar_errors = error_tracker.get_similar_errors(error_id)
    
    return {
        "error": asdict(error),
        "similar_errors": [asdict(e) for e in similar_errors]
    }

@app.get("/admin/errors/patterns")
async def get_error_patterns():
    """Get error patterns and frequencies."""
    
    patterns = []
    for pattern_key, pattern_data in error_tracker.aggregator.error_patterns.items():
        patterns.append({
            "pattern_id": pattern_key,
            "count": pattern_data["count"],
            "first_seen": pattern_data["first_seen"].isoformat(),
            "last_seen": pattern_data["last_seen"].isoformat(),
            "recent_count": len(pattern_data["recent_occurrences"]),
            "sample_error": {
                "exception_type": pattern_data["sample_error"].exception_type,
                "function_name": pattern_data["sample_error"].function_name,
                "message": pattern_data["sample_error"].exception_message
            }
        })
    
    # Sort by count (most frequent first)
    patterns.sort(key=lambda p: p["count"], reverse=True)
    
    return {"patterns": patterns}
```

## Recovery Procedures

### Automated Recovery Systems
```python
import asyncio
from typing import Dict, Any, List, Callable, Optional
from enum import Enum
from dataclasses import dataclass
import time

class RecoveryAction(Enum):
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    RECONNECT_DATABASE = "reconnect_database"
    SCALE_RESOURCES = "scale_resources"
    FALLBACK_MODE = "fallback_mode"
    CIRCUIT_BREAKER_RESET = "circuit_breaker_reset"
    FLUSH_QUEUES = "flush_queues"
    GARBAGE_COLLECT = "garbage_collect"

@dataclass
class RecoveryProcedure:
    name: str
    actions: List[RecoveryAction]
    trigger_conditions: Dict[str, Any]
    max_attempts: int = 3
    cooldown_seconds: int = 300
    timeout_seconds: int = 60

class RecoveryManager:
    """Manage automated recovery procedures."""
    
    def __init__(self):
        self.procedures: Dict[str, RecoveryProcedure] = {}
        self.action_handlers: Dict[RecoveryAction, Callable] = {}
        self.recovery_history = []
        self.active_recoveries = set()
        
        # Register default action handlers
        self._register_default_handlers()
    
    def register_procedure(self, procedure: RecoveryProcedure):
        """Register a recovery procedure."""
        self.procedures[procedure.name] = procedure
    
    def register_action_handler(self, action: RecoveryAction, handler: Callable):
        """Register handler for recovery action."""
        self.action_handlers[action] = handler
    
    async def evaluate_and_recover(self, system_metrics: Dict[str, Any]) -> List[str]:
        """Evaluate system state and execute recovery procedures if needed."""
        
        executed_procedures = []
        
        for procedure_name, procedure in self.procedures.items():
            if self._should_execute_procedure(procedure, system_metrics):
                success = await self.execute_recovery(procedure_name)
                if success:
                    executed_procedures.append(procedure_name)
        
        return executed_procedures
    
    def _should_execute_procedure(
        self,
        procedure: RecoveryProcedure,
        metrics: Dict[str, Any]
    ) -> bool:
        """Check if procedure should be executed based on conditions."""
        
        # Check if already running
        if procedure.name in self.active_recoveries:
            return False
        
        # Check cooldown period
        if self._is_in_cooldown(procedure.name):
            return False
        
        # Check trigger conditions
        for condition, threshold in procedure.trigger_conditions.items():
            metric_value = metrics.get(condition, 0)
            
            if isinstance(threshold, dict):
                # Range check
                if "min" in threshold and metric_value < threshold["min"]:
                    return True
                if "max" in threshold and metric_value > threshold["max"]:
                    return True
            else:
                # Simple threshold check
                if metric_value > threshold:
                    return True
        
        return False
    
    def _is_in_cooldown(self, procedure_name: str) -> bool:
        """Check if procedure is in cooldown period."""
        
        # Find last execution
        last_execution = None
        for record in reversed(self.recovery_history):
            if record["procedure"] == procedure_name:
                last_execution = record
                break
        
        if not last_execution:
            return False
        
        procedure = self.procedures[procedure_name]
        time_since_last = time.time() - last_execution["timestamp"]
        
        return time_since_last < procedure.cooldown_seconds
    
    async def execute_recovery(self, procedure_name: str) -> bool:
        """Execute a specific recovery procedure."""
        
        if procedure_name not in self.procedures:
            logger.error(f"Recovery procedure '{procedure_name}' not found")
            return False
        
        procedure = self.procedures[procedure_name]
        
        # Mark as active
        self.active_recoveries.add(procedure_name)
        
        recovery_record = {
            "procedure": procedure_name,
            "timestamp": time.time(),
            "success": False,
            "actions_executed": [],
            "errors": []
        }
        
        try:
            logger.info(f"Starting recovery procedure: {procedure_name}")
            
            # Execute each action in the procedure
            for action in procedure.actions:
                try:
                    await self._execute_action(action, procedure.timeout_seconds)
                    recovery_record["actions_executed"].append(action.value)
                    
                except Exception as e:
                    error_msg = f"Action {action.value} failed: {str(e)}"
                    logger.error(error_msg)
                    recovery_record["errors"].append(error_msg)
                    
                    # Stop execution on first failure
                    break
            
            # Consider successful if at least one action succeeded
            recovery_record["success"] = len(recovery_record["actions_executed"]) > 0
            
            if recovery_record["success"]:
                logger.info(f"Recovery procedure '{procedure_name}' completed successfully")
            else:
                logger.error(f"Recovery procedure '{procedure_name}' failed")
            
            return recovery_record["success"]
            
        finally:
            # Record recovery attempt
            self.recovery_history.append(recovery_record)
            
            # Remove from active recoveries
            self.active_recoveries.discard(procedure_name)
            
            # Clean old history
            self._cleanup_history()
    
    async def _execute_action(self, action: RecoveryAction, timeout: int):
        """Execute a specific recovery action."""
        
        if action not in self.action_handlers:
            raise ValueError(f"No handler registered for action: {action.value}")
        
        handler = self.action_handlers[action]
        
        try:
            await asyncio.wait_for(handler(), timeout=timeout)
            logger.info(f"Recovery action executed successfully: {action.value}")
        except asyncio.TimeoutError:
            raise Exception(f"Recovery action timed out: {action.value}")
        except Exception as e:
            raise Exception(f"Recovery action failed: {action.value} - {str(e)}")
    
    def _register_default_handlers(self):
        """Register default recovery action handlers."""
        
        self.register_action_handler(
            RecoveryAction.CLEAR_CACHE,
            self._clear_cache_handler
        )
        
        self.register_action_handler(
            RecoveryAction.RECONNECT_DATABASE,
            self._reconnect_database_handler
        )
        
        self.register_action_handler(
            RecoveryAction.GARBAGE_COLLECT,
            self._garbage_collect_handler
        )
        
        self.register_action_handler(
            RecoveryAction.CIRCUIT_BREAKER_RESET,
            self._circuit_breaker_reset_handler
        )
    
    async def _clear_cache_handler(self):
        """Clear application caches."""
        if hasattr(multi_cache, 'l1_cache'):
            multi_cache.l1_cache.cache.clear()
        logger.info("Cache cleared")
    
    async def _reconnect_database_handler(self):
        """Reconnect to Elasticsearch."""
        # Close existing connections
        if hasattr(es_pool, 'close_all_pools'):
            await es_pool.close_all_pools()
        
        # Reinitialize connections
        if hasattr(es_pool, 'initialize_clusters'):
            await es_pool.initialize_clusters()
        
        logger.info("Database connections reset")
    
    async def _garbage_collect_handler(self):
        """Force garbage collection."""
        import gc
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
    
    async def _circuit_breaker_reset_handler(self):
        """Reset all circuit breakers."""
        for breaker in circuit_breaker_manager.breakers.values():
            if breaker.state != CircuitState.CLOSED:
                breaker._transition_to_closed()
        logger.info("Circuit breakers reset")
    
    def _cleanup_history(self):
        """Clean up old recovery history."""
        cutoff_time = time.time() - 86400  # Keep last 24 hours
        self.recovery_history = [
            record for record in self.recovery_history
            if record["timestamp"] > cutoff_time
        ]
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        
        if not self.recovery_history:
            return {"message": "No recovery history available"}
        
        successful_recoveries = [r for r in self.recovery_history if r["success"]]
        failed_recoveries = [r for r in self.recovery_history if not r["success"]]
        
        return {
            "total_attempts": len(self.recovery_history),
            "successful_recoveries": len(successful_recoveries),
            "failed_recoveries": len(failed_recoveries),
            "success_rate": len(successful_recoveries) / len(self.recovery_history),
            "most_common_procedures": self._get_most_common_procedures(),
            "active_recoveries": list(self.active_recoveries),
            "recent_recoveries": self.recovery_history[-10:]  # Last 10
        }
    
    def _get_most_common_procedures(self) -> Dict[str, int]:
        """Get most commonly executed procedures."""
        
        procedure_counts = {}
        for record in self.recovery_history:
            procedure = record["procedure"]
            procedure_counts[procedure] = procedure_counts.get(procedure, 0) + 1
        
        return dict(sorted(procedure_counts.items(), key=lambda x: x[1], reverse=True))

# Initialize recovery manager
recovery_manager = RecoveryManager()

# Define recovery procedures
high_error_rate_recovery = RecoveryProcedure(
    name="high_error_rate",
    actions=[
        RecoveryAction.CLEAR_CACHE,
        RecoveryAction.CIRCUIT_BREAKER_RESET,
        RecoveryAction.GARBAGE_COLLECT
    ],
    trigger_conditions={
        "error_rate": 0.1,  # 10% error rate
        "response_time_ms": 5000  # 5 second response time
    },
    max_attempts=3,
    cooldown_seconds=300
)

memory_pressure_recovery = RecoveryProcedure(
    name="memory_pressure",
    actions=[
        RecoveryAction.GARBAGE_COLLECT,
        RecoveryAction.CLEAR_CACHE
    ],
    trigger_conditions={
        "memory_percent": 90  # 90% memory usage
    },
    max_attempts=2,
    cooldown_seconds=180
)

connection_issues_recovery = RecoveryProcedure(
    name="connection_issues",
    actions=[
        RecoveryAction.RECONNECT_DATABASE,
        RecoveryAction.CIRCUIT_BREAKER_RESET
    ],
    trigger_conditions={
        "connection_errors": 5  # 5 connection errors
    },
    max_attempts=3,
    cooldown_seconds=120
)

# Register procedures
recovery_manager.register_procedure(high_error_rate_recovery)
recovery_manager.register_procedure(memory_pressure_recovery)
recovery_manager.register_procedure(connection_issues_recovery)

# Recovery monitoring endpoint
@app.get("/admin/recovery/stats")
async def get_recovery_stats():
    """Get recovery system statistics."""
    return recovery_manager.get_recovery_stats()

@app.post("/admin/recovery/execute/{procedure_name}")
async def execute_recovery_procedure(procedure_name: str):
    """Manually execute a recovery procedure."""
    
    if procedure_name not in recovery_manager.procedures:
        raise HTTPException(status_code=404, detail="Recovery procedure not found")
    
    success = await recovery_manager.execute_recovery(procedure_name)
    
    return {
        "procedure": procedure_name,
        "success": success,
        "timestamp": time.time()
    }

# Background recovery monitor
async def recovery_monitor():
    """Background task to monitor and trigger recovery procedures."""
    
    while True:
        try:
            # Collect system metrics
            system_metrics = {
                "error_rate": 0.05,  # Replace with actual calculation
                "response_time_ms": 1500,  # Replace with actual calculation
                "memory_percent": 75,  # Replace with actual system memory
                "connection_errors": 2  # Replace with actual connection error count
            }
            
            # Evaluate and execute recovery procedures
            executed = await recovery_manager.evaluate_and_recover(system_metrics)
            
            if executed:
                logger.info(f"Executed recovery procedures: {executed}")
            
        except Exception as e:
            logger.error(f"Recovery monitor failed: {e}")
        
        await asyncio.sleep(60)  # Check every minute

# Start recovery monitoring
asyncio.create_task(recovery_monitor())
```

## Resilience Patterns

### Comprehensive Resilience Framework
```python
from typing import Dict, Any, List, Optional, Callable
import asyncio
import random
from dataclasses import dataclass
from enum import Enum

class ResiliencePattern(Enum):
    CIRCUIT_BREAKER = "circuit_breaker"
    RETRY = "retry"
    TIMEOUT = "timeout"
    BULKHEAD = "bulkhead"
    RATE_LIMIT = "rate_limit"
    FALLBACK = "fallback"

@dataclass
class ResilienceConfig:
    patterns: List[ResiliencePattern]
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    retry_config: Optional[RetryConfig] = None
    timeout_seconds: float = 30.0
    bulkhead_size: int = 10
    rate_limit: int = 100
    fallback_handler: Optional[Callable] = None

class ResilienceFramework:
    """Comprehensive resilience framework combining multiple patterns."""
    
    def __init__(self):
        self.configurations: Dict[str, ResilienceConfig] = {}
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        
    def register_service(self, service_name: str, config: ResilienceConfig):
        """Register a service with resilience configuration."""
        
        self.configurations[service_name] = config
        
        # Create bulkhead semaphore if needed
        if ResiliencePattern.BULKHEAD in config.patterns:
            self.semaphores[service_name] = asyncio.Semaphore(config.bulkhead_size)
    
    async def execute(
        self,
        service_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with configured resilience patterns."""
        
        if service_name not in self.configurations:
            # No resilience configuration, execute directly
            return await func(*args, **kwargs)
        
        config = self.configurations[service_name]
        
        # Apply patterns in order
        wrapped_func = func
        
        # Apply timeout
        if ResiliencePattern.TIMEOUT in config.patterns:
            wrapped_func = self._apply_timeout(wrapped_func, config.timeout_seconds)
        
        # Apply bulkhead
        if ResiliencePattern.BULKHEAD in config.patterns:
            wrapped_func = self._apply_bulkhead(wrapped_func, service_name)
        
        # Apply rate limiting
        if ResiliencePattern.RATE_LIMIT in config.patterns:
            wrapped_func = self._apply_rate_limit(wrapped_func, service_name, config.rate_limit)
        
        # Apply circuit breaker
        if ResiliencePattern.CIRCUIT_BREAKER in config.patterns:
            wrapped_func = self._apply_circuit_breaker(wrapped_func, service_name, config.circuit_breaker_config)
        
        # Apply retry
        if ResiliencePattern.RETRY in config.patterns:
            wrapped_func = self._apply_retry(wrapped_func, config.retry_config)
        
        # Apply fallback
        if ResiliencePattern.FALLBACK in config.patterns and config.fallback_handler:
            wrapped_func = self._apply_fallback(wrapped_func, config.fallback_handler)
        
        return await wrapped_func(*args, **kwargs)
    
    def _apply_timeout(self, func: Callable, timeout_seconds: float) -> Callable:
        """Apply timeout pattern."""
        
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                raise Exception(f"Operation timed out after {timeout_seconds} seconds")
        
        return wrapper
    
    def _apply_bulkhead(self, func: Callable, service_name: str) -> Callable:
        """Apply bulkhead pattern."""
        
        async def wrapper(*args, **kwargs):
            semaphore = self.semaphores[service_name]
            async with semaphore:
                return await func(*args, **kwargs)
        
        return wrapper
    
    def _apply_rate_limit(self, func: Callable, service_name: str, rate_limit: int) -> Callable:
        """Apply rate limiting pattern."""
        
        async def wrapper(*args, **kwargs):
            # Use existing rate limiter
            allowed, info = await rate_limiter.is_allowed(service_name, "default")
            
            if not allowed:
                raise Exception(f"Rate limit exceeded for service {service_name}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    def _apply_circuit_breaker(
        self,
        func: Callable,
        service_name: str,
        config: Optional[CircuitBreakerConfig]
    ) -> Callable:
        """Apply circuit breaker pattern."""
        
        async def wrapper(*args, **kwargs):
            breaker = circuit_breaker_manager.get_or_create(service_name, config)
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    
    def _apply_retry(self, func: Callable, config: Optional[RetryConfig]) -> Callable:
        """Apply retry pattern."""
        
        async def wrapper(*args, **kwargs):
            retry_config = config or RetryConfig()
            return await retry_manager.execute_with_retry(
                func, retry_config, *args, **kwargs
            )
        
        return wrapper
    
    def _apply_fallback(self, func: Callable, fallback_handler: Callable) -> Callable:
        """Apply fallback pattern."""
        
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Primary function failed, using fallback: {str(e)}")
                return await fallback_handler(*args, **kwargs)
        
        return wrapper
    
    def get_service_metrics(self, service_name: str) -> Dict[str, Any]:
        """Get metrics for a specific service."""
        
        metrics = {
            "service_name": service_name,
            "configured_patterns": []
        }
        
        if service_name in self.configurations:
            config = self.configurations[service_name]
            metrics["configured_patterns"] = [p.value for p in config.patterns]
            
            # Add bulkhead metrics
            if ResiliencePattern.BULKHEAD in config.patterns:
                semaphore = self.semaphores.get(service_name)
                if semaphore:
                    metrics["bulkhead"] = {
                        "max_concurrent": config.bulkhead_size,
                        "current_concurrent": config.bulkhead_size - semaphore._value
                    }
            
            # Add circuit breaker metrics
            if ResiliencePattern.CIRCUIT_BREAKER in config.patterns:
                breaker = circuit_breaker_manager.breakers.get(service_name)
                if breaker:
                    metrics["circuit_breaker"] = breaker.get_metrics()
        
        return metrics

# Initialize resilience framework
resilience_framework = ResilienceFramework()

# Configure services
elasticsearch_config = ResilienceConfig(
    patterns=[
        ResiliencePattern.CIRCUIT_BREAKER,
        ResiliencePattern.RETRY,
        ResiliencePattern.TIMEOUT,
        ResiliencePattern.BULKHEAD
    ],
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30
    ),
    retry_config=RetryConfig(
        max_attempts=3,
        base_delay=1.0
    ),
    timeout_seconds=30.0,
    bulkhead_size=20
)

cache_config = ResilienceConfig(
    patterns=[
        ResiliencePattern.TIMEOUT,
        ResiliencePattern.FALLBACK
    ],
    timeout_seconds=5.0,
    fallback_handler=lambda *args, **kwargs: {"cached": False, "data": None}
)

# Register services
resilience_framework.register_service("elasticsearch", elasticsearch_config)
resilience_framework.register_service("cache", cache_config)

# Resilient service wrapper
def resilient_service(service_name: str):
    """Decorator for resilient service execution."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await resilience_framework.execute(
                service_name, func, *args, **kwargs
            )
        return wrapper
    return decorator

# Example usage
@resilient_service("elasticsearch")
async def resilient_search(query: str, index: str):
    """Resilient Elasticsearch search."""
    es_client = await es_pool.get_client()
    return await es_client.search(
        index=index,
        body={"query": {"match": {"content": query}}}
    )

@resilient_service("cache")
async def resilient_cache_get(key: str):
    """Resilient cache retrieval."""
    return await multi_cache.get(key)
```

## Fault Tolerance

### System-Wide Fault Tolerance
```python
import asyncio
import psutil
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import time

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILING = "failing"

@dataclass
class SystemComponent:
    name: str
    health_check: Callable[[], Awaitable[bool]]
    dependencies: List[str]
    criticality: int  # 1-10, 10 being most critical
    recovery_actions: List[str]

class FaultToleranceManager:
    """System-wide fault tolerance management."""
    
    def __init__(self):
        self.components: Dict[str, SystemComponent] = {}
        self.component_status: Dict[str, HealthStatus] = {}
        self.system_health = HealthStatus.HEALTHY
        self.health_history = []
        self.fault_scenarios = {}
        
    def register_component(self, component: SystemComponent):
        """Register a system component."""
        self.components[component.name] = component
        self.component_status[component.name] = HealthStatus.HEALTHY
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        
        health_results = {}
        
        # Check all components concurrently
        tasks = {
            name: self._check_component_health(name, component)
            for name, component in self.components.items()
        }
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                health_results[name] = {
                    "status": HealthStatus.FAILING.value,
                    "error": str(result)
                }
                self.component_status[name] = HealthStatus.FAILING
            else:
                health_results[name] = result
        
        # Determine overall system health
        self._update_system_health()
        
        # Record health check
        self.health_history.append({
            "timestamp": time.time(),
            "system_health": self.system_health.value,
            "component_statuses": dict(self.component_status)
        })
        
        # Clean old history
        self._cleanup_health_history()
        
        return {
            "system_health": self.system_health.value,
            "components": health_results,
            "check_timestamp": time.time()
        }
    
    async def _check_component_health(self, name: str, component: SystemComponent) -> Dict[str, Any]:
        """Check health of a specific component."""
        
        try:
            start_time = time.time()
            is_healthy = await component.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if is_healthy:
                status = HealthStatus.HEALTHY
                self.component_status[name] = status
            else:
                # Check dependencies before marking as failing
                dependency_status = await self._check_dependencies(component.dependencies)
                
                if dependency_status == HealthStatus.FAILING:
                    status = HealthStatus.DEGRADED  # Degraded due to dependencies
                else:
                    status = HealthStatus.FAILING
                
                self.component_status[name] = status
            
            return {
                "status": status.value,
                "response_time_ms": response_time,
                "criticality": component.criticality,
                "dependencies": component.dependencies
            }
            
        except Exception as e:
            self.component_status[name] = HealthStatus.FAILING
            return {
                "status": HealthStatus.FAILING.value,
                "error": str(e),
                "criticality": component.criticality
            }
    
    async def _check_dependencies(self, dependencies: List[str]) -> HealthStatus:
        """Check the health status of dependencies."""
        
        if not dependencies:
            return HealthStatus.HEALTHY
        
        dependency_statuses = [
            self.component_status.get(dep, HealthStatus.FAILING)
            for dep in dependencies
        ]
        
        # If any critical dependency is failing, return failing
        if HealthStatus.FAILING in dependency_statuses:
            return HealthStatus.FAILING
        elif HealthStatus.DEGRADED in dependency_statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _update_system_health(self):
        """Update overall system health based on component statuses."""
        
        critical_components = [
            name for name, component in self.components.items()
            if component.criticality >= 8
        ]
        
        critical_failing = [
            name for name in critical_components
            if self.component_status.get(name) == HealthStatus.FAILING
        ]
        
        if critical_failing:
            self.system_health = HealthStatus.CRITICAL
        elif any(status == HealthStatus.FAILING for status in self.component_status.values()):
            self.system_health = HealthStatus.DEGRADED
        elif any(status == HealthStatus.DEGRADED for status in self.component_status.values()):
            self.system_health = HealthStatus.DEGRADED
        else:
            self.system_health = HealthStatus.HEALTHY
    
    def _cleanup_health_history(self):
        """Clean up old health history."""
        cutoff_time = time.time() - 86400  # Keep last 24 hours
        self.health_history = [
            record for record in self.health_history
            if record["timestamp"] > cutoff_time
        ]
    
    async def simulate_fault(self, component_name: str, duration_seconds: int):
        """Simulate a fault for testing fault tolerance."""
        
        if component_name not in self.components:
            raise ValueError(f"Component {component_name} not found")
        
        logger.warning(f"Simulating fault for component: {component_name}")
        
        # Store original health check
        original_health_check = self.components[component_name].health_check
        
        # Replace with failing health check
        self.components[component_name].health_check = lambda: False
        
        try:
            await asyncio.sleep(duration_seconds)
        finally:
            # Restore original health check
            self.components[component_name].health_check = original_health_check
            logger.info(f"Fault simulation ended for component: {component_name}")
    
    def get_fault_tolerance_metrics(self) -> Dict[str, Any]:
        """Get fault tolerance metrics."""
        
        if not self.health_history:
            return {"message": "No health history available"}
        
        # Calculate uptime percentages
        recent_history = self.health_history[-100:]  # Last 100 checks
        
        component_uptimes = {}
        for component_name in self.components.keys():
            healthy_count = sum(
                1 for record in recent_history
                if record["component_statuses"].get(component_name) == HealthStatus.HEALTHY
            )
            uptime_percentage = (healthy_count / len(recent_history)) * 100
            component_uptimes[component_name] = uptime_percentage
        
        # Calculate system uptime
        system_healthy_count = sum(
            1 for record in recent_history
            if record["system_health"] == HealthStatus.HEALTHY.value
        )
        system_uptime = (system_healthy_count / len(recent_history)) * 100
        
        return {
            "system_uptime_percentage": system_uptime,
            "component_uptimes": component_uptimes,
            "current_system_health": self.system_health.value,
            "total_components": len(self.components),
            "healthy_components": len([
                s for s in self.component_status.values()
                if s == HealthStatus.HEALTHY
            ]),
            "health_checks_performed": len(self.health_history)
        }

# Initialize fault tolerance manager
fault_tolerance_manager = FaultToleranceManager()

# Define component health checks
async def elasticsearch_health_check() -> bool:
    """Check Elasticsearch health."""
    try:
        client = await es_pool.get_client()
        health = await client.cluster.health()
        return health["status"] in ["green", "yellow"]
    except Exception:
        return False

async def cache_health_check() -> bool:
    """Check cache health."""
    try:
        await multi_cache.set("health_check", "ok", ttl=10)
        result = await multi_cache.get("health_check")
        return result == "ok"
    except Exception:
        return False

async def memory_health_check() -> bool:
    """Check memory health."""
    try:
        memory_usage = psutil.virtual_memory().percent
        return memory_usage < 90
    except Exception:
        return False

async def disk_health_check() -> bool:
    """Check disk health."""
    try:
        disk_usage = psutil.disk_usage('/').percent
        return disk_usage < 85
    except Exception:
        return False

# Register components
fault_tolerance_manager.register_component(SystemComponent(
    name="elasticsearch",
    health_check=elasticsearch_health_check,
    dependencies=[],
    criticality=10,
    recovery_actions=["restart_service", "reconnect_database"]
))

fault_tolerance_manager.register_component(SystemComponent(
    name="cache",
    health_check=cache_health_check,
    dependencies=["memory"],
    criticality=7,
    recovery_actions=["clear_cache", "restart_service"]
))

fault_tolerance_manager.register_component(SystemComponent(
    name="memory",
    health_check=memory_health_check,
    dependencies=[],
    criticality=9,
    recovery_actions=["garbage_collect", "clear_cache"]
))

fault_tolerance_manager.register_component(SystemComponent(
    name="disk",
    health_check=disk_health_check,
    dependencies=[],
    criticality=8,
    recovery_actions=["cleanup_logs", "compress_data"]
))

# Fault tolerance endpoints
@app.get("/admin/health/system")
async def system_health_check():
    """Get comprehensive system health status."""
    return await fault_tolerance_manager.health_check_all()

@app.get("/admin/health/metrics")
async def get_fault_tolerance_metrics():
    """Get fault tolerance metrics."""
    return fault_tolerance_manager.get_fault_tolerance_metrics()

@app.post("/admin/health/simulate-fault/{component_name}")
async def simulate_component_fault(component_name: str, duration: int = 60):
    """Simulate a component fault for testing."""
    try:
        await fault_tolerance_manager.simulate_fault(component_name, duration)
        return {"message": f"Fault simulation completed for {component_name}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Background health monitoring
async def health_monitor():
    """Background task for continuous health monitoring."""
    
    while True:
        try:
            await fault_tolerance_manager.health_check_all()
            
            # Trigger recovery if needed
            if fault_tolerance_manager.system_health in [HealthStatus.CRITICAL, HealthStatus.DEGRADED]:
                logger.warning(f"System health is {fault_tolerance_manager.system_health.value}, checking recovery options")
                
                # Trigger automated recovery
                system_metrics = {
                    "system_health": fault_tolerance_manager.system_health.value,
                    "component_failures": len([
                        s for s in fault_tolerance_manager.component_status.values()
                        if s == HealthStatus.FAILING
                    ])
                }
                
                await recovery_manager.evaluate_and_recover(system_metrics)
            
        except Exception as e:
            logger.error(f"Health monitoring failed: {e}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

# Start health monitoring
asyncio.create_task(health_monitor())
```

## Next Steps

1. **[Testing Strategies](../07-testing-deployment/01_testing-strategies.md)** - Comprehensive testing approaches
2. **[Deployment Patterns](../07-testing-deployment/02_deployment-strategies.md)** - Production deployment strategies
3. **[Monitoring & Logging](01_monitoring-logging.md)** - Return to monitoring patterns

## Additional Resources

- **Resilience Engineering**: [resilience-engineering.org](https://www.resilience-engineering.org/)
- **Circuit Breaker Pattern**: [martinfowler.com/bliki/CircuitBreaker.html](https://martinfowler.com/bliki/CircuitBreaker.html)
- **Bulkhead Pattern**: [docs.microsoft.com/en-us/azure/architecture/patterns/bulkhead](https://docs.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
- **Chaos Engineering**: [principlesofchaos.org](https://principlesofchaos.org/)