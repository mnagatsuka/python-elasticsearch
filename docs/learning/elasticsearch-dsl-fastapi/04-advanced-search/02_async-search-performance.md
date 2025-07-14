# Async Search Performance

Comprehensive guide to optimizing search performance in FastAPI applications with async patterns, caching strategies, connection pooling, and performance monitoring for high-throughput Elasticsearch operations.

## Table of Contents
- [Performance Optimization Fundamentals](#performance-optimization-fundamentals)
- [Async Processing Patterns](#async-processing-patterns)
- [Caching Strategies](#caching-strategies)
- [Connection Pooling and Resource Management](#connection-pooling-and-resource-management)
- [Large Dataset Processing](#large-dataset-processing)
- [Monitoring and Profiling](#monitoring-and-profiling)
- [Scaling Patterns](#scaling-patterns)
- [Next Steps](#next-steps)

## Performance Optimization Fundamentals

### Elasticsearch Client Optimization

```python
from fastapi import FastAPI, Depends, HTTPException
from elasticsearch_dsl import AsyncSearch, connections, Document
from elasticsearch import AsyncElasticsearch
from typing import Optional, Dict, Any, List
import asyncio
import time
import logging
from contextlib import asynccontextmanager
import aioredis
from prometheus_client import Counter, Histogram, generate_latest
import uvloop

app = FastAPI()
logger = logging.getLogger(__name__)

# Performance metrics
SEARCH_COUNTER = Counter('elasticsearch_searches_total', 'Total searches', ['operation', 'status'])
SEARCH_DURATION = Histogram('elasticsearch_search_duration_seconds', 'Search duration', ['operation'])

class OptimizedElasticsearchClient:
    """Optimized Elasticsearch client with connection pooling"""
    
    def __init__(self):
        self.client = None
        self.connection_pool_size = 20
        self.max_retries = 3
        self.retry_on_timeout = True
        self.sniff_on_start = True
        self.sniff_on_connection_fail = True
    
    async def initialize(self, hosts: List[str]):
        """Initialize optimized Elasticsearch client"""
        self.client = AsyncElasticsearch(
            hosts=hosts,
            
            # Connection pool optimization
            maxsize=self.connection_pool_size,
            
            # Timeout optimization
            timeout=30,
            request_timeout=30,
            
            # Retry configuration
            max_retries=self.max_retries,
            retry_on_timeout=self.retry_on_timeout,
            
            # Connection discovery
            sniff_on_start=self.sniff_on_start,
            sniff_on_connection_fail=self.sniff_on_connection_fail,
            sniff_timeout=10,
            
            # HTTP compression
            http_compress=True,
            
            # Connection keep-alive
            http_auth=None,  # Add auth if needed
            use_ssl=False,   # Enable for production
            verify_certs=False,
            
            # Performance tuning
            dead_timeout=60,
            selector_class='random'  # Load balancing
        )
        
        # Register with elasticsearch-dsl
        connections.add_connection('default', self.client)
        
        # Test connection
        try:
            await self.client.info()
            logger.info("Elasticsearch client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch client: {e}")
            raise
    
    async def close(self):
        """Close client connections"""
        if self.client:
            await self.client.close()

# Global client instance
es_client = OptimizedElasticsearchClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    await es_client.initialize(['localhost:9200'])
    
    # Set event loop policy for better performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    yield
    
    # Shutdown
    await es_client.close()

app = FastAPI(lifespan=lifespan)

class PerformanceOptimizedSearch:
    """High-performance search implementation"""
    
    def __init__(self, index: str, client=None):
        self.index = index
        self.client = client or es_client.client
        self.search = AsyncSearch(index=index, using=self.client)
        self._request_cache = True
        self._preference = None
        self._routing = None
        self._timeout = "30s"
    
    def with_performance_optimizations(self, 
                                     request_cache: bool = True,
                                     preference: str = None,
                                     routing: str = None,
                                     timeout: str = "30s") -> 'PerformanceOptimizedSearch':
        """Apply performance optimizations"""
        self._request_cache = request_cache
        self._preference = preference
        self._routing = routing
        self._timeout = timeout
        return self
    
    def optimize_for_throughput(self) -> 'PerformanceOptimizedSearch':
        """Optimize for high-throughput scenarios"""
        # Reduce precision for better performance
        self.search = self.search.extra(
            batched_reduce_size=512,
            pre_filter_shard_size=128,
            max_concurrent_shard_requests=5
        )
        return self
    
    def optimize_for_latency(self) -> 'PerformanceOptimizedSearch':
        """Optimize for low-latency scenarios"""
        self.search = self.search.extra(
            terminate_after=1000,  # Early termination
            timeout="5s"
        )
        return self
    
    def with_source_filtering(self, includes: List[str] = None, excludes: List[str] = None) -> 'PerformanceOptimizedSearch':
        """Optimize by filtering source fields"""
        if includes:
            self.search = self.search.source(includes)
        elif excludes:
            self.search = self.search.source([f"!{field}" for field in excludes])
        return self
    
    def with_stored_fields(self, fields: List[str]) -> 'PerformanceOptimizedSearch':
        """Use stored fields instead of source"""
        self.search = self.search.extra(stored_fields=fields)
        return self
    
    async def execute_with_metrics(self, operation_name: str = "search") -> Dict[str, Any]:
        """Execute search with performance metrics"""
        start_time = time.time()
        
        try:
            # Apply performance settings
            search = self.search
            
            if self._request_cache:
                search = search.extra(request_cache=True)
            
            if self._preference:
                search = search.extra(preference=self._preference)
            
            if self._routing:
                search = search.extra(routing=self._routing)
            
            search = search.extra(timeout=self._timeout)
            
            # Execute search
            with SEARCH_DURATION.labels(operation=operation_name).time():
                response = await search.execute()
            
            execution_time = time.time() - start_time
            
            # Record metrics
            SEARCH_COUNTER.labels(operation=operation_name, status='success').inc()
            
            # Log performance
            if execution_time > 1.0:
                logger.warning(f"Slow query detected: {operation_name} took {execution_time:.2f}s")
            
            return {
                'total': response.hits.total.value,
                'took': response.took,
                'execution_time': execution_time,
                'max_score': response.hits.max_score,
                'hits': [hit.to_dict() for hit in response.hits],
                'timed_out': response.timed_out
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            SEARCH_COUNTER.labels(operation=operation_name, status='error').inc()
            
            logger.error(f"Search failed: {operation_name} - {e} (took {execution_time:.2f}s)")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search/optimized")
async def optimized_search(
    q: str,
    user_id: Optional[str] = None,
    high_throughput: bool = False,
    low_latency: bool = False
):
    """Optimized search endpoint"""
    search = PerformanceOptimizedSearch('products')
    
    # Build query
    search.search = search.search.query(
        'multi_match',
        query=q,
        fields=['name^2', 'description'],
        type='best_fields'
    )
    
    # Apply optimizations
    preference = f"user_{user_id}" if user_id else "_local"
    search.with_performance_optimizations(
        request_cache=True,
        preference=preference,
        timeout="10s"
    )
    
    if high_throughput:
        search.optimize_for_throughput()
    
    if low_latency:
        search.optimize_for_latency()
    
    # Optimize source
    search.with_source_filtering(includes=['name', 'price', 'category'])
    
    result = await search.execute_with_metrics('optimized_search')
    return result
```

## Async Processing Patterns

### Parallel Search Execution

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Callable
import aiofiles

class ParallelSearchProcessor:
    """Process multiple searches in parallel"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    async def execute_searches_parallel(self, searches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple searches in parallel with concurrency control"""
        async def execute_single_search(search_config: Dict[str, Any]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    search = PerformanceOptimizedSearch(search_config['index'])
                    
                    # Build search from config
                    if 'query' in search_config:
                        search.search = search.search.query(**search_config['query'])
                    
                    if 'filters' in search_config:
                        for filter_config in search_config['filters']:
                            search.search = search.search.filter(**filter_config)
                    
                    if 'size' in search_config:
                        search.search = search.search[:search_config['size']]
                    
                    # Execute with optimizations
                    result = await search.execute_with_metrics(search_config.get('operation_name', 'parallel_search'))
                    
                    return {
                        'search_id': search_config.get('id', 'unknown'),
                        'success': True,
                        'result': result
                    }
                    
                except Exception as e:
                    return {
                        'search_id': search_config.get('id', 'unknown'),
                        'success': False,
                        'error': str(e)
                    }
        
        # Execute all searches in parallel
        tasks = [execute_single_search(search) for search in searches]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def batch_process_with_backpressure(self, 
                                            items: List[Any], 
                                            processor_func: Callable,
                                            batch_size: int = 50) -> List[Any]:
        """Process items in batches with backpressure control"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch in parallel
            batch_tasks = [processor_func(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            results.extend(batch_results)
            
            # Add small delay to prevent overwhelming the system
            if i + batch_size < len(items):
                await asyncio.sleep(0.1)
        
        return results

# Global processor
parallel_processor = ParallelSearchProcessor(max_concurrent=20)

@app.post("/search/parallel")
async def parallel_multi_search(searches: List[Dict[str, Any]]):
    """Execute multiple searches in parallel"""
    if len(searches) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 searches allowed")
    
    results = await parallel_processor.execute_searches_parallel(searches)
    
    # Calculate summary statistics
    successful_searches = [r for r in results if r['success']]
    failed_searches = [r for r in results if not r['success']]
    
    return {
        'total_searches': len(searches),
        'successful': len(successful_searches),
        'failed': len(failed_searches),
        'results': results
    }

# Streaming search results
class StreamingSearchProcessor:
    """Stream search results for large datasets"""
    
    def __init__(self, index: str):
        self.index = index
    
    async def stream_search_results(self, 
                                  query: Dict[str, Any], 
                                  batch_size: int = 100,
                                  max_results: int = 10000) -> AsyncIterator[Dict[str, Any]]:
        """Stream search results in batches"""
        search = PerformanceOptimizedSearch(self.index)
        search.search = search.search.query(**query)
        search.search = search.search[:batch_size]
        
        processed_count = 0
        
        while processed_count < max_results:
            # Set pagination
            search.search = search.search[processed_count:processed_count + batch_size]
            
            try:
                result = await search.execute_with_metrics('streaming_search')
                
                if not result['hits']:
                    break
                
                yield {
                    'batch_start': processed_count,
                    'batch_size': len(result['hits']),
                    'total': result['total'],
                    'hits': result['hits']
                }
                
                processed_count += len(result['hits'])
                
                # Check if we've reached the end
                if len(result['hits']) < batch_size:
                    break
                    
            except Exception as e:
                yield {
                    'error': str(e),
                    'batch_start': processed_count
                }
                break

@app.get("/search/stream")
async def stream_search_results(q: str, batch_size: int = 100):
    """Stream search results for large datasets"""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate():
        processor = StreamingSearchProcessor('products')
        query = {
            'multi_match': {
                'query': q,
                'fields': ['name', 'description']
            }
        }
        
        async for batch in processor.stream_search_results(query, batch_size):
            yield f"data: {json.dumps(batch)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )
```

## Caching Strategies

### Multi-Level Caching Implementation

```python
import hashlib
import json
import pickle
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import aioredis
from fastapi import Depends

class CacheManager:
    """Multi-level caching system for search results"""
    
    def __init__(self):
        self.redis_client = None
        self.local_cache = {}
        self.local_cache_size = 1000
        self.default_ttl = 300  # 5 minutes
    
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis connection"""
        self.redis_client = await aioredis.from_url(redis_url)
    
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate cache key from data"""
        serialized = json.dumps(data, sort_keys=True)
        hash_object = hashlib.md5(serialized.encode())
        return f"{prefix}:{hash_object.hexdigest()}"
    
    async def get_from_redis(self, key: str) -> Optional[Any]:
        """Get data from Redis cache"""
        try:
            if self.redis_client:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    return pickle.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache get error: {e}")
        return None
    
    async def set_to_redis(self, key: str, data: Any, ttl: int = None) -> bool:
        """Set data to Redis cache"""
        try:
            if self.redis_client:
                ttl = ttl or self.default_ttl
                serialized_data = pickle.dumps(data)
                await self.redis_client.setex(key, ttl, serialized_data)
                return True
        except Exception as e:
            logger.warning(f"Redis cache set error: {e}")
        return False
    
    def get_from_local(self, key: str) -> Optional[Any]:
        """Get data from local cache"""
        if key in self.local_cache:
            data, expiry = self.local_cache[key]
            if datetime.now() < expiry:
                return data
            else:
                del self.local_cache[key]
        return None
    
    def set_to_local(self, key: str, data: Any, ttl: int = None):
        """Set data to local cache"""
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        
        # Evict oldest entries if cache is full
        if len(self.local_cache) >= self.local_cache_size:
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k][1])
            del self.local_cache[oldest_key]
        
        self.local_cache[key] = (data, expiry)
    
    async def get(self, prefix: str, data: Dict[str, Any]) -> Optional[Any]:
        """Get from multi-level cache"""
        cache_key = self._generate_cache_key(prefix, data)
        
        # Try local cache first (fastest)
        result = self.get_from_local(cache_key)
        if result is not None:
            logger.debug(f"Local cache hit for {cache_key}")
            return result
        
        # Try Redis cache (slower but shared)
        result = await self.get_from_redis(cache_key)
        if result is not None:
            logger.debug(f"Redis cache hit for {cache_key}")
            # Store in local cache for future requests
            self.set_to_local(cache_key, result, ttl=60)  # Shorter TTL for local
            return result
        
        logger.debug(f"Cache miss for {cache_key}")
        return None
    
    async def set(self, prefix: str, data: Dict[str, Any], value: Any, ttl: int = None):
        """Set to multi-level cache"""
        cache_key = self._generate_cache_key(prefix, data)
        
        # Set to both caches
        self.set_to_local(cache_key, value, ttl=min(ttl or 300, 60))
        await self.set_to_redis(cache_key, value, ttl)
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        # Invalidate local cache
        keys_to_remove = [key for key in self.local_cache.keys() if pattern in key]
        for key in keys_to_remove:
            del self.local_cache[key]
        
        # Invalidate Redis cache
        try:
            if self.redis_client:
                keys = await self.redis_client.keys(f"*{pattern}*")
                if keys:
                    await self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")

# Global cache manager
cache_manager = CacheManager()

class CachedSearchBuilder:
    """Search builder with intelligent caching"""
    
    def __init__(self, index: str):
        self.index = index
        self.search = PerformanceOptimizedSearch(index)
        self.cache_ttl = 300
        self.cache_enabled = True
        self.cache_prefix = "search"
    
    def with_cache_config(self, 
                         enabled: bool = True, 
                         ttl: int = 300, 
                         prefix: str = "search") -> 'CachedSearchBuilder':
        """Configure caching behavior"""
        self.cache_enabled = enabled
        self.cache_ttl = ttl
        self.cache_prefix = prefix
        return self
    
    def _should_cache(self, query_data: Dict[str, Any]) -> bool:
        """Determine if query should be cached"""
        # Don't cache time-sensitive queries
        if 'range' in str(query_data) and 'now' in str(query_data):
            return False
        
        # Don't cache personalized queries
        if 'user_id' in query_data or 'preference' in query_data:
            return False
        
        # Don't cache very specific queries (likely one-time)
        if len(str(query_data)) > 1000:
            return False
        
        return True
    
    async def execute_with_cache(self, operation_name: str = "cached_search") -> Dict[str, Any]:
        """Execute search with caching"""
        query_data = {
            'index': self.index,
            'query': self.search.search.to_dict(),
            'operation': operation_name
        }
        
        # Check if we should use cache
        if not self.cache_enabled or not self._should_cache(query_data):
            return await self.search.execute_with_metrics(operation_name)
        
        # Try to get from cache
        cached_result = await cache_manager.get(self.cache_prefix, query_data)
        if cached_result is not None:
            # Add cache metadata
            cached_result['cache_hit'] = True
            cached_result['cache_timestamp'] = time.time()
            return cached_result
        
        # Execute search
        result = await self.search.execute_with_metrics(operation_name)
        
        # Cache the result
        result['cache_hit'] = False
        await cache_manager.set(self.cache_prefix, query_data, result, self.cache_ttl)
        
        return result

@app.get("/search/cached")
async def cached_search(
    q: str,
    category: Optional[str] = None,
    enable_cache: bool = True,
    cache_ttl: int = 300
):
    """Search with intelligent caching"""
    builder = CachedSearchBuilder('products')
    
    # Configure caching
    builder.with_cache_config(
        enabled=enable_cache,
        ttl=cache_ttl,
        prefix="product_search"
    )
    
    # Build query
    builder.search.search = builder.search.search.query(
        'multi_match',
        query=q,
        fields=['name^2', 'description']
    )
    
    if category:
        builder.search.search = builder.search.search.filter('term', category=category)
    
    result = await builder.execute_with_cache('cached_product_search')
    return result

# Cache warming strategies
class CacheWarmer:
    """Proactively warm cache with popular queries"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.popular_queries = []
    
    async def warm_popular_queries(self):
        """Warm cache with popular search queries"""
        # In real implementation, get from analytics
        popular_queries = [
            {'q': 'laptop', 'category': 'electronics'},
            {'q': 'shoes', 'category': 'fashion'},
            {'q': 'books', 'category': 'media'}
        ]
        
        for query in popular_queries:
            try:
                builder = CachedSearchBuilder('products')
                builder.search.search = builder.search.search.query(
                    'multi_match',
                    query=query['q'],
                    fields=['name^2', 'description']
                )
                
                if 'category' in query:
                    builder.search.search = builder.search.search.filter('term', category=query['category'])
                
                # Execute to warm cache
                await builder.execute_with_cache('cache_warming')
                logger.info(f"Warmed cache for query: {query}")
                
            except Exception as e:
                logger.error(f"Failed to warm cache for query {query}: {e}")
    
    async def schedule_cache_warming(self):
        """Schedule periodic cache warming"""
        while True:
            await self.warm_popular_queries()
            await asyncio.sleep(3600)  # Warm every hour

# Start cache warming on startup
@app.on_event("startup")
async def startup_cache():
    await cache_manager.initialize()
    
    # Start cache warming in background
    cache_warmer = CacheWarmer(cache_manager)
    asyncio.create_task(cache_warmer.schedule_cache_warming())
```

## Connection Pooling and Resource Management

### Advanced Connection Management

```python
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import psutil
import threading
from dataclasses import dataclass

@dataclass
class ConnectionPoolStats:
    """Connection pool statistics"""
    active_connections: int
    idle_connections: int
    total_connections: int
    peak_connections: int
    connection_errors: int
    average_response_time: float

class AdvancedConnectionManager:
    """Advanced connection pool management"""
    
    def __init__(self):
        self.pools = {}
        self.pool_stats = {}
        self.health_check_interval = 30
        self.max_pool_size = 50
        self.min_pool_size = 5
        self.connection_timeout = 30
        self.health_monitor_task = None
    
    async def create_pool(self, 
                         pool_name: str, 
                         hosts: List[str],
                         pool_size: int = None) -> AsyncElasticsearch:
        """Create optimized connection pool"""
        pool_size = pool_size or self.max_pool_size
        
        # Calculate optimal pool size based on system resources
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total // (1024**3)
        
        # Adjust pool size based on resources
        optimal_size = min(pool_size, max(cpu_count * 4, memory_gb * 2))
        
        client = AsyncElasticsearch(
            hosts=hosts,
            maxsize=optimal_size,
            timeout=self.connection_timeout,
            request_timeout=self.connection_timeout,
            
            # Advanced connection settings
            max_retries=3,
            retry_on_timeout=True,
            retry_on_status=[429, 502, 503, 504],
            
            # Health monitoring
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniff_timeout=10,
            
            # Performance optimization
            http_compress=True,
            dead_timeout=60,
            selector_class='round_robin'
        )
        
        self.pools[pool_name] = client
        self.pool_stats[pool_name] = ConnectionPoolStats(
            active_connections=0,
            idle_connections=optimal_size,
            total_connections=optimal_size,
            peak_connections=0,
            connection_errors=0,
            average_response_time=0.0
        )
        
        return client
    
    @asynccontextmanager
    async def get_connection(self, pool_name: str = 'default'):
        """Get connection from pool with monitoring"""
        if pool_name not in self.pools:
            raise ValueError(f"Pool {pool_name} not found")
        
        client = self.pools[pool_name]
        stats = self.pool_stats[pool_name]
        
        # Update stats
        stats.active_connections += 1
        stats.idle_connections = max(0, stats.idle_connections - 1)
        stats.peak_connections = max(stats.peak_connections, stats.active_connections)
        
        start_time = time.time()
        
        try:
            yield client
            
            # Update response time
            response_time = time.time() - start_time
            stats.average_response_time = (
                (stats.average_response_time * 0.9) + (response_time * 0.1)
            )
            
        except Exception as e:
            stats.connection_errors += 1
            logger.error(f"Connection error in pool {pool_name}: {e}")
            raise
        
        finally:
            # Update stats
            stats.active_connections = max(0, stats.active_connections - 1)
            stats.idle_connections += 1
    
    async def health_check(self):
        """Perform health checks on all pools"""
        for pool_name, client in self.pools.items():
            try:
                # Simple health check
                await client.ping()
                
                # Get cluster stats
                cluster_stats = await client.cluster.stats()
                logger.info(f"Pool {pool_name} healthy - nodes: {cluster_stats['nodes']['count']['total']}")
                
            except Exception as e:
                logger.error(f"Health check failed for pool {pool_name}: {e}")
                stats = self.pool_stats[pool_name]
                stats.connection_errors += 1
    
    async def start_health_monitoring(self):
        """Start background health monitoring"""
        async def monitor():
            while True:
                await self.health_check()
                await asyncio.sleep(self.health_check_interval)
        
        self.health_monitor_task = asyncio.create_task(monitor())
    
    async def get_pool_stats(self, pool_name: str) -> ConnectionPoolStats:
        """Get connection pool statistics"""
        return self.pool_stats.get(pool_name)
    
    async def close_all_pools(self):
        """Close all connection pools"""
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
        
        for pool_name, client in self.pools.items():
            try:
                await client.close()
                logger.info(f"Closed pool: {pool_name}")
            except Exception as e:
                logger.error(f"Error closing pool {pool_name}: {e}")

# Global connection manager
connection_manager = AdvancedConnectionManager()

class ResourceManagedSearch:
    """Search with advanced resource management"""
    
    def __init__(self, index: str, pool_name: str = 'default'):
        self.index = index
        self.pool_name = pool_name
    
    async def execute_with_resource_management(self, 
                                             query: Dict[str, Any],
                                             max_memory_mb: int = 500) -> Dict[str, Any]:
        """Execute search with resource monitoring"""
        # Check system resources before execution
        memory_before = psutil.virtual_memory().percent
        
        if memory_before > 90:
            raise HTTPException(status_code=503, detail="System memory usage too high")
        
        async with connection_manager.get_connection(self.pool_name) as client:
            search = AsyncSearch(index=self.index, using=client)
            search = search.query(**query)
            
            # Monitor memory during execution
            start_memory = psutil.Process().memory_info().rss // 1024 // 1024
            
            try:
                response = await search.execute()
                
                # Check memory usage after execution
                end_memory = psutil.Process().memory_info().rss // 1024 // 1024
                memory_used = end_memory - start_memory
                
                if memory_used > max_memory_mb:
                    logger.warning(f"High memory usage: {memory_used}MB for search")
                
                return {
                    'total': response.hits.total.value,
                    'hits': [hit.to_dict() for hit in response.hits],
                    'memory_used_mb': memory_used,
                    'system_memory_percent': psutil.virtual_memory().percent
                }
                
            except Exception as e:
                logger.error(f"Search failed with resource management: {e}")
                raise

@app.get("/search/resource-managed")
async def resource_managed_search(q: str):
    """Search with resource management"""
    search = ResourceManagedSearch('products')
    
    query = {
        'multi_match': {
            'query': q,
            'fields': ['name^2', 'description']
        }
    }
    
    result = await search.execute_with_resource_management(query)
    return result

@app.get("/admin/connection-stats")
async def get_connection_stats():
    """Get connection pool statistics"""
    stats = {}
    for pool_name in connection_manager.pools.keys():
        pool_stats = await connection_manager.get_pool_stats(pool_name)
        stats[pool_name] = {
            'active_connections': pool_stats.active_connections,
            'idle_connections': pool_stats.idle_connections,
            'total_connections': pool_stats.total_connections,
            'peak_connections': pool_stats.peak_connections,
            'connection_errors': pool_stats.connection_errors,
            'average_response_time': pool_stats.average_response_time
        }
    
    return stats
```

## Large Dataset Processing

### Bulk Operations and Streaming

```python
from typing import AsyncIterator, Generator
import aiofiles
import csv
import json

class BulkSearchProcessor:
    """Process large datasets with bulk operations"""
    
    def __init__(self, index: str, batch_size: int = 1000):
        self.index = index
        self.batch_size = batch_size
        self.processed_count = 0
        self.error_count = 0
    
    async def bulk_search_documents(self, 
                                  query_templates: List[Dict[str, Any]],
                                  output_file: str = None) -> AsyncIterator[Dict[str, Any]]:
        """Perform bulk searches and optionally save to file"""
        
        async with connection_manager.get_connection() as client:
            file_handle = None
            
            if output_file:
                file_handle = await aiofiles.open(output_file, 'w', newline='')
            
            try:
                for i, query_template in enumerate(query_templates):
                    try:
                        # Build search
                        search = AsyncSearch(index=self.index, using=client)
                        search = search.query(**query_template['query'])
                        
                        if 'filters' in query_template:
                            for filter_config in query_template['filters']:
                                search = search.filter(**filter_config)
                        
                        if 'size' in query_template:
                            search = search[:query_template['size']]
                        
                        # Execute search
                        response = await search.execute()
                        
                        result = {
                            'query_id': query_template.get('id', i),
                            'total': response.hits.total.value,
                            'hits': [hit.to_dict() for hit in response.hits],
                            'success': True
                        }
                        
                        # Write to file if specified
                        if file_handle:
                            await file_handle.write(json.dumps(result) + '\n')
                        
                        yield result
                        
                        self.processed_count += 1
                        
                        # Progress logging
                        if self.processed_count % 100 == 0:
                            logger.info(f"Processed {self.processed_count} bulk searches")
                        
                        # Rate limiting
                        if i % self.batch_size == 0:
                            await asyncio.sleep(0.1)
                    
                    except Exception as e:
                        self.error_count += 1
                        error_result = {
                            'query_id': query_template.get('id', i),
                            'error': str(e),
                            'success': False
                        }
                        
                        if file_handle:
                            await file_handle.write(json.dumps(error_result) + '\n')
                        
                        yield error_result
            
            finally:
                if file_handle:
                    await file_handle.close()
    
    async def scroll_search_all_documents(self, 
                                        query: Dict[str, Any],
                                        scroll_size: int = 1000,
                                        max_docs: int = None) -> AsyncIterator[Dict[str, Any]]:
        """Scroll through all documents matching query"""
        
        async with connection_manager.get_connection() as client:
            # Initial search
            search = AsyncSearch(index=self.index, using=client)
            search = search.query(**query)
            search = search[:scroll_size]
            
            response = await search.execute()
            scroll_id = response._scroll_id
            
            processed_docs = 0
            
            try:
                while response.hits and (max_docs is None or processed_docs < max_docs):
                    batch_results = []
                    
                    for hit in response.hits:
                        doc = {
                            '_id': hit.meta.id,
                            '_score': hit.meta.score,
                            '_source': hit.to_dict()
                        }
                        batch_results.append(doc)
                        processed_docs += 1
                        
                        if max_docs and processed_docs >= max_docs:
                            break
                    
                    yield {
                        'batch_size': len(batch_results),
                        'processed_total': processed_docs,
                        'documents': batch_results
                    }
                    
                    # Continue scrolling
                    if max_docs is None or processed_docs < max_docs:
                        response = await client.scroll(
                            scroll_id=scroll_id,
                            scroll='2m'
                        )
                        scroll_id = response['_scroll_id']
                        
                        # Convert to response object
                        from elasticsearch_dsl.response import Response
                        response = Response(response)
            
            finally:
                # Clear scroll
                if scroll_id:
                    try:
                        await client.clear_scroll(scroll_id=scroll_id)
                    except Exception as e:
                        logger.warning(f"Failed to clear scroll: {e}")

@app.post("/search/bulk-process")
async def bulk_process_searches(
    query_templates: List[Dict[str, Any]],
    output_file: Optional[str] = None
):
    """Process multiple searches in bulk"""
    if len(query_templates) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 queries allowed")
    
    processor = BulkSearchProcessor('products')
    results = []
    
    async for result in processor.bulk_search_documents(query_templates, output_file):
        results.append(result)
    
    return {
        'total_queries': len(query_templates),
        'processed_count': processor.processed_count,
        'error_count': processor.error_count,
        'output_file': output_file,
        'sample_results': results[:10]  # Return first 10 for preview
    }

@app.get("/search/export-all")
async def export_all_documents(
    q: Optional[str] = None,
    category: Optional[str] = None,
    max_docs: int = 10000
):
    """Export all matching documents"""
    from fastapi.responses import StreamingResponse
    import io
    
    # Build query
    query = {'match_all': {}}
    if q:
        query = {
            'multi_match': {
                'query': q,
                'fields': ['name', 'description']
            }
        }
    
    processor = BulkSearchProcessor('products')
    
    async def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['id', 'name', 'description', 'price', 'category'])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        # Stream documents
        async for batch in processor.scroll_search_all_documents(query, max_docs=max_docs):
            for doc in batch['documents']:
                source = doc['_source']
                writer.writerow([
                    doc['_id'],
                    source.get('name', ''),
                    source.get('description', ''),
                    source.get('price', ''),
                    source.get('category', '')
                ])
            
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
    
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=search_results.csv"}
    )
```

## Monitoring and Profiling

### Comprehensive Performance Monitoring

```python
import time
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil

@dataclass
class SearchProfileData:
    """Search profiling data"""
    query_type: str
    execution_times: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    result_counts: List[int] = field(default_factory=list)
    error_count: int = 0
    total_executions: int = 0

class PerformanceMonitor:
    """Comprehensive performance monitoring"""
    
    def __init__(self):
        self.profiles = {}
        self.system_metrics = {}
        self.alerts = []
        
        # Prometheus metrics
        self.search_duration = Histogram(
            'search_duration_seconds',
            'Search execution duration',
            ['operation', 'index']
        )
        
        self.search_counter = Counter(
            'searches_total',
            'Total number of searches',
            ['operation', 'status']
        )
        
        self.memory_usage = Gauge(
            'search_memory_usage_bytes',
            'Memory usage during search'
        )
        
        self.active_connections = Gauge(
            'elasticsearch_active_connections',
            'Active Elasticsearch connections'
        )
    
    def start_profiling(self, operation_name: str):
        """Start profiling a search operation"""
        if operation_name not in self.profiles:
            self.profiles[operation_name] = SearchProfileData(operation_name)
        
        return {
            'start_time': time.time(),
            'start_memory': psutil.Process().memory_info().rss,
            'operation': operation_name
        }
    
    def finish_profiling(self, profile_context: Dict[str, Any], 
                        result_count: int = 0, 
                        success: bool = True):
        """Finish profiling and record metrics"""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        operation = profile_context['operation']
        execution_time = end_time - profile_context['start_time']
        memory_used = end_memory - profile_context['start_memory']
        
        # Update profile data
        profile = self.profiles[operation]
        profile.execution_times.append(execution_time)
        profile.memory_usage.append(memory_used)
        profile.result_counts.append(result_count)
        profile.total_executions += 1
        
        if not success:
            profile.error_count += 1
        
        # Update Prometheus metrics
        self.search_duration.labels(
            operation=operation,
            index='products'  # Could be dynamic
        ).observe(execution_time)
        
        self.search_counter.labels(
            operation=operation,
            status='success' if success else 'error'
        ).inc()
        
        self.memory_usage.set(psutil.Process().memory_info().rss)
        
        # Check for performance alerts
        self._check_performance_alerts(operation, execution_time, memory_used)
    
    def _check_performance_alerts(self, operation: str, execution_time: float, memory_used: int):
        """Check for performance alerts"""
        alerts = []
        
        # Slow query alert
        if execution_time > 5.0:
            alerts.append({
                'type': 'slow_query',
                'operation': operation,
                'execution_time': execution_time,
                'threshold': 5.0,
                'timestamp': time.time()
            })
        
        # High memory usage alert
        memory_mb = memory_used / 1024 / 1024
        if memory_mb > 100:
            alerts.append({
                'type': 'high_memory',
                'operation': operation,
                'memory_mb': memory_mb,
                'threshold': 100,
                'timestamp': time.time()
            })
        
        # System memory alert
        system_memory = psutil.virtual_memory().percent
        if system_memory > 90:
            alerts.append({
                'type': 'system_memory',
                'memory_percent': system_memory,
                'threshold': 90,
                'timestamp': time.time()
            })
        
        self.alerts.extend(alerts)
        
        # Keep only recent alerts (last hour)
        current_time = time.time()
        self.alerts = [
            alert for alert in self.alerts
            if current_time - alert['timestamp'] < 3600
        ]
    
    def get_performance_report(self, operation: str = None) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        if operation and operation in self.profiles:
            profile = self.profiles[operation]
            return self._generate_profile_report(profile)
        
        # Generate report for all operations
        report = {
            'operations': {},
            'system_metrics': self._get_system_metrics(),
            'alerts': self.alerts[-10:],  # Last 10 alerts
            'summary': {
                'total_operations': len(self.profiles),
                'total_executions': sum(p.total_executions for p in self.profiles.values()),
                'total_errors': sum(p.error_count for p in self.profiles.values())
            }
        }
        
        for op_name, profile in self.profiles.items():
            report['operations'][op_name] = self._generate_profile_report(profile)
        
        return report
    
    def _generate_profile_report(self, profile: SearchProfileData) -> Dict[str, Any]:
        """Generate report for a specific profile"""
        if not profile.execution_times:
            return {'no_data': True}
        
        return {
            'total_executions': profile.total_executions,
            'error_count': profile.error_count,
            'error_rate': profile.error_count / profile.total_executions,
            'execution_time': {
                'mean': statistics.mean(profile.execution_times),
                'median': statistics.median(profile.execution_times),
                'min': min(profile.execution_times),
                'max': max(profile.execution_times),
                'p95': statistics.quantiles(profile.execution_times, n=20)[18] 
                      if len(profile.execution_times) >= 20 else max(profile.execution_times),
                'p99': statistics.quantiles(profile.execution_times, n=100)[98] 
                      if len(profile.execution_times) >= 100 else max(profile.execution_times)
            },
            'memory_usage': {
                'mean_mb': statistics.mean(profile.memory_usage) / 1024 / 1024,
                'max_mb': max(profile.memory_usage) / 1024 / 1024,
                'min_mb': min(profile.memory_usage) / 1024 / 1024
            },
            'result_counts': {
                'mean': statistics.mean(profile.result_counts),
                'max': max(profile.result_counts),
                'min': min(profile.result_counts)
            }
        }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg(),
            'active_connections': len(psutil.net_connections())
        }

# Global performance monitor
performance_monitor = PerformanceMonitor()

def profile_search(operation_name: str):
    """Decorator for profiling search operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Start profiling
            profile_ctx = performance_monitor.start_profiling(operation_name)
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract result count
                result_count = 0
                if isinstance(result, dict):
                    result_count = result.get('total', 0)
                
                # Finish profiling
                performance_monitor.finish_profiling(
                    profile_ctx, 
                    result_count=result_count, 
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Finish profiling with error
                performance_monitor.finish_profiling(
                    profile_ctx, 
                    result_count=0, 
                    success=False
                )
                raise
        
        return wrapper
    return decorator

@app.get("/admin/performance-report")
async def get_performance_report(operation: Optional[str] = None):
    """Get performance monitoring report"""
    return performance_monitor.get_performance_report(operation)

@app.get("/admin/metrics")
async def get_prometheus_metrics():
    """Get Prometheus metrics"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest())

# Apply profiling to search endpoints
@profile_search('optimized_search')
async def profiled_optimized_search(q: str):
    """Optimized search with profiling"""
    # Implementation here...
    pass
```

## Scaling Patterns

### Horizontal Scaling and Load Distribution

```python
import random
from typing import List, Dict, Any
from fastapi import BackgroundTasks
import aiohttp

class SearchLoadBalancer:
    """Load balancer for distributed search"""
    
    def __init__(self):
        self.elasticsearch_clusters = []
        self.cluster_weights = {}
        self.cluster_health = {}
        self.round_robin_index = 0
    
    def add_cluster(self, cluster_name: str, hosts: List[str], weight: float = 1.0):
        """Add Elasticsearch cluster"""
        self.elasticsearch_clusters.append({
            'name': cluster_name,
            'hosts': hosts,
            'weight': weight
        })
        self.cluster_weights[cluster_name] = weight
        self.cluster_health[cluster_name] = True
    
    async def health_check_clusters(self):
        """Check health of all clusters"""
        async with aiohttp.ClientSession() as session:
            for cluster in self.elasticsearch_clusters:
                try:
                    # Simple health check
                    async with session.get(f"http://{cluster['hosts'][0]}/_cluster/health") as response:
                        if response.status == 200:
                            health_data = await response.json()
                            self.cluster_health[cluster['name']] = health_data['status'] in ['green', 'yellow']
                        else:
                            self.cluster_health[cluster['name']] = False
                except Exception as e:
                    logger.error(f"Health check failed for cluster {cluster['name']}: {e}")
                    self.cluster_health[cluster['name']] = False
    
    def select_cluster(self, strategy: str = 'weighted_random') -> Dict[str, Any]:
        """Select cluster based on strategy"""
        healthy_clusters = [
            cluster for cluster in self.elasticsearch_clusters
            if self.cluster_health[cluster['name']]
        ]
        
        if not healthy_clusters:
            raise HTTPException(status_code=503, detail="No healthy clusters available")
        
        if strategy == 'round_robin':
            cluster = healthy_clusters[self.round_robin_index % len(healthy_clusters)]
            self.round_robin_index += 1
        
        elif strategy == 'weighted_random':
            weights = [self.cluster_weights[cluster['name']] for cluster in healthy_clusters]
            cluster = random.choices(healthy_clusters, weights=weights)[0]
        
        elif strategy == 'least_connections':
            # In real implementation, track active connections per cluster
            cluster = healthy_clusters[0]  # Simplified
        
        else:
            cluster = random.choice(healthy_clusters)
        
        return cluster

class DistributedSearchManager:
    """Manage distributed search across clusters"""
    
    def __init__(self, load_balancer: SearchLoadBalancer):
        self.load_balancer = load_balancer
        self.search_cache = {}
    
    async def distributed_search(self, 
                               query: Dict[str, Any], 
                               index: str,
                               cross_cluster: bool = False) -> Dict[str, Any]:
        """Execute search across distributed clusters"""
        
        if cross_cluster:
            # Search all healthy clusters and merge results
            return await self._cross_cluster_search(query, index)
        else:
            # Search single cluster
            cluster = self.load_balancer.select_cluster('weighted_random')
            return await self._single_cluster_search(query, index, cluster)
    
    async def _single_cluster_search(self, 
                                   query: Dict[str, Any], 
                                   index: str,
                                   cluster: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search on single cluster"""
        client = AsyncElasticsearch(hosts=cluster['hosts'])
        
        try:
            search = AsyncSearch(index=index, using=client)
            search = search.query(**query)
            
            response = await search.execute()
            
            return {
                'cluster': cluster['name'],
                'total': response.hits.total.value,
                'hits': [hit.to_dict() for hit in response.hits],
                'took': response.took
            }
        
        finally:
            await client.close()
    
    async def _cross_cluster_search(self, 
                                  query: Dict[str, Any], 
                                  index: str) -> Dict[str, Any]:
        """Execute search across all clusters and merge results"""
        healthy_clusters = [
            cluster for cluster in self.load_balancer.elasticsearch_clusters
            if self.load_balancer.cluster_health[cluster['name']]
        ]
        
        # Execute searches in parallel
        tasks = []
        for cluster in healthy_clusters:
            task = self._single_cluster_search(query, index, cluster)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge results
        all_hits = []
        total_results = 0
        cluster_stats = {}
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                cluster_name = healthy_clusters[i]['name']
                cluster_stats[cluster_name] = {'error': str(result)}
                continue
            
            cluster_name = result['cluster']
            cluster_stats[cluster_name] = {
                'total': result['total'],
                'took': result['took']
            }
            
            total_results += result['total']
            
            # Add cluster info to hits
            for hit in result['hits']:
                hit['_cluster'] = cluster_name
                all_hits.append(hit)
        
        # Sort merged results by score
        all_hits.sort(key=lambda x: x.get('_score', 0), reverse=True)
        
        return {
            'total': total_results,
            'clusters': cluster_stats,
            'hits': all_hits[:50],  # Limit merged results
            'cross_cluster': True
        }

# Global load balancer and search manager
load_balancer = SearchLoadBalancer()
search_manager = DistributedSearchManager(load_balancer)

@app.on_event("startup")
async def setup_clusters():
    """Setup Elasticsearch clusters"""
    # Add clusters (in real implementation, load from config)
    load_balancer.add_cluster('primary', ['localhost:9200'], weight=2.0)
    load_balancer.add_cluster('secondary', ['localhost:9201'], weight=1.0)
    
    # Start health monitoring
    async def health_monitor():
        while True:
            await load_balancer.health_check_clusters()
            await asyncio.sleep(30)
    
    asyncio.create_task(health_monitor())

@app.get("/search/distributed")
async def distributed_search(
    q: str,
    cross_cluster: bool = False,
    strategy: str = 'weighted_random'
):
    """Distributed search across clusters"""
    query = {
        'multi_match': {
            'query': q,
            'fields': ['name^2', 'description']
        }
    }
    
    result = await search_manager.distributed_search(
        query, 
        'products', 
        cross_cluster=cross_cluster
    )
    
    return result

@app.get("/admin/cluster-health")
async def get_cluster_health():
    """Get cluster health status"""
    await load_balancer.health_check_clusters()
    
    return {
        'clusters': [
            {
                'name': cluster['name'],
                'hosts': cluster['hosts'],
                'weight': load_balancer.cluster_weights[cluster['name']],
                'healthy': load_balancer.cluster_health[cluster['name']]
            }
            for cluster in load_balancer.elasticsearch_clusters
        ]
    }
```

## Next Steps

1. **[Aggregations and Faceting](03_aggregations-faceting.md)** - Master data aggregation and analytics
2. **[Geospatial and Vector Search](04_geospatial-vector-search.md)** - Implement advanced search capabilities
3. **[Data Modeling](../05-data-modeling/01_document-design.md)** - Design efficient document structures
4. **[Production Patterns](../06-production-patterns/01_monitoring-logging.md)** - Production deployment patterns
5. **[Testing and Deployment](../07-testing-deployment/01_testing-strategies.md)** - Testing and CI/CD strategies

## Additional Resources

- **Elasticsearch Performance Tuning**: [elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)
- **Python Async Programming**: [docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html)
- **FastAPI Performance**: [fastapi.tiangolo.com/advanced/](https://fastapi.tiangolo.com/advanced/)
- **Redis Caching**: [redis.io/docs/](https://redis.io/docs/)
- **Prometheus Monitoring**: [prometheus.io/docs/](https://prometheus.io/docs/)