# Pydantic Integration

Comprehensive guide to integrating Pydantic with FastAPI and Elasticsearch-DSL for type-safe request/response validation, data transformation, and seamless API development.

## Table of Contents
- [Request and Response Models](#request-and-response-models)
- [Data Transformation Patterns](#data-transformation-patterns)
- [Custom Validators and Serializers](#custom-validators-and-serializers)
- [Type Safety Throughout the Stack](#type-safety-throughout-the-stack)
- [Response Formatting and Field Selection](#response-formatting-and-field-selection)
- [Advanced Pydantic Features](#advanced-pydantic-features)
- [Integration with Elasticsearch-DSL](#integration-with-elasticsearch-dsl)
- [Performance Optimization](#performance-optimization)
- [Next Steps](#next-steps)

## Request and Response Models

### Core Model Definitions

```python
from pydantic import BaseModel, Field, validator, root_validator, ConfigDict
from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import re

# Configuration for all models
class BaseConfig:
    """Base configuration for all Pydantic models"""
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra='forbid',
        str_strip_whitespace=True,
        validate_default=True
    )

# Enums for type safety
class ProductCategory(str, Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME_GARDEN = "home_garden"
    SPORTS = "sports"
    TOYS = "toys"
    AUTOMOTIVE = "automotive"
    HEALTH_BEAUTY = "health_beauty"

class SortField(str, Enum):
    RELEVANCE = "_score"
    PRICE = "price"
    NAME = "name"
    RATING = "rating"
    CREATED_DATE = "created_date"
    POPULARITY = "popularity"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SearchMode(str, Enum):
    SIMPLE = "simple"
    ADVANCED = "advanced"
    SEMANTIC = "semantic"
    FUZZY = "fuzzy"

# Base models
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class PaginationMixin(BaseModel):
    """Mixin for pagination parameters"""
    page: int = Field(1, ge=1, le=1000, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Results per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and size"""
        return (self.page - 1) * self.size

# Request models
class ProductSearchRequest(BaseModel, BaseConfig):
    """Basic product search request"""
    query: str = Field(..., min_length=2, max_length=200, description="Search query")
    category: Optional[ProductCategory] = Field(None, description="Product category filter")
    price_min: Optional[Decimal] = Field(None, ge=0, description="Minimum price")
    price_max: Optional[Decimal] = Field(None, ge=0, description="Maximum price")
    rating_min: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating")
    in_stock_only: bool = Field(True, description="Show only in-stock products")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Results per page")
    
    # Sorting
    sort_by: SortField = Field(SortField.RELEVANCE, description="Sort field")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")
    
    # Features
    include_highlights: bool = Field(True, description="Include search highlights")
    include_aggregations: bool = Field(False, description="Include aggregations")
    search_mode: SearchMode = Field(SearchMode.SIMPLE, description="Search mode")
    
    @validator('price_max')
    def price_max_greater_than_min(cls, v, values):
        """Validate price_max is greater than price_min"""
        price_min = values.get('price_min')
        if price_min is not None and v is not None and v <= price_min:
            raise ValueError('price_max must be greater than price_min')
        return v
    
    @validator('query')
    def query_not_empty(cls, v):
        """Validate query is not empty after stripping"""
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class AdvancedSearchRequest(BaseModel, BaseConfig):
    """Advanced search request with complex parameters"""
    
    # Text search configuration
    query: Optional[str] = Field(None, min_length=2, max_length=500, description="Main search query")
    query_fields: List[str] = Field(
        default_factory=lambda: ["name^3", "description^2", "category", "brand"],
        description="Fields to search with boost values"
    )
    operator: Literal["and", "or"] = Field("and", description="Query operator")
    minimum_should_match: Optional[str] = Field(None, description="Minimum should match parameter")
    
    # Filtering
    categories: List[ProductCategory] = Field(default_factory=list, description="Category filters")
    brands: List[str] = Field(default_factory=list, description="Brand filters")
    tags: List[str] = Field(default_factory=list, description="Tag filters")
    price_range: Optional[Dict[str, Decimal]] = Field(None, description="Price range filter")
    date_range: Optional[Dict[str, date]] = Field(None, description="Date range filter")
    
    # Search behavior
    fuzzy_enabled: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_distance: int = Field(2, ge=0, le=2, description="Maximum edit distance for fuzzy matching")
    boost_exact_matches: bool = Field(True, description="Boost exact phrase matches")
    
    # Results configuration
    include_fields: Optional[List[str]] = Field(None, description="Fields to include in response")
    exclude_fields: Optional[List[str]] = Field(None, description="Fields to exclude from response")
    
    # Pagination and sorting
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Results per page")
    sort_criteria: List[Dict[str, str]] = Field(
        default_factory=lambda: [{"field": "_score", "order": "desc"}],
        description="Complex sorting criteria"
    )
    
    # Advanced features
    highlight_config: Optional[Dict[str, Any]] = Field(None, description="Highlight configuration")
    aggregations: List[str] = Field(default_factory=list, description="Aggregations to include")
    function_score_config: Optional[Dict[str, Any]] = Field(None, description="Function score configuration")
    
    @root_validator
    def validate_search_criteria(cls, values):
        """Validate that at least one search criterion is provided"""
        query = values.get('query')
        categories = values.get('categories', [])
        brands = values.get('brands', [])
        tags = values.get('tags', [])
        price_range = values.get('price_range')
        
        if not any([query, categories, brands, tags, price_range]):
            raise ValueError('At least one search criterion must be provided')
        
        return values
    
    @validator('price_range')
    def validate_price_range(cls, v):
        """Validate price range parameters"""
        if v is None:
            return v
        
        min_price = v.get('min')
        max_price = v.get('max')
        
        if min_price is not None and min_price < 0:
            raise ValueError('Minimum price cannot be negative')
        
        if max_price is not None and max_price < 0:
            raise ValueError('Maximum price cannot be negative')
        
        if min_price is not None and max_price is not None and min_price >= max_price:
            raise ValueError('Minimum price must be less than maximum price')
        
        return v
    
    @validator('query_fields')
    def validate_query_fields(cls, v):
        """Validate query fields format"""
        valid_fields = {'name', 'description', 'category', 'brand', 'tags'}
        
        for field in v:
            # Remove boost notation (^N) to get base field name
            base_field = re.sub(r'\^[\d.]+$', '', field)
            if base_field not in valid_fields:
                raise ValueError(f'Invalid query field: {base_field}')
        
        return v

class ProductCreateRequest(BaseModel, BaseConfig):
    """Request model for creating a new product"""
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    category: ProductCategory = Field(..., description="Product category")
    brand: Optional[str] = Field(None, min_length=1, max_length=100, description="Product brand")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Product price")
    currency: str = Field("USD", regex=r'^[A-Z]{3}$', description="Price currency code")
    sku: str = Field(..., min_length=1, max_length=50, description="Stock keeping unit")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Product specifications")
    images: List[str] = Field(default_factory=list, description="Product image URLs")
    stock_quantity: int = Field(0, ge=0, description="Available stock quantity")
    
    @validator('sku')
    def sku_format(cls, v):
        """Validate SKU format"""
        if not re.match(r'^[A-Z0-9\-_]+$', v.upper()):
            raise ValueError('SKU must contain only alphanumeric characters, hyphens, and underscores')
        return v.upper()
    
    @validator('images')
    def validate_image_urls(cls, v):
        """Validate image URLs"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        for url in v:
            if not url_pattern.match(url):
                raise ValueError(f'Invalid image URL: {url}')
        
        return v

class ProductUpdateRequest(BaseModel, BaseConfig):
    """Request model for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    category: Optional[ProductCategory] = Field(None, description="Product category")
    brand: Optional[str] = Field(None, min_length=1, max_length=100, description="Product brand")
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Product price")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Product specifications")
    images: Optional[List[str]] = Field(None, description="Product image URLs")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available stock quantity")
    active: Optional[bool] = Field(None, description="Product active status")

# Response models
class ProductResponse(BaseModel, BaseConfig):
    """Basic product response model"""
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category: ProductCategory = Field(..., description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    price: Decimal = Field(..., description="Product price")
    currency: str = Field(..., description="Price currency")
    sku: str = Field(..., description="Stock keeping unit")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    review_count: int = Field(0, ge=0, description="Number of reviews")
    in_stock: bool = Field(..., description="Stock availability")
    stock_quantity: int = Field(..., ge=0, description="Available stock")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    images: List[str] = Field(default_factory=list, description="Product images")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class SearchResultProduct(ProductResponse):
    """Product response with search-specific fields"""
    score: Optional[float] = Field(None, description="Search relevance score")
    highlights: Optional[Dict[str, List[str]]] = Field(None, description="Search result highlights")
    explanation: Optional[Dict[str, Any]] = Field(None, description="Score explanation")
    
    class Config(BaseConfig):
        # Allow additional fields for flexible search results
        extra = 'allow'

class SearchMetadata(BaseModel, BaseConfig):
    """Search result metadata"""
    total: int = Field(..., description="Total number of results")
    total_relation: Literal["eq", "gte"] = Field("eq", description="Total count relation")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total pages")
    took_ms: int = Field(..., description="Query execution time")
    max_score: Optional[float] = Field(None, description="Maximum relevance score")
    timed_out: bool = Field(False, description="Query timeout status")
    
    @validator('pages')
    def calculate_pages(cls, v, values):
        """Calculate total pages from total and size"""
        total = values.get('total', 0)
        size = values.get('size', 1)
        return (total + size - 1) // size if size > 0 else 0

class AggregationBucket(BaseModel, BaseConfig):
    """Aggregation bucket result"""
    key: Union[str, int, float] = Field(..., description="Bucket key")
    doc_count: int = Field(..., ge=0, description="Document count")
    key_as_string: Optional[str] = Field(None, description="Key as string")

class AggregationResult(BaseModel, BaseConfig):
    """Aggregation result container"""
    buckets: Optional[List[AggregationBucket]] = Field(None, description="Bucket aggregation results")
    value: Optional[float] = Field(None, description="Metric aggregation value")
    values: Optional[Dict[str, float]] = Field(None, description="Stats aggregation values")

class SearchResponse(BaseModel, BaseConfig):
    """Complete search response"""
    results: List[SearchResultProduct] = Field(..., description="Search results")
    metadata: SearchMetadata = Field(..., description="Search metadata")
    aggregations: Optional[Dict[str, AggregationResult]] = Field(None, description="Aggregation results")
    suggestions: Optional[List[str]] = Field(None, description="Search suggestions")
    debug: Optional[Dict[str, Any]] = Field(None, description="Debug information")

class APIResponse(BaseModel, BaseConfig):
    """Generic API response wrapper"""
    success: bool = Field(True, description="Operation success status")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    errors: Optional[List[str]] = Field(None, description="Error messages")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
```

## Data Transformation Patterns

### Elasticsearch-DSL to Pydantic Conversion

```python
from elasticsearch_dsl import Document, Text, Keyword, Float, Integer, Boolean, Date
from typing import Type, TypeVar, Generic

T = TypeVar('T', bound=BaseModel)

class ModelTransformer(Generic[T]):
    """Generic transformer for converting between Elasticsearch documents and Pydantic models"""
    
    def __init__(self, pydantic_model: Type[T]):
        self.pydantic_model = pydantic_model
    
    def from_es_hit(self, hit, include_meta: bool = True) -> T:
        """Convert Elasticsearch hit to Pydantic model"""
        # Extract document data
        doc_data = hit.to_dict()
        
        # Add metadata if requested
        if include_meta and hasattr(hit, 'meta'):
            doc_data['id'] = hit.meta.id
            if hasattr(hit.meta, 'score'):
                doc_data['score'] = hit.meta.score
            if hasattr(hit.meta, 'highlight'):
                doc_data['highlights'] = hit.meta.highlight.to_dict()
        
        # Handle timestamp conversion
        if 'created_at' in doc_data and isinstance(doc_data['created_at'], str):
            doc_data['created_at'] = datetime.fromisoformat(doc_data['created_at'].replace('Z', '+00:00'))
        if 'updated_at' in doc_data and isinstance(doc_data['updated_at'], str):
            doc_data['updated_at'] = datetime.fromisoformat(doc_data['updated_at'].replace('Z', '+00:00'))
        
        # Convert price to Decimal if present
        if 'price' in doc_data and not isinstance(doc_data['price'], Decimal):
            doc_data['price'] = Decimal(str(doc_data['price']))
        
        return self.pydantic_model(**doc_data)
    
    def from_es_document(self, document: Document, include_meta: bool = True) -> T:
        """Convert Elasticsearch Document to Pydantic model"""
        # Extract document data
        doc_data = document.to_dict()
        
        # Add metadata if requested
        if include_meta and hasattr(document, 'meta'):
            doc_data['id'] = document.meta.id
        
        return self.pydantic_model(**doc_data)
    
    def to_es_dict(self, model: T, exclude_meta: bool = True) -> Dict[str, Any]:
        """Convert Pydantic model to Elasticsearch document dictionary"""
        data = model.dict(exclude_unset=True)
        
        # Remove metadata fields if requested
        if exclude_meta:
            meta_fields = {'id', 'score', 'highlights', 'explanation'}
            data = {k: v for k, v in data.items() if k not in meta_fields}
        
        # Convert Decimal to float for Elasticsearch
        if 'price' in data and isinstance(data['price'], Decimal):
            data['price'] = float(data['price'])
        
        # Convert datetime to ISO string
        for field in ['created_at', 'updated_at']:
            if field in data and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()
        
        return data

# Elasticsearch Document definitions
class ProductDocument(Document):
    """Elasticsearch document for products"""
    name = Text(analyzer='standard', fields={'keyword': Keyword()})
    description = Text(analyzer='english')
    category = Keyword()
    brand = Keyword()
    price = Float()
    currency = Keyword()
    sku = Keyword()
    rating = Float()
    review_count = Integer()
    in_stock = Boolean()
    stock_quantity = Integer()
    tags = Keyword(multi=True)
    images = Keyword(multi=True)
    created_at = Date()
    updated_at = Date()
    
    class Index:
        name = 'products'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
            'analysis': {
                'analyzer': {
                    'custom_text_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'stop', 'snowball']
                    }
                }
            }
        }

# Transformer instances
product_transformer = ModelTransformer(ProductResponse)
search_result_transformer = ModelTransformer(SearchResultProduct)

# Usage in endpoints
@app.get("/api/v1/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str = Path(..., description="Product ID")) -> ProductResponse:
    """Get product by ID with automatic transformation"""
    try:
        # Get document from Elasticsearch
        product_doc = await ProductDocument.get(product_id)
        
        # Transform to Pydantic model
        return product_transformer.from_es_document(product_doc)
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

@app.post("/api/v1/products", response_model=ProductResponse)
async def create_product(product_request: ProductCreateRequest) -> ProductResponse:
    """Create new product with transformation"""
    # Convert Pydantic model to Elasticsearch document
    doc_data = product_transformer.to_es_dict(product_request)
    
    # Add timestamps
    now = datetime.utcnow()
    doc_data['created_at'] = now
    doc_data['updated_at'] = now
    
    # Create and save document
    product_doc = ProductDocument(**doc_data)
    await product_doc.save()
    
    # Return transformed response
    return product_transformer.from_es_document(product_doc)

# Advanced transformation with custom logic
class AdvancedProductTransformer:
    """Advanced transformer with custom business logic"""
    
    @staticmethod
    def enhance_search_result(hit, user_context: Optional[Dict[str, Any]] = None) -> SearchResultProduct:
        """Transform search hit with user-specific enhancements"""
        # Basic transformation
        product = search_result_transformer.from_es_hit(hit)
        
        # Add user-specific data if context provided
        if user_context:
            # Add personalized recommendations
            if user_context.get('user_id'):
                product.personalized = True
                product.user_rating_prediction = calculate_rating_prediction(
                    user_context['user_id'], 
                    product.id
                )
            
            # Add pricing context
            if user_context.get('location'):
                product.local_availability = check_local_availability(
                    product.id, 
                    user_context['location']
                )
            
            # Add promotional information
            if user_context.get('membership_tier'):
                product.member_discount = calculate_member_discount(
                    product.price, 
                    user_context['membership_tier']
                )
        
        return product
    
    @staticmethod
    def aggregate_to_facets(aggregations: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Transform Elasticsearch aggregations to facet format"""
        facets = {}
        
        for agg_name, agg_data in aggregations.items():
            if 'buckets' in agg_data:
                facets[agg_name] = [
                    {
                        'value': bucket['key'],
                        'count': bucket['doc_count'],
                        'selected': False  # Client will set this
                    }
                    for bucket in agg_data['buckets']
                ]
            elif 'value' in agg_data:
                facets[agg_name] = {
                    'type': 'metric',
                    'value': agg_data['value']
                }
        
        return facets

def calculate_rating_prediction(user_id: str, product_id: str) -> Optional[float]:
    """Calculate predicted rating for user-product pair"""
    # Placeholder for ML model prediction
    return None

def check_local_availability(product_id: str, location: str) -> Dict[str, Any]:
    """Check local availability for product"""
    # Placeholder for inventory check
    return {'available': True, 'delivery_days': 2}

def calculate_member_discount(price: Decimal, membership_tier: str) -> Optional[Decimal]:
    """Calculate member discount based on tier"""
    discounts = {
        'silver': Decimal('0.05'),  # 5%
        'gold': Decimal('0.10'),    # 10%
        'platinum': Decimal('0.15') # 15%
    }
    
    discount_rate = discounts.get(membership_tier)
    if discount_rate:
        return price * discount_rate
    
    return None
```

## Custom Validators and Serializers

### Advanced Validation Patterns

```python
from pydantic import validator, root_validator, Field
from typing import Any, Dict, List, Optional
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

class CustomValidators:
    """Collection of custom validators"""
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """Validate and sanitize search query"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript protocol
            r'on\w+\s*=',                 # Event handlers
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                raise ValueError("Query contains invalid content")
        
        return query
    
    @staticmethod
    def validate_price_range(price_min: Optional[Decimal], price_max: Optional[Decimal]) -> tuple:
        """Validate price range consistency"""
        if price_min is not None and price_min < 0:
            raise ValueError("Minimum price cannot be negative")
        
        if price_max is not None and price_max < 0:
            raise ValueError("Maximum price cannot be negative")
        
        if price_min is not None and price_max is not None:
            if price_min >= price_max:
                raise ValueError("Minimum price must be less than maximum price")
        
        return price_min, price_max
    
    @staticmethod
    def validate_date_range(date_from: Optional[date], date_to: Optional[date]) -> tuple:
        """Validate date range consistency"""
        if date_from and date_to:
            if date_from > date_to:
                raise ValueError("Start date must be before end date")
        
        # Don't allow future dates for historical data
        today = date.today()
        if date_from and date_from > today:
            raise ValueError("Start date cannot be in the future")
        
        if date_to and date_to > today:
            raise ValueError("End date cannot be in the future")
        
        return date_from, date_to

class SearchRequestValidator(BaseModel, BaseConfig):
    """Enhanced search request with comprehensive validation"""
    
    # Search parameters
    query: Optional[str] = Field(None, min_length=1, max_length=500)
    categories: List[ProductCategory] = Field(default_factory=list)
    price_min: Optional[Decimal] = Field(None, ge=0)
    price_max: Optional[Decimal] = Field(None, ge=0)
    rating_min: Optional[float] = Field(None, ge=0, le=5)
    date_from: Optional[date] = Field(None)
    date_to: Optional[date] = Field(None)
    
    # Pagination
    page: int = Field(1, ge=1, le=1000)
    size: int = Field(10, ge=1, le=100)
    
    # Advanced options
    include_out_of_stock: bool = Field(False)
    search_fields: List[str] = Field(default_factory=lambda: ["name", "description"])
    boost_config: Optional[Dict[str, float]] = Field(None)
    
    @validator('query')
    def validate_query(cls, v):
        """Validate search query"""
        if v is not None:
            return CustomValidators.validate_search_query(v)
        return v
    
    @root_validator
    def validate_price_range(cls, values):
        """Validate price range consistency"""
        price_min = values.get('price_min')
        price_max = values.get('price_max')
        
        if price_min is not None or price_max is not None:
            CustomValidators.validate_price_range(price_min, price_max)
        
        return values
    
    @root_validator
    def validate_date_range(cls, values):
        """Validate date range consistency"""
        date_from = values.get('date_from')
        date_to = values.get('date_to')
        
        if date_from is not None or date_to is not None:
            CustomValidators.validate_date_range(date_from, date_to)
        
        return values
    
    @root_validator
    def validate_search_criteria(cls, values):
        """Ensure at least one search criterion is provided"""
        query = values.get('query')
        categories = values.get('categories', [])
        price_min = values.get('price_min')
        price_max = values.get('price_max')
        rating_min = values.get('rating_min')
        
        if not any([query, categories, price_min, price_max, rating_min]):
            raise ValueError("At least one search criterion must be provided")
        
        return values
    
    @validator('search_fields')
    def validate_search_fields(cls, v):
        """Validate search fields are allowed"""
        allowed_fields = {
            'name', 'description', 'category', 'brand', 'tags',
            'name.keyword', 'description.english', 'category.keyword'
        }
        
        for field in v:
            # Remove boost notation
            base_field = re.sub(r'\^[\d.]+$', '', field)
            if base_field not in allowed_fields:
                raise ValueError(f"Invalid search field: {base_field}")
        
        return v
    
    @validator('boost_config')
    def validate_boost_config(cls, v):
        """Validate boost configuration"""
        if v is None:
            return v
        
        allowed_boost_fields = {'exact_match', 'recent_products', 'popular_products', 'in_stock'}
        
        for field, boost_value in v.items():
            if field not in allowed_boost_fields:
                raise ValueError(f"Invalid boost field: {field}")
            
            if not isinstance(boost_value, (int, float)) or boost_value < 0:
                raise ValueError(f"Boost value must be a non-negative number: {field}")
        
        return v

# Custom serializers for response formatting
class CustomSerializer:
    """Custom serialization utilities"""
    
    @staticmethod
    def serialize_decimal(value: Decimal) -> str:
        """Serialize Decimal to string with proper formatting"""
        return f"{value:.2f}"
    
    @staticmethod
    def serialize_datetime(value: datetime) -> str:
        """Serialize datetime to ISO format"""
        return value.isoformat() + 'Z'
    
    @staticmethod
    def serialize_highlights(highlights: Dict[str, List[str]]) -> Dict[str, str]:
        """Serialize highlights to user-friendly format"""
        serialized = {}
        for field, fragments in highlights.items():
            # Join fragments with ellipsis
            serialized[field] = ' ... '.join(fragments)
        return serialized

class FormattedProductResponse(ProductResponse):
    """Product response with custom formatting"""
    
    class Config(BaseConfig):
        # Custom JSON encoders
        json_encoders = {
            Decimal: CustomSerializer.serialize_decimal,
            datetime: CustomSerializer.serialize_datetime
        }
    
    @validator('price', pre=False, always=True)
    def format_price(cls, v):
        """Format price for display"""
        if isinstance(v, Decimal):
            return v.quantize(Decimal('0.01'))
        return v
    
    @validator('rating', pre=False, always=True)
    def format_rating(cls, v):
        """Format rating to one decimal place"""
        if v is not None:
            return round(v, 1)
        return v

class FlexibleSearchResponse(SearchResponse):
    """Search response with flexible field formatting"""
    
    @validator('results', pre=False, always=True)
    def format_results(cls, v):
        """Apply custom formatting to search results"""
        formatted_results = []
        
        for result in v:
            # Convert to dict for manipulation
            result_dict = result.dict()
            
            # Format highlights
            if result_dict.get('highlights'):
                result_dict['highlights'] = CustomSerializer.serialize_highlights(
                    result_dict['highlights']
                )
            
            # Add computed fields
            result_dict['display_price'] = f"${result_dict['price']:.2f}"
            result_dict['in_stock_text'] = "In Stock" if result_dict['in_stock'] else "Out of Stock"
            
            # Reconstruct model
            formatted_results.append(SearchResultProduct(**result_dict))
        
        return formatted_results

# Dynamic model creation for flexible responses
def create_dynamic_response_model(fields: List[str]) -> Type[BaseModel]:
    """Create dynamic response model with specified fields"""
    
    # Base field definitions
    field_definitions = {
        'id': (str, Field(..., description="Product ID")),
        'name': (str, Field(..., description="Product name")),
        'description': (Optional[str], Field(None, description="Product description")),
        'category': (ProductCategory, Field(..., description="Product category")),
        'brand': (Optional[str], Field(None, description="Product brand")),
        'price': (Decimal, Field(..., description="Product price")),
        'rating': (Optional[float], Field(None, description="Average rating")),
        'in_stock': (bool, Field(..., description="Stock availability")),
        'score': (Optional[float], Field(None, description="Search score")),
        'highlights': (Optional[Dict[str, List[str]]], Field(None, description="Highlights"))
    }
    
    # Select only requested fields
    selected_fields = {
        field: field_definitions[field] 
        for field in fields 
        if field in field_definitions
    }
    
    # Create dynamic model
    DynamicResponseModel = type(
        'DynamicProductResponse',
        (BaseModel,),
        {
            '__annotations__': {field: definition[0] for field, definition in selected_fields.items()},
            **{field: definition[1] for field, definition in selected_fields.items()},
            'Config': BaseConfig
        }
    )
    
    return DynamicResponseModel

# Usage in endpoint with field selection
@app.get("/api/v1/products/flexible-search")
async def flexible_search(
    request: SearchRequestValidator = Depends(),
    fields: Optional[List[str]] = Query(None, description="Fields to include in response")
) -> Any:
    """Search endpoint with flexible response fields"""
    
    # Default fields if none specified
    if not fields:
        fields = ['id', 'name', 'category', 'price', 'rating', 'in_stock', 'score']
    
    # Validate requested fields
    valid_fields = {'id', 'name', 'description', 'category', 'brand', 'price', 'rating', 'in_stock', 'score', 'highlights'}
    invalid_fields = set(fields) - valid_fields
    if invalid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid fields requested: {', '.join(invalid_fields)}"
        )
    
    # Execute search (implementation depends on search logic)
    search_results = await execute_search(request)
    
    # Create dynamic response model
    ResponseModel = create_dynamic_response_model(fields)
    
    # Transform results
    formatted_results = []
    for result in search_results:
        # Filter result to include only requested fields
        result_data = {field: getattr(result, field, None) for field in fields}
        formatted_results.append(ResponseModel(**result_data))
    
    return {
        'results': formatted_results,
        'metadata': {
            'total': len(search_results),
            'fields_included': fields
        }
    }
```

## Type Safety Throughout the Stack

### End-to-End Type Safety Implementation

```python
from typing import TypeVar, Generic, Protocol, runtime_checkable
from abc import ABC, abstractmethod

# Type variables for generic implementations
TRequest = TypeVar('TRequest', bound=BaseModel)
TResponse = TypeVar('TResponse', bound=BaseModel)
TDocument = TypeVar('TDocument', bound=Document)

@runtime_checkable
class SearchService(Protocol[TRequest, TResponse]):
    """Protocol for type-safe search services"""
    
    async def search(self, request: TRequest) -> TResponse:
        """Execute search and return typed response"""
        ...
    
    async def suggest(self, query: str) -> List[str]:
        """Get search suggestions"""
        ...

class TypedSearchService(Generic[TRequest, TResponse]):
    """Generic search service with type safety"""
    
    def __init__(
        self,
        request_model: Type[TRequest],
        response_model: Type[TResponse],
        document_model: Type[TDocument]
    ):
        self.request_model = request_model
        self.response_model = response_model
        self.document_model = document_model
        self.transformer = ModelTransformer(response_model)
    
    async def search(self, request: TRequest) -> TResponse:
        """Type-safe search implementation"""
        # Validate request type
        if not isinstance(request, self.request_model):
            raise TypeError(f"Expected {self.request_model.__name__}, got {type(request).__name__}")
        
        # Build Elasticsearch query
        search = self._build_search_query(request)
        
        # Execute search
        response = await search.execute()
        
        # Transform results
        results = []
        for hit in response.hits:
            result = self.transformer.from_es_hit(hit)
            results.append(result)
        
        # Build typed response
        metadata = SearchMetadata(
            total=response.hits.total.value,
            page=getattr(request, 'page', 1),
            size=getattr(request, 'size', 10),
            pages=(response.hits.total.value + getattr(request, 'size', 10) - 1) // getattr(request, 'size', 10),
            took_ms=response.took
        )
        
        return SearchResponse(results=results, metadata=metadata)
    
    def _build_search_query(self, request: TRequest) -> AsyncSearch:
        """Build Elasticsearch query from typed request"""
        search = AsyncSearch(index=self.document_model._doc_type.index)
        
        # Add query if present
        if hasattr(request, 'query') and request.query:
            search = search.query('multi_match', 
                                query=request.query,
                                fields=['name^3', 'description^2'])
        
        # Add filters
        if hasattr(request, 'category') and request.category:
            search = search.filter('term', category=request.category)
        
        # Add pagination
        if hasattr(request, 'page') and hasattr(request, 'size'):
            start = (request.page - 1) * request.size
            search = search[start:start + request.size]
        
        return search

# Specific service implementations
ProductSearchService = TypedSearchService[ProductSearchRequest, SearchResponse]
AdvancedSearchService = TypedSearchService[AdvancedSearchRequest, SearchResponse]

# Type-safe repository pattern
class TypedRepository(Generic[TDocument], ABC):
    """Abstract repository with type safety"""
    
    def __init__(self, document_model: Type[TDocument]):
        self.document_model = document_model
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> TDocument:
        """Create new document"""
        pass
    
    @abstractmethod
    async def get_by_id(self, doc_id: str) -> Optional[TDocument]:
        """Get document by ID"""
        pass
    
    @abstractmethod
    async def update(self, doc_id: str, data: Dict[str, Any]) -> TDocument:
        """Update document"""
        pass
    
    @abstractmethod
    async def delete(self, doc_id: str) -> bool:
        """Delete document"""
        pass
    
    @abstractmethod
    async def search(self, query: Dict[str, Any]) -> List[TDocument]:
        """Search documents"""
        pass

class ProductRepository(TypedRepository[ProductDocument]):
    """Type-safe product repository"""
    
    async def create(self, data: Dict[str, Any]) -> ProductDocument:
        """Create new product document"""
        product = ProductDocument(**data)
        await product.save()
        return product
    
    async def get_by_id(self, product_id: str) -> Optional[ProductDocument]:
        """Get product by ID"""
        try:
            return await ProductDocument.get(product_id)
        except NotFoundError:
            return None
    
    async def update(self, product_id: str, data: Dict[str, Any]) -> ProductDocument:
        """Update product document"""
        product = await self.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        for field, value in data.items():
            if hasattr(product, field):
                setattr(product, field, value)
        
        await product.save()
        return product
    
    async def delete(self, product_id: str) -> bool:
        """Delete product document"""
        product = await self.get_by_id(product_id)
        if product:
            await product.delete()
            return True
        return False
    
    async def search(self, query: Dict[str, Any]) -> List[ProductDocument]:
        """Search product documents"""
        search = ProductDocument.search()
        
        # Apply query filters
        if 'query' in query:
            search = search.query('multi_match', 
                                query=query['query'],
                                fields=['name', 'description'])
        
        response = await search.execute()
        return list(response.hits)

# Type-safe controller pattern
class TypedController(Generic[TRequest, TResponse]):
    """Generic controller with type safety"""
    
    def __init__(
        self,
        service: SearchService[TRequest, TResponse],
        request_model: Type[TRequest],
        response_model: Type[TResponse]
    ):
        self.service = service
        self.request_model = request_model
        self.response_model = response_model
    
    async def handle_search(self, **kwargs) -> TResponse:
        """Handle search request with type validation"""
        try:
            # Create typed request
            request = self.request_model(**kwargs)
            
            # Execute service
            response = await self.service.search(request)
            
            # Validate response type
            if not isinstance(response, self.response_model):
                raise TypeError(f"Service returned {type(response).__name__}, expected {self.response_model.__name__}")
            
            return response
            
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# Dependency injection with type safety
def get_product_search_service() -> ProductSearchService:
    """Get product search service dependency"""
    return TypedSearchService(
        ProductSearchRequest,
        SearchResponse,
        ProductDocument
    )

def get_product_repository() -> ProductRepository:
    """Get product repository dependency"""
    return ProductRepository(ProductDocument)

# Type-safe endpoints
@app.get("/api/v1/products/typed-search", response_model=SearchResponse)
async def typed_search_endpoint(
    q: str = Query(..., description="Search query"),
    category: Optional[ProductCategory] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    service: ProductSearchService = Depends(get_product_search_service)
) -> SearchResponse:
    """Type-safe search endpoint"""
    
    # Create typed request
    request = ProductSearchRequest(
        query=q,
        category=category,
        page=page,
        size=size
    )
    
    # Execute typed service
    return await service.search(request)

@app.post("/api/v1/products/typed-create", response_model=ProductResponse)
async def typed_create_endpoint(
    product_data: ProductCreateRequest,
    repository: ProductRepository = Depends(get_product_repository)
) -> ProductResponse:
    """Type-safe product creation endpoint"""
    
    # Convert to dict for repository
    data = product_data.dict()
    data['created_at'] = datetime.utcnow()
    data['updated_at'] = datetime.utcnow()
    
    # Create document
    product_doc = await repository.create(data)
    
    # Transform to response model
    transformer = ModelTransformer(ProductResponse)
    return transformer.from_es_document(product_doc)
```

## Response Formatting and Field Selection

### Dynamic Response Construction

```python
from typing import Set, Dict, Any, Optional, Type
from pydantic import create_model
import inspect

class ResponseFormatter:
    """Dynamic response formatting and field selection"""
    
    def __init__(self, base_model: Type[BaseModel]):
        self.base_model = base_model
        self.field_definitions = self._extract_field_definitions()
    
    def _extract_field_definitions(self) -> Dict[str, Any]:
        """Extract field definitions from base model"""
        fields = {}
        
        for field_name, field_info in self.base_model.__fields__.items():
            fields[field_name] = {
                'type': field_info.type_,
                'default': field_info.default,
                'field_info': field_info.field_info,
                'required': field_info.required
            }
        
        return fields
    
    def create_filtered_model(
        self, 
        included_fields: Optional[Set[str]] = None,
        excluded_fields: Optional[Set[str]] = None,
        model_name: str = "FilteredResponse"
    ) -> Type[BaseModel]:
        """Create new model with filtered fields"""
        
        # Determine which fields to include
        if included_fields:
            selected_fields = included_fields & set(self.field_definitions.keys())
        else:
            selected_fields = set(self.field_definitions.keys())
        
        if excluded_fields:
            selected_fields = selected_fields - excluded_fields
        
        # Build field definitions for new model
        field_definitions = {}
        annotations = {}
        
        for field_name in selected_fields:
            field_def = self.field_definitions[field_name]
            field_definitions[field_name] = field_def['field_info']
            annotations[field_name] = field_def['type']
        
        # Create dynamic model
        dynamic_model = create_model(
            model_name,
            __config__=BaseConfig,
            **field_definitions
        )
        
        # Set annotations
        dynamic_model.__annotations__ = annotations
        
        return dynamic_model
    
    def format_response(
        self,
        data: Any,
        included_fields: Optional[Set[str]] = None,
        excluded_fields: Optional[Set[str]] = None,
        transformations: Optional[Dict[str, callable]] = None
    ) -> Dict[str, Any]:
        """Format response data with field selection and transformations"""
        
        # Convert to dict if it's a model instance
        if isinstance(data, BaseModel):
            response_data = data.dict()
        else:
            response_data = data
        
        # Apply field filtering
        if included_fields:
            response_data = {k: v for k, v in response_data.items() if k in included_fields}
        
        if excluded_fields:
            response_data = {k: v for k, v in response_data.items() if k not in excluded_fields}
        
        # Apply transformations
        if transformations:
            for field, transform_func in transformations.items():
                if field in response_data:
                    response_data[field] = transform_func(response_data[field])
        
        return response_data

class AdvancedResponseFormatter(ResponseFormatter):
    """Advanced response formatter with conditional logic"""
    
    def format_search_results(
        self,
        results: List[Any],
        user_context: Optional[Dict[str, Any]] = None,
        response_format: str = "standard"
    ) -> List[Dict[str, Any]]:
        """Format search results based on context and format"""
        
        formatted_results = []
        
        for result in results:
            # Base formatting
            formatted_result = self.format_response(result)
            
            # Apply format-specific modifications
            if response_format == "minimal":
                formatted_result = self._apply_minimal_format(formatted_result)
            elif response_format == "detailed":
                formatted_result = self._apply_detailed_format(formatted_result, user_context)
            elif response_format == "mobile":
                formatted_result = self._apply_mobile_format(formatted_result)
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _apply_minimal_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply minimal format - only essential fields"""
        essential_fields = {'id', 'name', 'price', 'in_stock'}
        return {k: v for k, v in data.items() if k in essential_fields}
    
    def _apply_detailed_format(self, data: Dict[str, Any], user_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply detailed format with user-specific enhancements"""
        # Add computed fields
        if 'price' in data:
            data['formatted_price'] = f"${data['price']:.2f}"
        
        if 'rating' in data:
            data['rating_stars'] = '★' * int(data.get('rating', 0))
        
        # Add user-specific data
        if user_context and user_context.get('user_id'):
            data['is_favorited'] = self._check_user_favorite(
                user_context['user_id'], 
                data.get('id')
            )
            data['user_recommendations'] = self._get_user_recommendations(
                user_context['user_id'], 
                data.get('category')
            )
        
        return data
    
    def _apply_mobile_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply mobile-optimized format"""
        # Optimize for mobile display
        if 'description' in data:
            # Truncate description for mobile
            description = data['description']
            if len(description) > 100:
                data['description'] = description[:97] + '...'
        
        # Add mobile-specific fields
        data['mobile_image_url'] = self._get_mobile_optimized_image(data.get('images', []))
        
        return data
    
    def _check_user_favorite(self, user_id: str, product_id: str) -> bool:
        """Check if product is user's favorite"""
        # Placeholder for favorite check logic
        return False
    
    def _get_user_recommendations(self, user_id: str, category: str) -> List[str]:
        """Get user-specific recommendations"""
        # Placeholder for recommendation logic
        return []
    
    def _get_mobile_optimized_image(self, images: List[str]) -> Optional[str]:
        """Get mobile-optimized image URL"""
        if not images:
            return None
        
        # Return first image with mobile optimization parameter
        return f"{images[0]}?w=300&h=300&fit=crop"

# Usage in endpoints with field selection
@app.get("/api/v1/products/formatted-search")
async def formatted_search(
    q: str = Query(..., description="Search query"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
    exclude_fields: Optional[str] = Query(None, description="Comma-separated list of fields to exclude"),
    format_type: str = Query("standard", regex="^(minimal|standard|detailed|mobile)$"),
    user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Dict[str, Any]:
    """Search endpoint with dynamic response formatting"""
    
    # Parse field parameters
    included_fields = set(fields.split(',')) if fields else None
    excluded_fields = set(exclude_fields.split(',')) if exclude_fields else None
    
    # Execute search
    search_results = await execute_search_query(q)
    
    # Format results
    formatter = AdvancedResponseFormatter(SearchResultProduct)
    
    user_context = {'user_id': user_id} if user_id else None
    
    formatted_results = formatter.format_search_results(
        search_results,
        user_context=user_context,
        response_format=format_type
    )
    
    # Apply field filtering to individual results
    if included_fields or excluded_fields:
        filtered_results = []
        for result in formatted_results:
            filtered_result = formatter.format_response(
                result,
                included_fields=included_fields,
                excluded_fields=excluded_fields
            )
            filtered_results.append(filtered_result)
        formatted_results = filtered_results
    
    return {
        'results': formatted_results,
        'metadata': {
            'total': len(formatted_results),
            'format': format_type,
            'fields_included': list(included_fields) if included_fields else 'all',
            'fields_excluded': list(excluded_fields) if excluded_fields else 'none'
        }
    }

# Response transformation middleware
class ResponseTransformationMiddleware:
    """Middleware for automatic response transformation"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.formatters = {
            SearchResultProduct: AdvancedResponseFormatter(SearchResultProduct),
            ProductResponse: ResponseFormatter(ProductResponse)
        }
    
    async def __call__(self, scope, receive, send):
        """Process responses and apply transformations"""
        
        async def wrapped_send(message):
            if message["type"] == "http.response.body":
                # Transform response body if needed
                body = message.get("body", b"")
                if body:
                    try:
                        # Parse response
                        response_data = json.loads(body.decode())
                        
                        # Apply transformations based on request headers
                        # This is a simplified example
                        transformed_data = self._transform_response(response_data, scope)
                        
                        # Update message body
                        message["body"] = json.dumps(transformed_data).encode()
                    except Exception:
                        # If transformation fails, send original response
                        pass
            
            await send(message)
        
        await self.app(scope, receive, wrapped_send)
    
    def _transform_response(self, data: Dict[str, Any], scope: Dict[str, Any]) -> Dict[str, Any]:
        """Transform response data based on request context"""
        # Extract request context
        headers = dict(scope.get("headers", []))
        query_params = scope.get("query_string", b"").decode()
        
        # Apply transformations based on context
        # This is a placeholder for actual transformation logic
        return data

# Add middleware to app
# app.add_middleware(ResponseTransformationMiddleware)

async def execute_search_query(query: str) -> List[SearchResultProduct]:
    """Execute search query and return results"""
    # Placeholder implementation
    return []
```

## Advanced Pydantic Features

### Custom Field Types and Advanced Patterns

```python
from pydantic import BaseModel, Field, validator, root_validator, PrivateAttr
from pydantic.fields import ModelField
from typing import Any, Callable, Dict, List, Optional, Union
import json
from decimal import Decimal
from datetime import datetime

# Custom field types
class PriceField(Decimal):
    """Custom price field with validation and formatting"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            try:
                v = Decimal(v)
            except Exception:
                raise ValueError('Invalid price format')
        
        if isinstance(v, (int, float)):
            v = Decimal(str(v))
        
        if not isinstance(v, Decimal):
            raise ValueError('Price must be a valid decimal number')
        
        if v < 0:
            raise ValueError('Price cannot be negative')
        
        if v > Decimal('999999.99'):
            raise ValueError('Price cannot exceed $999,999.99')
        
        # Round to 2 decimal places
        return v.quantize(Decimal('0.01'))
    
    def __str__(self):
        return f"${self:.2f}"

class SearchQueryField(str):
    """Custom search query field with validation"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise ValueError('Search query must be a string')
        
        # Clean and validate
        v = v.strip()
        
        if not v:
            raise ValueError('Search query cannot be empty')
        
        if len(v) < 2:
            raise ValueError('Search query must be at least 2 characters')
        
        if len(v) > 500:
            raise ValueError('Search query cannot exceed 500 characters')
        
        # Remove potentially harmful characters
        forbidden_chars = ['<', '>', '"', "'", '&', '\\']
        for char in forbidden_chars:
            if char in v:
                raise ValueError(f'Search query contains forbidden character: {char}')
        
        return v

class JSONField(str):
    """Custom JSON field that validates and stores JSON as string"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            try:
                # Validate JSON format
                json.loads(v)
                return v
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON format')
        
        elif isinstance(v, (dict, list)):
            # Convert dict/list to JSON string
            return json.dumps(v)
        
        else:
            raise ValueError('JSON field must be a string, dict, or list')
    
    def to_dict(self):
        """Convert JSON string back to dict/list"""
        return json.loads(self)

# Advanced model with custom fields
class AdvancedProductModel(BaseModel, BaseConfig):
    """Advanced product model with custom field types"""
    
    # Standard fields
    id: str = Field(..., description="Product ID")
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    
    # Custom field types
    price: PriceField = Field(..., description="Product price")
    search_query: Optional[SearchQueryField] = Field(None, description="Associated search query")
    metadata: Optional[JSONField] = Field(None, description="Product metadata as JSON")
    
    # Computed fields (not stored)
    _computed_discount: Optional[Decimal] = PrivateAttr(default=None)
    _search_boost: Optional[float] = PrivateAttr(default=None)
    
    # Dynamic fields based on user context
    user_rating: Optional[float] = Field(None, ge=0, le=5, description="User-specific rating")
    personalized_price: Optional[PriceField] = Field(None, description="Personalized price")
    
    @validator('metadata', pre=True)
    def validate_metadata_structure(cls, v):
        """Validate metadata structure"""
        if v is None:
            return v
        
        # If it's already a string, validate JSON
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('Invalid JSON in metadata')
        else:
            parsed = v
        
        # Validate required structure
        if isinstance(parsed, dict):
            # Check for required metadata fields
            required_fields = {'version', 'source'}
            missing_fields = required_fields - set(parsed.keys())
            if missing_fields:
                raise ValueError(f'Metadata missing required fields: {missing_fields}')
        
        return v
    
    @root_validator
    def validate_price_consistency(cls, values):
        """Validate price consistency across fields"""
        price = values.get('price')
        personalized_price = values.get('personalized_price')
        
        if price and personalized_price:
            # Personalized price should not be more than 50% different
            price_diff = abs(personalized_price - price) / price
            if price_diff > 0.5:
                raise ValueError('Personalized price differs too much from base price')
        
        return values
    
    def compute_discount(self, original_price: PriceField) -> Decimal:
        """Compute discount percentage"""
        if self.price >= original_price:
            return Decimal('0')
        
        discount = ((original_price - self.price) / original_price) * 100
        self._computed_discount = discount.quantize(Decimal('0.01'))
        return self._computed_discount
    
    def calculate_search_boost(self, user_preferences: Dict[str, Any]) -> float:
        """Calculate search boost based on user preferences"""
        boost = 1.0
        
        # Boost based on user rating
        if self.user_rating:
            boost += (self.user_rating - 3.0) * 0.1
        
        # Boost based on price preference
        if 'price_preference' in user_preferences:
            price_pref = user_preferences['price_preference']
            if price_pref == 'budget' and self.price < 50:
                boost += 0.2
            elif price_pref == 'premium' and self.price > 200:
                boost += 0.2
        
        self._search_boost = max(0.1, min(2.0, boost))
        return self._search_boost
    
    class Config(BaseConfig):
        # Allow arbitrary user attributes
        extra = 'allow'
        
        # Custom JSON encoders
        json_encoders = {
            PriceField: lambda v: str(v),
            JSONField: lambda v: v.to_dict() if hasattr(v, 'to_dict') else json.loads(v)
        }

# Model factories for dynamic creation
class ModelFactory:
    """Factory for creating dynamic Pydantic models"""
    
    @staticmethod
    def create_filtered_model(
        base_model: Type[BaseModel],
        included_fields: Optional[Set[str]] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
        model_name: str = "DynamicModel"
    ) -> Type[BaseModel]:
        """Create a new model with filtered fields"""
        
        # Get base model fields
        base_fields = base_model.__fields__
        
        # Filter fields
        if included_fields:
            filtered_fields = {
                name: field for name, field in base_fields.items()
                if name in included_fields
            }
        else:
            filtered_fields = base_fields.copy()
        
        # Add additional fields
        if additional_fields:
            for field_name, field_config in additional_fields.items():
                if isinstance(field_config, tuple):
                    field_type, field_info = field_config
                    filtered_fields[field_name] = ModelField(
                        name=field_name,
                        type_=field_type,
                        field_info=field_info,
                        model_config=base_model.__config__
                    )
        
        # Create new model class
        new_model = type(
            model_name,
            (BaseModel,),
            {
                '__fields__': filtered_fields,
                '__config__': base_model.__config__
            }
        )
        
        return new_model
    
    @staticmethod
    def create_request_response_pair(
        base_fields: Dict[str, Any],
        request_name: str = "Request",
        response_name: str = "Response"
    ) -> tuple[Type[BaseModel], Type[BaseModel]]:
        """Create matching request and response models"""
        
        # Request model (input validation)
        request_fields = {}
        response_fields = {}
        
        for field_name, field_config in base_fields.items():
            field_type, field_info, field_category = field_config
            
            if field_category in ['input', 'both']:
                request_fields[field_name] = (field_type, field_info)
            
            if field_category in ['output', 'both']:
                response_fields[field_name] = (field_type, field_info)
        
        # Create models
        RequestModel = create_model(request_name, **request_fields)
        ResponseModel = create_model(response_name, **response_fields)
        
        return RequestModel, ResponseModel

# Usage examples
def create_search_models():
    """Create search request and response models dynamically"""
    
    search_fields = {
        'query': (str, Field(..., min_length=2), 'input'),
        'category': (Optional[ProductCategory], Field(None), 'input'),
        'page': (int, Field(1, ge=1), 'input'),
        'size': (int, Field(10, ge=1, le=100), 'input'),
        'results': (List[AdvancedProductModel], Field(...), 'output'),
        'total': (int, Field(...), 'output'),
        'took_ms': (int, Field(...), 'output')
    }
    
    SearchRequest, SearchResponse = ModelFactory.create_request_response_pair(
        search_fields,
        "DynamicSearchRequest",
        "DynamicSearchResponse"
    )
    
    return SearchRequest, SearchResponse

# Advanced validation with context
class ContextualValidator:
    """Validator that considers request context"""
    
    def __init__(self, context: Dict[str, Any]):
        self.context = context
    
    def validate_user_permissions(self, value: Any, field: ModelField) -> Any:
        """Validate based on user permissions"""
        user_role = self.context.get('user_role', 'guest')
        
        if field.name == 'admin_fields' and user_role != 'admin':
            raise ValueError('Insufficient permissions for admin fields')
        
        return value
    
    def validate_rate_limits(self, value: Any, field: ModelField) -> Any:
        """Validate based on rate limits"""
        user_id = self.context.get('user_id')
        
        if field.name == 'size' and value > 50:
            # Check if user has premium access
            if not self.context.get('premium_user', False):
                raise ValueError('Large page sizes require premium access')
        
        return value

# Context-aware model
class ContextualSearchRequest(BaseModel):
    """Search request with contextual validation"""
    
    query: SearchQueryField = Field(..., description="Search query")
    size: int = Field(10, ge=1, le=100, description="Page size")
    include_admin_fields: bool = Field(False, description="Include admin fields")
    
    # Private context
    _context: Dict[str, Any] = PrivateAttr(default_factory=dict)
    
    def __init__(self, **data):
        # Extract context from data
        context = data.pop('_context', {})
        super().__init__(**data)
        self._context = context
    
    @validator('size')
    def validate_size_with_context(cls, v, values, **kwargs):
        """Validate size based on context"""
        # Note: In real implementation, context would be passed differently
        # This is a simplified example
        if v > 50:
            # This would check actual user context in practice
            raise ValueError('Large page sizes require premium access')
        return v
    
    @validator('include_admin_fields')
    def validate_admin_access(cls, v, values, **kwargs):
        """Validate admin field access"""
        if v:
            # This would check actual user role in practice
            raise ValueError('Admin fields require admin access')
        return v
```

## Integration with Elasticsearch-DSL

### Seamless Integration Patterns

```python
from elasticsearch_dsl import Document, Text, Keyword, Float, Integer, Boolean, Date, AsyncSearch
from typing import Type, TypeVar, Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

T = TypeVar('T', bound=BaseModel)

class PydanticElasticsearchIntegration:
    """Integration layer between Pydantic models and Elasticsearch-DSL"""
    
    def __init__(self, pydantic_model: Type[T], es_document: Type[Document]):
        self.pydantic_model = pydantic_model
        self.es_document = es_document
        self.field_mapping = self._create_field_mapping()
    
    def _create_field_mapping(self) -> Dict[str, str]:
        """Create mapping between Pydantic and Elasticsearch fields"""
        mapping = {}
        
        pydantic_fields = self.pydantic_model.__fields__
        es_fields = self.es_document._doc_type.mapping.to_dict()['properties']
        
        # Create direct mapping for matching field names
        for pydantic_field in pydantic_fields:
            if pydantic_field in es_fields:
                mapping[pydantic_field] = pydantic_field
        
        # Add custom mappings for different field names
        custom_mappings = {
            'id': '_id',
            'created_at': 'created_date',
            'updated_at': 'updated_date'
        }
        
        for pydantic_field, es_field in custom_mappings.items():
            if pydantic_field in pydantic_fields and es_field in es_fields:
                mapping[pydantic_field] = es_field
        
        return mapping
    
    def pydantic_to_es(self, pydantic_obj: T) -> Dict[str, Any]:
        """Convert Pydantic model to Elasticsearch document dict"""
        data = pydantic_obj.dict(exclude_unset=True)
        es_data = {}
        
        for pydantic_field, value in data.items():
            # Skip fields not in mapping
            if pydantic_field not in self.field_mapping:
                continue
            
            es_field = self.field_mapping[pydantic_field]
            
            # Apply type conversions
            if isinstance(value, Decimal):
                es_data[es_field] = float(value)
            elif isinstance(value, datetime):
                es_data[es_field] = value.isoformat()
            elif isinstance(value, Enum):
                es_data[es_field] = value.value
            else:
                es_data[es_field] = value
        
        return es_data
    
    def es_to_pydantic(self, es_hit) -> T:
        """Convert Elasticsearch hit to Pydantic model"""
        es_data = es_hit.to_dict()
        pydantic_data = {}
        
        # Reverse mapping
        reverse_mapping = {v: k for k, v in self.field_mapping.items()}
        
        for es_field, value in es_data.items():
            pydantic_field = reverse_mapping.get(es_field, es_field)
            
            # Skip unmapped fields
            if pydantic_field not in self.pydantic_model.__fields__:
                continue
            
            # Apply type conversions
            field_info = self.pydantic_model.__fields__[pydantic_field]
            
            if field_info.type_ == Decimal and isinstance(value, (int, float)):
                pydantic_data[pydantic_field] = Decimal(str(value))
            elif field_info.type_ == datetime and isinstance(value, str):
                pydantic_data[pydantic_field] = datetime.fromisoformat(
                    value.replace('Z', '+00:00')
                )
            else:
                pydantic_data[pydantic_field] = value
        
        # Add metadata
        if hasattr(es_hit, 'meta'):
            pydantic_data['id'] = es_hit.meta.id
            if hasattr(es_hit.meta, 'score'):
                pydantic_data['score'] = es_hit.meta.score
        
        return self.pydantic_model(**pydantic_data)
    
    async def create_document(self, pydantic_obj: T) -> str:
        """Create Elasticsearch document from Pydantic model"""
        es_data = self.pydantic_to_es(pydantic_obj)
        
        # Create document
        doc = self.es_document(**es_data)
        await doc.save()
        
        return doc.meta.id
    
    async def update_document(self, doc_id: str, pydantic_obj: T) -> bool:
        """Update Elasticsearch document with Pydantic model"""
        try:
            doc = await self.es_document.get(doc_id)
            es_data = self.pydantic_to_es(pydantic_obj)
            
            # Update document fields
            for field, value in es_data.items():
                setattr(doc, field, value)
            
            await doc.save()
            return True
        except NotFoundError:
            return False
    
    async def search_to_pydantic(
        self, 
        search: AsyncSearch, 
        include_aggregations: bool = False
    ) -> Dict[str, Any]:
        """Execute search and convert results to Pydantic models"""
        response = await search.execute()
        
        # Convert hits to Pydantic models
        results = [
            self.es_to_pydantic(hit) 
            for hit in response.hits
        ]
        
        # Build response
        search_response = {
            'results': results,
            'total': response.hits.total.value,
            'max_score': response.hits.max_score,
            'took_ms': response.took
        }
        
        if include_aggregations and hasattr(response, 'aggregations'):
            search_response['aggregations'] = response.aggregations.to_dict()
        
        return search_response

# Auto-sync decorator
def auto_sync_elasticsearch(pydantic_model: Type[BaseModel], es_document: Type[Document]):
    """Decorator to automatically sync Pydantic model changes to Elasticsearch"""
    
    def decorator(cls):
        original_init = cls.__init__
        
        def __init__(self, **data):
            original_init(self, **data)
            self._es_integration = PydanticElasticsearchIntegration(pydantic_model, es_document)
        
        async def save_to_elasticsearch(self) -> str:
            """Save this model to Elasticsearch"""
            return await self._es_integration.create_document(self)
        
        async def update_in_elasticsearch(self, doc_id: str) -> bool:
            """Update Elasticsearch document with this model"""
            return await self._es_integration.update_document(doc_id, self)
        
        cls.__init__ = __init__
        cls.save_to_elasticsearch = save_to_elasticsearch
        cls.update_in_elasticsearch = update_in_elasticsearch
        
        return cls
    
    return decorator

# Usage example
@auto_sync_elasticsearch(ProductResponse, ProductDocument)
class SyncedProductModel(ProductResponse):
    """Product model with auto-sync to Elasticsearch"""
    pass

# Repository pattern with Pydantic integration
class PydanticElasticsearchRepository:
    """Repository pattern with Pydantic and Elasticsearch integration"""
    
    def __init__(self, pydantic_model: Type[T], es_document: Type[Document]):
        self.integration = PydanticElasticsearchIntegration(pydantic_model, es_document)
        self.pydantic_model = pydantic_model
        self.es_document = es_document
    
    async def create(self, model: T) -> str:
        """Create new document"""
        return await self.integration.create_document(model)
    
    async def get_by_id(self, doc_id: str) -> Optional[T]:
        """Get document by ID"""
        try:
            doc = await self.es_document.get(doc_id)
            return self.integration.es_to_pydantic(doc)
        except NotFoundError:
            return None
    
    async def update(self, doc_id: str, model: T) -> bool:
        """Update document"""
        return await self.integration.update_document(doc_id, model)
    
    async def delete(self, doc_id: str) -> bool:
        """Delete document"""
        try:
            doc = await self.es_document.get(doc_id)
            await doc.delete()
            return True
        except NotFoundError:
            return False
    
    async def search(self, **kwargs) -> List[T]:
        """Search documents and return Pydantic models"""
        search = self.es_document.search()
        
        # Apply search parameters
        if 'query' in kwargs:
            search = search.query('multi_match', query=kwargs['query'])
        
        if 'filters' in kwargs:
            for field, value in kwargs['filters'].items():
                search = search.filter('term', **{field: value})
        
        response = await search.execute()
        
        return [
            self.integration.es_to_pydantic(hit)
            for hit in response.hits
        ]
    
    async def bulk_create(self, models: List[T]) -> List[str]:
        """Create multiple documents in bulk"""
        from elasticsearch.helpers import async_bulk
        from elasticsearch_dsl.connections import connections
        
        client = connections.get_connection()
        
        # Prepare bulk actions
        actions = []
        for model in models:
            es_data = self.integration.pydantic_to_es(model)
            action = {
                '_index': self.es_document._doc_type.index,
                '_source': es_data
            }
            actions.append(action)
        
        # Execute bulk operation
        results = await async_bulk(client, actions)
        
        # Return document IDs
        return [result['create']['_id'] for result in results[1]]

# Service layer with Pydantic validation
class PydanticSearchService:
    """Search service with Pydantic model validation"""
    
    def __init__(self, repository: PydanticElasticsearchRepository):
        self.repository = repository
    
    async def search_products(
        self, 
        request: ProductSearchRequest
    ) -> SearchResponse:
        """Search products with validated request and response"""
        
        # Build Elasticsearch search
        search = AsyncSearch(index='products')
        
        # Add query
        if request.query:
            search = search.query('multi_match', 
                                query=request.query,
                                fields=['name^3', 'description^2'])
        
        # Add filters
        if request.category:
            search = search.filter('term', category=request.category.value)
        
        if request.price_min is not None or request.price_max is not None:
            price_range = {}
            if request.price_min is not None:
                price_range['gte'] = float(request.price_min)
            if request.price_max is not None:
                price_range['lte'] = float(request.price_max)
            search = search.filter('range', price=price_range)
        
        # Add pagination
        start = (request.page - 1) * request.size
        search = search[start:start + request.size]
        
        # Execute and convert
        search_results = await self.repository.integration.search_to_pydantic(
            search, 
            include_aggregations=request.include_aggregations
        )
        
        # Build response
        metadata = SearchMetadata(
            total=search_results['total'],
            page=request.page,
            size=request.size,
            pages=(search_results['total'] + request.size - 1) // request.size,
            took_ms=search_results['took_ms'],
            max_score=search_results.get('max_score')
        )
        
        return SearchResponse(
            results=search_results['results'],
            metadata=metadata,
            aggregations=search_results.get('aggregations')
        )

# Initialize components
product_repository = PydanticElasticsearchRepository(ProductResponse, ProductDocument)
search_service = PydanticSearchService(product_repository)

# FastAPI endpoint with full integration
@app.post("/api/v1/products/integrated-search", response_model=SearchResponse)
async def integrated_search(
    request: ProductSearchRequest
) -> SearchResponse:
    """Fully integrated search endpoint with Pydantic and Elasticsearch-DSL"""
    return await search_service.search_products(request)
```

## Performance Optimization

### Optimization Strategies for Pydantic Models

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Type
import asyncio
from functools import lru_cache, wraps
import cProfile
import time

class PerformanceOptimizedModel(BaseModel):
    """Base model with performance optimizations"""
    
    class Config:
        # Performance optimizations
        validate_assignment = False  # Skip validation on assignment
        copy_on_model_validation = False  # Avoid unnecessary copying
        validate_all = False  # Only validate changed fields
        use_enum_values = True  # Use enum values directly
        allow_reuse = True  # Allow model reuse
        extra = 'forbid'  # Strict field validation
    
    def dict(self, **kwargs):
        """Optimized dict conversion"""
        # Use exclude_unset by default for better performance
        kwargs.setdefault('exclude_unset', True)
        return super().dict(**kwargs)

# Model caching
class CachedModelMixin:
    """Mixin for caching model instances"""
    
    _model_cache: Dict[str, Any] = {}
    _cache_size_limit = 1000
    
    @classmethod
    def from_cache_or_create(cls, cache_key: str, **data):
        """Get model from cache or create new one"""
        if cache_key in cls._model_cache:
            return cls._model_cache[cache_key]
        
        # Check cache size limit
        if len(cls._model_cache) >= cls._cache_size_limit:
            # Remove oldest entries (simple LRU)
            oldest_key = next(iter(cls._model_cache))
            del cls._model_cache[oldest_key]
        
        # Create and cache new model
        model = cls(**data)
        cls._model_cache[cache_key] = model
        return model
    
    @classmethod
    def clear_cache(cls):
        """Clear model cache"""
        cls._model_cache.clear()

# Batch processing for better performance
class BatchProcessor:
    """Batch processor for Pydantic models"""
    
    def __init__(self, model_class: Type[BaseModel], batch_size: int = 100):
        self.model_class = model_class
        self.batch_size = batch_size
    
    async def process_batch(self, data_list: List[Dict[str, Any]]) -> List[BaseModel]:
        """Process data in batches for better performance"""
        results = []
        
        for i in range(0, len(data_list), self.batch_size):
            batch = data_list[i:i + self.batch_size]
            
            # Process batch
            batch_results = await self._process_single_batch(batch)
            results.extend(batch_results)
            
            # Allow other coroutines to run
            await asyncio.sleep(0)
        
        return results
    
    async def _process_single_batch(self, batch: List[Dict[str, Any]]) -> List[BaseModel]:
        """Process a single batch"""
        models = []
        
        for data in batch:
            try:
                model = self.model_class(**data)
                models.append(model)
            except Exception as e:
                # Log error and continue
                print(f"Error processing item: {e}")
                continue
        
        return models

# Lazy loading for expensive fields
class LazyLoadedModel(BaseModel):
    """Model with lazy loading for expensive fields"""
    
    # Regular fields
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    price: Decimal = Field(..., description="Product price")
    
    # Lazy-loaded fields
    _detailed_description: Optional[str] = None
    _reviews: Optional[List[Dict[str, Any]]] = None
    _recommendations: Optional[List[str]] = None
    
    @property
    def detailed_description(self) -> Optional[str]:
        """Lazy-loaded detailed description"""
        if self._detailed_description is None:
            self._detailed_description = self._load_detailed_description()
        return self._detailed_description
    
    @property
    def reviews(self) -> List[Dict[str, Any]]:
        """Lazy-loaded reviews"""
        if self._reviews is None:
            self._reviews = self._load_reviews()
        return self._reviews
    
    @property
    def recommendations(self) -> List[str]:
        """Lazy-loaded recommendations"""
        if self._recommendations is None:
            self._recommendations = self._load_recommendations()
        return self._recommendations
    
    def _load_detailed_description(self) -> str:
        """Load detailed description (placeholder)"""
        # This would make an async call to get detailed description
        return f"Detailed description for {self.name}"
    
    def _load_reviews(self) -> List[Dict[str, Any]]:
        """Load reviews (placeholder)"""
        # This would make an async call to get reviews
        return [{"rating": 5, "comment": "Great product!"}]
    
    def _load_recommendations(self) -> List[str]:
        """Load recommendations (placeholder)"""
        # This would make an async call to get recommendations
        return ["rec1", "rec2", "rec3"]

# Performance monitoring
class PerformanceMonitor:
    """Monitor performance of Pydantic operations"""
    
    def __init__(self):
        self.timings = {}
        self.call_counts = {}
    
    def time_operation(self, operation_name: str):
        """Decorator to time operations"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                result = await func(*args, **kwargs)
                end_time = time.time()
                
                self._record_timing(operation_name, end_time - start_time)
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                self._record_timing(operation_name, end_time - start_time)
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _record_timing(self, operation: str, duration: float):
        """Record timing for operation"""
        if operation not in self.timings:
            self.timings[operation] = []
            self.call_counts[operation] = 0
        
        self.timings[operation].append(duration)
        self.call_counts[operation] += 1
    
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics"""
        stats = {}
        
        for operation, times in self.timings.items():
            stats[operation] = {
                'count': self.call_counts[operation],
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        
        return stats

# Global performance monitor
perf_monitor = PerformanceMonitor()

# Optimized search response
class OptimizedSearchResponse(PerformanceOptimizedModel, CachedModelMixin):
    """Optimized search response model"""
    
    results: List[Dict[str, Any]] = Field(..., description="Raw results for better performance")
    metadata: SearchMetadata = Field(..., description="Search metadata")
    
    @validator('results', pre=True)
    def optimize_results(cls, v):
        """Optimize results for performance"""
        if isinstance(v, list) and len(v) > 100:
            # For large result sets, only include essential fields
            essential_fields = {'id', 'name', 'price', 'score'}
            return [
                {k: item.get(k) for k in essential_fields if k in item}
                for item in v
            ]
        return v
    
    def get_typed_results(self, result_model: Type[BaseModel]) -> List[BaseModel]:
        """Convert results to typed models on demand"""
        cache_key = f"typed_results_{id(self)}_{result_model.__name__}"
        
        if hasattr(self, '_typed_results_cache'):
            cached = self._typed_results_cache.get(cache_key)
            if cached:
                return cached
        
        # Convert to typed models
        typed_results = []
        for result_data in self.results:
            try:
                typed_result = result_model(**result_data)
                typed_results.append(typed_result)
            except Exception:
                continue
        
        # Cache results
        if not hasattr(self, '_typed_results_cache'):
            self._typed_results_cache = {}
        self._typed_results_cache[cache_key] = typed_results
        
        return typed_results

# Benchmarking utilities
class PydanticBenchmark:
    """Benchmark Pydantic model performance"""
    
    @staticmethod
    async def benchmark_model_creation(
        model_class: Type[BaseModel],
        test_data: List[Dict[str, Any]],
        iterations: int = 1000
    ) -> Dict[str, float]:
        """Benchmark model creation performance"""
        
        # Warmup
        for _ in range(10):
            model_class(**test_data[0])
        
        # Benchmark
        start_time = time.time()
        
        for i in range(iterations):
            data = test_data[i % len(test_data)]
            model_class(**data)
        
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        return {
            'total_time': total_time,
            'avg_time': avg_time,
            'models_per_second': iterations / total_time
        }
    
    @staticmethod
    async def benchmark_serialization(
        models: List[BaseModel],
        iterations: int = 1000
    ) -> Dict[str, float]:
        """Benchmark model serialization performance"""
        
        # Warmup
        for _ in range(10):
            models[0].dict()
        
        # Benchmark
        start_time = time.time()
        
        for i in range(iterations):
            model = models[i % len(models)]
            model.dict()
        
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        return {
            'total_time': total_time,
            'avg_time': avg_time,
            'serializations_per_second': iterations / total_time
        }

# Performance-optimized endpoint
@app.get("/api/v1/products/optimized-search")
@perf_monitor.time_operation("optimized_search")
async def optimized_search_endpoint(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    include_full_models: bool = Query(False, description="Include full model objects")
) -> Union[OptimizedSearchResponse, SearchResponse]:
    """Performance-optimized search endpoint"""
    
    # Use batch processing for large requests
    if size > 50:
        processor = BatchProcessor(SearchResultProduct, batch_size=25)
    
    # Execute search
    search_results = await execute_optimized_search(q, page, size)
    
    # Return optimized response by default
    if not include_full_models:
        return OptimizedSearchResponse(
            results=search_results['raw_results'],
            metadata=SearchMetadata(**search_results['metadata'])
        )
    
    # Return full response if requested
    return SearchResponse(
        results=search_results['typed_results'],
        metadata=SearchMetadata(**search_results['metadata'])
    )

@app.get("/api/v1/performance/stats")
async def get_performance_stats():
    """Get performance monitoring statistics"""
    return perf_monitor.get_statistics()

async def execute_optimized_search(query: str, page: int, size: int) -> Dict[str, Any]:
    """Execute optimized search (placeholder implementation)"""
    # This would contain the actual search logic
    return {
        'raw_results': [],
        'typed_results': [],
        'metadata': {
            'total': 0,
            'page': page,
            'size': size,
            'pages': 0,
            'took_ms': 10
        }
    }
```

## Next Steps

1. **[Dependency Injection](04_dependency-injection.md)** - Implement service architecture with FastAPI dependencies
2. **[Advanced Search](../04-advanced-search/01_complex-queries.md)** - Build sophisticated search features
3. **[Data Modeling](../05-data-modeling/01_document-relationships.md)** - Design complex data relationships
4. **[Testing](../07-testing-deployment/01_testing-strategies.md)** - Test your Pydantic models and endpoints

## Additional Resources

- **Pydantic Documentation**: [pydantic-docs.helpmanual.io](https://pydantic-docs.helpmanual.io/)
- **FastAPI with Pydantic**: [fastapi.tiangolo.com/tutorial/response-model](https://fastapi.tiangolo.com/tutorial/response-model/)
- **Performance Best Practices**: [pydantic-docs.helpmanual.io/usage/performance](https://pydantic-docs.helpmanual.io/usage/performance/)
- **Type Hints Guide**: [docs.python.org/3/library/typing.html](https://docs.python.org/3/library/typing.html)