# Testing Strategies for FastAPI + Elasticsearch-DSL

## Table of Contents
- [Overview](#overview)
- [Testing Architecture](#testing-architecture)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [Async Test Patterns](#async-test-patterns)
- [Mocking Elasticsearch](#mocking-elasticsearch)
- [Test Fixtures](#test-fixtures)
- [Performance Testing](#performance-testing)
- [Best Practices](#best-practices)

## Overview

Comprehensive testing strategies for FastAPI applications using Elasticsearch-DSL, focusing on async patterns, proper mocking, and production-ready test suites.

### Testing Pyramid

```python
# Test configuration
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from elasticsearch_dsl import Document, Text, Date, Integer
from elasticsearch_dsl.connections import connections

# Test categories by scope
UNIT_TESTS = "unit"        # Fast, isolated, mocked dependencies
INTEGRATION_TESTS = "integration"  # Real Elasticsearch, isolated data
E2E_TESTS = "e2e"         # Full system, realistic scenarios
PERFORMANCE_TESTS = "performance"  # Load, stress, benchmark tests
```

### Test Environment Setup

```python
# conftest.py
import pytest
import asyncio
from typing import AsyncGenerator
from elasticsearch_dsl import Index
from app.core.config import get_settings
from app.core.elasticsearch import get_elasticsearch_client
from app.models.product import Product

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def es_client():
    """Elasticsearch client for integration tests."""
    settings = get_settings()
    client = await get_elasticsearch_client()
    yield client
    await client.close()

@pytest.fixture(scope="function")
async def clean_test_index(es_client):
    """Clean test index before and after each test."""
    test_index = "test_products"
    
    # Clean before test
    if await es_client.indices.exists(index=test_index):
        await es_client.indices.delete(index=test_index)
    
    yield test_index
    
    # Clean after test
    if await es_client.indices.exists(index=test_index):
        await es_client.indices.delete(index=test_index)
```

## Testing Architecture

### Test Structure Organization

```python
# tests/
# ├── unit/
# │   ├── test_models.py
# │   ├── test_services.py
# │   └── test_utils.py
# ├── integration/
# │   ├── test_api_endpoints.py
# │   ├── test_elasticsearch_ops.py
# │   └── test_search_functionality.py
# ├── e2e/
# │   ├── test_complete_workflows.py
# │   └── test_user_journeys.py
# ├── performance/
# │   ├── test_load_testing.py
# │   └── test_benchmark.py
# └── conftest.py

# Pytest markers configuration
pytest_markers = [
    "unit: Unit tests with mocked dependencies",
    "integration: Integration tests with real Elasticsearch",
    "e2e: End-to-end tests with full system",
    "performance: Performance and load tests",
    "slow: Tests that take more than 5 seconds"
]
```

### Test Database Management

```python
# tests/utils/database.py
from typing import List, Dict, Any
from elasticsearch_dsl import Index, Document

class TestDatabaseManager:
    """Manage test databases and indices."""
    
    def __init__(self, es_client, test_prefix: str = "test_"):
        self.es_client = es_client
        self.test_prefix = test_prefix
        self.created_indices: List[str] = []
    
    async def create_test_index(
        self, 
        base_name: str, 
        mapping: Dict[str, Any] = None
    ) -> str:
        """Create a test index with optional mapping."""
        index_name = f"{self.test_prefix}{base_name}"
        
        if await self.es_client.indices.exists(index=index_name):
            await self.es_client.indices.delete(index=index_name)
        
        index_body = {"settings": {"number_of_shards": 1, "number_of_replicas": 0}}
        if mapping:
            index_body["mappings"] = mapping
        
        await self.es_client.indices.create(index=index_name, body=index_body)
        self.created_indices.append(index_name)
        return index_name
    
    async def cleanup_all(self):
        """Clean up all created test indices."""
        for index_name in self.created_indices:
            if await self.es_client.indices.exists(index=index_name):
                await self.es_client.indices.delete(index=index_name)
        self.created_indices.clear()
    
    async def bulk_insert_test_data(
        self, 
        index_name: str, 
        documents: List[Dict[str, Any]]
    ):
        """Insert test data in bulk."""
        body = []
        for doc in documents:
            body.append({"index": {"_index": index_name}})
            body.append(doc)
        
        await self.es_client.bulk(body=body, refresh=True)
```

## Unit Testing

### Testing Document Models

```python
# tests/unit/test_models.py
import pytest
from datetime import datetime
from app.models.product import Product, Review
from app.models.user import User

class TestProductModel:
    """Unit tests for Product document model."""
    
    def test_product_creation(self):
        """Test product model instantiation."""
        product = Product(
            title="Test Product",
            description="A test product description",
            price=29.99,
            category="electronics",
            tags=["test", "electronics"],
            created_at=datetime.utcnow()
        )
        
        assert product.title == "Test Product"
        assert product.price == 29.99
        assert "test" in product.tags
        assert product.category == "electronics"
    
    def test_product_validation(self):
        """Test product model validation."""
        with pytest.raises(ValueError):
            Product(price=-10)  # Negative price should fail
        
        with pytest.raises(ValueError):
            Product(title="")  # Empty title should fail
    
    def test_product_search_methods(self):
        """Test product search-related methods."""
        product = Product(title="Gaming Laptop", category="electronics")
        
        # Test search score calculation
        search_terms = ["gaming", "laptop"]
        score = product.calculate_relevance_score(search_terms)
        assert score > 0
        
        # Test category matching
        assert product.matches_category("electronics")
        assert not product.matches_category("clothing")

class TestReviewModel:
    """Unit tests for Review document model."""
    
    def test_review_creation(self):
        """Test review model creation."""
        review = Review(
            product_id="prod_123",
            user_id="user_456",
            rating=4,
            comment="Great product!",
            created_at=datetime.utcnow()
        )
        
        assert review.rating == 4
        assert review.product_id == "prod_123"
        assert "Great" in review.comment
    
    def test_review_sentiment_analysis(self):
        """Test review sentiment analysis."""
        positive_review = Review(
            rating=5,
            comment="Absolutely love this product!"
        )
        
        negative_review = Review(
            rating=1,
            comment="Terrible quality, don't buy"
        )
        
        assert positive_review.get_sentiment() == "positive"
        assert negative_review.get_sentiment() == "negative"
```

### Testing Services with Mocks

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.product_service import ProductService
from app.services.search_service import SearchService

class TestProductService:
    """Unit tests for ProductService."""
    
    @pytest.fixture
    def mock_es_client(self):
        """Mock Elasticsearch client."""
        client = AsyncMock()
        client.index = AsyncMock()
        client.get = AsyncMock()
        client.update = AsyncMock()
        client.delete = AsyncMock()
        client.search = AsyncMock()
        return client
    
    @pytest.fixture
    def product_service(self, mock_es_client):
        """ProductService with mocked dependencies."""
        return ProductService(es_client=mock_es_client)
    
    async def test_create_product(self, product_service, mock_es_client):
        """Test product creation."""
        # Setup mock response
        mock_es_client.index.return_value = {
            "_id": "test_id_123",
            "_index": "products",
            "result": "created"
        }
        
        product_data = {
            "title": "Test Product",
            "price": 29.99,
            "category": "electronics"
        }
        
        result = await product_service.create_product(product_data)
        
        # Assertions
        assert result["id"] == "test_id_123"
        mock_es_client.index.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_es_client.index.call_args
        assert call_args[1]["index"] == "products"
        assert call_args[1]["body"]["title"] == "Test Product"
    
    async def test_update_product(self, product_service, mock_es_client):
        """Test product update."""
        mock_es_client.update.return_value = {
            "_id": "test_id_123",
            "result": "updated"
        }
        
        update_data = {"price": 39.99}
        result = await product_service.update_product("test_id_123", update_data)
        
        assert result["result"] == "updated"
        mock_es_client.update.assert_called_once()
    
    async def test_delete_product(self, product_service, mock_es_client):
        """Test product deletion."""
        mock_es_client.delete.return_value = {
            "_id": "test_id_123",
            "result": "deleted"
        }
        
        result = await product_service.delete_product("test_id_123")
        
        assert result["result"] == "deleted"
        mock_es_client.delete.assert_called_once_with(
            index="products",
            id="test_id_123"
        )

class TestSearchService:
    """Unit tests for SearchService."""
    
    @pytest.fixture
    def mock_es_client(self):
        """Mock Elasticsearch client for search tests."""
        client = AsyncMock()
        client.search = AsyncMock()
        return client
    
    @pytest.fixture
    def search_service(self, mock_es_client):
        """SearchService with mocked dependencies."""
        return SearchService(es_client=mock_es_client)
    
    async def test_basic_search(self, search_service, mock_es_client):
        """Test basic search functionality."""
        # Mock search response
        mock_response = {
            "hits": {
                "total": {"value": 2},
                "hits": [
                    {
                        "_id": "1",
                        "_source": {"title": "Gaming Laptop", "price": 999},
                        "_score": 1.5
                    },
                    {
                        "_id": "2",
                        "_source": {"title": "Gaming Mouse", "price": 29},
                        "_score": 1.2
                    }
                ]
            }
        }
        mock_es_client.search.return_value = mock_response
        
        results = await search_service.search("gaming")
        
        assert len(results["hits"]) == 2
        assert results["total"] == 2
        assert results["hits"][0]["title"] == "Gaming Laptop"
        
        # Verify search query construction
        search_call = mock_es_client.search.call_args
        query = search_call[1]["body"]["query"]
        assert "gaming" in str(query)
```

## Integration Testing

### API Endpoint Testing

```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.core.elasticsearch import get_elasticsearch_client

class TestProductAPI:
    """Integration tests for Product API endpoints."""
    
    @pytest.fixture
    async def async_client(self):
        """Async HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.mark.integration
    async def test_create_product_endpoint(
        self, 
        async_client: AsyncClient,
        clean_test_index
    ):
        """Test product creation endpoint."""
        product_data = {
            "title": "Integration Test Product",
            "description": "A product for integration testing",
            "price": 49.99,
            "category": "test",
            "tags": ["integration", "test"]
        }
        
        response = await async_client.post("/products/", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == product_data["title"]
        assert "id" in data
        
        # Verify product was actually created in Elasticsearch
        es_client = await get_elasticsearch_client()
        doc = await es_client.get(index="products", id=data["id"])
        assert doc["_source"]["title"] == product_data["title"]
    
    @pytest.mark.integration
    async def test_search_products_endpoint(
        self, 
        async_client: AsyncClient,
        clean_test_index
    ):
        """Test product search endpoint."""
        # Create test products first
        products = [
            {"title": "Gaming Laptop", "category": "electronics", "price": 999},
            {"title": "Gaming Mouse", "category": "electronics", "price": 29},
            {"title": "Office Chair", "category": "furniture", "price": 199}
        ]
        
        created_ids = []
        for product in products:
            response = await async_client.post("/products/", json=product)
            created_ids.append(response.json()["id"])
        
        # Test search
        search_response = await async_client.get(
            "/products/search",
            params={"q": "gaming", "category": "electronics"}
        )
        
        assert search_response.status_code == 200
        results = search_response.json()
        assert results["total"] == 2
        assert all("gaming" in hit["title"].lower() for hit in results["hits"])
    
    @pytest.mark.integration
    async def test_product_lifecycle(
        self, 
        async_client: AsyncClient,
        clean_test_index
    ):
        """Test complete product CRUD lifecycle."""
        # Create
        create_data = {
            "title": "Lifecycle Test Product",
            "price": 99.99,
            "category": "test"
        }
        
        create_response = await async_client.post("/products/", json=create_data)
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]
        
        # Read
        get_response = await async_client.get(f"/products/{product_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == create_data["title"]
        
        # Update
        update_data = {"price": 149.99}
        update_response = await async_client.patch(
            f"/products/{product_id}", 
            json=update_data
        )
        assert update_response.status_code == 200
        assert update_response.json()["price"] == 149.99
        
        # Delete
        delete_response = await async_client.delete(f"/products/{product_id}")
        assert delete_response.status_code == 204
        
        # Verify deletion
        get_after_delete = await async_client.get(f"/products/{product_id}")
        assert get_after_delete.status_code == 404
```

### Elasticsearch Operations Testing

```python
# tests/integration/test_elasticsearch_ops.py
import pytest
from datetime import datetime
from app.models.product import Product
from app.services.elasticsearch_service import ElasticsearchService

class TestElasticsearchOperations:
    """Integration tests for Elasticsearch operations."""
    
    @pytest.mark.integration
    async def test_document_indexing(self, es_client, clean_test_index):
        """Test document indexing and retrieval."""
        service = ElasticsearchService(es_client)
        
        # Index a document
        doc_data = {
            "title": "Test Product",
            "description": "Integration test document",
            "price": 29.99,
            "created_at": datetime.utcnow().isoformat()
        }
        
        doc_id = await service.index_document(clean_test_index, doc_data)
        assert doc_id is not None
        
        # Retrieve the document
        retrieved = await service.get_document(clean_test_index, doc_id)
        assert retrieved["title"] == doc_data["title"]
        assert retrieved["price"] == doc_data["price"]
    
    @pytest.mark.integration
    async def test_bulk_operations(self, es_client, clean_test_index):
        """Test bulk indexing operations."""
        service = ElasticsearchService(es_client)
        
        # Prepare bulk data
        documents = [
            {"title": f"Product {i}", "price": i * 10, "category": "test"}
            for i in range(1, 11)
        ]
        
        # Bulk index
        result = await service.bulk_index(clean_test_index, documents)
        assert result["errors"] is False
        assert len(result["items"]) == 10
        
        # Verify all documents were indexed
        search_result = await es_client.search(
            index=clean_test_index,
            body={"query": {"match_all": {}}}
        )
        assert search_result["hits"]["total"]["value"] == 10
    
    @pytest.mark.integration
    async def test_complex_query_execution(self, es_client, clean_test_index):
        """Test complex query execution."""
        service = ElasticsearchService(es_client)
        
        # Index test data
        test_products = [
            {"title": "Gaming Laptop Pro", "price": 1299, "category": "electronics", "tags": ["gaming", "laptop"]},
            {"title": "Gaming Mouse RGB", "price": 59, "category": "electronics", "tags": ["gaming", "mouse"]},
            {"title": "Office Laptop", "price": 699, "category": "electronics", "tags": ["office", "laptop"]},
            {"title": "Gaming Chair", "price": 299, "category": "furniture", "tags": ["gaming", "chair"]}
        ]
        
        for product in test_products:
            await service.index_document(clean_test_index, product)
        
        # Refresh index
        await es_client.indices.refresh(index=clean_test_index)
        
        # Complex query: gaming products under $300
        query = {
            "bool": {
                "must": [
                    {"match": {"tags": "gaming"}},
                    {"range": {"price": {"lte": 300}}}
                ]
            }
        }
        
        results = await service.search(clean_test_index, query)
        assert len(results["hits"]) == 2  # Gaming Mouse and Gaming Chair
        
        for hit in results["hits"]:
            assert "gaming" in hit["_source"]["tags"]
            assert hit["_source"]["price"] <= 300
```

## Async Test Patterns

### Testing Async Operations

```python
# tests/async_patterns/test_concurrent_operations.py
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.services.product_service import ProductService

class TestAsyncPatterns:
    """Test patterns for async operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_product_creation(self, product_service):
        """Test concurrent product creation."""
        async def create_product(index: int):
            return await product_service.create_product({
                "title": f"Concurrent Product {index}",
                "price": index * 10,
                "category": "test"
            })
        
        # Create 5 products concurrently
        tasks = [create_product(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all("id" in result for result in results)
        assert len(set(result["id"] for result in results)) == 5  # All unique IDs
    
    @pytest.mark.asyncio
    async def test_async_context_managers(self, es_client):
        """Test async context managers in services."""
        class AsyncProductManager:
            def __init__(self, es_client):
                self.es_client = es_client
                self.created_products = []
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                # Clean up created products
                for product_id in self.created_products:
                    try:
                        await self.es_client.delete(
                            index="products", 
                            id=product_id
                        )
                    except Exception:
                        pass
            
            async def create_product(self, data):
                result = await self.es_client.index(
                    index="products",
                    body=data
                )
                self.created_products.append(result["_id"])
                return result
        
        async with AsyncProductManager(es_client) as manager:
            result = await manager.create_product({
                "title": "Context Manager Product",
                "price": 99.99
            })
            assert "_id" in result
        
        # Verify cleanup happened
        with pytest.raises(Exception):
            await es_client.get(index="products", id=result["_id"])
    
    @pytest.mark.asyncio
    async def test_async_generator_patterns(self, product_service):
        """Test async generator patterns for streaming results."""
        async def stream_products(category: str):
            """Async generator for streaming search results."""
            page_size = 2
            page = 0
            
            while True:
                results = await product_service.search_products(
                    category=category,
                    page=page,
                    size=page_size
                )
                
                if not results["hits"]:
                    break
                
                for hit in results["hits"]:
                    yield hit
                
                page += 1
        
        # Create test products
        for i in range(5):
            await product_service.create_product({
                "title": f"Stream Product {i}",
                "category": "streaming_test",
                "price": i * 10
            })
        
        # Stream results
        streamed_products = []
        async for product in stream_products("streaming_test"):
            streamed_products.append(product)
        
        assert len(streamed_products) == 5
```

## Mocking Elasticsearch

### Advanced Mocking Strategies

```python
# tests/mocks/elasticsearch_mock.py
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock

class ElasticsearchMockBuilder:
    """Builder for creating sophisticated Elasticsearch mocks."""
    
    def __init__(self):
        self.mock_data = {}
        self.mock_indices = set()
        self.mock_client = AsyncMock()
        self._setup_base_methods()
    
    def _setup_base_methods(self):
        """Setup base mock methods."""
        self.mock_client.index = AsyncMock(side_effect=self._mock_index)
        self.mock_client.get = AsyncMock(side_effect=self._mock_get)
        self.mock_client.search = AsyncMock(side_effect=self._mock_search)
        self.mock_client.delete = AsyncMock(side_effect=self._mock_delete)
        self.mock_client.update = AsyncMock(side_effect=self._mock_update)
        
        # Indices operations
        self.mock_client.indices = MagicMock()
        self.mock_client.indices.exists = AsyncMock(side_effect=self._mock_index_exists)
        self.mock_client.indices.create = AsyncMock(side_effect=self._mock_create_index)
        self.mock_client.indices.delete = AsyncMock(side_effect=self._mock_delete_index)
    
    def with_existing_documents(self, index: str, documents: List[Dict[str, Any]]):
        """Add existing documents to the mock."""
        if index not in self.mock_data:
            self.mock_data[index] = {}
            self.mock_indices.add(index)
        
        for i, doc in enumerate(documents):
            doc_id = doc.get("_id", f"mock_id_{i}")
            self.mock_data[index][doc_id] = doc
        
        return self
    
    def with_search_results(self, query_pattern: str, results: List[Dict[str, Any]]):
        """Configure search results for specific query patterns."""
        if not hasattr(self, "_search_patterns"):
            self._search_patterns = {}
        
        self._search_patterns[query_pattern] = results
        return self
    
    async def _mock_index(self, index: str, body: Dict[str, Any], id: str = None, **kwargs):
        """Mock document indexing."""
        if index not in self.mock_data:
            self.mock_data[index] = {}
            self.mock_indices.add(index)
        
        doc_id = id or f"mock_{len(self.mock_data[index])}"
        self.mock_data[index][doc_id] = body
        
        return {
            "_id": doc_id,
            "_index": index,
            "_version": 1,
            "result": "created"
        }
    
    async def _mock_get(self, index: str, id: str, **kwargs):
        """Mock document retrieval."""
        if index not in self.mock_data or id not in self.mock_data[index]:
            raise Exception(f"Document not found: {index}/{id}")
        
        return {
            "_id": id,
            "_index": index,
            "_source": self.mock_data[index][id],
            "found": True
        }
    
    async def _mock_search(self, index: str = None, body: Dict[str, Any] = None, **kwargs):
        """Mock search operations."""
        if hasattr(self, "_search_patterns"):
            query_str = str(body.get("query", {}))
            for pattern, results in self._search_patterns.items():
                if pattern in query_str:
                    return {
                        "hits": {
                            "total": {"value": len(results)},
                            "hits": [
                                {
                                    "_id": f"result_{i}",
                                    "_source": result,
                                    "_score": 1.0
                                }
                                for i, result in enumerate(results)
                            ]
                        }
                    }
        
        # Default: return all documents from index
        if index and index in self.mock_data:
            hits = [
                {
                    "_id": doc_id,
                    "_source": doc_data,
                    "_score": 1.0
                }
                for doc_id, doc_data in self.mock_data[index].items()
            ]
            
            return {
                "hits": {
                    "total": {"value": len(hits)},
                    "hits": hits
                }
            }
        
        return {"hits": {"total": {"value": 0}, "hits": []}}
    
    async def _mock_delete(self, index: str, id: str, **kwargs):
        """Mock document deletion."""
        if index in self.mock_data and id in self.mock_data[index]:
            del self.mock_data[index][id]
            return {"_id": id, "_index": index, "result": "deleted"}
        
        raise Exception(f"Document not found: {index}/{id}")
    
    async def _mock_update(self, index: str, id: str, body: Dict[str, Any], **kwargs):
        """Mock document update."""
        if index not in self.mock_data or id not in self.mock_data[index]:
            raise Exception(f"Document not found: {index}/{id}")
        
        if "doc" in body:
            self.mock_data[index][id].update(body["doc"])
        
        return {"_id": id, "_index": index, "result": "updated"}
    
    async def _mock_index_exists(self, index: str, **kwargs):
        """Mock index existence check."""
        return index in self.mock_indices
    
    async def _mock_create_index(self, index: str, **kwargs):
        """Mock index creation."""
        self.mock_indices.add(index)
        return {"acknowledged": True}
    
    async def _mock_delete_index(self, index: str, **kwargs):
        """Mock index deletion."""
        if index in self.mock_indices:
            self.mock_indices.remove(index)
            if index in self.mock_data:
                del self.mock_data[index]
        return {"acknowledged": True}
    
    def build(self):
        """Build the configured mock client."""
        return self.mock_client

# Usage in tests
@pytest.fixture
def mock_es_with_products():
    """Mock Elasticsearch client with pre-loaded products."""
    return (ElasticsearchMockBuilder()
        .with_existing_documents("products", [
            {"title": "Laptop", "price": 999, "category": "electronics"},
            {"title": "Mouse", "price": 29, "category": "electronics"},
            {"title": "Chair", "price": 199, "category": "furniture"}
        ])
        .with_search_results("electronics", [
            {"title": "Laptop", "price": 999, "category": "electronics"},
            {"title": "Mouse", "price": 29, "category": "electronics"}
        ])
        .build())
```

## Test Fixtures

### Data Fixtures and Factories

```python
# tests/fixtures/data_factories.py
import factory
from datetime import datetime, timedelta
from typing import Dict, Any, List
from faker import Faker

fake = Faker()

class ProductFactory(factory.Factory):
    """Factory for creating test product data."""
    
    class Meta:
        model = dict
    
    title = factory.LazyFunction(lambda: fake.catch_phrase())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    price = factory.LazyFunction(lambda: round(fake.random.uniform(10, 1000), 2))
    category = factory.LazyFunction(lambda: fake.random_element([
        "electronics", "clothing", "home", "sports", "books"
    ]))
    tags = factory.LazyFunction(lambda: fake.words(nb=3))
    created_at = factory.LazyFunction(lambda: datetime.utcnow().isoformat())
    
    @classmethod
    def gaming_product(cls, **kwargs) -> Dict[str, Any]:
        """Create a gaming-related product."""
        defaults = {
            "title": f"Gaming {fake.word().title()}",
            "category": "electronics",
            "tags": ["gaming", "electronics"],
            "price": round(fake.random.uniform(50, 500), 2)
        }
        defaults.update(kwargs)
        return cls(**defaults)
    
    @classmethod
    def bulk_products(cls, count: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple products for bulk operations."""
        return [cls(**kwargs) for _ in range(count)]

class ReviewFactory(factory.Factory):
    """Factory for creating test review data."""
    
    class Meta:
        model = dict
    
    product_id = factory.LazyFunction(lambda: f"prod_{fake.uuid4()}")
    user_id = factory.LazyFunction(lambda: f"user_{fake.uuid4()}")
    rating = factory.LazyFunction(lambda: fake.random_int(min=1, max=5))
    comment = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    helpful_votes = factory.LazyFunction(lambda: fake.random_int(min=0, max=100))
    created_at = factory.LazyFunction(lambda: datetime.utcnow().isoformat())

# Advanced fixtures
@pytest.fixture
def sample_products():
    """Sample products for testing."""
    return ProductFactory.bulk_products(10)

@pytest.fixture
def gaming_products():
    """Gaming-specific products."""
    return [
        ProductFactory.gaming_product(title="Gaming Laptop Pro"),
        ProductFactory.gaming_product(title="RGB Gaming Keyboard"),
        ProductFactory.gaming_product(title="Gaming Mouse Pad"),
    ]

@pytest.fixture
async def populated_test_index(es_client, clean_test_index, sample_products):
    """Test index populated with sample data."""
    # Index sample products
    for i, product in enumerate(sample_products):
        await es_client.index(
            index=clean_test_index,
            id=f"prod_{i}",
            body=product
        )
    
    # Refresh index to make documents searchable
    await es_client.indices.refresh(index=clean_test_index)
    
    return clean_test_index
```

## Performance Testing

### Load Testing and Benchmarks

```python
# tests/performance/test_load_testing.py
import pytest
import asyncio
import time
from typing import List, Dict, Any
from statistics import mean, median
from app.services.product_service import ProductService
from app.services.search_service import SearchService

class TestPerformance:
    """Performance and load testing."""
    
    @pytest.mark.performance
    async def test_concurrent_search_performance(
        self, 
        search_service: SearchService,
        populated_test_index
    ):
        """Test search performance under concurrent load."""
        search_terms = ["gaming", "laptop", "electronics", "wireless", "pro"]
        concurrent_requests = 50
        
        async def perform_search(term: str) -> Dict[str, Any]:
            start_time = time.time()
            result = await search_service.search(term)
            end_time = time.time()
            
            return {
                "term": term,
                "duration": end_time - start_time,
                "result_count": len(result.get("hits", []))
            }
        
        # Create concurrent search tasks
        tasks = []
        for _ in range(concurrent_requests):
            term = search_terms[_ % len(search_terms)]
            tasks.append(perform_search(term))
        
        # Execute all searches concurrently
        start_total = time.time()
        results = await asyncio.gather(*tasks)
        end_total = time.time()
        
        # Analyze performance
        durations = [r["duration"] for r in results]
        
        assert len(results) == concurrent_requests
        assert all(r["result_count"] >= 0 for r in results)
        
        # Performance assertions
        avg_duration = mean(durations)
        median_duration = median(durations)
        max_duration = max(durations)
        total_duration = end_total - start_total
        
        print(f"Performance Results:")
        print(f"  Total time: {total_duration:.2f}s")
        print(f"  Average search time: {avg_duration:.3f}s")
        print(f"  Median search time: {median_duration:.3f}s")
        print(f"  Max search time: {max_duration:.3f}s")
        print(f"  Requests per second: {concurrent_requests/total_duration:.1f}")
        
        # Performance thresholds
        assert avg_duration < 0.5, f"Average search time too high: {avg_duration:.3f}s"
        assert max_duration < 2.0, f"Max search time too high: {max_duration:.3f}s"
        assert total_duration < 10.0, f"Total execution time too high: {total_duration:.2f}s"
    
    @pytest.mark.performance
    async def test_bulk_indexing_performance(
        self, 
        product_service: ProductService,
        clean_test_index
    ):
        """Test bulk indexing performance."""
        batch_sizes = [100, 500, 1000]
        results = {}
        
        for batch_size in batch_sizes:
            # Generate test data
            products = ProductFactory.bulk_products(batch_size)
            
            # Measure bulk indexing time
            start_time = time.time()
            await product_service.bulk_create_products(products)
            end_time = time.time()
            
            duration = end_time - start_time
            throughput = batch_size / duration
            
            results[batch_size] = {
                "duration": duration,
                "throughput": throughput
            }
            
            print(f"Batch size {batch_size}: {duration:.2f}s, {throughput:.1f} docs/sec")
        
        # Performance assertions
        for batch_size, metrics in results.items():
            assert metrics["throughput"] > 50, f"Throughput too low for batch {batch_size}"
            assert metrics["duration"] < 30, f"Duration too high for batch {batch_size}"
    
    @pytest.mark.performance
    async def test_memory_usage_monitoring(self, product_service):
        """Test memory usage during operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        large_batch = ProductFactory.bulk_products(5000)
        await product_service.bulk_create_products(large_batch)
        
        # Search operations
        for _ in range(100):
            await product_service.search_products("test")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB")
        
        # Memory leak detection
        assert memory_increase < 100, f"Excessive memory usage: {memory_increase:.1f}MB"

class BenchmarkSuite:
    """Comprehensive benchmark suite."""
    
    @staticmethod
    async def run_search_benchmarks(search_service: SearchService) -> Dict[str, Any]:
        """Run comprehensive search benchmarks."""
        benchmarks = {}
        
        # Simple term search
        start = time.time()
        for _ in range(100):
            await search_service.search("laptop")
        benchmarks["simple_search"] = (time.time() - start) / 100
        
        # Complex query search
        start = time.time()
        for _ in range(50):
            await search_service.advanced_search(
                query="gaming laptop",
                filters={"category": "electronics", "price_range": [500, 1500]},
                sort=[{"price": "asc"}]
            )
        benchmarks["complex_search"] = (time.time() - start) / 50
        
        # Aggregation queries
        start = time.time()
        for _ in range(20):
            await search_service.get_aggregations(
                aggs=["category", "price_ranges", "avg_rating"]
            )
        benchmarks["aggregations"] = (time.time() - start) / 20
        
        return benchmarks
```

## Best Practices

### Testing Guidelines

```python
# Test organization best practices

# 1. Test naming conventions
class TestProductAPI:
    """Tests for Product API endpoints."""
    
    def test_create_product_success(self):
        """Test successful product creation."""
        pass
    
    def test_create_product_invalid_data(self):
        """Test product creation with invalid data."""
        pass
    
    def test_create_product_unauthorized(self):
        """Test product creation without authorization."""
        pass

# 2. Test data management
@pytest.fixture(scope="function")
def clean_test_environment():
    """Ensure clean test environment for each test."""
    # Setup
    yield
    # Teardown

# 3. Error case testing
async def test_elasticsearch_connection_failure():
    """Test behavior when Elasticsearch is unavailable."""
    with pytest.raises(ConnectionError):
        await product_service.create_product(test_data)

# 4. Performance test markers
@pytest.mark.slow
@pytest.mark.performance
@pytest.mark.integration
async def test_large_dataset_search():
    """Test search performance with large datasets."""
    pass

# 5. Parameterized tests
@pytest.mark.parametrize("category,expected_count", [
    ("electronics", 5),
    ("clothing", 3),
    ("books", 2),
])
async def test_category_filtering(category, expected_count):
    """Test category filtering with various categories."""
    pass
```

### Test Configuration

```python
# pytest.ini configuration
[tool:pytest]
minversion = 6.0
addopts = 
    -ra
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    slow: Tests that take more than 5 seconds

# Test environment variables
TEST_ELASTICSEARCH_URL = "http://localhost:9200"
TEST_DATABASE_URL = "elasticsearch://localhost:9200"
TEST_INDEX_PREFIX = "test_"
```

This comprehensive testing strategy ensures robust, maintainable, and performant FastAPI applications with Elasticsearch-DSL. The approach covers all testing levels from unit to performance testing, with practical examples and best practices for production deployment.