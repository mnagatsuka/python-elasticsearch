# Complex Queries

Advanced patterns for building sophisticated Elasticsearch queries in FastAPI applications, including bool queries, nested searches, full-text search optimization, and multi-index operations with async/await support.

## Table of Contents
- [Bool Queries with Multiple Conditions](#bool-queries-with-multiple-conditions)
- [Nested and Parent-Child Queries](#nested-and-parent-child-queries)
- [Full-Text Search with Scoring](#full-text-search-with-scoring)
- [Multi-Index and Cross-Cluster Search](#multi-index-and-cross-cluster-search)
- [Query Optimization Techniques](#query-optimization-techniques)
- [Real-World Complex Scenarios](#real-world-complex-scenarios)
- [Performance Monitoring](#performance-monitoring)
- [Next Steps](#next-steps)

## Bool Queries with Multiple Conditions

### Advanced Bool Query Builder

```python
from fastapi import FastAPI, Query, HTTPException
from elasticsearch_dsl import AsyncSearch, Q
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

class BoolOperator(str, Enum):
    MUST = "must"
    SHOULD = "should"
    MUST_NOT = "must_not"
    FILTER = "filter"

class QueryClause(BaseModel):
    query_type: str = Field(..., description="Type of query (match, term, range, etc.)")
    field: str = Field(..., description="Field to query")
    value: Union[str, int, float, Dict[str, Any]] = Field(..., description="Query value")
    boost: Optional[float] = Field(None, description="Query boost factor")
    operator: BoolOperator = Field(BoolOperator.MUST, description="Bool operator")

class ComplexSearchRequest(BaseModel):
    clauses: List[QueryClause] = Field(..., description="List of query clauses")
    minimum_should_match: Optional[Union[int, str]] = Field(None, description="Minimum should match")
    boost: Optional[float] = Field(None, description="Overall query boost")
    
    # Scoring and relevance
    disable_coord: bool = Field(False, description="Disable coordination factor")
    tie_breaker: Optional[float] = Field(None, description="Tie breaker for dis_max queries")
    
    # Result configuration
    size: int = Field(10, ge=1, le=100)
    from_: int = Field(0, ge=0, alias="from")
    sort: Optional[List[str]] = Field(None, description="Sort fields")
    _source: Optional[List[str]] = Field(None, description="Fields to return")

class AdvancedBoolQueryBuilder:
    """Builder for complex bool queries with multiple conditions"""
    
    def __init__(self, index: str, using=None):
        self.search = AsyncSearch(index=index, using=using)
        self.must_clauses = []
        self.should_clauses = []
        self.must_not_clauses = []
        self.filter_clauses = []
        self.minimum_should_match = None
        self.boost = None
    
    def add_clause(self, clause: QueryClause) -> 'AdvancedBoolQueryBuilder':
        """Add a query clause to the appropriate bool section"""
        query = self._build_query_from_clause(clause)
        
        if clause.operator == BoolOperator.MUST:
            self.must_clauses.append(query)
        elif clause.operator == BoolOperator.SHOULD:
            self.should_clauses.append(query)
        elif clause.operator == BoolOperator.MUST_NOT:
            self.must_not_clauses.append(query)
        elif clause.operator == BoolOperator.FILTER:
            self.filter_clauses.append(query)
        
        return self
    
    def _build_query_from_clause(self, clause: QueryClause) -> Q:
        """Build Elasticsearch query from clause"""
        query_params = {}
        
        if clause.query_type == 'match':
            query_params[clause.field] = clause.value
        elif clause.query_type == 'term':
            query_params[clause.field] = clause.value
        elif clause.query_type == 'range':
            query_params[clause.field] = clause.value
        elif clause.query_type == 'wildcard':
            query_params[clause.field] = clause.value
        elif clause.query_type == 'fuzzy':
            query_params[clause.field] = clause.value
        elif clause.query_type == 'prefix':
            query_params[clause.field] = clause.value
        elif clause.query_type == 'multi_match':
            query_params['query'] = clause.value
            query_params['fields'] = [clause.field] if isinstance(clause.field, str) else clause.field
        else:
            raise ValueError(f"Unsupported query type: {clause.query_type}")
        
        # Add boost if specified
        if clause.boost:
            query_params['boost'] = clause.boost
        
        return Q(clause.query_type, **query_params)
    
    def with_minimum_should_match(self, value: Union[int, str]) -> 'AdvancedBoolQueryBuilder':
        """Set minimum should match parameter"""
        self.minimum_should_match = value
        return self
    
    def with_boost(self, boost: float) -> 'AdvancedBoolQueryBuilder':
        """Set overall query boost"""
        self.boost = boost
        return self
    
    def build_bool_query(self) -> Q:
        """Build the complete bool query"""
        bool_params = {}
        
        if self.must_clauses:
            bool_params['must'] = self.must_clauses
        if self.should_clauses:
            bool_params['should'] = self.should_clauses
        if self.must_not_clauses:
            bool_params['must_not'] = self.must_not_clauses
        if self.filter_clauses:
            bool_params['filter'] = self.filter_clauses
        if self.minimum_should_match is not None:
            bool_params['minimum_should_match'] = self.minimum_should_match
        if self.boost is not None:
            bool_params['boost'] = self.boost
        
        return Q('bool', **bool_params)
    
    def apply_query(self) -> 'AdvancedBoolQueryBuilder':
        """Apply the built bool query to the search"""
        bool_query = self.build_bool_query()
        self.search = self.search.query(bool_query)
        return self
    
    def configure_results(self, request: ComplexSearchRequest) -> 'AdvancedBoolQueryBuilder':
        """Configure result settings"""
        # Pagination
        self.search = self.search[request.from_:request.from_ + request.size]
        
        # Sorting
        if request.sort:
            self.search = self.search.sort(*request.sort)
        
        # Source filtering
        if request._source:
            self.search = self.search.source(request._source)
        
        return self
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the search and return formatted results"""
        try:
            response = await self.search.execute()
            
            return {
                'total': response.hits.total.value,
                'max_score': response.hits.max_score,
                'took': response.took,
                'hits': [
                    {
                        '_id': hit.meta.id,
                        '_score': hit.meta.score,
                        '_source': hit.to_dict()
                    }
                    for hit in response.hits
                ],
                'query': self.search.to_dict()
            }
        except Exception as e:
            logger.error(f"Complex query execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/search/complex-bool")
async def complex_bool_search(request: ComplexSearchRequest):
    """Execute complex bool query with multiple conditions"""
    builder = AdvancedBoolQueryBuilder('products')
    
    # Add all clauses
    for clause in request.clauses:
        builder.add_clause(clause)
    
    # Set bool query parameters
    if request.minimum_should_match:
        builder.with_minimum_should_match(request.minimum_should_match)
    
    if request.boost:
        builder.with_boost(request.boost)
    
    # Apply query and configure results
    result = await (
        builder
        .apply_query()
        .configure_results(request)
        .execute()
    )
    
    return result

# Example: E-commerce product search with complex criteria
@app.get("/products/advanced-filter")
async def advanced_product_filter(
    query: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    tags: List[str] = Query(default_factory=list),
    in_stock: Optional[bool] = None,
    featured: Optional[bool] = None,
    size: int = Query(20, le=100)
):
    """Advanced product filtering with complex bool logic"""
    builder = AdvancedBoolQueryBuilder('products')
    
    # Text search (must match if provided)
    if query:
        builder.must_clauses.append(
            Q('multi_match', 
              query=query,
              fields=['name^3', 'description^2', 'category^1.5'],
              type='best_fields',
              operator='and',
              minimum_should_match='75%')
        )
    
    # Category filter (must match if provided)
    if category:
        builder.filter_clauses.append(Q('term', category=category))
    
    # Brand preference (should match, boosts score)
    if brand:
        builder.should_clauses.append(
            Q('term', brand=brand, boost=2.0)
        )
    
    # Price range filter
    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range['gte'] = min_price
        if max_price is not None:
            price_range['lte'] = max_price
        builder.filter_clauses.append(Q('range', price=price_range))
    
    # Rating filter
    if min_rating is not None:
        builder.filter_clauses.append(Q('range', rating={'gte': min_rating}))
    
    # Tags (should match any)
    if tags:
        for tag in tags:
            builder.should_clauses.append(Q('term', tags=tag, boost=1.5))
    
    # Stock availability
    if in_stock is not None:
        builder.filter_clauses.append(Q('term', in_stock=in_stock))
    
    # Featured products boost
    if featured:
        builder.should_clauses.append(Q('term', featured=True, boost=3.0))
    
    # Exclude discontinued products
    builder.must_not_clauses.append(Q('term', discontinued=True))
    
    # Set minimum should match for tags
    if tags or brand or featured:
        builder.with_minimum_should_match(1)
    
    # Apply query and execute
    result = await (
        builder
        .apply_query()
        .configure_results(ComplexSearchRequest(
            clauses=[],
            size=size,
            sort=['_score', '-rating', '-created_date']
        ))
        .execute()
    )
    
    return result
```

## Nested and Parent-Child Queries

### Nested Object Search

```python
from elasticsearch_dsl import Document, Nested, Text, Keyword, Float, Integer

class ProductReview(Document):
    """Document with nested reviews"""
    name = Text(analyzer='standard')
    description = Text(analyzer='standard')
    category = Keyword()
    price = Float()
    
    # Nested reviews
    reviews = Nested(properties={
        'reviewer_name': Text(),
        'rating': Integer(),
        'comment': Text(analyzer='standard'),
        'verified_purchase': Boolean(),
        'review_date': Date()
    })
    
    class Index:
        name = 'products_with_reviews'

class NestedQueryBuilder:
    """Builder for nested object queries"""
    
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
        self.nested_queries = []
    
    def add_nested_query(self, path: str, query: Q, score_mode: str = 'avg') -> 'NestedQueryBuilder':
        """Add a nested query"""
        nested_query = Q('nested', 
                        path=path, 
                        query=query, 
                        score_mode=score_mode)
        self.nested_queries.append(nested_query)
        return self
    
    def with_nested_aggregation(self, name: str, path: str, agg_type: str, **params) -> 'NestedQueryBuilder':
        """Add nested aggregation"""
        nested_agg = A('nested', path=path)
        nested_agg.bucket(name, agg_type, **params)
        self.search.aggs.bucket(f'{name}_nested', nested_agg)
        return self
    
    def apply_queries(self) -> 'NestedQueryBuilder':
        """Apply all nested queries"""
        if len(self.nested_queries) == 1:
            self.search = self.search.query(self.nested_queries[0])
        elif len(self.nested_queries) > 1:
            # Combine multiple nested queries with bool
            self.search = self.search.query('bool', must=self.nested_queries)
        return self
    
    async def execute(self) -> Dict[str, Any]:
        """Execute nested search"""
        response = await self.search.execute()
        
        return {
            'total': response.hits.total.value,
            'products': [
                {
                    '_id': hit.meta.id,
                    '_score': hit.meta.score,
                    **hit.to_dict()
                }
                for hit in response.hits
            ],
            'aggregations': response.aggregations.to_dict() if hasattr(response, 'aggregations') else {}
        }

@app.get("/products/nested-search")
async def nested_review_search(
    product_query: Optional[str] = None,
    min_rating: Optional[int] = None,
    reviewer_name: Optional[str] = None,
    verified_only: bool = False,
    comment_contains: Optional[str] = None
):
    """Search products with nested review criteria"""
    builder = NestedQueryBuilder('products_with_reviews')
    
    # Main product query
    if product_query:
        product_q = Q('multi_match',
                     query=product_query,
                     fields=['name^2', 'description'])
        builder.search = builder.search.query(product_q)
    
    # Build nested review query
    review_conditions = []
    
    if min_rating:
        review_conditions.append(Q('range', reviews__rating={'gte': min_rating}))
    
    if reviewer_name:
        review_conditions.append(Q('match', reviews__reviewer_name=reviewer_name))
    
    if verified_only:
        review_conditions.append(Q('term', reviews__verified_purchase=True))
    
    if comment_contains:
        review_conditions.append(Q('match', reviews__comment=comment_contains))
    
    # Add nested query if we have review conditions
    if review_conditions:
        if len(review_conditions) == 1:
            nested_query = review_conditions[0]
        else:
            nested_query = Q('bool', must=review_conditions)
        
        builder.add_nested_query('reviews', nested_query, score_mode='max')
    
    # Add nested aggregations
    builder.with_nested_aggregation('avg_rating', 'reviews', 'avg', field='reviews.rating')
    builder.with_nested_aggregation('review_count', 'reviews', 'value_count', field='reviews.rating')
    
    # Execute search
    result = await builder.apply_queries().execute()
    
    return result

# Parent-Child relationship queries
class ParentChildQueryBuilder:
    """Builder for parent-child relationship queries"""
    
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
    
    def has_child_query(self, child_type: str, query: Q, score_mode: str = 'max') -> 'ParentChildQueryBuilder':
        """Add has_child query"""
        has_child_q = Q('has_child',
                       type=child_type,
                       query=query,
                       score_mode=score_mode)
        self.search = self.search.query(has_child_q)
        return self
    
    def has_parent_query(self, parent_type: str, query: Q, score: bool = True) -> 'ParentChildQueryBuilder':
        """Add has_parent query"""
        has_parent_q = Q('has_parent',
                        parent_type=parent_type,
                        query=query,
                        score=score)
        self.search = self.search.query(has_parent_q)
        return self
    
    async def execute(self) -> Dict[str, Any]:
        """Execute parent-child search"""
        response = await self.search.execute()
        
        return {
            'total': response.hits.total.value,
            'hits': [hit.to_dict() for hit in response.hits]
        }

@app.get("/categories/with-active-products")
async def categories_with_active_products(
    min_price: Optional[float] = None,
    in_stock: bool = True
):
    """Find categories that have active products"""
    builder = ParentChildQueryBuilder('categories_products')
    
    # Build child (product) query
    product_conditions = [Q('term', active=True)]
    
    if in_stock:
        product_conditions.append(Q('term', in_stock=True))
    
    if min_price:
        product_conditions.append(Q('range', price={'gte': min_price}))
    
    child_query = Q('bool', must=product_conditions)
    
    # Find categories that have matching products
    result = await (
        builder
        .has_child_query('product', child_query, score_mode='max')
        .execute()
    )
    
    return result
```

## Full-Text Search with Scoring

### Advanced Full-Text Search Configuration

```python
from elasticsearch_dsl import analyzer, tokenizer, normalizer

# Custom analyzers for better text search
custom_analyzer = analyzer('custom_search',
    tokenizer=tokenizer('standard'),
    filter=['lowercase', 'stop', 'snowball']
)

class FullTextSearchBuilder:
    """Advanced full-text search with custom scoring"""
    
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
        self.text_queries = []
        self.boost_functions = []
    
    def add_multi_match(self, 
                       query: str, 
                       fields: List[str], 
                       match_type: str = 'best_fields',
                       operator: str = 'and',
                       minimum_should_match: str = '75%',
                       fuzziness: str = 'AUTO') -> 'FullTextSearchBuilder':
        """Add multi-match query with advanced options"""
        multi_match_query = Q('multi_match',
                             query=query,
                             fields=fields,
                             type=match_type,
                             operator=operator,
                             minimum_should_match=minimum_should_match,
                             fuzziness=fuzziness)
        self.text_queries.append(multi_match_query)
        return self
    
    def add_phrase_search(self, 
                         query: str, 
                         fields: List[str], 
                         slop: int = 2) -> 'FullTextSearchBuilder':
        """Add phrase matching with slop"""
        phrase_queries = [
            Q('match_phrase', **{field: {'query': query, 'slop': slop}})
            for field in fields
        ]
        
        phrase_query = Q('dis_max', queries=phrase_queries, tie_breaker=0.3)
        self.text_queries.append(phrase_query)
        return self
    
    def add_prefix_search(self, 
                         query: str, 
                         fields: List[str], 
                         boost: float = 0.5) -> 'FullTextSearchBuilder':
        """Add prefix matching for autocomplete-style search"""
        prefix_queries = [
            Q('prefix', **{field: {'value': query, 'boost': boost}})
            for field in fields
        ]
        
        prefix_query = Q('dis_max', queries=prefix_queries)
        self.text_queries.append(prefix_query)
        return self
    
    def add_function_score(self, 
                          functions: List[Dict[str, Any]], 
                          score_mode: str = 'multiply',
                          boost_mode: str = 'multiply') -> 'FullTextSearchBuilder':
        """Add function score for custom scoring"""
        self.boost_functions.extend(functions)
        return self
    
    def build_text_query(self) -> Q:
        """Build combined text query"""
        if not self.text_queries:
            return Q('match_all')
        
        if len(self.text_queries) == 1:
            base_query = self.text_queries[0]
        else:
            # Combine with different weights
            base_query = Q('dis_max', 
                          queries=self.text_queries, 
                          tie_breaker=0.3)
        
        # Apply function scoring if specified
        if self.boost_functions:
            return Q('function_score',
                    query=base_query,
                    functions=self.boost_functions,
                    score_mode='multiply',
                    boost_mode='multiply')
        
        return base_query
    
    def with_highlighting(self, 
                         fields: List[str], 
                         fragment_size: int = 150,
                         number_of_fragments: int = 3) -> 'FullTextSearchBuilder':
        """Add result highlighting"""
        highlight_fields = {
            field: {
                'fragment_size': fragment_size,
                'number_of_fragments': number_of_fragments
            }
            for field in fields
        }
        
        self.search = self.search.highlight_options(
            pre_tags=['<mark>'],
            post_tags=['</mark>']
        ).highlight(**highlight_fields)
        
        return self
    
    def apply_query(self) -> 'FullTextSearchBuilder':
        """Apply the built text query"""
        text_query = self.build_text_query()
        self.search = self.search.query(text_query)
        return self
    
    async def execute(self) -> Dict[str, Any]:
        """Execute full-text search"""
        response = await self.search.execute()
        
        results = []
        for hit in response.hits:
            result = {
                '_id': hit.meta.id,
                '_score': hit.meta.score,
                '_source': hit.to_dict()
            }
            
            # Add highlights if present
            if hasattr(hit.meta, 'highlight'):
                result['_highlight'] = hit.meta.highlight.to_dict()
            
            results.append(result)
        
        return {
            'total': response.hits.total.value,
            'max_score': response.hits.max_score,
            'hits': results
        }

@app.get("/search/full-text")
async def advanced_full_text_search(
    q: str,
    include_phrases: bool = True,
    include_prefix: bool = True,
    boost_recent: bool = True,
    boost_popular: bool = True,
    highlight: bool = True
):
    """Advanced full-text search with multiple techniques"""
    builder = FullTextSearchBuilder('products')
    
    # Main multi-match query
    builder.add_multi_match(
        query=q,
        fields=['name^3', 'description^2', 'category^1.5', 'tags^1'],
        match_type='best_fields',
        operator='and',
        minimum_should_match='75%',
        fuzziness='AUTO'
    )
    
    # Add phrase search for exact matches
    if include_phrases:
        builder.add_phrase_search(
            query=q,
            fields=['name^2', 'description'],
            slop=2
        )
    
    # Add prefix search for partial matches
    if include_prefix:
        builder.add_prefix_search(
            query=q,
            fields=['name', 'category'],
            boost=0.3
        )
    
    # Function scoring for business logic
    functions = []
    
    if boost_recent:
        # Boost recently added products
        functions.append({
            'gauss': {
                'created_date': {
                    'origin': 'now',
                    'scale': '30d',
                    'decay': 0.5
                }
            },
            'weight': 1.2
        })
    
    if boost_popular:
        # Boost popular products
        functions.append({
            'field_value_factor': {
                'field': 'view_count',
                'factor': 0.1,
                'modifier': 'log1p',
                'missing': 1
            },
            'weight': 1.5
        })
    
    if functions:
        builder.add_function_score(functions)
    
    # Add highlighting
    if highlight:
        builder.with_highlighting(['name', 'description'])
    
    # Execute search
    result = await (
        builder
        .apply_query()
        .execute()
    )
    
    return result
```

## Multi-Index and Cross-Cluster Search

### Multi-Index Search Implementation

```python
import asyncio
from typing import Dict, List, Any, Optional

class MultiIndexSearchOrchestrator:
    """Orchestrate searches across multiple indices"""
    
    def __init__(self, using=None):
        self.using = using
        self.index_searches = {}
        self.parallel_execution = True
    
    def add_index_search(self, 
                        index_name: str, 
                        search_config: Dict[str, Any],
                        weight: float = 1.0) -> 'MultiIndexSearchOrchestrator':
        """Add search configuration for an index"""
        self.index_searches[index_name] = {
            'config': search_config,
            'weight': weight
        }
        return self
    
    def build_search_for_index(self, index_name: str, config: Dict[str, Any]) -> AsyncSearch:
        """Build search object for specific index"""
        search = AsyncSearch(index=index_name, using=self.using)
        
        # Apply query
        if 'query' in config:
            search = search.query(**config['query'])
        
        # Apply filters
        if 'filters' in config:
            for filter_config in config['filters']:
                search = search.filter(**filter_config)
        
        # Apply aggregations
        if 'aggregations' in config:
            for agg_name, agg_config in config['aggregations'].items():
                search.aggs.bucket(agg_name, **agg_config)
        
        # Apply sorting
        if 'sort' in config:
            search = search.sort(*config['sort'])
        
        # Apply pagination
        if 'size' in config:
            search = search[:config['size']]
        
        return search
    
    async def execute_searches(self) -> Dict[str, Any]:
        """Execute all searches in parallel or sequence"""
        results = {}
        
        if self.parallel_execution:
            # Execute all searches in parallel
            tasks = {}
            for index_name, search_info in self.index_searches.items():
                search = self.build_search_for_index(index_name, search_info['config'])
                tasks[index_name] = search.execute()
            
            # Wait for all searches to complete
            completed_tasks = await asyncio.gather(
                *tasks.values(), 
                return_exceptions=True
            )
            
            # Process results
            for i, (index_name, _) in enumerate(self.index_searches.items()):
                result = completed_tasks[i]
                if isinstance(result, Exception):
                    results[index_name] = {
                        'error': str(result),
                        'weight': self.index_searches[index_name]['weight']
                    }
                else:
                    results[index_name] = {
                        'response': result,
                        'weight': self.index_searches[index_name]['weight']
                    }
        else:
            # Execute searches sequentially
            for index_name, search_info in self.index_searches.items():
                try:
                    search = self.build_search_for_index(index_name, search_info['config'])
                    response = await search.execute()
                    results[index_name] = {
                        'response': response,
                        'weight': search_info['weight']
                    }
                except Exception as e:
                    results[index_name] = {
                        'error': str(e),
                        'weight': search_info['weight']
                    }
        
        return results
    
    def merge_and_rank_results(self, 
                              results: Dict[str, Any], 
                              max_results: int = 50) -> List[Dict[str, Any]]:
        """Merge and rank results from multiple indices"""
        all_hits = []
        
        for index_name, result_data in results.items():
            if 'error' in result_data:
                logger.warning(f"Error in index {index_name}: {result_data['error']}")
                continue
            
            response = result_data['response']
            weight = result_data['weight']
            max_score = response.hits.max_score or 1.0
            
            for hit in response.hits:
                # Normalize and weight the score
                original_score = hit.meta.score or 0
                normalized_score = original_score / max_score if max_score > 0 else 0
                weighted_score = normalized_score * weight
                
                hit_data = {
                    '_id': hit.meta.id,
                    '_index': index_name,
                    '_score': original_score,
                    '_normalized_score': normalized_score,
                    '_weighted_score': weighted_score,
                    '_source': hit.to_dict()
                }
                
                # Add highlights if present
                if hasattr(hit.meta, 'highlight'):
                    hit_data['_highlight'] = hit.meta.highlight.to_dict()
                
                all_hits.append(hit_data)
        
        # Sort by weighted score
        all_hits.sort(key=lambda x: x['_weighted_score'], reverse=True)
        
        return all_hits[:max_results]

@app.get("/search/multi-index")
async def multi_index_search(
    q: str,
    include_products: bool = True,
    include_articles: bool = True,
    include_categories: bool = True,
    max_results: int = 30
):
    """Search across multiple indices with unified results"""
    orchestrator = MultiIndexSearchOrchestrator()
    
    base_query = {
        'multi_match': {
            'query': q,
            'type': 'best_fields',
            'operator': 'and'
        }
    }
    
    if include_products:
        orchestrator.add_index_search(
            'products',
            {
                'query': {
                    **base_query,
                    'multi_match': {
                        **base_query['multi_match'],
                        'fields': ['name^3', 'description^2', 'category']
                    }
                },
                'filters': [{'term': {'active': True}}],
                'sort': ['_score', '-popularity'],
                'size': int(max_results * 0.6)
            },
            weight=1.0
        )
    
    if include_articles:
        orchestrator.add_index_search(
            'articles',
            {
                'query': {
                    **base_query,
                    'multi_match': {
                        **base_query['multi_match'],
                        'fields': ['title^3', 'content^1', 'tags^2']
                    }
                },
                'filters': [{'term': {'published': True}}],
                'sort': ['_score', '-publish_date'],
                'size': int(max_results * 0.3)
            },
            weight=0.8
        )
    
    if include_categories:
        orchestrator.add_index_search(
            'categories',
            {
                'query': {
                    **base_query,
                    'multi_match': {
                        **base_query['multi_match'],
                        'fields': ['name^3', 'description^2']
                    }
                },
                'sort': ['_score', 'product_count'],
                'size': int(max_results * 0.1)
            },
            weight=0.6
        )
    
    # Execute searches
    search_results = await orchestrator.execute_searches()
    
    # Merge and rank results
    merged_results = orchestrator.merge_and_rank_results(search_results, max_results)
    
    # Calculate summary statistics
    total_results = sum(
        result_data.get('response', {}).get('hits', {}).get('total', {}).get('value', 0)
        for result_data in search_results.values()
        if 'response' in result_data
    )
    
    return {
        'total': total_results,
        'merged_count': len(merged_results),
        'results': merged_results,
        'index_breakdown': {
            index: {
                'total': result_data.get('response', {}).get('hits', {}).get('total', {}).get('value', 0),
                'max_score': result_data.get('response', {}).get('hits', {}).get('max_score'),
                'error': result_data.get('error')
            }
            for index, result_data in search_results.items()
        }
    }
```

## Query Optimization Techniques

### Performance Optimization Strategies

```python
import time
from functools import wraps
from typing import Callable, Any

class QueryProfiler:
    """Profile and optimize query performance"""
    
    def __init__(self):
        self.profile_data = {}
    
    def profile_query(self, query_name: str):
        """Decorator to profile query execution"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Store profile data
                    if query_name not in self.profile_data:
                        self.profile_data[query_name] = []
                    
                    self.profile_data[query_name].append({
                        'execution_time': execution_time,
                        'success': True,
                        'timestamp': time.time()
                    })
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    if query_name not in self.profile_data:
                        self.profile_data[query_name] = []
                    
                    self.profile_data[query_name].append({
                        'execution_time': execution_time,
                        'success': False,
                        'error': str(e),
                        'timestamp': time.time()
                    })
                    
                    raise
            
            return wrapper
        return decorator
    
    def get_performance_stats(self, query_name: str) -> Dict[str, Any]:
        """Get performance statistics for a query"""
        if query_name not in self.profile_data:
            return {}
        
        data = self.profile_data[query_name]
        execution_times = [entry['execution_time'] for entry in data if entry['success']]
        
        if not execution_times:
            return {'no_successful_executions': True}
        
        return {
            'total_executions': len(data),
            'successful_executions': len(execution_times),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'success_rate': len(execution_times) / len(data)
        }

profiler = QueryProfiler()

class OptimizedQueryBuilder:
    """Query builder with optimization techniques"""
    
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
        self.optimization_hints = {}
    
    def with_request_cache(self, enabled: bool = True) -> 'OptimizedQueryBuilder':
        """Enable Elasticsearch request cache"""
        self.search = self.search.extra(request_cache=enabled)
        return self
    
    def with_preference(self, preference: str) -> 'OptimizedQueryBuilder':
        """Set search preference for consistent shard routing"""
        self.search = self.search.extra(preference=preference)
        return self
    
    def with_timeout(self, timeout: str = "30s") -> 'OptimizedQueryBuilder':
        """Set query timeout"""
        self.search = self.search.extra(timeout=timeout)
        return self
    
    def optimize_for_aggregations(self) -> 'OptimizedQueryBuilder':
        """Optimize for aggregation-only queries"""
        self.search = self.search[:0]  # No hits needed
        self.optimization_hints['aggregation_only'] = True
        return self
    
    def optimize_for_count(self) -> 'OptimizedQueryBuilder':
        """Optimize for count queries"""
        self.search = self.search.extra(terminate_after=1)
        self.optimization_hints['count_only'] = True
        return self
    
    def with_source_filtering(self, includes: List[str] = None, excludes: List[str] = None) -> 'OptimizedQueryBuilder':
        """Optimize by filtering source fields"""
        if includes:
            self.search = self.search.source(includes)
        elif excludes:
            excludes_formatted = [f"!{field}" for field in excludes]
            self.search = self.search.source(excludes_formatted)
        return self
    
    def with_stored_fields(self, fields: List[str]) -> 'OptimizedQueryBuilder':
        """Use stored fields instead of source"""
        self.search = self.search.extra(stored_fields=fields)
        return self
    
    @profiler.profile_query('optimized_search')
    async def execute_optimized(self) -> Dict[str, Any]:
        """Execute with optimization telemetry"""
        start_time = time.time()
        
        # Add explain for debugging
        if logger.isEnabledFor(logging.DEBUG):
            self.search = self.search.extra(explain=True)
        
        response = await self.search.execute()
        execution_time = time.time() - start_time
        
        result = {
            'took': response.took,
            'execution_time': execution_time,
            'optimization_hints': self.optimization_hints,
            'total': getattr(response.hits.total, 'value', 0),
            'hits': [hit.to_dict() for hit in response.hits]
        }
        
        # Add performance warnings
        if execution_time > 1.0:
            result['performance_warning'] = 'Query took longer than 1 second'
        
        if response.timed_out:
            result['timeout_warning'] = 'Query timed out'
        
        return result

@app.get("/search/optimized")
async def optimized_search_endpoint(
    q: str,
    enable_cache: bool = True,
    user_id: Optional[str] = None,
    aggregations_only: bool = False
):
    """Optimized search endpoint"""
    builder = OptimizedQueryBuilder('products')
    
    # Build query
    builder.search = builder.search.query(
        'multi_match',
        query=q,
        fields=['name^2', 'description'],
        type='best_fields'
    )
    
    # Apply optimizations
    if enable_cache:
        builder.with_request_cache(True)
    
    if user_id:
        builder.with_preference(f"user_{user_id}")
    
    if aggregations_only:
        builder.optimize_for_aggregations()
        # Add sample aggregations
        builder.search.aggs.bucket('categories', 'terms', field='category', size=10)
        builder.search.aggs.bucket('price_ranges', 'range', 
                                 field='price',
                                 ranges=[
                                     {'to': 100},
                                     {'from': 100, 'to': 500},
                                     {'from': 500}
                                 ])
    else:
        builder.with_source_filtering(includes=['name', 'price', 'category', 'rating'])
    
    builder.with_timeout("10s")
    
    result = await builder.execute_optimized()
    
    # Add profiling stats
    result['profiling'] = profiler.get_performance_stats('optimized_search')
    
    return result
```

## Real-World Complex Scenarios

### E-commerce Search with Business Logic

```python
class EcommerceSearchBuilder:
    """Real-world e-commerce search with business rules"""
    
    def __init__(self):
        self.search = AsyncSearch(index='products')
        self.business_rules = []
        self.personalization_factors = {}
    
    def add_business_rule(self, rule_func: Callable) -> 'EcommerceSearchBuilder':
        """Add business rule to search"""
        self.business_rules.append(rule_func)
        return self
    
    def with_personalization(self, user_profile: Dict[str, Any]) -> 'EcommerceSearchBuilder':
        """Add personalization factors"""
        self.personalization_factors = user_profile
        return self
    
    def build_search(self, query: str, filters: Dict[str, Any] = None) -> 'EcommerceSearchBuilder':
        """Build comprehensive e-commerce search"""
        filters = filters or {}
        
        # Main search query
        if query:
            self.search = self.search.query(
                'function_score',
                query=Q('multi_match',
                       query=query,
                       fields=['name^3', 'description^2', 'brand^1.5', 'category'],
                       type='most_fields',
                       operator='and',
                       minimum_should_match='75%'),
                functions=self._build_scoring_functions()
            )
        
        # Apply filters
        self._apply_filters(filters)
        
        # Apply business rules
        for rule in self.business_rules:
            rule(self.search)
        
        # Apply personalization
        if self.personalization_factors:
            self._apply_personalization()
        
        return self
    
    def _build_scoring_functions(self) -> List[Dict[str, Any]]:
        """Build scoring functions for business logic"""
        functions = []
        
        # Boost popular products
        functions.append({
            'field_value_factor': {
                'field': 'popularity_score',
                'factor': 1.2,
                'modifier': 'log1p',
                'missing': 1
            },
            'weight': 1.5
        })
        
        # Boost products with high ratings
        functions.append({
            'gauss': {
                'average_rating': {
                    'origin': 5,
                    'scale': 1,
                    'decay': 0.5
                }
            },
            'weight': 1.3
        })
        
        # Boost recently added products
        functions.append({
            'gauss': {
                'created_date': {
                    'origin': 'now',
                    'scale': '30d',
                    'decay': 0.3
                }
            },
            'weight': 1.1
        })
        
        # Penalize out of stock items
        functions.append({
            'filter': Q('term', in_stock=False),
            'weight': 0.1
        })
        
        return functions
    
    def _apply_filters(self, filters: Dict[str, Any]):
        """Apply standard filters"""
        if 'category' in filters:
            self.search = self.search.filter('term', category=filters['category'])
        
        if 'brand' in filters:
            self.search = self.search.filter('terms', brand=filters['brand'])
        
        if 'price_range' in filters:
            price_range = filters['price_range']
            self.search = self.search.filter('range', price=price_range)
        
        if 'rating_min' in filters:
            self.search = self.search.filter('range', average_rating={'gte': filters['rating_min']})
        
        # Always filter out discontinued products
        self.search = self.search.filter('term', active=True)
    
    def _apply_personalization(self):
        """Apply personalization based on user profile"""
        # Boost preferred brands
        if 'preferred_brands' in self.personalization_factors:
            for brand in self.personalization_factors['preferred_brands']:
                self.search = self.search.query('bool',
                    should=[
                        self.search.to_dict()['query'],
                        Q('term', brand=brand, boost=2.0)
                    ]
                )
        
        # Boost products in preferred price range
        if 'price_preference' in self.personalization_factors:
            price_pref = self.personalization_factors['price_preference']
            self.search = self.search.query('bool',
                should=[
                    self.search.to_dict()['query'],
                    Q('range', price=price_pref, boost=1.5)
                ]
            )
    
    async def execute_with_fallback(self) -> Dict[str, Any]:
        """Execute search with fallback strategies"""
        try:
            # Try exact search first
            response = await self.search.execute()
            
            if response.hits.total.value > 0:
                return self._format_response(response, 'exact')
            
            # Fallback: relax minimum_should_match
            fallback_search = self.search.to_dict()
            if 'query' in fallback_search and 'function_score' in fallback_search['query']:
                multi_match = fallback_search['query']['function_score']['query']['multi_match']
                multi_match['minimum_should_match'] = '50%'
                
                fallback_response = await AsyncSearch().from_dict(fallback_search).execute()
                
                if fallback_response.hits.total.value > 0:
                    return self._format_response(fallback_response, 'relaxed')
            
            # Final fallback: fuzzy search
            fuzzy_search = self.search.to_dict()
            if 'query' in fuzzy_search and 'function_score' in fuzzy_search['query']:
                multi_match = fuzzy_search['query']['function_score']['query']['multi_match']
                multi_match['fuzziness'] = 'AUTO'
                multi_match['minimum_should_match'] = '25%'
                
                fuzzy_response = await AsyncSearch().from_dict(fuzzy_search).execute()
                return self._format_response(fuzzy_response, 'fuzzy')
            
            return self._format_response(None, 'no_results')
            
        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            return {'error': str(e), 'fallback_applied': 'error'}
    
    def _format_response(self, response, search_type: str) -> Dict[str, Any]:
        """Format search response"""
        if response is None:
            return {
                'total': 0,
                'hits': [],
                'search_type': search_type
            }
        
        return {
            'total': response.hits.total.value,
            'max_score': response.hits.max_score,
            'search_type': search_type,
            'hits': [
                {
                    '_id': hit.meta.id,
                    '_score': hit.meta.score,
                    **hit.to_dict()
                }
                for hit in response.hits
            ]
        }

# Business rule examples
def boost_seasonal_products(search: AsyncSearch):
    """Boost seasonal products during relevant periods"""
    import datetime
    
    current_month = datetime.datetime.now().month
    
    seasonal_boosts = {
        12: ['winter', 'holiday', 'christmas'],  # December
        6: ['summer', 'vacation', 'outdoor'],    # June
        9: ['back-to-school', 'fall']            # September
    }
    
    if current_month in seasonal_boosts:
        for tag in seasonal_boosts[current_month]:
            search.query('bool', should=[
                search.to_dict()['query'],
                Q('term', tags=tag, boost=2.0)
            ])

def prioritize_local_inventory(search: AsyncSearch):
    """Prioritize products available in local warehouses"""
    search.query('bool', should=[
        search.to_dict()['query'],
        Q('term', local_inventory=True, boost=1.8)
    ])

@app.get("/products/smart-search")
async def smart_ecommerce_search(
    q: str,
    category: Optional[str] = None,
    brand: Optional[List[str]] = Query(default_factory=list),
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    user_id: Optional[str] = None
):
    """Smart e-commerce search with business logic"""
    builder = EcommerceSearchBuilder()
    
    # Add business rules
    builder.add_business_rule(boost_seasonal_products)
    builder.add_business_rule(prioritize_local_inventory)
    
    # Add personalization if user provided
    if user_id:
        # In real implementation, fetch from user service
        user_profile = {
            'preferred_brands': ['nike', 'adidas'],
            'price_preference': {'gte': 50, 'lte': 200}
        }
        builder.with_personalization(user_profile)
    
    # Build filters
    filters = {}
    if category:
        filters['category'] = category
    if brand:
        filters['brand'] = brand
    if price_min or price_max:
        price_range = {}
        if price_min:
            price_range['gte'] = price_min
        if price_max:
            price_range['lte'] = price_max
        filters['price_range'] = price_range
    
    # Execute search
    result = await (
        builder
        .build_search(q, filters)
        .execute_with_fallback()
    )
    
    return result
```

## Performance Monitoring

### Search Performance Metrics

```python
import time
import statistics
from collections import defaultdict
from typing import Dict, List, Any

class SearchMetrics:
    """Collect and analyze search performance metrics"""
    
    def __init__(self):
        self.query_times = defaultdict(list)
        self.result_counts = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.slow_queries = []
    
    def record_query(self, 
                    query_type: str, 
                    execution_time: float, 
                    result_count: int, 
                    success: bool = True,
                    query_details: Dict[str, Any] = None):
        """Record query execution metrics"""
        self.query_times[query_type].append(execution_time)
        self.result_counts[query_type].append(result_count)
        
        if not success:
            self.error_counts[query_type] += 1
        
        # Track slow queries (>1 second)
        if execution_time > 1.0:
            self.slow_queries.append({
                'query_type': query_type,
                'execution_time': execution_time,
                'result_count': result_count,
                'timestamp': time.time(),
                'details': query_details or {}
            })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {}
        
        for query_type, times in self.query_times.items():
            if times:
                summary[query_type] = {
                    'total_queries': len(times),
                    'avg_time': statistics.mean(times),
                    'median_time': statistics.median(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'p95_time': statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                    'avg_results': statistics.mean(self.result_counts[query_type]),
                    'error_count': self.error_counts[query_type],
                    'error_rate': self.error_counts[query_type] / len(times)
                }
        
        summary['slow_queries'] = self.slow_queries[-10:]  # Last 10 slow queries
        
        return summary

# Global metrics instance
search_metrics = SearchMetrics()

def monitor_search_performance(query_type: str):
    """Decorator to monitor search performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            result_count = 0
            query_details = {}
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Extract result count from response
                if isinstance(result, dict):
                    result_count = result.get('total', 0)
                    query_details = {
                        'args': str(args)[:100],  # Truncate for storage
                        'kwargs': str(kwargs)[:100]
                    }
                
                search_metrics.record_query(
                    query_type, 
                    execution_time, 
                    result_count, 
                    success, 
                    query_details
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                success = False
                
                search_metrics.record_query(
                    query_type, 
                    execution_time, 
                    result_count, 
                    success, 
                    {'error': str(e)}
                )
                
                raise
        
        return wrapper
    return decorator

@app.get("/search/performance-metrics")
async def get_search_metrics():
    """Get search performance metrics"""
    return search_metrics.get_performance_summary()

# Apply monitoring to search endpoints
@monitor_search_performance('complex_bool')
async def monitored_complex_search(request: ComplexSearchRequest):
    """Complex search with performance monitoring"""
    # Implementation here...
    pass

@monitor_search_performance('full_text')
async def monitored_full_text_search(q: str, **kwargs):
    """Full-text search with performance monitoring"""
    # Implementation here...
    pass
```

## Next Steps

1. **[Async Search Performance](02_async-search-performance.md)** - Learn performance optimization and async patterns
2. **[Aggregations and Faceting](03_aggregations-faceting.md)** - Master data aggregation and faceted search
3. **[Geospatial and Vector Search](04_geospatial-vector-search.md)** - Implement location and semantic search
4. **[Data Modeling](../05-data-modeling/01_document-design.md)** - Design efficient document structures
5. **[Production Patterns](../06-production-patterns/01_monitoring-logging.md)** - Implement production-ready patterns

## Additional Resources

- **Elasticsearch Query DSL**: [elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- **Bool Query Reference**: [elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html)
- **Function Score Query**: [elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-function-score-query.html)
- **Multi-Index Search**: [elastic.co/guide/en/elasticsearch/reference/current/multi-index.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/multi-index.html)