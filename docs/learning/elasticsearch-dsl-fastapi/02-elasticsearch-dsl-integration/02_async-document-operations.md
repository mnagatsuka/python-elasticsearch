# Async Document Operations

Comprehensive guide to performing CRUD operations with elasticsearch-dsl using async patterns for optimal performance.

## Table of Contents
- [Basic CRUD Operations](#basic-crud-operations)
- [Bulk Operations & Batch Processing](#bulk-operations--batch-processing)
- [Advanced Search Operations](#advanced-search-operations)
- [Error Handling & Resilience](#error-handling--resilience)
- [Performance Optimization](#performance-optimization)
- [Transaction-like Patterns](#transaction-like-patterns)
- [Streaming & Pagination](#streaming--pagination)
- [Next Steps](#next-steps)

## Basic CRUD Operations

### Document Creation and Updates
Efficient async patterns for creating and updating documents with proper error handling.

```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Integer, Date, Boolean
from elasticsearch import AsyncElasticsearch
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio

class BlogPost(AsyncDocument):
    """Blog post document model."""
    
    title = Text(analyzer='english', boost=2.0)
    content = Text(analyzer='english')
    author = Keyword()
    category = Keyword()
    tags = Keyword(multi=True)
    view_count = Integer()
    published_date = Date()
    created_at = Date()
    updated_at = Date()
    is_published = Boolean()
    
    class Index:
        name = 'blog_posts'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
    
    async def save(self, **kwargs):
        """Override save to add timestamps."""
        now = datetime.utcnow()
        if not self.created_at:
            self.created_at = now
        self.updated_at = now
        return await super().save(**kwargs)

class DocumentService:
    """Service class for document operations."""
    
    async def create_blog_post(self, post_data: Dict[str, Any]) -> BlogPost:
        """Create a new blog post with validation."""
        try:
            post = BlogPost(
                title=post_data.get('title'),
                content=post_data.get('content'),
                author=post_data.get('author'),
                category=post_data.get('category'),
                tags=post_data.get('tags', []),
                view_count=0,
                published_date=datetime.utcnow() if post_data.get('is_published') else None,
                is_published=post_data.get('is_published', False)
            )
            
            await post.save()
            return post
            
        except Exception as e:
            raise ValueError(f"Failed to create blog post: {str(e)}")
    
    async def get_blog_post(self, post_id: str) -> Optional[BlogPost]:
        """Retrieve a blog post by ID."""
        try:
            return await BlogPost.get(id=post_id)
        except Exception:
            return None
    
    async def update_blog_post(self, post_id: str, updates: Dict[str, Any]) -> Optional[BlogPost]:
        """Update an existing blog post."""
        try:
            post = await BlogPost.get(id=post_id)
            
            # Update fields
            for field, value in updates.items():
                if hasattr(post, field):
                    setattr(post, field, value)
            
            # Handle publication status change
            if 'is_published' in updates and updates['is_published'] and not post.published_date:
                post.published_date = datetime.utcnow()
            
            await post.save()
            return post
            
        except Exception as e:
            raise ValueError(f"Failed to update blog post {post_id}: {str(e)}")
    
    async def delete_blog_post(self, post_id: str) -> bool:
        """Delete a blog post."""
        try:
            post = await BlogPost.get(id=post_id)
            await post.delete()
            return True
        except Exception:
            return False
    
    async def increment_view_count(self, post_id: str) -> Optional[int]:
        """Atomically increment view count."""
        try:
            from elasticsearch_dsl.connections import connections
            client = connections.get_connection()
            
            # Use update API for atomic increment
            response = await client.update(
                index='blog_posts',
                id=post_id,
                body={
                    'script': {
                        'source': 'ctx._source.view_count = (ctx._source.view_count ?: 0) + 1'
                    }
                }
            )
            
            # Get updated document to return new count
            updated_post = await BlogPost.get(id=post_id)
            return updated_post.view_count
            
        except Exception as e:
            print(f"Failed to increment view count: {e}")
            return None

# Usage examples
document_service = DocumentService()

async def crud_examples():
    """Demonstrate basic CRUD operations."""
    
    # Create
    post_data = {
        'title': 'Advanced Elasticsearch Patterns',
        'content': 'This post covers advanced patterns for using Elasticsearch...',
        'author': 'john_doe',
        'category': 'tutorial',
        'tags': ['elasticsearch', 'python', 'async'],
        'is_published': True
    }
    
    new_post = await document_service.create_blog_post(post_data)
    print(f"Created post: {new_post.meta.id}")
    
    # Read
    retrieved_post = await document_service.get_blog_post(new_post.meta.id)
    print(f"Retrieved post: {retrieved_post.title}")
    
    # Update
    updates = {
        'title': 'Advanced Elasticsearch Patterns - Updated',
        'tags': ['elasticsearch', 'python', 'async', 'fastapi']
    }
    updated_post = await document_service.update_blog_post(new_post.meta.id, updates)
    print(f"Updated post title: {updated_post.title}")
    
    # Increment view count
    new_count = await document_service.increment_view_count(new_post.meta.id)
    print(f"New view count: {new_count}")
    
    # Delete
    deleted = await document_service.delete_blog_post(new_post.meta.id)
    print(f"Post deleted: {deleted}")
    
    return {
        'created_id': new_post.meta.id,
        'final_view_count': new_count,
        'deleted': deleted
    }
```

### Upsert Operations
```python
class UpsertService:
    """Service for upsert operations."""
    
    async def upsert_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> 'UserProfile':
        """Create or update user profile."""
        from elasticsearch_dsl.connections import connections
        
        client = connections.get_connection()
        
        try:
            # Try to get existing document
            existing = await UserProfile.get(id=user_id)
            
            # Update existing document
            for field, value in profile_data.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)
            
            await existing.save()
            return existing
            
        except Exception:
            # Document doesn't exist, create new one
            profile = UserProfile(meta={'id': user_id}, **profile_data)
            await profile.save()
            return profile
    
    async def bulk_upsert_using_update_api(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk upsert using Elasticsearch update API."""
        from elasticsearch_dsl.connections import connections
        from elasticsearch.helpers import async_bulk
        
        client = connections.get_connection()
        
        actions = []
        for doc in documents:
            doc_id = doc.get('id')
            doc_body = {k: v for k, v in doc.items() if k != 'id'}
            
            action = {
                '_op_type': 'update',
                '_index': 'user_profiles',
                '_id': doc_id,
                'doc': doc_body,
                'doc_as_upsert': True  # Create if doesn't exist
            }
            actions.append(action)
        
        success, failed = await async_bulk(client, actions)
        
        return {
            'successful': success,
            'failed': len(failed),
            'failed_docs': failed
        }

class UserProfile(AsyncDocument):
    """User profile document."""
    
    username = Keyword()
    email = Keyword()
    full_name = Text()
    bio = Text()
    last_login = Date()
    preferences = Object(
        properties={
            'theme': Keyword(),
            'notifications': Boolean(),
            'language': Keyword()
        }
    )
    
    class Index:
        name = 'user_profiles'
```

## Bulk Operations & Batch Processing

### Efficient Bulk Operations
```python
from elasticsearch.helpers import async_bulk, async_streaming_bulk
from elasticsearch_dsl.connections import connections
import asyncio
from typing import AsyncGenerator

class BulkOperationsService:
    """Service for efficient bulk operations."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def bulk_index_documents(self, documents: List[Dict[str, Any]], 
                                 index_name: str, batch_size: int = 100) -> Dict[str, Any]:
        """Bulk index documents with batching."""
        
        def doc_generator():
            """Generator for bulk indexing."""
            for doc in documents:
                yield {
                    '_index': index_name,
                    '_source': doc
                }
        
        try:
            success, failed = await async_bulk(
                self.client,
                doc_generator(),
                chunk_size=batch_size,
                max_chunk_bytes=10 * 1024 * 1024  # 10MB chunks
            )
            
            return {
                'indexed': success,
                'failed': len(failed),
                'errors': failed
            }
            
        except Exception as e:
            return {
                'indexed': 0,
                'failed': len(documents),
                'errors': [str(e)]
            }
    
    async def streaming_bulk_index(self, document_stream: AsyncGenerator[Dict[str, Any], None],
                                 index_name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream documents for bulk indexing."""
        
        async def action_generator():
            async for doc in document_stream:
                yield {
                    '_index': index_name,
                    '_source': doc
                }
        
        async for ok, info in async_streaming_bulk(
            self.client,
            action_generator(),
            chunk_size=100
        ):
            if not ok:
                yield {'status': 'error', 'info': info}
            else:
                yield {'status': 'success', 'info': info}
    
    async def bulk_update_with_script(self, updates: List[Dict[str, Any]], 
                                    index_name: str) -> Dict[str, Any]:
        """Bulk update using scripts."""
        
        actions = []
        for update in updates:
            action = {
                '_op_type': 'update',
                '_index': index_name,
                '_id': update['id'],
                'script': {
                    'source': update['script_source'],
                    'params': update.get('params', {})
                }
            }
            actions.append(action)
        
        success, failed = await async_bulk(self.client, actions)
        
        return {
            'updated': success,
            'failed': len(failed),
            'errors': failed
        }
    
    async def bulk_delete_by_query(self, index_name: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk delete documents matching query."""
        try:
            response = await self.client.delete_by_query(
                index=index_name,
                body={'query': query},
                wait_for_completion=True,
                refresh=True
            )
            
            return {
                'deleted': response['deleted'],
                'took': response['took'],
                'failures': response.get('failures', [])
            }
            
        except Exception as e:
            return {
                'deleted': 0,
                'error': str(e)
            }

# Usage examples
async def bulk_operations_examples():
    """Demonstrate bulk operations."""
    bulk_service = BulkOperationsService()
    
    # Generate sample documents
    sample_docs = [
        {
            'title': f'Blog Post {i}',
            'content': f'Content for blog post number {i}',
            'author': f'author_{i % 5}',
            'tags': ['sample', 'bulk'],
            'created_at': datetime.utcnow().isoformat()
        }
        for i in range(1000)
    ]
    
    # Bulk index
    result = await bulk_service.bulk_index_documents(sample_docs, 'blog_posts')
    print(f"Bulk indexed: {result['indexed']} documents")
    
    # Bulk update with script
    updates = [
        {
            'id': f'doc_{i}',
            'script_source': 'ctx._source.view_count = (ctx._source.view_count ?: 0) + params.increment',
            'params': {'increment': 1}
        }
        for i in range(100)
    ]
    
    update_result = await bulk_service.bulk_update_with_script(updates, 'blog_posts')
    print(f"Bulk updated: {update_result['updated']} documents")
    
    # Bulk delete by query
    delete_query = {
        'range': {
            'created_at': {
                'lt': 'now-30d'
            }
        }
    }
    
    delete_result = await bulk_service.bulk_delete_by_query('blog_posts', delete_query)
    print(f"Bulk deleted: {delete_result['deleted']} documents")
    
    return {
        'indexed': result['indexed'],
        'updated': update_result['updated'],
        'deleted': delete_result['deleted']
    }
```

### Concurrent Processing
```python
import asyncio
from asyncio import Semaphore
from typing import Callable, List, Any

class ConcurrentProcessor:
    """Handle concurrent document processing."""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = Semaphore(max_concurrent)
    
    async def process_documents_concurrently(self, 
                                           documents: List[Any],
                                           processor: Callable,
                                           batch_size: int = 100) -> List[Any]:
        """Process documents concurrently in batches."""
        
        async def process_batch(batch: List[Any]) -> List[Any]:
            async with self.semaphore:
                tasks = [processor(doc) for doc in batch]
                return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Split into batches
        batches = [
            documents[i:i + batch_size] 
            for i in range(0, len(documents), batch_size)
        ]
        
        # Process batches concurrently
        batch_tasks = [process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Flatten results
        results = []
        for batch_result in batch_results:
            results.extend(batch_result)
        
        return results
    
    async def concurrent_document_enrichment(self, documents: List[BlogPost]) -> List[BlogPost]:
        """Enrich documents concurrently."""
        
        async def enrich_document(doc: BlogPost) -> BlogPost:
            """Enrich a single document with additional data."""
            # Simulate external API call
            await asyncio.sleep(0.1)
            
            # Add computed fields
            if doc.content:
                doc.word_count = len(doc.content.split())
                doc.reading_time = max(1, doc.word_count // 200)
            
            # Enrich with category data
            category_info = await self.get_category_info(doc.category)
            doc.category_description = category_info.get('description', '')
            
            return doc
        
        return await self.process_documents_concurrently(
            documents, 
            enrich_document,
            batch_size=50
        )
    
    async def get_category_info(self, category: str) -> Dict[str, Any]:
        """Mock category enrichment."""
        category_map = {
            'tutorial': {'description': 'Educational content'},
            'news': {'description': 'Latest updates'},
            'review': {'description': 'Product and service reviews'}
        }
        return category_map.get(category, {'description': 'General content'})
```

## Advanced Search Operations

### Complex Query Building
```python
from elasticsearch_dsl import AsyncSearch, Q, A
from typing import Optional, Dict, List, Any

class AdvancedSearchService:
    """Service for complex search operations."""
    
    async def multi_field_search(self, query_text: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Advanced multi-field search with filtering."""
        
        search = AsyncSearch(index='blog_posts')
        
        if query_text:
            # Multi-match query with boosting
            query = Q('multi_match', 
                     query=query_text,
                     fields=['title^3', 'content^1', 'tags^2'],
                     type='best_fields',
                     fuzziness='AUTO')
            
            search = search.query(query)
        
        # Apply filters
        if filters:
            if 'author' in filters:
                search = search.filter('term', author=filters['author'])
            
            if 'category' in filters:
                search = search.filter('term', category=filters['category'])
            
            if 'date_range' in filters:
                date_filter = filters['date_range']
                search = search.filter('range', published_date=date_filter)
            
            if 'tags' in filters:
                search = search.filter('terms', tags=filters['tags'])
        
        # Add aggregations
        search.aggs.bucket('categories', 'terms', field='category', size=10)
        search.aggs.bucket('authors', 'terms', field='author', size=10)
        search.aggs.bucket('monthly_posts', 'date_histogram',
                          field='published_date', calendar_interval='month')
        
        # Add highlighting
        search = search.highlight('title', 'content', fragment_size=150)
        
        # Execute search
        response = await search.execute()
        
        return {
            'hits': [
                {
                    'id': hit.meta.id,
                    'score': hit.meta.score,
                    'source': hit.to_dict(),
                    'highlights': hit.meta.highlight.to_dict() if hasattr(hit.meta, 'highlight') else {}
                }
                for hit in response.hits
            ],
            'total': response.hits.total.value,
            'aggregations': {
                'categories': [
                    {'key': bucket.key, 'count': bucket.doc_count}
                    for bucket in response.aggregations.categories.buckets
                ],
                'authors': [
                    {'key': bucket.key, 'count': bucket.doc_count}
                    for bucket in response.aggregations.authors.buckets
                ],
                'monthly_distribution': [
                    {'month': bucket.key_as_string, 'count': bucket.doc_count}
                    for bucket in response.aggregations.monthly_posts.buckets
                ]
            }
        }
    
    async def semantic_search_with_vector(self, query_text: str, vector_field: str = 'content_vector') -> List[Dict[str, Any]]:
        """Semantic search using vector similarity."""
        
        # Generate query vector (mock implementation)
        query_vector = await self.generate_vector(query_text)
        
        search = AsyncSearch(index='blog_posts')
        
        # Vector similarity query
        vector_query = Q('script_score',
                        query=Q('match_all'),
                        script={
                            'source': 'cosineSimilarity(params.query_vector, doc[params.vector_field]) + 1.0',
                            'params': {
                                'query_vector': query_vector,
                                'vector_field': vector_field
                            }
                        })
        
        search = search.query(vector_query)
        search = search[:10]  # Top 10 results
        
        response = await search.execute()
        
        return [
            {
                'id': hit.meta.id,
                'score': hit.meta.score,
                'title': hit.title,
                'content_preview': hit.content[:200] + '...' if len(hit.content) > 200 else hit.content
            }
            for hit in response.hits
        ]
    
    async def generate_vector(self, text: str) -> List[float]:
        """Mock vector generation."""
        # In reality, this would call a sentence transformer or API
        import hashlib
        import struct
        
        # Simple hash-based mock vector
        hash_object = hashlib.md5(text.encode())
        hash_bytes = hash_object.digest()
        
        # Convert to 384-dimensional vector (mock)
        vector = []
        for i in range(0, len(hash_bytes), 4):
            chunk = hash_bytes[i:i+4].ljust(4, b'\x00')
            value = struct.unpack('f', chunk)[0]
            vector.append(value)
        
        # Extend to 384 dimensions
        while len(vector) < 384:
            vector.extend(vector[:min(4, 384 - len(vector))])
        
        return vector[:384]
    
    async def autocomplete_search(self, prefix: str, field: str = 'title') -> List[Dict[str, str]]:
        """Autocomplete search using prefix queries."""
        
        search = AsyncSearch(index='blog_posts')
        
        # Prefix query for autocomplete
        prefix_query = Q('prefix', **{field: prefix.lower()})
        
        search = search.query(prefix_query)
        search = search[:10]
        search = search.source([field, 'author'])  # Only return necessary fields
        
        response = await search.execute()
        
        return [
            {
                'text': getattr(hit, field),
                'author': hit.author,
                'id': hit.meta.id
            }
            for hit in response.hits
        ]
```

### Result Processing and Pagination
```python
class SearchResultProcessor:
    """Process and paginate search results."""
    
    async def paginated_search(self, query: Dict[str, Any], 
                             page: int = 1, size: int = 20) -> Dict[str, Any]:
        """Paginated search with cursor support."""
        
        search = AsyncSearch(index='blog_posts')
        
        # Apply query
        if 'query' in query:
            search = search.query('match', title=query['query'])
        
        # Calculate offset
        offset = (page - 1) * size
        search = search[offset:offset + size]
        
        # Add sort for consistent pagination
        search = search.sort('-published_date', '_id')
        
        response = await search.execute()
        
        total_pages = (response.hits.total.value + size - 1) // size
        
        return {
            'results': [hit.to_dict() for hit in response.hits],
            'pagination': {
                'current_page': page,
                'page_size': size,
                'total_results': response.hits.total.value,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
        }
    
    async def search_after_pagination(self, query: Dict[str, Any],
                                    search_after: Optional[List[Any]] = None,
                                    size: int = 20) -> Dict[str, Any]:
        """Deep pagination using search_after."""
        
        search = AsyncSearch(index='blog_posts')
        
        if 'query' in query:
            search = search.query('match', title=query['query'])
        
        # Add sort
        search = search.sort('-published_date', '_id')
        search = search[:size]
        
        # Apply search_after for deep pagination
        if search_after:
            search = search.extra(search_after=search_after)
        
        response = await search.execute()
        
        # Get sort values for next page
        next_search_after = None
        if response.hits:
            last_hit = response.hits[-1]
            next_search_after = last_hit.meta.sort
        
        return {
            'results': [hit.to_dict() for hit in response.hits],
            'next_search_after': next_search_after,
            'has_more': len(response.hits) == size
        }
    
    async def scroll_search(self, query: Dict[str, Any], 
                          scroll_time: str = '5m') -> AsyncGenerator[Dict[str, Any], None]:
        """Scroll through all results."""
        
        search = AsyncSearch(index='blog_posts')
        
        if 'query' in query:
            search = search.query('match', title=query['query'])
        
        # Configure scroll
        search = search.params(scroll=scroll_time, size=100)
        
        async for hit in search.scan():
            yield hit.to_dict()
```

## Error Handling & Resilience

### Robust Error Handling
```python
from elasticsearch.exceptions import NotFoundError, ConflictError, RequestError
import logging
from typing import Optional, Union
import asyncio

logger = logging.getLogger(__name__)

class ResilientDocumentService:
    """Document service with comprehensive error handling."""
    
    async def safe_get_document(self, doc_class: type, doc_id: str, 
                              retries: int = 3) -> Optional[AsyncDocument]:
        """Safely retrieve document with retries."""
        
        for attempt in range(retries):
            try:
                return await doc_class.get(id=doc_id)
                
            except NotFoundError:
                logger.warning(f"Document {doc_id} not found")
                return None
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for document {doc_id}: {e}")
                
                if attempt == retries - 1:
                    raise
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def safe_save_document(self, document: AsyncDocument, 
                               retries: int = 3) -> bool:
        """Safely save document with conflict resolution."""
        
        for attempt in range(retries):
            try:
                await document.save()
                return True
                
            except ConflictError:
                logger.warning(f"Version conflict for document {document.meta.id}, retrying...")
                
                # Refresh document to get latest version
                try:
                    latest = await document.__class__.get(id=document.meta.id)
                    document.meta.version = latest.meta.version
                except NotFoundError:
                    # Document was deleted, safe to create
                    document.meta.version = None
                
            except RequestError as e:
                if e.status_code == 429:  # Rate limiting
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request error: {e}")
                    raise
                
            except Exception as e:
                logger.error(f"Unexpected error saving document: {e}")
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(1)
        
        return False
    
    async def batch_operation_with_retry(self, operations: List[Callable],
                                       max_concurrent: int = 5) -> Dict[str, Any]:
        """Execute batch operations with individual retry logic."""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {'successful': 0, 'failed': 0, 'errors': []}
        
        async def execute_with_semaphore(operation):
            async with semaphore:
                try:
                    await operation()
                    results['successful'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(str(e))
                    logger.error(f"Operation failed: {e}")
        
        tasks = [execute_with_semaphore(op) for op in operations]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch cluster health."""
        try:
            from elasticsearch_dsl.connections import connections
            client = connections.get_connection()
            
            # Check cluster health
            health = await client.cluster.health()
            
            # Test basic operations
            test_doc = BlogPost(title="Health Check", content="Test")
            await test_doc.save()
            await test_doc.delete()
            
            return {
                'status': 'healthy',
                'cluster_status': health['status'],
                'number_of_nodes': health['number_of_nodes'],
                'active_shards': health['active_shards']
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Circuit breaker pattern
class CircuitBreaker:
    """Circuit breaker for Elasticsearch operations."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        import time
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed operation."""
        import time
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

## Performance Optimization

### Connection Pooling and Caching
```python
from elasticsearch_dsl.connections import connections
import asyncio
from typing import Dict, Any, Optional
import json
import hashlib
from datetime import datetime, timedelta

class PerformanceOptimizedService:
    """Service with performance optimizations."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def configure_connection_pool(self):
        """Configure optimized connection pool."""
        
        connections.configure(
            default={
                'hosts': ['localhost:9200'],
                'max_retries': 3,
                'retry_on_timeout': True,
                'timeout': 30,
                'max_timeout': 60,
                # Connection pool settings
                'maxsize': 20,
                'http_compress': True,
                'verify_certs': False
            }
        )
    
    def _cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        key_data = json.dumps(kwargs, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cache entry is still valid."""
        return datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl)
    
    async def cached_search(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search with result caching."""
        
        cache_key = self._cache_key("search", **query)
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                return cached_result
        
        # Execute search
        search = AsyncSearch(index='blog_posts')
        if 'query' in query:
            search = search.query('match', title=query['query'])
        
        response = await search.execute()
        result = {
            'hits': [hit.to_dict() for hit in response.hits],
            'total': response.hits.total.value
        }
        
        # Cache result
        self.cache[cache_key] = (result, datetime.utcnow())
        
        return result
    
    async def batch_get_with_mget(self, doc_ids: List[str], 
                                index: str = 'blog_posts') -> List[Optional[Dict[str, Any]]]:
        """Efficient batch retrieval using mget."""
        
        if not doc_ids:
            return []
        
        from elasticsearch_dsl.connections import connections
        client = connections.get_connection()
        
        # Prepare mget request
        body = {
            'docs': [
                {'_index': index, '_id': doc_id}
                for doc_id in doc_ids
            ]
        }
        
        response = await client.mget(body=body)
        
        results = []
        for doc in response['docs']:
            if doc['found']:
                results.append(doc['_source'])
            else:
                results.append(None)
        
        return results
    
    async def optimized_aggregation_query(self, field: str, 
                                        filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimized aggregation with minimal document retrieval."""
        
        search = AsyncSearch(index='blog_posts')
        
        # Apply filters
        if filters:
            for filter_field, filter_value in filters.items():
                search = search.filter('term', **{filter_field: filter_value})
        
        # Add aggregation
        search.aggs.bucket('field_values', 'terms', field=field, size=100)
        
        # Don't retrieve documents, only aggregations
        search = search[:0]
        
        response = await search.execute()
        
        return {
            'aggregation_results': [
                {'key': bucket.key, 'count': bucket.doc_count}
                for bucket in response.aggregations.field_values.buckets
            ],
            'total_documents': response.hits.total.value
        }
    
    async def streaming_export(self, query: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream large result sets efficiently."""
        
        search = AsyncSearch(index='blog_posts')
        
        if 'query' in query:
            search = search.query('match', title=query['query'])
        
        # Use scan for efficient scrolling
        search = search.params(scroll='5m', size=100)
        
        document_count = 0
        async for hit in search.scan():
            document_count += 1
            
            # Yield minimal data structure
            yield {
                'id': hit.meta.id,
                'title': hit.title,
                'author': hit.author,
                'published_date': hit.published_date.isoformat() if hit.published_date else None
            }
            
            # Periodic logging
            if document_count % 1000 == 0:
                logger.info(f"Exported {document_count} documents")
```

## Transaction-like Patterns

### Coordinated Updates
```python
class TransactionService:
    """Service for coordinated document updates."""
    
    async def atomic_transfer_operation(self, source_id: str, target_id: str, 
                                      amount: int) -> Dict[str, Any]:
        """Simulate atomic transfer between documents."""
        
        from elasticsearch_dsl.connections import connections
        client = connections.get_connection()
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Get both documents with their current versions
                source_doc = await BlogPost.get(id=source_id)
                target_doc = await BlogPost.get(id=target_id)
                
                # Check business rules
                if source_doc.view_count < amount:
                    return {'success': False, 'error': 'Insufficient views'}
                
                # Prepare updates with version checks
                source_update = {
                    'script': {
                        'source': 'ctx._source.view_count -= params.amount',
                        'params': {'amount': amount}
                    },
                    'version': source_doc.meta.version,
                    'version_type': 'external_gte'
                }
                
                target_update = {
                    'script': {
                        'source': 'ctx._source.view_count += params.amount',
                        'params': {'amount': amount}
                    },
                    'version': target_doc.meta.version,
                    'version_type': 'external_gte'
                }
                
                # Execute updates
                await client.update(index='blog_posts', id=source_id, body=source_update)
                await client.update(index='blog_posts', id=target_id, body=target_update)
                
                return {
                    'success': True,
                    'transferred': amount,
                    'attempt': attempt + 1
                }
                
            except ConflictError:
                if attempt == max_retries - 1:
                    return {'success': False, 'error': 'Max retries exceeded'}
                await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': 'Operation failed'}
    
    async def saga_pattern_example(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Implement saga pattern for distributed transactions."""
        
        completed_operations = []
        
        try:
            # Execute operations in sequence
            for i, operation in enumerate(operations):
                result = await self._execute_operation(operation)
                completed_operations.append((i, operation, result))
                
                if not result.get('success', False):
                    raise Exception(f"Operation {i} failed: {result.get('error')}")
            
            return {'success': True, 'completed_operations': len(operations)}
            
        except Exception as e:
            # Compensate completed operations in reverse order
            logger.error(f"Saga failed: {e}. Starting compensation...")
            
            compensation_results = []
            for i, operation, result in reversed(completed_operations):
                try:
                    compensation = await self._compensate_operation(operation, result)
                    compensation_results.append(compensation)
                except Exception as comp_error:
                    logger.error(f"Compensation failed for operation {i}: {comp_error}")
            
            return {
                'success': False,
                'error': str(e),
                'compensated': len(compensation_results)
            }
    
    async def _execute_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single operation."""
        op_type = operation['type']
        
        if op_type == 'update_document':
            try:
                doc = await BlogPost.get(id=operation['doc_id'])
                for field, value in operation['updates'].items():
                    setattr(doc, field, value)
                await doc.save()
                return {'success': True, 'doc_id': operation['doc_id']}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Add more operation types as needed
        return {'success': False, 'error': 'Unknown operation type'}
    
    async def _compensate_operation(self, operation: Dict[str, Any], 
                                  original_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compensate a completed operation."""
        # Implement compensation logic based on operation type
        if operation['type'] == 'update_document':
            # Restore original values
            try:
                doc = await BlogPost.get(id=operation['doc_id'])
                for field, value in operation.get('original_values', {}).items():
                    setattr(doc, field, value)
                await doc.save()
                return {'compensated': True}
            except Exception as e:
                return {'compensated': False, 'error': str(e)}
        
        return {'compensated': False, 'error': 'No compensation defined'}
```

## Streaming & Pagination

### Efficient Data Streaming
```python
class StreamingService:
    """Service for efficient data streaming."""
    
    async def stream_search_results(self, query: Dict[str, Any],
                                  batch_size: int = 100) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Stream search results in batches."""
        
        search = AsyncSearch(index='blog_posts')
        
        if 'query' in query:
            search = search.query('match', title=query['query'])
        
        # Configure for streaming
        search = search.params(scroll='2m', size=batch_size)
        
        batch = []
        async for hit in search.scan():
            batch.append(hit.to_dict())
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
        
        # Yield remaining documents
        if batch:
            yield batch
    
    async def export_to_jsonl(self, query: Dict[str, Any], 
                            output_file: str) -> Dict[str, Any]:
        """Export search results to JSONL format."""
        
        import aiofiles
        import json
        
        exported_count = 0
        
        async with aiofiles.open(output_file, 'w') as f:
            async for batch in self.stream_search_results(query):
                for doc in batch:
                    line = json.dumps(doc) + '\n'
                    await f.write(line)
                    exported_count += 1
                
                # Log progress
                if exported_count % 1000 == 0:
                    logger.info(f"Exported {exported_count} documents")
        
        return {
            'exported_count': exported_count,
            'output_file': output_file
        }
    
    async def parallel_processing_stream(self, query: Dict[str, Any],
                                       processor: Callable,
                                       max_workers: int = 5) -> AsyncGenerator[Any, None]:
        """Process search results with parallel workers."""
        
        import asyncio
        from asyncio import Queue
        
        result_queue = Queue()
        
        async def producer():
            """Produce batches for processing."""
            async for batch in self.stream_search_results(query):
                await result_queue.put(batch)
            
            # Signal completion
            for _ in range(max_workers):
                await result_queue.put(None)
        
        async def worker():
            """Process batches."""
            while True:
                batch = await result_queue.get()
                if batch is None:
                    break
                
                for doc in batch:
                    try:
                        processed = await processor(doc)
                        yield processed
                    except Exception as e:
                        logger.error(f"Processing error: {e}")
        
        # Start producer
        producer_task = asyncio.create_task(producer())
        
        # Start workers
        workers = [worker() for _ in range(max_workers)]
        
        # Yield results as they become available
        async for worker in asyncio.as_completed(workers):
            async for result in worker:
                yield result
        
        await producer_task
```

## Next Steps

1. **[Index Management](03_index-management.md)** - Lifecycle and schema management
2. **[Migration Strategies](04_migration-strategies.md)** - Schema evolution and data migration
3. **[FastAPI Integration](../03-fastapi-integration/01_query-builder-patterns.md)** - Integrating with FastAPI applications

## Additional Resources

- **Elasticsearch Bulk API**: [elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html)
- **Async Python Patterns**: [docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html)
- **Elasticsearch-DSL Async**: [elasticsearch-dsl.readthedocs.io/en/latest/persistence.html#asyncdocument](https://elasticsearch-dsl.readthedocs.io/en/latest/persistence.html#asyncdocument)