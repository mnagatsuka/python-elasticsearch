# Dependency Injection

Comprehensive guide to implementing FastAPI's dependency injection system for Elasticsearch connections, service layer architecture, and production-ready patterns.

## Table of Contents
- [FastAPI Dependency System Overview](#fastapi-dependency-system-overview)
- [Elasticsearch Connection Management](#elasticsearch-connection-management)
- [Service Layer Architecture](#service-layer-architecture)
- [Testing with Dependency Overrides](#testing-with-dependency-overrides)
- [Caching and Performance Optimization](#caching-and-performance-optimization)
- [Advanced Dependency Patterns](#advanced-dependency-patterns)
- [Production Configuration](#production-configuration)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Next Steps](#next-steps)

## FastAPI Dependency System Overview

### Basic Dependency Concepts

```python
from fastapi import FastAPI, Depends, HTTPException, status
from elasticsearch_dsl import AsyncSearch, connections
from elasticsearch_dsl.connections import AsyncElasticsearch
from typing import AsyncGenerator, Optional, Dict, Any
import logging
from contextlib import asynccontextmanager
import asyncio

logger = logging.getLogger(__name__)

app = FastAPI(title="Search API with Dependency Injection")

# Basic dependency functions
async def get_elasticsearch_client() -> AsyncElasticsearch:
    """Basic dependency to get Elasticsearch client"""
    try:
        client = connections.get_connection('default')
        return client
    except Exception as e:
        logger.error(f"Failed to get Elasticsearch client: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elasticsearch service unavailable"
        )

async def get_search_index(index_name: str = "products") -> str:
    """Dependency to provide index name with validation"""
    valid_indices = ["products", "categories", "users", "orders"]
    
    if index_name not in valid_indices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid index name. Valid indices: {valid_indices}"
        )
    
    return index_name

# Basic usage in endpoints
@app.get("/products/search")
async def basic_search(
    q: str,
    client: AsyncElasticsearch = Depends(get_elasticsearch_client),
    index: str = Depends(get_search_index)
):
    """Basic search endpoint using dependencies"""
    search = AsyncSearch(using=client, index=index)
    search = search.query('match', name=q)
    
    response = await search.execute()
    
    return {
        'total': response.hits.total.value,
        'results': [hit.to_dict() for hit in response.hits]
    }

# Dependency with parameters
def get_paginated_search(default_size: int = 10):
    """Dependency factory for pagination"""
    def paginated_search(
        page: int = 1,
        size: int = default_size
    ) -> Dict[str, int]:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be greater than 0"
            )
        
        if size < 1 or size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Size must be between 1 and 100"
            )
        
        return {
            'page': page,
            'size': size,
            'offset': (page - 1) * size
        }
    
    return paginated_search

@app.get("/products/paginated-search")
async def paginated_search(
    q: str,
    pagination: Dict[str, int] = Depends(get_paginated_search(default_size=20)),
    client: AsyncElasticsearch = Depends(get_elasticsearch_client)
):
    """Search endpoint with pagination dependency"""
    search = AsyncSearch(using=client, index='products')
    search = search.query('match', name=q)
    search = search[pagination['offset']:pagination['offset'] + pagination['size']]
    
    response = await search.execute()
    
    return {
        'page': pagination['page'],
        'size': pagination['size'],
        'total': response.hits.total.value,
        'results': [hit.to_dict() for hit in response.hits]
    }
```

## Elasticsearch Connection Management

### Connection Pool and Lifecycle Management

```python
from elasticsearch_dsl.connections import connections
from elasticsearch import AsyncElasticsearch
from typing import AsyncGenerator, Dict, Any, Optional
import ssl
import certifi
from urllib.parse import urlparse
import os

class ElasticsearchConfig:
    """Configuration for Elasticsearch connections"""
    
    def __init__(self):
        self.hosts = self._parse_hosts()
        self.auth = self._get_auth()
        self.ssl_config = self._get_ssl_config()
        self.connection_params = self._get_connection_params()
    
    def _parse_hosts(self) -> list:
        """Parse Elasticsearch hosts from environment"""
        hosts_str = os.getenv('ELASTICSEARCH_HOSTS', 'localhost:9200')
        hosts = []
        
        for host_str in hosts_str.split(','):
            host_str = host_str.strip()
            if '://' not in host_str:
                host_str = f'http://{host_str}'
            
            parsed = urlparse(host_str)
            host_config = {
                'host': parsed.hostname,
                'port': parsed.port or 9200,
                'use_ssl': parsed.scheme == 'https'
            }
            hosts.append(host_config)
        
        return hosts
    
    def _get_auth(self) -> Optional[tuple]:
        """Get authentication credentials"""
        username = os.getenv('ELASTICSEARCH_USERNAME')
        password = os.getenv('ELASTICSEARCH_PASSWORD')
        
        if username and password:
            return (username, password)
        
        return None
    
    def _get_ssl_config(self) -> Dict[str, Any]:
        """Get SSL configuration"""
        ssl_config = {}
        
        if os.getenv('ELASTICSEARCH_USE_SSL', 'false').lower() == 'true':
            ssl_config['use_ssl'] = True
            ssl_config['verify_certs'] = os.getenv('ELASTICSEARCH_VERIFY_SSL', 'true').lower() == 'true'
            
            # Use system CA bundle
            ssl_config['ca_certs'] = certifi.where()
            
            # Custom CA certificate
            ca_cert_path = os.getenv('ELASTICSEARCH_CA_CERT_PATH')
            if ca_cert_path and os.path.exists(ca_cert_path):
                ssl_config['ca_certs'] = ca_cert_path
        
        return ssl_config
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """Get additional connection parameters"""
        return {
            'timeout': int(os.getenv('ELASTICSEARCH_TIMEOUT', '30')),
            'max_retries': int(os.getenv('ELASTICSEARCH_MAX_RETRIES', '3')),
            'retry_on_timeout': True,
            'sniff_on_start': os.getenv('ELASTICSEARCH_SNIFF_ON_START', 'false').lower() == 'true',
            'sniff_on_connection_fail': os.getenv('ELASTICSEARCH_SNIFF_ON_FAIL', 'false').lower() == 'true',
            'sniffer_timeout': int(os.getenv('ELASTICSEARCH_SNIFFER_TIMEOUT', '10'))
        }

class ElasticsearchConnectionManager:
    """Manages Elasticsearch connections with proper lifecycle"""
    
    def __init__(self, config: ElasticsearchConfig):
        self.config = config
        self.client: Optional[AsyncElasticsearch] = None
        self.is_connected = False
    
    async def initialize(self) -> None:
        """Initialize Elasticsearch connection"""
        try:
            # Create client
            self.client = AsyncElasticsearch(
                hosts=self.config.hosts,
                http_auth=self.config.auth,
                **self.config.ssl_config,
                **self.config.connection_params
            )
            
            # Test connection
            info = await self.client.info()
            logger.info(f"Connected to Elasticsearch: {info['version']['number']}")
            
            # Configure elasticsearch-dsl connections
            connections.configure(
                default={'hosts': self.config.hosts, 'timeout': 30},
                async_default=self.client
            )
            
            self.is_connected = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Elasticsearch connection: {e}")
            self.is_connected = False
            raise
    
    async def close(self) -> None:
        """Close Elasticsearch connection"""
        if self.client:
            await self.client.close()
            self.client = None
            self.is_connected = False
            logger.info("Elasticsearch connection closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        if not self.client or not self.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Elasticsearch client not available"
            )
        
        try:
            cluster_health = await self.client.cluster.health()
            return {
                'status': cluster_health['status'],
                'cluster_name': cluster_health['cluster_name'],
                'number_of_nodes': cluster_health['number_of_nodes'],
                'active_primary_shards': cluster_health['active_primary_shards'],
                'active_shards': cluster_health['active_shards'],
                'relocating_shards': cluster_health['relocating_shards'],
                'initializing_shards': cluster_health['initializing_shards'],
                'unassigned_shards': cluster_health['unassigned_shards']
            }
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Elasticsearch health check failed: {str(e)}"
            )
    
    def get_client(self) -> AsyncElasticsearch:
        """Get Elasticsearch client"""
        if not self.client or not self.is_connected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Elasticsearch client not available"
            )
        return self.client

# Global connection manager
es_config = ElasticsearchConfig()
es_manager = ElasticsearchConnectionManager(es_config)

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting up application...")
    await es_manager.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await es_manager.close()

app = FastAPI(title="Search API", lifespan=lifespan)

# Connection dependencies
async def get_elasticsearch_client() -> AsyncElasticsearch:
    """Dependency to get Elasticsearch client"""
    return es_manager.get_client()

async def get_connection_manager() -> ElasticsearchConnectionManager:
    """Dependency to get connection manager"""
    return es_manager

@app.get("/health/elasticsearch")
async def elasticsearch_health(
    manager: ElasticsearchConnectionManager = Depends(get_connection_manager)
):
    """Elasticsearch health check endpoint"""
    return await manager.health_check()
```

## Service Layer Architecture

### Service-Oriented Dependency Injection

```python
from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, Generic, List, Optional, Dict, Any
from pydantic import BaseModel
from dataclasses import dataclass
import asyncio

# Service protocols and interfaces
class SearchService(Protocol):
    """Protocol for search services"""
    
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Perform search operation"""
        ...
    
    async def suggest(self, query: str, size: int = 10) -> List[str]:
        """Get search suggestions"""
        ...

class AnalyticsService(Protocol):
    """Protocol for analytics services"""
    
    async def track_search(
        self, 
        query: str, 
        results_count: int,
        user_id: Optional[str] = None
    ) -> None:
        """Track search event"""
        ...
    
    async def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular search queries"""
        ...

# Service implementations
class ElasticsearchSearchService:
    """Elasticsearch-based search service"""
    
    def __init__(self, client: AsyncElasticsearch, index: str):
        self.client = client
        self.index = index
    
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Perform Elasticsearch search"""
        search = AsyncSearch(using=self.client, index=self.index)
        
        # Add query
        search = search.query('multi_match', 
                            query=query,
                            fields=['name^3', 'description^2', 'category'])
        
        # Add filters
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    search = search.filter('terms', **{field: value})
                else:
                    search = search.filter('term', **{field: value})
        
        # Add pagination
        if pagination:
            offset = pagination.get('offset', 0)
            size = pagination.get('size', 10)
            search = search[offset:offset + size]
        
        # Execute search
        response = await search.execute()
        
        return {
            'total': response.hits.total.value,
            'results': [hit.to_dict() for hit in response.hits],
            'took_ms': response.took,
            'max_score': response.hits.max_score
        }
    
    async def suggest(self, query: str, size: int = 10) -> List[str]:
        """Get search suggestions using completion suggester"""
        suggest_body = {
            'suggest': {
                'product_suggest': {
                    'prefix': query,
                    'completion': {
                        'field': 'suggest',
                        'size': size
                    }
                }
            }
        }
        
        response = await self.client.search(
            index=self.index,
            body=suggest_body
        )
        
        suggestions = []
        for option in response['suggest']['product_suggest'][0]['options']:
            suggestions.append(option['text'])
        
        return suggestions

class RedisAnalyticsService:
    """Redis-based analytics service"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def track_search(
        self, 
        query: str, 
        results_count: int,
        user_id: Optional[str] = None
    ) -> None:
        """Track search event in Redis"""
        # Increment search query counter
        await self.redis.zincrby('popular_searches', 1, query)
        
        # Track user search if user_id provided
        if user_id:
            user_key = f'user_searches:{user_id}'
            await self.redis.zadd(user_key, {query: asyncio.get_event_loop().time()})
            
            # Expire user searches after 30 days
            await self.redis.expire(user_key, 30 * 24 * 3600)
        
        # Track search results count
        await self.redis.hset('search_results_stats', query, results_count)
    
    async def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular search queries from Redis"""
        popular = await self.redis.zrevrange('popular_searches', 0, limit - 1, withscores=True)
        
        return [
            {'query': query.decode(), 'count': int(count)}
            for query, count in popular
        ]

# Service configuration
@dataclass
class ServiceConfig:
    """Configuration for services"""
    search_index: str = "products"
    analytics_enabled: bool = True
    cache_ttl: int = 300
    max_suggestions: int = 10

# Service factory
class ServiceFactory:
    """Factory for creating services with dependencies"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
    
    def create_search_service(self, client: AsyncElasticsearch) -> SearchService:
        """Create search service"""
        return ElasticsearchSearchService(client, self.config.search_index)
    
    def create_analytics_service(self, redis_client) -> AnalyticsService:
        """Create analytics service"""
        return RedisAnalyticsService(redis_client)

# Service dependencies
service_config = ServiceConfig()
service_factory = ServiceFactory(service_config)

async def get_search_service(
    client: AsyncElasticsearch = Depends(get_elasticsearch_client)
) -> SearchService:
    """Dependency to get search service"""
    return service_factory.create_search_service(client)

async def get_analytics_service() -> AnalyticsService:
    """Dependency to get analytics service"""
    # In a real application, you would inject Redis client here
    import fakeredis.aioredis
    redis_client = fakeredis.aioredis.FakeRedis()
    return service_factory.create_analytics_service(redis_client)

# Composite service for complex operations
class CompositeSearchService:
    """Composite service combining search and analytics"""
    
    def __init__(
        self, 
        search_service: SearchService,
        analytics_service: AnalyticsService
    ):
        self.search_service = search_service
        self.analytics_service = analytics_service
    
    async def search_with_analytics(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform search and track analytics"""
        # Perform search
        search_results = await self.search_service.search(query, filters, pagination)
        
        # Track analytics
        await self.analytics_service.track_search(
            query,
            search_results['total'],
            user_id
        )
        
        return search_results
    
    async def search_with_suggestions(
        self,
        query: str,
        include_suggestions: bool = True
    ) -> Dict[str, Any]:
        """Perform search with suggestions"""
        # Perform search
        search_task = self.search_service.search(query)
        
        # Get suggestions if requested
        if include_suggestions:
            suggestions_task = self.search_service.suggest(query)
            search_results, suggestions = await asyncio.gather(search_task, suggestions_task)
            search_results['suggestions'] = suggestions
        else:
            search_results = await search_task
        
        return search_results

async def get_composite_search_service(
    search_service: SearchService = Depends(get_search_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> CompositeSearchService:
    """Dependency to get composite search service"""
    return CompositeSearchService(search_service, analytics_service)

# Service-based endpoints
@app.get("/products/service-search")
async def service_search(
    q: str,
    category: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    user_id: Optional[str] = None,
    composite_service: CompositeSearchService = Depends(get_composite_search_service)
):
    """Search endpoint using service layer"""
    filters = {'category': category} if category else None
    pagination = {'offset': (page - 1) * size, 'size': size}
    
    return await composite_service.search_with_analytics(
        query=q,
        filters=filters,
        pagination=pagination,
        user_id=user_id
    )

@app.get("/search/suggestions")
async def get_suggestions(
    q: str,
    search_service: SearchService = Depends(get_search_service)
):
    """Get search suggestions"""
    suggestions = await search_service.suggest(q)
    return {'suggestions': suggestions}

@app.get("/analytics/popular-searches")
async def get_popular_searches(
    limit: int = 10,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get popular search queries"""
    popular_searches = await analytics_service.get_popular_searches(limit)
    return {'popular_searches': popular_searches}
```

## Testing with Dependency Overrides

### Comprehensive Testing Strategy

```python
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List
import json

# Test doubles and mocks
class MockElasticsearchClient:
    """Mock Elasticsearch client for testing"""
    
    def __init__(self):
        self.search_responses = {}
        self.call_history = []
    
    def set_search_response(self, index: str, response: Dict[str, Any]):
        """Set mock response for search"""
        self.search_responses[index] = response
    
    async def search(self, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Mock search method"""
        self.call_history.append(('search', index, body))
        
        if index in self.search_responses:
            return self.search_responses[index]
        
        # Default response
        return {
            'took': 5,
            'hits': {
                'total': {'value': 0, 'relation': 'eq'},
                'max_score': None,
                'hits': []
            },
            'suggest': {
                'product_suggest': [{
                    'options': []
                }]
            }
        }
    
    async def info(self) -> Dict[str, Any]:
        """Mock info method"""
        return {
            'version': {'number': '8.0.0'},
            'cluster_name': 'test-cluster'
        }
    
    async def cluster_health(self) -> Dict[str, Any]:
        """Mock cluster health"""
        return {
            'status': 'green',
            'cluster_name': 'test-cluster',
            'number_of_nodes': 1,
            'active_primary_shards': 5,
            'active_shards': 5,
            'relocating_shards': 0,
            'initializing_shards': 0,
            'unassigned_shards': 0
        }
    
    async def close(self):
        """Mock close method"""
        pass

class MockSearchService:
    """Mock search service for testing"""
    
    def __init__(self):
        self.search_calls = []
        self.suggest_calls = []
        self.search_response = {
            'total': 10,
            'results': [
                {'id': '1', 'name': 'Test Product 1', 'price': 100},
                {'id': '2', 'name': 'Test Product 2', 'price': 200}
            ],
            'took_ms': 15,
            'max_score': 2.5
        }
        self.suggestions = ['test suggestion 1', 'test suggestion 2']
    
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Mock search method"""
        self.search_calls.append((query, filters, pagination))
        return self.search_response
    
    async def suggest(self, query: str, size: int = 10) -> List[str]:
        """Mock suggest method"""
        self.suggest_calls.append((query, size))
        return self.suggestions[:size]

class MockAnalyticsService:
    """Mock analytics service for testing"""
    
    def __init__(self):
        self.tracked_searches = []
        self.popular_searches = [
            {'query': 'laptop', 'count': 100},
            {'query': 'phone', 'count': 80},
            {'query': 'headphones', 'count': 60}
        ]
    
    async def track_search(
        self, 
        query: str, 
        results_count: int,
        user_id: Optional[str] = None
    ) -> None:
        """Mock track search method"""
        self.tracked_searches.append((query, results_count, user_id))
    
    async def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Mock get popular searches method"""
        return self.popular_searches[:limit]

# Test fixtures
@pytest.fixture
def mock_elasticsearch_client():
    """Fixture providing mock Elasticsearch client"""
    return MockElasticsearchClient()

@pytest.fixture
def mock_search_service():
    """Fixture providing mock search service"""
    return MockSearchService()

@pytest.fixture
def mock_analytics_service():
    """Fixture providing mock analytics service"""
    return MockAnalyticsService()

@pytest.fixture
def test_app(mock_elasticsearch_client, mock_search_service, mock_analytics_service):
    """Fixture providing test FastAPI app with dependency overrides"""
    from your_app import app, get_elasticsearch_client, get_search_service, get_analytics_service
    
    # Override dependencies
    app.dependency_overrides[get_elasticsearch_client] = lambda: mock_elasticsearch_client
    app.dependency_overrides[get_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_analytics_service] = lambda: mock_analytics_service
    
    yield app
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture
def test_client(test_app):
    """Fixture providing test client"""
    return TestClient(test_app)

# Test cases
class TestSearchEndpoints:
    """Test cases for search endpoints"""
    
    def test_basic_search(self, test_client, mock_search_service):
        """Test basic search endpoint"""
        response = test_client.get("/products/search?q=laptop")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert 'total' in data
        assert 'results' in data
        
        # Verify service was called
        assert len(mock_search_service.search_calls) == 1
        assert mock_search_service.search_calls[0][0] == 'laptop'
    
    def test_search_with_filters(self, test_client, mock_search_service):
        """Test search with filters"""
        response = test_client.get("/products/search?q=laptop&category=electronics")
        
        assert response.status_code == 200
        
        # Verify filters were passed to service
        call_args = mock_search_service.search_calls[0]
        assert call_args[1] == {'category': 'electronics'}
    
    def test_search_with_pagination(self, test_client, mock_search_service):
        """Test search with pagination"""
        response = test_client.get("/products/search?q=laptop&page=2&size=20")
        
        assert response.status_code == 200
        
        # Verify pagination was passed to service
        call_args = mock_search_service.search_calls[0]
        expected_pagination = {'offset': 20, 'size': 20}
        assert call_args[2] == expected_pagination
    
    def test_search_analytics_tracking(self, test_client, mock_analytics_service):
        """Test search analytics tracking"""
        response = test_client.get("/products/service-search?q=laptop&user_id=user123")
        
        assert response.status_code == 200
        
        # Verify analytics tracking
        assert len(mock_analytics_service.tracked_searches) == 1
        tracked_call = mock_analytics_service.tracked_searches[0]
        assert tracked_call[0] == 'laptop'  # query
        assert tracked_call[2] == 'user123'  # user_id
    
    def test_suggestions_endpoint(self, test_client, mock_search_service):
        """Test suggestions endpoint"""
        response = test_client.get("/search/suggestions?q=lap")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'suggestions' in data
        assert len(data['suggestions']) == 2
        
        # Verify service was called
        assert len(mock_search_service.suggest_calls) == 1
        assert mock_search_service.suggest_calls[0][0] == 'lap'
    
    def test_popular_searches(self, test_client, mock_analytics_service):
        """Test popular searches endpoint"""
        response = test_client.get("/analytics/popular-searches?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'popular_searches' in data
        assert len(data['popular_searches']) <= 5

class TestDependencyInjection:
    """Test dependency injection behavior"""
    
    def test_elasticsearch_client_dependency(self, mock_elasticsearch_client):
        """Test Elasticsearch client dependency"""
        # Test that the mock client is properly injected
        assert mock_elasticsearch_client is not None
        
        # Test client methods
        asyncio.run(self._test_client_methods(mock_elasticsearch_client))
    
    async def _test_client_methods(self, client):
        """Test mock client methods"""
        # Test info method
        info = await client.info()
        assert info['version']['number'] == '8.0.0'
        
        # Test search method
        client.set_search_response('products', {
            'hits': {
                'total': {'value': 1},
                'hits': [{'_source': {'name': 'Test Product'}}]
            }
        })
        
        result = await client.search('products', {'query': {'match_all': {}}})
        assert result['hits']['total']['value'] == 1
    
    def test_service_dependency_override(self, test_app, mock_search_service):
        """Test service dependency override"""
        from your_app import get_search_service
        
        # Verify override is in place
        assert get_search_service in test_app.dependency_overrides
        
        # Test that calling the dependency returns our mock
        mock_service = test_app.dependency_overrides[get_search_service]()
        assert mock_service is mock_search_service

# Integration tests
class TestIntegration:
    """Integration tests with multiple dependencies"""
    
    @pytest.mark.asyncio
    async def test_composite_service_integration(
        self, 
        mock_search_service, 
        mock_analytics_service
    ):
        """Test composite service with multiple dependencies"""
        composite_service = CompositeSearchService(
            mock_search_service, 
            mock_analytics_service
        )
        
        # Test search with analytics
        result = await composite_service.search_with_analytics(
            query='laptop',
            user_id='user123'
        )
        
        # Verify search was performed
        assert len(mock_search_service.search_calls) == 1
        assert result['total'] == 10
        
        # Verify analytics tracking
        assert len(mock_analytics_service.tracked_searches) == 1
        tracked = mock_analytics_service.tracked_searches[0]
        assert tracked[0] == 'laptop'
        assert tracked[1] == 10  # results count
        assert tracked[2] == 'user123'
    
    @pytest.mark.asyncio
    async def test_search_with_suggestions_integration(
        self, 
        mock_search_service
    ):
        """Test search with suggestions"""
        composite_service = CompositeSearchService(
            mock_search_service, 
            MockAnalyticsService()
        )
        
        result = await composite_service.search_with_suggestions(
            query='laptop',
            include_suggestions=True
        )
        
        # Verify both search and suggestions were called
        assert len(mock_search_service.search_calls) == 1
        assert len(mock_search_service.suggest_calls) == 1
        
        # Verify response includes suggestions
        assert 'suggestions' in result
        assert len(result['suggestions']) == 2

# Performance tests
class TestPerformance:
    """Performance tests for dependency injection"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_client):
        """Test concurrent requests with dependency injection"""
        import aiohttp
        import asyncio
        
        async def make_request(session, url):
            async with session.get(url) as response:
                return await response.json()
        
        async with aiohttp.ClientSession() as session:
            # Make multiple concurrent requests
            tasks = [
                make_request(session, "http://testserver/products/search?q=laptop")
                for _ in range(10)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all requests succeeded
            for result in results:
                assert 'total' in result
                assert 'results' in result

# Test configuration
class TestConfig:
    """Test configuration and setup"""
    
    def test_service_config(self):
        """Test service configuration"""
        config = ServiceConfig(
            search_index='test_products',
            analytics_enabled=False,
            cache_ttl=600
        )
        
        assert config.search_index == 'test_products'
        assert config.analytics_enabled is False
        assert config.cache_ttl == 600
    
    def test_service_factory(self, mock_elasticsearch_client):
        """Test service factory"""
        config = ServiceConfig()
        factory = ServiceFactory(config)
        
        search_service = factory.create_search_service(mock_elasticsearch_client)
        assert isinstance(search_service, ElasticsearchSearchService)
        assert search_service.client is mock_elasticsearch_client
        assert search_service.index == config.search_index

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Caching and Performance Optimization

### Advanced Caching with Dependencies

```python
import asyncio
import hashlib
import json
import time
from functools import wraps
from typing import Any, Dict, Optional, Callable
import redis.asyncio as redis
from dataclasses import dataclass

@dataclass
class CacheConfig:
    """Configuration for caching"""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 300  # 5 minutes
    key_prefix: str = "search_api"
    max_key_length: int = 250

class CacheManager:
    """Redis-based cache manager"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = redis.from_url(self.config.redis_url)
        # Test connection
        await self.redis.ping()
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        # Create deterministic key from arguments
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_json.encode()).hexdigest()
        
        cache_key = f"{self.config.key_prefix}:{prefix}:{key_hash}"
        
        # Ensure key length doesn't exceed Redis limits
        if len(cache_key) > self.config.max_key_length:
            cache_key = f"{self.config.key_prefix}:{prefix}:{hashlib.sha256(key_json.encode()).hexdigest()}"
        
        return cache_key
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
        
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis:
            return False
        
        try:
            ttl = ttl or self.config.default_ttl
            serialized_value = json.dumps(value, default=str)
            await self.redis.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return await self.redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
        
        return 0

# Global cache manager
cache_config = CacheConfig()
cache_manager = CacheManager(cache_config)

# Cache decorators
def cached_function(ttl: Optional[int] = None, cache_prefix: str = "func"):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager._generate_cache_key(
                f"{cache_prefix}:{func.__name__}", 
                *args, 
                **kwargs
            )
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Cached services
class CachedSearchService:
    """Search service with caching"""
    
    def __init__(self, base_service: SearchService, cache_manager: CacheManager):
        self.base_service = base_service
        self.cache_manager = cache_manager
    
    @cached_function(ttl=300, cache_prefix="search")
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Cached search method"""
        return await self.base_service.search(query, filters, pagination)
    
    @cached_function(ttl=600, cache_prefix="suggest")
    async def suggest(self, query: str, size: int = 10) -> List[str]:
        """Cached suggest method"""
        return await self.base_service.suggest(query, size)
    
    async def invalidate_search_cache(self, query: Optional[str] = None):
        """Invalidate search cache"""
        if query:
            # Invalidate specific query cache
            cache_key = self.cache_manager._generate_cache_key(
                "search:search", 
                query
            )
            await self.cache_manager.redis.delete(cache_key)
        else:
            # Invalidate all search cache
            pattern = f"{self.cache_manager.config.key_prefix}:search:*"
            await self.cache_manager.invalidate_pattern(pattern)

# Performance monitoring
class PerformanceMonitor:
    """Monitor performance of dependencies"""
    
    def __init__(self):
        self.metrics = {}
    
    def track_execution_time(self, operation: str):
        """Decorator to track execution time"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise
                finally:
                    end_time = time.time()
                    execution_time = end_time - start_time
                    
                    self._record_metric(operation, execution_time, success)
                
                return result
            
            return wrapper
        return decorator
    
    def _record_metric(self, operation: str, execution_time: float, success: bool):
        """Record performance metric"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                'total_calls': 0,
                'successful_calls': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0
            }
        
        metric = self.metrics[operation]
        metric['total_calls'] += 1
        
        if success:
            metric['successful_calls'] += 1
        
        metric['total_time'] += execution_time
        metric['min_time'] = min(metric['min_time'], execution_time)
        metric['max_time'] = max(metric['max_time'], execution_time)
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics"""
        result = {}
        
        for operation, metric in self.metrics.items():
            avg_time = metric['total_time'] / metric['total_calls'] if metric['total_calls'] > 0 else 0
            success_rate = metric['successful_calls'] / metric['total_calls'] if metric['total_calls'] > 0 else 0
            
            result[operation] = {
                'total_calls': metric['total_calls'],
                'successful_calls': metric['successful_calls'],
                'success_rate': success_rate,
                'avg_execution_time': avg_time,
                'min_execution_time': metric['min_time'],
                'max_execution_time': metric['max_time'],
                'total_execution_time': metric['total_time']
            }
        
        return result

# Global performance monitor
perf_monitor = PerformanceMonitor()

# Performance-optimized services
class OptimizedSearchService(ElasticsearchSearchService):
    """Search service with performance optimizations"""
    
    @perf_monitor.track_execution_time("elasticsearch_search")
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Optimized search with performance tracking"""
        return await super().search(query, filters, pagination)
    
    @perf_monitor.track_execution_time("elasticsearch_suggest")
    async def suggest(self, query: str, size: int = 10) -> List[str]:
        """Optimized suggest with performance tracking"""
        return await super().suggest(query, size)

# Dependencies with caching
async def get_cache_manager() -> CacheManager:
    """Dependency to get cache manager"""
    return cache_manager

async def get_cached_search_service(
    base_service: SearchService = Depends(get_search_service),
    cache_mgr: CacheManager = Depends(get_cache_manager)
) -> CachedSearchService:
    """Dependency to get cached search service"""
    return CachedSearchService(base_service, cache_mgr)

async def get_performance_monitor() -> PerformanceMonitor:
    """Dependency to get performance monitor"""
    return perf_monitor

# Connection pooling
class ConnectionPool:
    """Connection pool for Elasticsearch clients"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pool = asyncio.Queue(maxsize=max_connections)
        self.created_connections = 0
    
    async def get_connection(self) -> AsyncElasticsearch:
        """Get connection from pool"""
        try:
            # Try to get existing connection
            client = self.pool.get_nowait()
            return client
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            if self.created_connections < self.max_connections:
                client = self._create_connection()
                self.created_connections += 1
                return client
            else:
                # Wait for available connection
                return await self.pool.get()
    
    async def return_connection(self, client: AsyncElasticsearch):
        """Return connection to pool"""
        try:
            self.pool.put_nowait(client)
        except asyncio.QueueFull:
            # Pool is full, close connection
            await client.close()
            self.created_connections -= 1
    
    def _create_connection(self) -> AsyncElasticsearch:
        """Create new Elasticsearch connection"""
        return AsyncElasticsearch(
            hosts=es_config.hosts,
            http_auth=es_config.auth,
            **es_config.ssl_config,
            **es_config.connection_params
        )
    
    async def close_all(self):
        """Close all connections"""
        while not self.pool.empty():
            client = await self.pool.get()
            await client.close()
        self.created_connections = 0

# Global connection pool
connection_pool = ConnectionPool()

@asynccontextmanager
async def get_pooled_elasticsearch_client():
    """Context manager for pooled Elasticsearch client"""
    client = await connection_pool.get_connection()
    try:
        yield client
    finally:
        await connection_pool.return_connection(client)

# Optimized endpoints
@app.get("/products/cached-search")
async def cached_search(
    q: str,
    category: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    cached_service: CachedSearchService = Depends(get_cached_search_service)
):
    """Cached search endpoint"""
    filters = {'category': category} if category else None
    pagination = {'offset': (page - 1) * size, 'size': size}
    
    return await cached_service.search(q, filters, pagination)

@app.delete("/cache/search")
async def invalidate_search_cache(
    query: Optional[str] = None,
    cached_service: CachedSearchService = Depends(get_cached_search_service)
):
    """Invalidate search cache"""
    await cached_service.invalidate_search_cache(query)
    return {"message": "Cache invalidated successfully"}

@app.get("/metrics/performance")
async def get_performance_metrics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """Get performance metrics"""
    return monitor.get_metrics()
```

## Advanced Dependency Patterns

### Complex Dependency Scenarios

```python
from typing import Annotated, Union, Literal
from fastapi import Depends, Header, Query, HTTPException, BackgroundTasks
from functools import partial
from dataclasses import dataclass
from enum import Enum

# Advanced dependency types
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class SearchMode(str, Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    AI_POWERED = "ai_powered"

@dataclass
class UserContext:
    """User context for requests"""
    user_id: Optional[str]
    role: UserRole
    permissions: List[str]
    preferences: Dict[str, Any]

@dataclass
class SearchContext:
    """Search context for requests"""
    mode: SearchMode
    index: str
    user_context: UserContext
    features: List[str]

# Advanced dependency functions
async def get_user_context(
    user_id: Annotated[Optional[str], Header(alias="X-User-ID")] = None,
    user_role: Annotated[Optional[str], Header(alias="X-User-Role")] = None,
    api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None
) -> UserContext:
    """Get user context from headers"""
    
    if api_key:
        # Validate API key and get user info
        user_info = await validate_api_key(api_key)
        return UserContext(
            user_id=user_info['user_id'],
            role=UserRole(user_info['role']),
            permissions=user_info['permissions'],
            preferences=user_info['preferences']
        )
    
    # Default context for unauthenticated users
    return UserContext(
        user_id=user_id,
        role=UserRole(user_role) if user_role else UserRole.GUEST,
        permissions=[],
        preferences={}
    )

async def get_search_context(
    search_mode: SearchMode = Query(SearchMode.BASIC),
    index: str = Query("products"),
    user_context: UserContext = Depends(get_user_context)
) -> SearchContext:
    """Get search context with user permissions"""
    
    # Validate user permissions for search mode
    if search_mode == SearchMode.AI_POWERED:
        if "ai_search" not in user_context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="AI-powered search requires special permissions"
            )
    
    # Determine available features based on user role
    features = ["basic_search"]
    
    if user_context.role in [UserRole.USER, UserRole.ADMIN]:
        features.extend(["advanced_filters", "saved_searches"])
    
    if user_context.role == UserRole.ADMIN:
        features.extend(["analytics", "admin_search"])
    
    return SearchContext(
        mode=search_mode,
        index=index,
        user_context=user_context,
        features=features
    )

# Conditional dependencies
def create_search_service_dependency(search_mode: SearchMode):
    """Create search service dependency based on mode"""
    
    async def get_mode_specific_service(
        base_service: SearchService = Depends(get_search_service),
        user_context: UserContext = Depends(get_user_context)
    ) -> SearchService:
        
        if search_mode == SearchMode.BASIC:
            return base_service
        elif search_mode == SearchMode.ADVANCED:
            return AdvancedSearchService(base_service, user_context)
        elif search_mode == SearchMode.AI_POWERED:
            return AISearchService(base_service, user_context)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported search mode: {search_mode}"
            )
    
    return get_mode_specific_service

# Factory pattern for dependencies
class DependencyFactory:
    """Factory for creating dependencies"""
    
    @staticmethod
    def create_search_service_provider(
        service_type: str,
        **kwargs
    ) -> Callable[[], SearchService]:
        """Create search service provider"""
        
        async def provider(
            client: AsyncElasticsearch = Depends(get_elasticsearch_client)
        ) -> SearchService:
            
            if service_type == "elasticsearch":
                return ElasticsearchSearchService(client, **kwargs)
            elif service_type == "cached":
                base_service = ElasticsearchSearchService(client, **kwargs)
                return CachedSearchService(base_service, cache_manager)
            elif service_type == "optimized":
                return OptimizedSearchService(client, **kwargs)
            else:
                raise ValueError(f"Unknown service type: {service_type}")
        
        return provider
    
    @staticmethod
    def create_conditional_dependency(
        condition_header: str,
        true_dependency: Callable,
        false_dependency: Callable
    ) -> Callable:
        """Create conditional dependency based on header"""
        
        async def conditional_dep(
            condition_value: Optional[str] = Header(None, alias=condition_header)
        ):
            if condition_value and condition_value.lower() == "true":
                return await true_dependency()
            else:
                return await false_dependency()
        
        return conditional_dep

# Background task dependencies
class BackgroundTaskManager:
    """Manages background tasks"""
    
    def __init__(self):
        self.tasks = []
    
    def add_task(self, func: Callable, *args, **kwargs):
        """Add background task"""
        self.tasks.append((func, args, kwargs))
    
    async def execute_tasks(self):
        """Execute all background tasks"""
        for func, args, kwargs in self.tasks:
            try:
                if asyncio.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Background task failed: {e}")
        
        self.tasks.clear()

async def get_background_task_manager() -> BackgroundTaskManager:
    """Dependency for background task manager"""
    return BackgroundTaskManager()

# Complex endpoint with multiple dependencies
@app.get("/products/advanced-search")
async def advanced_search(
    q: str,
    category: Optional[str] = None,
    price_range: Optional[str] = None,
    sort_by: str = "relevance",
    
    # Context dependencies
    search_context: SearchContext = Depends(get_search_context),
    
    # Service dependencies
    search_service: SearchService = Depends(get_search_service),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    
    # Utility dependencies
    background_tasks: BackgroundTasks,
    task_manager: BackgroundTaskManager = Depends(get_background_task_manager),
    
    # Monitoring dependencies
    perf_monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """Advanced search endpoint with complex dependencies"""
    
    # Validate permissions
    if "advanced_search" not in search_context.features:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Advanced search not available for your user level"
        )
    
    # Parse price range
    price_filter = None
    if price_range:
        try:
            min_price, max_price = map(float, price_range.split('-'))
            price_filter = {'min': min_price, 'max': max_price}
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid price range format. Use 'min-max'"
            )
    
    # Build filters
    filters = {}
    if category:
        filters['category'] = category
    if price_filter:
        filters['price'] = price_filter
    
    # Perform search
    start_time = time.time()
    search_results = await search_service.search(
        query=q,
        filters=filters
    )
    search_time = time.time() - start_time
    
    # Add background tasks
    task_manager.add_task(
        analytics_service.track_search,
        q,
        search_results['total'],
        search_context.user_context.user_id
    )
    
    if search_context.user_context.user_id:
        task_manager.add_task(
            update_user_search_history,
            search_context.user_context.user_id,
            q,
            search_results['total']
        )
    
    # Execute background tasks
    background_tasks.add_task(task_manager.execute_tasks)
    
    # Add performance info for admin users
    response = {
        'results': search_results['results'],
        'total': search_results['total'],
        'took_ms': search_results['took_ms']
    }
    
    if search_context.user_context.role == UserRole.ADMIN:
        response['debug'] = {
            'search_time': search_time,
            'user_context': search_context.user_context.__dict__,
            'search_context': {
                'mode': search_context.mode,
                'features': search_context.features
            }
        }
    
    return response

# Dependency classes for complex scenarios
class SearchServiceProvider:
    """Advanced search service provider"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.service_cache = {}
    
    async def get_service(
        self,
        search_context: SearchContext,
        client: AsyncElasticsearch
    ) -> SearchService:
        """Get service based on context"""
        
        cache_key = f"{search_context.mode}_{search_context.index}_{search_context.user_context.role}"
        
        if cache_key in self.service_cache:
            return self.service_cache[cache_key]
        
        # Create appropriate service
        if search_context.mode == SearchMode.BASIC:
            service = ElasticsearchSearchService(client, search_context.index)
        elif search_context.mode == SearchMode.ADVANCED:
            service = AdvancedSearchService(client, search_context.index)
        elif search_context.mode == SearchMode.AI_POWERED:
            service = AISearchService(client, search_context.index)
        
        # Wrap with caching if enabled
        if self.config.get('enable_cache', True):
            service = CachedSearchService(service, cache_manager)
        
        # Cache service instance
        self.service_cache[cache_key] = service
        
        return service

# Global service provider
search_service_provider = SearchServiceProvider({
    'enable_cache': True,
    'cache_ttl': 300
})

async def get_contextual_search_service(
    search_context: SearchContext = Depends(get_search_context),
    client: AsyncElasticsearch = Depends(get_elasticsearch_client)
) -> SearchService:
    """Get search service based on context"""
    return await search_service_provider.get_service(search_context, client)

# Placeholder functions
async def validate_api_key(api_key: str) -> Dict[str, Any]:
    """Validate API key and return user info"""
    # Placeholder implementation
    return {
        'user_id': 'user123',
        'role': 'user',
        'permissions': ['basic_search', 'advanced_filters'],
        'preferences': {}
    }

async def update_user_search_history(user_id: str, query: str, results_count: int):
    """Update user search history"""
    # Placeholder implementation
    pass

class AdvancedSearchService(ElasticsearchSearchService):
    """Advanced search service with enhanced features"""
    
    def __init__(self, client: AsyncElasticsearch, index: str):
        super().__init__(client, index)

class AISearchService(ElasticsearchSearchService):
    """AI-powered search service"""
    
    def __init__(self, client: AsyncElasticsearch, index: str):
        super().__init__(client, index)
```

## Production Configuration

### Production-Ready Dependency Setup

```python
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # Elasticsearch settings
    elasticsearch_hosts: str = "localhost:9200"
    elasticsearch_username: Optional[str] = None
    elasticsearch_password: Optional[str] = None
    elasticsearch_use_ssl: bool = False
    elasticsearch_verify_ssl: bool = True
    elasticsearch_ca_cert_path: Optional[str] = None
    elasticsearch_timeout: int = 30
    elasticsearch_max_retries: int = 3
    elasticsearch_max_connections: int = 10
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    redis_max_connections: int = 10
    redis_retry_on_timeout: bool = True
    
    # Cache settings
    cache_enabled: bool = True
    cache_default_ttl: int = 300
    cache_max_key_length: int = 250
    
    # Application settings
    debug: bool = False
    log_level: str = "INFO"
    api_title: str = "Search API"
    api_version: str = "1.0.0"
    
    # Performance settings
    max_search_results: int = 1000
    default_search_size: int = 10
    max_search_timeout: int = 30
    
    # Security settings
    cors_origins: List[str] = ["*"]
    api_key_header: str = "X-API-Key"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()

# Production-ready dependency providers
class ProductionDependencyProvider:
    """Production dependency provider with proper error handling"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.es_manager: Optional[ElasticsearchConnectionManager] = None
        self.cache_manager: Optional[CacheManager] = None
        self.service_factory: Optional[ServiceFactory] = None
    
    async def initialize(self):
        """Initialize all dependencies"""
        try:
            # Initialize Elasticsearch
            es_config = ElasticsearchConfig()
            self.es_manager = ElasticsearchConnectionManager(es_config)
            await self.es_manager.initialize()
            
            # Initialize cache
            if self.settings.cache_enabled:
                cache_config = CacheConfig(
                    redis_url=self.settings.redis_url,
                    default_ttl=self.settings.cache_default_ttl
                )
                self.cache_manager = CacheManager(cache_config)
                await self.cache_manager.initialize()
            
            # Initialize service factory
            service_config = ServiceConfig(
                search_index="products",
                analytics_enabled=True,
                cache_ttl=self.settings.cache_default_ttl
            )
            self.service_factory = ServiceFactory(service_config)
            
            logger.info("All dependencies initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize dependencies: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown all dependencies"""
        try:
            if self.es_manager:
                await self.es_manager.close()
            
            if self.cache_manager:
                await self.cache_manager.close()
            
            logger.info("All dependencies shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_elasticsearch_client(self) -> AsyncElasticsearch:
        """Get Elasticsearch client"""
        if not self.es_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Elasticsearch not available"
            )
        return self.es_manager.get_client()
    
    def get_search_service(self) -> SearchService:
        """Get search service"""
        if not self.service_factory:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )
        
        client = self.get_elasticsearch_client()
        service = self.service_factory.create_search_service(client)
        
        # Wrap with caching if available
        if self.cache_manager:
            service = CachedSearchService(service, self.cache_manager)
        
        return service
    
    def get_analytics_service(self) -> AnalyticsService:
        """Get analytics service"""
        if not self.service_factory:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Analytics service not available"
            )
        
        # This would use actual Redis client in production
        import fakeredis.aioredis
        redis_client = fakeredis.aioredis.FakeRedis()
        return self.service_factory.create_analytics_service(redis_client)

# Global production provider
settings = get_settings()
production_provider = ProductionDependencyProvider(settings)

# Production dependency functions
async def get_production_elasticsearch_client() -> AsyncElasticsearch:
    """Production Elasticsearch client dependency"""
    return production_provider.get_elasticsearch_client()

async def get_production_search_service() -> SearchService:
    """Production search service dependency"""
    return production_provider.get_search_service()

async def get_production_analytics_service() -> AnalyticsService:
    """Production analytics service dependency"""
    return production_provider.get_analytics_service()

# Application factory
def create_app() -> FastAPI:
    """Create FastAPI app with production dependencies"""
    
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        debug=settings.debug
    )
    
    # Override dependencies for production
    app.dependency_overrides[get_elasticsearch_client] = get_production_elasticsearch_client
    app.dependency_overrides[get_search_service] = get_production_search_service
    app.dependency_overrides[get_analytics_service] = get_production_analytics_service
    
    # Add middleware
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Application lifecycle
    @app.on_event("startup")
    async def startup_event():
        await production_provider.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await production_provider.shutdown()
    
    return app

# Environment-specific configurations
class DevelopmentConfig(Settings):
    """Development configuration"""
    debug: bool = True
    log_level: str = "DEBUG"
    cache_enabled: bool = False
    elasticsearch_hosts: str = "localhost:9200"

class ProductionConfig(Settings):
    """Production configuration"""
    debug: bool = False
    log_level: str = "WARNING"
    cache_enabled: bool = True
    elasticsearch_max_connections: int = 50
    redis_max_connections: int = 50

class TestingConfig(Settings):
    """Testing configuration"""
    debug: bool = True
    log_level: str = "DEBUG"
    cache_enabled: bool = False
    elasticsearch_hosts: str = "localhost:9201"  # Test ES instance

def get_config_for_environment(env: str) -> Settings:
    """Get configuration for specific environment"""
    if env == "development":
        return DevelopmentConfig()
    elif env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return Settings()

# Configuration-based app creation
def create_app_for_environment(env: str = None) -> FastAPI:
    """Create app for specific environment"""
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")
    
    # Update global settings
    global settings, production_provider
    settings = get_config_for_environment(env)
    production_provider = ProductionDependencyProvider(settings)
    
    return create_app()
```

## Monitoring and Health Checks

### Comprehensive Health Monitoring

```python
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"

@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time_ms: float

@dataclass
class SystemHealth:
    """Overall system health"""
    status: HealthStatus
    checks: List[HealthCheck]
    timestamp: datetime
    version: str

class HealthMonitor:
    """Health monitoring for dependencies"""
    
    def __init__(self):
        self.checks = {}
        self.history = []
        self.max_history = 100
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check"""
        self.checks[name] = check_func
    
    async def run_check(self, name: str) -> HealthCheck:
        """Run individual health check"""
        if name not in self.checks:
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check '{name}' not found",
                details={},
                timestamp=datetime.utcnow(),
                response_time_ms=0.0
            )
        
        start_time = time.time()
        
        try:
            check_func = self.checks[name]
            result = await check_func()
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            if isinstance(result, dict):
                status = HealthStatus(result.get('status', 'healthy'))
                message = result.get('message', 'OK')
                details = result.get('details', {})
            else:
                status = HealthStatus.HEALTHY
                message = "OK"
                details = {'result': result}
            
            return HealthCheck(
                name=name,
                status=status,
                message=message,
                details=details,
                timestamp=datetime.utcnow(),
                response_time_ms=response_time
            )
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return HealthCheck(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                details={'error': str(e), 'type': type(e).__name__},
                timestamp=datetime.utcnow(),
                response_time_ms=response_time
            )
    
    async def run_all_checks(self) -> SystemHealth:
        """Run all registered health checks"""
        check_tasks = [
            self.run_check(name) 
            for name in self.checks.keys()
        ]
        
        check_results = await asyncio.gather(*check_tasks)
        
        # Determine overall status
        overall_status = HealthStatus.HEALTHY
        
        for check in check_results:
            if check.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
                break
            elif check.status == HealthStatus.DEGRADED:
                overall_status = HealthStatus.DEGRADED
        
        system_health = SystemHealth(
            status=overall_status,
            checks=check_results,
            timestamp=datetime.utcnow(),
            version=settings.api_version
        )
        
        # Store in history
        self.history.append(system_health)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        return system_health
    
    def get_history(self, hours: int = 24) -> List[SystemHealth]:
        """Get health check history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            health for health in self.history
            if health.timestamp >= cutoff_time
        ]

# Health check implementations
async def check_elasticsearch_health(
    manager: ElasticsearchConnectionManager = Depends(get_connection_manager)
) -> Dict[str, Any]:
    """Health check for Elasticsearch"""
    try:
        health_info = await manager.health_check()
        
        # Check cluster status
        cluster_status = health_info['status']
        
        if cluster_status == 'red':
            return {
                'status': 'unhealthy',
                'message': 'Elasticsearch cluster is red',
                'details': health_info
            }
        elif cluster_status == 'yellow':
            return {
                'status': 'degraded',
                'message': 'Elasticsearch cluster is yellow',
                'details': health_info
            }
        else:
            return {
                'status': 'healthy',
                'message': 'Elasticsearch cluster is healthy',
                'details': health_info
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Elasticsearch check failed: {str(e)}',
            'details': {'error': str(e)}
        }

async def check_redis_health(
    cache_mgr: CacheManager = Depends(get_cache_manager)
) -> Dict[str, Any]:
    """Health check for Redis"""
    try:
        if not cache_mgr.redis:
            return {
                'status': 'unhealthy',
                'message': 'Redis client not initialized',
                'details': {}
            }
        
        # Test Redis connection
        await cache_mgr.redis.ping()
        
        # Get Redis info
        info = await cache_mgr.redis.info()
        
        return {
            'status': 'healthy',
            'message': 'Redis is healthy',
            'details': {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'redis_version': info.get('redis_version', 'unknown')
            }
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Redis check failed: {str(e)}',
            'details': {'error': str(e)}
        }

async def check_search_service_health(
    search_service: SearchService = Depends(get_search_service)
) -> Dict[str, Any]:
    """Health check for search service"""
    try:
        # Perform a simple search to test service
        test_results = await search_service.search(
            query="test",
            pagination={'offset': 0, 'size': 1}
        )
        
        return {
            'status': 'healthy',
            'message': 'Search service is healthy',
            'details': {
                'test_query_took_ms': test_results.get('took_ms', 0),
                'total_documents': test_results.get('total', 0)
            }
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Search service check failed: {str(e)}',
            'details': {'error': str(e)}
        }

async def check_memory_usage() -> Dict[str, Any]:
    """Health check for memory usage"""
    try:
        import psutil
        
        # Get memory info
        memory = psutil.virtual_memory()
        
        # Consider unhealthy if memory usage > 90%
        if memory.percent > 90:
            status = 'unhealthy'
            message = f'High memory usage: {memory.percent}%'
        elif memory.percent > 80:
            status = 'degraded'
            message = f'Elevated memory usage: {memory.percent}%'
        else:
            status = 'healthy'
            message = f'Memory usage is normal: {memory.percent}%'
        
        return {
            'status': status,
            'message': message,
            'details': {
                'percent': memory.percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'total_gb': round(memory.total / (1024**3), 2)
            }
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Memory check failed: {str(e)}',
            'details': {'error': str(e)}
        }

# Global health monitor
health_monitor = HealthMonitor()

# Register health checks
health_monitor.register_check('elasticsearch', check_elasticsearch_health)
health_monitor.register_check('redis', check_redis_health)
health_monitor.register_check('search_service', check_search_service_health)
health_monitor.register_check('memory', check_memory_usage)

async def get_health_monitor() -> HealthMonitor:
    """Dependency to get health monitor"""
    return health_monitor

# Health check endpoints
@app.get("/health")
async def health_check(
    monitor: HealthMonitor = Depends(get_health_monitor)
):
    """Basic health check endpoint"""
    system_health = await monitor.run_all_checks()
    
    status_code = 200
    if system_health.status == HealthStatus.UNHEALTHY:
        status_code = 503
    elif system_health.status == HealthStatus.DEGRADED:
        status_code = 200  # Still returning 200 for degraded
    
    return Response(
        content=json.dumps(asdict(system_health), default=str),
        media_type="application/json",
        status_code=status_code
    )

@app.get("/health/detailed")
async def detailed_health_check(
    monitor: HealthMonitor = Depends(get_health_monitor)
):
    """Detailed health check with full information"""
    system_health = await monitor.run_all_checks()
    return asdict(system_health)

@app.get("/health/{check_name}")
async def individual_health_check(
    check_name: str,
    monitor: HealthMonitor = Depends(get_health_monitor)
):
    """Individual health check"""
    check_result = await monitor.run_check(check_name)
    
    status_code = 200
    if check_result.status == HealthStatus.UNHEALTHY:
        status_code = 503
    
    return Response(
        content=json.dumps(asdict(check_result), default=str),
        media_type="application/json",
        status_code=status_code
    )

@app.get("/health/history")
async def health_history(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    monitor: HealthMonitor = Depends(get_health_monitor)
):
    """Get health check history"""
    history = monitor.get_history(hours)
    return [asdict(health) for health in history]

@app.get("/metrics")
async def get_metrics(
    monitor: PerformanceMonitor = Depends(get_performance_monitor)
):
    """Get application metrics"""
    return monitor.get_metrics()
```

## Next Steps

1. **[Advanced Search](../04-advanced-search/01_complex-queries.md)** - Build sophisticated search features using dependency injection
2. **[Data Modeling](../05-data-modeling/01_document-relationships.md)** - Design complex data relationships with service layers
3. **[Testing](../07-testing-deployment/01_testing-strategies.md)** - Test your dependency injection patterns
4. **[Production Patterns](../06-production-patterns/01_performance-optimization.md)** - Optimize for production deployment

## Additional Resources

- **FastAPI Dependency Injection**: [fastapi.tiangolo.com/tutorial/dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- **Dependency Injection Patterns**: [python-dependency-injector.ets-labs.org](https://python-dependency-injector.ets-labs.org/)
- **Async Context Managers**: [docs.python.org/3/library/contextlib.html](https://docs.python.org/3/library/contextlib.html)
- **Connection Pooling**: [elasticsearch-py.readthedocs.io](https://elasticsearch-py.readthedocs.io/)