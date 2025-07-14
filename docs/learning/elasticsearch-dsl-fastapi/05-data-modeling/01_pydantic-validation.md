# Pydantic Validation

Advanced Pydantic validation patterns for FastAPI + Elasticsearch-DSL applications with comprehensive data validation and transformation.

## Table of Contents
- [Request Validation Models](#request-validation-models)
- [Response Serialization](#response-serialization)
- [Custom Validators](#custom-validators)
- [Data Transformation](#data-transformation)
- [Validation Error Handling](#validation-error-handling)
- [Advanced Patterns](#advanced-patterns)
- [Performance Optimization](#performance-optimization)
- [Next Steps](#next-steps)

## Request Validation Models

### Basic Search Request Models
```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SearchSortField(BaseModel):
    field: str = Field(..., min_length=1, max_length=100)
    order: SortOrder = SortOrder.DESC

class SearchRequest(BaseModel):
    """Comprehensive search request model with validation."""
    
    query: str = Field(..., min_length=1, max_length=1000, 
                      description="Search query text")
    
    # Filtering options
    filters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Field-based filters"
    )
    
    # Pagination
    page: int = Field(default=1, ge=1, le=1000,
                     description="Page number (1-based)")
    size: int = Field(default=10, ge=1, le=100,
                     description="Results per page")
    
    # Sorting
    sort: Optional[List[SearchSortField]] = Field(
        default=None,
        max_items=5,
        description="Sort criteria"
    )
    
    # Search options
    highlight: bool = Field(default=False,
                           description="Enable result highlighting")
    include_aggregations: bool = Field(default=False,
                                     description="Include facet aggregations")
    
    # Field selection
    include_fields: Optional[List[str]] = Field(
        default=None,
        max_items=50,
        description="Fields to include in response"
    )
    exclude_fields: Optional[List[str]] = Field(
        default=None,
        max_items=50,
        description="Fields to exclude from response"
    )

    @validator('query')
    def validate_query(cls, v):
        """Custom query validation."""
        if not v or v.isspace():
            raise ValueError('Query cannot be empty or whitespace')
        
        # Remove dangerous characters
        forbidden_chars = ['<', '>', '"', "'"]
        if any(char in v for char in forbidden_chars):
            raise ValueError('Query contains forbidden characters')
        
        return v.strip()

    @validator('filters')
    def validate_filters(cls, v):
        """Validate filter structure."""
        if not v:
            return v
        
        allowed_filter_fields = {
            'category', 'author', 'status', 'tags', 'date_range',
            'price_range', 'location', 'language'
        }
        
        for field in v.keys():
            if field not in allowed_filter_fields:
                raise ValueError(f'Filter field "{field}" is not allowed')
        
        # Validate date ranges
        if 'date_range' in v:
            date_range = v['date_range']
            if not isinstance(date_range, dict):
                raise ValueError('date_range must be an object')
            
            if 'from' in date_range:
                try:
                    datetime.fromisoformat(date_range['from'].replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError('Invalid date format in date_range.from')
        
        return v

    @root_validator
    def validate_field_selection(cls, values):
        """Validate include/exclude field combinations."""
        include_fields = values.get('include_fields')
        exclude_fields = values.get('exclude_fields')
        
        if include_fields and exclude_fields:
            # Check for conflicts
            if set(include_fields) & set(exclude_fields):
                raise ValueError('Cannot include and exclude the same fields')
        
        return values

    def to_elasticsearch_params(self) -> Dict[str, Any]:
        """Convert to Elasticsearch query parameters."""
        params = {
            'from': (self.page - 1) * self.size,
            'size': self.size,
        }
        
        if self.sort:
            params['sort'] = [
                {sort_field.field: {'order': sort_field.order}}
                for sort_field in self.sort
            ]
        
        if self.include_fields:
            params['_source'] = {'includes': self.include_fields}
        elif self.exclude_fields:
            params['_source'] = {'excludes': self.exclude_fields}
        
        if self.highlight:
            params['highlight'] = {
                'fields': {
                    'title': {},
                    'content': {}
                }
            }
        
        return params
```

### Advanced Request Models
```python
from typing import Literal, Union
from pydantic import Field, validator

class DateRange(BaseModel):
    """Date range validation model."""
    
    from_date: Optional[datetime] = Field(alias='from')
    to_date: Optional[datetime] = Field(alias='to')
    
    @root_validator
    def validate_date_range(cls, values):
        from_date = values.get('from_date')
        to_date = values.get('to_date')
        
        if from_date and to_date and from_date >= to_date:
            raise ValueError('from_date must be before to_date')
        
        return values

class NumericRange(BaseModel):
    """Numeric range validation model."""
    
    min_value: Optional[float] = Field(alias='min', ge=0)
    max_value: Optional[float] = Field(alias='max', ge=0)
    
    @root_validator
    def validate_numeric_range(cls, values):
        min_val = values.get('min_value')
        max_val = values.get('max_value')
        
        if min_val is not None and max_val is not None and min_val >= max_val:
            raise ValueError('min_value must be less than max_value')
        
        return values

class AdvancedSearchRequest(BaseModel):
    """Advanced search with complex filtering."""
    
    # Text search
    query: Optional[str] = Field(default="*", max_length=1000)
    query_type: Literal["match", "multi_match", "query_string"] = "multi_match"
    
    # Advanced filters
    category_filters: Optional[List[str]] = Field(
        default=None, max_items=10
    )
    date_range: Optional[DateRange] = None
    price_range: Optional[NumericRange] = None
    
    # Geospatial
    location: Optional[Dict[str, float]] = None
    radius_km: Optional[float] = Field(default=None, ge=0.1, le=100)
    
    # Aggregations
    facets: Optional[List[str]] = Field(
        default=None,
        max_items=10,
        description="Fields to aggregate for faceted search"
    )
    
    # Search behavior
    fuzzy: bool = Field(default=False)
    boost_fields: Optional[Dict[str, float]] = Field(
        default=None,
        description="Field boost weights"
    )

    @validator('location')
    def validate_location(cls, v):
        if not v:
            return v
        
        required_fields = {'lat', 'lon'}
        if not required_fields.issubset(v.keys()):
            raise ValueError('Location must contain lat and lon fields')
        
        lat, lon = v['lat'], v['lon']
        if not (-90 <= lat <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        if not (-180 <= lon <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        
        return v

    @root_validator
    def validate_location_radius(cls, values):
        location = values.get('location')
        radius = values.get('radius_km')
        
        if bool(location) != bool(radius):
            raise ValueError('location and radius_km must be provided together')
        
        return values
```

## Response Serialization

### Structured Response Models
```python
from typing import Generic, TypeVar, List
from pydantic.generics import GenericModel

T = TypeVar('T')

class SearchHighlight(BaseModel):
    """Search result highlighting."""
    field: str
    fragments: List[str]

class SearchResult(BaseModel):
    """Individual search result."""
    
    id: str
    score: float
    source: Dict[str, Any]
    highlight: Optional[List[SearchHighlight]] = None
    
    @validator('score')
    def validate_score(cls, v):
        if v < 0:
            raise ValueError('Score cannot be negative')
        return round(v, 4)  # Limit precision

class AggregationBucket(BaseModel):
    """Aggregation bucket result."""
    key: Union[str, int, float]
    doc_count: int
    key_as_string: Optional[str] = None

class Aggregation(BaseModel):
    """Aggregation result."""
    name: str
    buckets: Optional[List[AggregationBucket]] = None
    value: Optional[float] = None

class SearchResponse(GenericModel, Generic[T]):
    """Generic search response model."""
    
    total: int = Field(..., ge=0)
    max_score: Optional[float] = Field(None, ge=0)
    hits: List[T]
    
    # Pagination info
    page: int = Field(..., ge=1)
    size: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
    
    # Aggregations
    aggregations: Optional[List[Aggregation]] = None
    
    # Performance metrics
    took_ms: int = Field(..., ge=0)
    
    @validator('total_pages', always=True)
    def calculate_total_pages(cls, v, values):
        total = values.get('total', 0)
        size = values.get('size', 1)
        return (total + size - 1) // size  # Ceiling division

class ProductSearchResult(BaseModel):
    """Typed product search result."""
    
    id: str
    name: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: str
    brand: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    image_url: Optional[str] = None
    
    # Computed fields
    formatted_price: Optional[str] = None
    
    @validator('formatted_price', always=True)
    def format_price(cls, v, values):
        price = values.get('price')
        if price is not None:
            return f"${price:.2f}"
        return None

# Type-specific response
ProductSearchResponse = SearchResponse[ProductSearchResult]
```

### Dynamic Response Models
```python
from pydantic import create_model
from typing import Type

class ResponseModelFactory:
    """Factory for creating dynamic response models."""
    
    @staticmethod
    def create_search_result_model(
        index_name: str,
        included_fields: Optional[List[str]] = None,
        excluded_fields: Optional[List[str]] = None
    ) -> Type[BaseModel]:
        """Create dynamic model based on field selection."""
        
        # Base fields always included
        base_fields = {
            'id': (str, ...),
            'score': (float, ...)
        }
        
        # Field definitions based on index type
        field_definitions = {
            'blog_posts': {
                'title': (str, ...),
                'content': (Optional[str], None),
                'author': (str, ...),
                'published_date': (Optional[datetime], None),
                'tags': (Optional[List[str]], None)
            },
            'products': {
                'name': (str, ...),
                'description': (Optional[str], None),
                'price': (float, ...),
                'category': (str, ...),
                'brand': (Optional[str], None)
            }
        }
        
        available_fields = field_definitions.get(index_name, {})
        
        # Apply field selection
        if included_fields:
            available_fields = {
                k: v for k, v in available_fields.items()
                if k in included_fields
            }
        
        if excluded_fields:
            available_fields = {
                k: v for k, v in available_fields.items()
                if k not in excluded_fields
            }
        
        # Combine base and selected fields
        model_fields = {**base_fields, **available_fields}
        
        # Create dynamic model
        model_name = f"{index_name.title()}SearchResult"
        return create_model(model_name, **model_fields)

# Usage in FastAPI endpoint
@app.post("/search/{index_name}")
async def dynamic_search(
    index_name: str,
    request: SearchRequest
):
    """Search endpoint with dynamic response model."""
    
    # Create response model based on request
    ResultModel = ResponseModelFactory.create_search_result_model(
        index_name=index_name,
        included_fields=request.include_fields,
        excluded_fields=request.exclude_fields
    )
    
    # Perform search...
    # Return typed response
    pass
```

## Custom Validators

### Field-Level Validators
```python
import re
from typing import Any

class CustomValidators:
    """Collection of reusable custom validators."""
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Email validation with normalization."""
        if not email:
            raise ValueError('Email cannot be empty')
        
        email = email.strip().lower()
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError('Invalid email format')
        
        return email
    
    @staticmethod
    def validate_slug(slug: str) -> str:
        """URL slug validation."""
        if not slug:
            raise ValueError('Slug cannot be empty')
        
        slug = slug.strip().lower()
        
        # Allow only letters, numbers, and hyphens
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValueError('Slug can only contain letters, numbers, and hyphens')
        
        if slug.startswith('-') or slug.endswith('-'):
            raise ValueError('Slug cannot start or end with hyphen')
        
        if '--' in slug:
            raise ValueError('Slug cannot contain consecutive hyphens')
        
        return slug
    
    @staticmethod
    def validate_tags(tags: List[str]) -> List[str]:
        """Tag validation and normalization."""
        if not tags:
            return []
        
        normalized_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise ValueError('All tags must be strings')
            
            tag = tag.strip().lower()
            if not tag:
                continue
            
            if len(tag) > 50:
                raise ValueError('Tag length cannot exceed 50 characters')
            
            if not re.match(r'^[a-z0-9\s-]+$', tag):
                raise ValueError('Tags can only contain letters, numbers, spaces, and hyphens')
            
            normalized_tags.append(tag)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(normalized_tags))

class BlogPostRequest(BaseModel):
    """Blog post with custom validators."""
    
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10)
    author_email: str
    tags: List[str] = Field(default_factory=list, max_items=10)
    
    # Apply custom validators
    _validate_email = validator('author_email', allow_reuse=True)(CustomValidators.validate_email)
    _validate_slug = validator('slug', allow_reuse=True)(CustomValidators.validate_slug)
    _validate_tags = validator('tags', allow_reuse=True)(CustomValidators.validate_tags)
    
    @validator('title')
    def validate_title(cls, v):
        """Title-specific validation."""
        v = v.strip()
        
        # Check for common title issues
        if v.isupper():
            raise ValueError('Title should not be all uppercase')
        
        if v.count('!') > 3:
            raise ValueError('Title contains too many exclamation marks')
        
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """Content validation."""
        if len(v.split()) < 10:
            raise ValueError('Content must contain at least 10 words')
        
        # Check for potentially problematic content
        forbidden_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'on\w+\s*=',  # Event handlers
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, v, re.IGNORECASE | re.DOTALL):
                raise ValueError('Content contains potentially dangerous code')
        
        return v
```

### Cross-Field Validation
```python
class EventRequest(BaseModel):
    """Event with complex cross-field validation."""
    
    name: str = Field(..., min_length=1, max_length=100)
    start_date: datetime
    end_date: datetime
    location: str = Field(..., min_length=1, max_length=200)
    capacity: int = Field(..., ge=1, le=10000)
    ticket_price: float = Field(..., ge=0)
    is_free: bool = False
    
    @root_validator
    def validate_event_logic(cls, values):
        """Cross-field validation for event logic."""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        is_free = values.get('is_free')
        ticket_price = values.get('ticket_price')
        
        # Date validation
        if start_date and end_date:
            if start_date >= end_date:
                raise ValueError('end_date must be after start_date')
            
            # Check if start date is not in the past
            if start_date < datetime.utcnow():
                raise ValueError('start_date cannot be in the past')
            
            # Check maximum event duration (30 days)
            max_duration = timedelta(days=30)
            if end_date - start_date > max_duration:
                raise ValueError('Event duration cannot exceed 30 days')
        
        # Price validation
        if is_free and ticket_price > 0:
            raise ValueError('Free events cannot have a ticket price')
        
        if not is_free and ticket_price == 0:
            values['is_free'] = True  # Auto-correct
        
        return values
```

## Data Transformation

### Elasticsearch to Pydantic Conversion
```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Float, Date

class ProductDocument(AsyncDocument):
    """Elasticsearch document model."""
    name = Text()
    description = Text()
    price = Float()
    category = Keyword()
    brand = Keyword()
    
    class Index:
        name = 'products'

class ProductResponse(BaseModel):
    """API response model."""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    category: str
    brand: Optional[str] = None
    formatted_price: str
    
    @classmethod
    def from_elasticsearch(cls, hit, include_score: bool = False):
        """Convert Elasticsearch hit to Pydantic model."""
        data = {
            'id': hit.meta.id,
            'name': hit.name,
            'description': getattr(hit, 'description', None),
            'price': hit.price,
            'category': hit.category,
            'brand': getattr(hit, 'brand', None),
            'formatted_price': f"${hit.price:.2f}"
        }
        
        if include_score:
            data['score'] = hit.meta.score
        
        return cls(**data)

class TransformationService:
    """Service for data transformation between models."""
    
    @staticmethod
    async def transform_search_results(
        search_response,
        result_model: Type[BaseModel],
        include_score: bool = False
    ) -> List[BaseModel]:
        """Transform Elasticsearch results to Pydantic models."""
        results = []
        
        for hit in search_response.hits:
            if hasattr(result_model, 'from_elasticsearch'):
                result = result_model.from_elasticsearch(hit, include_score)
            else:
                # Generic transformation
                data = hit.to_dict()
                data['id'] = hit.meta.id
                
                if include_score:
                    data['score'] = hit.meta.score
                
                result = result_model(**data)
            
            results.append(result)
        
        return results
    
    @staticmethod
    def transform_aggregations(aggs_response) -> List[Aggregation]:
        """Transform Elasticsearch aggregations to Pydantic models."""
        aggregations = []
        
        for agg_name, agg_data in aggs_response.to_dict().items():
            if 'buckets' in agg_data:
                # Bucket aggregation
                buckets = [
                    AggregationBucket(
                        key=bucket['key'],
                        doc_count=bucket['doc_count'],
                        key_as_string=bucket.get('key_as_string')
                    )
                    for bucket in agg_data['buckets']
                ]
                
                aggregations.append(Aggregation(
                    name=agg_name,
                    buckets=buckets
                ))
            
            elif 'value' in agg_data:
                # Metric aggregation
                aggregations.append(Aggregation(
                    name=agg_name,
                    value=agg_data['value']
                ))
        
        return aggregations
```

## Validation Error Handling

### Custom Exception Handling
```python
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

class ValidationErrorResponse(BaseModel):
    """Structured validation error response."""
    
    error: str = "validation_error"
    message: str
    details: List[Dict[str, Any]]

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    
    error_details = []
    for error in exc.errors():
        error_details.append({
            'field': '.'.join(str(x) for x in error['loc'][1:]),  # Remove 'body' prefix
            'message': error['msg'],
            'type': error['type'],
            'input': error.get('input')
        })
    
    response = ValidationErrorResponse(
        message="Request validation failed",
        details=error_details
    )
    
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )

class BusinessValidationError(Exception):
    """Custom business logic validation error."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(message)

@app.exception_handler(BusinessValidationError)
async def business_validation_exception_handler(request: Request, exc: BusinessValidationError):
    """Handle business logic validation errors."""
    
    response = ValidationErrorResponse(
        message="Business validation failed",
        details=[{
            'field': exc.field,
            'message': exc.message,
            'type': 'business_validation',
            'input': exc.value
        }]
    )
    
    return JSONResponse(
        status_code=400,
        content=response.dict()
    )
```

## Advanced Patterns

### Conditional Model Validation
```python
from typing import Union

class BaseProductRequest(BaseModel):
    name: str
    price: float

class PhysicalProductRequest(BaseProductRequest):
    weight_kg: float = Field(..., gt=0)
    dimensions: Dict[str, float]  # length, width, height
    shipping_class: str

class DigitalProductRequest(BaseProductRequest):
    download_url: str = Field(..., regex=r'^https?://.+')
    file_size_mb: float = Field(..., gt=0)
    license_type: str

class ProductRequest(BaseModel):
    """Product request with conditional validation."""
    
    product_type: Literal["physical", "digital"]
    product_data: Union[PhysicalProductRequest, DigitalProductRequest]
    
    @root_validator(pre=True)
    def validate_product_data(cls, values):
        """Validate product data based on type."""
        product_type = values.get('product_type')
        product_data = values.get('product_data', {})
        
        if product_type == 'physical':
            values['product_data'] = PhysicalProductRequest(**product_data)
        elif product_type == 'digital':
            values['product_data'] = DigitalProductRequest(**product_data)
        else:
            raise ValueError(f'Invalid product_type: {product_type}')
        
        return values

# Usage with FastAPI discriminated unions
from pydantic import Field
from typing_extensions import Annotated

class ProductRequestV2(BaseModel):
    product: Annotated[
        Union[PhysicalProductRequest, DigitalProductRequest],
        Field(discriminator='product_type')
    ]
```

## Performance Optimization

### Model Caching and Validation Optimization
```python
from functools import lru_cache
from typing import Type

class ModelCache:
    """Cache for frequently used model instances."""
    
    _model_cache: Dict[str, Type[BaseModel]] = {}
    
    @classmethod
    @lru_cache(maxsize=100)
    def get_cached_model(cls, model_name: str, fields_hash: str) -> Type[BaseModel]:
        """Get cached model definition."""
        cache_key = f"{model_name}_{fields_hash}"
        return cls._model_cache.get(cache_key)
    
    @classmethod
    def cache_model(cls, model_name: str, fields_hash: str, model: Type[BaseModel]):
        """Cache model definition."""
        cache_key = f"{model_name}_{fields_hash}"
        cls._model_cache[cache_key] = model

class OptimizedValidation:
    """Optimized validation patterns."""
    
    @staticmethod
    def batch_validate(
        data_list: List[Dict[str, Any]],
        model_class: Type[BaseModel]
    ) -> List[BaseModel]:
        """Batch validation for multiple items."""
        results = []
        errors = []
        
        for i, data in enumerate(data_list):
            try:
                result = model_class(**data)
                results.append(result)
            except ValidationError as e:
                errors.append({'index': i, 'errors': e.errors()})
        
        if errors:
            raise ValueError(f"Validation failed for {len(errors)} items: {errors}")
        
        return results
    
    @staticmethod
    def lazy_validation(data: Dict[str, Any], model_class: Type[BaseModel]):
        """Lazy validation - validate only when accessed."""
        
        class LazyModel:
            def __init__(self, data, model_class):
                self._data = data
                self._model_class = model_class
                self._validated = None
            
            def __getattr__(self, name):
                if self._validated is None:
                    self._validated = self._model_class(**self._data)
                return getattr(self._validated, name)
        
        return LazyModel(data, model_class)
```

## Next Steps

1. **[Document Relationships](02_document-relationships.md)** - Modeling related data
2. **[Schema Design](03_schema-design.md)** - Efficient index structures
3. **[Performance Optimization](../06-production-patterns/03_performance-optimization.md)** - Scaling and efficiency

## Additional Resources

- **Pydantic Documentation**: [pydantic-docs.helpmanual.io](https://pydantic-docs.helpmanual.io)
- **FastAPI Validation**: [fastapi.tiangolo.com/tutorial/body](https://fastapi.tiangolo.com/tutorial/body/)
- **Python Type Hints**: [docs.python.org/3/library/typing.html](https://docs.python.org/3/library/typing.html)