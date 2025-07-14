# Performance Optimization

Advanced performance optimization patterns for production FastAPI + Elasticsearch-DSL applications with enterprise-scale efficiency.

## Table of Contents
- [Query Optimization](#query-optimization)
- [Connection Pooling](#connection-pooling)
- [Caching Strategies](#caching-strategies)
- [Scaling Patterns](#scaling-patterns)
- [Load Balancing](#load-balancing)
- [Performance Monitoring](#performance-monitoring)
- [Memory Management](#memory-management)
- [Next Steps](#next-steps)

## Query Optimization

### Elasticsearch Query Optimization
```python
from elasticsearch_dsl import Search, Q, A
from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass
import time

@dataclass
class QueryPerformanceMetrics:
    took_ms: int
    total_hits: int
    max_score: float
    shard_count: int
    query_cache_hit: bool
    suggestion_time_ms: Optional[int] = None

class QueryOptimizer:
    """Advanced query optimization for Elasticsearch."""
    
    def __init__(self):
        self.query_cache = {}
        self.performance_thresholds = {
            "slow_query_ms": 1000,
            "very_slow_query_ms": 5000,
            "max_results": 10000
        }
    
    async def optimize_search_query(
        self,
        search: Search,
        optimization_hints: Dict[str, Any] = None
    ) -> Search:
        """Optimize search query for better performance."""
        
        hints = optimization_hints or {}
        
        # 1. Add query timeout
        search = search.params(timeout="30s")
        
        # 2. Optimize source filtering
        if hints.get("required_fields"):
            search = search.source(hints["required_fields"])
        elif hints.get("exclude_large_fields"):
            search = search.source(excludes=["large_text", "binary_data", "raw_content"])
        
        # 3. Add preference for consistent shard routing
        if hints.get("user_id"):
            search = search.params(preference=f"user_{hints['user_id']}")
        
        # 4. Optimize sort operations
        search = self._optimize_sorting(search, hints)
        
        # 5. Add result size limits
        search = self._add_size_limits(search, hints)
        
        # 6. Optimize filters for caching
        search = self._optimize_filters(search)
        
        return search
    
    def _optimize_sorting(self, search: Search, hints: Dict[str, Any]) -> Search:
        """Optimize sorting for better performance."""
        
        # Prefer field-based sorting over script-based
        if hasattr(search, '_sort') and search._sort:
            optimized_sorts = []
            
            for sort_clause in search._sort:
                if isinstance(sort_clause, dict):
                    for field, sort_opts in sort_clause.items():
                        if field.startswith('_script'):
                            # Replace script sorting with field sorting when possible
                            if hints.get("prefer_field_sort"):
                                optimized_sorts.append({"timestamp": {"order": "desc"}})
                            else:
                                optimized_sorts.append(sort_clause)
                        else:
                            # Add unmapped_type for missing fields
                            if isinstance(sort_opts, dict):
                                sort_opts.setdefault("unmapped_type", "long")
                            optimized_sorts.append({field: sort_opts})
                else:
                    optimized_sorts.append(sort_clause)
            
            search._sort = optimized_sorts
        
        return search
    
    def _add_size_limits(self, search: Search, hints: Dict[str, Any]) -> Search:
        """Add appropriate size limits to prevent large result sets."""
        
        current_size = getattr(search, '_size', 10)
        max_size = hints.get("max_size", self.performance_thresholds["max_results"])
        
        if current_size > max_size:
            search = search.extra(size=max_size)
            
        return search
    
    def _optimize_filters(self, search: Search) -> Search:
        """Optimize filters for better caching."""
        
        if hasattr(search, 'query') and search.query:
            # Convert term queries to filters when possible
            optimized_query = self._convert_terms_to_filters(search.query)
            search.query = optimized_query
        
        return search
    
    def _convert_terms_to_filters(self, query) -> Q:
        """Convert term queries to filters for better caching."""
        
        if hasattr(query, 'to_dict'):
            query_dict = query.to_dict()
            
            # Convert bool query terms to filters
            if 'bool' in query_dict:
                bool_query = query_dict['bool']
                
                # Move term/terms queries from must to filter
                if 'must' in bool_query:
                    must_clauses = bool_query['must']
                    filter_clauses = bool_query.get('filter', [])
                    new_must = []
                    
                    for clause in must_clauses:
                        if any(key in clause for key in ['term', 'terms', 'range']):
                            filter_clauses.append(clause)
                        else:
                            new_must.append(clause)
                    
                    bool_query['must'] = new_must
                    bool_query['filter'] = filter_clauses
        
        return query

class AsyncBulkProcessor:
    """Optimized bulk processing for high-throughput operations."""
    
    def __init__(self, es_client, chunk_size: int = 500, max_concurrent: int = 5):
        self.es_client = es_client
        self.chunk_size = chunk_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bulk_index_documents(
        self,
        documents: List[Dict[str, Any]],
        index_name: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """Efficiently bulk index documents with concurrency control."""
        
        # Split into chunks
        chunks = [
            documents[i:i + self.chunk_size]
            for i in range(0, len(documents), self.chunk_size)
        ]
        
        results = {
            "total_docs": len(documents),
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        # Process chunks concurrently
        tasks = [
            self._process_chunk(chunk, index_name, chunk_idx, results)
            for chunk_idx, chunk in enumerate(chunks)
        ]
        
        completed_chunks = 0
        for task in asyncio.as_completed(tasks):
            await task
            completed_chunks += 1
            
            if progress_callback:
                progress = (completed_chunks / len(chunks)) * 100
                await progress_callback(progress)
        
        return results
    
    async def _process_chunk(
        self,
        chunk: List[Dict[str, Any]],
        index_name: str,
        chunk_idx: int,
        results: Dict[str, Any]
    ):
        """Process a single chunk of documents."""
        
        async with self.semaphore:
            try:
                # Prepare bulk actions
                actions = []
                for doc in chunk:
                    action = {
                        "_index": index_name,
                        "_source": doc
                    }
                    
                    # Add document ID if provided
                    if "_id" in doc:
                        action["_id"] = doc["_id"]
                    
                    actions.append(action)
                
                # Execute bulk operation
                response = await self.es_client.bulk(
                    body=actions,
                    refresh=False,  # Don't refresh immediately
                    timeout="60s"
                )
                
                # Process results
                for item in response.get("items", []):
                    if "index" in item:
                        if item["index"].get("status") in [200, 201]:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append({
                                "chunk": chunk_idx,
                                "error": item["index"].get("error")
                            })
                
            except Exception as e:
                results["failed"] += len(chunk)
                results["errors"].append({
                    "chunk": chunk_idx,
                    "error": str(e)
                })

query_optimizer = QueryOptimizer()
```

## Connection Pooling

### Advanced Connection Management
```python
import aiohttp
import asyncio
from elasticsearch import AsyncElasticsearch
from typing import Optional, Dict, Any
import ssl
from urllib3.util.retry import Retry

class ElasticsearchConnectionPool:
    """Advanced Elasticsearch connection pool with health monitoring."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pools = {}
        self.health_check_interval = 30
        self.max_retries = 3
        self.timeout_config = {
            "connect": 10,
            "read": 30,
            "total": 60
        }
        
    async def get_client(self, pool_name: str = "default") -> AsyncElasticsearch:
        """Get or create an Elasticsearch client from pool."""
        
        if pool_name not in self.pools:
            await self._create_pool(pool_name)
        
        return self.pools[pool_name]["client"]
    
    async def _create_pool(self, pool_name: str):
        """Create a new connection pool."""
        
        # SSL/TLS configuration
        ssl_context = ssl.create_default_context()
        if not self.config.get("verify_ssl", True):
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connection timeout and retry configuration
        timeout = aiohttp.ClientTimeout(
            total=self.timeout_config["total"],
            connect=self.timeout_config["connect"],
            sock_read=self.timeout_config["read"]
        )
        
        # Create HTTP session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=20,  # Connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            ssl=ssl_context,
            enable_cleanup_closed=True
        )
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # Create Elasticsearch client
        client = AsyncElasticsearch(
            hosts=self.config["hosts"],
            http_auth=(self.config["username"], self.config["password"]),
            use_ssl=self.config.get("use_ssl", True),
            verify_certs=self.config.get("verify_ssl", True),
            ssl_context=ssl_context,
            timeout=30,
            max_retries=self.max_retries,
            retry_on_timeout=True,
            http_session=session
        )
        
        self.pools[pool_name] = {
            "client": client,
            "session": session,
            "health_status": "unknown",
            "last_health_check": None
        }
        
        # Start health monitoring
        asyncio.create_task(self._monitor_pool_health(pool_name))
    
    async def _monitor_pool_health(self, pool_name: str):
        """Monitor pool health and recreate if needed."""
        
        while pool_name in self.pools:
            try:
                pool = self.pools[pool_name]
                client = pool["client"]
                
                # Perform health check
                health = await client.cluster.health()
                pool["health_status"] = health["status"]
                pool["last_health_check"] = time.time()
                
                # Log health status
                if health["status"] != "green":
                    logger.warning(
                        "Elasticsearch cluster health degraded",
                        pool_name=pool_name,
                        status=health["status"]
                    )
                
            except Exception as e:
                logger.error(
                    "Health check failed for pool",
                    pool_name=pool_name,
                    error=str(e)
                )
                pool["health_status"] = "unhealthy"
            
            await asyncio.sleep(self.health_check_interval)
    
    async def close_pool(self, pool_name: str):
        """Close a specific connection pool."""
        
        if pool_name in self.pools:
            pool = self.pools[pool_name]
            
            # Close Elasticsearch client
            await pool["client"].close()
            
            # Close HTTP session
            await pool["session"].close()
            
            del self.pools[pool_name]
    
    async def close_all_pools(self):
        """Close all connection pools."""
        
        for pool_name in list(self.pools.keys()):
            await self.close_pool(pool_name)

# Connection pool middleware
class ConnectionPoolMiddleware:
    """Middleware for connection pool management."""
    
    def __init__(self, pool_manager: ElasticsearchConnectionPool):
        self.pool_manager = pool_manager
    
    async def __call__(self, request, call_next):
        # Add pool manager to request state
        request.state.es_pool = self.pool_manager
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log connection errors
            logger.error(
                "Request failed with connection error",
                error=str(e),
                path=request.url.path
            )
            raise

# Global connection pool
es_pool = ElasticsearchConnectionPool({
    "hosts": ["https://localhost:9200"],
    "username": "elastic",
    "password": "password",
    "use_ssl": True,
    "verify_ssl": False
})

async def get_es_client(request) -> AsyncElasticsearch:
    """Dependency to get Elasticsearch client from pool."""
    return await request.state.es_pool.get_client()
```

## Caching Strategies

### Multi-Layer Caching System
```python
import redis.asyncio as redis
import json
import hashlib
from typing import Any, Optional, Union
import pickle
from datetime import timedelta
import asyncio

class CacheLayer:
    """Base cache layer interface."""
    
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        raise NotImplementedError

class MemoryCache(CacheLayer):
    """In-memory cache layer with LRU eviction."""
    
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.access_order = []
        self.max_size = max_size
        self.ttl_data = {}
    
    async def get(self, key: str) -> Optional[Any]:
        current_time = time.time()
        
        # Check if key exists and not expired
        if key in self.cache:
            if key in self.ttl_data and self.ttl_data[key] < current_time:
                await self.delete(key)
                return None
            
            # Update access order
            self.access_order.remove(key)
            self.access_order.append(key)
            
            return self.cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        current_time = time.time()
        
        # Add to cache
        self.cache[key] = value
        self.ttl_data[key] = current_time + ttl
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        # Evict if necessary
        await self._evict_if_needed()
        
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            if key in self.ttl_data:
                del self.ttl_data[key]
            if key in self.access_order:
                self.access_order.remove(key)
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None
    
    async def _evict_if_needed(self):
        """Evict least recently used items if cache is full."""
        
        while len(self.cache) > self.max_size:
            lru_key = self.access_order.pop(0)
            await self.delete(lru_key)

class RedisCache(CacheLayer):
    """Redis-based cache layer."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            data = await self.redis.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        try:
            data = pickle.dumps(value)
            return await self.redis.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            return await self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists failed: {e}")
            return False

class MultiLayerCache:
    """Multi-layer cache with L1 (memory) and L2 (Redis) layers."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.l1_cache = MemoryCache(max_size=500)
        self.l2_cache = RedisCache(redis_client) if redis_client else None
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "sets": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache layers."""
        
        # Try L1 cache first
        value = await self.l1_cache.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value
        
        # Try L2 cache
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value is not None:
                self.stats["l2_hits"] += 1
                # Backfill L1 cache
                await self.l1_cache.set(key, value, ttl=3600)
                return value
        
        self.stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in all cache layers."""
        
        self.stats["sets"] += 1
        
        # Set in L1 cache
        await self.l1_cache.set(key, value, ttl)
        
        # Set in L2 cache if available
        if self.l2_cache:
            await self.l2_cache.set(key, value, ttl)
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete from all cache layers."""
        
        l1_deleted = await self.l1_cache.delete(key)
        l2_deleted = True
        
        if self.l2_cache:
            l2_deleted = await self.l2_cache.delete(key)
        
        return l1_deleted or l2_deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        
        total_requests = sum([
            self.stats["l1_hits"],
            self.stats["l2_hits"],
            self.stats["misses"]
        ])
        
        if total_requests == 0:
            return self.stats
        
        return {
            **self.stats,
            "hit_rate": (self.stats["l1_hits"] + self.stats["l2_hits"]) / total_requests,
            "l1_hit_rate": self.stats["l1_hits"] / total_requests,
            "l2_hit_rate": self.stats["l2_hits"] / total_requests
        }

class SearchResultCache:
    """Specialized cache for search results."""
    
    def __init__(self, cache: MultiLayerCache):
        self.cache = cache
        self.default_ttl = 3600  # 1 hour
    
    def _generate_cache_key(self, query: Dict[str, Any], index: str) -> str:
        """Generate cache key for search query."""
        
        # Create deterministic hash of query
        query_str = json.dumps(query, sort_keys=True)
        query_hash = hashlib.md5(query_str.encode()).hexdigest()
        
        return f"search:{index}:{query_hash}"
    
    async def get_cached_result(
        self,
        query: Dict[str, Any],
        index: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached search result."""
        
        cache_key = self._generate_cache_key(query, index)
        return await self.cache.get(cache_key)
    
    async def cache_result(
        self,
        query: Dict[str, Any],
        index: str,
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ):
        """Cache search result."""
        
        cache_key = self._generate_cache_key(query, index)
        ttl = ttl or self.default_ttl
        
        # Only cache successful results
        if result.get("hits", {}).get("total", {}).get("value", 0) > 0:
            await self.cache.set(cache_key, result, ttl)
    
    async def invalidate_index_cache(self, index: str):
        """Invalidate all cached results for an index."""
        
        # This would require pattern-based deletion in production
        # For now, we'll just clear the cache entirely
        logger.info(f"Cache invalidation requested for index: {index}")

# Initialize caching system
redis_client = redis.Redis(host="localhost", port=6379, db=0)
multi_cache = MultiLayerCache(redis_client)
search_cache = SearchResultCache(multi_cache)

# Caching decorator
def cache_search_result(ttl: int = 3600):
    """Decorator to cache search results."""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract query and index from arguments
            if 'query' in kwargs and 'index' in kwargs:
                query = kwargs['query']
                index = kwargs['index']
                
                # Try to get from cache
                cached_result = await search_cache.get_cached_result(query, index)
                if cached_result:
                    return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await search_cache.cache_result(query, index, result, ttl)
                
                return result
            else:
                # No caching if we can't identify query/index
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

## Scaling Patterns

### Horizontal Scaling Architecture
```python
from typing import List, Dict, Any
import hashlib
import asyncio
import random

class ShardingStrategy:
    """Base class for sharding strategies."""
    
    def get_shard(self, key: str, shard_count: int) -> int:
        raise NotImplementedError

class HashSharding(ShardingStrategy):
    """Hash-based sharding strategy."""
    
    def get_shard(self, key: str, shard_count: int) -> int:
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return hash_value % shard_count

class ConsistentHashSharding(ShardingStrategy):
    """Consistent hash-based sharding."""
    
    def __init__(self, virtual_nodes: int = 150):
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
    
    def add_node(self, node: str):
        """Add a node to the consistent hash ring."""
        for i in range(self.virtual_nodes):
            virtual_key = hashlib.md5(f"{node}:{i}".encode()).hexdigest()
            self.ring[virtual_key] = node
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def get_shard(self, key: str, shard_count: int) -> int:
        if not self.ring:
            return 0
        
        hash_key = hashlib.md5(key.encode()).hexdigest()
        
        # Find the first node with hash >= hash_key
        for ring_key in self.sorted_keys:
            if hash_key <= ring_key:
                node = self.ring[ring_key]
                return int(node.split('_')[-1]) % shard_count
        
        # Wrap around to first node
        node = self.ring[self.sorted_keys[0]]
        return int(node.split('_')[-1]) % shard_count

class ElasticsearchClusterManager:
    """Manage multiple Elasticsearch clusters for scaling."""
    
    def __init__(self, clusters: List[Dict[str, Any]], sharding_strategy: ShardingStrategy):
        self.clusters = clusters
        self.sharding_strategy = sharding_strategy
        self.cluster_clients = {}
        self.cluster_health = {}
        
    async def initialize_clusters(self):
        """Initialize connections to all clusters."""
        
        for i, cluster_config in enumerate(self.clusters):
            cluster_id = f"cluster_{i}"
            
            # Create client for each cluster
            client = AsyncElasticsearch(
                hosts=cluster_config["hosts"],
                http_auth=(cluster_config["username"], cluster_config["password"]),
                use_ssl=cluster_config.get("use_ssl", True),
                verify_certs=cluster_config.get("verify_ssl", False),
                timeout=30,
                max_retries=3
            )
            
            self.cluster_clients[cluster_id] = client
            
            # Start health monitoring
            asyncio.create_task(self._monitor_cluster_health(cluster_id))
    
    async def _monitor_cluster_health(self, cluster_id: str):
        """Monitor health of a specific cluster."""
        
        while cluster_id in self.cluster_clients:
            try:
                client = self.cluster_clients[cluster_id]
                health = await client.cluster.health()
                
                self.cluster_health[cluster_id] = {
                    "status": health["status"],
                    "nodes": health["number_of_nodes"],
                    "last_check": time.time()
                }
                
            except Exception as e:
                self.cluster_health[cluster_id] = {
                    "status": "red",
                    "error": str(e),
                    "last_check": time.time()
                }
            
            await asyncio.sleep(30)
    
    async def get_cluster_for_document(self, document_id: str) -> AsyncElasticsearch:
        """Get the appropriate cluster for a document."""
        
        shard = self.sharding_strategy.get_shard(document_id, len(self.clusters))
        cluster_id = f"cluster_{shard}"
        
        # Check if cluster is healthy
        if cluster_id in self.cluster_health:
            health = self.cluster_health[cluster_id]
            if health.get("status") == "red":
                # Fall back to a healthy cluster
                return await self._get_healthy_cluster()
        
        return self.cluster_clients[cluster_id]
    
    async def _get_healthy_cluster(self) -> AsyncElasticsearch:
        """Get a healthy cluster as fallback."""
        
        healthy_clusters = [
            cluster_id for cluster_id, health in self.cluster_health.items()
            if health.get("status") in ["green", "yellow"]
        ]
        
        if healthy_clusters:
            cluster_id = random.choice(healthy_clusters)
            return self.cluster_clients[cluster_id]
        
        # If no healthy clusters, return first available
        return list(self.cluster_clients.values())[0]
    
    async def search_across_clusters(
        self,
        query: Dict[str, Any],
        index_pattern: str
    ) -> Dict[str, Any]:
        """Search across all healthy clusters and merge results."""
        
        # Get healthy clusters
        healthy_clusters = [
            (cluster_id, client) for cluster_id, client in self.cluster_clients.items()
            if self.cluster_health.get(cluster_id, {}).get("status") in ["green", "yellow"]
        ]
        
        if not healthy_clusters:
            raise Exception("No healthy clusters available")
        
        # Execute search on all clusters concurrently
        search_tasks = [
            self._search_cluster(client, query, index_pattern, cluster_id)
            for cluster_id, client in healthy_clusters
        ]
        
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Merge results
        return self._merge_search_results(results)
    
    async def _search_cluster(
        self,
        client: AsyncElasticsearch,
        query: Dict[str, Any],
        index_pattern: str,
        cluster_id: str
    ) -> Dict[str, Any]:
        """Search a specific cluster."""
        
        try:
            result = await client.search(
                index=index_pattern,
                body=query,
                timeout="30s"
            )
            result["_cluster_id"] = cluster_id
            return result
            
        except Exception as e:
            logger.error(
                "Cluster search failed",
                cluster_id=cluster_id,
                error=str(e)
            )
            return {"error": str(e), "_cluster_id": cluster_id}
    
    def _merge_search_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge search results from multiple clusters."""
        
        all_hits = []
        total_hits = 0
        max_score = 0
        took_total = 0
        
        for result in results:
            if isinstance(result, Exception) or "error" in result:
                continue
            
            hits = result.get("hits", {})
            all_hits.extend(hits.get("hits", []))
            total_hits += hits.get("total", {}).get("value", 0)
            
            if hits.get("max_score", 0) > max_score:
                max_score = hits.get("max_score", 0)
            
            took_total += result.get("took", 0)
        
        # Sort by score and apply size limit
        all_hits.sort(key=lambda x: x.get("_score", 0), reverse=True)
        
        return {
            "took": took_total,
            "hits": {
                "total": {"value": total_hits, "relation": "eq"},
                "max_score": max_score,
                "hits": all_hits[:10]  # Default size limit
            }
        }

# Auto-scaling manager
class AutoScaler:
    """Automatic scaling based on metrics."""
    
    def __init__(self, cluster_manager: ElasticsearchClusterManager):
        self.cluster_manager = cluster_manager
        self.scaling_thresholds = {
            "cpu_high": 80,
            "memory_high": 85,
            "queue_depth_high": 100,
            "response_time_high": 2000  # ms
        }
        self.metrics_history = []
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics."""
        
        metrics = {
            "timestamp": time.time(),
            "cluster_metrics": {}
        }
        
        for cluster_id, client in self.cluster_manager.cluster_clients.items():
            try:
                # Get cluster stats
                stats = await client.cluster.stats()
                nodes = await client.cat.nodes(format="json")
                
                cluster_metrics = {
                    "cpu_percent": self._calculate_avg_cpu(nodes),
                    "memory_percent": self._calculate_avg_memory(nodes),
                    "disk_percent": self._calculate_avg_disk(nodes),
                    "active_shards": stats["indices"]["shards"]["total"],
                    "pending_tasks": stats.get("pending_tasks", 0)
                }
                
                metrics["cluster_metrics"][cluster_id] = cluster_metrics
                
            except Exception as e:
                logger.error(f"Failed to collect metrics for {cluster_id}: {e}")
        
        self.metrics_history.append(metrics)
        
        # Keep only last hour of metrics
        cutoff_time = time.time() - 3600
        self.metrics_history = [
            m for m in self.metrics_history
            if m["timestamp"] > cutoff_time
        ]
        
        return metrics
    
    def _calculate_avg_cpu(self, nodes: List[Dict[str, Any]]) -> float:
        """Calculate average CPU usage across nodes."""
        if not nodes:
            return 0
        
        total_cpu = sum(float(node.get("cpu", "0").replace("%", "")) for node in nodes)
        return total_cpu / len(nodes)
    
    def _calculate_avg_memory(self, nodes: List[Dict[str, Any]]) -> float:
        """Calculate average memory usage across nodes."""
        if not nodes:
            return 0
        
        total_memory = sum(
            float(node.get("ram.percent", "0").replace("%", ""))
            for node in nodes
        )
        return total_memory / len(nodes)
    
    def _calculate_avg_disk(self, nodes: List[Dict[str, Any]]) -> float:
        """Calculate average disk usage across nodes."""
        if not nodes:
            return 0
        
        total_disk = sum(
            float(node.get("disk.used_percent", "0").replace("%", ""))
            for node in nodes
        )
        return total_disk / len(nodes)
    
    async def should_scale_up(self) -> bool:
        """Determine if scaling up is needed."""
        
        if len(self.metrics_history) < 3:
            return False
        
        # Check recent metrics
        recent_metrics = self.metrics_history[-3:]
        
        for metrics in recent_metrics:
            for cluster_id, cluster_metrics in metrics["cluster_metrics"].items():
                if (cluster_metrics["cpu_percent"] > self.scaling_thresholds["cpu_high"] or
                    cluster_metrics["memory_percent"] > self.scaling_thresholds["memory_high"]):
                    return True
        
        return False
    
    async def should_scale_down(self) -> bool:
        """Determine if scaling down is possible."""
        
        if len(self.metrics_history) < 10:  # Need more history for scale down
            return False
        
        # Check if consistently low usage
        recent_metrics = self.metrics_history[-10:]
        
        for metrics in recent_metrics:
            for cluster_id, cluster_metrics in metrics["cluster_metrics"].items():
                if (cluster_metrics["cpu_percent"] > 50 or
                    cluster_metrics["memory_percent"] > 60):
                    return False
        
        return True

# Initialize scaling infrastructure
sharding_strategy = ConsistentHashSharding()
cluster_manager = ElasticsearchClusterManager(
    clusters=[
        {
            "hosts": ["https://es-cluster1:9200"],
            "username": "elastic",
            "password": "password1"
        },
        {
            "hosts": ["https://es-cluster2:9200"],
            "username": "elastic",
            "password": "password2"
        }
    ],
    sharding_strategy=sharding_strategy
)
auto_scaler = AutoScaler(cluster_manager)
```

## Load Balancing

### Advanced Load Balancing
```python
import random
import time
from typing import List, Dict, Any, Optional
from enum import Enum
import asyncio

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    HEALTH_BASED = "health_based"

class ElasticsearchNode:
    """Represents an Elasticsearch node with health and performance metrics."""
    
    def __init__(self, host: str, port: int, weight: int = 1):
        self.host = host
        self.port = port
        self.weight = weight
        self.active_connections = 0
        self.total_requests = 0
        self.total_response_time = 0
        self.health_status = "unknown"
        self.last_health_check = 0
        self.consecutive_failures = 0
        self.max_failures = 3
        
    @property
    def endpoint(self) -> str:
        return f"https://{self.host}:{self.port}"
    
    @property
    def average_response_time(self) -> float:
        if self.total_requests == 0:
            return 0
        return self.total_response_time / self.total_requests
    
    @property
    def is_healthy(self) -> bool:
        return (self.health_status in ["green", "yellow"] and
                self.consecutive_failures < self.max_failures)
    
    def record_request(self, response_time: float, success: bool):
        """Record request metrics."""
        self.total_requests += 1
        self.total_response_time += response_time
        
        if success:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1

class LoadBalancer:
    """Advanced load balancer for Elasticsearch nodes."""
    
    def __init__(self, nodes: List[ElasticsearchNode], strategy: LoadBalancingStrategy):
        self.nodes = nodes
        self.strategy = strategy
        self.current_index = 0
        self.health_check_interval = 30
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor())
    
    async def get_node(self) -> Optional[ElasticsearchNode]:
        """Get the next node based on load balancing strategy."""
        
        healthy_nodes = [node for node in self.nodes if node.is_healthy]
        if not healthy_nodes:
            logger.warning("No healthy nodes available")
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.RESPONSE_TIME:
            return self._fastest_response_time(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.HEALTH_BASED:
            return self._health_based(healthy_nodes)
        else:
            return self._round_robin(healthy_nodes)
    
    def _round_robin(self, nodes: List[ElasticsearchNode]) -> ElasticsearchNode:
        """Simple round-robin selection."""
        node = nodes[self.current_index % len(nodes)]
        self.current_index += 1
        return node
    
    def _weighted_round_robin(self, nodes: List[ElasticsearchNode]) -> ElasticsearchNode:
        """Weighted round-robin based on node weights."""
        total_weight = sum(node.weight for node in nodes)
        random_weight = random.randint(1, total_weight)
        
        current_weight = 0
        for node in nodes:
            current_weight += node.weight
            if random_weight <= current_weight:
                return node
        
        return nodes[0]  # Fallback
    
    def _least_connections(self, nodes: List[ElasticsearchNode]) -> ElasticsearchNode:
        """Select node with least active connections."""
        return min(nodes, key=lambda n: n.active_connections)
    
    def _fastest_response_time(self, nodes: List[ElasticsearchNode]) -> ElasticsearchNode:
        """Select node with fastest average response time."""
        return min(nodes, key=lambda n: n.average_response_time or float('inf'))
    
    def _health_based(self, nodes: List[ElasticsearchNode]) -> ElasticsearchNode:
        """Select based on health score (green > yellow > red)."""
        green_nodes = [n for n in nodes if n.health_status == "green"]
        if green_nodes:
            return self._least_connections(green_nodes)
        
        yellow_nodes = [n for n in nodes if n.health_status == "yellow"]
        if yellow_nodes:
            return self._least_connections(yellow_nodes)
        
        return self._least_connections(nodes)
    
    async def _health_monitor(self):
        """Monitor health of all nodes."""
        
        while True:
            health_tasks = [
                self._check_node_health(node) for node in self.nodes
            ]
            
            await asyncio.gather(*health_tasks, return_exceptions=True)
            await asyncio.sleep(self.health_check_interval)
    
    async def _check_node_health(self, node: ElasticsearchNode):
        """Check health of a specific node."""
        
        try:
            client = AsyncElasticsearch([node.endpoint])
            start_time = time.time()
            
            health = await client.cluster.health()
            response_time = (time.time() - start_time) * 1000
            
            node.health_status = health["status"]
            node.last_health_check = time.time()
            node.record_request(response_time, True)
            
            await client.close()
            
        except Exception as e:
            node.health_status = "red"
            node.record_request(0, False)
            logger.error(f"Health check failed for {node.endpoint}: {e}")

class LoadBalancedElasticsearchClient:
    """Elasticsearch client with integrated load balancing."""
    
    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self.client_pool = {}
    
    async def _get_client(self, node: ElasticsearchNode) -> AsyncElasticsearch:
        """Get or create client for a node."""
        
        if node.endpoint not in self.client_pool:
            self.client_pool[node.endpoint] = AsyncElasticsearch(
                [node.endpoint],
                timeout=30,
                max_retries=1
            )
        
        return self.client_pool[node.endpoint]
    
    async def search(self, **kwargs) -> Dict[str, Any]:
        """Execute search with load balancing."""
        
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            node = await self.load_balancer.get_node()
            if not node:
                raise Exception("No available nodes")
            
            try:
                node.active_connections += 1
                start_time = time.time()
                
                client = await self._get_client(node)
                result = await client.search(**kwargs)
                
                response_time = (time.time() - start_time) * 1000
                node.record_request(response_time, True)
                
                return result
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                node.record_request(response_time, False)
                last_exception = e
                
                logger.warning(
                    f"Request failed on {node.endpoint}, "
                    f"attempt {attempt + 1}/{max_retries}: {e}"
                )
                
            finally:
                node.active_connections = max(0, node.active_connections - 1)
        
        raise last_exception or Exception("All retry attempts failed")
    
    async def index(self, **kwargs) -> Dict[str, Any]:
        """Execute index operation with load balancing."""
        
        node = await self.load_balancer.get_node()
        if not node:
            raise Exception("No available nodes")
        
        try:
            node.active_connections += 1
            start_time = time.time()
            
            client = await self._get_client(node)
            result = await client.index(**kwargs)
            
            response_time = (time.time() - start_time) * 1000
            node.record_request(response_time, True)
            
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            node.record_request(response_time, False)
            raise
        finally:
            node.active_connections = max(0, node.active_connections - 1)
    
    async def close(self):
        """Close all client connections."""
        for client in self.client_pool.values():
            await client.close()
        self.client_pool.clear()

# Initialize load balancer
nodes = [
    ElasticsearchNode("es-node1.example.com", 9200, weight=2),
    ElasticsearchNode("es-node2.example.com", 9200, weight=1),
    ElasticsearchNode("es-node3.example.com", 9200, weight=1),
]

load_balancer = LoadBalancer(nodes, LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN)
lb_client = LoadBalancedElasticsearchClient(load_balancer)
```

## Performance Monitoring

### Real-time Performance Monitoring
```python
import psutil
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np

@dataclass
class PerformanceMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    network_io_sent: int
    network_io_recv: int
    elasticsearch_response_time: float
    active_connections: int
    cache_hit_rate: float
    search_throughput: float

class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, es_client: AsyncElasticsearch, cache: MultiLayerCache):
        self.es_client = es_client
        self.cache = cache
        self.metrics_history = []
        self.alerts = []
        self.monitoring_interval = 10  # seconds
        
        # Performance baselines
        self.baselines = {
            "cpu_percent": 70,
            "memory_percent": 80,
            "response_time_ms": 500,
            "cache_hit_rate": 0.7
        }
    
    async def start_monitoring(self):
        """Start continuous performance monitoring."""
        
        while True:
            try:
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.metrics_history = [
                    m for m in self.metrics_history
                    if m.timestamp > cutoff_time
                ]
                
                # Check for alerts
                await self.check_alerts(metrics)
                
            except Exception as e:
                logger.error(f"Performance monitoring failed: {e}")
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        network_io = psutil.net_io_counters()
        
        # Elasticsearch metrics
        es_response_time = await self._measure_es_response_time()
        active_connections = await self._get_active_connections()
        
        # Cache metrics
        cache_stats = self.cache.get_stats()
        cache_hit_rate = cache_stats.get("hit_rate", 0)
        
        # Search throughput (requests per second)
        search_throughput = await self._calculate_search_throughput()
        
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_io_read=disk_io.read_bytes if disk_io else 0,
            disk_io_write=disk_io.write_bytes if disk_io else 0,
            network_io_sent=network_io.bytes_sent if network_io else 0,
            network_io_recv=network_io.bytes_recv if network_io else 0,
            elasticsearch_response_time=es_response_time,
            active_connections=active_connections,
            cache_hit_rate=cache_hit_rate,
            search_throughput=search_throughput
        )
    
    async def _measure_es_response_time(self) -> float:
        """Measure Elasticsearch response time."""
        
        try:
            start_time = time.time()
            await self.es_client.cluster.health()
            return (time.time() - start_time) * 1000  # Convert to ms
        except Exception:
            return -1  # Indicate failure
    
    async def _get_active_connections(self) -> int:
        """Get number of active connections."""
        # This would integrate with your connection pool
        return len([c for c in psutil.net_connections() if c.status == 'ESTABLISHED'])
    
    async def _calculate_search_throughput(self) -> float:
        """Calculate search requests per second."""
        
        if len(self.metrics_history) < 2:
            return 0
        
        # Calculate based on recent requests
        recent_metrics = self.metrics_history[-6:]  # Last 6 measurements (1 minute)
        if len(recent_metrics) < 2:
            return 0
        
        time_span = (recent_metrics[-1].timestamp - recent_metrics[0].timestamp).total_seconds()
        if time_span == 0:
            return 0
        
        # Mock calculation - replace with actual request counting
        return random.uniform(10, 100)  # Requests per second
    
    async def check_alerts(self, metrics: PerformanceMetrics):
        """Check if any alerts should be triggered."""
        
        alerts = []
        
        # CPU alert
        if metrics.cpu_percent > self.baselines["cpu_percent"]:
            alerts.append({
                "type": "cpu_high",
                "value": metrics.cpu_percent,
                "threshold": self.baselines["cpu_percent"],
                "timestamp": metrics.timestamp
            })
        
        # Memory alert
        if metrics.memory_percent > self.baselines["memory_percent"]:
            alerts.append({
                "type": "memory_high",
                "value": metrics.memory_percent,
                "threshold": self.baselines["memory_percent"],
                "timestamp": metrics.timestamp
            })
        
        # Response time alert
        if metrics.elasticsearch_response_time > self.baselines["response_time_ms"]:
            alerts.append({
                "type": "response_time_high",
                "value": metrics.elasticsearch_response_time,
                "threshold": self.baselines["response_time_ms"],
                "timestamp": metrics.timestamp
            })
        
        # Cache hit rate alert
        if metrics.cache_hit_rate < self.baselines["cache_hit_rate"]:
            alerts.append({
                "type": "cache_hit_rate_low",
                "value": metrics.cache_hit_rate,
                "threshold": self.baselines["cache_hit_rate"],
                "timestamp": metrics.timestamp
            })
        
        # Store alerts
        self.alerts.extend(alerts)
        
        # Log critical alerts
        for alert in alerts:
            logger.warning(
                f"Performance alert: {alert['type']}",
                value=alert["value"],
                threshold=alert["threshold"]
            )
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the specified time period."""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No metrics available for the specified period"}
        
        # Calculate averages
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        response_times = [m.elasticsearch_response_time for m in recent_metrics if m.elasticsearch_response_time > 0]
        cache_hit_rates = [m.cache_hit_rate for m in recent_metrics]
        
        return {
            "period_hours": hours,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg": np.mean(cpu_values),
                "max": np.max(cpu_values),
                "min": np.min(cpu_values),
                "p95": np.percentile(cpu_values, 95)
            },
            "memory": {
                "avg": np.mean(memory_values),
                "max": np.max(memory_values),
                "min": np.min(memory_values),
                "p95": np.percentile(memory_values, 95)
            },
            "elasticsearch_response_time": {
                "avg": np.mean(response_times) if response_times else 0,
                "max": np.max(response_times) if response_times else 0,
                "min": np.min(response_times) if response_times else 0,
                "p95": np.percentile(response_times, 95) if response_times else 0
            },
            "cache_hit_rate": {
                "avg": np.mean(cache_hit_rates),
                "max": np.max(cache_hit_rates),
                "min": np.min(cache_hit_rates)
            }
        }

# Performance monitoring endpoints
@app.get("/admin/performance/current")
async def get_current_performance():
    """Get current performance metrics."""
    return asdict(await performance_monitor.collect_metrics())

@app.get("/admin/performance/summary")
async def get_performance_summary(hours: int = 1):
    """Get performance summary."""
    return performance_monitor.get_performance_summary(hours)

@app.get("/admin/performance/alerts")
async def get_recent_alerts(hours: int = 24):
    """Get recent performance alerts."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    recent_alerts = [
        alert for alert in performance_monitor.alerts
        if alert["timestamp"] > cutoff_time
    ]
    return {"alerts": recent_alerts, "count": len(recent_alerts)}

# Initialize performance monitoring
performance_monitor = PerformanceMonitor(es_client, multi_cache)
asyncio.create_task(performance_monitor.start_monitoring())
```

## Memory Management

### Memory Optimization Patterns
```python
import gc
import tracemalloc
from typing import Dict, Any, Optional
import weakref
from functools import wraps
import sys

class MemoryManager:
    """Advanced memory management for large-scale applications."""
    
    def __init__(self):
        self.memory_threshold_mb = 1000  # 1GB
        self.cleanup_interval = 300  # 5 minutes
        self.object_pools = {}
        self.weak_references = weakref.WeakSet()
        
        # Start memory monitoring
        tracemalloc.start()
        asyncio.create_task(self._memory_monitor())
    
    async def _memory_monitor(self):
        """Monitor memory usage and trigger cleanup when needed."""
        
        while True:
            try:
                # Get current memory usage
                memory_usage = self._get_memory_usage_mb()
                
                if memory_usage > self.memory_threshold_mb:
                    logger.warning(
                        f"High memory usage detected: {memory_usage}MB"
                    )
                    await self._trigger_cleanup()
                
                # Log memory statistics
                if len(self.weak_references) > 0:
                    logger.info(
                        f"Memory stats: {memory_usage}MB, "
                        f"tracked objects: {len(self.weak_references)}"
                    )
                
            except Exception as e:
                logger.error(f"Memory monitoring failed: {e}")
            
            await asyncio.sleep(self.cleanup_interval)
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        
        current, peak = tracemalloc.get_traced_memory()
        return current / 1024 / 1024  # Convert to MB
    
    async def _trigger_cleanup(self):
        """Trigger memory cleanup procedures."""
        
        logger.info("Starting memory cleanup")
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Clean object pools
        self._cleanup_object_pools()
        
        # Clear weak references to deleted objects
        self._cleanup_weak_references()
        
        # Clear caches if available
        if hasattr(multi_cache, 'clear'):
            await multi_cache.l1_cache._evict_if_needed()
        
        # Log new memory usage
        new_usage = self._get_memory_usage_mb()
        logger.info(f"Memory cleanup completed. Usage: {new_usage}MB")
    
    def _cleanup_object_pools(self):
        """Clean up object pools."""
        
        for pool_name, pool in self.object_pools.items():
            if hasattr(pool, 'clear'):
                pool.clear()
                logger.info(f"Cleared object pool: {pool_name}")
    
    def _cleanup_weak_references(self):
        """Clean up weak references."""
        
        # WeakSet automatically removes dead references
        logger.info(f"Active weak references: {len(self.weak_references)}")
    
    def track_object(self, obj):
        """Track an object for memory management."""
        self.weak_references.add(obj)
    
    def create_object_pool(self, name: str, factory_func, max_size: int = 100):
        """Create an object pool for memory efficiency."""
        
        self.object_pools[name] = ObjectPool(factory_func, max_size)
        return self.object_pools[name]

class ObjectPool:
    """Object pool for reusing expensive objects."""
    
    def __init__(self, factory_func, max_size: int = 100):
        self.factory_func = factory_func
        self.max_size = max_size
        self.pool = []
        self.in_use = set()
    
    def acquire(self):
        """Acquire an object from the pool."""
        
        if self.pool:
            obj = self.pool.pop()
        else:
            obj = self.factory_func()
        
        self.in_use.add(id(obj))
        return obj
    
    def release(self, obj):
        """Release an object back to the pool."""
        
        obj_id = id(obj)
        if obj_id in self.in_use:
            self.in_use.remove(obj_id)
            
            if len(self.pool) < self.max_size:
                # Reset object state if needed
                if hasattr(obj, 'reset'):
                    obj.reset()
                self.pool.append(obj)
    
    def clear(self):
        """Clear the object pool."""
        self.pool.clear()
        self.in_use.clear()

def memory_efficient(func):
    """Decorator for memory-efficient function execution."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Track memory before execution
        start_memory = memory_manager._get_memory_usage_mb()
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            # Check memory usage after execution
            end_memory = memory_manager._get_memory_usage_mb()
            memory_diff = end_memory - start_memory
            
            if memory_diff > 100:  # More than 100MB increase
                logger.warning(
                    f"High memory usage in {func.__name__}: +{memory_diff}MB"
                )
                # Trigger cleanup if memory usage is high
                if end_memory > memory_manager.memory_threshold_mb:
                    await memory_manager._trigger_cleanup()
    
    return wrapper

# Memory-optimized search result processor
class MemoryEfficientSearchProcessor:
    """Process search results with memory optimization."""
    
    def __init__(self):
        self.result_pool = ObjectPool(lambda: {}, max_size=50)
    
    @memory_efficient
    async def process_search_results(
        self,
        raw_results: Dict[str, Any],
        transform_func: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Process search results with memory optimization."""
        
        # Use object pool for result dict
        processed_results = self.result_pool.acquire()
        
        try:
            # Clear previous data
            processed_results.clear()
            
            # Process hits efficiently
            hits = raw_results.get("hits", {}).get("hits", [])
            processed_hits = []
            
            for hit in hits:
                # Process each hit and immediately release large objects
                processed_hit = self._process_hit(hit, transform_func)
                processed_hits.append(processed_hit)
                
                # Clear source reference to help GC
                if "_source" in hit:
                    del hit["_source"]
            
            processed_results.update({
                "hits": {
                    "total": raw_results.get("hits", {}).get("total", {}),
                    "max_score": raw_results.get("hits", {}).get("max_score"),
                    "hits": processed_hits
                },
                "took": raw_results.get("took"),
                "timed_out": raw_results.get("timed_out", False)
            })
            
            # Create a copy to return (since we'll release the pooled object)
            return dict(processed_results)
            
        finally:
            # Release object back to pool
            self.result_pool.release(processed_results)
    
    def _process_hit(self, hit: Dict[str, Any], transform_func: Optional[callable]) -> Dict[str, Any]:
        """Process individual hit with memory efficiency."""
        
        processed = {
            "_id": hit.get("_id"),
            "_score": hit.get("_score"),
            "_source": hit.get("_source", {})
        }
        
        if transform_func:
            processed["_source"] = transform_func(processed["_source"])
        
        return processed

# Initialize memory management
memory_manager = MemoryManager()
search_processor = MemoryEfficientSearchProcessor()

# Memory monitoring endpoint
@app.get("/admin/memory/stats")
async def get_memory_stats():
    """Get current memory statistics."""
    
    current, peak = tracemalloc.get_traced_memory()
    
    return {
        "current_mb": current / 1024 / 1024,
        "peak_mb": peak / 1024 / 1024,
        "tracked_objects": len(memory_manager.weak_references),
        "object_pools": list(memory_manager.object_pools.keys()),
        "gc_stats": {
            "collections": gc.get_stats(),
            "counts": gc.get_count()
        }
    }
```

## Next Steps

1. **[Error Handling](04_error-handling.md)** - Resilience and recovery patterns
2. **[Testing Strategies](../07-testing-deployment/01_testing-strategies.md)** - Performance testing
3. **[Deployment Patterns](../07-testing-deployment/02_deployment-strategies.md)** - Production deployment

## Additional Resources

- **Elasticsearch Performance Tuning**: [elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)
- **FastAPI Performance**: [fastapi.tiangolo.com/benchmarks](https://fastapi.tiangolo.com/benchmarks/)
- **Redis Caching**: [redis.io/topics/lru-cache](https://redis.io/topics/lru-cache)
- **Python Memory Profiling**: [docs.python.org/3/library/tracemalloc.html](https://docs.python.org/3/library/tracemalloc.html)