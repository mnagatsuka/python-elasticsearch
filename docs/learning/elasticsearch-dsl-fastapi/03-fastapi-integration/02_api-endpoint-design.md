# API Endpoint Design

Comprehensive guide to designing RESTful search APIs with FastAPI and Elasticsearch-DSL, including endpoint patterns, HTTP methods, and OpenAPI integration.

## Table of Contents
- [RESTful Search API Design](#restful-search-api-design)
- [Endpoint Structure and Patterns](#endpoint-structure-and-patterns)
- [HTTP Methods and Status Codes](#http-methods-and-status-codes)
- [Request and Response Schemas](#request-and-response-schemas)
- [Pagination and Filtering](#pagination-and-filtering)
- [Error Handling and Validation](#error-handling-and-validation)
- [OpenAPI Documentation](#openapi-documentation)
- [Performance Considerations](#performance-considerations)
- [Next Steps](#next-steps)

## RESTful Search API Design

### Core API Principles

```python
from fastapi import FastAPI, Query, Path, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from elasticsearch_dsl import AsyncSearch, Q, A
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Product Search API",
    description="RESTful API for product search using Elasticsearch",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchResultMeta(BaseModel):
    """Metadata for search results"""
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Results per page")
    pages: int = Field(..., description="Total number of pages")
    took_ms: int = Field(..., description="Query execution time in milliseconds")
    max_score: Optional[float] = Field(None, description="Maximum relevance score")

class ProductSearchResult(BaseModel):
    """Individual product search result"""
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Product category")
    price: float = Field(..., description="Product price")
    rating: Optional[float] = Field(None, description="Average rating")
    in_stock: bool = Field(..., description="Stock availability")
    score: Optional[float] = Field(None, description="Relevance score")
    highlights: Optional[Dict[str, List[str]]] = Field(None, description="Search highlights")

class SearchResponse(BaseModel):
    """Search API response"""
    results: List[ProductSearchResult] = Field(..., description="Search results")
    meta: SearchResultMeta = Field(..., description="Search metadata")
    aggregations: Optional[Dict[str, Any]] = Field(None, description="Aggregation results")

# API versioning
API_V1_PREFIX = "/api/v1"
```

### Resource-Based Endpoint Design

```python
class SearchAPIRouter:
    """Router class for organizing search endpoints"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all search-related routes"""
        
        # Product search endpoints
        self.app.get(
            f"{API_V1_PREFIX}/products/search",
            response_model=SearchResponse,
            summary="Search products",
            description="Search for products with text query and filters"
        )(self.search_products)
        
        self.app.post(
            f"{API_V1_PREFIX}/products/search",
            response_model=SearchResponse,
            summary="Advanced product search",
            description="Advanced search with complex query parameters"
        )(self.advanced_search_products)
        
        self.app.get(
            f"{API_V1_PREFIX}/products/{{product_id}}/similar",
            response_model=SearchResponse,
            summary="Find similar products",
            description="Find products similar to a specific product"
        )(self.find_similar_products)
        
        # Category-specific endpoints
        self.app.get(
            f"{API_V1_PREFIX}/categories/{{category}}/products",
            response_model=SearchResponse,
            summary="Search products in category",
            description="Search for products within a specific category"
        )(self.search_products_in_category)
        
        # Suggestion and autocomplete
        self.app.get(
            f"{API_V1_PREFIX}/search/suggestions",
            response_model=Dict[str, List[str]],
            summary="Get search suggestions",
            description="Get autocomplete suggestions for search queries"
        )(self.get_search_suggestions)
        
        # Aggregation endpoints
        self.app.get(
            f"{API_V1_PREFIX}/products/facets",
            response_model=Dict[str, Any],
            summary="Get product facets",
            description="Get aggregated facets for filtering"
        )(self.get_product_facets)
        
        # Search analytics
        self.app.get(
            f"{API_V1_PREFIX}/search/analytics",
            response_model=Dict[str, Any],
            summary="Search analytics",
            description="Get search analytics and trends"
        )(self.get_search_analytics)
    
    async def search_products(
        self,
        q: str = Query(..., description="Search query", min_length=1),
        category: Optional[str] = Query(None, description="Product category"),
        price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
        price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
        rating_min: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
        in_stock: Optional[bool] = Query(None, description="In stock filter"),
        sort_by: str = Query("relevance", description="Sort field"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Results per page"),
        include_highlights: bool = Query(True, description="Include search highlights"),
        include_aggregations: bool = Query(False, description="Include aggregations")
    ) -> SearchResponse:
        """Basic product search endpoint"""
        
        try:
            # Build search query
            search = AsyncSearch(index='products')
            
            # Add text query
            if q:
                search = search.query('multi_match',
                                    query=q,
                                    fields=['name^3', 'description^2', 'category'],
                                    type='best_fields',
                                    operator='and')
            
            # Add filters
            if category:
                search = search.filter('term', category=category)
            
            if price_min is not None or price_max is not None:
                price_range = {}
                if price_min is not None:
                    price_range['gte'] = price_min
                if price_max is not None:
                    price_range['lte'] = price_max
                search = search.filter('range', price=price_range)
            
            if rating_min is not None:
                search = search.filter('range', rating={'gte': rating_min})
            
            if in_stock is not None:
                search = search.filter('term', in_stock=in_stock)
            
            # Add sorting
            if sort_by == "relevance":
                search = search.sort('-_score')
            elif sort_by == "price":
                sort_field = 'price' if sort_order == 'asc' else '-price'
                search = search.sort(sort_field)
            elif sort_by == "rating":
                sort_field = 'rating' if sort_order == 'asc' else '-rating'
                search = search.sort(sort_field)
            elif sort_by == "name":
                sort_field = 'name.keyword' if sort_order == 'asc' else '-name.keyword'
                search = search.sort(sort_field)
            
            # Add highlights
            if include_highlights:
                search = search.highlight('name', 'description',
                                        fragment_size=150,
                                        number_of_fragments=2)
            
            # Add aggregations
            if include_aggregations:
                search.aggs.bucket('categories', 'terms', field='category', size=10)
                search.aggs.bucket('price_ranges', 'range', field='price',
                                 ranges=[
                                     {'to': 50},
                                     {'from': 50, 'to': 100},
                                     {'from': 100, 'to': 500},
                                     {'from': 500}
                                 ])
                search.aggs.metric('avg_rating', 'avg', field='rating')
            
            # Add pagination
            start = (page - 1) * size
            search = search[start:start + size]
            
            # Execute search
            response = await search.execute()
            
            # Format results
            results = []
            for hit in response.hits:
                result = ProductSearchResult(
                    id=hit.meta.id,
                    name=hit.name,
                    description=getattr(hit, 'description', None),
                    category=hit.category,
                    price=hit.price,
                    rating=getattr(hit, 'rating', None),
                    in_stock=hit.in_stock,
                    score=hit.meta.score
                )
                
                # Add highlights if present
                if include_highlights and hasattr(hit.meta, 'highlight'):
                    result.highlights = hit.meta.highlight.to_dict()
                
                results.append(result)
            
            # Calculate metadata
            total = response.hits.total.value
            pages = (total + size - 1) // size
            
            meta = SearchResultMeta(
                total=total,
                page=page,
                size=size,
                pages=pages,
                took_ms=response.took,
                max_score=response.hits.max_score
            )
            
            # Format aggregations
            aggregations = None
            if include_aggregations and hasattr(response, 'aggregations'):
                aggregations = response.aggregations.to_dict()
            
            return SearchResponse(
                results=results,
                meta=meta,
                aggregations=aggregations
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search failed: {str(e)}"
            )
    
    async def advanced_search_products(
        self,
        search_request: "AdvancedSearchRequest" = Body(...)
    ) -> SearchResponse:
        """Advanced search with complex parameters in request body"""
        
        try:
            search = AsyncSearch(index='products')
            
            # Build complex query from request
            if search_request.query:
                # Multi-field search with field-specific boosts
                search = search.query('multi_match',
                                    query=search_request.query,
                                    fields=search_request.search_fields,
                                    type=search_request.match_type,
                                    operator=search_request.operator,
                                    minimum_should_match=search_request.minimum_should_match)
            
            # Apply complex filters
            for filter_item in search_request.filters:
                if filter_item.type == 'term':
                    search = search.filter('term', **{filter_item.field: filter_item.value})
                elif filter_item.type == 'range':
                    search = search.filter('range', **{filter_item.field: filter_item.value})
                elif filter_item.type == 'terms':
                    search = search.filter('terms', **{filter_item.field: filter_item.value})
            
            # Apply boost queries
            for boost in search_request.boost_queries:
                boost_query = Q(boost.query_type, **boost.parameters)
                search = search.query('function_score',
                                    query=search.to_dict()['query'],
                                    functions=[{
                                        'filter': boost_query,
                                        'weight': boost.weight
                                    }])
            
            # Add custom sorting
            for sort_item in search_request.sort:
                if sort_item.order == 'asc':
                    search = search.sort(sort_item.field)
                else:
                    search = search.sort(f'-{sort_item.field}')
            
            # Execute and format response similar to basic search
            # ... (implementation similar to search_products)
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Advanced search failed: {str(e)}"
            )
    
    async def find_similar_products(
        self,
        product_id: str = Path(..., description="Product ID"),
        limit: int = Query(10, ge=1, le=50, description="Number of similar products"),
        categories: Optional[List[str]] = Query(None, description="Limit to categories")
    ) -> SearchResponse:
        """Find products similar to a given product"""
        
        try:
            # First, get the reference product
            product_search = AsyncSearch(index='products')
            product_search = product_search.filter('term', _id=product_id)
            product_response = await product_search.execute()
            
            if not product_response.hits:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product {product_id} not found"
                )
            
            reference_product = product_response.hits[0]
            
            # Build more-like-this query
            search = AsyncSearch(index='products')
            search = search.query('more_like_this',
                                fields=['name', 'description', 'category'],
                                like=[{'_index': 'products', '_id': product_id}],
                                min_term_freq=1,
                                max_query_terms=12,
                                minimum_should_match='30%')
            
            # Exclude the reference product
            search = search.exclude('term', _id=product_id)
            
            # Filter by categories if specified
            if categories:
                search = search.filter('terms', category=categories)
            
            # Limit results
            search = search[:limit]
            
            # Execute and format response
            response = await search.execute()
            
            results = []
            for hit in response.hits:
                result = ProductSearchResult(
                    id=hit.meta.id,
                    name=hit.name,
                    description=getattr(hit, 'description', None),
                    category=hit.category,
                    price=hit.price,
                    rating=getattr(hit, 'rating', None),
                    in_stock=hit.in_stock,
                    score=hit.meta.score
                )
                results.append(result)
            
            meta = SearchResultMeta(
                total=len(results),
                page=1,
                size=limit,
                pages=1,
                took_ms=response.took,
                max_score=response.hits.max_score
            )
            
            return SearchResponse(results=results, meta=meta)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Similar products search failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Similar products search failed: {str(e)}"
            )

# Initialize router
search_router = SearchAPIRouter(app)
```

## Endpoint Structure and Patterns

### Resource Hierarchy

```python
class ResourceEndpoints:
    """Organized endpoint structure following REST conventions"""
    
    # Primary resource endpoints
    PRODUCTS_BASE = "/api/v1/products"
    CATEGORIES_BASE = "/api/v1/categories"
    SEARCH_BASE = "/api/v1/search"
    
    # Nested resource patterns
    @staticmethod
    def get_product_endpoints():
        return {
            # Collection endpoints
            "search_products": f"{ResourceEndpoints.PRODUCTS_BASE}/search",
            "list_products": f"{ResourceEndpoints.PRODUCTS_BASE}",
            "create_product": f"{ResourceEndpoints.PRODUCTS_BASE}",
            
            # Individual resource endpoints
            "get_product": f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}",
            "update_product": f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}",
            "delete_product": f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}",
            
            # Sub-resource endpoints
            "product_similar": f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}/similar",
            "product_reviews": f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}/reviews",
            "product_recommendations": f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}/recommendations",
            
            # Bulk operations
            "bulk_search": f"{ResourceEndpoints.PRODUCTS_BASE}/bulk-search",
            "bulk_update": f"{ResourceEndpoints.PRODUCTS_BASE}/bulk-update"
        }
    
    @staticmethod
    def get_search_endpoints():
        return {
            # General search endpoints
            "universal_search": f"{ResourceEndpoints.SEARCH_BASE}",
            "search_suggestions": f"{ResourceEndpoints.SEARCH_BASE}/suggestions",
            "search_analytics": f"{ResourceEndpoints.SEARCH_BASE}/analytics",
            
            # Type-specific searches
            "search_products": f"{ResourceEndpoints.SEARCH_BASE}/products",
            "search_categories": f"{ResourceEndpoints.SEARCH_BASE}/categories",
            "search_brands": f"{ResourceEndpoints.SEARCH_BASE}/brands",
            
            # Advanced search features
            "semantic_search": f"{ResourceEndpoints.SEARCH_BASE}/semantic",
            "visual_search": f"{ResourceEndpoints.SEARCH_BASE}/visual",
            "voice_search": f"{ResourceEndpoints.SEARCH_BASE}/voice"
        }

# Endpoint pattern implementations
@app.get(f"{ResourceEndpoints.PRODUCTS_BASE}")
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_date"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    category: Optional[str] = Query(None),
    active_only: bool = Query(True)
) -> SearchResponse:
    """List products with pagination and filtering"""
    
    search = AsyncSearch(index='products')
    
    # Apply filters
    if active_only:
        search = search.filter('term', active=True)
    
    if category:
        search = search.filter('term', category=category)
    
    # Apply sorting
    sort_field = sort_by if sort_order == 'asc' else f'-{sort_by}'
    search = search.sort(sort_field)
    
    # Apply pagination
    start = (page - 1) * size
    search = search[start:start + size]
    
    response = await search.execute()
    
    # Format response (similar to search_products)
    # ...

@app.post(f"{ResourceEndpoints.PRODUCTS_BASE}")
async def create_product(
    product: "ProductCreateRequest" = Body(...)
) -> Dict[str, Any]:
    """Create a new product"""
    
    # Create product document
    product_doc = ProductDocument(
        name=product.name,
        description=product.description,
        category=product.category,
        price=product.price,
        # ... other fields
    )
    
    # Save to Elasticsearch
    await product_doc.save()
    
    return {
        "success": True,
        "id": product_doc.meta.id,
        "message": "Product created successfully"
    }

@app.get(f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}")
async def get_product(
    product_id: str = Path(..., description="Product ID")
) -> ProductSearchResult:
    """Get a specific product by ID"""
    
    try:
        product_doc = await ProductDocument.get(product_id)
        
        return ProductSearchResult(
            id=product_doc.meta.id,
            name=product_doc.name,
            description=product_doc.description,
            category=product_doc.category,
            price=product_doc.price,
            rating=product_doc.rating,
            in_stock=product_doc.in_stock
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

@app.put(f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}")
async def update_product(
    product_id: str = Path(..., description="Product ID"),
    product_update: "ProductUpdateRequest" = Body(...)
) -> Dict[str, Any]:
    """Update a specific product"""
    
    try:
        product_doc = await ProductDocument.get(product_id)
        
        # Update fields
        for field, value in product_update.dict(exclude_unset=True).items():
            setattr(product_doc, field, value)
        
        await product_doc.save()
        
        return {
            "success": True,
            "message": "Product updated successfully"
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )

@app.delete(f"{ResourceEndpoints.PRODUCTS_BASE}/{{product_id}}")
async def delete_product(
    product_id: str = Path(..., description="Product ID")
) -> Dict[str, Any]:
    """Delete a specific product"""
    
    try:
        product_doc = await ProductDocument.get(product_id)
        await product_doc.delete()
        
        return {
            "success": True,
            "message": "Product deleted successfully"
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
```

## HTTP Methods and Status Codes

### Comprehensive HTTP Method Usage

```python
from fastapi import status
from fastapi.responses import JSONResponse

class HTTPMethodPatterns:
    """HTTP method patterns for search APIs"""
    
    # GET - Safe, idempotent operations
    @app.get("/api/v1/products/search", status_code=status.HTTP_200_OK)
    async def search_products_get():
        """GET method for basic search operations"""
        pass
    
    # POST - Complex search operations, non-idempotent
    @app.post("/api/v1/products/search", status_code=status.HTTP_200_OK)
    async def search_products_post():
        """POST method for complex search with request body"""
        pass
    
    # PUT - Full resource replacement
    @app.put("/api/v1/products/{product_id}", status_code=status.HTTP_200_OK)
    async def replace_product():
        """PUT method for complete resource replacement"""
        pass
    
    # PATCH - Partial resource updates
    @app.patch("/api/v1/products/{product_id}", status_code=status.HTTP_200_OK)
    async def update_product_partial():
        """PATCH method for partial resource updates"""
        pass
    
    # DELETE - Resource deletion
    @app.delete("/api/v1/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_product():
        """DELETE method for resource removal"""
        pass
    
    # HEAD - Metadata only
    @app.head("/api/v1/products/{product_id}")
    async def check_product_exists():
        """HEAD method for existence checks"""
        pass

class StatusCodeHandler:
    """Proper HTTP status code usage"""
    
    @staticmethod
    def success_responses():
        return {
            status.HTTP_200_OK: "Successful operation",
            status.HTTP_201_CREATED: "Resource created",
            status.HTTP_202_ACCEPTED: "Request accepted for processing",
            status.HTTP_204_NO_CONTENT: "Successful operation with no content"
        }
    
    @staticmethod
    def client_error_responses():
        return {
            status.HTTP_400_BAD_REQUEST: "Invalid request parameters",
            status.HTTP_401_UNAUTHORIZED: "Authentication required",
            status.HTTP_403_FORBIDDEN: "Access denied",
            status.HTTP_404_NOT_FOUND: "Resource not found",
            status.HTTP_409_CONFLICT: "Resource conflict",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "Validation error"
        }
    
    @staticmethod
    def server_error_responses():
        return {
            status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal server error",
            status.HTTP_502_BAD_GATEWAY: "Elasticsearch unavailable",
            status.HTTP_503_SERVICE_UNAVAILABLE: "Service temporarily unavailable",
            status.HTTP_504_GATEWAY_TIMEOUT: "Elasticsearch timeout"
        }

# Comprehensive endpoint with all status codes
@app.post(
    "/api/v1/products/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Search completed successfully"},
        400: {"description": "Invalid search parameters"},
        422: {"description": "Validation error"},
        500: {"description": "Search execution failed"},
        503: {"description": "Elasticsearch unavailable"}
    }
)
async def comprehensive_search(
    search_request: "SearchRequest" = Body(...)
):
    """Comprehensive search endpoint with proper status code handling"""
    
    try:
        # Validate request
        if not search_request.query and not search_request.filters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either query or filters must be provided"
            )
        
        # Execute search
        search = AsyncSearch(index='products')
        # ... search logic ...
        response = await search.execute()
        
        # Return successful response
        return SearchResponse(
            results=[],  # formatted results
            meta=SearchResultMeta(
                total=response.hits.total.value,
                page=1,
                size=10,
                pages=1,
                took_ms=response.took
            )
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {e}"
        )
    
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elasticsearch service unavailable"
        )
    
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Search request timed out"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

## Request and Response Schemas

### Comprehensive Schema Definitions

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class MatchType(str, Enum):
    BEST_FIELDS = "best_fields"
    MOST_FIELDS = "most_fields"
    CROSS_FIELDS = "cross_fields"
    PHRASE = "phrase"
    PHRASE_PREFIX = "phrase_prefix"

class Operator(str, Enum):
    AND = "and"
    OR = "or"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class FilterType(str, Enum):
    TERM = "term"
    TERMS = "terms"
    RANGE = "range"
    EXISTS = "exists"
    BOOL = "bool"

# Request schemas
class SearchFilter(BaseModel):
    """Individual search filter"""
    type: FilterType = Field(..., description="Filter type")
    field: str = Field(..., description="Field name")
    value: Union[str, int, float, List[str], Dict[str, Any]] = Field(..., description="Filter value")
    
    @validator('value')
    def validate_value_for_type(cls, v, values):
        filter_type = values.get('type')
        
        if filter_type == FilterType.TERMS and not isinstance(v, list):
            raise ValueError("Terms filter requires list value")
        
        if filter_type == FilterType.RANGE and not isinstance(v, dict):
            raise ValueError("Range filter requires dict value")
        
        return v

class SortField(BaseModel):
    """Sort field specification"""
    field: str = Field(..., description="Field name")
    order: SortOrder = Field(SortOrder.DESC, description="Sort order")
    missing: Optional[str] = Field(None, description="How to handle missing values")

class BoostQuery(BaseModel):
    """Query boost specification"""
    query_type: str = Field(..., description="Query type (match, term, etc.)")
    parameters: Dict[str, Any] = Field(..., description="Query parameters")
    weight: float = Field(1.0, ge=0, description="Boost weight")

class HighlightSettings(BaseModel):
    """Highlight configuration"""
    fields: List[str] = Field(..., description="Fields to highlight")
    fragment_size: int = Field(150, ge=1, le=1000, description="Fragment size")
    number_of_fragments: int = Field(3, ge=1, le=10, description="Number of fragments")
    pre_tags: List[str] = Field(["<mark>"], description="Pre-highlight tags")
    post_tags: List[str] = Field(["</mark>"], description="Post-highlight tags")

class SearchRequest(BaseModel):
    """Basic search request"""
    query: Optional[str] = Field(None, description="Search query text", min_length=1)
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Results per page")
    
    @validator('query')
    def validate_query(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip() if v else v

class AdvancedSearchRequest(BaseModel):
    """Advanced search request with all options"""
    query: Optional[str] = Field(None, description="Main search query")
    search_fields: List[str] = Field(
        ["name^3", "description^2", "category"],
        description="Fields to search with boost values"
    )
    match_type: MatchType = Field(MatchType.BEST_FIELDS, description="Multi-match type")
    operator: Operator = Field(Operator.AND, description="Query operator")
    minimum_should_match: Optional[str] = Field(None, description="Minimum should match")
    
    # Filtering
    filters: List[SearchFilter] = Field(default_factory=list, description="Search filters")
    
    # Sorting
    sort: List[SortField] = Field(
        default_factory=lambda: [SortField(field="_score", order=SortOrder.DESC)],
        description="Sort fields"
    )
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Results per page")
    
    # Response formatting
    source_includes: Optional[List[str]] = Field(None, description="Fields to include")
    source_excludes: Optional[List[str]] = Field(None, description="Fields to exclude")
    
    # Features
    highlight: Optional[HighlightSettings] = Field(None, description="Highlight settings")
    include_aggregations: bool = Field(False, description="Include aggregations")
    aggregation_fields: List[str] = Field(default_factory=list, description="Fields for aggregation")
    
    # Query enhancement
    boost_queries: List[BoostQuery] = Field(default_factory=list, description="Boost queries")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    
    @root_validator
    def validate_search_criteria(cls, values):
        query = values.get('query')
        filters = values.get('filters', [])
        
        if not query and not filters:
            raise ValueError("Either query or filters must be provided")
        
        return values
    
    @validator('search_fields')
    def validate_search_fields(cls, v):
        if not v:
            raise ValueError("At least one search field must be specified")
        return v

class BulkSearchRequest(BaseModel):
    """Bulk search request for multiple queries"""
    searches: List[AdvancedSearchRequest] = Field(
        ..., 
        min_items=1, 
        max_items=10,
        description="List of search requests"
    )
    preference: Optional[str] = Field(None, description="Search preference for routing")

# Response schemas
class SearchResultHighlight(BaseModel):
    """Search result highlights"""
    field: str = Field(..., description="Highlighted field")
    fragments: List[str] = Field(..., description="Highlighted fragments")

class ProductDetail(BaseModel):
    """Detailed product information"""
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    price: float = Field(..., description="Product price")
    currency: str = Field("USD", description="Price currency")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    review_count: Optional[int] = Field(None, ge=0, description="Number of reviews")
    in_stock: bool = Field(..., description="Stock availability")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")
    image_urls: List[str] = Field(default_factory=list, description="Product images")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    created_date: datetime = Field(..., description="Creation date")
    updated_date: datetime = Field(..., description="Last update date")
    score: Optional[float] = Field(None, description="Search relevance score")
    highlights: Optional[Dict[str, List[str]]] = Field(None, description="Search highlights")

class AggregationBucket(BaseModel):
    """Aggregation bucket result"""
    key: Union[str, int, float] = Field(..., description="Bucket key")
    doc_count: int = Field(..., description="Document count")
    key_as_string: Optional[str] = Field(None, description="Key as string")

class AggregationResult(BaseModel):
    """Aggregation results"""
    buckets: Optional[List[AggregationBucket]] = Field(None, description="Term aggregation buckets")
    value: Optional[float] = Field(None, description="Metric aggregation value")
    values: Optional[Dict[str, float]] = Field(None, description="Stats aggregation values")

class SearchResponseMeta(BaseModel):
    """Extended search response metadata"""
    total: int = Field(..., description="Total number of results")
    total_relation: str = Field("eq", description="Total count relation (eq, gte)")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Results per page")
    pages: int = Field(..., description="Total number of pages")
    took_ms: int = Field(..., description="Query execution time in milliseconds")
    max_score: Optional[float] = Field(None, description="Maximum relevance score")
    timed_out: bool = Field(False, description="Whether the search timed out")
    shards: Optional[Dict[str, int]] = Field(None, description="Shard information")

class DetailedSearchResponse(BaseModel):
    """Detailed search response"""
    results: List[ProductDetail] = Field(..., description="Search results")
    meta: SearchResponseMeta = Field(..., description="Search metadata")
    aggregations: Optional[Dict[str, AggregationResult]] = Field(None, description="Aggregation results")
    suggestions: Optional[Dict[str, List[str]]] = Field(None, description="Search suggestions")
    debug: Optional[Dict[str, Any]] = Field(None, description="Debug information")

class BulkSearchResponse(BaseModel):
    """Bulk search response"""
    responses: List[DetailedSearchResponse] = Field(..., description="Individual search responses")
    total_took_ms: int = Field(..., description="Total execution time")
    errors: List[str] = Field(default_factory=list, description="Execution errors")

# Error response schemas
class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")

class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = Field(False, description="Request success status")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[List[ValidationErrorDetail]] = Field(None, description="Validation errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request tracking ID")

# Usage in endpoints
@app.post(
    "/api/v1/products/search",
    response_model=DetailedSearchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def advanced_search_endpoint(
    request: AdvancedSearchRequest = Body(..., description="Search parameters")
) -> DetailedSearchResponse:
    """Advanced search endpoint with comprehensive schemas"""
    # Implementation here
    pass
```

## Pagination and Filtering

### Advanced Pagination Patterns

```python
from typing import Optional, List, Dict, Any
import base64
import json

class PaginationStrategy(str, Enum):
    OFFSET = "offset"
    CURSOR = "cursor"
    SEARCH_AFTER = "search_after"

class CursorPagination:
    """Cursor-based pagination for large result sets"""
    
    @staticmethod
    def encode_cursor(sort_values: List[Any], doc_id: str) -> str:
        """Encode sort values and document ID into cursor"""
        cursor_data = {
            'sort_values': sort_values,
            'doc_id': doc_id
        }
        cursor_json = json.dumps(cursor_data, default=str)
        return base64.b64encode(cursor_json.encode()).decode()
    
    @staticmethod
    def decode_cursor(cursor: str) -> Dict[str, Any]:
        """Decode cursor back to sort values and document ID"""
        try:
            cursor_json = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_json)
        except Exception:
            raise ValueError("Invalid cursor format")

class PaginationRequest(BaseModel):
    """Flexible pagination request"""
    strategy: PaginationStrategy = Field(PaginationStrategy.OFFSET, description="Pagination strategy")
    
    # Offset pagination
    page: Optional[int] = Field(None, ge=1, description="Page number for offset pagination")
    size: int = Field(10, ge=1, le=100, description="Results per page")
    
    # Cursor pagination
    cursor: Optional[str] = Field(None, description="Cursor for cursor-based pagination")
    
    # Search after pagination
    search_after: Optional[List[Any]] = Field(None, description="Search after values")

class PaginationResponse(BaseModel):
    """Pagination response metadata"""
    strategy: PaginationStrategy = Field(..., description="Pagination strategy used")
    
    # Common fields
    size: int = Field(..., description="Requested page size")
    total: Optional[int] = Field(None, description="Total results (if available)")
    
    # Offset pagination
    page: Optional[int] = Field(None, description="Current page number")
    pages: Optional[int] = Field(None, description="Total pages")
    
    # Cursor pagination
    has_next: Optional[bool] = Field(None, description="Has next page")
    has_previous: Optional[bool] = Field(None, description="Has previous page")
    next_cursor: Optional[str] = Field(None, description="Next page cursor")
    previous_cursor: Optional[str] = Field(None, description="Previous page cursor")
    
    # Search after pagination
    next_search_after: Optional[List[Any]] = Field(None, description="Next search after values")

@app.get("/api/v1/products/paginated-search")
async def paginated_search(
    q: str = Query(..., description="Search query"),
    pagination: PaginationRequest = Depends(),
    sort_by: str = Query("_score", description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order")
) -> Dict[str, Any]:
    """Search with flexible pagination strategies"""
    
    search = AsyncSearch(index='products')
    search = search.query('multi_match', query=q, fields=['name', 'description'])
    
    # Add sorting (required for cursor and search_after pagination)
    if sort_by == '_score':
        search = search.sort('-_score', '_id')  # Always include _id for tiebreaking
    else:
        sort_field = sort_by if sort_order == SortOrder.ASC else f'-{sort_by}'
        search = search.sort(sort_field, '_id')
    
    # Apply pagination strategy
    if pagination.strategy == PaginationStrategy.OFFSET:
        # Traditional offset pagination
        start = (pagination.page - 1) * pagination.size if pagination.page else 0
        search = search[start:start + pagination.size]
        
        response = await search.execute()
        
        total = response.hits.total.value
        pages = (total + pagination.size - 1) // pagination.size
        
        pagination_meta = PaginationResponse(
            strategy=PaginationStrategy.OFFSET,
            size=pagination.size,
            total=total,
            page=pagination.page or 1,
            pages=pages
        )
    
    elif pagination.strategy == PaginationStrategy.CURSOR:
        # Cursor-based pagination
        if pagination.cursor:
            cursor_data = CursorPagination.decode_cursor(pagination.cursor)
            search = search.extra(search_after=cursor_data['sort_values'])
        
        search = search[:pagination.size + 1]  # Fetch one extra to check if there's a next page
        response = await search.execute()
        
        has_next = len(response.hits) > pagination.size
        if has_next:
            response.hits = response.hits[:pagination.size]  # Remove the extra hit
        
        # Generate next cursor if there are more results
        next_cursor = None
        if has_next and response.hits:
            last_hit = response.hits[-1]
            sort_values = list(last_hit.meta.sort)
            next_cursor = CursorPagination.encode_cursor(sort_values, last_hit.meta.id)
        
        pagination_meta = PaginationResponse(
            strategy=PaginationStrategy.CURSOR,
            size=pagination.size,
            has_next=has_next,
            has_previous=pagination.cursor is not None,
            next_cursor=next_cursor
        )
    
    elif pagination.strategy == PaginationStrategy.SEARCH_AFTER:
        # Elasticsearch search_after pagination
        if pagination.search_after:
            search = search.extra(search_after=pagination.search_after)
        
        search = search[:pagination.size]
        response = await search.execute()
        
        # Generate next search_after values
        next_search_after = None
        if response.hits:
            last_hit = response.hits[-1]
            next_search_after = list(last_hit.meta.sort)
        
        pagination_meta = PaginationResponse(
            strategy=PaginationStrategy.SEARCH_AFTER,
            size=pagination.size,
            next_search_after=next_search_after
        )
    
    # Format results
    results = []
    for hit in response.hits:
        result = {
            'id': hit.meta.id,
            'name': hit.name,
            'description': getattr(hit, 'description', None),
            'category': hit.category,
            'price': hit.price,
            'score': hit.meta.score,
            'sort_values': list(hit.meta.sort) if hasattr(hit.meta, 'sort') else None
        }
        results.append(result)
    
    return {
        'results': results,
        'pagination': pagination_meta,
        'took_ms': response.took
    }

# Advanced filtering patterns
class FilterOperator(str, Enum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"

class AdvancedFilter(BaseModel):
    """Advanced filter specification"""
    field: str = Field(..., description="Field name")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Optional[Union[str, int, float, List[str], bool]] = Field(None, description="Filter value")
    case_sensitive: bool = Field(True, description="Case sensitive matching")

class FilterGroup(BaseModel):
    """Group of filters with logical operator"""
    operator: str = Field("and", regex="^(and|or)$", description="Logical operator")
    filters: List[Union[AdvancedFilter, 'FilterGroup']] = Field(..., description="Filters in group")

# Enable forward references
FilterGroup.model_rebuild()

class FilterProcessor:
    """Process advanced filters into Elasticsearch queries"""
    
    @staticmethod
    def process_filter(filter_item: AdvancedFilter) -> Q:
        """Convert AdvancedFilter to Elasticsearch query"""
        field = filter_item.field
        operator = filter_item.operator
        value = filter_item.value
        
        if operator == FilterOperator.EQUALS:
            return Q('term', **{field: value})
        
        elif operator == FilterOperator.NOT_EQUALS:
            return ~Q('term', **{field: value})
        
        elif operator == FilterOperator.GREATER_THAN:
            return Q('range', **{field: {'gt': value}})
        
        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return Q('range', **{field: {'gte': value}})
        
        elif operator == FilterOperator.LESS_THAN:
            return Q('range', **{field: {'lt': value}})
        
        elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return Q('range', **{field: {'lte': value}})
        
        elif operator == FilterOperator.IN:
            return Q('terms', **{field: value})
        
        elif operator == FilterOperator.NOT_IN:
            return ~Q('terms', **{field: value})
        
        elif operator == FilterOperator.CONTAINS:
            if filter_item.case_sensitive:
                return Q('wildcard', **{field: f'*{value}*'})
            else:
                return Q('wildcard', **{f'{field}.lowercase': f'*{value.lower()}*'})
        
        elif operator == FilterOperator.STARTS_WITH:
            if filter_item.case_sensitive:
                return Q('prefix', **{field: value})
            else:
                return Q('prefix', **{f'{field}.lowercase': value.lower()})
        
        elif operator == FilterOperator.EXISTS:
            return Q('exists', field=field)
        
        elif operator == FilterOperator.NOT_EXISTS:
            return ~Q('exists', field=field)
        
        else:
            raise ValueError(f"Unsupported filter operator: {operator}")
    
    @staticmethod
    def process_filter_group(group: FilterGroup) -> Q:
        """Convert FilterGroup to Elasticsearch bool query"""
        queries = []
        
        for filter_item in group.filters:
            if isinstance(filter_item, AdvancedFilter):
                queries.append(FilterProcessor.process_filter(filter_item))
            elif isinstance(filter_item, FilterGroup):
                queries.append(FilterProcessor.process_filter_group(filter_item))
        
        if group.operator == "and":
            return Q('bool', must=queries)
        else:  # or
            return Q('bool', should=queries, minimum_should_match=1)

@app.post("/api/v1/products/advanced-filtered-search")
async def advanced_filtered_search(
    q: Optional[str] = Field(None, description="Search query"),
    filter_groups: List[FilterGroup] = Field(..., description="Filter groups"),
    pagination: PaginationRequest = Depends(),
    sort_by: str = Query("_score"),
    sort_order: SortOrder = Query(SortOrder.DESC)
) -> Dict[str, Any]:
    """Search with advanced filtering capabilities"""
    
    search = AsyncSearch(index='products')
    
    # Add text query if provided
    if q:
        search = search.query('multi_match', query=q, fields=['name^3', 'description^2'])
    
    # Process filter groups
    for group in filter_groups:
        filter_query = FilterProcessor.process_filter_group(group)
        search = search.filter(filter_query)
    
    # Add sorting
    if sort_by == '_score':
        search = search.sort('-_score', '_id')
    else:
        sort_field = sort_by if sort_order == SortOrder.ASC else f'-{sort_by}'
        search = search.sort(sort_field, '_id')
    
    # Apply pagination (using previous pagination logic)
    # ... pagination implementation ...
    
    response = await search.execute()
    
    return {
        'results': [hit.to_dict() for hit in response.hits],
        'query_debug': search.to_dict(),
        'took_ms': response.took
    }
```

## Error Handling and Validation

### Comprehensive Error Management

```python
from fastapi import HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from elasticsearch.exceptions import ElasticsearchException, NotFoundError, RequestError
import logging
import traceback
from typing import Dict, Any
import uuid

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base API error class"""
    def __init__(
        self, 
        message: str, 
        error_code: str, 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class SearchValidationError(APIError):
    """Search validation specific error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SEARCH_VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class SearchExecutionError(APIError):
    """Search execution error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SEARCH_EXECUTION_ERROR",
            status_code=500,
            details=details
        )

class SearchTimeoutError(APIError):
    """Search timeout error"""
    def __init__(self, message: str = "Search request timed out", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SEARCH_TIMEOUT_ERROR",
            status_code=408,
            details=details
        )

class ResourceNotFoundError(APIError):
    """Resource not found error"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )

class ErrorResponse(BaseModel):
    """Standardized error response"""
    success: bool = Field(False, description="Request success status")
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    path: Optional[str] = Field(None, description="Request path that caused the error")

# Custom exception handlers
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors"""
    request_id = str(uuid.uuid4())
    
    logger.error(
        f"API Error [{request_id}]: {exc.error_code} - {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
            path=request.url.path
        ).dict()
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    request_id = str(uuid.uuid4())
    
    # Format validation errors
    validation_details = []
    for error in exc.errors():
        validation_details.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.warning(
        f"Validation Error [{request_id}]: {len(validation_details)} validation errors",
        extra={
            "request_id": request_id,
            "validation_errors": validation_details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": validation_details},
            request_id=request_id,
            path=request.url.path
        ).dict()
    )

@app.exception_handler(ElasticsearchException)
async def elasticsearch_error_handler(request: Request, exc: ElasticsearchException) -> JSONResponse:
    """Handle Elasticsearch-specific errors"""
    request_id = str(uuid.uuid4())
    
    # Determine error type and status code
    if isinstance(exc, NotFoundError):
        error_code = "ELASTICSEARCH_NOT_FOUND"
        status_code = 404
        message = "Requested resource not found in Elasticsearch"
    elif isinstance(exc, RequestError):
        error_code = "ELASTICSEARCH_REQUEST_ERROR"
        status_code = 400
        message = "Invalid Elasticsearch request"
    elif "timeout" in str(exc).lower():
        error_code = "ELASTICSEARCH_TIMEOUT"
        status_code = 408
        message = "Elasticsearch request timed out"
    else:
        error_code = "ELASTICSEARCH_ERROR"
        status_code = 500
        message = "Elasticsearch operation failed"
    
    # Extract additional details from exception
    details = {
        "elasticsearch_error_type": type(exc).__name__,
        "elasticsearch_error": str(exc)
    }
    
    # Add more details if available
    if hasattr(exc, 'error'):
        details["elasticsearch_error_details"] = exc.error
    
    logger.error(
        f"Elasticsearch Error [{request_id}]: {error_code} - {message}",
        extra={
            "request_id": request_id,
            "error_code": error_code,
            "status_code": status_code,
            "details": details,
            "path": request.url.path,
            "elasticsearch_exception": str(exc)
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message,
            details=details,
            request_id=request_id,
            path=request.url.path
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = str(uuid.uuid4())
    
    logger.error(
        f"Unexpected Error [{request_id}]: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={"exception_type": type(exc).__name__},
            request_id=request_id,
            path=request.url.path
        ).dict()
    )

# Validation decorators
def validate_search_parameters(func):
    """Decorator to validate search parameters"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract search parameters
        q = kwargs.get('q')
        page = kwargs.get('page', 1)
        size = kwargs.get('size', 10)
        
        # Validate query
        if q is not None and len(q.strip()) < 2:
            raise SearchValidationError(
                "Search query must be at least 2 characters long",
                details={"query": q, "min_length": 2}
            )
        
        # Validate pagination
        if page < 1:
            raise SearchValidationError(
                "Page number must be greater than 0",
                details={"page": page}
            )
        
        if size < 1 or size > 100:
            raise SearchValidationError(
                "Page size must be between 1 and 100",
                details={"size": size, "min_size": 1, "max_size": 100}
            )
        
        return await func(*args, **kwargs)
    return wrapper

# Enhanced search endpoint with comprehensive error handling
@app.get("/api/v1/products/robust-search")
@validate_search_parameters
async def robust_search(
    q: str = Query(..., min_length=2, description="Search query"),
    category: Optional[str] = Query(None, description="Product category"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Results per page"),
    timeout: Optional[str] = Query("10s", description="Search timeout")
) -> SearchResponse:
    """Robust search endpoint with comprehensive error handling"""
    
    try:
        # Validate category if provided
        if category:
            valid_categories = ['electronics', 'clothing', 'books', 'home', 'sports']
            if category not in valid_categories:
                raise SearchValidationError(
                    f"Invalid category: {category}",
                    details={
                        "provided_category": category,
                        "valid_categories": valid_categories
                    }
                )
        
        # Build search
        search = AsyncSearch(index='products')
        search = search.query('multi_match', 
                            query=q, 
                            fields=['name^3', 'description^2'])
        
        if category:
            search = search.filter('term', category=category)
        
        # Add timeout
        if timeout:
            search = search.extra(timeout=timeout)
        
        # Add pagination
        start = (page - 1) * size
        search = search[start:start + size]
        
        # Execute search
        response = await search.execute()
        
        # Check if any results found
        if response.hits.total.value == 0:
            logger.info(f"No results found for query: {q}")
        
        # Format response
        results = []
        for hit in response.hits:
            result = ProductSearchResult(
                id=hit.meta.id,
                name=hit.name,
                description=getattr(hit, 'description', ''),
                category=hit.category,
                price=hit.price,
                rating=getattr(hit, 'rating'),
                in_stock=hit.in_stock,
                score=hit.meta.score
            )
            results.append(result)
        
        # Calculate metadata
        total = response.hits.total.value
        pages = (total + size - 1) // size
        
        meta = SearchResultMeta(
            total=total,
            page=page,
            size=size,
            pages=pages,
            took_ms=response.took,
            max_score=response.hits.max_score
        )
        
        return SearchResponse(results=results, meta=meta)
        
    except SearchValidationError:
        # Re-raise validation errors
        raise
    
    except NotFoundError as e:
        raise ResourceNotFoundError("index", "products")
    
    except RequestError as e:
        raise SearchValidationError(
            f"Invalid search request: {str(e)}",
            details={"elasticsearch_error": str(e)}
        )
    
    except Exception as e:
        if "timeout" in str(e).lower():
            raise SearchTimeoutError(
                f"Search timed out after {timeout}",
                details={"timeout": timeout, "query": q}
            )
        else:
            raise SearchExecutionError(
                f"Search execution failed: {str(e)}",
                details={"query": q, "exception_type": type(e).__name__}
            )
```

## OpenAPI Documentation

### Enhanced Documentation Patterns

```python
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

# Custom OpenAPI schema generation
def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Product Search API",
        version="1.0.0",
        description="""
        ## Product Search API
        
        A comprehensive RESTful API for product search using Elasticsearch and FastAPI.
        
        ### Features
        - **Full-text search** across product catalog
        - **Advanced filtering** with multiple criteria
        - **Flexible pagination** (offset, cursor, search_after)
        - **Real-time suggestions** and autocomplete
        - **Aggregations** for faceted search
        - **Similarity search** using more-like-this queries
        
        ### Authentication
        API uses JWT token-based authentication. Include the token in the Authorization header:
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ### Rate Limiting
        API requests are limited to 1000 requests per hour per API key.
        
        ### Error Handling
        All errors follow a consistent format with error codes, messages, and details.
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Products",
                "description": "Product search and management operations"
            },
            {
                "name": "Search",
                "description": "Advanced search operations and suggestions"
            },
            {
                "name": "Analytics",
                "description": "Search analytics and reporting"
            }
        ]
    )
    
    # Add custom response examples
    openapi_schema["components"]["examples"] = {
        "SearchResponseExample": {
            "summary": "Successful search response",
            "value": {
                "results": [
                    {
                        "id": "prod-123",
                        "name": "Gaming Laptop",
                        "description": "High-performance gaming laptop",
                        "category": "electronics",
                        "price": 1299.99,
                        "rating": 4.5,
                        "in_stock": True,
                        "score": 2.3
                    }
                ],
                "meta": {
                    "total": 156,
                    "page": 1,
                    "size": 10,
                    "pages": 16,
                    "took_ms": 25,
                    "max_score": 2.3
                }
            }
        },
        "ErrorResponseExample": {
            "summary": "Error response",
            "value": {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": [
                        {
                            "field": "query",
                            "message": "Query must be at least 2 characters long",
                            "type": "value_error.any_str.min_length"
                        }
                    ]
                },
                "request_id": "req-123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2024-01-15T10:30:00Z",
                "path": "/api/v1/products/search"
            }
        }
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Enhanced endpoint documentation
@app.get(
    "/api/v1/products/search",
    response_model=SearchResponse,
    summary="Search Products",
    description="""
    Search for products using text queries and filters.
    
    This endpoint supports:
    - **Full-text search** across product name, description, and category
    - **Filtering** by category, price range, rating, and stock status
    - **Sorting** by relevance, price, rating, or name
    - **Pagination** with configurable page size
    - **Highlighting** of search terms in results
    - **Aggregations** for faceted search interface
    
    ### Examples
    
    **Basic search:**
    ```
    GET /api/v1/products/search?q=laptop&page=1&size=10
    ```
    
    **Filtered search:**
    ```
    GET /api/v1/products/search?q=gaming&category=electronics&price_min=500&price_max=2000
    ```
    
    **Sorted search:**
    ```
    GET /api/v1/products/search?q=phone&sort_by=price&sort_order=asc
    ```
    """,
    responses={
        200: {
            "description": "Search completed successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "successful_search": {
                            "$ref": "#/components/examples/SearchResponseExample"
                        }
                    }
                }
            }
        },
        400: {
            "description": "Invalid search parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "validation_error": {
                            "$ref": "#/components/examples/ErrorResponseExample"
                        }
                    }
                }
            }
        },
        408: {"description": "Search request timed out"},
        500: {"description": "Internal server error"}
    },
    tags=["Products"],
    dependencies=[Depends(rate_limit)]
)
async def documented_search_products(
    q: str = Query(
        ..., 
        description="Search query text",
        min_length=2,
        max_length=100,
        example="gaming laptop"
    ),
    category: Optional[str] = Query(
        None, 
        description="Filter by product category",
        example="electronics"
    ),
    price_min: Optional[float] = Query(
        None, 
        ge=0,
        description="Minimum price filter",
        example=500.0
    ),
    price_max: Optional[float] = Query(
        None, 
        ge=0,
        description="Maximum price filter",
        example=2000.0
    ),
    sort_by: str = Query(
        "relevance",
        description="Field to sort by",
        example="price"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-based)",
        example=1
    ),
    size: int = Query(
        10,
        ge=1,
        le=100,
        description="Number of results per page",
        example=20
    )
) -> SearchResponse:
    """Documented search endpoint with comprehensive examples"""
    # Implementation here
    pass

# Custom documentation pages
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with enhanced styling"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={
            "deepLinking": True,
            "displayRequestDuration": True,
            "docExpansion": "none",
            "operationsSorter": "method",
            "filter": True,
            "tagsSorter": "alpha"
        }
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc documentation"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
    )
```

## Performance Considerations

### Caching and Optimization

```python
import asyncio
import hashlib
from functools import wraps
from typing import Optional, Any
import redis.asyncio as redis

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
    
    def cache_key(self, prefix: str, **params) -> str:
        """Generate cache key from parameters"""
        key_data = json.dumps(params, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value"""
        try:
            cached = await self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    async def set_cached(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value"""
        try:
            ttl = ttl or self.default_ttl
            await self.redis.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
        return False

# Initialize performance optimizer
redis_client = redis.from_url("redis://localhost:6379")
performance_optimizer = PerformanceOptimizer(redis_client)

def cached_endpoint(ttl: int = 300, cache_prefix: str = "api"):
    """Decorator for caching endpoint responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = performance_optimizer.cache_key(
                f"{cache_prefix}:{func.__name__}",
                **kwargs
            )
            
            # Try cache first
            cached_result = await performance_optimizer.get_cached(cache_key)
            if cached_result:
                logger.info(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await performance_optimizer.set_cached(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

@app.get("/api/v1/products/cached-search")
@cached_endpoint(ttl=600, cache_prefix="search")
async def cached_search(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50)
) -> SearchResponse:
    """Cached search endpoint for better performance"""
    # Implementation with caching
    pass

# Request batching
@app.post("/api/v1/products/batch-search")
async def batch_search(
    requests: List[SearchRequest] = Body(..., max_items=10)
) -> List[SearchResponse]:
    """Batch multiple search requests for better performance"""
    
    # Execute searches in parallel
    tasks = []
    for search_request in requests:
        task = execute_single_search(search_request)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results and exceptions
    responses = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Return error response for failed search
            responses.append({
                "error": str(result),
                "request_index": i
            })
        else:
            responses.append(result)
    
    return responses

async def execute_single_search(request: SearchRequest) -> SearchResponse:
    """Execute a single search request"""
    # Implementation here
    pass
```

## Next Steps

1. **[Pydantic Integration](03_pydantic-integration.md)** - Master request/response validation and transformation
2. **[Dependency Injection](04_dependency-injection.md)** - Implement service architecture with FastAPI dependencies
3. **[Advanced Search](../04-advanced-search/01_complex-queries.md)** - Build sophisticated search features
4. **[Testing](../07-testing-deployment/01_testing-strategies.md)** - Test your API endpoints comprehensively

## Additional Resources

- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **OpenAPI Specification**: [swagger.io/specification](https://swagger.io/specification/)
- **REST API Design Guidelines**: [restfulapi.net](https://restfulapi.net/)
- **HTTP Status Codes**: [httpstatuses.com](https://httpstatuses.com/)