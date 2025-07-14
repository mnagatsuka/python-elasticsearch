# Search Applications

Complete search API implementation examples with FastAPI + Elasticsearch-DSL, featuring faceted search, auto-complete, and advanced search functionality.

## Table of Contents
- [Complete Search API Implementation](#complete-search-api-implementation)
- [Faceted Search with Aggregations](#faceted-search-with-aggregations)
- [Auto-complete and Suggestion Endpoints](#auto-complete-and-suggestion-endpoints)
- [Search Result Highlighting](#search-result-highlighting)
- [Advanced Search Features](#advanced-search-features)
- [Search Analytics](#search-analytics)
- [Performance Optimization](#performance-optimization)
- [Next Steps](#next-steps)

## Complete Search API Implementation

### E-commerce Search Application
```python
# ecommerce_search.py - Complete e-commerce search implementation
from fastapi import FastAPI, Depends, Query, HTTPException
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Float, Integer, Date, Boolean, Nested, Completion
from elasticsearch_dsl import AsyncSearch, Q, A
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import asyncio

# Document Models
class ProductDocument(AsyncDocument):
    """Enhanced product document for e-commerce search."""
    
    # Basic product information
    name = Text(
        analyzer='standard',
        fields={
            'keyword': Keyword(),
            'suggest': Completion()
        }
    )
    description = Text(analyzer='english')
    brand = Keyword()
    category = Keyword()
    
    # Pricing and inventory
    price = Float()
    sale_price = Float()
    in_stock = Boolean()
    stock_quantity = Integer()
    
    # Product attributes
    color = Keyword()
    size = Keyword()
    material = Keyword()
    weight = Float()
    
    # Ratings and reviews
    average_rating = Float()
    review_count = Integer()
    
    # SEO and metadata
    tags = Keyword(multi=True)
    sku = Keyword()
    
    # Timestamps
    created_at = Date()
    updated_at = Date()
    
    # Nested variant information
    variants = Nested(
        properties={
            'sku': Keyword(),
            'color': Keyword(),
            'size': Keyword(),
            'price': Float(),
            'stock': Integer(),
            'images': Keyword(multi=True)
        }
    )
    
    # Categories hierarchy
    category_path = Keyword(multi=True)  # ["Electronics", "Computers", "Laptops"]
    
    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 2,
            'number_of_replicas': 1,
            'analysis': {
                'analyzer': {
                    'product_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': [
                            'lowercase',
                            'asciifolding',
                            'stop',
                            'synonym_filter'
                        ]
                    }
                },
                'filter': {
                    'synonym_filter': {
                        'type': 'synonym',
                        'synonyms': [
                            'laptop,notebook,computer',
                            'mobile,phone,smartphone',
                            'tv,television'
                        ]
                    }
                }
            }
        }

# Pydantic Models
class SortOption(str, Enum):
    RELEVANCE = "relevance"
    PRICE_LOW_HIGH = "price_asc"
    PRICE_HIGH_LOW = "price_desc"
    RATING = "rating"
    NEWEST = "newest"
    POPULARITY = "popularity"

class PriceRange(BaseModel):
    min: Optional[float] = Field(None, ge=0)
    max: Optional[float] = Field(None, ge=0)

class SearchFilters(BaseModel):
    category: Optional[str] = None
    brand: Optional[List[str]] = None
    price_range: Optional[PriceRange] = None
    color: Optional[List[str]] = None
    size: Optional[List[str]] = None
    material: Optional[List[str]] = None
    in_stock_only: bool = False
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    tags: Optional[List[str]] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    filters: Optional[SearchFilters] = None
    sort_by: SortOption = SortOption.RELEVANCE
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    include_aggregations: bool = True
    include_suggestions: bool = False

class ProductSummary(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    price: float
    sale_price: Optional[float] = None
    average_rating: Optional[float] = None
    review_count: int
    in_stock: bool
    image_url: Optional[str] = None
    relevance_score: Optional[float] = None

class Aggregation(BaseModel):
    name: str
    buckets: List[Dict[str, Any]]

class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    query_time_ms: int
    products: List[ProductSummary]
    aggregations: Optional[List[Aggregation]] = None
    suggestions: Optional[List[str]] = None
    applied_filters: Optional[SearchFilters] = None

# Search Service
class EcommerceSearchService:
    """Comprehensive e-commerce search service."""
    
    @staticmethod
    async def search_products(request: SearchRequest) -> SearchResponse:
        """Execute comprehensive product search."""
        
        # Build base search
        search = AsyncSearch(index='products')
        
        # Apply text query
        if request.query.strip() != "*":
            search = search.query(
                'multi_match',
                query=request.query,
                fields=[
                    'name^3',
                    'brand^2',
                    'description^1',
                    'tags^1.5',
                    'category^1.5'
                ],
                type='best_fields',
                fuzziness='AUTO',
                minimum_should_match='75%'
            )
        
        # Apply filters
        if request.filters:
            search = await EcommerceSearchService._apply_filters(search, request.filters)
        
        # Apply sorting
        search = EcommerceSearchService._apply_sorting(search, request.sort_by)
        
        # Add aggregations
        if request.include_aggregations:
            search = EcommerceSearchService._add_aggregations(search)
        
        # Pagination
        offset = (request.page - 1) * request.size
        search = search[offset:offset + request.size]
        
        # Add highlighting
        search = search.highlight(
            'name', 'description',
            fragment_size=150,
            number_of_fragments=2
        )
        
        # Execute search
        start_time = asyncio.get_event_loop().time()
        response = await search.execute()
        query_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
        
        # Format response
        products = []
        for hit in response.hits:
            product = ProductSummary(
                id=hit.meta.id,
                name=hit.name,
                brand=hit.brand,
                category=hit.category,
                price=hit.price,
                sale_price=getattr(hit, 'sale_price', None),
                average_rating=getattr(hit, 'average_rating', None),
                review_count=getattr(hit, 'review_count', 0),
                in_stock=getattr(hit, 'in_stock', False),
                relevance_score=hit.meta.score
            )
            products.append(product)
        
        # Format aggregations
        aggregations = None
        if request.include_aggregations and hasattr(response, 'aggregations'):
            aggregations = EcommerceSearchService._format_aggregations(response.aggregations)
        
        # Get suggestions if requested
        suggestions = None
        if request.include_suggestions:
            suggestions = await EcommerceSearchService._get_suggestions(request.query)
        
        return SearchResponse(
            total=response.hits.total.value,
            page=request.page,
            size=request.size,
            query_time_ms=query_time,
            products=products,
            aggregations=aggregations,
            suggestions=suggestions,
            applied_filters=request.filters
        )
    
    @staticmethod
    async def _apply_filters(search: AsyncSearch, filters: SearchFilters) -> AsyncSearch:
        """Apply search filters."""
        
        filter_conditions = []
        
        # Category filter
        if filters.category:
            filter_conditions.append(Q('term', category=filters.category))
        
        # Brand filter
        if filters.brand:
            filter_conditions.append(Q('terms', brand=filters.brand))
        
        # Price range filter
        if filters.price_range:
            price_filter = {}
            if filters.price_range.min is not None:
                price_filter['gte'] = filters.price_range.min
            if filters.price_range.max is not None:
                price_filter['lte'] = filters.price_range.max
            
            if price_filter:
                filter_conditions.append(Q('range', price=price_filter))
        
        # Color filter
        if filters.color:
            filter_conditions.append(Q('terms', color=filters.color))
        
        # Size filter
        if filters.size:
            filter_conditions.append(Q('terms', size=filters.size))
        
        # Material filter
        if filters.material:
            filter_conditions.append(Q('terms', material=filters.material))
        
        # Stock filter
        if filters.in_stock_only:
            filter_conditions.append(Q('term', in_stock=True))
        
        # Rating filter
        if filters.min_rating is not None:
            filter_conditions.append(Q('range', average_rating={'gte': filters.min_rating}))
        
        # Tags filter
        if filters.tags:
            filter_conditions.append(Q('terms', tags=filters.tags))
        
        # Apply all filters
        if filter_conditions:
            search = search.filter('bool', must=filter_conditions)
        
        return search
    
    @staticmethod
    def _apply_sorting(search: AsyncSearch, sort_by: SortOption) -> AsyncSearch:
        """Apply sorting to search."""
        
        if sort_by == SortOption.PRICE_LOW_HIGH:
            search = search.sort('price')
        elif sort_by == SortOption.PRICE_HIGH_LOW:
            search = search.sort('-price')
        elif sort_by == SortOption.RATING:
            search = search.sort('-average_rating', '-review_count')
        elif sort_by == SortOption.NEWEST:
            search = search.sort('-created_at')
        elif sort_by == SortOption.POPULARITY:
            search = search.sort('-review_count', '-average_rating')
        # RELEVANCE uses default Elasticsearch scoring
        
        return search
    
    @staticmethod
    def _add_aggregations(search: AsyncSearch) -> AsyncSearch:
        """Add faceted search aggregations."""
        
        # Brand aggregation
        search.aggs.bucket('brands', 'terms', field='brand', size=20)
        
        # Category aggregation
        search.aggs.bucket('categories', 'terms', field='category', size=15)
        
        # Price range aggregation
        search.aggs.bucket('price_ranges', 'range', field='price', ranges=[
            {'to': 25},
            {'from': 25, 'to': 50},
            {'from': 50, 'to': 100},
            {'from': 100, 'to': 250},
            {'from': 250, 'to': 500},
            {'from': 500}
        ])
        
        # Color aggregation
        search.aggs.bucket('colors', 'terms', field='color', size=10)
        
        # Size aggregation
        search.aggs.bucket('sizes', 'terms', field='size', size=10)
        
        # Rating aggregation
        search.aggs.bucket('ratings', 'range', field='average_rating', ranges=[
            {'from': 4, 'to': 5},
            {'from': 3, 'to': 4},
            {'from': 2, 'to': 3},
            {'from': 1, 'to': 2}
        ])
        
        # Availability aggregation
        search.aggs.bucket('availability', 'terms', field='in_stock')
        
        return search
    
    @staticmethod
    def _format_aggregations(aggs) -> List[Aggregation]:
        """Format aggregation results."""
        
        formatted_aggs = []
        
        for agg_name, agg_data in aggs.to_dict().items():
            if 'buckets' in agg_data:
                buckets = []
                for bucket in agg_data['buckets']:
                    bucket_data = {
                        'key': bucket['key'],
                        'doc_count': bucket['doc_count']
                    }
                    
                    # Add formatted key for ranges
                    if 'key_as_string' in bucket:
                        bucket_data['display_name'] = bucket['key_as_string']
                    elif agg_name == 'price_ranges':
                        bucket_data['display_name'] = EcommerceSearchService._format_price_range(bucket)
                    elif agg_name == 'ratings':
                        bucket_data['display_name'] = EcommerceSearchService._format_rating_range(bucket)
                    
                    buckets.append(bucket_data)
                
                formatted_aggs.append(Aggregation(name=agg_name, buckets=buckets))
        
        return formatted_aggs
    
    @staticmethod
    def _format_price_range(bucket: Dict) -> str:
        """Format price range for display."""
        if 'from' in bucket and 'to' in bucket:
            return f"${bucket['from']:.0f} - ${bucket['to']:.0f}"
        elif 'from' in bucket:
            return f"${bucket['from']:.0f}+"
        elif 'to' in bucket:
            return f"Under ${bucket['to']:.0f}"
        return "Unknown"
    
    @staticmethod
    def _format_rating_range(bucket: Dict) -> str:
        """Format rating range for display."""
        if 'from' in bucket and 'to' in bucket:
            return f"{bucket['from']:.0f} - {bucket['to']:.0f} stars"
        elif 'from' in bucket:
            return f"{bucket['from']:.0f}+ stars"
        return "Unknown"
    
    @staticmethod
    async def _get_suggestions(query: str) -> List[str]:
        """Get search suggestions."""
        
        # Implement suggestion logic here
        # This could include:
        # - Query corrections
        # - Related searches
        # - Popular searches
        
        suggestions = []
        
        # Example: Simple query-based suggestions
        if len(query) >= 3:
            search = AsyncSearch(index='products')
            search = search.suggest(
                'product_suggestions',
                query,
                completion={'field': 'name.suggest', 'size': 5}
            )
            
            response = await search.execute()
            
            if hasattr(response, 'suggest') and 'product_suggestions' in response.suggest:
                for suggestion in response.suggest.product_suggestions[0].options:
                    suggestions.append(suggestion.text)
        
        return suggestions

# FastAPI Application
app = FastAPI(title="E-commerce Search API", version="1.0.0")

@app.post("/search", response_model=SearchResponse)
async def search_products(request: SearchRequest):
    """Advanced product search endpoint."""
    try:
        return await EcommerceSearchService.search_products(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

@app.get("/search/autocomplete")
async def autocomplete_search(
    q: str = Query(..., min_length=2, max_length=50),
    limit: int = Query(default=10, ge=1, le=20)
):
    """Autocomplete search suggestions."""
    try:
        search = AsyncSearch(index='products')
        search = search.suggest(
            'name_suggest',
            q,
            completion={
                'field': 'name.suggest',
                'size': limit,
                'skip_duplicates': True
            }
        )
        
        response = await search.execute()
        
        suggestions = []
        if hasattr(response, 'suggest') and 'name_suggest' in response.suggest:
            for suggestion in response.suggest.name_suggest[0].options:
                suggestions.append({
                    'text': suggestion.text,
                    'score': suggestion.score
                })
        
        return {'suggestions': suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {e}")
```

## Faceted Search with Aggregations

### Advanced Faceted Search Implementation
```python
# faceted_search.py - Advanced faceted search with drill-down
from typing import Dict, List, Any
from elasticsearch_dsl import A

class FacetedSearchService:
    """Advanced faceted search with drill-down capabilities."""
    
    @staticmethod
    async def faceted_search(
        query: str,
        selected_facets: Dict[str, List[str]] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Execute faceted search with drill-down."""
        
        search = AsyncSearch(index='products')
        
        # Apply text query
        if query and query.strip() != "*":
            search = search.query('multi_match', 
                                query=query,
                                fields=['name^3', 'description', 'brand^2'])
        
        # Apply selected facet filters
        filter_conditions = []
        if selected_facets:
            for facet_field, values in selected_facets.items():
                if values:
                    if facet_field in ['brand', 'category', 'color', 'size']:
                        filter_conditions.append(Q('terms', **{facet_field: values}))
        
        if filter_conditions:
            search = search.filter('bool', must=filter_conditions)
        
        # Add comprehensive aggregations
        search = FacetedSearchService._add_facet_aggregations(search, selected_facets)
        
        # Pagination
        offset = (page - 1) * size
        search = search[offset:offset + size]
        
        response = await search.execute()
        
        # Format results
        products = [
            {
                'id': hit.meta.id,
                'name': hit.name,
                'brand': hit.brand,
                'category': hit.category,
                'price': hit.price,
                'average_rating': getattr(hit, 'average_rating', None)
            }
            for hit in response.hits
        ]
        
        # Format facets
        facets = FacetedSearchService._format_facets(response.aggregations, selected_facets)
        
        return {
            'total': response.hits.total.value,
            'products': products,
            'facets': facets,
            'page': page,
            'size': size
        }
    
    @staticmethod
    def _add_facet_aggregations(search: AsyncSearch, selected_facets: Dict[str, List[str]]) -> AsyncSearch:
        """Add facet aggregations with post-filters for drill-down."""
        
        # Create post-filter for each facet
        post_filters = {}
        if selected_facets:
            for facet_field, values in selected_facets.items():
                if values:
                    post_filters[facet_field] = Q('terms', **{facet_field: values})
        
        # Brand facet
        brand_agg = A('terms', field='brand', size=20)
        if 'brand' in post_filters:
            # Apply all filters except brand for brand facet
            other_filters = [f for k, f in post_filters.items() if k != 'brand']
            if other_filters:
                brand_agg = A('filter', Q('bool', must=other_filters)).metric('brand_terms', brand_agg)
        search.aggs['brands'] = brand_agg
        
        # Category facet
        category_agg = A('terms', field='category', size=15)
        if 'category' in post_filters:
            other_filters = [f for k, f in post_filters.items() if k != 'category']
            if other_filters:
                category_agg = A('filter', Q('bool', must=other_filters)).metric('category_terms', category_agg)
        search.aggs['categories'] = category_agg
        
        # Color facet
        color_agg = A('terms', field='color', size=10)
        if 'color' in post_filters:
            other_filters = [f for k, f in post_filters.items() if k != 'color']
            if other_filters:
                color_agg = A('filter', Q('bool', must=other_filters)).metric('color_terms', color_agg)
        search.aggs['colors'] = color_agg
        
        # Size facet
        size_agg = A('terms', field='size', size=10)
        if 'size' in post_filters:
            other_filters = [f for k, f in post_filters.items() if k != 'size']
            if other_filters:
                size_agg = A('filter', Q('bool', must=other_filters)).metric('size_terms', size_agg)
        search.aggs['sizes'] = size_agg
        
        # Price histogram
        search.aggs['price_histogram'] = A('histogram', field='price', interval=50, min_doc_count=1)
        
        # Rating distribution
        search.aggs['rating_distribution'] = A('histogram', field='average_rating', interval=1, min_doc_count=1)
        
        return search
    
    @staticmethod
    def _format_facets(aggs, selected_facets: Dict[str, List[str]]) -> Dict[str, Any]:
        """Format facet aggregations for response."""
        
        facets = {}
        
        for agg_name, agg_data in aggs.to_dict().items():
            facet_name = agg_name.replace('s', '')  # brands -> brand
            
            if 'buckets' in agg_data:
                buckets = agg_data['buckets']
            elif f'{facet_name}_terms' in agg_data and 'buckets' in agg_data[f'{facet_name}_terms']:
                buckets = agg_data[f'{facet_name}_terms']['buckets']
            else:
                continue
            
            formatted_buckets = []
            selected_values = selected_facets.get(facet_name, []) if selected_facets else []
            
            for bucket in buckets:
                formatted_buckets.append({
                    'value': bucket['key'],
                    'count': bucket['doc_count'],
                    'selected': bucket['key'] in selected_values
                })
            
            facets[facet_name] = {
                'buckets': formatted_buckets,
                'total_options': len(formatted_buckets)
            }
        
        return facets

# Faceted search endpoint
@app.post("/search/faceted")
async def faceted_search_endpoint(
    query: str = Query("*", description="Search query"),
    facets: str = Query(None, description="JSON string of selected facets"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Faceted search with drill-down capabilities."""
    
    selected_facets = None
    if facets:
        try:
            import json
            selected_facets = json.loads(facets)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid facets JSON")
    
    try:
        return await FacetedSearchService.faceted_search(query, selected_facets, page, size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Faceted search failed: {e}")
```

## Auto-complete and Suggestion Endpoints

### Advanced Auto-complete System
```python
# autocomplete.py - Advanced auto-complete and suggestions
from elasticsearch_dsl import AsyncSearch, Q
from typing import List, Dict, Any

class AutocompleteService:
    """Advanced auto-complete and suggestion service."""
    
    @staticmethod
    async def get_suggestions(
        query: str,
        suggestion_types: List[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get comprehensive search suggestions."""
        
        if not suggestion_types:
            suggestion_types = ['products', 'brands', 'categories']
        
        suggestions = {}
        
        # Product name suggestions
        if 'products' in suggestion_types:
            suggestions['products'] = await AutocompleteService._get_product_suggestions(query, limit)
        
        # Brand suggestions
        if 'brands' in suggestion_types:
            suggestions['brands'] = await AutocompleteService._get_brand_suggestions(query, limit)
        
        # Category suggestions
        if 'categories' in suggestion_types:
            suggestions['categories'] = await AutocompleteService._get_category_suggestions(query, limit)
        
        # Query corrections
        if 'corrections' in suggestion_types:
            suggestions['corrections'] = await AutocompleteService._get_query_corrections(query)
        
        # Popular searches
        if 'popular' in suggestion_types:
            suggestions['popular'] = await AutocompleteService._get_popular_searches(query, limit)
        
        return suggestions
    
    @staticmethod
    async def _get_product_suggestions(query: str, limit: int) -> List[Dict[str, Any]]:
        """Get product name suggestions."""
        
        search = AsyncSearch(index='products')
        search = search.suggest(
            'product_suggest',
            query,
            completion={
                'field': 'name.suggest',
                'size': limit * 2,  # Get more to filter duplicates
                'skip_duplicates': True
            }
        )
        
        response = await search.execute()
        
        suggestions = []
        seen_texts = set()
        
        if hasattr(response, 'suggest') and 'product_suggest' in response.suggest:
            for option in response.suggest.product_suggest[0].options:
                if option.text not in seen_texts and len(suggestions) < limit:
                    suggestions.append({
                        'text': option.text,
                        'type': 'product',
                        'score': option.score
                    })
                    seen_texts.add(option.text)
        
        return suggestions
    
    @staticmethod
    async def _get_brand_suggestions(query: str, limit: int) -> List[Dict[str, Any]]:
        """Get brand suggestions."""
        
        search = AsyncSearch(index='products')
        search = search.query('prefix', brand=query.lower())
        search.aggs.bucket('unique_brands', 'terms', field='brand', size=limit)
        search = search[:0]  # We only want aggregations
        
        response = await search.execute()
        
        suggestions = []
        if hasattr(response, 'aggregations') and 'unique_brands' in response.aggregations:
            for bucket in response.aggregations.unique_brands.buckets:
                suggestions.append({
                    'text': bucket.key,
                    'type': 'brand',
                    'count': bucket.doc_count
                })
        
        return suggestions
    
    @staticmethod
    async def _get_category_suggestions(query: str, limit: int) -> List[Dict[str, Any]]:
        """Get category suggestions."""
        
        search = AsyncSearch(index='products')
        search = search.query('prefix', category=query.lower())
        search.aggs.bucket('unique_categories', 'terms', field='category', size=limit)
        search = search[:0]
        
        response = await search.execute()
        
        suggestions = []
        if hasattr(response, 'aggregations') and 'unique_categories' in response.aggregations:
            for bucket in response.aggregations.unique_categories.buckets:
                suggestions.append({
                    'text': bucket.key,
                    'type': 'category',
                    'count': bucket.doc_count
                })
        
        return suggestions
    
    @staticmethod
    async def _get_query_corrections(query: str) -> List[Dict[str, Any]]:
        """Get query spelling corrections."""
        
        search = AsyncSearch(index='products')
        search = search.suggest(
            'spelling_suggest',
            query,
            term={
                'field': 'name',
                'suggest_mode': 'popular',
                'sort': 'frequency'
            }
        )
        
        response = await search.execute()
        
        corrections = []
        if hasattr(response, 'suggest') and 'spelling_suggest' in response.suggest:
            for suggest in response.suggest.spelling_suggest:
                for option in suggest.options:
                    corrections.append({
                        'text': option.text,
                        'type': 'correction',
                        'score': option.score,
                        'freq': option.freq
                    })
        
        return corrections
    
    @staticmethod
    async def _get_popular_searches(query: str, limit: int) -> List[Dict[str, Any]]:
        """Get popular searches (mock implementation)."""
        
        # In a real implementation, you'd track search queries and their frequency
        # This could be stored in a separate index or database
        
        popular_searches = [
            {'text': 'laptop', 'type': 'popular', 'frequency': 1000},
            {'text': 'smartphone', 'type': 'popular', 'frequency': 800},
            {'text': 'headphones', 'type': 'popular', 'frequency': 600},
            {'text': 'keyboard', 'type': 'popular', 'frequency': 400},
            {'text': 'mouse', 'type': 'popular', 'frequency': 350}
        ]
        
        # Filter based on query prefix
        filtered_searches = [
            search for search in popular_searches
            if search['text'].startswith(query.lower())
        ]
        
        return filtered_searches[:limit]

# Auto-complete endpoints
@app.get("/autocomplete")
async def autocomplete_endpoint(
    q: str = Query(..., min_length=1, max_length=50),
    types: str = Query("products,brands,categories", description="Comma-separated suggestion types"),
    limit: int = Query(10, ge=1, le=20)
):
    """Advanced auto-complete endpoint."""
    
    suggestion_types = [t.strip() for t in types.split(',')]
    
    try:
        return await AutocompleteService.get_suggestions(q, suggestion_types, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {e}")

@app.get("/suggest/popular")
async def popular_suggestions(
    limit: int = Query(10, ge=1, le=50)
):
    """Get popular search suggestions."""
    
    # This would typically come from analytics data
    popular_suggestions = [
        {'text': 'laptop computers', 'frequency': 1500},
        {'text': 'wireless headphones', 'frequency': 1200},
        {'text': 'smartphone cases', 'frequency': 1100},
        {'text': 'gaming keyboard', 'frequency': 900},
        {'text': 'bluetooth speakers', 'frequency': 800}
    ]
    
    return {'suggestions': popular_suggestions[:limit]}
```

## Search Result Highlighting

### Advanced Highlighting Implementation
```python
# highlighting.py - Advanced search result highlighting
from elasticsearch_dsl import AsyncSearch
from typing import Dict, List, Any
import re

class HighlightingService:
    """Advanced search result highlighting service."""
    
    @staticmethod
    async def search_with_highlighting(
        query: str,
        page: int = 1,
        size: int = 20,
        highlight_fields: List[str] = None
    ) -> Dict[str, Any]:
        """Search with advanced highlighting."""
        
        if not highlight_fields:
            highlight_fields = ['name', 'description', 'brand']
        
        search = AsyncSearch(index='products')
        
        # Text query
        search = search.query(
            'multi_match',
            query=query,
            fields=['name^3', 'description^1', 'brand^2'],
            type='best_fields'
        )
        
        # Advanced highlighting configuration
        highlight_config = {
            'fields': {},
            'pre_tags': ['<mark>'],
            'post_tags': ['</mark>'],
            'fragment_size': 150,
            'number_of_fragments': 3,
            'fragmenter': 'span',
            'order': 'score',
            'require_field_match': False,
            'boundary_scanner': 'sentence',
            'boundary_max_scan': 20
        }
        
        # Configure highlighting for each field
        for field in highlight_fields:
            if field == 'name':
                highlight_config['fields'][field] = {
                    'fragment_size': 0,  # Highlight entire field
                    'number_of_fragments': 0
                }
            elif field == 'description':
                highlight_config['fields'][field] = {
                    'fragment_size': 200,
                    'number_of_fragments': 2,
                    'fragmenter': 'sentence'
                }
            else:
                highlight_config['fields'][field] = {
                    'fragment_size': 100,
                    'number_of_fragments': 1
                }
        
        search = search.highlight(**highlight_config)
        
        # Pagination
        offset = (page - 1) * size
        search = search[offset:offset + size]
        
        response = await search.execute()
        
        # Format results with highlighting
        products = []
        for hit in response.hits:
            product = {
                'id': hit.meta.id,
                'name': hit.name,
                'description': hit.description,
                'brand': hit.brand,
                'price': hit.price,
                'score': hit.meta.score
            }
            
            # Add highlights
            if hasattr(hit.meta, 'highlight'):
                highlights = {}
                for field, fragments in hit.meta.highlight.to_dict().items():
                    highlights[field] = fragments
                product['highlights'] = highlights
                
                # Update display text with highlighted version
                product = HighlightingService._apply_highlights(product, highlights)
            
            products.append(product)
        
        return {
            'total': response.hits.total.value,
            'products': products,
            'page': page,
            'size': size
        }
    
    @staticmethod
    def _apply_highlights(product: Dict[str, Any], highlights: Dict[str, List[str]]) -> Dict[str, Any]:
        """Apply highlights to product display fields."""
        
        # Replace field values with highlighted versions
        for field, fragments in highlights.items():
            if field in product and fragments:
                if field == 'name':
                    # For name, use the highlighted version directly
                    product[f'{field}_highlighted'] = fragments[0]
                else:
                    # For other fields, use fragments
                    product[f'{field}_highlighted'] = fragments
        
        return product

# Custom highlighting for specific use cases
class CustomHighlighter:
    """Custom highlighting for specific search scenarios."""
    
    @staticmethod
    def highlight_product_specs(text: str, query: str) -> str:
        """Custom highlighting for product specifications."""
        
        # Split query into terms
        terms = query.lower().split()
        
        highlighted_text = text
        for term in terms:
            if len(term) >= 3:  # Only highlight terms with 3+ characters
                # Case-insensitive regex replacement
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                highlighted_text = pattern.sub(f'<mark>{term}</mark>', highlighted_text)
        
        return highlighted_text
    
    @staticmethod
    def highlight_price_matches(price: float, query: str) -> str:
        """Highlight price matches in search results."""
        
        price_str = f"${price:.2f}"
        
        # Check if query contains price-related terms
        price_terms = re.findall(r'\$?\d+(?:\.\d{2})?', query)
        
        for term in price_terms:
            clean_term = term.replace('$', '')
            try:
                query_price = float(clean_term)
                if abs(query_price - price) < 10:  # Within $10
                    price_str = f'<mark>${price:.2f}</mark>'
                    break
            except ValueError:
                continue
        
        return price_str

# Highlighting endpoint
@app.get("/search/highlighted")
async def search_with_highlighting_endpoint(
    q: str = Query(..., min_length=1),
    fields: str = Query("name,description,brand", description="Fields to highlight"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Search with advanced highlighting."""
    
    highlight_fields = [f.strip() for f in fields.split(',')]
    
    try:
        return await HighlightingService.search_with_highlighting(q, page, size, highlight_fields)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Highlighted search failed: {e}")
```

## Advanced Search Features

### Multi-Language and Geo Search
```python
# advanced_features.py - Advanced search features
from elasticsearch_dsl import GeoPoint, GeoDistance
from typing import Optional, Tuple

class AdvancedSearchService:
    """Advanced search features including geo and multi-language."""
    
    @staticmethod
    async def geo_search(
        query: str,
        location: Tuple[float, float],  # (lat, lon)
        radius: str = "10km",
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Geographic search with distance filtering."""
        
        search = AsyncSearch(index='stores')  # Assuming stores index
        
        # Text query
        if query.strip():
            search = search.query('multi_match', query=query, fields=['name', 'description'])
        
        # Geo distance filter
        search = search.filter(
            'geo_distance',
            distance=radius,
            location={
                'lat': location[0],
                'lon': location[1]
            }
        )
        
        # Sort by distance
        search = search.sort({
            '_geo_distance': {
                'location': {
                    'lat': location[0],
                    'lon': location[1]
                },
                'order': 'asc',
                'unit': 'km'
            }
        })
        
        # Pagination
        offset = (page - 1) * size
        search = search[offset:offset + size]
        
        response = await search.execute()
        
        results = []
        for hit in response.hits:
            store = {
                'id': hit.meta.id,
                'name': hit.name,
                'address': hit.address,
                'distance_km': hit.meta.sort[0] if hit.meta.sort else None
            }
            results.append(store)
        
        return {
            'total': response.hits.total.value,
            'stores': results,
            'center': {'lat': location[0], 'lon': location[1]},
            'radius': radius
        }
    
    @staticmethod
    async def multi_language_search(
        query: str,
        language: str = 'en',
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Multi-language search with language-specific analyzers."""
        
        search = AsyncSearch(index='products_multilang')
        
        # Language-specific field mapping
        language_fields = {
            'en': ['name_en^3', 'description_en'],
            'es': ['name_es^3', 'description_es'],
            'fr': ['name_fr^3', 'description_fr'],
            'de': ['name_de^3', 'description_de']
        }
        
        fields = language_fields.get(language, language_fields['en'])
        
        # Multi-match query with language-specific fields
        search = search.query(
            'multi_match',
            query=query,
            fields=fields,
            type='best_fields',
            analyzer=f'{language}_analyzer'
        )
        
        # Boost results that match the requested language
        search = search.query(
            'function_score',
            query=search.to_dict()['query'],
            functions=[
                {
                    'filter': {'term': {'primary_language': language}},
                    'weight': 2.0
                }
            ],
            score_mode='multiply'
        )
        
        offset = (page - 1) * size
        search = search[offset:offset + size]
        
        response = await search.execute()
        
        products = []
        for hit in response.hits:
            # Get language-specific content
            name_field = f'name_{language}'
            desc_field = f'description_{language}'
            
            product = {
                'id': hit.meta.id,
                'name': getattr(hit, name_field, hit.name_en),
                'description': getattr(hit, desc_field, hit.description_en),
                'price': hit.price,
                'language': language,
                'score': hit.meta.score
            }
            products.append(product)
        
        return {
            'total': response.hits.total.value,
            'products': products,
            'language': language
        }

# Advanced search endpoints
@app.get("/search/geo")
async def geo_search_endpoint(
    q: str = Query("", description="Search query"),
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius: str = Query("10km", regex=r'^\d+(?:\.\d+)?(?:km|mi|m)$'),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Geographic search endpoint."""
    
    try:
        return await AdvancedSearchService.geo_search(q, (lat, lon), radius, page, size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geo search failed: {e}")

@app.get("/search/multilang")
async def multilang_search_endpoint(
    q: str = Query(..., min_length=1),
    lang: str = Query("en", regex="^(en|es|fr|de)$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Multi-language search endpoint."""
    
    try:
        return await AdvancedSearchService.multi_language_search(q, lang, page, size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-language search failed: {e}")
```

## Search Analytics

### Search Analytics Implementation
```python
# search_analytics.py - Search analytics and tracking
from datetime import datetime, timedelta
from typing import Dict, List, Any

class SearchAnalyticsService:
    """Track and analyze search behavior."""
    
    @staticmethod
    async def track_search_event(
        query: str,
        results_count: int,
        user_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        response_time_ms: int = 0
    ):
        """Track search events for analytics."""
        
        search_event = {
            'timestamp': datetime.utcnow(),
            'query': query.lower().strip(),
            'results_count': results_count,
            'user_id': user_id,
            'filters': filters or {},
            'response_time_ms': response_time_ms,
            'has_results': results_count > 0
        }
        
        # Index to analytics index
        analytics_doc = AsyncDocument()
        analytics_doc.meta.index = 'search_analytics'
        
        for key, value in search_event.items():
            setattr(analytics_doc, key, value)
        
        await analytics_doc.save()
    
    @staticmethod
    async def get_search_analytics(
        days: int = 7,
        include_queries: bool = True
    ) -> Dict[str, Any]:
        """Get search analytics for the specified period."""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        search = AsyncSearch(index='search_analytics')
        search = search.filter('range', timestamp={
            'gte': start_date.isoformat(),
            'lte': end_date.isoformat()
        })
        
        # Total searches
        search.aggs.metric('total_searches', 'value_count', field='query')
        
        # Average response time
        search.aggs.metric('avg_response_time', 'avg', field='response_time_ms')
        
        # Zero result searches
        search.aggs.bucket('zero_results', 'filter', filter={'term': {'has_results': False}})
        
        # Popular queries
        if include_queries:
            search.aggs.bucket('popular_queries', 'terms', field='query.keyword', size=20)
        
        # Search volume over time
        search.aggs.bucket('search_volume', 'date_histogram', 
                          field='timestamp', 
                          calendar_interval='1d')
        
        # Most used filters
        search.aggs.bucket('filter_usage', 'nested', path='filters').\
                    bucket('filter_keys', 'terms', field='filters.keyword')
        
        search = search[:0]  # We only want aggregations
        
        response = await search.execute()
        
        analytics = {
            'period_days': days,
            'total_searches': response.aggregations.total_searches.value,
            'avg_response_time_ms': response.aggregations.avg_response_time.value,
            'zero_result_rate': (
                response.aggregations.zero_results.doc_count / 
                response.aggregations.total_searches.value
            ) if response.aggregations.total_searches.value > 0 else 0
        }
        
        if include_queries:
            analytics['popular_queries'] = [
                {
                    'query': bucket.key,
                    'count': bucket.doc_count
                }
                for bucket in response.aggregations.popular_queries.buckets
            ]
        
        analytics['daily_volume'] = [
            {
                'date': bucket.key_as_string,
                'searches': bucket.doc_count
            }
            for bucket in response.aggregations.search_volume.buckets
        ]
        
        return analytics

# Analytics endpoints
@app.post("/analytics/search")
async def track_search(
    query: str,
    results_count: int,
    response_time_ms: int = 0,
    user_id: Optional[str] = None
):
    """Track a search event."""
    
    try:
        await SearchAnalyticsService.track_search_event(
            query, results_count, user_id, None, response_time_ms
        )
        return {"status": "tracked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track search: {e}")

@app.get("/analytics/dashboard")
async def search_analytics_dashboard(
    days: int = Query(7, ge=1, le=90),
    include_queries: bool = Query(True)
):
    """Get search analytics dashboard data."""
    
    try:
        return await SearchAnalyticsService.get_search_analytics(days, include_queries)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {e}")
```

## Performance Optimization

### Search Performance Optimization
```python
# performance.py - Search performance optimization
import asyncio
from functools import wraps
import time

class SearchPerformanceOptimizer:
    """Optimize search performance with caching and batching."""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def cache_search_results(self, ttl: int = 300):
        """Decorator to cache search results."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Create cache key from function arguments
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                # Check cache
                if cache_key in self.cache:
                    cached_result, timestamp = self.cache[cache_key]
                    if time.time() - timestamp < ttl:
                        return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                self.cache[cache_key] = (result, time.time())
                
                return result
            return wrapper
        return decorator
    
    async def batch_get_products(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """Efficiently batch get multiple products."""
        
        if not product_ids:
            return []
        
        search = AsyncSearch(index='products')
        search = search.filter('terms', _id=product_ids)
        search = search[:len(product_ids)]
        
        response = await search.execute()
        
        # Maintain order of requested IDs
        products_by_id = {hit.meta.id: hit for hit in response.hits}
        ordered_products = []
        
        for product_id in product_ids:
            if product_id in products_by_id:
                hit = products_by_id[product_id]
                ordered_products.append({
                    'id': hit.meta.id,
                    'name': hit.name,
                    'price': hit.price,
                    'brand': hit.brand
                })
        
        return ordered_products
    
    async def parallel_search_operations(self, operations: List[Dict[str, Any]]) -> List[Any]:
        """Execute multiple search operations in parallel."""
        
        tasks = []
        for operation in operations:
            if operation['type'] == 'search':
                task = self._execute_search(operation['params'])
            elif operation['type'] == 'suggest':
                task = self._execute_suggest(operation['params'])
            elif operation['type'] == 'aggregation':
                task = self._execute_aggregation(operation['params'])
            else:
                continue
            
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _execute_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search operation."""
        # Implementation depends on specific search parameters
        pass
    
    async def _execute_suggest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute suggestion operation."""
        pass
    
    async def _execute_aggregation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute aggregation operation."""
        pass

# Global performance optimizer
performance_optimizer = SearchPerformanceOptimizer()

# Optimized search endpoint
@app.post("/search/optimized")
@performance_optimizer.cache_search_results(ttl=300)
async def optimized_search(request: SearchRequest):
    """Optimized search endpoint with caching."""
    
    start_time = time.time()
    
    # Use cached/optimized search service
    result = await EcommerceSearchService.search_products(request)
    
    # Add performance metrics
    result.query_time_ms = int((time.time() - start_time) * 1000)
    
    return result
```

## Next Steps

1. **[Integration Examples](03_integration-examples.md)** - Authentication, monitoring, and background tasks
2. **[Performance Optimization](../06-production-patterns/03_performance-optimization.md)** - Advanced scaling and efficiency
3. **[Deployment Patterns](../07-testing-deployment/02_deployment-patterns.md)** - Production deployment strategies

## Additional Resources

- **Elasticsearch Guide**: [elastic.co/guide/en/elasticsearch/reference/current](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- **Search UI Patterns**: [elastic.co/guide/en/app-search/current](https://www.elastic.co/guide/en/app-search/current/)
- **FastAPI Performance**: [fastapi.tiangolo.com/advanced](https://fastapi.tiangolo.com/advanced/)