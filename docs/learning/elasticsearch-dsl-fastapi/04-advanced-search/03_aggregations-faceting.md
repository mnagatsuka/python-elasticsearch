# Aggregations and Faceting

Comprehensive guide to implementing aggregations and faceted search in FastAPI applications with Elasticsearch-DSL, covering metric aggregations, bucket aggregations, nested aggregations, and real-time analytics patterns.

## Table of Contents
- [Metric and Bucket Aggregations](#metric-and-bucket-aggregations)
- [Nested Aggregations and Pipelines](#nested-aggregations-and-pipelines)
- [Faceted Search Implementation](#faceted-search-implementation)
- [Real-Time Analytics](#real-time-analytics)
- [Performance Optimization](#performance-optimization)
- [Complex Aggregation Scenarios](#complex-aggregation-scenarios)
- [Aggregation Caching](#aggregation-caching)
- [Next Steps](#next-steps)

## Metric and Bucket Aggregations

### Comprehensive Aggregation Builder

```python
from fastapi import FastAPI, Query, HTTPException, Depends
from elasticsearch_dsl import AsyncSearch, A, Q
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from enum import Enum
import asyncio
import time
import logging
from datetime import datetime, timedelta

app = FastAPI()
logger = logging.getLogger(__name__)

class AggregationType(str, Enum):
    # Metric aggregations
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    SUM = "sum"
    COUNT = "value_count"
    CARDINALITY = "cardinality"
    STATS = "stats"
    EXTENDED_STATS = "extended_stats"
    PERCENTILES = "percentiles"
    PERCENTILE_RANKS = "percentile_ranks"
    
    # Bucket aggregations
    TERMS = "terms"
    RANGE = "range"
    DATE_RANGE = "date_range"
    HISTOGRAM = "histogram"
    DATE_HISTOGRAM = "date_histogram"
    FILTERS = "filters"
    NESTED = "nested"
    REVERSE_NESTED = "reverse_nested"

class AggregationConfig(BaseModel):
    name: str = Field(..., description="Aggregation name")
    type: AggregationType = Field(..., description="Aggregation type")
    field: Optional[str] = Field(None, description="Field to aggregate on")
    size: Optional[int] = Field(None, description="Number of buckets/results")
    missing: Optional[Union[str, int, float]] = Field(None, description="Missing value replacement")
    
    # Range aggregation specific
    ranges: Optional[List[Dict[str, Any]]] = Field(None, description="Ranges for range aggregation")
    
    # Histogram specific
    interval: Optional[Union[int, str]] = Field(None, description="Histogram interval")
    
    # Percentiles specific
    percents: Optional[List[float]] = Field(None, description="Percentile values")
    
    # Date histogram specific
    calendar_interval: Optional[str] = Field(None, description="Calendar interval")
    fixed_interval: Optional[str] = Field(None, description="Fixed interval")
    
    # Terms aggregation specific
    min_doc_count: Optional[int] = Field(None, description="Minimum document count")
    shard_min_doc_count: Optional[int] = Field(None, description="Shard minimum document count")
    
    # Sub-aggregations
    sub_aggregations: Optional[List['AggregationConfig']] = Field(None, description="Sub-aggregations")

AggregationConfig.model_rebuild()  # Required for self-referencing model

class AdvancedAggregationBuilder:
    """Build complex aggregations with type safety"""
    
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
        self.aggregations = {}
        self.performance_hints = {}
    
    def add_aggregation(self, config: AggregationConfig) -> 'AdvancedAggregationBuilder':
        """Add aggregation from configuration"""
        agg = self._build_aggregation_from_config(config)
        self.search.aggs.bucket(config.name, agg)
        self.aggregations[config.name] = config
        return self
    
    def _build_aggregation_from_config(self, config: AggregationConfig) -> A:
        """Build Elasticsearch aggregation from config"""
        agg_params = {}
        
        # Add common parameters
        if config.field:
            agg_params['field'] = config.field
        if config.size is not None:
            agg_params['size'] = config.size
        if config.missing is not None:
            agg_params['missing'] = config.missing
        
        # Add type-specific parameters
        if config.type == AggregationType.TERMS:
            if config.min_doc_count is not None:
                agg_params['min_doc_count'] = config.min_doc_count
            if config.shard_min_doc_count is not None:
                agg_params['shard_min_doc_count'] = config.shard_min_doc_count
        
        elif config.type == AggregationType.RANGE:
            if config.ranges:
                agg_params['ranges'] = config.ranges
        
        elif config.type == AggregationType.HISTOGRAM:
            if config.interval:
                agg_params['interval'] = config.interval
        
        elif config.type == AggregationType.DATE_HISTOGRAM:
            if config.calendar_interval:
                agg_params['calendar_interval'] = config.calendar_interval
            elif config.fixed_interval:
                agg_params['fixed_interval'] = config.fixed_interval
        
        elif config.type == AggregationType.PERCENTILES:
            if config.percents:
                agg_params['percents'] = config.percents
        
        # Create the aggregation
        agg = A(config.type.value, **agg_params)
        
        # Add sub-aggregations
        if config.sub_aggregations:
            for sub_agg_config in config.sub_aggregations:
                sub_agg = self._build_aggregation_from_config(sub_agg_config)
                agg.bucket(sub_agg_config.name, sub_agg)
        
        return agg
    
    def add_metric_aggregations(self, field: str, metrics: List[str] = None) -> 'AdvancedAggregationBuilder':
        """Add common metric aggregations for a field"""
        metrics = metrics or ['avg', 'min', 'max', 'sum', 'count']
        
        for metric in metrics:
            if metric == 'count':
                self.search.aggs.metric(f'{field}_{metric}', 'value_count', field=field)
            else:
                self.search.aggs.metric(f'{field}_{metric}', metric, field=field)
        
        return self
    
    def add_price_range_aggregation(self, field: str = 'price') -> 'AdvancedAggregationBuilder':
        """Add common price range aggregation"""
        price_ranges = [
            {'to': 50, 'key': 'budget'},
            {'from': 50, 'to': 200, 'key': 'mid_range'},
            {'from': 200, 'to': 500, 'key': 'premium'},
            {'from': 500, 'key': 'luxury'}
        ]
        
        self.search.aggs.bucket('price_ranges', 'range', field=field, ranges=price_ranges)
        return self
    
    def add_date_trend_aggregation(self, 
                                 field: str = 'created_date',
                                 interval: str = 'month') -> 'AdvancedAggregationBuilder':
        """Add date trend aggregation"""
        self.search.aggs.bucket('date_trend', 'date_histogram', 
                               field=field, 
                               calendar_interval=interval,
                               min_doc_count=1)
        return self
    
    def optimize_for_aggregations(self) -> 'AdvancedAggregationBuilder':
        """Optimize search for aggregation-focused queries"""
        # Don't return hits when only aggregations are needed
        self.search = self.search[:0]
        self.performance_hints['aggregation_only'] = True
        return self
    
    def with_query_filter(self, query: Q) -> 'AdvancedAggregationBuilder':
        """Add query filter before aggregations"""
        self.search = self.search.query(query)
        return self
    
    async def execute_aggregations(self, timeout: str = "30s") -> Dict[str, Any]:
        """Execute aggregations and return structured results"""
        try:
            start_time = time.time()
            
            # Add timeout
            search = self.search.extra(timeout=timeout)
            
            # Execute
            response = await search.execute()
            execution_time = time.time() - start_time
            
            # Process aggregation results
            agg_results = {}
            if hasattr(response, 'aggregations'):
                agg_results = self._process_aggregation_response(response.aggregations.to_dict())
            
            return {
                'aggregations': agg_results,
                'execution_time': execution_time,
                'total_docs': response.hits.total.value if hasattr(response.hits, 'total') else 0,
                'performance_hints': self.performance_hints
            }
            
        except Exception as e:
            logger.error(f"Aggregation execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(e)}")
    
    def _process_aggregation_response(self, agg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure aggregation response"""
        processed = {}
        
        for agg_name, agg_result in agg_data.items():
            if 'buckets' in agg_result:
                # Bucket aggregation
                processed[agg_name] = {
                    'type': 'bucket',
                    'buckets': []
                }
                
                for bucket in agg_result['buckets']:
                    bucket_data = {
                        'key': bucket.get('key'),
                        'doc_count': bucket.get('doc_count', 0)
                    }
                    
                    # Process nested aggregations
                    for key, value in bucket.items():
                        if key not in ['key', 'doc_count'] and isinstance(value, dict):
                            if 'buckets' in value or 'value' in value:
                                bucket_data[key] = self._process_aggregation_response({key: value})[key]
                    
                    processed[agg_name]['buckets'].append(bucket_data)
            
            elif 'value' in agg_result:
                # Metric aggregation
                processed[agg_name] = {
                    'type': 'metric',
                    'value': agg_result['value']
                }
            
            elif 'values' in agg_result:
                # Multi-value metric (like stats)
                processed[agg_name] = {
                    'type': 'multi_metric',
                    'values': agg_result['values']
                }
            
            else:
                # Pass through other formats
                processed[agg_name] = agg_result
        
        return processed

@app.post("/analytics/aggregations")
async def execute_custom_aggregations(aggregation_configs: List[AggregationConfig]):
    """Execute custom aggregations"""
    if len(aggregation_configs) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 aggregations allowed")
    
    builder = AdvancedAggregationBuilder('products')
    
    # Add all aggregations
    for config in aggregation_configs:
        builder.add_aggregation(config)
    
    # Optimize for aggregations only
    builder.optimize_for_aggregations()
    
    result = await builder.execute_aggregations()
    return result

# Example: E-commerce analytics endpoint
@app.get("/analytics/product-insights")
async def product_analytics_insights(
    category: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    include_trends: bool = True,
    include_price_analysis: bool = True
):
    """Comprehensive product analytics"""
    builder = AdvancedAggregationBuilder('products')
    
    # Add query filters
    filters = []
    if category:
        filters.append(Q('term', category=category))
    if date_from or date_to:
        date_range = {}
        if date_from:
            date_range['gte'] = date_from
        if date_to:
            date_range['lte'] = date_to
        filters.append(Q('range', created_date=date_range))
    
    if filters:
        if len(filters) == 1:
            builder.with_query_filter(filters[0])
        else:
            builder.with_query_filter(Q('bool', must=filters))
    
    # Category distribution
    builder.search.aggs.bucket('categories', 'terms', field='category', size=20)
    
    # Brand distribution
    builder.search.aggs.bucket('brands', 'terms', field='brand', size=15)
    
    # Price analysis
    if include_price_analysis:
        builder.add_metric_aggregations('price', ['avg', 'min', 'max', 'stats'])
        builder.add_price_range_aggregation()
        
        # Price by category
        builder.search.aggs.bucket('price_by_category', 'terms', field='category', size=10)\
                           .metric('avg_price', 'avg', field='price')\
                           .metric('max_price', 'max', field='price')
    
    # Rating analysis
    builder.search.aggs.bucket('rating_distribution', 'histogram', 
                              field='rating', interval=1, min_doc_count=1)
    builder.add_metric_aggregations('rating', ['avg', 'stats'])
    
    # Date trends
    if include_trends:
        builder.add_date_trend_aggregation('created_date', 'month')
        
        # Sales trend with revenue
        builder.search.aggs.bucket('monthly_sales', 'date_histogram',
                                  field='created_date', calendar_interval='month')\
                           .metric('total_revenue', 'sum', field='price')\
                           .metric('avg_price', 'avg', field='price')
    
    # In stock analysis
    builder.search.aggs.bucket('stock_status', 'terms', field='in_stock')
    
    # Optimize and execute
    result = await builder.optimize_for_aggregations().execute_aggregations()
    
    return result
```

## Nested Aggregations and Pipelines

### Complex Nested Aggregation Patterns

```python
from elasticsearch_dsl import Document, Nested, Text, Keyword, Float, Integer, Boolean, Date

class ProductWithReviews(Document):
    """Product document with nested reviews for aggregation examples"""
    name = Text(analyzer='standard')
    category = Keyword()
    brand = Keyword()
    price = Float()
    in_stock = Boolean()
    created_date = Date()
    
    # Nested reviews
    reviews = Nested(properties={
        'rating': Integer(),
        'reviewer_name': Text(),
        'review_text': Text(),
        'verified_purchase': Boolean(),
        'review_date': Date(),
        'helpful_votes': Integer()
    })
    
    # Nested variants (for size, color, etc.)
    variants = Nested(properties={
        'sku': Keyword(),
        'size': Keyword(),
        'color': Keyword(),
        'price': Float(),
        'stock_quantity': Integer()
    })
    
    class Index:
        name = 'products_with_nested'

class NestedAggregationBuilder:
    """Builder for nested aggregations and pipeline aggregations"""
    
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
        self.nested_aggs = {}
        self.pipeline_aggs = {}
    
    def add_nested_aggregation(self, 
                             path: str, 
                             name: str,
                             inner_aggs: List[Dict[str, Any]]) -> 'NestedAggregationBuilder':
        """Add nested aggregation with inner aggregations"""
        nested_agg = A('nested', path=path)
        
        # Add inner aggregations
        for inner_agg in inner_aggs:
            agg_name = inner_agg['name']
            agg_type = inner_agg['type']
            agg_params = inner_agg.get('params', {})
            
            if inner_agg.get('is_bucket', False):
                nested_agg.bucket(agg_name, agg_type, **agg_params)
            else:
                nested_agg.metric(agg_name, agg_type, **agg_params)
        
        self.search.aggs.bucket(name, nested_agg)
        self.nested_aggs[name] = {'path': path, 'inner_aggs': inner_aggs}
        return self
    
    def add_reverse_nested_aggregation(self, 
                                     nested_agg_name: str,
                                     reverse_agg_name: str,
                                     parent_aggs: List[Dict[str, Any]]) -> 'NestedAggregationBuilder':
        """Add reverse nested aggregation"""
        # Get the nested aggregation and add reverse nested
        nested_agg = self.search.aggs[nested_agg_name]
        reverse_nested = A('reverse_nested')
        
        # Add parent document aggregations
        for parent_agg in parent_aggs:
            agg_name = parent_agg['name']
            agg_type = parent_agg['type']
            agg_params = parent_agg.get('params', {})
            
            if parent_agg.get('is_bucket', False):
                reverse_nested.bucket(agg_name, agg_type, **agg_params)
            else:
                reverse_nested.metric(agg_name, agg_type, **agg_params)
        
        nested_agg.bucket(reverse_agg_name, reverse_nested)
        return self
    
    def add_pipeline_aggregation(self, 
                                name: str,
                                pipeline_type: str,
                                **params) -> 'NestedAggregationBuilder':
        """Add pipeline aggregation"""
        pipeline_agg = A(pipeline_type, **params)
        self.search.aggs.pipeline(name, pipeline_agg)
        self.pipeline_aggs[name] = {'type': pipeline_type, 'params': params}
        return self
    
    def add_bucket_sort_pipeline(self, 
                               sort_fields: List[Dict[str, str]],
                               size: int = 10,
                               from_: int = 0) -> 'NestedAggregationBuilder':
        """Add bucket sort pipeline aggregation"""
        sort_config = []
        for sort_field in sort_fields:
            sort_config.append({sort_field['field']: {'order': sort_field['order']}})
        
        return self.add_pipeline_aggregation(
            'bucket_sort',
            'bucket_sort',
            sort=sort_config,
            size=size,
            **({'from': from_} if from_ > 0 else {})
        )
    
    def add_moving_average_pipeline(self, 
                                  buckets_path: str,
                                  window: int = 5,
                                  model: str = 'simple') -> 'NestedAggregationBuilder':
        """Add moving average pipeline aggregation"""
        return self.add_pipeline_aggregation(
            'moving_avg',
            'moving_avg',
            buckets_path=buckets_path,
            window=window,
            model=model
        )
    
    def add_derivative_pipeline(self, buckets_path: str) -> 'NestedAggregationBuilder':
        """Add derivative pipeline aggregation"""
        return self.add_pipeline_aggregation(
            'sales_derivative',
            'derivative',
            buckets_path=buckets_path
        )
    
    async def execute_nested_aggregations(self) -> Dict[str, Any]:
        """Execute nested aggregations"""
        try:
            # Optimize for aggregations only
            search = self.search[:0]
            
            response = await search.execute()
            
            return {
                'aggregations': response.aggregations.to_dict(),
                'nested_paths': list(self.nested_aggs.keys()),
                'pipeline_aggs': list(self.pipeline_aggs.keys())
            }
            
        except Exception as e:
            logger.error(f"Nested aggregation execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Nested aggregation failed: {str(e)}")

@app.get("/analytics/reviews-analysis")
async def reviews_analysis(
    min_rating: Optional[int] = None,
    verified_only: bool = False,
    category: Optional[str] = None
):
    """Analyze product reviews with nested aggregations"""
    builder = NestedAggregationBuilder('products_with_nested')
    
    # Add query filters
    query_filters = []
    if category:
        query_filters.append(Q('term', category=category))
    
    # Nested query for reviews
    review_filters = []
    if min_rating:
        review_filters.append(Q('range', reviews__rating={'gte': min_rating}))
    if verified_only:
        review_filters.append(Q('term', reviews__verified_purchase=True))
    
    if review_filters:
        nested_query = Q('nested', 
                        path='reviews',
                        query=Q('bool', must=review_filters))
        query_filters.append(nested_query)
    
    if query_filters:
        if len(query_filters) == 1:
            builder.search = builder.search.query(query_filters[0])
        else:
            builder.search = builder.search.query(Q('bool', must=query_filters))
    
    # Reviews aggregations
    reviews_inner_aggs = [
        {
            'name': 'avg_rating',
            'type': 'avg',
            'params': {'field': 'reviews.rating'},
            'is_bucket': False
        },
        {
            'name': 'rating_distribution',
            'type': 'terms',
            'params': {'field': 'reviews.rating', 'size': 5},
            'is_bucket': True
        },
        {
            'name': 'verified_reviews',
            'type': 'filter',
            'params': {'filter': Q('term', reviews__verified_purchase=True).to_dict()},
            'is_bucket': True
        },
        {
            'name': 'review_timeline',
            'type': 'date_histogram',
            'params': {
                'field': 'reviews.review_date',
                'calendar_interval': 'month',
                'min_doc_count': 1
            },
            'is_bucket': True
        }
    ]
    
    builder.add_nested_aggregation('reviews', 'reviews_analysis', reviews_inner_aggs)
    
    # Add reverse nested to get product-level metrics
    product_level_aggs = [
        {
            'name': 'unique_products',
            'type': 'cardinality',
            'params': {'field': '_id'},
            'is_bucket': False
        },
        {
            'name': 'category_distribution',
            'type': 'terms',
            'params': {'field': 'category', 'size': 10},
            'is_bucket': True
        }
    ]
    
    builder.add_reverse_nested_aggregation(
        'reviews_analysis',
        'product_level',
        product_level_aggs
    )
    
    # Product variants analysis
    variants_inner_aggs = [
        {
            'name': 'avg_variant_price',
            'type': 'avg',
            'params': {'field': 'variants.price'},
            'is_bucket': False
        },
        {
            'name': 'color_distribution',
            'type': 'terms',
            'params': {'field': 'variants.color', 'size': 15},
            'is_bucket': True
        },
        {
            'name': 'size_distribution',
            'type': 'terms',
            'params': {'field': 'variants.size', 'size': 10},
            'is_bucket': True
        },
        {
            'name': 'total_stock',
            'type': 'sum',
            'params': {'field': 'variants.stock_quantity'},
            'is_bucket': False
        }
    ]
    
    builder.add_nested_aggregation('variants', 'variants_analysis', variants_inner_aggs)
    
    result = await builder.execute_nested_aggregations()
    return result

@app.get("/analytics/sales-trends")
async def sales_trends_with_pipelines(
    months_back: int = 12,
    include_moving_average: bool = True,
    include_growth_rate: bool = True
):
    """Sales trends analysis with pipeline aggregations"""
    builder = NestedAggregationBuilder('products_with_nested')
    
    # Date filter for recent months
    date_from = datetime.now() - timedelta(days=months_back * 30)
    builder.search = builder.search.query(
        Q('range', created_date={'gte': date_from})
    )
    
    # Monthly sales aggregation
    builder.search.aggs.bucket('monthly_sales', 'date_histogram',
                              field='created_date',
                              calendar_interval='month',
                              min_doc_count=0)\
                       .metric('total_revenue', 'sum', field='price')\
                       .metric('product_count', 'value_count', field='_id')\
                       .metric('avg_price', 'avg', field='price')
    
    # Add pipeline aggregations
    if include_moving_average:
        # Moving average of revenue
        builder.search.aggs['monthly_sales'].pipeline(
            'revenue_moving_avg',
            'moving_avg',
            buckets_path='total_revenue',
            window=3,
            model='simple'
        )
    
    if include_growth_rate:
        # Revenue growth rate (derivative)
        builder.search.aggs['monthly_sales'].pipeline(
            'revenue_growth',
            'derivative',
            buckets_path='total_revenue'
        )
        
        # Growth rate percentage
        builder.search.aggs['monthly_sales'].pipeline(
            'growth_rate_percent',
            'bucket_script',
            buckets_path={'current': 'revenue_growth', 'previous': 'total_revenue'},
            script='params.current != null && params.previous != 0 ? (params.current / params.previous) * 100 : 0'
        )
    
    # Top categories by revenue with sorting
    builder.search.aggs.bucket('top_categories', 'terms',
                              field='category',
                              size=1000)  # Get all first\
                       .metric('category_revenue', 'sum', field='price')\
                       .pipeline('category_bucket_sort', 'bucket_sort',
                                sort=[{'category_revenue': {'order': 'desc'}}],
                                size=10)
    
    # Cumulative revenue
    builder.search.aggs['monthly_sales'].pipeline(
        'cumulative_revenue',
        'cumulative_sum',
        buckets_path='total_revenue'
    )
    
    result = await builder.execute_nested_aggregations()
    return result
```

## Faceted Search Implementation

### Dynamic Faceted Search System

```python
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel
from enum import Enum

class FacetType(str, Enum):
    TERMS = "terms"
    RANGE = "range"
    DATE_RANGE = "date_range"
    HISTOGRAM = "histogram"
    BOOLEAN = "boolean"

class FacetConfig(BaseModel):
    name: str
    field: str
    type: FacetType
    size: int = 10
    min_doc_count: int = 1
    
    # Range facet specific
    ranges: Optional[List[Dict[str, Any]]] = None
    
    # Histogram specific
    interval: Optional[Union[int, str]] = None
    
    # Display configuration
    display_name: str = None
    display_order: int = 0
    collapsible: bool = False

class FacetedSearchRequest(BaseModel):
    query: Optional[str] = None
    filters: Dict[str, Any] = {}
    facets: List[str] = []  # Which facets to include
    page: int = 1
    size: int = 20
    sort: Optional[List[str]] = None

class FacetedSearchManager:
    """Manage faceted search with dynamic facet configuration"""
    
    def __init__(self, index: str):
        self.index = index
        self.facet_configs = {}
        self.default_facets = []
        self._setup_default_facets()
    
    def _setup_default_facets(self):
        """Setup default facet configurations"""
        default_configs = [
            FacetConfig(
                name='category',
                field='category',
                type=FacetType.TERMS,
                display_name='Category',
                size=15,
                display_order=1
            ),
            FacetConfig(
                name='brand',
                field='brand',
                type=FacetType.TERMS,
                display_name='Brand',
                size=20,
                display_order=2
            ),
            FacetConfig(
                name='price_ranges',
                field='price',
                type=FacetType.RANGE,
                display_name='Price',
                display_order=3,
                ranges=[
                    {'to': 50, 'key': 'Under $50'},
                    {'from': 50, 'to': 100, 'key': '$50 - $100'},
                    {'from': 100, 'to': 250, 'key': '$100 - $250'},
                    {'from': 250, 'to': 500, 'key': '$250 - $500'},
                    {'from': 500, 'key': 'Over $500'}
                ]
            ),
            FacetConfig(
                name='rating',
                field='rating',
                type=FacetType.HISTOGRAM,
                display_name='Rating',
                interval=1,
                display_order=4
            ),
            FacetConfig(
                name='in_stock',
                field='in_stock',
                type=FacetType.BOOLEAN,
                display_name='Availability',
                display_order=5
            ),
            FacetConfig(
                name='created_date',
                field='created_date',
                type=FacetType.DATE_RANGE,
                display_name='Date Added',
                display_order=6,
                ranges=[
                    {'from': 'now-7d', 'key': 'Last 7 days'},
                    {'from': 'now-30d', 'key': 'Last 30 days'},
                    {'from': 'now-90d', 'key': 'Last 3 months'},
                    {'from': 'now-1y', 'key': 'Last year'}
                ]
            )
        ]
        
        for config in default_configs:
            self.facet_configs[config.name] = config
            self.default_facets.append(config.name)
    
    def add_facet_config(self, config: FacetConfig):
        """Add custom facet configuration"""
        self.facet_configs[config.name] = config
    
    def build_faceted_search(self, request: FacetedSearchRequest) -> AsyncSearch:
        """Build search with facets and filters"""
        search = AsyncSearch(index=self.index)
        
        # Build main query
        if request.query:
            search = search.query(
                'multi_match',
                query=request.query,
                fields=['name^3', 'description^2', 'category^1.5'],
                type='best_fields',
                operator='and'
            )
        else:
            search = search.query('match_all')
        
        # Apply filters
        filters = self._build_filters(request.filters)
        if filters:
            current_query = search.to_dict().get('query', {})
            search = search.query('bool', must=[current_query], filter=filters)
        
        # Add facets
        facets_to_include = request.facets or self.default_facets
        for facet_name in facets_to_include:
            if facet_name in self.facet_configs:
                self._add_facet_to_search(search, facet_name, request.filters)
        
        # Apply sorting
        if request.sort:
            search = search.sort(*request.sort)
        else:
            search = search.sort('_score', '-created_date')
        
        # Apply pagination
        start = (request.page - 1) * request.size
        search = search[start:start + request.size]
        
        return search
    
    def _build_filters(self, filters: Dict[str, Any]) -> List[Q]:
        """Build filter queries from filter parameters"""
        filter_queries = []
        
        for filter_name, filter_value in filters.items():
            if filter_name not in self.facet_configs:
                continue
            
            facet_config = self.facet_configs[filter_name]
            
            if facet_config.type == FacetType.TERMS:
                if isinstance(filter_value, list):
                    filter_queries.append(Q('terms', **{facet_config.field: filter_value}))
                else:
                    filter_queries.append(Q('term', **{facet_config.field: filter_value}))
            
            elif facet_config.type == FacetType.RANGE:
                if isinstance(filter_value, dict):
                    filter_queries.append(Q('range', **{facet_config.field: filter_value}))
                elif isinstance(filter_value, list):
                    # Multiple range selections
                    range_queries = []
                    for range_key in filter_value:
                        range_def = self._find_range_definition(facet_config, range_key)
                        if range_def:
                            range_queries.append(Q('range', **{facet_config.field: range_def}))
                    if range_queries:
                        filter_queries.append(Q('bool', should=range_queries))
            
            elif facet_config.type == FacetType.BOOLEAN:
                filter_queries.append(Q('term', **{facet_config.field: filter_value}))
            
            elif facet_config.type == FacetType.DATE_RANGE:
                if isinstance(filter_value, list):
                    date_queries = []
                    for date_key in filter_value:
                        date_def = self._find_date_range_definition(facet_config, date_key)
                        if date_def:
                            date_queries.append(Q('range', **{facet_config.field: date_def}))
                    if date_queries:
                        filter_queries.append(Q('bool', should=date_queries))
        
        return filter_queries
    
    def _find_range_definition(self, facet_config: FacetConfig, range_key: str) -> Optional[Dict[str, Any]]:
        """Find range definition for a given key"""
        if not facet_config.ranges:
            return None
        
        for range_def in facet_config.ranges:
            if range_def.get('key') == range_key:
                return {k: v for k, v in range_def.items() if k != 'key'}
        return None
    
    def _find_date_range_definition(self, facet_config: FacetConfig, date_key: str) -> Optional[Dict[str, Any]]:
        """Find date range definition for a given key"""
        if not facet_config.ranges:
            return None
        
        for range_def in facet_config.ranges:
            if range_def.get('key') == date_key:
                return {k: v for k, v in range_def.items() if k != 'key'}
        return None
    
    def _add_facet_to_search(self, search: AsyncSearch, facet_name: str, current_filters: Dict[str, Any]):
        """Add facet aggregation to search"""
        facet_config = self.facet_configs[facet_name]
        
        # Create post-filter aggregation to show all facet values
        agg_search = search
        
        # Remove current facet filter for this aggregation (to show all options)
        if facet_name in current_filters:
            # Create a copy of filters without this facet
            other_filters = {k: v for k, v in current_filters.items() if k != facet_name}
            if other_filters:
                other_filter_queries = self._build_filters(other_filters)
                if other_filter_queries:
                    main_query = search.to_dict().get('query', {})
                    # Extract the main query without filters
                    if 'bool' in main_query and 'must' in main_query['bool']:
                        main_query = main_query['bool']['must'][0]
                    
                    agg_search = AsyncSearch(index=self.index).query('bool', 
                                                                   must=[main_query], 
                                                                   filter=other_filter_queries)
        
        # Add the appropriate aggregation type
        if facet_config.type == FacetType.TERMS:
            search.aggs.bucket(facet_name, 'terms',
                              field=facet_config.field,
                              size=facet_config.size,
                              min_doc_count=facet_config.min_doc_count)
        
        elif facet_config.type == FacetType.RANGE:
            search.aggs.bucket(facet_name, 'range',
                              field=facet_config.field,
                              ranges=[{k: v for k, v in r.items() if k != 'key'} 
                                     for r in facet_config.ranges])
        
        elif facet_config.type == FacetType.HISTOGRAM:
            search.aggs.bucket(facet_name, 'histogram',
                              field=facet_config.field,
                              interval=facet_config.interval,
                              min_doc_count=facet_config.min_doc_count)
        
        elif facet_config.type == FacetType.BOOLEAN:
            search.aggs.bucket(facet_name, 'terms',
                              field=facet_config.field,
                              size=2)
        
        elif facet_config.type == FacetType.DATE_RANGE:
            search.aggs.bucket(facet_name, 'date_range',
                              field=facet_config.field,
                              ranges=[{k: v for k, v in r.items() if k != 'key'} 
                                     for r in facet_config.ranges])
    
    async def execute_faceted_search(self, request: FacetedSearchRequest) -> Dict[str, Any]:
        """Execute faceted search and return structured results"""
        try:
            search = self.build_faceted_search(request)
            response = await search.execute()
            
            # Process results
            results = {
                'total': response.hits.total.value,
                'page': request.page,
                'size': request.size,
                'query': request.query,
                'filters': request.filters,
                'hits': []
            }
            
            # Add documents
            for hit in response.hits:
                doc = hit.to_dict()
                doc['_id'] = hit.meta.id
                doc['_score'] = hit.meta.score
                results['hits'].append(doc)
            
            # Process facets
            facets = {}
            if hasattr(response, 'aggregations'):
                for facet_name in (request.facets or self.default_facets):
                    if facet_name in self.facet_configs and facet_name in response.aggregations:
                        facets[facet_name] = self._process_facet_response(
                            facet_name, 
                            response.aggregations[facet_name],
                            request.filters.get(facet_name)
                        )
            
            results['facets'] = facets
            
            return results
            
        except Exception as e:
            logger.error(f"Faceted search execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Faceted search failed: {str(e)}")
    
    def _process_facet_response(self, facet_name: str, facet_data: Any, current_filter: Any) -> Dict[str, Any]:
        """Process facet aggregation response"""
        facet_config = self.facet_configs[facet_name]
        current_selections = current_filter if isinstance(current_filter, list) else ([current_filter] if current_filter else [])
        
        facet_result = {
            'display_name': facet_config.display_name or facet_name.replace('_', ' ').title(),
            'type': facet_config.type.value,
            'display_order': facet_config.display_order,
            'collapsible': facet_config.collapsible,
            'values': []
        }
        
        if hasattr(facet_data, 'buckets'):
            for bucket in facet_data.buckets:
                value_key = bucket.key
                
                # For range facets, use the predefined key
                if facet_config.type in [FacetType.RANGE, FacetType.DATE_RANGE]:
                    for range_def in (facet_config.ranges or []):
                        if self._bucket_matches_range(bucket, range_def):
                            value_key = range_def.get('key', bucket.key)
                            break
                
                facet_result['values'].append({
                    'key': value_key,
                    'count': bucket.doc_count,
                    'selected': value_key in current_selections or bucket.key in current_selections
                })
        
        # Sort facet values
        if facet_config.type == FacetType.TERMS:
            facet_result['values'].sort(key=lambda x: x['count'], reverse=True)
        
        return facet_result
    
    def _bucket_matches_range(self, bucket, range_def: Dict[str, Any]) -> bool:
        """Check if bucket matches range definition"""
        # This is a simplified implementation
        # In practice, you'd need more sophisticated matching
        return True

# Global faceted search manager
faceted_search = FacetedSearchManager('products')

@app.post("/search/faceted")
async def faceted_search_endpoint(request: FacetedSearchRequest):
    """Faceted search endpoint"""
    result = await faceted_search.execute_faceted_search(request)
    return result

@app.get("/search/faceted/config")
async def get_facet_configuration():
    """Get available facet configurations"""
    configs = {}
    for name, config in faceted_search.facet_configs.items():
        configs[name] = {
            'display_name': config.display_name or name.replace('_', ' ').title(),
            'type': config.type.value,
            'field': config.field,
            'display_order': config.display_order,
            'size': config.size
        }
    
    return {
        'available_facets': configs,
        'default_facets': faceted_search.default_facets
    }
```

## Real-Time Analytics

### Live Analytics Dashboard Implementation

```python
import asyncio
from datetime import datetime, timedelta
from typing import AsyncIterator
import json

class RealTimeAnalytics:
    """Real-time analytics with live data streaming"""
    
    def __init__(self, index: str):
        self.index = index
        self.active_streams = set()
        self.update_interval = 5  # seconds
    
    async def stream_live_metrics(self, 
                                 metrics: List[str],
                                 update_interval: int = 5) -> AsyncIterator[Dict[str, Any]]:
        """Stream live metrics updates"""
        stream_id = f"stream_{int(time.time())}"
        self.active_streams.add(stream_id)
        
        try:
            while stream_id in self.active_streams:
                # Get current metrics
                current_metrics = await self._calculate_live_metrics(metrics)
                
                yield {
                    'timestamp': datetime.now().isoformat(),
                    'stream_id': stream_id,
                    'metrics': current_metrics
                }
                
                await asyncio.sleep(update_interval)
        
        finally:
            self.active_streams.discard(stream_id)
    
    async def _calculate_live_metrics(self, metrics: List[str]) -> Dict[str, Any]:
        """Calculate current metrics"""
        search = AsyncSearch(index=self.index)
        
        # Time ranges for different metrics
        now = datetime.now()
        time_ranges = {
            'last_hour': now - timedelta(hours=1),
            'last_day': now - timedelta(days=1),
            'last_week': now - timedelta(weeks=1)
        }
        
        results = {}
        
        for metric in metrics:
            if metric == 'total_products':
                search_copy = search.query('match_all')
                response = await search_copy.count()
                results[metric] = response
            
            elif metric == 'recent_additions':
                for period, since_time in time_ranges.items():
                    search_copy = search.query('range', created_date={'gte': since_time})
                    count = await search_copy.count()
                    results[f'{metric}_{period}'] = count
            
            elif metric == 'category_distribution':
                search_copy = search[:0]  # No hits needed
                search_copy.aggs.bucket('categories', 'terms', field='category', size=10)
                response = await search_copy.execute()
                results[metric] = [
                    {'category': bucket.key, 'count': bucket.doc_count}
                    for bucket in response.aggregations.categories.buckets
                ]
            
            elif metric == 'price_stats':
                search_copy = search[:0]
                search_copy.aggs.metric('price_stats', 'stats', field='price')
                response = await search_copy.execute()
                results[metric] = response.aggregations.price_stats.to_dict()
            
            elif metric == 'hourly_trend':
                # Last 24 hours by hour
                since_24h = now - timedelta(hours=24)
                search_copy = search.query('range', created_date={'gte': since_24h})[:0]
                search_copy.aggs.bucket('hourly', 'date_histogram',
                                       field='created_date',
                                       fixed_interval='1h',
                                       min_doc_count=0)
                response = await search_copy.execute()
                results[metric] = [
                    {
                        'hour': bucket.key_as_string,
                        'count': bucket.doc_count
                    }
                    for bucket in response.aggregations.hourly.buckets
                ]
        
        return results
    
    async def get_dashboard_snapshot(self) -> Dict[str, Any]:
        """Get complete dashboard snapshot"""
        search = AsyncSearch(index=self.index)
        
        # Get comprehensive metrics in parallel
        tasks = {
            'total_count': self._get_total_count(search),
            'category_stats': self._get_category_stats(search),
            'price_analysis': self._get_price_analysis(search),
            'recent_trends': self._get_recent_trends(search),
            'top_products': self._get_top_products(search),
            'inventory_status': self._get_inventory_status(search)
        }
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Combine results
        dashboard_data = {}
        for i, (key, _) in enumerate(tasks.items()):
            if isinstance(results[i], Exception):
                dashboard_data[key] = {'error': str(results[i])}
            else:
                dashboard_data[key] = results[i]
        
        dashboard_data['generated_at'] = datetime.now().isoformat()
        
        return dashboard_data
    
    async def _get_total_count(self, search: AsyncSearch) -> int:
        """Get total product count"""
        return await search.query('match_all').count()
    
    async def _get_category_stats(self, search: AsyncSearch) -> Dict[str, Any]:
        """Get category statistics"""
        search_copy = search[:0]
        search_copy.aggs.bucket('categories', 'terms', field='category', size=20)\
                         .metric('avg_price', 'avg', field='price')\
                         .metric('total_value', 'sum', field='price')
        
        response = await search_copy.execute()
        
        return {
            'categories': [
                {
                    'name': bucket.key,
                    'count': bucket.doc_count,
                    'avg_price': bucket.avg_price.value,
                    'total_value': bucket.total_value.value
                }
                for bucket in response.aggregations.categories.buckets
            ]
        }
    
    async def _get_price_analysis(self, search: AsyncSearch) -> Dict[str, Any]:
        """Get price analysis"""
        search_copy = search[:0]
        search_copy.aggs.metric('price_stats', 'extended_stats', field='price')
        search_copy.aggs.bucket('price_ranges', 'range', 
                               field='price',
                               ranges=[
                                   {'to': 50},
                                   {'from': 50, 'to': 200},
                                   {'from': 200, 'to': 500},
                                   {'from': 500}
                               ])
        
        response = await search_copy.execute()
        
        return {
            'stats': response.aggregations.price_stats.to_dict(),
            'ranges': [
                {
                    'range': f"{bucket.get('from', 0)}-{bucket.get('to', 'unlimited')}",
                    'count': bucket.doc_count
                }
                for bucket in response.aggregations.price_ranges.buckets
            ]
        }
    
    async def _get_recent_trends(self, search: AsyncSearch) -> Dict[str, Any]:
        """Get recent addition trends"""
        now = datetime.now()
        last_30_days = now - timedelta(days=30)
        
        search_copy = search.query('range', created_date={'gte': last_30_days})[:0]
        search_copy.aggs.bucket('daily_trend', 'date_histogram',
                               field='created_date',
                               calendar_interval='day',
                               min_doc_count=0)
        
        response = await search_copy.execute()
        
        return {
            'daily_additions': [
                {
                    'date': bucket.key_as_string,
                    'count': bucket.doc_count
                }
                for bucket in response.aggregations.daily_trend.buckets
            ]
        }
    
    async def _get_top_products(self, search: AsyncSearch) -> Dict[str, Any]:
        """Get top products by various metrics"""
        # Top by price
        search_price = search.sort('-price')[:5]
        response_price = await search_price.execute()
        
        # Top by rating
        search_rating = search.sort('-rating')[:5]
        response_rating = await search_rating.execute()
        
        return {
            'by_price': [
                {
                    'id': hit.meta.id,
                    'name': hit.name,
                    'price': hit.price
                }
                for hit in response_price.hits
            ],
            'by_rating': [
                {
                    'id': hit.meta.id,
                    'name': hit.name,
                    'rating': getattr(hit, 'rating', None)
                }
                for hit in response_rating.hits
            ]
        }
    
    async def _get_inventory_status(self, search: AsyncSearch) -> Dict[str, Any]:
        """Get inventory status overview"""
        search_copy = search[:0]
        search_copy.aggs.bucket('stock_status', 'terms', field='in_stock')
        search_copy.aggs.bucket('low_stock', 'range', 
                               field='stock_quantity',
                               ranges=[
                                   {'to': 10, 'key': 'low'},
                                   {'from': 10, 'to': 50, 'key': 'medium'},
                                   {'from': 50, 'key': 'high'}
                               ])
        
        response = await search_copy.execute()
        
        return {
            'in_stock_distribution': [
                {
                    'status': 'in_stock' if bucket.key else 'out_of_stock',
                    'count': bucket.doc_count
                }
                for bucket in response.aggregations.stock_status.buckets
            ],
            'stock_levels': [
                {
                    'level': bucket.key,
                    'count': bucket.doc_count
                }
                for bucket in response.aggregations.low_stock.buckets
            ]
        }

# Global analytics instance
analytics = RealTimeAnalytics('products')

@app.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get complete analytics dashboard"""
    return await analytics.get_dashboard_snapshot()

@app.get("/analytics/live-stream")
async def live_analytics_stream(
    metrics: List[str] = Query(['total_products', 'category_distribution', 'hourly_trend']),
    update_interval: int = 5
):
    """Stream live analytics data"""
    from fastapi.responses import StreamingResponse
    
    async def generate():
        async for data in analytics.stream_live_metrics(metrics, update_interval):
            yield f"data: {json.dumps(data)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@app.delete("/analytics/stream/{stream_id}")
async def stop_analytics_stream(stream_id: str):
    """Stop a specific analytics stream"""
    analytics.active_streams.discard(stream_id)
    return {"message": f"Stream {stream_id} stopped"}
```

## Performance Optimization

### Aggregation Performance Tuning

```python
class AggregationPerformanceOptimizer:
    """Optimize aggregation performance"""
    
    def __init__(self):
        self.optimization_rules = {}
        self.performance_cache = {}
    
    def add_optimization_rule(self, rule_name: str, rule_func: Callable):
        """Add performance optimization rule"""
        self.optimization_rules[rule_name] = rule_func
    
    def optimize_aggregation_query(self, search: AsyncSearch, agg_config: Dict[str, Any]) -> AsyncSearch:
        """Apply optimization rules to aggregation query"""
        # Rule 1: Reduce precision for large datasets
        if 'size_hint' in agg_config and agg_config['size_hint'] > 100000:
            search = search.extra(
                batched_reduce_size=512,
                pre_filter_shard_size=128
            )
        
        # Rule 2: Use global ordinals for terms aggregations
        for agg_name, agg_def in agg_config.get('aggregations', {}).items():
            if agg_def.get('type') == 'terms':
                # Enable global ordinals optimization
                search.aggs[agg_name] = search.aggs[agg_name].extra(
                    execution_hint='global_ordinals'
                )
        
        # Rule 3: Optimize for aggregation-only queries
        if agg_config.get('aggregation_only', False):
            search = search[:0]  # No hits needed
            search = search.extra(track_total_hits=False)
        
        # Rule 4: Add early termination for sampling
        if agg_config.get('sampling', False):
            search = search.extra(terminate_after=10000)
        
        return search
    
    async def profile_aggregation_performance(self, 
                                            search: AsyncSearch,
                                            agg_name: str) -> Dict[str, Any]:
        """Profile aggregation performance"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        # Execute with profiling
        search_with_profile = search.extra(profile=True)
        response = await search_with_profile.execute()
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        
        # Extract profiling information
        profile_data = {
            'execution_time': end_time - start_time,
            'memory_used': end_memory - start_memory,
            'took_ms': response.took
        }
        
        # Add Elasticsearch profiling data if available
        if hasattr(response, 'profile'):
            profile_data['elasticsearch_profile'] = response.profile
        
        # Store for future optimization
        self.performance_cache[agg_name] = profile_data
        
        return profile_data

# Performance monitoring for aggregations
aggregation_optimizer = AggregationPerformanceOptimizer()

@app.get("/analytics/performance-optimized")
async def performance_optimized_analytics(
    enable_sampling: bool = False,
    max_buckets: int = 1000,
    timeout: str = "30s"
):
    """Analytics with performance optimizations"""
    search = AsyncSearch(index='products')
    
    # Optimization configuration
    agg_config = {
        'aggregation_only': True,
        'sampling': enable_sampling,
        'size_hint': 100000,
        'aggregations': {
            'categories': {'type': 'terms'},
            'brands': {'type': 'terms'},
            'price_ranges': {'type': 'range'}
        }
    }
    
    # Apply optimizations
    search = aggregation_optimizer.optimize_aggregation_query(search, agg_config)
    
    # Add aggregations with limits
    search.aggs.bucket('categories', 'terms', 
                      field='category', 
                      size=min(max_buckets, 50),
                      execution_hint='global_ordinals')
    
    search.aggs.bucket('brands', 'terms', 
                      field='brand', 
                      size=min(max_buckets, 30),
                      execution_hint='global_ordinals')
    
    search.aggs.bucket('price_ranges', 'range',
                      field='price',
                      ranges=[
                          {'to': 100},
                          {'from': 100, 'to': 500},
                          {'from': 500}
                      ])
    
    # Add timeout
    search = search.extra(timeout=timeout)
    
    # Profile performance
    profile_data = await aggregation_optimizer.profile_aggregation_performance(
        search, 
        'optimized_analytics'
    )
    
    # Execute
    response = await search.execute()
    
    return {
        'aggregations': response.aggregations.to_dict(),
        'performance': profile_data,
        'optimizations_applied': agg_config
    }
```

## Complex Aggregation Scenarios

### E-commerce Business Intelligence

```python
class EcommerceBusinessIntelligence:
    """Advanced e-commerce analytics with complex aggregations"""
    
    def __init__(self, index: str):
        self.index = index
    
    async def get_customer_segmentation_analysis(self) -> Dict[str, Any]:
        """Customer segmentation based on purchase behavior"""
        search = AsyncSearch(index='orders')  # Assuming orders index
        
        # RFM Analysis (Recency, Frequency, Monetary)
        search.aggs.bucket('customer_segments', 'terms', field='customer_id', size=10000)\
                   .metric('total_spent', 'sum', field='total_amount')\
                   .metric('order_count', 'value_count', field='order_id')\
                   .metric('last_order', 'max', field='order_date')\
                   .metric('avg_order_value', 'avg', field='total_amount')\
                   .pipeline('recency_days', 'bucket_script',
                            buckets_path={'last_order': 'last_order'},
                            script='(System.currentTimeMillis() - params.last_order) / (1000 * 60 * 60 * 24)')
        
        # Segment customers by value
        search.aggs.bucket('value_segments', 'range',
                          script={'source': 'doc["total_amount"].value'},
                          ranges=[
                              {'to': 100, 'key': 'low_value'},
                              {'from': 100, 'to': 500, 'key': 'medium_value'},
                              {'from': 500, 'to': 1000, 'key': 'high_value'},
                              {'from': 1000, 'key': 'vip'}
                          ])
        
        response = await search[:0].execute()
        return response.aggregations.to_dict()
    
    async def get_product_performance_matrix(self) -> Dict[str, Any]:
        """Product performance analysis matrix"""
        search = AsyncSearch(index=self.index)
        
        # Performance matrix: Sales volume vs Profit margin
        search.aggs.bucket('category_performance', 'terms', field='category', size=20)\
                   .metric('total_sales', 'sum', field='sales_count')\
                   .metric('avg_profit_margin', 'avg', field='profit_margin')\
                   .metric('total_revenue', 'sum', field='revenue')\
                   .bucket('price_tiers', 'range',
                          field='price',
                          ranges=[
                              {'to': 50, 'key': 'budget'},
                              {'from': 50, 'to': 200, 'key': 'mid'},
                              {'from': 200, 'key': 'premium'}
                          ])\
                   .metric('tier_sales', 'sum', field='sales_count')\
                   .metric('tier_profit', 'avg', field='profit_margin')
        
        # Product lifecycle analysis
        search.aggs.bucket('lifecycle_stages', 'date_histogram',
                          field='created_date',
                          calendar_interval='month')\
                   .bucket('performance_by_age', 'range',
                          script={'source': 'System.currentTimeMillis() - doc["created_date"].value.millis'},
                          ranges=[
                              {'to': 2592000000, 'key': 'new'},  # 30 days
                              {'from': 2592000000, 'to': 7776000000, 'key': 'growing'},  # 30-90 days
                              {'from': 7776000000, 'to': 31536000000, 'key': 'mature'},  # 90 days - 1 year
                              {'from': 31536000000, 'key': 'declining'}  # > 1 year
                          ])\
                   .metric('stage_revenue', 'sum', field='revenue')
        
        response = await search[:0].execute()
        return response.aggregations.to_dict()
    
    async def get_seasonal_trend_analysis(self, years_back: int = 2) -> Dict[str, Any]:
        """Seasonal trend analysis with year-over-year comparison"""
        search = AsyncSearch(index=self.index)
        
        # Date range for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years_back * 365)
        
        search = search.query('range', created_date={'gte': start_date, 'lte': end_date})
        
        # Monthly trends with year comparison
        search.aggs.bucket('monthly_trends', 'date_histogram',
                          field='created_date',
                          calendar_interval='month')\
                   .metric('monthly_sales', 'sum', field='sales_count')\
                   .metric('monthly_revenue', 'sum', field='revenue')\
                   .bucket('categories_monthly', 'terms', field='category', size=10)\
                   .metric('category_sales', 'sum', field='sales_count')
        
        # Seasonal patterns
        search.aggs.bucket('quarterly_patterns', 'date_histogram',
                          field='created_date',
                          calendar_interval='quarter')\
                   .metric('quarterly_revenue', 'sum', field='revenue')\
                   .pipeline('revenue_change', 'derivative', buckets_path='quarterly_revenue')
        
        # Day of week patterns
        search.aggs.bucket('day_of_week', 'terms',
                          script={'source': 'doc["created_date"].value.dayOfWeek'},
                          size=7)\
                   .metric('daily_avg_sales', 'avg', field='sales_count')
        
        # Holiday impact analysis
        search.aggs.bucket('monthly_with_holidays', 'date_histogram',
                          field='created_date',
                          calendar_interval='month')\
                   .bucket('holiday_boost', 'filter',
                          filter=Q('terms', created_date=[
                              '2023-11-01', '2023-12-01',  # Holiday season
                              '2024-11-01', '2024-12-01'
                          ]).to_dict())\
                   .metric('holiday_sales', 'sum', field='sales_count')
        
        response = await search[:0].execute()
        return response.aggregations.to_dict()
    
    async def get_inventory_optimization_insights(self) -> Dict[str, Any]:
        """Inventory optimization insights"""
        search = AsyncSearch(index=self.index)
        
        # Stock velocity analysis
        search.aggs.bucket('velocity_analysis', 'terms', field='category', size=20)\
                   .metric('avg_stock_days', 'avg', 
                          script={'source': 'doc["stock_quantity"].value / Math.max(doc["sales_velocity"].value, 1)'})\
                   .metric('total_stock_value', 'sum',
                          script={'source': 'doc["stock_quantity"].value * doc["price"].value'})\
                   .bucket('velocity_segments', 'range',
                          script={'source': 'doc["sales_velocity"].value'},
                          ranges=[
                              {'to': 1, 'key': 'slow_moving'},
                              {'from': 1, 'to': 10, 'key': 'normal'},
                              {'from': 10, 'key': 'fast_moving'}
                          ])\
                   .metric('segment_stock_value', 'sum',
                          script={'source': 'doc["stock_quantity"].value * doc["price"].value'})
        
        # Demand forecasting aggregations
        search.aggs.bucket('demand_forecast', 'date_histogram',
                          field='created_date',
                          calendar_interval='week')\
                   .metric('weekly_demand', 'sum', field='sales_count')\
                   .pipeline('demand_trend', 'moving_avg',
                            buckets_path='weekly_demand',
                            window=4)\
                   .pipeline('demand_growth', 'derivative',
                            buckets_path='demand_trend')
        
        # ABC Analysis (by revenue contribution)
        search.aggs.bucket('abc_analysis', 'terms', field='product_id', size=10000)\
                   .metric('product_revenue', 'sum', field='revenue')\
                   .pipeline('revenue_percentile', 'percentiles_bucket',
                            buckets_path='product_revenue',
                            percents=[80, 95])
        
        response = await search[:0].execute()
        return response.aggregations.to_dict()

# Global BI instance
ecommerce_bi = EcommerceBusinessIntelligence('products')

@app.get("/analytics/business-intelligence")
async def get_business_intelligence_dashboard():
    """Complete business intelligence dashboard"""
    tasks = {
        'customer_segmentation': ecommerce_bi.get_customer_segmentation_analysis(),
        'product_performance': ecommerce_bi.get_product_performance_matrix(),
        'seasonal_trends': ecommerce_bi.get_seasonal_trend_analysis(),
        'inventory_insights': ecommerce_bi.get_inventory_optimization_insights()
    }
    
    results = {}
    for name, task in tasks.items():
        try:
            results[name] = await task
        except Exception as e:
            results[name] = {'error': str(e)}
    
    results['generated_at'] = datetime.now().isoformat()
    return results
```

## Aggregation Caching

### Intelligent Aggregation Caching

```python
class AggregationCache:
    """Intelligent caching for aggregation results"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_configs = {}
        self.default_ttl = 3600  # 1 hour
    
    def configure_cache(self, agg_name: str, ttl: int, invalidation_triggers: List[str] = None):
        """Configure caching for specific aggregation"""
        self.cache_configs[agg_name] = {
            'ttl': ttl,
            'invalidation_triggers': invalidation_triggers or []
        }
    
    def _generate_cache_key(self, agg_name: str, query_hash: str, filters: Dict[str, Any]) -> str:
        """Generate cache key for aggregation"""
        filter_hash = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
        return f"agg:{agg_name}:{query_hash}:{filter_hash}"
    
    async def get_cached_aggregation(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached aggregation result"""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    async def cache_aggregation(self, cache_key: str, result: Dict[str, Any], ttl: int = None):
        """Cache aggregation result"""
        try:
            ttl = ttl or self.default_ttl
            await self.redis.setex(cache_key, ttl, json.dumps(result))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    async def invalidate_aggregation_cache(self, pattern: str):
        """Invalidate cached aggregations matching pattern"""
        try:
            keys = await self.redis.keys(f"agg:*{pattern}*")
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")

# Integration with smart caching
class CachedAggregationBuilder(AdvancedAggregationBuilder):
    """Aggregation builder with intelligent caching"""
    
    def __init__(self, index: str, cache: AggregationCache):
        super().__init__(index)
        self.cache = cache
        self.cache_enabled = True
    
    async def execute_with_cache(self, agg_name: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute aggregations with caching"""
        filters = filters or {}
        
        if not self.cache_enabled:
            return await self.execute_aggregations()
        
        # Generate cache key
        query_dict = self.search.to_dict()
        query_hash = hashlib.md5(json.dumps(query_dict, sort_keys=True).encode()).hexdigest()
        cache_key = self.cache._generate_cache_key(agg_name, query_hash, filters)
        
        # Try cache first
        cached_result = await self.cache.get_cached_aggregation(cache_key)
        if cached_result:
            cached_result['cache_hit'] = True
            return cached_result
        
        # Execute aggregation
        result = await self.execute_aggregations()
        
        # Cache result
        cache_config = self.cache.cache_configs.get(agg_name, {})
        ttl = cache_config.get('ttl', self.cache.default_ttl)
        
        result['cache_hit'] = False
        await self.cache.cache_aggregation(cache_key, result, ttl)
        
        return result

@app.get("/analytics/cached-insights")
async def cached_analytics_insights(
    category: Optional[str] = None,
    use_cache: bool = True
):
    """Analytics with intelligent caching"""
    # Setup cache configurations
    agg_cache = AggregationCache(redis_client)  # Assume redis_client exists
    agg_cache.configure_cache('product_insights', ttl=1800)  # 30 minutes
    
    builder = CachedAggregationBuilder('products', agg_cache)
    builder.cache_enabled = use_cache
    
    # Build aggregations
    if category:
        builder.search = builder.search.query('term', category=category)
    
    builder.search.aggs.bucket('categories', 'terms', field='category', size=20)
    builder.search.aggs.bucket('price_stats', 'stats', field='price')
    builder.search.aggs.bucket('brands', 'terms', field='brand', size=15)
    
    builder.optimize_for_aggregations()
    
    # Execute with caching
    result = await builder.execute_with_cache('product_insights', {'category': category})
    
    return result
```

## Next Steps

1. **[Geospatial and Vector Search](04_geospatial-vector-search.md)** - Implement location and semantic search
2. **[Data Modeling](../05-data-modeling/01_document-design.md)** - Design efficient document structures
3. **[Production Patterns](../06-production-patterns/01_monitoring-logging.md)** - Production-ready patterns
4. **[Testing and Deployment](../07-testing-deployment/01_testing-strategies.md)** - Testing strategies
5. **[Performance Optimization](02_async-search-performance.md)** - Advanced performance patterns

## Additional Resources

- **Elasticsearch Aggregations**: [elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations.html)
- **Pipeline Aggregations**: [elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-pipeline.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-pipeline.html)
- **Performance Tuning**: [elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-search-speed.html)
- **Redis Caching**: [redis.io/docs/](https://redis.io/docs/)
- **Real-time Analytics**: [elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-datehistogram-aggregation.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-datehistogram-aggregation.html)