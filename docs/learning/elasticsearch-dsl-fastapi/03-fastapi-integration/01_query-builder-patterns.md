# Query Builder Patterns

Advanced patterns for building dynamic, type-safe Elasticsearch queries in FastAPI applications with async/await support and request parameter integration.

## Table of Contents
- [Dynamic Query Construction](#dynamic-query-construction)
- [Query Builder Classes](#query-builder-classes)
- [Request Parameter Integration](#request-parameter-integration)
- [Complex Search Scenarios](#complex-search-scenarios)
- [Performance Optimization](#performance-optimization)
- [Error Handling](#error-handling)
- [Testing Patterns](#testing-patterns)
- [Next Steps](#next-steps)

## Dynamic Query Construction

### FastAPI Request Parameter Mapping

Build Elasticsearch queries dynamically from FastAPI request parameters with full type safety and validation.

```python
from fastapi import FastAPI, Query, Depends
from elasticsearch_dsl import AsyncSearch, Q
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

app = FastAPI()

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SearchParams(BaseModel):
    q: str = Field(..., description="Search query text")
    category: Optional[str] = Field(None, description="Product category filter")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    sort_by: Optional[str] = Field("_score", description="Sort field")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Results per page")

@app.get("/products/search")
async def search_products(params: SearchParams = Depends()):
    """Dynamic search with request parameter mapping"""
    search = AsyncSearch(index='products')
    
    # Build query from parameters
    query_builder = ProductQueryBuilder(search)
    
    # Apply search text
    if params.q:
        query_builder.with_text_search(params.q)
    
    # Apply filters
    if params.category:
        query_builder.with_category_filter(params.category)
    
    if params.price_min is not None or params.price_max is not None:
        query_builder.with_price_range(params.price_min, params.price_max)
    
    if params.tags:
        query_builder.with_tags_filter(params.tags)
    
    # Apply sorting and pagination
    query_builder.with_sorting(params.sort_by, params.sort_order)
    query_builder.with_pagination(params.page, params.size)
    
    # Execute search
    response = await query_builder.execute()
    
    return {
        "total": response.hits.total.value,
        "page": params.page,
        "size": params.size,
        "products": [hit.to_dict() for hit in response.hits]
    }
```

### Conditional Query Building

```python
class ConditionalSearchBuilder:
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
        self.has_query = False
        self.filters = []
    
    def add_text_search(self, text: str, fields: List[str] = None):
        """Add text search if text is provided"""
        if not text or not text.strip():
            return self
        
        fields = fields or ['name^2', 'description', 'category']
        
        query = Q('multi_match', 
                 query=text.strip(),
                 fields=fields,
                 type='best_fields',
                 operator='and',
                 minimum_should_match='75%')
        
        if self.has_query:
            # Combine with existing query using bool should
            self.search = self.search.query('bool', must=[query])
        else:
            self.search = self.search.query(query)
            self.has_query = True
        
        return self
    
    def add_filter_if_present(self, field: str, value, filter_type: str = 'term'):
        """Add filter only if value is present and valid"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return self
        
        if filter_type == 'term':
            filter_query = Q('term', **{field: value})
        elif filter_type == 'range':
            filter_query = Q('range', **{field: value})
        elif filter_type == 'terms':
            filter_query = Q('terms', **{field: value})
        else:
            raise ValueError(f"Unsupported filter type: {filter_type}")
        
        self.filters.append(filter_query)
        return self
    
    def add_range_filter(self, field: str, min_val=None, max_val=None):
        """Add range filter if either min or max is specified"""
        if min_val is None and max_val is None:
            return self
        
        range_params = {}
        if min_val is not None:
            range_params['gte'] = min_val
        if max_val is not None:
            range_params['lte'] = max_val
        
        return self.add_filter_if_present(field, range_params, 'range')
    
    def apply_filters(self):
        """Apply all accumulated filters"""
        if self.filters:
            if self.has_query:
                # Add filters to existing query
                current_query = self.search.to_dict()['query']
                self.search = self.search.query('bool', 
                                               must=[current_query],
                                               filter=self.filters)
            else:
                # Only filters, no query
                self.search = self.search.query('bool', filter=self.filters)
        
        return self
    
    async def execute(self):
        """Execute the search with all applied conditions"""
        self.apply_filters()
        return await self.search.execute()

# Usage example
@app.get("/products/advanced-search")
async def advanced_search(
    q: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    in_stock: Optional[bool] = None,
    tags: Optional[List[str]] = Query(None)
):
    """Advanced search with conditional query building"""
    builder = ConditionalSearchBuilder('products')
    
    # Add search conditions
    builder.add_text_search(q, ['name^3', 'description^2', 'category'])
    builder.add_filter_if_present('category', category)
    builder.add_filter_if_present('brand', brand)
    builder.add_range_filter('price', price_min, price_max)
    
    if in_stock is not None:
        builder.add_filter_if_present('in_stock', in_stock)
    
    if tags:
        builder.add_filter_if_present('tags', tags, 'terms')
    
    response = await builder.execute()
    
    return {
        "total": response.hits.total.value,
        "products": [hit.to_dict() for hit in response.hits]
    }
```

## Query Builder Classes

### Fluent Interface Pattern

```python
from elasticsearch_dsl import AsyncSearch, Q, A
from typing import Dict, Any, List, Union
import logging

logger = logging.getLogger(__name__)

class FluentSearchBuilder:
    """Fluent interface for building complex Elasticsearch queries"""
    
    def __init__(self, index: str, using=None):
        self.search = AsyncSearch(index=index, using=using)
        self._aggregations = {}
        self._highlighting = {}
        self._source_fields = None
        
    def query(self, query_type: str, **params) -> 'FluentSearchBuilder':
        """Add a query to the search"""
        self.search = self.search.query(query_type, **params)
        return self
    
    def filter(self, filter_type: str, **params) -> 'FluentSearchBuilder':
        """Add a filter to the search"""
        self.search = self.search.filter(filter_type, **params)
        return self
    
    def exclude(self, filter_type: str, **params) -> 'FluentSearchBuilder':
        """Add an exclusion filter"""
        self.search = self.search.exclude(filter_type, **params)
        return self
    
    def sort(self, *fields) -> 'FluentSearchBuilder':
        """Add sorting to the search"""
        self.search = self.search.sort(*fields)
        return self
    
    def slice(self, start: int, end: int = None) -> 'FluentSearchBuilder':
        """Add pagination"""
        if end is None:
            self.search = self.search[start:]
        else:
            self.search = self.search[start:end]
        return self
    
    def source(self, fields: Union[List[str], bool]) -> 'FluentSearchBuilder':
        """Specify which fields to return"""
        self._source_fields = fields
        self.search = self.search.source(fields)
        return self
    
    def highlight(self, *fields, **params) -> 'FluentSearchBuilder':
        """Add highlighting"""
        self.search = self.search.highlight(*fields, **params)
        self._highlighting = {
            'fields': fields,
            'params': params
        }
        return self
    
    def aggregate(self, name: str, agg_type: str, **params) -> 'FluentSearchBuilder':
        """Add aggregation"""
        agg = A(agg_type, **params)
        self.search.aggs.bucket(name, agg)
        self._aggregations[name] = {'type': agg_type, 'params': params}
        return self
    
    def boost_query(self, query_type: str, boost: float, **params) -> 'FluentSearchBuilder':
        """Add a boosted query"""
        boosted_query = Q(query_type, **params)
        boosted_query = boosted_query.to_dict()
        boosted_query[query_type]['boost'] = boost
        
        self.search = self.search.query(Q(boosted_query))
        return self
    
    def function_score(self, functions: List[Dict], **params) -> 'FluentSearchBuilder':
        """Add function score query"""
        self.search = self.search.query('function_score', 
                                       functions=functions, 
                                       **params)
        return self
    
    def multi_match(self, query: str, fields: List[str], **params) -> 'FluentSearchBuilder':
        """Convenience method for multi-match queries"""
        return self.query('multi_match', 
                         query=query, 
                         fields=fields, 
                         **params)
    
    def bool_query(self) -> 'BoolQueryBuilder':
        """Start building a bool query"""
        return BoolQueryBuilder(self)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return self.search.to_dict()
    
    async def execute(self) -> Any:
        """Execute the search"""
        try:
            logger.info(f"Executing search: {self.search.to_dict()}")
            response = await self.search.execute()
            logger.info(f"Search completed: {response.hits.total.value} results")
            return response
        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            raise
    
    async def count(self) -> int:
        """Get only the count of results"""
        return await self.search.count()

class BoolQueryBuilder:
    """Builder for complex boolean queries"""
    
    def __init__(self, parent_builder: FluentSearchBuilder):
        self.parent = parent_builder
        self.must_queries = []
        self.should_queries = []
        self.must_not_queries = []
        self.filter_queries = []
        self.minimum_should_match = None
        self.boost = None
    
    def must(self, query_type: str, **params) -> 'BoolQueryBuilder':
        """Add must clause"""
        self.must_queries.append(Q(query_type, **params))
        return self
    
    def should(self, query_type: str, **params) -> 'BoolQueryBuilder':
        """Add should clause"""
        self.should_queries.append(Q(query_type, **params))
        return self
    
    def must_not(self, query_type: str, **params) -> 'BoolQueryBuilder':
        """Add must_not clause"""
        self.must_not_queries.append(Q(query_type, **params))
        return self
    
    def filter(self, filter_type: str, **params) -> 'BoolQueryBuilder':
        """Add filter clause"""
        self.filter_queries.append(Q(filter_type, **params))
        return self
    
    def minimum_should_match(self, value: Union[int, str]) -> 'BoolQueryBuilder':
        """Set minimum_should_match parameter"""
        self.minimum_should_match = value
        return self
    
    def boost(self, boost_value: float) -> 'BoolQueryBuilder':
        """Set boost for the bool query"""
        self.boost = boost_value
        return self
    
    def build(self) -> FluentSearchBuilder:
        """Build the bool query and return to parent builder"""
        bool_params = {}
        
        if self.must_queries:
            bool_params['must'] = self.must_queries
        if self.should_queries:
            bool_params['should'] = self.should_queries
        if self.must_not_queries:
            bool_params['must_not'] = self.must_not_queries
        if self.filter_queries:
            bool_params['filter'] = self.filter_queries
        if self.minimum_should_match is not None:
            bool_params['minimum_should_match'] = self.minimum_should_match
        if self.boost is not None:
            bool_params['boost'] = self.boost
        
        self.parent.search = self.parent.search.query('bool', **bool_params)
        return self.parent

# Usage examples
@app.get("/products/fluent-search")
async def fluent_search_example():
    """Example using fluent search builder"""
    builder = FluentSearchBuilder('products')
    
    # Build complex search with fluent interface
    search_results = await (
        builder
        .multi_match('laptop computer', ['name^3', 'description^2'])
        .filter('range', price={'gte': 500, 'lte': 2000})
        .filter('term', category='electronics')
        .exclude('term', discontinued=True)
        .sort('-price', '_score')
        .highlight('name', 'description', 
                  fragment_size=150, 
                  number_of_fragments=3)
        .aggregate('price_ranges', 'range', 
                  field='price',
                  ranges=[
                      {'to': 500},
                      {'from': 500, 'to': 1000},
                      {'from': 1000, 'to': 2000},
                      {'from': 2000}
                  ])
        .source(['name', 'price', 'category', 'rating'])
        .slice(0, 20)
        .execute()
    )
    
    return {
        "total": search_results.hits.total.value,
        "products": [hit.to_dict() for hit in search_results.hits],
        "aggregations": search_results.aggregations.to_dict(),
        "max_score": search_results.hits.max_score
    }

@app.get("/products/bool-search")
async def bool_search_example():
    """Example using bool query builder"""
    builder = FluentSearchBuilder('products')
    
    search_results = await (
        builder
        .bool_query()
        .must('multi_match', query='gaming laptop', fields=['name', 'description'])
        .should('match', brand='dell')
        .should('match', brand='lenovo')
        .must_not('term', discontinued=True)
        .filter('range', price={'gte': 800})
        .filter('term', category='electronics')
        .minimum_should_match(1)
        .boost(1.2)
        .build()
        .sort('-rating', '-price')
        .slice(0, 10)
        .execute()
    )
    
    return {
        "total": search_results.hits.total.value,
        "products": [hit.to_dict() for hit in search_results.hits]
    }
```

## Request Parameter Integration

### Advanced Parameter Validation

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class AdvancedSearchRequest(BaseModel):
    # Text search parameters
    query: Optional[str] = Field(None, description="Main search query")
    query_fields: List[str] = Field(['name', 'description'], description="Fields to search")
    operator: str = Field('and', regex='^(and|or)$', description="Query operator")
    
    # Filter parameters
    category: Optional[str] = None
    brand: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None
    date_range: Optional[Dict[str, datetime]] = None
    tags: List[str] = Field(default_factory=list)
    
    # Search behavior
    fuzzy: bool = Field(False, description="Enable fuzzy matching")
    minimum_should_match: Optional[str] = Field(None, description="Minimum match criteria")
    
    # Results formatting
    sort_by: str = Field('_score', description="Sort field")
    sort_order: str = Field('desc', regex='^(asc|desc)$')
    include_fields: Optional[List[str]] = None
    exclude_fields: Optional[List[str]] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)
    
    # Aggregations
    include_aggregations: bool = Field(False)
    aggregation_fields: List[str] = Field(default_factory=list)
    
    @validator('price_range')
    def validate_price_range(cls, v):
        if v is None:
            return v
        
        if 'min' in v and 'max' in v and v['min'] > v['max']:
            raise ValueError('Minimum price cannot be greater than maximum price')
        
        return v
    
    @validator('query_fields')
    def validate_query_fields(cls, v):
        allowed_fields = ['name', 'description', 'category', 'brand', 'tags']
        invalid_fields = [f for f in v if f not in allowed_fields]
        if invalid_fields:
            raise ValueError(f'Invalid query fields: {invalid_fields}')
        return v
    
    @root_validator
    def validate_search_requirements(cls, values):
        query = values.get('query')
        category = values.get('category')
        brand = values.get('brand')
        tags = values.get('tags', [])
        
        # At least one search criterion is required
        if not any([query, category, brand, tags]):
            raise ValueError('At least one search criterion is required')
        
        return values

class SearchQueryFactory:
    """Factory for creating search queries from request parameters"""
    
    @staticmethod
    def create_search_from_request(request: AdvancedSearchRequest) -> FluentSearchBuilder:
        """Create a FluentSearchBuilder from request parameters"""
        builder = FluentSearchBuilder('products')
        
        # Add main query if present
        if request.query:
            if request.fuzzy:
                builder.query('multi_match', 
                            query=request.query,
                            fields=request.query_fields,
                            fuzziness='AUTO',
                            operator=request.operator)
            else:
                builder.multi_match(request.query, 
                                   request.query_fields,
                                   operator=request.operator)
        
        # Add filters
        SearchQueryFactory._add_filters(builder, request)
        
        # Add sorting
        SearchQueryFactory._add_sorting(builder, request)
        
        # Add field selection
        SearchQueryFactory._add_field_selection(builder, request)
        
        # Add pagination
        start = (request.page - 1) * request.size
        builder.slice(start, start + request.size)
        
        # Add aggregations
        if request.include_aggregations:
            SearchQueryFactory._add_aggregations(builder, request)
        
        return builder
    
    @staticmethod
    def _add_filters(builder: FluentSearchBuilder, request: AdvancedSearchRequest):
        """Add filters to the search builder"""
        if request.category:
            builder.filter('term', category=request.category)
        
        if request.brand:
            builder.filter('term', brand=request.brand)
        
        if request.tags:
            builder.filter('terms', tags=request.tags)
        
        if request.price_range:
            range_filter = {}
            if 'min' in request.price_range:
                range_filter['gte'] = request.price_range['min']
            if 'max' in request.price_range:
                range_filter['lte'] = request.price_range['max']
            builder.filter('range', price=range_filter)
        
        if request.date_range:
            date_filter = {}
            if 'from' in request.date_range:
                date_filter['gte'] = request.date_range['from']
            if 'to' in request.date_range:
                date_filter['lte'] = request.date_range['to']
            builder.filter('range', created_date=date_filter)
    
    @staticmethod
    def _add_sorting(builder: FluentSearchBuilder, request: AdvancedSearchRequest):
        """Add sorting to the search builder"""
        if request.sort_by == '_score':
            if request.sort_order == 'asc':
                builder.sort('_score')
            else:
                builder.sort('-_score')
        else:
            sort_field = request.sort_by
            if request.sort_order == 'desc':
                sort_field = f'-{sort_field}'
            builder.sort(sort_field)
    
    @staticmethod
    def _add_field_selection(builder: FluentSearchBuilder, request: AdvancedSearchRequest):
        """Add field selection to the search builder"""
        if request.include_fields:
            builder.source(request.include_fields)
        elif request.exclude_fields:
            # Get all available fields and exclude specified ones
            all_fields = True  # This would normally come from mapping
            builder.source(all_fields)
            for field in request.exclude_fields:
                builder.source([f"!{field}"])
    
    @staticmethod
    def _add_aggregations(builder: FluentSearchBuilder, request: AdvancedSearchRequest):
        """Add aggregations to the search builder"""
        for field in request.aggregation_fields:
            if field in ['category', 'brand']:
                builder.aggregate(f'{field}_terms', 'terms', field=field, size=10)
            elif field == 'price':
                builder.aggregate('price_ranges', 'range', 
                                field='price',
                                ranges=[
                                    {'to': 100},
                                    {'from': 100, 'to': 500},
                                    {'from': 500, 'to': 1000},
                                    {'from': 1000}
                                ])

@app.post("/products/advanced-search", response_model=Dict[str, Any])
async def advanced_search_endpoint(request: AdvancedSearchRequest):
    """Advanced search endpoint with comprehensive parameter handling"""
    try:
        # Create search from request
        builder = SearchQueryFactory.create_search_from_request(request)
        
        # Execute search
        response = await builder.execute()
        
        # Format response
        result = {
            "total": response.hits.total.value,
            "page": request.page,
            "size": request.size,
            "max_score": response.hits.max_score,
            "products": []
        }
        
        # Add products
        for hit in response.hits:
            product = hit.to_dict()
            product['_id'] = hit.meta.id
            product['_score'] = hit.meta.score
            
            # Add highlights if present
            if hasattr(hit.meta, 'highlight'):
                product['_highlights'] = hit.meta.highlight.to_dict()
            
            result['products'].append(product)
        
        # Add aggregations if requested
        if request.include_aggregations and hasattr(response, 'aggregations'):
            result['aggregations'] = response.aggregations.to_dict()
        
        return result
        
    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

## Complex Search Scenarios

### Multi-Index Search with Routing

```python
from elasticsearch_dsl import MultiSearch, AsyncSearch
from typing import Dict, List, Any
import asyncio

class MultiIndexSearchBuilder:
    """Builder for searching across multiple indices"""
    
    def __init__(self, using=None):
        self.using = using
        self.searches = []
        self.index_configs = {}
    
    def add_index_search(self, 
                        index: str, 
                        query_config: Dict[str, Any],
                        weight: float = 1.0,
                        transform_func=None) -> 'MultiIndexSearchBuilder':
        """Add a search for a specific index"""
        search = AsyncSearch(index=index, using=self.using)
        
        # Apply query configuration
        if 'query' in query_config:
            search = search.query(**query_config['query'])
        
        if 'filters' in query_config:
            for filter_config in query_config['filters']:
                search = search.filter(**filter_config)
        
        if 'sort' in query_config:
            search = search.sort(*query_config['sort'])
        
        if 'size' in query_config:
            search = search[:query_config['size']]
        
        self.searches.append(search)
        self.index_configs[index] = {
            'weight': weight,
            'transform_func': transform_func
        }
        
        return self
    
    async def execute_parallel(self) -> Dict[str, Any]:
        """Execute all searches in parallel"""
        tasks = [search.execute() for search in self.searches]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        for i, response in enumerate(responses):
            index_name = self.searches[i]._index[0]
            
            if isinstance(response, Exception):
                results[index_name] = {'error': str(response)}
            else:
                config = self.index_configs[index_name]
                
                # Apply transformation if specified
                if config.get('transform_func'):
                    transformed_hits = [
                        config['transform_func'](hit) 
                        for hit in response.hits
                    ]
                else:
                    transformed_hits = [hit.to_dict() for hit in response.hits]
                
                results[index_name] = {
                    'total': response.hits.total.value,
                    'max_score': response.hits.max_score,
                    'weight': config['weight'],
                    'hits': transformed_hits
                }
        
        return results
    
    def merge_results(self, results: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        """Merge and rank results from multiple indices"""
        all_hits = []
        
        for index_name, index_results in results.items():
            if 'error' in index_results:
                continue
            
            weight = index_results['weight']
            max_score = index_results.get('max_score', 1.0)
            
            for hit in index_results['hits']:
                # Apply index-specific scoring
                original_score = hit.get('_score', 0)
                normalized_score = (original_score / max_score) if max_score > 0 else 0
                weighted_score = normalized_score * weight
                
                hit['_normalized_score'] = normalized_score
                hit['_weighted_score'] = weighted_score
                hit['_source_index'] = index_name
                
                all_hits.append(hit)
        
        # Sort by weighted score
        all_hits.sort(key=lambda x: x['_weighted_score'], reverse=True)
        
        return all_hits[:limit]

@app.get("/search/federated")
async def federated_search(
    q: str,
    categories: List[str] = Query(default_factory=list),
    limit: int = 20
):
    """Search across multiple product indices"""
    builder = MultiIndexSearchBuilder()
    
    # Search products index
    builder.add_index_search(
        'products',
        {
            'query': {'multi_match': {
                'query': q,
                'fields': ['name^3', 'description^2'],
                'type': 'best_fields'
            }},
            'filters': [{'terms': {'category': categories}}] if categories else [],
            'sort': ['_score'],
            'size': limit
        },
        weight=1.0,
        transform_func=lambda hit: {
            **hit.to_dict(),
            'type': 'product',
            '_id': hit.meta.id,
            '_score': hit.meta.score
        }
    )
    
    # Search articles index
    builder.add_index_search(
        'articles',
        {
            'query': {'multi_match': {
                'query': q,
                'fields': ['title^3', 'content^1'],
                'type': 'best_fields'
            }},
            'sort': ['_score'],
            'size': int(limit * 0.3)  # Fewer articles
        },
        weight=0.8,
        transform_func=lambda hit: {
            **hit.to_dict(),
            'type': 'article',
            '_id': hit.meta.id,
            '_score': hit.meta.score
        }
    )
    
    # Execute searches
    results = await builder.execute_parallel()
    
    # Merge and return results
    merged_results = builder.merge_results(results, limit)
    
    return {
        'total_sources': len([r for r in results.values() if 'error' not in r]),
        'results': merged_results,
        'source_breakdown': {
            index: {
                'total': data.get('total', 0),
                'max_score': data.get('max_score', 0),
                'error': data.get('error')
            }
            for index, data in results.items()
        }
    }
```

## Performance Optimization

### Query Caching and Optimization

```python
import hashlib
import json
from functools import wraps
from typing import Optional, Dict, Any
import redis
import pickle

class QueryCache:
    """Redis-based query result caching"""
    
    def __init__(self, redis_client, default_ttl: int = 300):
        self.redis = redis_client
        self.default_ttl = default_ttl
    
    def _generate_cache_key(self, query_dict: Dict[str, Any], prefix: str = "search") -> str:
        """Generate cache key from query dictionary"""
        query_str = json.dumps(query_dict, sort_keys=True)
        query_hash = hashlib.md5(query_str.encode()).hexdigest()
        return f"{prefix}:{query_hash}"
    
    async def get(self, cache_key: str) -> Optional[Any]:
        """Get cached result"""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    async def set(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Set cached result"""
        try:
            ttl = ttl or self.default_ttl
            serialized_data = pickle.dumps(data)
            await self.redis.setex(cache_key, ttl, serialized_data)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
        return False

def cached_search(cache: QueryCache, ttl: int = 300):
    """Decorator for caching search results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            cache_key = cache._generate_cache_key(cache_data)
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            logger.info(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

class OptimizedSearchBuilder(FluentSearchBuilder):
    """Search builder with performance optimizations"""
    
    def __init__(self, index: str, using=None, cache: QueryCache = None):
        super().__init__(index, using)
        self.cache = cache
        self._request_cache = True
        self._preference = None
        self._routing = None
    
    def with_request_cache(self, enabled: bool = True) -> 'OptimizedSearchBuilder':
        """Enable/disable Elasticsearch request cache"""
        self._request_cache = enabled
        return self
    
    def with_preference(self, preference: str) -> 'OptimizedSearchBuilder':
        """Set search preference for consistent shard routing"""
        self._preference = preference
        return self
    
    def with_routing(self, routing: str) -> 'OptimizedSearchBuilder':
        """Set routing for targeted shard search"""
        self._routing = routing
        return self
    
    def optimize_for_count(self) -> 'OptimizedSearchBuilder':
        """Optimize query for count operations"""
        self.search = self.search.extra(
            terminate_after=1,
            timeout='1s'
        )
        return self
    
    def optimize_for_aggregations(self) -> 'OptimizedSearchBuilder':
        """Optimize query for aggregation-focused searches"""
        self.search = self.search[:0]  # No hits needed
        return self
    
    async def execute_cached(self, ttl: int = 300) -> Any:
        """Execute search with caching"""
        if not self.cache:
            return await self.execute()
        
        # Generate cache key
        query_dict = self.search.to_dict()
        if self._preference:
            query_dict['preference'] = self._preference
        if self._routing:
            query_dict['routing'] = self._routing
        
        cache_key = self.cache._generate_cache_key(query_dict, "optimized_search")
        
        # Try cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute search with optimizations
        search = self.search
        
        if self._request_cache:
            search = search.extra(request_cache=True)
        
        if self._preference:
            search = search.extra(preference=self._preference)
        
        if self._routing:
            search = search.extra(routing=self._routing)
        
        result = await search.execute()
        
        # Cache result
        await self.cache.set(cache_key, result, ttl)
        
        return result

# Usage example
@app.get("/products/optimized-search")
async def optimized_search(
    q: str,
    user_id: Optional[str] = None,
    cache_ttl: int = 300
):
    """Search with performance optimizations"""
    builder = OptimizedSearchBuilder('products', cache=query_cache)
    
    # Build optimized search
    search_result = await (
        builder
        .multi_match(q, ['name^3', 'description^2'])
        .filter('term', active=True)
        .with_request_cache(True)
        .with_preference(user_id or 'default')  # Consistent routing
        .sort('_score', 'popularity')
        .slice(0, 20)
        .execute_cached(ttl=cache_ttl)
    )
    
    return {
        "total": search_result.hits.total.value,
        "products": [hit.to_dict() for hit in search_result.hits],
        "took_ms": search_result.took
    }
```

## Error Handling

### Comprehensive Error Management

```python
from elasticsearch_dsl.exceptions import ElasticsearchException
from fastapi import HTTPException
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SearchError(Exception):
    """Base class for search-related errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class SearchValidationError(SearchError):
    """Error for invalid search parameters"""
    pass

class SearchExecutionError(SearchError):
    """Error during search execution"""
    pass

class SearchTimeoutError(SearchError):
    """Error for search timeouts"""
    pass

class ErrorHandlingSearchBuilder(FluentSearchBuilder):
    """Search builder with comprehensive error handling"""
    
    def __init__(self, index: str, using=None, timeout: str = "30s"):
        super().__init__(index, using)
        self.timeout = timeout
        self._validations = []
    
    def add_validation(self, validator_func, error_message: str):
        """Add custom validation"""
        self._validations.append((validator_func, error_message))
        return self
    
    def validate(self) -> None:
        """Run all validations"""
        for validator_func, error_message in self._validations:
            if not validator_func(self.search):
                raise SearchValidationError(error_message)
    
    async def safe_execute(self) -> Dict[str, Any]:
        """Execute search with comprehensive error handling"""
        try:
            # Run validations
            self.validate()
            
            # Add timeout
            search = self.search.extra(timeout=self.timeout)
            
            # Execute
            response = await search.execute()
            
            return {
                'success': True,
                'data': {
                    'total': response.hits.total.value,
                    'hits': [hit.to_dict() for hit in response.hits],
                    'took': response.took,
                    'max_score': response.hits.max_score
                },
                'metadata': {
                    'query': search.to_dict(),
                    'index': self.search._index[0] if self.search._index else None
                }
            }
            
        except SearchValidationError as e:
            logger.warning(f"Search validation failed: {e.message}")
            return {
                'success': False,
                'error': {
                    'type': 'validation_error',
                    'message': e.message,
                    'details': e.details
                }
            }
            
        except ElasticsearchException as e:
            # Handle Elasticsearch-specific errors
            error_type = type(e).__name__
            
            if 'timeout' in str(e).lower():
                logger.error(f"Search timeout: {e}")
                return {
                    'success': False,
                    'error': {
                        'type': 'timeout_error',
                        'message': 'Search request timed out',
                        'details': {'timeout': self.timeout}
                    }
                }
            
            logger.error(f"Elasticsearch error ({error_type}): {e}")
            return {
                'success': False,
                'error': {
                    'type': 'elasticsearch_error',
                    'message': str(e),
                    'details': {'error_type': error_type}
                }
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return {
                'success': False,
                'error': {
                    'type': 'internal_error',
                    'message': 'An unexpected error occurred',
                    'details': {}
                }
            }

@app.exception_handler(SearchError)
async def search_error_handler(request, exc: SearchError):
    """Global exception handler for search errors"""
    logger.error(f"Search error: {exc.message}", extra=exc.details)
    
    status_code = 400
    if isinstance(exc, SearchTimeoutError):
        status_code = 408
    elif isinstance(exc, SearchExecutionError):
        status_code = 500
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": type(exc).__name__,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

@app.get("/products/safe-search")
async def safe_search_endpoint(
    q: str,
    category: Optional[str] = None,
    max_results: int = 50
):
    """Search endpoint with comprehensive error handling"""
    builder = ErrorHandlingSearchBuilder('products', timeout="10s")
    
    # Add custom validations
    builder.add_validation(
        lambda search: len(q.strip()) >= 2,
        "Query must be at least 2 characters long"
    )
    
    builder.add_validation(
        lambda search: max_results <= 100,
        "Maximum results cannot exceed 100"
    )
    
    # Build search
    builder.multi_match(q, ['name^3', 'description^2'])
    
    if category:
        builder.filter('term', category=category)
    
    builder.slice(0, max_results)
    
    # Execute with error handling
    result = await builder.safe_execute()
    
    if not result['success']:
        error = result['error']
        
        if error['type'] == 'validation_error':
            raise HTTPException(status_code=400, detail=error['message'])
        elif error['type'] == 'timeout_error':
            raise HTTPException(status_code=408, detail=error['message'])
        else:
            raise HTTPException(status_code=500, detail="Search failed")
    
    return result['data']
```

## Testing Patterns

### Query Builder Testing

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from elasticsearch_dsl import AsyncSearch, Response

class TestFluentSearchBuilder:
    """Test cases for FluentSearchBuilder"""
    
    @pytest.fixture
    def mock_response(self):
        """Mock Elasticsearch response"""
        response = MagicMock(spec=Response)
        response.hits.total.value = 10
        response.hits.max_score = 2.5
        response.took = 15
        
        # Mock hits
        hit1 = MagicMock()
        hit1.to_dict.return_value = {'name': 'Product 1', 'price': 100}
        hit1.meta.id = '1'
        hit1.meta.score = 2.5
        
        hit2 = MagicMock()
        hit2.to_dict.return_value = {'name': 'Product 2', 'price': 200}
        hit2.meta.id = '2'
        hit2.meta.score = 2.0
        
        response.hits = [hit1, hit2]
        
        return response
    
    @pytest.fixture
    def builder(self):
        """Create a FluentSearchBuilder instance"""
        return FluentSearchBuilder('test_index')
    
    def test_query_building(self, builder):
        """Test basic query building"""
        result = (
            builder
            .multi_match('test query', ['name', 'description'])
            .filter('term', category='electronics')
            .sort('-price')
            .slice(0, 10)
        )
        
        query_dict = result.to_dict()
        
        assert 'query' in query_dict
        assert 'sort' in query_dict
        assert 'from' in query_dict
        assert 'size' in query_dict
        
        # Check query structure
        assert query_dict['query']['multi_match']['query'] == 'test query'
        assert 'name' in query_dict['query']['multi_match']['fields']
    
    def test_bool_query_building(self, builder):
        """Test bool query building"""
        result = (
            builder
            .bool_query()
            .must('match', name='laptop')
            .should('match', brand='dell')
            .must_not('term', discontinued=True)
            .filter('range', price={'gte': 100})
            .minimum_should_match(1)
            .build()
        )
        
        query_dict = result.to_dict()
        bool_query = query_dict['query']['bool']
        
        assert 'must' in bool_query
        assert 'should' in bool_query
        assert 'must_not' in bool_query
        assert 'filter' in bool_query
        assert bool_query['minimum_should_match'] == 1
    
    @pytest.mark.asyncio
    async def test_search_execution(self, builder, mock_response):
        """Test search execution with mocking"""
        # Mock the execute method
        builder.search.execute = AsyncMock(return_value=mock_response)
        
        result = await (
            builder
            .multi_match('test', ['name'])
            .execute()
        )
        
        assert result.hits.total.value == 10
        assert len(result.hits) == 2
        builder.search.execute.assert_called_once()

@pytest.mark.asyncio
async def test_search_endpoint(client):
    """Test search endpoint integration"""
    # Mock Elasticsearch response
    with patch('your_app.FluentSearchBuilder') as mock_builder:
        mock_instance = AsyncMock()
        mock_builder.return_value = mock_instance
        
        mock_response = MagicMock()
        mock_response.hits.total.value = 5
        mock_response.hits = []
        
        mock_instance.multi_match.return_value = mock_instance
        mock_instance.filter.return_value = mock_instance
        mock_instance.slice.return_value = mock_instance
        mock_instance.execute.return_value = mock_response
        
        # Test the endpoint
        response = await client.get("/products/search?q=test&category=electronics")
        
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'products' in data
```

## Next Steps

1. **[API Endpoint Design](02_api-endpoint-design.md)** - Learn RESTful search API patterns
2. **[Pydantic Integration](03_pydantic-integration.md)** - Master request/response validation
3. **[Dependency Injection](04_dependency-injection.md)** - Implement service architecture patterns
4. **[Advanced Search](../04-advanced-search/01_complex-queries.md)** - Build sophisticated search features

## Additional Resources

- **FastAPI Query Parameters**: [fastapi.tiangolo.com/tutorial/query-params](https://fastapi.tiangolo.com/tutorial/query-params/)
- **Elasticsearch Query DSL**: [elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- **Python Async Patterns**: [docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html)