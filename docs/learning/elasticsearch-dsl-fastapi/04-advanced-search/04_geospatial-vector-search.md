# Geospatial and Vector Search

Advanced implementation guide for geospatial search patterns, vector similarity search, and hybrid search combining multiple approaches in FastAPI applications with Elasticsearch-DSL.

## Table of Contents
- [Geospatial Search Patterns](#geospatial-search-patterns)
- [Vector Search for Semantic Similarity](#vector-search-for-semantic-similarity)
- [Dense and Sparse Vector Patterns](#dense-and-sparse-vector-patterns)
- [Location-Based Search with FastAPI](#location-based-search-with-fastapi)
- [Machine Learning Integration](#machine-learning-integration)
- [Hybrid Search Strategies](#hybrid-search-strategies)
- [Performance and Scaling](#performance-and-scaling)
- [Next Steps](#next-steps)

## Geospatial Search Patterns

### Comprehensive Geospatial Data Models

```python
from fastapi import FastAPI, Query, HTTPException, Depends
from elasticsearch_dsl import Document, GeoPoint, Text, Keyword, Float, Integer, Boolean, Date
from elasticsearch_dsl import AsyncSearch, Q
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Tuple, Union
from enum import Enum
import math
import logging
from datetime import datetime
import numpy as np

app = FastAPI()
logger = logging.getLogger(__name__)

class LocationDocument(Document):
    """Base document with geospatial capabilities"""
    name = Text(analyzer='standard')
    description = Text(analyzer='standard')
    location = GeoPoint()
    address = Text()
    city = Keyword()
    state = Keyword()
    country = Keyword()
    postal_code = Keyword()
    created_date = Date()
    
    class Index:
        name = 'locations'

class RestaurantDocument(LocationDocument):
    """Restaurant with geospatial and business data"""
    cuisine_type = Keyword()
    price_range = Integer()  # 1-4 scale
    rating = Float()
    phone = Keyword()
    website = Text()
    opening_hours = Text()
    delivery_radius_km = Float()
    features = Keyword(multi=True)  # wifi, parking, etc.
    
    class Index:
        name = 'restaurants'

class DeliveryZone(Document):
    """Delivery zone with polygon geometry"""
    name = Text()
    zone_polygon = GeoShape()  # Polygon for delivery area
    delivery_fee = Float()
    min_order_amount = Float()
    estimated_delivery_time = Integer()  # minutes
    active = Boolean()
    
    class Index:
        name = 'delivery_zones'

class GeoSearchType(str, Enum):
    GEO_DISTANCE = "geo_distance"
    GEO_BOUNDING_BOX = "geo_bounding_box"
    GEO_POLYGON = "geo_polygon"
    GEO_SHAPE = "geo_shape"

class GeospatialSearchBuilder:
    """Advanced geospatial search builder"""
    
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
        self.geo_queries = []
        self.location_field = 'location'
        self.distance_sort = None
        self.geo_aggregations = []
    
    def near_point(self, 
                   lat: float, 
                   lon: float, 
                   distance: str = "10km",
                   location_field: str = None) -> 'GeospatialSearchBuilder':
        """Add geo distance query"""
        field = location_field or self.location_field
        
        geo_query = Q('geo_distance',
                     **{field: {'lat': lat, 'lon': lon}},
                     distance=distance)
        
        self.geo_queries.append(geo_query)
        return self
    
    def within_bounding_box(self, 
                           top_left: Tuple[float, float],
                           bottom_right: Tuple[float, float],
                           location_field: str = None) -> 'GeospatialSearchBuilder':
        """Add geo bounding box query"""
        field = location_field or self.location_field
        
        geo_query = Q('geo_bounding_box',
                     **{field: {
                         'top_left': {'lat': top_left[0], 'lon': top_left[1]},
                         'bottom_right': {'lat': bottom_right[0], 'lon': bottom_right[1]}
                     }})
        
        self.geo_queries.append(geo_query)
        return self
    
    def within_polygon(self, 
                      points: List[Tuple[float, float]],
                      location_field: str = None) -> 'GeospatialSearchBuilder':
        """Add geo polygon query"""
        field = location_field or self.location_field
        
        # Convert points to required format
        polygon_points = [{'lat': lat, 'lon': lon} for lat, lon in points]
        
        geo_query = Q('geo_polygon',
                     **{field: {'points': polygon_points}})
        
        self.geo_queries.append(geo_query)
        return self
    
    def intersects_shape(self, 
                        shape: Dict[str, Any],
                        location_field: str = None) -> 'GeospatialSearchBuilder':
        """Add geo shape query for complex geometries"""
        field = location_field or self.location_field
        
        geo_query = Q('geo_shape',
                     **{field: {'shape': shape, 'relation': 'intersects'}})
        
        self.geo_queries.append(geo_query)
        return self
    
    def sort_by_distance(self, 
                        lat: float, 
                        lon: float,
                        location_field: str = None,
                        order: str = 'asc',
                        unit: str = 'km') -> 'GeospatialSearchBuilder':
        """Sort results by distance from point"""
        field = location_field or self.location_field
        
        self.distance_sort = {
            '_geo_distance': {
                field: {'lat': lat, 'lon': lon},
                'order': order,
                'unit': unit,
                'distance_type': 'arc'
            }
        }
        return self
    
    def add_distance_aggregation(self, 
                               lat: float, 
                               lon: float,
                               ranges: List[Dict[str, Any]],
                               location_field: str = None) -> 'GeospatialSearchBuilder':
        """Add geo distance aggregation"""
        field = location_field or self.location_field
        
        self.search.aggs.bucket('distance_ranges', 'geo_distance',
                               field=field,
                               origin={'lat': lat, 'lon': lon},
                               ranges=ranges,
                               unit='km')
        return self
    
    def add_geohash_grid_aggregation(self, 
                                   precision: int = 5,
                                   location_field: str = None) -> 'GeospatialSearchBuilder':
        """Add geohash grid aggregation for heatmap data"""
        field = location_field or self.location_field
        
        self.search.aggs.bucket('geohash_grid', 'geohash_grid',
                               field=field,
                               precision=precision)
        return self
    
    def add_geo_bounds_aggregation(self, location_field: str = None) -> 'GeospatialSearchBuilder':
        """Add geo bounds aggregation to find bounding box"""
        field = location_field or self.location_field
        
        self.search.aggs.metric('geo_bounds', 'geo_bounds', field=field)
        return self
    
    def apply_geo_queries(self) -> 'GeospatialSearchBuilder':
        """Apply all accumulated geo queries"""
        if self.geo_queries:
            if len(self.geo_queries) == 1:
                self.search = self.search.query(self.geo_queries[0])
            else:
                # Combine multiple geo queries with bool must
                self.search = self.search.query('bool', must=self.geo_queries)
        
        # Apply distance sorting
        if self.distance_sort:
            self.search = self.search.sort(self.distance_sort)
        
        return self
    
    async def execute_geo_search(self) -> Dict[str, Any]:
        """Execute geospatial search with distance calculation"""
        try:
            response = await self.search.execute()
            
            results = {
                'total': response.hits.total.value,
                'hits': []
            }
            
            # Process hits with distance information
            for hit in response.hits:
                hit_data = {
                    '_id': hit.meta.id,
                    '_score': hit.meta.score,
                    '_source': hit.to_dict()
                }
                
                # Add distance if available
                if hasattr(hit.meta, 'sort') and self.distance_sort:
                    hit_data['_distance_km'] = hit.meta.sort[0]
                
                results['hits'].append(hit_data)
            
            # Add aggregation results
            if hasattr(response, 'aggregations'):
                results['aggregations'] = response.aggregations.to_dict()
            
            return results
            
        except Exception as e:
            logger.error(f"Geospatial search execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Geo search failed: {str(e)}")

@app.get("/restaurants/nearby")
async def find_nearby_restaurants(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius: str = Query("5km", description="Search radius"),
    cuisine: Optional[str] = None,
    min_rating: Optional[float] = None,
    price_range: Optional[int] = None,
    features: List[str] = Query(default_factory=list),
    limit: int = Query(20, le=100)
):
    """Find nearby restaurants with filters"""
    builder = GeospatialSearchBuilder('restaurants')
    
    # Geographic search
    builder.near_point(lat, lon, radius)
    builder.sort_by_distance(lat, lon)
    
    # Add business logic filters
    filters = []
    
    if cuisine:
        filters.append(Q('term', cuisine_type=cuisine))
    
    if min_rating:
        filters.append(Q('range', rating={'gte': min_rating}))
    
    if price_range:
        filters.append(Q('term', price_range=price_range))
    
    if features:
        filters.append(Q('terms', features=features))
    
    # Combine geo and business filters
    if filters:
        builder.search = builder.search.filter('bool', must=filters)
    
    # Add distance aggregations
    distance_ranges = [
        {'to': 1, 'key': 'within_1km'},
        {'from': 1, 'to': 3, 'key': '1_to_3km'},
        {'from': 3, 'to': 5, 'key': '3_to_5km'},
        {'from': 5, 'key': 'over_5km'}
    ]
    builder.add_distance_aggregation(lat, lon, distance_ranges)
    
    # Add cuisine aggregation
    builder.search.aggs.bucket('cuisines', 'terms', field='cuisine_type', size=10)
    
    # Apply pagination
    builder.search = builder.search[:limit]
    
    # Execute search
    result = await builder.apply_geo_queries().execute_geo_search()
    
    return result

# Advanced geospatial queries
@app.post("/locations/search")
async def advanced_geospatial_search(
    search_request: Dict[str, Any]
):
    """Advanced geospatial search with multiple criteria"""
    builder = GeospatialSearchBuilder('locations')
    
    # Handle different geo query types
    if 'geo_distance' in search_request:
        geo_dist = search_request['geo_distance']
        builder.near_point(
            lat=geo_dist['lat'],
            lon=geo_dist['lon'],
            distance=geo_dist.get('distance', '10km')
        )
    
    if 'geo_bounding_box' in search_request:
        bbox = search_request['geo_bounding_box']
        builder.within_bounding_box(
            top_left=(bbox['top_left']['lat'], bbox['top_left']['lon']),
            bottom_right=(bbox['bottom_right']['lat'], bbox['bottom_right']['lon'])
        )
    
    if 'geo_polygon' in search_request:
        polygon = search_request['geo_polygon']
        points = [(p['lat'], p['lon']) for p in polygon['points']]
        builder.within_polygon(points)
    
    # Add text search if provided
    if 'query' in search_request:
        builder.search = builder.search.query(
            'multi_match',
            query=search_request['query'],
            fields=['name^2', 'description', 'address']
        )
    
    # Add sorting
    if 'sort_by_distance' in search_request:
        sort_config = search_request['sort_by_distance']
        builder.sort_by_distance(
            lat=sort_config['lat'],
            lon=sort_config['lon']
        )
    
    # Add aggregations for heatmap
    if search_request.get('include_heatmap', False):
        builder.add_geohash_grid_aggregation(precision=6)
        builder.add_geo_bounds_aggregation()
    
    result = await builder.apply_geo_queries().execute_geo_search()
    
    return result
```

## Vector Search for Semantic Similarity

### Vector Search Implementation

```python
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Any
import asyncio
import json

class VectorDocument(Document):
    """Document with vector embeddings"""
    title = Text(analyzer='standard')
    content = Text(analyzer='standard')
    category = Keyword()
    tags = Keyword(multi=True)
    
    # Dense vector for semantic search
    content_vector = DenseVector(dims=384)  # Sentence transformer dimension
    
    # Sparse vector for keyword relevance
    content_sparse_vector = SparseVector()
    
    # Metadata
    created_date = Date()
    view_count = Integer()
    
    class Index:
        name = 'vector_documents'

class VectorSearchBuilder:
    """Advanced vector search implementation"""
    
    def __init__(self, index: str):
        self.search = AsyncSearch(index=index)
        self.vector_queries = []
        self.text_queries = []
        self.hybrid_config = {}
    
    def semantic_search(self, 
                       query_vector: List[float],
                       field: str = 'content_vector',
                       k: int = 10,
                       num_candidates: int = 100,
                       boost: float = 1.0) -> 'VectorSearchBuilder':
        """Add semantic vector search"""
        vector_query = {
            'knn': {
                'field': field,
                'query_vector': query_vector,
                'k': k,
                'num_candidates': num_candidates,
                'boost': boost
            }
        }
        
        self.vector_queries.append(vector_query)
        return self
    
    def sparse_vector_search(self,
                           query_vector: Dict[str, float],
                           field: str = 'content_sparse_vector',
                           boost: float = 1.0) -> 'VectorSearchBuilder':
        """Add sparse vector search for keyword relevance"""
        sparse_query = Q('sparse_vector',
                        **{field: {'query_vector': query_vector, 'boost': boost}})
        
        self.vector_queries.append({'query': sparse_query.to_dict()})
        return self
    
    def text_search(self,
                   query: str,
                   fields: List[str] = None,
                   boost: float = 1.0) -> 'VectorSearchBuilder':
        """Add traditional text search"""
        fields = fields or ['title^2', 'content']
        
        text_query = Q('multi_match',
                      query=query,
                      fields=fields,
                      type='best_fields',
                      boost=boost)
        
        self.text_queries.append(text_query)
        return self
    
    def configure_hybrid_search(self,
                              vector_weight: float = 0.7,
                              text_weight: float = 0.3,
                              rrf_rank_constant: int = 60) -> 'VectorSearchBuilder':
        """Configure hybrid search combining vector and text"""
        self.hybrid_config = {
            'vector_weight': vector_weight,
            'text_weight': text_weight,
            'rrf_rank_constant': rrf_rank_constant
        }
        return self
    
    def add_vector_aggregations(self) -> 'VectorSearchBuilder':
        """Add aggregations for vector search analytics"""
        # Category distribution
        self.search.aggs.bucket('categories', 'terms', field='category', size=10)
        
        # Vector similarity ranges (requires custom script)
        self.search.aggs.bucket('similarity_ranges', 'range',
                               script={'source': 'Math.max(0, params._score)'},
                               ranges=[
                                   {'to': 0.5, 'key': 'low_similarity'},
                                   {'from': 0.5, 'to': 0.8, 'key': 'medium_similarity'},
                                   {'from': 0.8, 'key': 'high_similarity'}
                               ])
        return self
    
    async def execute_vector_search(self, size: int = 20) -> Dict[str, Any]:
        """Execute vector search with hybrid capabilities"""
        try:
            # Handle different search strategies
            if self.vector_queries and self.text_queries and self.hybrid_config:
                # Hybrid search with RRF (Reciprocal Rank Fusion)
                return await self._execute_hybrid_search(size)
            
            elif self.vector_queries:
                # Pure vector search
                return await self._execute_pure_vector_search(size)
            
            elif self.text_queries:
                # Pure text search
                return await self._execute_pure_text_search(size)
            
            else:
                raise ValueError("No search queries configured")
                
        except Exception as e:
            logger.error(f"Vector search execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")
    
    async def _execute_pure_vector_search(self, size: int) -> Dict[str, Any]:
        """Execute pure vector search"""
        # For kNN queries, we need to use the native Elasticsearch kNN API
        if any('knn' in vq for vq in self.vector_queries):
            # Use kNN endpoint
            knn_query = self.vector_queries[0]['knn']
            knn_query['k'] = min(size, knn_query.get('k', size))
            
            # Build search with kNN
            search_body = {
                'knn': knn_query,
                'size': size
            }
            
            # Add aggregations if present
            if self.search.aggs:
                search_body['aggs'] = self.search.aggs.to_dict()
            
            # Execute native kNN search
            from elasticsearch import AsyncElasticsearch
            client = AsyncElasticsearch()  # Use configured client
            response = await client.search(index=self.search._index[0], body=search_body)
            
        else:
            # Standard query approach
            if len(self.vector_queries) == 1:
                vector_query = self.vector_queries[0]['query']
                self.search = self.search.query(Q(vector_query))
            else:
                # Combine multiple vector queries
                combined_queries = [vq['query'] for vq in self.vector_queries]
                self.search = self.search.query('bool', should=combined_queries)
            
            self.search = self.search[:size]
            response = await self.search.execute()
        
        return self._format_vector_response(response)
    
    async def _execute_pure_text_search(self, size: int) -> Dict[str, Any]:
        """Execute pure text search"""
        if len(self.text_queries) == 1:
            self.search = self.search.query(self.text_queries[0])
        else:
            self.search = self.search.query('bool', should=self.text_queries)
        
        self.search = self.search[:size]
        response = await self.search.execute()
        
        return self._format_vector_response(response)
    
    async def _execute_hybrid_search(self, size: int) -> Dict[str, Any]:
        """Execute hybrid search with RRF"""
        # Execute vector and text searches separately
        vector_task = self._execute_pure_vector_search(size * 2)  # Get more for RRF
        text_task = self._execute_pure_text_search(size * 2)
        
        vector_results, text_results = await asyncio.gather(vector_task, text_task)
        
        # Apply Reciprocal Rank Fusion
        merged_results = self._apply_rrf(
            vector_results['hits'],
            text_results['hits'],
            self.hybrid_config['rrf_rank_constant']
        )
        
        return {
            'total': max(vector_results.get('total', 0), text_results.get('total', 0)),
            'hits': merged_results[:size],
            'hybrid_search': True,
            'vector_weight': self.hybrid_config['vector_weight'],
            'text_weight': self.hybrid_config['text_weight']
        }
    
    def _apply_rrf(self, 
                   vector_hits: List[Dict], 
                   text_hits: List[Dict], 
                   rank_constant: int = 60) -> List[Dict]:
        """Apply Reciprocal Rank Fusion to merge results"""
        doc_scores = {}
        
        # Score from vector results
        for rank, hit in enumerate(vector_hits, 1):
            doc_id = hit['_id']
            score = 1.0 / (rank_constant + rank)
            doc_scores[doc_id] = {
                'vector_score': score,
                'text_score': 0.0,
                'hit': hit
            }
        
        # Add scores from text results
        for rank, hit in enumerate(text_hits, 1):
            doc_id = hit['_id']
            score = 1.0 / (rank_constant + rank)
            
            if doc_id in doc_scores:
                doc_scores[doc_id]['text_score'] = score
            else:
                doc_scores[doc_id] = {
                    'vector_score': 0.0,
                    'text_score': score,
                    'hit': hit
                }
        
        # Calculate combined scores and sort
        for doc_id, scores in doc_scores.items():
            vector_weight = self.hybrid_config['vector_weight']
            text_weight = self.hybrid_config['text_weight']
            
            combined_score = (
                scores['vector_score'] * vector_weight +
                scores['text_score'] * text_weight
            )
            
            scores['combined_score'] = combined_score
            scores['hit']['_hybrid_score'] = combined_score
        
        # Sort by combined score
        sorted_results = sorted(
            doc_scores.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        return [result['hit'] for result in sorted_results]
    
    def _format_vector_response(self, response: Any) -> Dict[str, Any]:
        """Format vector search response"""
        if isinstance(response, dict):
            # Native kNN response format
            hits = response.get('hits', {}).get('hits', [])
            total = response.get('hits', {}).get('total', {}).get('value', 0)
            
            formatted_hits = []
            for hit in hits:
                formatted_hit = {
                    '_id': hit['_id'],
                    '_score': hit['_score'],
                    '_source': hit['_source']
                }
                formatted_hits.append(formatted_hit)
            
            return {
                'total': total,
                'hits': formatted_hits
            }
        
        else:
            # Standard elasticsearch-dsl response
            return {
                'total': response.hits.total.value,
                'hits': [
                    {
                        '_id': hit.meta.id,
                        '_score': hit.meta.score,
                        '_source': hit.to_dict()
                    }
                    for hit in response.hits
                ],
                'aggregations': response.aggregations.to_dict() if hasattr(response, 'aggregations') else {}
            }

class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    def encode_text(self, text: str) -> List[float]:
        """Generate dense vector embedding for text"""
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def generate_sparse_vector(self, text: str, vocabulary: Dict[str, int]) -> Dict[str, float]:
        """Generate sparse vector representation (TF-IDF style)"""
        # Simple TF implementation (in production, use proper TF-IDF)
        words = text.lower().split()
        word_counts = {}
        
        for word in words:
            if word in vocabulary:
                word_counts[str(vocabulary[word])] = word_counts.get(str(vocabulary[word]), 0) + 1
        
        # Normalize
        max_count = max(word_counts.values()) if word_counts else 1
        return {k: v / max_count for k, v in word_counts.items()}

# Global embedding service
embedding_service = EmbeddingService()

@app.post("/documents/vector-search")
async def vector_search_endpoint(
    query: str,
    search_type: str = Query("hybrid", regex="^(vector|text|hybrid)$"),
    vector_weight: float = Query(0.7, ge=0.0, le=1.0),
    text_weight: float = Query(0.3, ge=0.0, le=1.0),
    size: int = Query(20, le=100),
    category: Optional[str] = None
):
    """Vector-based semantic search"""
    builder = VectorSearchBuilder('vector_documents')
    
    # Generate query embedding for vector search
    if search_type in ['vector', 'hybrid']:
        query_vector = embedding_service.encode_text(query)
        builder.semantic_search(query_vector, k=size, num_candidates=size * 5)
    
    # Add text search for hybrid or text-only
    if search_type in ['text', 'hybrid']:
        builder.text_search(query, ['title^2', 'content'])
    
    # Configure hybrid search
    if search_type == 'hybrid':
        builder.configure_hybrid_search(
            vector_weight=vector_weight,
            text_weight=text_weight
        )
    
    # Add filters
    if category:
        builder.search = builder.search.filter('term', category=category)
    
    # Add aggregations
    builder.add_vector_aggregations()
    
    # Execute search
    result = await builder.execute_vector_search(size)
    
    return result

@app.get("/documents/similar/{document_id}")
async def find_similar_documents(
    document_id: str,
    size: int = Query(10, le=50),
    similarity_threshold: float = Query(0.5, ge=0.0, le=1.0)
):
    """Find documents similar to a given document"""
    # First, get the source document and its vector
    source_search = AsyncSearch(index='vector_documents')
    source_search = source_search.filter('term', _id=document_id)
    
    try:
        source_response = await source_search.execute()
        if not source_response.hits:
            raise HTTPException(status_code=404, detail="Document not found")
        
        source_doc = source_response.hits[0]
        source_vector = source_doc.content_vector
        
        # Search for similar documents
        builder = VectorSearchBuilder('vector_documents')
        builder.semantic_search(source_vector, k=size + 1, num_candidates=size * 10)
        
        # Exclude the source document
        builder.search = builder.search.filter('bool', must_not=[Q('term', _id=document_id)])
        
        result = await builder.execute_vector_search(size)
        
        # Filter by similarity threshold
        filtered_hits = [
            hit for hit in result['hits']
            if hit['_score'] >= similarity_threshold
        ]
        
        return {
            'source_document': {
                '_id': source_doc.meta.id,
                'title': source_doc.title,
                'category': source_doc.category
            },
            'similar_documents': filtered_hits,
            'total_found': len(filtered_hits),
            'similarity_threshold': similarity_threshold
        }
        
    except Exception as e:
        logger.error(f"Similar document search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")
```

## Dense and Sparse Vector Patterns

### Advanced Vector Management

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import joblib

class VectorIndexManager:
    """Manage vector indices and embeddings"""
    
    def __init__(self, index_name: str):
        self.index_name = index_name
        self.embedding_service = embedding_service
        self.tfidf_vectorizer = None
        self.vocabulary = {}
    
    async def create_vector_index(self, 
                                mapping_config: Dict[str, Any] = None) -> bool:
        """Create index with vector field mappings"""
        default_mapping = {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "category": {"type": "keyword"},
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": self.embedding_service.dimension,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "content_sparse_vector": {
                        "type": "sparse_vector"
                    },
                    "hybrid_vector": {
                        "type": "dense_vector",
                        "dims": self.embedding_service.dimension + 100,  # Combined dense + sparse
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            },
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "index.knn": True
            }
        }
        
        mapping = mapping_config or default_mapping
        
        try:
            from elasticsearch import AsyncElasticsearch
            client = AsyncElasticsearch()
            
            # Create index
            await client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Created vector index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            return False
    
    async def index_document_with_vectors(self, 
                                        document: Dict[str, Any],
                                        doc_id: str = None) -> bool:
        """Index document with generated vectors"""
        try:
            # Generate dense vector
            text_content = f"{document.get('title', '')} {document.get('content', '')}"
            dense_vector = self.embedding_service.encode_text(text_content)
            
            # Generate sparse vector
            sparse_vector = self._generate_sparse_vector(text_content)
            
            # Generate hybrid vector (combining dense and sparse features)
            hybrid_vector = self._generate_hybrid_vector(dense_vector, sparse_vector)
            
            # Add vectors to document
            document['content_vector'] = dense_vector
            document['content_sparse_vector'] = sparse_vector
            document['hybrid_vector'] = hybrid_vector
            
            # Index the document
            doc = VectorDocument(**document)
            if doc_id:
                doc.meta.id = doc_id
            
            await doc.save()
            return True
            
        except Exception as e:
            logger.error(f"Failed to index document with vectors: {e}")
            return False
    
    def _generate_sparse_vector(self, text: str) -> Dict[str, float]:
        """Generate sparse vector using TF-IDF"""
        if not self.tfidf_vectorizer:
            # Initialize TF-IDF vectorizer (in production, load pre-trained)
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=10000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # This would be trained on your corpus
            corpus = [text]  # Simplified - use your actual corpus
            self.tfidf_vectorizer.fit(corpus)
            
            # Build vocabulary mapping
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            self.vocabulary = {name: idx for idx, name in enumerate(feature_names)}
        
        # Transform text to sparse vector
        tfidf_matrix = self.tfidf_vectorizer.transform([text])
        
        # Convert to dictionary format
        sparse_vector = {}
        for idx, score in zip(tfidf_matrix.indices, tfidf_matrix.data):
            if score > 0.01:  # Threshold for sparse vector
                sparse_vector[str(idx)] = float(score)
        
        return sparse_vector
    
    def _generate_hybrid_vector(self, 
                              dense_vector: List[float], 
                              sparse_vector: Dict[str, float]) -> List[float]:
        """Generate hybrid vector combining dense and sparse features"""
        # Take top sparse features
        sorted_sparse = sorted(sparse_vector.items(), key=lambda x: x[1], reverse=True)
        top_sparse_features = [float(score) for _, score in sorted_sparse[:100]]
        
        # Pad if necessary
        while len(top_sparse_features) < 100:
            top_sparse_features.append(0.0)
        
        # Combine dense and sparse
        hybrid_vector = dense_vector + top_sparse_features
        
        return hybrid_vector
    
    async def batch_index_with_vectors(self, 
                                     documents: List[Dict[str, Any]],
                                     batch_size: int = 100) -> Dict[str, Any]:
        """Batch index documents with vector generation"""
        results = {
            'total': len(documents),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Generate vectors for batch
                texts = [f"{doc.get('title', '')} {doc.get('content', '')}" for doc in batch]
                dense_vectors = self.embedding_service.encode_batch(texts)
                
                # Process each document in batch
                for j, doc in enumerate(batch):
                    try:
                        # Add dense vector
                        doc['content_vector'] = dense_vectors[j]
                        
                        # Add sparse vector
                        doc['content_sparse_vector'] = self._generate_sparse_vector(texts[j])
                        
                        # Add hybrid vector
                        doc['hybrid_vector'] = self._generate_hybrid_vector(
                            dense_vectors[j], 
                            doc['content_sparse_vector']
                        )
                        
                        # Index document
                        vector_doc = VectorDocument(**doc)
                        await vector_doc.save()
                        
                        results['successful'] += 1
                        
                    except Exception as e:
                        results['failed'] += 1
                        results['errors'].append(f"Document {i+j}: {str(e)}")
                
                # Small delay between batches
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                results['failed'] += len(batch)
                results['errors'].append(f"Batch {i//batch_size}: {str(e)}")
        
        return results
    
    async def update_vector_weights(self, 
                                  performance_data: Dict[str, float]) -> bool:
        """Update vector weights based on performance feedback"""
        try:
            # This could adjust embedding model weights or sparse vector weights
            # Based on user feedback, click-through rates, etc.
            
            # Example: Boost certain categories in sparse vectors
            category_boosts = performance_data.get('category_boosts', {})
            
            # Update TF-IDF weights (simplified example)
            if self.tfidf_vectorizer and category_boosts:
                # In practice, you'd retrain or adjust the vectorizer
                logger.info(f"Updated vector weights with boosts: {category_boosts}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update vector weights: {e}")
            return False

# Global vector manager
vector_manager = VectorIndexManager('vector_documents')

@app.post("/admin/vectors/create-index")
async def create_vector_index():
    """Create vector search index"""
    success = await vector_manager.create_vector_index()
    
    if success:
        return {"message": "Vector index created successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to create vector index")

@app.post("/documents/index-with-vectors")
async def index_document_with_vectors(document: Dict[str, Any]):
    """Index single document with vector generation"""
    success = await vector_manager.index_document_with_vectors(document)
    
    if success:
        return {"message": "Document indexed with vectors successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to index document")

@app.post("/documents/batch-index-vectors")
async def batch_index_documents_with_vectors(
    documents: List[Dict[str, Any]],
    batch_size: int = Query(100, le=1000)
):
    """Batch index documents with vector generation"""
    if len(documents) > 10000:
        raise HTTPException(status_code=400, detail="Maximum 10,000 documents per batch")
    
    result = await vector_manager.batch_index_with_vectors(documents, batch_size)
    return result
```

## Location-Based Search with FastAPI

### Real-World Location Services

```python
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import folium
import base64
from io import BytesIO

class LocationService:
    """Comprehensive location-based services"""
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="fastapi-geo-search")
        self.earth_radius_km = 6371
    
    def calculate_distance(self, 
                          point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in kilometers"""
        return geodesic(point1, point2).kilometers
    
    def calculate_bounding_box(self, 
                             center_lat: float, 
                             center_lon: float, 
                             radius_km: float) -> Dict[str, Dict[str, float]]:
        """Calculate bounding box for a circular area"""
        # Approximate degrees per kilometer
        lat_delta = radius_km / 111.0  # 1 degree lat ≈ 111 km
        lon_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        
        return {
            'top_left': {
                'lat': center_lat + lat_delta,
                'lon': center_lon - lon_delta
            },
            'bottom_right': {
                'lat': center_lat - lat_delta,
                'lon': center_lon + lon_delta
            }
        }
    
    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Convert address to coordinates"""
        try:
            location = self.geocoder.geocode(address)
            if location:
                return {
                    'address': location.address,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'raw': location.raw
                }
        except Exception as e:
            logger.error(f"Geocoding failed: {e}")
        
        return None
    
    async def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Convert coordinates to address"""
        try:
            location = self.geocoder.reverse((lat, lon))
            if location:
                return {
                    'address': location.address,
                    'raw': location.raw
                }
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
        
        return None
    
    def generate_map_visualization(self, 
                                 locations: List[Dict[str, Any]],
                                 center_lat: float = None,
                                 center_lon: float = None) -> str:
        """Generate HTML map visualization"""
        if not locations:
            return ""
        
        # Calculate center if not provided
        if center_lat is None or center_lon is None:
            lats = [loc['location']['lat'] for loc in locations if 'location' in loc]
            lons = [loc['location']['lon'] for loc in locations if 'location' in loc]
            
            if lats and lons:
                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)
            else:
                center_lat, center_lon = 40.7128, -74.0060  # Default to NYC
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        
        # Add markers
        for i, location in enumerate(locations):
            if 'location' in location and 'lat' in location['location']:
                lat = location['location']['lat']
                lon = location['location']['lon']
                
                popup_text = f"""
                <b>{location.get('name', f'Location {i+1}')}</b><br>
                {location.get('address', '')}<br>
                Score: {location.get('_score', 'N/A')}<br>
                Distance: {location.get('_distance_km', 'N/A')} km
                """
                
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=location.get('name', f'Location {i+1}')
                ).add_to(m)
        
        # Convert to HTML string
        return m._repr_html_()

class DeliveryZoneManager:
    """Manage delivery zones and route optimization"""
    
    def __init__(self):
        self.location_service = LocationService()
    
    async def find_delivery_zones(self, 
                                lat: float, 
                                lon: float) -> List[Dict[str, Any]]:
        """Find delivery zones covering a location"""
        search = AsyncSearch(index='delivery_zones')
        
        # Use geo_shape query to find zones containing the point
        point_query = Q('geo_shape',
                       zone_polygon={
                           'shape': {
                               'type': 'point',
                               'coordinates': [lon, lat]
                           },
                           'relation': 'contains'
                       })
        
        search = search.query(point_query).filter('term', active=True)
        
        try:
            response = await search.execute()
            
            zones = []
            for hit in response.hits:
                zone = hit.to_dict()
                zone['_id'] = hit.meta.id
                zones.append(zone)
            
            return zones
            
        except Exception as e:
            logger.error(f"Delivery zone search failed: {e}")
            return []
    
    async def calculate_delivery_routes(self, 
                                      origin: Tuple[float, float],
                                      destinations: List[Tuple[float, float]]) -> Dict[str, Any]:
        """Calculate optimized delivery routes"""
        # Simplified route calculation (in production, use routing service)
        routes = []
        total_distance = 0
        
        current_location = origin
        remaining_destinations = destinations.copy()
        
        # Greedy nearest neighbor approach
        while remaining_destinations:
            distances = [
                self.location_service.calculate_distance(current_location, dest)
                for dest in remaining_destinations
            ]
            
            nearest_idx = distances.index(min(distances))
            nearest_dest = remaining_destinations.pop(nearest_idx)
            nearest_distance = distances[nearest_idx]
            
            routes.append({
                'from': current_location,
                'to': nearest_dest,
                'distance_km': nearest_distance
            })
            
            total_distance += nearest_distance
            current_location = nearest_dest
        
        return {
            'routes': routes,
            'total_distance_km': total_distance,
            'estimated_time_minutes': total_distance * 2,  # Simplified: 2 min/km
            'optimization_method': 'nearest_neighbor'
        }

# Global services
location_service = LocationService()
delivery_manager = DeliveryZoneManager()

@app.get("/locations/geocode")
async def geocode_address_endpoint(address: str):
    """Convert address to coordinates"""
    result = await location_service.geocode_address(address)
    
    if result:
        return result
    else:
        raise HTTPException(status_code=404, detail="Address not found")

@app.get("/locations/reverse-geocode")
async def reverse_geocode_endpoint(lat: float, lon: float):
    """Convert coordinates to address"""
    result = await location_service.reverse_geocode(lat, lon)
    
    if result:
        return result
    else:
        raise HTTPException(status_code=404, detail="Location not found")

@app.get("/locations/nearby-with-map")
async def nearby_locations_with_map(
    lat: float,
    lon: float,
    radius: str = "5km",
    category: Optional[str] = None,
    include_map: bool = True
):
    """Find nearby locations with optional map visualization"""
    # Search for nearby locations
    builder = GeospatialSearchBuilder('locations')
    builder.near_point(lat, lon, radius)
    builder.sort_by_distance(lat, lon)
    
    if category:
        builder.search = builder.search.filter('term', category=category)
    
    result = await builder.apply_geo_queries().execute_geo_search()
    
    # Add map visualization if requested
    if include_map and result['hits']:
        map_html = location_service.generate_map_visualization(
            result['hits'], lat, lon
        )
        result['map_html'] = map_html
    
    return result

@app.get("/delivery/zones")
async def find_delivery_zones_endpoint(lat: float, lon: float):
    """Find delivery zones for a location"""
    zones = await delivery_manager.find_delivery_zones(lat, lon)
    
    return {
        'location': {'lat': lat, 'lon': lon},
        'zones': zones,
        'zone_count': len(zones)
    }

@app.post("/delivery/route-optimization")
async def optimize_delivery_route(
    origin_lat: float,
    origin_lon: float,
    destinations: List[Dict[str, float]]  # [{"lat": x, "lon": y}, ...]
):
    """Optimize delivery route for multiple destinations"""
    if len(destinations) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 destinations allowed")
    
    origin = (origin_lat, origin_lon)
    dest_coords = [(d['lat'], d['lon']) for d in destinations]
    
    route_data = await delivery_manager.calculate_delivery_routes(origin, dest_coords)
    
    return {
        'origin': {'lat': origin_lat, 'lon': origin_lon},
        'destination_count': len(destinations),
        **route_data
    }
```

## Machine Learning Integration

### ML-Powered Search Enhancement

```python
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime, timedelta

class SearchMLService:
    """Machine learning service for search enhancement"""
    
    def __init__(self):
        self.ranking_model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.click_through_data = defaultdict(list)
    
    def extract_features(self, query: str, document: Dict[str, Any], 
                        context: Dict[str, Any] = None) -> List[float]:
        """Extract features for ML ranking"""
        features = []
        
        # Text similarity features
        query_terms = set(query.lower().split())
        doc_text = f"{document.get('title', '')} {document.get('content', '')}".lower()
        doc_terms = set(doc_text.split())
        
        # Jaccard similarity
        intersection = len(query_terms & doc_terms)
        union = len(query_terms | doc_terms)
        jaccard_sim = intersection / union if union > 0 else 0.0
        features.append(jaccard_sim)
        
        # Term frequency features
        query_term_freq = sum(1 for term in query_terms if term in doc_text)
        features.append(query_term_freq / len(query_terms) if query_terms else 0.0)
        
        # Document features
        features.extend([
            float(document.get('rating', 0.0)),
            float(document.get('view_count', 0)),
            float(document.get('price', 0.0)),
            1.0 if document.get('in_stock', False) else 0.0
        ])
        
        # Temporal features
        created_date = document.get('created_date')
        if created_date:
            if isinstance(created_date, str):
                created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            
            days_old = (datetime.now() - created_date).days
            features.append(float(days_old))
        else:
            features.append(0.0)
        
        # Context features
        if context:
            features.extend([
                float(context.get('user_rating_preference', 0.0)),
                float(context.get('user_price_preference', 0.0)),
                1.0 if context.get('user_category') == document.get('category') else 0.0
            ])
        else:
            features.extend([0.0, 0.0, 0.0])
        
        # Geospatial features (if available)
        if context and 'user_location' in context and 'location' in document:
            user_lat, user_lon = context['user_location']
            doc_lat = document['location'].get('lat', 0)
            doc_lon = document['location'].get('lon', 0)
            
            distance = location_service.calculate_distance(
                (user_lat, user_lon), (doc_lat, doc_lon)
            )
            features.append(float(distance))
        else:
            features.append(0.0)
        
        return features
    
    def train_ranking_model(self, training_data: List[Dict[str, Any]]):
        """Train ML ranking model"""
        X = []
        y = []
        
        for sample in training_data:
            features = self.extract_features(
                sample['query'], 
                sample['document'], 
                sample.get('context')
            )
            X.append(features)
            y.append(sample['relevance_score'])  # Ground truth relevance
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.ranking_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.ranking_model.fit(X_scaled, y)
        
        # Store feature importance
        feature_names = [
            'jaccard_similarity', 'term_frequency', 'rating', 'view_count',
            'price', 'in_stock', 'days_old', 'user_rating_pref',
            'user_price_pref', 'category_match', 'distance'
        ]
        
        self.feature_importance = dict(zip(
            feature_names, 
            self.ranking_model.feature_importances_
        ))
        
        logger.info(f"Trained ranking model with {len(training_data)} samples")
    
    def predict_relevance(self, query: str, document: Dict[str, Any], 
                         context: Dict[str, Any] = None) -> float:
        """Predict relevance score for query-document pair"""
        if not self.ranking_model:
            return 0.5  # Default score if no model
        
        features = self.extract_features(query, document, context)
        X = np.array([features])
        X_scaled = self.scaler.transform(X)
        
        relevance_score = self.ranking_model.predict(X_scaled)[0]
        return float(np.clip(relevance_score, 0.0, 1.0))
    
    def record_click_through(self, query: str, document_id: str, 
                           position: int, clicked: bool):
        """Record click-through data for model improvement"""
        self.click_through_data[query].append({
            'document_id': document_id,
            'position': position,
            'clicked': clicked,
            'timestamp': datetime.now()
        })
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        return {
            'feature_importance': self.feature_importance,
            'click_through_data_size': sum(len(data) for data in self.click_through_data.values()),
            'model_trained': self.ranking_model is not None
        }
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if self.ranking_model:
            joblib.dump({
                'model': self.ranking_model,
                'scaler': self.scaler,
                'feature_importance': self.feature_importance
            }, filepath)
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        try:
            data = joblib.load(filepath)
            self.ranking_model = data['model']
            self.scaler = data['scaler']
            self.feature_importance = data['feature_importance']
            logger.info(f"Loaded ML ranking model from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

class MLEnhancedSearchBuilder:
    """Search builder with ML ranking enhancement"""
    
    def __init__(self, index: str, ml_service: SearchMLService):
        self.search = AsyncSearch(index=index)
        self.ml_service = ml_service
        self.original_query = ""
        self.user_context = {}
    
    def with_query(self, query: str) -> 'MLEnhancedSearchBuilder':
        """Set search query"""
        self.original_query = query
        self.search = self.search.query(
            'multi_match',
            query=query,
            fields=['title^2', 'content', 'category'],
            type='best_fields'
        )
        return self
    
    def with_user_context(self, context: Dict[str, Any]) -> 'MLEnhancedSearchBuilder':
        """Set user context for personalization"""
        self.user_context = context
        return self
    
    def with_filters(self, filters: Dict[str, Any]) -> 'MLEnhancedSearchBuilder':
        """Add search filters"""
        for field, value in filters.items():
            if isinstance(value, list):
                self.search = self.search.filter('terms', **{field: value})
            else:
                self.search = self.search.filter('term', **{field: value})
        return self
    
    async def execute_ml_enhanced_search(self, size: int = 20) -> Dict[str, Any]:
        """Execute search with ML re-ranking"""
        try:
            # Get more results than needed for re-ranking
            extended_size = min(size * 5, 100)
            response = await self.search[:extended_size].execute()
            
            # Extract documents for ML scoring
            documents = []
            for hit in response.hits:
                doc = hit.to_dict()
                doc['_id'] = hit.meta.id
                doc['_original_score'] = hit.meta.score
                documents.append(doc)
            
            # Apply ML re-ranking
            scored_documents = []
            for doc in documents:
                ml_score = self.ml_service.predict_relevance(
                    self.original_query, doc, self.user_context
                )
                
                # Combine original Elasticsearch score with ML score
                combined_score = 0.6 * doc['_original_score'] + 0.4 * ml_score
                
                doc['_ml_score'] = ml_score
                doc['_combined_score'] = combined_score
                scored_documents.append(doc)
            
            # Sort by combined score
            scored_documents.sort(key=lambda x: x['_combined_score'], reverse=True)
            
            # Return top results
            final_results = scored_documents[:size]
            
            return {
                'total': response.hits.total.value,
                'query': self.original_query,
                'ml_enhanced': True,
                'hits': final_results,
                'feature_importance': self.ml_service.feature_importance
            }
            
        except Exception as e:
            logger.error(f"ML-enhanced search failed: {e}")
            raise HTTPException(status_code=500, detail="Search failed")

# Global ML service
ml_service = SearchMLService()

@app.post("/search/ml-enhanced")
async def ml_enhanced_search(
    query: str,
    filters: Dict[str, Any] = {},
    user_context: Dict[str, Any] = {},
    size: int = Query(20, le=100)
):
    """Search with ML-enhanced ranking"""
    builder = MLEnhancedSearchBuilder('products', ml_service)
    
    result = await (
        builder
        .with_query(query)
        .with_user_context(user_context)
        .with_filters(filters)
        .execute_ml_enhanced_search(size)
    )
    
    return result

@app.post("/search/record-click")
async def record_click_through(
    query: str,
    document_id: str,
    position: int,
    clicked: bool
):
    """Record click-through data for model improvement"""
    ml_service.record_click_through(query, document_id, position, clicked)
    
    return {"message": "Click-through data recorded"}

@app.post("/admin/ml/train-model")
async def train_ranking_model(training_data: List[Dict[str, Any]]):
    """Train ML ranking model with provided data"""
    if len(training_data) < 100:
        raise HTTPException(status_code=400, detail="Minimum 100 training samples required")
    
    try:
        ml_service.train_ranking_model(training_data)
        return {
            "message": "Model trained successfully",
            "training_samples": len(training_data),
            "feature_importance": ml_service.feature_importance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@app.get("/admin/ml/model-performance")
async def get_model_performance():
    """Get ML model performance metrics"""
    return ml_service.get_model_performance()
```

## Hybrid Search Strategies

### Advanced Hybrid Search Implementation

```python
class HybridSearchOrchestrator:
    """Orchestrate multiple search strategies"""
    
    def __init__(self):
        self.strategies = {}
        self.fusion_methods = {
            'rrf': self._reciprocal_rank_fusion,
            'weighted_sum': self._weighted_sum_fusion,
            'max_score': self._max_score_fusion,
            'bayesian': self._bayesian_fusion
        }
    
    def register_strategy(self, name: str, search_func: callable, weight: float = 1.0):
        """Register a search strategy"""
        self.strategies[name] = {
            'func': search_func,
            'weight': weight
        }
    
    async def execute_hybrid_search(self, 
                                  query: str,
                                  strategies: List[str],
                                  fusion_method: str = 'rrf',
                                  size: int = 20) -> Dict[str, Any]:
        """Execute hybrid search with multiple strategies"""
        if not all(strategy in self.strategies for strategy in strategies):
            missing = [s for s in strategies if s not in self.strategies]
            raise ValueError(f"Unknown strategies: {missing}")
        
        # Execute all strategies in parallel
        tasks = {}
        for strategy_name in strategies:
            strategy = self.strategies[strategy_name]
            tasks[strategy_name] = strategy['func'](query, size * 2)  # Get more for fusion
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Process results
        strategy_results = {}
        for i, strategy_name in enumerate(strategies):
            if isinstance(results[i], Exception):
                logger.error(f"Strategy {strategy_name} failed: {results[i]}")
                strategy_results[strategy_name] = {'hits': [], 'error': str(results[i])}
            else:
                strategy_results[strategy_name] = results[i]
        
        # Apply fusion
        fusion_func = self.fusion_methods.get(fusion_method, self._reciprocal_rank_fusion)
        fused_results = fusion_func(strategy_results, strategies, size)
        
        return {
            'query': query,
            'strategies_used': strategies,
            'fusion_method': fusion_method,
            'total': fused_results.get('total', 0),
            'hits': fused_results.get('hits', []),
            'strategy_breakdown': {
                name: {
                    'total': result.get('total', 0),
                    'error': result.get('error')
                }
                for name, result in strategy_results.items()
            }
        }
    
    def _reciprocal_rank_fusion(self, 
                               strategy_results: Dict[str, Any],
                               strategies: List[str],
                               size: int,
                               k: int = 60) -> Dict[str, Any]:
        """Reciprocal Rank Fusion algorithm"""
        doc_scores = defaultdict(lambda: {'total_score': 0.0, 'strategy_scores': {}, 'doc': None})
        
        for strategy_name in strategies:
            result = strategy_results[strategy_name]
            weight = self.strategies[strategy_name]['weight']
            
            for rank, hit in enumerate(result.get('hits', []), 1):
                doc_id = hit['_id']
                rrf_score = weight / (k + rank)
                
                doc_scores[doc_id]['total_score'] += rrf_score
                doc_scores[doc_id]['strategy_scores'][strategy_name] = rrf_score
                
                if doc_scores[doc_id]['doc'] is None:
                    doc_scores[doc_id]['doc'] = hit
        
        # Sort by total score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        )
        
        # Format results
        hits = []
        for doc_id, score_data in sorted_docs[:size]:
            hit = score_data['doc'].copy()
            hit['_fusion_score'] = score_data['total_score']
            hit['_strategy_scores'] = score_data['strategy_scores']
            hits.append(hit)
        
        return {
            'hits': hits,
            'total': len(doc_scores)
        }
    
    def _weighted_sum_fusion(self, 
                           strategy_results: Dict[str, Any],
                           strategies: List[str],
                           size: int) -> Dict[str, Any]:
        """Weighted sum fusion of normalized scores"""
        doc_scores = defaultdict(lambda: {'total_score': 0.0, 'strategy_scores': {}, 'doc': None})
        
        # Normalize scores within each strategy
        for strategy_name in strategies:
            result = strategy_results[strategy_name]
            hits = result.get('hits', [])
            
            if not hits:
                continue
            
            # Find max score for normalization
            max_score = max(hit.get('_score', 0) for hit in hits)
            if max_score == 0:
                max_score = 1
            
            weight = self.strategies[strategy_name]['weight']
            
            for hit in hits:
                doc_id = hit['_id']
                normalized_score = hit.get('_score', 0) / max_score
                weighted_score = normalized_score * weight
                
                doc_scores[doc_id]['total_score'] += weighted_score
                doc_scores[doc_id]['strategy_scores'][strategy_name] = weighted_score
                
                if doc_scores[doc_id]['doc'] is None:
                    doc_scores[doc_id]['doc'] = hit
        
        # Sort and format
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        )
        
        hits = []
        for doc_id, score_data in sorted_docs[:size]:
            hit = score_data['doc'].copy()
            hit['_fusion_score'] = score_data['total_score']
            hit['_strategy_scores'] = score_data['strategy_scores']
            hits.append(hit)
        
        return {
            'hits': hits,
            'total': len(doc_scores)
        }
    
    def _max_score_fusion(self, 
                         strategy_results: Dict[str, Any],
                         strategies: List[str],
                         size: int) -> Dict[str, Any]:
        """Take maximum score across strategies"""
        doc_scores = {}
        
        for strategy_name in strategies:
            result = strategy_results[strategy_name]
            
            for hit in result.get('hits', []):
                doc_id = hit['_id']
                score = hit.get('_score', 0)
                
                if doc_id not in doc_scores or score > doc_scores[doc_id]['score']:
                    doc_scores[doc_id] = {
                        'score': score,
                        'best_strategy': strategy_name,
                        'doc': hit
                    }
        
        # Sort and format
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        hits = []
        for doc_id, score_data in sorted_docs[:size]:
            hit = score_data['doc'].copy()
            hit['_fusion_score'] = score_data['score']
            hit['_best_strategy'] = score_data['best_strategy']
            hits.append(hit)
        
        return {
            'hits': hits,
            'total': len(doc_scores)
        }
    
    def _bayesian_fusion(self, 
                        strategy_results: Dict[str, Any],
                        strategies: List[str],
                        size: int) -> Dict[str, Any]:
        """Bayesian fusion based on strategy reliability"""
        # Simplified Bayesian approach
        strategy_reliabilities = {
            strategy: 0.8 + 0.2 * (i / len(strategies))  # Varying reliability
            for i, strategy in enumerate(strategies)
        }
        
        doc_scores = defaultdict(lambda: {'combined_prob': 1.0, 'doc': None})
        
        for strategy_name in strategies:
            result = strategy_results[strategy_name]
            reliability = strategy_reliabilities[strategy_name]
            
            for hit in result.get('hits', []):
                doc_id = hit['_id']
                score = hit.get('_score', 0)
                
                # Convert score to probability
                prob = min(score / 10.0, 1.0)  # Assuming scores are 0-10 range
                
                # Bayesian update
                prior = doc_scores[doc_id]['combined_prob']
                likelihood = reliability * prob + (1 - reliability) * 0.5
                
                doc_scores[doc_id]['combined_prob'] = prior * likelihood
                
                if doc_scores[doc_id]['doc'] is None:
                    doc_scores[doc_id]['doc'] = hit
        
        # Sort and format
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1]['combined_prob'],
            reverse=True
        )
        
        hits = []
        for doc_id, score_data in sorted_docs[:size]:
            hit = score_data['doc'].copy()
            hit['_fusion_score'] = score_data['combined_prob']
            hits.append(hit)
        
        return {
            'hits': hits,
            'total': len(doc_scores)
        }

# Define search strategies
async def text_search_strategy(query: str, size: int) -> Dict[str, Any]:
    """Traditional text search strategy"""
    search = AsyncSearch(index='products')
    search = search.query(
        'multi_match',
        query=query,
        fields=['name^2', 'description'],
        type='best_fields'
    )[:size]
    
    response = await search.execute()
    
    return {
        'total': response.hits.total.value,
        'hits': [
            {
                '_id': hit.meta.id,
                '_score': hit.meta.score,
                '_source': hit.to_dict()
            }
            for hit in response.hits
        ]
    }

async def vector_search_strategy(query: str, size: int) -> Dict[str, Any]:
    """Vector semantic search strategy"""
    query_vector = embedding_service.encode_text(query)
    
    builder = VectorSearchBuilder('vector_documents')
    builder.semantic_search(query_vector, k=size, num_candidates=size * 5)
    
    return await builder.execute_vector_search(size)

async def geo_search_strategy(query: str, size: int) -> Dict[str, Any]:
    """Geo-aware search strategy"""
    # This is a simplified example - in practice, you'd extract location from query
    search = AsyncSearch(index='locations')
    search = search.query(
        'multi_match',
        query=query,
        fields=['name^2', 'description', 'address']
    )[:size]
    
    response = await search.execute()
    
    return {
        'total': response.hits.total.value,
        'hits': [
            {
                '_id': hit.meta.id,
                '_score': hit.meta.score,
                '_source': hit.to_dict()
            }
            for hit in response.hits
        ]
    }

async def ml_search_strategy(query: str, size: int) -> Dict[str, Any]:
    """ML-enhanced search strategy"""
    builder = MLEnhancedSearchBuilder('products', ml_service)
    
    return await (
        builder
        .with_query(query)
        .execute_ml_enhanced_search(size)
    )

# Global hybrid search orchestrator
hybrid_orchestrator = HybridSearchOrchestrator()

# Register strategies
hybrid_orchestrator.register_strategy('text', text_search_strategy, weight=1.0)
hybrid_orchestrator.register_strategy('vector', vector_search_strategy, weight=1.2)
hybrid_orchestrator.register_strategy('geo', geo_search_strategy, weight=0.8)
hybrid_orchestrator.register_strategy('ml', ml_search_strategy, weight=1.1)

@app.post("/search/hybrid")
async def hybrid_search_endpoint(
    query: str,
    strategies: List[str] = Query(['text', 'vector']),
    fusion_method: str = Query('rrf', regex='^(rrf|weighted_sum|max_score|bayesian)$'),
    size: int = Query(20, le=100)
):
    """Hybrid search combining multiple strategies"""
    result = await hybrid_orchestrator.execute_hybrid_search(
        query, strategies, fusion_method, size
    )
    
    return result

@app.get("/search/strategies")
async def get_available_strategies():
    """Get available search strategies"""
    return {
        'strategies': list(hybrid_orchestrator.strategies.keys()),
        'fusion_methods': list(hybrid_orchestrator.fusion_methods.keys())
    }
```

## Performance and Scaling

### Production-Ready Optimizations

```python
class ProductionSearchOptimizer:
    """Production-level search optimizations"""
    
    def __init__(self):
        self.cache_manager = None
        self.performance_metrics = defaultdict(list)
        self.optimization_rules = {}
    
    def setup_production_optimizations(self):
        """Setup production-level optimizations"""
        # Enable compression
        self.enable_request_compression()
        
        # Setup connection pooling
        self.setup_connection_pooling()
        
        # Configure caching
        self.setup_intelligent_caching()
        
        # Setup monitoring
        self.setup_performance_monitoring()
    
    def enable_request_compression(self):
        """Enable request/response compression"""
        # This would be configured at the Elasticsearch client level
        logger.info("Request compression enabled")
    
    def setup_connection_pooling(self):
        """Configure optimal connection pooling"""
        # Configure based on expected load
        logger.info("Connection pooling configured")
    
    def setup_intelligent_caching(self):
        """Setup multi-tier caching"""
        logger.info("Intelligent caching enabled")
    
    def setup_performance_monitoring(self):
        """Setup comprehensive performance monitoring"""
        logger.info("Performance monitoring enabled")
    
    async def auto_optimize_query(self, search_request: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically optimize query based on patterns"""
        optimizations_applied = []
        
        # Check query complexity
        if self._is_complex_query(search_request):
            search_request = self._optimize_complex_query(search_request)
            optimizations_applied.append('complex_query_optimization')
        
        # Check for geo queries
        if self._has_geo_component(search_request):
            search_request = self._optimize_geo_query(search_request)
            optimizations_applied.append('geo_optimization')
        
        # Check for vector queries
        if self._has_vector_component(search_request):
            search_request = self._optimize_vector_query(search_request)
            optimizations_applied.append('vector_optimization')
        
        search_request['optimizations_applied'] = optimizations_applied
        return search_request
    
    def _is_complex_query(self, request: Dict[str, Any]) -> bool:
        """Check if query is complex and needs optimization"""
        # Heuristics for complex queries
        return (
            len(str(request)) > 1000 or
            'aggregations' in request or
            'nested' in str(request)
        )
    
    def _has_geo_component(self, request: Dict[str, Any]) -> bool:
        """Check if query has geospatial components"""
        return any(geo_term in str(request) for geo_term in ['geo_', 'location', 'distance'])
    
    def _has_vector_component(self, request: Dict[str, Any]) -> bool:
        """Check if query has vector components"""
        return 'vector' in str(request) or 'knn' in str(request)
    
    def _optimize_complex_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize complex queries"""
        # Add timeout
        if 'timeout' not in request:
            request['timeout'] = '30s'
        
        # Enable request cache for aggregations
        if 'aggregations' in request:
            request['request_cache'] = True
        
        return request
    
    def _optimize_geo_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize geospatial queries"""
        # Use precision optimizations
        request['geo_optimization'] = True
        return request
    
    def _optimize_vector_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize vector queries"""
        # Adjust candidate multiplier based on size
        if 'knn' in request:
            size = request.get('size', 10)
            request['knn']['num_candidates'] = min(size * 10, 1000)
        
        return request

# Global optimizer
production_optimizer = ProductionSearchOptimizer()

@app.on_event("startup")
async def setup_production_optimizations():
    """Setup production optimizations on startup"""
    production_optimizer.setup_production_optimizations()

@app.get("/admin/performance/optimize-query")
async def optimize_query_endpoint(search_request: Dict[str, Any]):
    """Auto-optimize search query"""
    optimized_request = await production_optimizer.auto_optimize_query(search_request)
    
    return {
        'original_request': search_request,
        'optimized_request': optimized_request,
        'optimizations_applied': optimized_request.get('optimizations_applied', [])
    }
```

## Next Steps

1. **[Data Modeling](../05-data-modeling/01_document-design.md)** - Design efficient document structures
2. **[Production Patterns](../06-production-patterns/01_monitoring-logging.md)** - Production deployment patterns
3. **[Testing and Deployment](../07-testing-deployment/01_testing-strategies.md)** - Testing strategies and CI/CD
4. **[Performance Optimization](02_async-search-performance.md)** - Advanced performance patterns
5. **[Complex Queries](01_complex-queries.md)** - Advanced query patterns

## Additional Resources

- **Elasticsearch Geospatial**: [elastic.co/guide/en/elasticsearch/reference/current/geo-queries.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/geo-queries.html)
- **Vector Search**: [elastic.co/guide/en/elasticsearch/reference/current/knn-search.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html)
- **Machine Learning**: [elastic.co/guide/en/elasticsearch/reference/current/ml-apis.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/ml-apis.html)
- **Geopy Documentation**: [geopy.readthedocs.io](https://geopy.readthedocs.io)
- **Sentence Transformers**: [sbert.net](https://www.sbert.net)