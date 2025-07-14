# Basic Patterns

Essential FastAPI + Elasticsearch-DSL patterns and examples for building search applications with async patterns and best practices.

## Table of Contents
- [Simple FastAPI + Elasticsearch Setup](#simple-fastapi--elasticsearch-setup)
- [Basic CRUD Operations](#basic-crud-operations)
- [Query Parameter Handling](#query-parameter-handling)
- [Response Formatting Examples](#response-formatting-examples)
- [Error Handling Patterns](#error-handling-patterns)
- [Authentication Integration](#authentication-integration)
- [Production-Ready Examples](#production-ready-examples)
- [Next Steps](#next-steps)

## Simple FastAPI + Elasticsearch Setup

### Minimal Application Structure
```python
# main.py - Complete minimal FastAPI + Elasticsearch application
from fastapi import FastAPI, HTTPException, Depends, Query
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Float, Date, AsyncSearch
from elasticsearch_dsl.connections import connections
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import asyncio

# Configure Elasticsearch connection
connections.configure(
    default={'hosts': ['localhost:9200'], 'timeout': 20}
)

# Document Model
class Product(AsyncDocument):
    """Product document for Elasticsearch."""
    
    name = Text(analyzer='standard')
    description = Text(analyzer='english')
    price = Float()
    category = Keyword()
    brand = Keyword()
    in_stock = Keyword()  # 'yes' or 'no'
    created_at = Date()
    
    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

# Pydantic Models
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    brand: str = Field(..., min_length=1, max_length=50)
    in_stock: bool = True

class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str
    brand: str
    in_stock: bool
    created_at: datetime
    score: Optional[float] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock_only: bool = True
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)

class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    products: List[ProductResponse]

# FastAPI App
app = FastAPI(title="Product Search API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize Elasticsearch index on startup."""
    try:
        await Product.init()
        print("✅ Elasticsearch index initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Elasticsearch: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    try:
        client = connections.get_connection()
        await client.close()
        print("✅ Elasticsearch connection closed")
    except Exception as e:
        print(f"❌ Error closing Elasticsearch connection: {e}")

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = connections.get_connection()
        await client.ping()
        return {"status": "healthy", "elasticsearch": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Elasticsearch unavailable: {e}")

# Basic CRUD Endpoints
@app.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(product: ProductCreate):
    """Create a new product."""
    try:
        # Create Elasticsearch document
        doc = Product(
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            brand=product.brand,
            in_stock='yes' if product.in_stock else 'no',
            created_at=datetime.utcnow()
        )
        
        # Save to Elasticsearch
        await doc.save()
        
        # Return response
        return ProductResponse(
            id=doc.meta.id,
            name=doc.name,
            description=doc.description,
            price=doc.price,
            category=doc.category,
            brand=doc.brand,
            in_stock=doc.in_stock == 'yes',
            created_at=doc.created_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {e}")

@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """Get a product by ID."""
    try:
        product = await Product.get(id=product_id)
        return ProductResponse(
            id=product.meta.id,
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            brand=product.brand,
            in_stock=product.in_stock == 'yes',
            created_at=product.created_at
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Product not found")

@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product_update: ProductCreate):
    """Update a product."""
    try:
        # Get existing product
        product = await Product.get(id=product_id)
        
        # Update fields
        product.name = product_update.name
        product.description = product_update.description
        product.price = product_update.price
        product.category = product_update.category
        product.brand = product_update.brand
        product.in_stock = 'yes' if product_update.in_stock else 'no'
        
        # Save changes
        await product.save()
        
        return ProductResponse(
            id=product.meta.id,
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            brand=product.brand,
            in_stock=product.in_stock == 'yes',
            created_at=product.created_at
        )
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Product not found")
        raise HTTPException(status_code=500, detail=f"Failed to update product: {e}")

@app.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Delete a product."""
    try:
        product = await Product.get(id=product_id)
        await product.delete()
        return {"message": "Product deleted successfully"}
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Product not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {e}")

@app.post("/search", response_model=SearchResponse)
async def search_products(search_request: SearchRequest):
    """Search products with filters."""
    try:
        # Build search query
        search = AsyncSearch(index='products')
        
        # Text search
        search = search.query('multi_match', 
                            query=search_request.query,
                            fields=['name^2', 'description', 'brand'],
                            type='best_fields')
        
        # Apply filters
        if search_request.category:
            search = search.filter('term', category=search_request.category)
        
        if search_request.in_stock_only:
            search = search.filter('term', in_stock='yes')
        
        # Price range filter
        if search_request.min_price is not None or search_request.max_price is not None:
            price_filter = {}
            if search_request.min_price is not None:
                price_filter['gte'] = search_request.min_price
            if search_request.max_price is not None:
                price_filter['lte'] = search_request.max_price
            search = search.filter('range', price=price_filter)
        
        # Pagination
        offset = (search_request.page - 1) * search_request.size
        search = search[offset:offset + search_request.size]
        
        # Execute search
        response = await search.execute()
        
        # Format results
        products = []
        for hit in response.hits:
            products.append(ProductResponse(
                id=hit.meta.id,
                name=hit.name,
                description=hit.description,
                price=hit.price,
                category=hit.category,
                brand=hit.brand,
                in_stock=hit.in_stock == 'yes',
                created_at=hit.created_at,
                score=hit.meta.score
            ))
        
        return SearchResponse(
            total=response.hits.total.value,
            page=search_request.page,
            size=search_request.size,
            products=products
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

# Quick start data seeding
@app.post("/seed-data")
async def seed_sample_data():
    """Seed the database with sample products for testing."""
    sample_products = [
        ProductCreate(
            name="MacBook Pro 16-inch",
            description="Powerful laptop with M2 Pro chip, perfect for development and creative work",
            price=2499.99,
            category="electronics",
            brand="Apple",
            in_stock=True
        ),
        ProductCreate(
            name="Wireless Mouse",
            description="Ergonomic wireless mouse with precision tracking and long battery life",
            price=29.99,
            category="electronics",
            brand="Logitech",
            in_stock=True
        ),
        ProductCreate(
            name="Programming Book",
            description="Complete guide to Python programming with practical examples and exercises",
            price=45.00,
            category="books",
            brand="TechBooks",
            in_stock=False
        ),
        ProductCreate(
            name="Coffee Mug",
            description="Large ceramic mug perfect for your morning coffee, holds 16oz",
            price=12.99,
            category="home",
            brand="HomeGoods",
            in_stock=True
        ),
        ProductCreate(
            name="Mechanical Keyboard",
            description="RGB mechanical keyboard with blue switches, perfect for gaming and typing",
            price=149.99,
            category="electronics",
            brand="Corsair",
            in_stock=True
        )
    ]
    
    created_products = []
    for product_data in sample_products:
        try:
            product_response = await create_product(product_data)
            created_products.append(product_response.id)
        except Exception as e:
            print(f"Failed to create product: {e}")
    
    return {
        "message": f"Created {len(created_products)} sample products",
        "product_ids": created_products
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

## Basic CRUD Operations

### Advanced CRUD with Validation
```python
# crud_service.py - Service layer for CRUD operations
from typing import Optional, List, Dict, Any
from elasticsearch_dsl import AsyncSearch
from elasticsearch.exceptions import NotFoundError, ConflictError
from datetime import datetime

class ProductService:
    """Service class for product CRUD operations."""
    
    @staticmethod
    async def create_product(product_data: ProductCreate) -> ProductResponse:
        """Create a new product with validation."""
        
        # Check for duplicate product names
        existing = await ProductService.find_by_name(product_data.name)
        if existing:
            raise ValueError(f"Product with name '{product_data.name}' already exists")
        
        # Create document
        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            category=product_data.category.lower(),
            brand=product_data.brand,
            in_stock='yes' if product_data.in_stock else 'no',
            created_at=datetime.utcnow()
        )
        
        try:
            await product.save()
            return ProductService._to_response(product)
        except Exception as e:
            raise RuntimeError(f"Failed to save product: {e}")
    
    @staticmethod
    async def get_product(product_id: str) -> Optional[ProductResponse]:
        """Get product by ID."""
        try:
            product = await Product.get(id=product_id)
            return ProductService._to_response(product)
        except NotFoundError:
            return None
    
    @staticmethod
    async def update_product(product_id: str, product_data: ProductCreate) -> ProductResponse:
        """Update existing product."""
        try:
            product = await Product.get(id=product_id)
            
            # Update fields
            product.name = product_data.name
            product.description = product_data.description
            product.price = product_data.price
            product.category = product_data.category.lower()
            product.brand = product_data.brand
            product.in_stock = 'yes' if product_data.in_stock else 'no'
            
            await product.save()
            return ProductService._to_response(product)
            
        except NotFoundError:
            raise ValueError("Product not found")
    
    @staticmethod
    async def delete_product(product_id: str) -> bool:
        """Delete product by ID."""
        try:
            product = await Product.get(id=product_id)
            await product.delete()
            return True
        except NotFoundError:
            return False
    
    @staticmethod
    async def find_by_name(name: str) -> Optional[ProductResponse]:
        """Find product by exact name."""
        search = AsyncSearch(index='products')
        search = search.filter('term', name__keyword=name)
        search = search[:1]
        
        response = await search.execute()
        if response.hits:
            return ProductService._to_response(response.hits[0])
        return None
    
    @staticmethod
    async def list_products(
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        in_stock_only: bool = False
    ) -> SearchResponse:
        """List products with pagination and filters."""
        
        search = AsyncSearch(index='products')
        
        # Apply filters
        if category:
            search = search.filter('term', category=category.lower())
        
        if in_stock_only:
            search = search.filter('term', in_stock='yes')
        
        # Sort by creation date (newest first)
        search = search.sort('-created_at')
        
        # Pagination
        offset = (page - 1) * size
        search = search[offset:offset + size]
        
        response = await search.execute()
        
        products = [
            ProductService._to_response(hit)
            for hit in response.hits
        ]
        
        return SearchResponse(
            total=response.hits.total.value,
            page=page,
            size=size,
            products=products
        )
    
    @staticmethod
    def _to_response(product) -> ProductResponse:
        """Convert Product document to ProductResponse."""
        return ProductResponse(
            id=product.meta.id,
            name=product.name,
            description=product.description,
            price=product.price,
            category=product.category,
            brand=product.brand,
            in_stock=product.in_stock == 'yes',
            created_at=product.created_at,
            score=getattr(product.meta, 'score', None)
        )

# Updated endpoints using service layer
@app.post("/products", response_model=ProductResponse, status_code=201)
async def create_product_endpoint(product: ProductCreate):
    """Create a new product using service layer."""
    try:
        return await ProductService.create_product(product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {e}")

@app.get("/products", response_model=SearchResponse)
async def list_products_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    in_stock_only: bool = Query(False, description="Show only in-stock items")
):
    """List products with pagination and filters."""
    try:
        return await ProductService.list_products(page, size, category, in_stock_only)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list products: {e}")
```

## Query Parameter Handling

### Advanced Query Parameter Validation
```python
# query_params.py - Advanced query parameter handling
from fastapi import Query, HTTPException
from typing import Optional, List
from enum import Enum
import re

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SortField(str, Enum):
    NAME = "name"
    PRICE = "price"
    CREATED_AT = "created_at"
    RELEVANCE = "relevance"

def validate_search_query(q: str = Query(..., min_length=1, max_length=100)) -> str:
    """Validate and sanitize search query."""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', q.strip())
    
    if not sanitized:
        raise HTTPException(status_code=400, detail="Query cannot be empty after sanitization")
    
    return sanitized

def validate_price_range(
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price")
) -> tuple[Optional[float], Optional[float]]:
    """Validate price range parameters."""
    
    if min_price is not None and max_price is not None:
        if min_price >= max_price:
            raise HTTPException(
                status_code=400, 
                detail="min_price must be less than max_price"
            )
    
    return min_price, max_price

def validate_pagination(
    page: int = Query(1, ge=1, le=1000, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page")
) -> tuple[int, int]:
    """Validate pagination parameters."""
    return page, size

# Advanced search endpoint with comprehensive parameter validation
@app.get("/products/search", response_model=SearchResponse)
async def advanced_search(
    # Query validation
    q: str = Depends(validate_search_query),
    
    # Category filter
    category: Optional[str] = Query(
        None, 
        regex="^[a-zA-Z0-9_-]+$", 
        max_length=50,
        description="Product category"
    ),
    
    # Brand filter
    brand: Optional[str] = Query(
        None, 
        max_length=50,
        description="Product brand"
    ),
    
    # Price range
    price_range: tuple[Optional[float], Optional[float]] = Depends(validate_price_range),
    
    # Stock filter
    in_stock_only: bool = Query(False, description="Show only in-stock items"),
    
    # Sorting
    sort_by: SortField = Query(SortField.RELEVANCE, description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    
    # Pagination
    pagination: tuple[int, int] = Depends(validate_pagination),
    
    # Additional filters
    tags: Optional[List[str]] = Query(None, max_items=10, description="Product tags"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date")
):
    """Advanced product search with comprehensive parameter validation."""
    
    min_price, max_price = price_range
    page, size = pagination
    
    try:
        # Build Elasticsearch query
        search = AsyncSearch(index='products')
        
        # Text search
        if q != "*":  # Allow wildcard search
            search = search.query(
                'multi_match',
                query=q,
                fields=['name^3', 'description^1', 'brand^2'],
                type='best_fields',
                fuzziness='AUTO'
            )
        
        # Apply filters
        filters = []
        
        if category:
            filters.append({'term': {'category': category.lower()}})
        
        if brand:
            filters.append({'term': {'brand': brand}})
        
        if in_stock_only:
            filters.append({'term': {'in_stock': 'yes'}})
        
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter['gte'] = min_price
            if max_price is not None:
                price_filter['lte'] = max_price
            filters.append({'range': {'price': price_filter}})
        
        if created_after:
            filters.append({
                'range': {
                    'created_at': {'gte': created_after.isoformat()}
                }
            })
        
        if tags:
            filters.append({
                'terms': {'tags': tags}
            })
        
        # Apply all filters
        if filters:
            search = search.filter('bool', must=filters)
        
        # Sorting
        if sort_by == SortField.RELEVANCE and q != "*":
            # Use relevance scoring for text queries
            pass  # Default Elasticsearch scoring
        else:
            sort_field = sort_by.value
            if sort_by == SortField.NAME:
                sort_field = 'name.keyword'  # Use keyword field for sorting
            
            sort_direction = sort_order.value
            search = search.sort({sort_field: {'order': sort_direction}})
        
        # Pagination
        offset = (page - 1) * size
        search = search[offset:offset + size]
        
        # Add highlighting
        search = search.highlight('name', 'description', fragment_size=150)
        
        # Execute search
        response = await search.execute()
        
        # Format results
        products = []
        for hit in response.hits:
            product_data = ProductService._to_response(hit)
            
            # Add highlighting if available
            if hasattr(hit.meta, 'highlight'):
                # Store highlight info (you might want to add this to the response model)
                pass
            
            products.append(product_data)
        
        return SearchResponse(
            total=response.hits.total.value,
            page=page,
            size=size,
            products=products
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
```

## Response Formatting Examples

### Dynamic Response Formatting
```python
# response_formatting.py - Dynamic response formatting
from typing import Optional, Set, Dict, Any
from fastapi import Query, Depends

class ResponseFormatter:
    """Format responses based on client requirements."""
    
    @staticmethod
    def format_product(
        product: Product,
        include_fields: Optional[Set[str]] = None,
        exclude_fields: Optional[Set[str]] = None,
        include_score: bool = False
    ) -> Dict[str, Any]:
        """Format product response with field selection."""
        
        # Base product data
        data = {
            'id': product.meta.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'category': product.category,
            'brand': product.brand,
            'in_stock': product.in_stock == 'yes',
            'created_at': product.created_at.isoformat()
        }
        
        # Add score if requested and available
        if include_score and hasattr(product.meta, 'score'):
            data['score'] = product.meta.score
        
        # Apply field inclusion/exclusion
        if include_fields:
            data = {k: v for k, v in data.items() if k in include_fields}
        
        if exclude_fields:
            data = {k: v for k, v in data.items() if k not in exclude_fields}
        
        return data

def parse_field_selection(
    fields: Optional[str] = Query(None, description="Comma-separated fields to include"),
    exclude: Optional[str] = Query(None, description="Comma-separated fields to exclude")
) -> tuple[Optional[Set[str]], Optional[Set[str]]]:
    """Parse field selection parameters."""
    
    include_fields = None
    exclude_fields = None
    
    if fields:
        include_fields = set(f.strip() for f in fields.split(',') if f.strip())
    
    if exclude:
        exclude_fields = set(f.strip() for f in exclude.split(',') if f.strip())
    
    return include_fields, exclude_fields

# Flexible response endpoint
@app.get("/products/{product_id}/flexible")
async def get_product_flexible(
    product_id: str,
    field_selection: tuple[Optional[Set[str]], Optional[Set[str]]] = Depends(parse_field_selection),
    include_score: bool = Query(False, description="Include relevance score")
):
    """Get product with flexible response formatting."""
    
    include_fields, exclude_fields = field_selection
    
    try:
        product = await Product.get(id=product_id)
        
        formatted_product = ResponseFormatter.format_product(
            product,
            include_fields=include_fields,
            exclude_fields=exclude_fields,
            include_score=include_score
        )
        
        return formatted_product
        
    except Exception:
        raise HTTPException(status_code=404, detail="Product not found")

# Bulk formatting for search results
@app.post("/search/flexible", response_model=Dict[str, Any])
async def flexible_search(
    search_request: SearchRequest,
    field_selection: tuple[Optional[Set[str]], Optional[Set[str]]] = Depends(parse_field_selection),
    format_type: str = Query("standard", regex="^(standard|minimal|detailed)$")
):
    """Search with flexible response formatting."""
    
    include_fields, exclude_fields = field_selection
    
    # Execute search (reuse existing search logic)
    search = AsyncSearch(index='products')
    search = search.query('multi_match', 
                        query=search_request.query,
                        fields=['name^2', 'description', 'brand'])
    
    # Apply filters (simplified for example)
    if search_request.category:
        search = search.filter('term', category=search_request.category)
    
    response = await search.execute()
    
    # Format results based on format_type
    if format_type == "minimal":
        include_fields = {'id', 'name', 'price'} if not include_fields else include_fields
    elif format_type == "detailed":
        # Include all fields plus additional metadata
        pass
    
    formatted_products = []
    for hit in response.hits:
        formatted_product = ResponseFormatter.format_product(
            hit,
            include_fields=include_fields,
            exclude_fields=exclude_fields,
            include_score=True
        )
        formatted_products.append(formatted_product)
    
    return {
        'total': response.hits.total.value,
        'products': formatted_products,
        'format_type': format_type,
        'query_time_ms': response.took
    }
```

## Error Handling Patterns

### Comprehensive Error Handling
```python
# error_handling.py - Comprehensive error handling patterns
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from elasticsearch.exceptions import (
    ConnectionError, 
    NotFoundError, 
    RequestError,
    ConflictError
)
import logging

logger = logging.getLogger(__name__)

class ProductAPIException(Exception):
    """Base exception for Product API."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ProductNotFoundError(ProductAPIException):
    """Product not found exception."""
    
    def __init__(self, product_id: str):
        super().__init__(f"Product with ID '{product_id}' not found", 404)

class DuplicateProductError(ProductAPIException):
    """Duplicate product exception."""
    
    def __init__(self, name: str):
        super().__init__(f"Product with name '{name}' already exists", 409)

class SearchServiceError(ProductAPIException):
    """Search service exception."""
    
    def __init__(self, message: str):
        super().__init__(f"Search service error: {message}", 503)

# Global exception handlers
@app.exception_handler(ProductAPIException)
async def product_api_exception_handler(request: Request, exc: ProductAPIException):
    """Handle custom Product API exceptions."""
    logger.error(f"Product API error: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "product_api_error",
            "message": exc.message,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    
    error_details = []
    for error in exc.errors():
        error_details.append({
            'field': '.'.join(str(x) for x in error['loc'][1:]),
            'message': error['msg'],
            'type': error['type']
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": error_details
        }
    )

@app.exception_handler(ConnectionError)
async def elasticsearch_connection_error_handler(request: Request, exc: ConnectionError):
    """Handle Elasticsearch connection errors."""
    logger.error(f"Elasticsearch connection error: {exc}")
    
    return JSONResponse(
        status_code=503,
        content={
            "error": "service_unavailable",
            "message": "Search service is temporarily unavailable",
            "retry_after": 30
        }
    )

@app.exception_handler(RequestError)
async def elasticsearch_request_error_handler(request: Request, exc: RequestError):
    """Handle Elasticsearch request errors."""
    logger.error(f"Elasticsearch request error: {exc}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_search_request",
            "message": "Invalid search request parameters"
        }
    )

# Safe operation wrapper
async def safe_execute(operation, *args, **kwargs):
    """Safely execute an operation with comprehensive error handling."""
    try:
        return await operation(*args, **kwargs)
    
    except NotFoundError as e:
        raise ProductNotFoundError(str(e))
    
    except ConflictError as e:
        raise DuplicateProductError(str(e))
    
    except ConnectionError as e:
        raise SearchServiceError(f"Connection failed: {e}")
    
    except RequestError as e:
        raise SearchServiceError(f"Invalid request: {e}")
    
    except Exception as e:
        logger.exception(f"Unexpected error in {operation.__name__}: {e}")
        raise ProductAPIException(f"Internal server error: {str(e)}")

# Example usage in endpoints
@app.get("/products/{product_id}/safe", response_model=ProductResponse)
async def get_product_safe(product_id: str):
    """Get product with comprehensive error handling."""
    
    async def get_operation():
        product = await Product.get(id=product_id)
        return ProductService._to_response(product)
    
    return await safe_execute(get_operation)
```

## Authentication Integration

### JWT Authentication Example
```python
# auth.py - JWT authentication integration
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class User(BaseModel):
    username: str
    email: str
    is_active: bool = True
    is_admin: bool = False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # In a real app, you'd fetch the user from a database
    # For this example, we'll create a mock user
    user = User(username=username, email=f"{username}@example.com")
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

# Protected endpoints
@app.post("/products/protected", response_model=ProductResponse)
async def create_product_protected(
    product: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    """Create product (requires authentication)."""
    logger.info(f"User {current_user.username} creating product: {product.name}")
    return await ProductService.create_product(product)

@app.delete("/products/{product_id}/admin")
async def delete_product_admin(
    product_id: str,
    admin_user: User = Depends(get_admin_user)
):
    """Delete product (requires admin privileges)."""
    logger.info(f"Admin {admin_user.username} deleting product: {product_id}")
    success = await ProductService.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# Login endpoint
@app.post("/auth/login")
async def login(username: str, password: str):
    """Login and get access token."""
    # In a real app, you'd validate credentials against a database
    if username == "admin" and password == "admin123":
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )
```

## Production-Ready Examples

### Complete Production Setup
```python
# production_main.py - Production-ready FastAPI application
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Product Search API")
    try:
        await Product.init()
        logger.info("Elasticsearch connection established")
    except Exception as e:
        logger.error(f"Failed to initialize Elasticsearch: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Product Search API")
    try:
        client = connections.get_connection()
        await client.close()
        logger.info("Elasticsearch connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Product Search API",
    description="Production-ready FastAPI + Elasticsearch search API",
    version="1.0.0",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "https://app.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )

# Include all the endpoints defined above
# (create_product, get_product, update_product, delete_product, search_products, etc.)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "production_main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload in production
        access_log=True,
        log_level="info"
    )
```

### Docker Configuration
```dockerfile
# Dockerfile for production deployment
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Next Steps

1. **[Search Applications](02_search-applications.md)** - Complete search API implementation
2. **[Integration Examples](03_integration-examples.md)** - Authentication, monitoring, and background tasks
3. **[Performance Optimization](../06-production-patterns/03_performance-optimization.md)** - Scaling and efficiency

## Additional Resources

- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Elasticsearch-DSL Python**: [elasticsearch-dsl.readthedocs.io](https://elasticsearch-dsl.readthedocs.io)
- **Pydantic Documentation**: [pydantic-docs.helpmanual.io](https://pydantic-docs.helpmanual.io)