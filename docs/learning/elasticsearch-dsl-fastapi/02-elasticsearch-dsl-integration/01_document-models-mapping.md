# Document Models & Mapping

Creating type-safe Elasticsearch document models using elasticsearch-dsl with proper field mapping and validation.

## Table of Contents
- [Document Model Fundamentals](#document-model-fundamentals)
- [Field Types and Mapping](#field-types-and-mapping)
- [Index Configuration](#index-configuration)
- [Advanced Field Options](#advanced-field-options)
- [Validation and Serialization](#validation-and-serialization)
- [Model Relationships](#model-relationships)
- [Migration Patterns](#migration-patterns)
- [Next Steps](#next-steps)

## Document Model Fundamentals

### Basic Document Structure
Elasticsearch-DSL documents provide ORM-like functionality for Elasticsearch with type safety and validation.

```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Integer, Date, Boolean
from datetime import datetime
from typing import List, Optional

class BlogPost(AsyncDocument):
    """Blog post document model with type-safe fields."""
    
    # Text fields for full-text search
    title = Text(analyzer='english', boost=2.0)
    content = Text(analyzer='english')
    summary = Text(analyzer='english')
    
    # Keyword fields for exact matching and aggregations
    author = Keyword()
    category = Keyword()
    status = Keyword()  # draft, published, archived
    tags = Keyword(multi=True)  # Array of tags
    
    # Structured data types
    view_count = Integer()
    published_date = Date()
    created_at = Date()
    updated_at = Date()
    is_featured = Boolean()
    
    class Index:
        name = 'blog_posts'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'english': {
                        'type': 'standard',
                        'stopwords': '_english_'
                    }
                }
            }
        }
    
    def save(self, **kwargs):
        """Override save to add timestamps."""
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        return super().save(**kwargs)

# Usage examples
async def create_blog_post():
    """Create and save a new blog post."""
    post = BlogPost(
        title="Getting Started with FastAPI and Elasticsearch",
        content="This comprehensive guide covers...",
        summary="Learn how to build search APIs with FastAPI",
        author="john_doe",
        category="tutorial",
        status="published",
        tags=["fastapi", "elasticsearch", "python"],
        view_count=0,
        published_date=datetime.utcnow(),
        is_featured=True
    )
    
    await post.save()
    print(f"Blog post created with ID: {post.meta.id}")
    return post
```

### Document Inheritance
Create reusable base classes for common functionality.

```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Date
from datetime import datetime

class BaseDocument(AsyncDocument):
    """Base document with common fields and functionality."""
    
    created_at = Date()
    updated_at = Date()
    created_by = Keyword()
    updated_by = Keyword()
    
    class Meta:
        abstract = True  # Don't create index for this class
    
    async def save(self, user_id: str = None, **kwargs):
        """Save with automatic timestamp and user tracking."""
        now = datetime.utcnow()
        
        if not self.created_at:
            self.created_at = now
            if user_id:
                self.created_by = user_id
        
        self.updated_at = now
        if user_id:
            self.updated_by = user_id
        
        return await super().save(**kwargs)

class ContentDocument(BaseDocument):
    """Base for content-type documents."""
    
    title = Text(analyzer='english', boost=2.0)
    content = Text(analyzer='english')
    status = Keyword()  # draft, published, archived
    author = Keyword()
    
    class Meta:
        abstract = True

class BlogPost(ContentDocument):
    """Blog post extending content document."""
    
    category = Keyword()
    tags = Keyword(multi=True)
    view_count = Integer(value=0)
    
    class Index:
        name = 'blog_posts'

class NewsArticle(ContentDocument):
    """News article extending content document."""
    
    source = Keyword()
    urgency = Keyword()  # low, medium, high, breaking
    location = Keyword()
    
    class Index:
        name = 'news_articles'
```

## Field Types and Mapping

### Text and Keyword Fields
Understanding when to use text vs keyword fields is crucial for search performance.

```python
from elasticsearch_dsl import Text, Keyword, Completion

class ProductDocument(AsyncDocument):
    """Product catalog document with optimized field types."""
    
    # Text fields - analyzed for full-text search
    name = Text(
        analyzer='standard',
        search_analyzer='standard',
        boost=3.0  # Higher relevance for name matches
    )
    
    description = Text(
        analyzer='english',
        search_analyzer='english'
    )
    
    # Keyword fields - exact matching, aggregations, sorting
    sku = Keyword()  # Product SKU - exact match only
    brand = Keyword()  # For aggregations and filtering
    category = Keyword()  # Hierarchical categories
    
    # Multi-field mapping - both text and keyword
    product_name = Text(
        analyzer='standard',
        fields={
            'keyword': Keyword(),  # For exact matching and sorting
            'completion': Completion()  # For autocomplete suggestions
        }
    )
    
    # Tags for faceted search
    tags = Keyword(multi=True)
    
    class Index:
        name = 'products'
        settings = {
            'analysis': {
                'analyzer': {
                    'product_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': [
                            'lowercase',
                            'asciifolding',  # Convert accents
                            'stop'
                        ]
                    }
                }
            }
        }

# Search examples using different field types
async def search_products_examples():
    from elasticsearch_dsl import AsyncSearch, Q
    
    # Full-text search on analyzed fields
    text_search = AsyncSearch(index='products')
    text_search = text_search.query('match', description='wireless headphones')
    
    # Exact keyword matching
    exact_search = AsyncSearch(index='products')
    exact_search = exact_search.query('term', brand='Sony')
    
    # Multi-field search with boosting
    multi_search = AsyncSearch(index='products')
    multi_search = multi_search.query(
        'multi_match',
        query='bluetooth speaker',
        fields=['name^3', 'description^1', 'tags^2'],
        type='best_fields'
    )
    
    # Autocomplete using completion field
    suggest_search = AsyncSearch(index='products')
    suggest_search = suggest_search.suggest(
        'product_suggestions',
        'blue',
        completion={'field': 'product_name.completion'}
    )
    
    return {
        'text_results': await text_search.execute(),
        'exact_results': await exact_search.execute(),
        'multi_results': await multi_search.execute(),
        'suggestions': await suggest_search.execute()
    }
```

### Numeric and Date Fields
```python
from elasticsearch_dsl import Integer, Float, Date, Boolean, Long
from datetime import datetime

class OrderDocument(AsyncDocument):
    """E-commerce order document with various numeric types."""
    
    # Numeric fields
    order_id = Long()  # Large integers
    item_count = Integer()  # Small integers
    total_amount = Float()  # Decimal prices
    discount_percent = Float()
    
    # Date fields with different formats
    order_date = Date()  # ISO format by default
    delivery_date = Date(format='yyyy-MM-dd')  # Custom format
    
    # Boolean fields
    is_paid = Boolean()
    is_shipped = Boolean()
    is_gift = Boolean()
    
    # Customer information
    customer_email = Keyword()
    customer_id = Keyword()
    
    # Shipping address (nested object)
    shipping_address = Object(
        properties={
            'street': Text(),
            'city': Keyword(),
            'state': Keyword(),
            'zip_code': Keyword(),
            'country': Keyword()
        }
    )
    
    class Index:
        name = 'orders'
        settings = {
            'number_of_shards': 2,  # More shards for larger dataset
            'number_of_replicas': 1
        }

# Range queries and aggregations on numeric fields
async def order_analytics():
    from elasticsearch_dsl import AsyncSearch, A
    
    search = AsyncSearch(index='orders')
    
    # Date range filter
    search = search.filter(
        'range',
        order_date={
            'gte': '2024-01-01',
            'lte': '2024-12-31'
        }
    )
    
    # Numeric range filter
    search = search.filter(
        'range',
        total_amount={'gte': 100, 'lte': 1000}
    )
    
    # Aggregations on numeric fields
    search.aggs.metric('avg_order_value', 'avg', field='total_amount')
    search.aggs.metric('total_revenue', 'sum', field='total_amount')
    search.aggs.bucket('orders_by_month', 'date_histogram', 
                      field='order_date', calendar_interval='month')
    
    response = await search.execute()
    
    return {
        'average_order_value': response.aggregations.avg_order_value.value,
        'total_revenue': response.aggregations.total_revenue.value,
        'monthly_orders': [
            {
                'month': bucket.key_as_string,
                'order_count': bucket.doc_count,
                'revenue': bucket.total_revenue.value if hasattr(bucket, 'total_revenue') else 0
            }
            for bucket in response.aggregations.orders_by_month.buckets
        ]
    }
```

### Nested and Object Fields
```python
from elasticsearch_dsl import Nested, Object, Keyword, Text, Float, Integer

class ProductDocument(AsyncDocument):
    """Product with complex nested structures."""
    
    name = Text()
    brand = Keyword()
    
    # Object field - flattened in Elasticsearch
    basic_specs = Object(
        properties={
            'weight': Float(),
            'dimensions': Object(
                properties={
                    'length': Float(),
                    'width': Float(),
                    'height': Float()
                }
            ),
            'color': Keyword(),
            'material': Keyword()
        }
    )
    
    # Nested field - maintains object relationships
    variants = Nested(
        properties={
            'sku': Keyword(),
            'size': Keyword(),
            'color': Keyword(),
            'price': Float(),
            'stock_count': Integer(),
            'images': Keyword(multi=True)
        }
    )
    
    # Reviews as nested objects
    reviews = Nested(
        properties={
            'reviewer_id': Keyword(),
            'rating': Integer(),
            'title': Text(),
            'content': Text(),
            'review_date': Date(),
            'verified_purchase': Boolean()
        }
    )
    
    class Index:
        name = 'products_complex'

# Working with nested queries
async def search_products_with_variants():
    from elasticsearch_dsl import AsyncSearch, Q
    
    search = AsyncSearch(index='products_complex')
    
    # Nested query - find products with specific variant criteria
    variant_query = Q(
        'nested',
        path='variants',
        query=Q('bool', must=[
            Q('term', variants__color='red'),
            Q('range', variants__price={'gte': 50, 'lte': 200})
        ])
    )
    
    # Reviews aggregation with nested structure
    search.aggs.bucket(
        'avg_rating',
        'nested',
        path='reviews'
    ).metric('rating_avg', 'avg', field='reviews.rating')
    
    search = search.query(variant_query)
    response = await search.execute()
    
    return {
        'products': [hit.to_dict() for hit in response.hits],
        'average_rating': response.aggregations.avg_rating.rating_avg.value
    }

# Creating complex documents
async def create_complex_product():
    product = ProductDocument(
        name="Premium Wireless Headphones",
        brand="AudioTech",
        basic_specs={
            'weight': 250.5,
            'dimensions': {
                'length': 18.5,
                'width': 15.2,
                'height': 8.1
            },
            'color': 'black',
            'material': 'plastic'
        },
        variants=[
            {
                'sku': 'WH-001-BLK',
                'size': 'standard',
                'color': 'black',
                'price': 199.99,
                'stock_count': 15,
                'images': ['black-front.jpg', 'black-side.jpg']
            },
            {
                'sku': 'WH-001-WHT',
                'size': 'standard',
                'color': 'white',
                'price': 199.99,
                'stock_count': 8,
                'images': ['white-front.jpg', 'white-side.jpg']
            }
        ],
        reviews=[
            {
                'reviewer_id': 'user123',
                'rating': 5,
                'title': 'Excellent sound quality',
                'content': 'These headphones exceed expectations...',
                'review_date': datetime.utcnow(),
                'verified_purchase': True
            }
        ]
    )
    
    await product.save()
    return product
```

## Index Configuration

### Custom Analyzers and Settings
```python
class SearchOptimizedDocument(AsyncDocument):
    """Document with custom analyzers for different languages and use cases."""
    
    title = Text(analyzer='title_analyzer')
    content = Text(analyzer='content_analyzer')
    tags = Text(analyzer='tag_analyzer', search_analyzer='tag_search_analyzer')
    
    class Index:
        name = 'search_optimized'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'max_result_window': 50000,  # For deep pagination
            'analysis': {
                'analyzer': {
                    'title_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': [
                            'lowercase',
                            'asciifolding',
                            'title_stop_filter',
                            'title_synonym_filter'
                        ]
                    },
                    'content_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': [
                            'lowercase',
                            'asciifolding',
                            'stop',
                            'snowball',
                            'content_synonym_filter'
                        ]
                    },
                    'tag_analyzer': {
                        'type': 'keyword',
                        'normalizer': 'tag_normalizer'
                    },
                    'tag_search_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'keyword',
                        'filter': ['lowercase']
                    }
                },
                'filter': {
                    'title_stop_filter': {
                        'type': 'stop',
                        'stopwords': ['the', 'a', 'an', 'and', 'or', 'but']
                    },
                    'title_synonym_filter': {
                        'type': 'synonym',
                        'synonyms': [
                            'quick,fast,rapid',
                            'guide,tutorial,howto'
                        ]
                    },
                    'content_synonym_filter': {
                        'type': 'synonym',
                        'synonyms_path': 'synonyms.txt'  # External file
                    }
                },
                'normalizer': {
                    'tag_normalizer': {
                        'type': 'custom',
                        'filter': ['lowercase', 'asciifolding']
                    }
                }
            }
        }

# Index template for multiple similar indices
class TimeSeriesDocument(AsyncDocument):
    """Base class for time-series data with rollover support."""
    
    timestamp = Date()
    value = Float()
    metric_name = Keyword()
    
    class Index:
        name = 'metrics-*'  # Pattern for rollover indices
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'index': {
                'lifecycle': {
                    'name': 'metrics_policy',
                    'rollover_alias': 'metrics'
                }
            }
        }
    
    @classmethod
    async def setup_index_template(cls):
        """Setup index template for time-series data."""
        from elasticsearch_dsl.connections import connections
        
        client = connections.get_connection()
        
        template = {
            'index_patterns': ['metrics-*'],
            'settings': cls.Index.settings,
            'mappings': cls.get_mapping().to_dict()
        }
        
        await client.indices.put_index_template(
            name='metrics_template',
            body=template
        )
```

## Advanced Field Options

### Dynamic Templates and Runtime Fields
```python
class FlexibleDocument(AsyncDocument):
    """Document with dynamic field mapping."""
    
    # Static fields
    id = Keyword()
    title = Text()
    
    # Dynamic field template will be applied to unknown fields
    class Index:
        name = 'flexible_docs'
        settings = {
            'mappings': {
                'dynamic_templates': [
                    {
                        'strings_as_keywords': {
                            'match_mapping_type': 'string',
                            'match': '*_exact',
                            'mapping': {
                                'type': 'keyword'
                            }
                        }
                    },
                    {
                        'strings_as_text': {
                            'match_mapping_type': 'string',
                            'mapping': {
                                'type': 'text',
                                'analyzer': 'standard'
                            }
                        }
                    }
                ],
                'runtime': {
                    'full_name': {
                        'type': 'keyword',
                        'script': {
                            'source': "emit(doc['first_name'].value + ' ' + doc['last_name'].value)"
                        }
                    },
                    'price_with_tax': {
                        'type': 'double',
                        'script': {
                            'source': "emit(doc['price'].value * 1.1)"
                        }
                    }
                }
            }
        }

# Working with runtime fields
async def search_with_runtime_fields():
    from elasticsearch_dsl import AsyncSearch
    
    search = AsyncSearch(index='flexible_docs')
    
    # Use runtime field in query
    search = search.filter('term', full_name='John Doe')
    
    # Use runtime field in aggregation
    search.aggs.bucket('price_ranges', 'range', 
                      field='price_with_tax',
                      ranges=[
                          {'to': 100},
                          {'from': 100, 'to': 500},
                          {'from': 500}
                      ])
    
    return await search.execute()
```

### Custom Field Classes
```python
from elasticsearch_dsl import Field
import json

class JSONField(Field):
    """Custom field for storing JSON data."""
    
    name = 'json'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def to_dict(self):
        return {'type': 'text', 'index': False}
    
    def deserialize(self, data):
        if isinstance(data, str):
            return json.loads(data)
        return data
    
    def serialize(self, data):
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        return data

class ConfigDocument(AsyncDocument):
    """Document with custom JSON field."""
    
    name = Keyword()
    config_data = JSONField()
    
    class Index:
        name = 'configurations'

# Usage of custom field
async def create_config_document():
    config = ConfigDocument(
        name='api_settings',
        config_data={
            'timeout': 30,
            'retries': 3,
            'endpoints': {
                'search': '/api/search',
                'index': '/api/index'
            }
        }
    )
    
    await config.save()
    
    # Retrieve and use
    retrieved = await ConfigDocument.get(config.meta.id)
    timeout = retrieved.config_data['timeout']  # Automatically deserialized
    
    return retrieved
```

## Validation and Serialization

### Field Validation
```python
from elasticsearch_dsl import Document, Text, Keyword, Integer, ValidationException

class ValidatedDocument(AsyncDocument):
    """Document with custom validation."""
    
    email = Keyword()
    age = Integer()
    username = Keyword()
    
    def clean(self):
        """Custom validation logic."""
        # Email validation
        if self.email and '@' not in self.email:
            raise ValidationException('Invalid email format')
        
        # Age validation
        if self.age is not None and (self.age < 0 or self.age > 150):
            raise ValidationException('Age must be between 0 and 150')
        
        # Username validation
        if self.username and len(self.username) < 3:
            raise ValidationException('Username must be at least 3 characters')
    
    def clean_email(self):
        """Field-specific validation."""
        if self.email:
            self.email = self.email.lower().strip()
    
    def clean_username(self):
        """Field-specific validation."""
        if self.username:
            # Remove special characters
            import re
            self.username = re.sub(r'[^a-zA-Z0-9_]', '', self.username)
    
    class Index:
        name = 'validated_docs'

# Usage with validation
async def create_validated_document():
    try:
        doc = ValidatedDocument(
            email='USER@EXAMPLE.COM',  # Will be normalized
            age=25,
            username='user@name!'  # Will be cleaned
        )
        
        # Validation happens on save
        await doc.save()
        print(f"Document saved: {doc.email}, {doc.username}")
        
    except ValidationException as e:
        print(f"Validation error: {e}")
        return None
```

### Serialization Methods
```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Date, Integer
from datetime import datetime
import json

class SerializableDocument(AsyncDocument):
    """Document with custom serialization methods."""
    
    title = Text()
    author = Keyword()
    published_date = Date()
    view_count = Integer()
    
    def to_dict(self, include_meta=False, skip_empty=True):
        """Custom serialization with options."""
        result = super().to_dict(include_meta=include_meta, skip_empty=skip_empty)
        
        # Add computed fields
        if hasattr(self, 'published_date') and self.published_date:
            result['days_since_published'] = (
                datetime.utcnow() - self.published_date
            ).days
        
        # Format dates for API consumption
        if 'published_date' in result and result['published_date']:
            result['published_date_formatted'] = self.published_date.strftime('%Y-%m-%d')
        
        return result
    
    def to_api_dict(self):
        """Serialization for API responses."""
        return {
            'id': self.meta.id,
            'title': self.title,
            'author': self.author,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'view_count': self.view_count or 0,
            'url': f"/posts/{self.meta.id}"
        }
    
    @classmethod
    def from_api_dict(cls, data):
        """Create document from API data."""
        # Remove API-specific fields
        doc_data = data.copy()
        doc_data.pop('id', None)
        doc_data.pop('url', None)
        
        # Convert date strings
        if 'published_date' in doc_data and doc_data['published_date']:
            doc_data['published_date'] = datetime.fromisoformat(
                doc_data['published_date'].replace('Z', '+00:00')
            )
        
        return cls(**doc_data)
    
    class Index:
        name = 'serializable_docs'

# Usage examples
async def serialization_examples():
    doc = SerializableDocument(
        title="Advanced Elasticsearch Patterns",
        author="jane_doe",
        published_date=datetime.utcnow(),
        view_count=150
    )
    
    await doc.save()
    
    # Different serialization formats
    full_dict = doc.to_dict(include_meta=True)
    api_dict = doc.to_api_dict()
    
    # Create from API data
    api_data = {
        'title': 'New Post',
        'author': 'john_doe',
        'published_date': '2024-01-15T10:30:00Z',
        'view_count': 0
    }
    
    new_doc = SerializableDocument.from_api_dict(api_data)
    await new_doc.save()
    
    return {
        'full_dict': full_dict,
        'api_dict': api_dict,
        'new_doc_id': new_doc.meta.id
    }
```

## Model Relationships

### Parent-Child Relationships
```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Join

class ContentDocument(AsyncDocument):
    """Parent-child relationship using join field."""
    
    title = Text()
    content = Text()
    author = Keyword()
    
    # Join field to establish parent-child relationships
    content_relation = Join(
        relations={
            'post': 'comment'  # post is parent, comment is child
        }
    )
    
    class Index:
        name = 'content_relations'

# Create parent documents (posts)
async def create_blog_post_with_comments():
    # Create parent post
    post = ContentDocument(
        title="Introduction to Elasticsearch",
        content="Elasticsearch is a powerful search engine...",
        author="john_doe",
        content_relation={'name': 'post'}  # Mark as parent
    )
    await post.save()
    
    # Create child comments
    comment1 = ContentDocument(
        title="Great article!",
        content="This was very helpful, thanks for sharing.",
        author="reader1",
        content_relation={
            'name': 'comment',
            'parent': post.meta.id  # Reference parent
        }
    )
    
    comment2 = ContentDocument(
        title="Question about performance",
        content="How does this scale with large datasets?",
        author="reader2",
        content_relation={
            'name': 'comment',
            'parent': post.meta.id
        }
    )
    
    # Save with routing to same shard as parent
    await comment1.save(routing=post.meta.id)
    await comment2.save(routing=post.meta.id)
    
    return post, [comment1, comment2]

# Query parent-child relationships
async def find_posts_with_active_comments():
    from elasticsearch_dsl import AsyncSearch, Q
    
    search = AsyncSearch(index='content_relations')
    
    # Find posts that have comments
    has_child_query = Q(
        'has_child',
        type='comment',
        query=Q('match_all')
    )
    
    search = search.query(has_child_query)
    search = search.filter('term', content_relation='post')
    
    return await search.execute()
```

### Reference-based Relationships
```python
class UserDocument(AsyncDocument):
    """User document."""
    
    username = Keyword()
    email = Keyword()
    full_name = Text()
    
    class Index:
        name = 'users'

class PostDocument(AsyncDocument):
    """Post document with user reference."""
    
    title = Text()
    content = Text()
    author_id = Keyword()  # Reference to user document
    category_id = Keyword()  # Reference to category
    
    class Index:
        name = 'posts'

class CategoryDocument(AsyncDocument):
    """Category document."""
    
    name = Keyword()
    description = Text()
    
    class Index:
        name = 'categories'

# Service class to handle relationships
class ContentService:
    """Service to manage related documents."""
    
    async def get_post_with_relations(self, post_id: str):
        """Get post with populated author and category."""
        try:
            # Get the main post
            post = await PostDocument.get(id=post_id)
            
            # Get related documents
            author = await UserDocument.get(id=post.author_id) if post.author_id else None
            category = await CategoryDocument.get(id=post.category_id) if post.category_id else None
            
            # Build response with relations
            return {
                'post': post.to_dict(),
                'author': author.to_dict() if author else None,
                'category': category.to_dict() if category else None
            }
            
        except Exception as e:
            return None
    
    async def search_posts_with_authors(self, query: str):
        """Search posts and include author information."""
        from elasticsearch_dsl import AsyncSearch
        
        # Search posts
        search = AsyncSearch(index='posts')
        search = search.query('match', title=query)
        post_results = await search.execute()
        
        # Get unique author IDs
        author_ids = list(set(
            hit.author_id for hit in post_results.hits 
            if hasattr(hit, 'author_id') and hit.author_id
        ))
        
        # Bulk get authors
        authors = {}
        if author_ids:
            author_search = AsyncSearch(index='users')
            author_search = author_search.filter('terms', _id=author_ids)
            author_results = await author_search.execute()
            
            authors = {
                hit.meta.id: hit.to_dict() 
                for hit in author_results.hits
            }
        
        # Combine results
        posts_with_authors = []
        for hit in post_results.hits:
            post_dict = hit.to_dict()
            post_dict['author'] = authors.get(hit.author_id) if hasattr(hit, 'author_id') else None
            posts_with_authors.append(post_dict)
        
        return posts_with_authors

# Usage
content_service = ContentService()

async def relationship_examples():
    # Create related documents
    user = UserDocument(username='johndoe', email='john@example.com', full_name='John Doe')
    await user.save()
    
    category = CategoryDocument(name='Technology', description='Tech-related posts')
    await category.save()
    
    post = PostDocument(
        title='FastAPI Best Practices',
        content='Here are some best practices...',
        author_id=user.meta.id,
        category_id=category.meta.id
    )
    await post.save()
    
    # Query with relationships
    post_with_relations = await content_service.get_post_with_relations(post.meta.id)
    search_results = await content_service.search_posts_with_authors('FastAPI')
    
    return {
        'post_with_relations': post_with_relations,
        'search_results': search_results
    }
```

## Migration Patterns

### Schema Evolution
```python
class DocumentMigration:
    """Handle document schema migrations."""
    
    @staticmethod
    async def migrate_v1_to_v2():
        """Migrate from version 1 to version 2 schema."""
        from elasticsearch_dsl import AsyncSearch
        from elasticsearch.helpers import async_bulk
        from elasticsearch_dsl.connections import connections
        
        client = connections.get_connection()
        
        # Create new index with v2 schema
        await BlogPostV2.init()
        
        # Scroll through old documents
        search = AsyncSearch(index='blog_posts_v1')
        search = search.params(scroll='5m', size=100)
        
        async def migrate_batch():
            actions = []
            async for hit in search.scan():
                # Transform old format to new format
                new_doc = {
                    '_index': 'blog_posts_v2',
                    '_source': {
                        'title': hit.title,
                        'content': hit.content,
                        'author': hit.author,
                        'tags': hit.tags if hasattr(hit, 'tags') else [],
                        'metadata': {  # New nested field
                            'word_count': len(hit.content.split()) if hit.content else 0,
                            'reading_time': len(hit.content.split()) // 200 if hit.content else 0,
                            'migrated_from': 'v1',
                            'migration_date': datetime.utcnow().isoformat()
                        }
                    }
                }
                actions.append(new_doc)
                
                # Process in batches
                if len(actions) >= 100:
                    success, failed = await async_bulk(client, actions)
                    print(f"Migrated batch: {success} successful, {len(failed)} failed")
                    actions = []
            
            # Process remaining documents
            if actions:
                success, failed = await async_bulk(client, actions)
                print(f"Final batch: {success} successful, {len(failed)} failed")
        
        await migrate_batch()
        
        # Update alias to point to new index
        await client.indices.update_aliases(body={
            'actions': [
                {'remove': {'index': 'blog_posts_v1', 'alias': 'blog_posts'}},
                {'add': {'index': 'blog_posts_v2', 'alias': 'blog_posts'}}
            ]
        })

class BlogPostV2(AsyncDocument):
    """Version 2 of blog post with enhanced schema."""
    
    title = Text(analyzer='english', boost=2.0)
    content = Text(analyzer='english')
    author = Keyword()
    tags = Keyword(multi=True)
    
    # New nested metadata field
    metadata = Object(
        properties={
            'word_count': Integer(),
            'reading_time': Integer(),  # minutes
            'migrated_from': Keyword(),
            'migration_date': Date()
        }
    )
    
    class Index:
        name = 'blog_posts_v2'
```

## Next Steps

1. **[Async Document Operations](02_async-document-operations.md)** - CRUD operations with async patterns
2. **[Index Management](03_index-management.md)** - Lifecycle and schema management
3. **[Query Builder Patterns](../03-fastapi-integration/01_query-builder-patterns.md)** - Building dynamic queries

## Additional Resources

- **Elasticsearch Mapping**: [elastic.co/guide/en/elasticsearch/reference/current/mapping.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html)
- **Elasticsearch-DSL Documents**: [elasticsearch-dsl.readthedocs.io/en/latest/persistence.html](https://elasticsearch-dsl.readthedocs.io/en/latest/persistence.html)
- **Field Types Reference**: [elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping-types.html)