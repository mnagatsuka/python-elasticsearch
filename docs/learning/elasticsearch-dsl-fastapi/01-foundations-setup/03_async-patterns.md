# Async Patterns

Mastering async/await patterns with Elasticsearch-DSL for high-performance, non-blocking search applications.

## Table of Contents
- [Async/Await Fundamentals](#asyncawait-fundamentals)
- [Elasticsearch Async Operations](#elasticsearch-async-operations)
- [FastAPI Async Integration](#fastapi-async-integration)
- [Connection Management](#connection-management)
- [Error Handling Patterns](#error-handling-patterns)
- [Performance Optimization](#performance-optimization)
- [Common Pitfalls](#common-pitfalls)
- [Next Steps](#next-steps)

## Async/Await Fundamentals

### Understanding Async Programming
Async programming allows your application to handle multiple operations concurrently without blocking the main thread.

**Traditional Synchronous Approach:**
```python
import time

def slow_operation():
    time.sleep(1)  # Blocks entire application
    return "result"

def handle_requests():
    # Each request must wait for the previous one
    result1 = slow_operation()  # Takes 1 second
    result2 = slow_operation()  # Takes another 1 second
    result3 = slow_operation()  # Takes another 1 second
    # Total time: 3 seconds
    return [result1, result2, result3]
```

**Async Approach:**
```python
import asyncio

async def slow_operation():
    await asyncio.sleep(1)  # Non-blocking
    return "result"

async def handle_requests():
    # All requests can run concurrently
    tasks = [
        slow_operation(),
        slow_operation(),
        slow_operation()
    ]
    results = await asyncio.gather(*tasks)
    # Total time: ~1 second
    return results
```

### Python Async Concepts

**Coroutines:**
```python
async def my_coroutine():
    """A coroutine function - returns a coroutine object when called"""
    await asyncio.sleep(1)
    return "Hello"

# Usage
async def main():
    result = await my_coroutine()  # Await the coroutine
    print(result)
```

**Event Loop:**
```python
import asyncio

async def example():
    print("Start")
    await asyncio.sleep(1)
    print("End")

# Run with event loop
asyncio.run(example())

# Or in existing async context
await example()
```

## Elasticsearch Async Operations

### Async Document Operations
Elasticsearch-DSL provides async versions of all document operations.

```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Date
from datetime import datetime

class BlogPost(AsyncDocument):
    title = Text(analyzer='english')
    content = Text(analyzer='english')
    author = Keyword()
    published_date = Date()
    tags = Keyword(multi=True)
    
    class Index:
        name = 'blog_posts'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

# Create and save document
async def create_blog_post():
    post = BlogPost(
        title="Async Programming with FastAPI",
        content="This is a comprehensive guide...",
        author="john_doe",
        published_date=datetime.utcnow(),
        tags=["python", "fastapi", "async"]
    )
    
    # Async save operation
    await post.save()
    print(f"Post saved with ID: {post.meta.id}")
    return post

# Retrieve document
async def get_blog_post(post_id: str):
    try:
        post = await BlogPost.get(id=post_id)
        return post
    except NotFoundError:
        return None

# Update document
async def update_blog_post(post_id: str, new_title: str):
    post = await BlogPost.get(id=post_id)
    post.title = new_title
    await post.save()
    return post

# Delete document
async def delete_blog_post(post_id: str):
    post = await BlogPost.get(id=post_id)
    await post.delete()
```

### Async Search Operations
```python
from elasticsearch_dsl import AsyncSearch, Q

async def search_blog_posts(query: str, author: str = None):
    """Async search with dynamic filters"""
    search = AsyncSearch(index='blog_posts')
    
    # Add text query
    search = search.query('match', title=query)
    
    # Add optional filter
    if author:
        search = search.filter('term', author=author)
    
    # Execute async search
    response = await search.execute()
    
    return {
        'total': response.hits.total.value,
        'posts': [
            {
                'id': hit.meta.id,
                'title': hit.title,
                'author': hit.author,
                'score': hit.meta.score
            }
            for hit in response.hits
        ]
    }

# Complex query with multiple operations
async def advanced_search(text_query: str, tags: list = None):
    search = AsyncSearch(index='blog_posts')
    
    # Multi-field search
    search = search.query(
        'multi_match',
        query=text_query,
        fields=['title^2', 'content'],  # Boost title matches
        type='best_fields'
    )
    
    # Tag filtering
    if tags:
        tag_queries = [Q('term', tags=tag) for tag in tags]
        search = search.filter('bool', should=tag_queries, minimum_should_match=1)
    
    # Add aggregations
    search.aggs.bucket('authors', 'terms', field='author', size=10)
    search.aggs.bucket('publication_dates', 'date_histogram', 
                      field='published_date', 
                      calendar_interval='month')
    
    # Execute with pagination
    search = search[0:20]  # First 20 results
    response = await search.execute()
    
    return {
        'hits': [hit.to_dict() for hit in response.hits],
        'aggregations': {
            'authors': [
                {'key': bucket.key, 'count': bucket.doc_count}
                for bucket in response.aggregations.authors.buckets
            ],
            'publication_dates': [
                {'date': bucket.key_as_string, 'count': bucket.doc_count}
                for bucket in response.aggregations.publication_dates.buckets
            ]
        }
    }
```

### Bulk Operations
```python
from elasticsearch_dsl import AsyncDocument
from elasticsearch.helpers import async_bulk
from elasticsearch_dsl.connections import connections

async def bulk_index_posts(posts_data: list):
    """Efficiently index multiple documents"""
    
    # Prepare documents for bulk indexing
    documents = []
    for post_data in posts_data:
        post = BlogPost(**post_data)
        documents.append(post.to_dict(include_meta=True))
    
    # Async bulk operation
    client = connections.get_connection()
    success_count, failed_docs = await async_bulk(
        client,
        documents,
        index='blog_posts',
        chunk_size=100  # Process in chunks
    )
    
    return {
        'indexed': success_count,
        'failed': len(failed_docs) if failed_docs else 0
    }

async def bulk_update_posts(updates: list):
    """Bulk update multiple documents"""
    actions = []
    for update in updates:
        action = {
            '_op_type': 'update',
            '_index': 'blog_posts',
            '_id': update['id'],
            '_source': {'doc': update['changes']}
        }
        actions.append(action)
    
    client = connections.get_connection()
    success_count, failed_docs = await async_bulk(client, actions)
    
    return {'updated': success_count, 'failed': len(failed_docs) if failed_docs else 0}
```

## FastAPI Async Integration

### Async Route Handlers
```python
from fastapi import FastAPI, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

class SearchRequest(BaseModel):
    query: str
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    page: int = 1
    size: int = 10

class PostResponse(BaseModel):
    id: str
    title: str
    author: str
    score: float

@app.post("/search", response_model=List[PostResponse])
async def search_posts(request: SearchRequest):
    """Async search endpoint"""
    try:
        results = await search_blog_posts(
            query=request.query,
            author=request.author
        )
        
        return [
            PostResponse(
                id=post['id'],
                title=post['title'],
                author=post['author'],
                score=post['score']
            )
            for post in results['posts']
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/{post_id}")
async def get_post(post_id: str):
    """Async post retrieval"""
    post = await get_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return post.to_dict()
```

### Dependency Injection with Async
```python
from elasticsearch_dsl.connections import connections
from fastapi import Depends

async def get_elasticsearch_client():
    """Dependency for Elasticsearch client"""
    return connections.get_connection()

class SearchService:
    def __init__(self, client):
        self.client = client
    
    async def search_posts(self, query: str, filters: dict = None):
        search = AsyncSearch(using=self.client, index='blog_posts')
        search = search.query('match', title=query)
        
        if filters:
            for field, value in filters.items():
                search = search.filter('term', **{field: value})
        
        return await search.execute()

async def get_search_service(client = Depends(get_elasticsearch_client)):
    """Dependency for search service"""
    return SearchService(client)

@app.get("/search")
async def search_endpoint(
    q: str,
    author: str = None,
    search_service: SearchService = Depends(get_search_service)
):
    """Endpoint using dependency injection"""
    filters = {'author': author} if author else None
    results = await search_service.search_posts(q, filters)
    
    return {
        'total': results.hits.total.value,
        'hits': [hit.to_dict() for hit in results.hits]
    }
```

## Connection Management

### Async Connection Pool
```python
from elasticsearch_dsl.connections import connections
from contextlib import asynccontextmanager

class ElasticsearchManager:
    def __init__(self, host: str, port: int = 9200):
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"
    
    async def connect(self):
        """Initialize async connection pool"""
        connections.configure(
            default={
                'hosts': [self.url],
                'timeout': 20,
                'max_retries': 3,
                'retry_on_timeout': True,
                'sniff_on_start': False,
                'sniff_on_connection_fail': False,
                'sniffer_timeout': 60
            }
        )
        
        # Test connection
        client = connections.get_connection()
        await client.ping()
        print(f"Connected to Elasticsearch at {self.url}")
    
    async def disconnect(self):
        """Close connection pool"""
        client = connections.get_connection()
        await client.close()
        print("Elasticsearch connection closed")

# Global connection manager
es_manager = ElasticsearchManager("localhost", 9200)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with connection management"""
    # Startup
    await es_manager.connect()
    
    yield
    
    # Shutdown
    await es_manager.disconnect()

app = FastAPI(lifespan=lifespan)
```

### Connection Health Checks
```python
import asyncio
from elasticsearch_dsl.connections import connections

async def check_elasticsearch_health():
    """Check Elasticsearch cluster health"""
    try:
        client = connections.get_connection()
        
        # Basic connectivity
        await client.ping()
        
        # Cluster health
        health = await client.cluster.health()
        
        # Index health
        indices = await client.cat.indices(format='json')
        
        return {
            'status': 'healthy',
            'cluster_status': health['status'],
            'active_indices': len(indices)
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    es_health = await check_elasticsearch_health()
    
    return {
        'application': 'healthy',
        'elasticsearch': es_health
    }
```

## Error Handling Patterns

### Async Exception Handling
```python
from elasticsearch.exceptions import NotFoundError, RequestError, ConnectionError
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def safe_get_document(doc_id: str):
    """Safe document retrieval with error handling"""
    try:
        return await BlogPost.get(id=doc_id)
        
    except NotFoundError:
        logger.warning(f"Document not found: {doc_id}")
        return None
        
    except ConnectionError as e:
        logger.error(f"Elasticsearch connection error: {e}")
        raise HTTPException(
            status_code=503, 
            detail="Search service temporarily unavailable"
        )
        
    except RequestError as e:
        logger.error(f"Elasticsearch request error: {e}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid search request"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Internal server error"
        )

# Circuit breaker pattern for resilient connections
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise HTTPException(
                    status_code=503, 
                    detail="Service temporarily unavailable"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self):
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.timeout
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'

# Usage
circuit_breaker = CircuitBreaker()

@app.get("/posts/{post_id}")
async def get_post_with_circuit_breaker(post_id: str):
    return await circuit_breaker.call(safe_get_document, post_id)
```

## Performance Optimization

### Concurrent Operations
```python
import asyncio
from typing import List

async def search_multiple_indices(queries: List[str]):
    """Search multiple indices concurrently"""
    tasks = []
    
    for i, query in enumerate(queries):
        search = AsyncSearch(index=f'posts_{i}')
        search = search.query('match', content=query)
        tasks.append(search.execute())
    
    # Run all searches concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Search {i} failed: {result}")
        else:
            successful_results.append(result)
    
    return successful_results

# Batch processing with semaphore for rate limiting
async def batch_process_documents(documents: List[dict], max_concurrent: int = 10):
    """Process documents with concurrency control"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_document(doc_data):
        async with semaphore:
            doc = BlogPost(**doc_data)
            await doc.save()
            return doc.meta.id
    
    tasks = [process_single_document(doc) for doc in documents]
    return await asyncio.gather(*tasks)
```

### Async Generators for Large Datasets
```python
async def scan_all_posts():
    """Async generator for processing large datasets"""
    search = AsyncSearch(index='blog_posts')
    search = search.params(scroll='5m', size=100)
    
    async for hit in search.scan():
        yield {
            'id': hit.meta.id,
            'title': hit.title,
            'author': hit.author
        }

# Usage
@app.get("/export/posts")
async def export_posts():
    """Stream large datasets efficiently"""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate_posts():
        yield '{"posts": ['
        first = True
        
        async for post in scan_all_posts():
            if not first:
                yield ','
            yield json.dumps(post)
            first = False
        
        yield ']}'
    
    return StreamingResponse(
        generate_posts(),
        media_type='application/json',
        headers={'Content-Disposition': 'attachment; filename=posts.json'}
    )
```

## Common Pitfalls

### ❌ Blocking Operations in Async Functions
```python
# Wrong: Using synchronous operations
async def bad_search(query: str):
    import time
    time.sleep(1)  # Blocks the event loop!
    
    search = Search(index='posts')  # Synchronous client
    return search.execute()  # Blocks

# Wrong: Not awaiting async operations
async def bad_save(post_data: dict):
    post = BlogPost(**post_data)
    post.save()  # Missing await!
    return post.meta.id
```

### ✅ Proper Async Usage
```python
# Correct: Using async operations
async def good_search(query: str):
    await asyncio.sleep(1)  # Non-blocking
    
    search = AsyncSearch(index='posts')  # Async client
    return await search.execute()  # Properly awaited

# Correct: Awaiting async operations
async def good_save(post_data: dict):
    post = BlogPost(**post_data)
    await post.save()  # Properly awaited
    return post.meta.id
```

### ❌ Creating Connections in Request Handlers
```python
# Wrong: New connection per request
@app.get("/search")
async def bad_search(q: str):
    # Creates new connection every time
    connections.configure(default={'hosts': ['localhost:9200']})
    search = AsyncSearch(index='posts')
    return await search.execute()
```

### ✅ Proper Connection Management
```python
# Correct: Reuse connection pool
@app.get("/search")
async def good_search(q: str, client = Depends(get_elasticsearch_client)):
    # Reuses existing connection
    search = AsyncSearch(using=client, index='posts')
    return await search.execute()
```

## Next Steps

1. **[Development Environment](04_development-environment.md)** - Advanced tooling and workflow setup
2. **[Document Models & Mapping](../02-elasticsearch-dsl-integration/01_document-models-mapping.md)** - Type-safe document modeling

## Additional Resources

- **Python Asyncio Documentation**: [docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html)
- **FastAPI Async Guide**: [fastapi.tiangolo.com/async](https://fastapi.tiangolo.com/async/)
- **Elasticsearch-DSL Async**: [elasticsearch-dsl.readthedocs.io/en/latest/async.html](https://elasticsearch-dsl.readthedocs.io/en/latest/async.html)