# Serialization Patterns

Advanced data serialization and transformation patterns for FastAPI + Elasticsearch-DSL applications with performance optimization and streaming support.

## Table of Contents
- [Serialization Architecture](#serialization-architecture)
- [Custom Serialization Methods](#custom-serialization-methods)
- [Response Formatting](#response-formatting)
- [Pagination Patterns](#pagination-patterns)
- [Streaming Patterns](#streaming-patterns)
- [Caching Strategies](#caching-strategies)
- [Performance Optimization](#performance-optimization)
- [Error Handling](#error-handling)
- [Next Steps](#next-steps)

## Serialization Architecture

### Core Serialization Framework
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, AsyncIterator
from pydantic import BaseModel, Field, root_validator
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from elasticsearch_dsl import AsyncDocument, AsyncSearch
from elasticsearch.exceptions import NotFoundError
import json
import asyncio
from datetime import datetime
import logging
from functools import lru_cache
import gzip
import pickle
from redis import asyncio as aioredis

T = TypeVar('T')

class SerializationStrategy(ABC, Generic[T]):
    """Abstract base class for serialization strategies."""
    
    @abstractmethod
    async def serialize(self, data: Any) -> T:
        """Serialize data to target format."""
        pass
    
    @abstractmethod
    async def deserialize(self, serialized_data: T) -> Any:
        """Deserialize data from target format."""
        pass
    
    @abstractmethod
    def get_content_type(self) -> str:
        """Get content type for serialized data."""
        pass

class JSONSerializationStrategy(SerializationStrategy[str]):
    """JSON serialization strategy with custom encoders."""
    
    def __init__(self, custom_encoders: Dict[type, callable] = None):
        self.custom_encoders = custom_encoders or {}
        self.default_encoders = {
            datetime: lambda dt: dt.isoformat(),
            bytes: lambda b: b.decode('utf-8', errors='ignore'),
            set: list,
        }
    
    async def serialize(self, data: Any) -> str:
        """Serialize data to JSON string."""
        try:
            return json.dumps(
                data,
                default=self._custom_encoder,
                ensure_ascii=False,
                separators=(',', ':')  # Compact format
            )
        except (TypeError, ValueError) as e:
            raise ValueError(f"JSON serialization failed: {str(e)}")
    
    async def deserialize(self, serialized_data: str) -> Any:
        """Deserialize JSON string to Python object."""
        try:
            return json.loads(serialized_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON deserialization failed: {str(e)}")
    
    def get_content_type(self) -> str:
        return "application/json"
    
    def _custom_encoder(self, obj):
        """Custom encoder for non-serializable objects."""
        obj_type = type(obj)
        
        # Check custom encoders first
        if obj_type in self.custom_encoders:
            return self.custom_encoders[obj_type](obj)
        
        # Check default encoders
        if obj_type in self.default_encoders:
            return self.default_encoders[obj_type](obj)
        
        # Handle Elasticsearch document objects
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        
        # Handle Pydantic models
        if hasattr(obj, 'dict'):
            return obj.dict()
        
        raise TypeError(f"Object of type {obj_type} is not JSON serializable")

class MessagePackSerializationStrategy(SerializationStrategy[bytes]):
    """MessagePack serialization for binary efficiency."""
    
    def __init__(self):
        try:
            import msgpack
            self.msgpack = msgpack
        except ImportError:
            raise ImportError("msgpack-python is required for MessagePack serialization")
    
    async def serialize(self, data: Any) -> bytes:
        """Serialize data to MessagePack bytes."""
        try:
            return self.msgpack.packb(
                data,
                default=self._msgpack_encoder,
                use_bin_type=True
            )
        except Exception as e:
            raise ValueError(f"MessagePack serialization failed: {str(e)}")
    
    async def deserialize(self, serialized_data: bytes) -> Any:
        """Deserialize MessagePack bytes to Python object."""
        try:
            return self.msgpack.unpackb(
                serialized_data,
                raw=False,
                strict_map_key=False
            )
        except Exception as e:
            raise ValueError(f"MessagePack deserialization failed: {str(e)}")
    
    def get_content_type(self) -> str:
        return "application/msgpack"
    
    def _msgpack_encoder(self, obj):
        """Custom encoder for MessagePack."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        
        raise TypeError(f"Object of type {type(obj)} is not MessagePack serializable")

class SerializationContext:
    """Context for managing serialization options and metadata."""
    
    def __init__(
        self,
        strategy: SerializationStrategy,
        include_metadata: bool = True,
        compression: bool = False,
        encryption: bool = False,
        cache_ttl: Optional[int] = None
    ):
        self.strategy = strategy
        self.include_metadata = include_metadata
        self.compression = compression
        self.encryption = encryption
        self.cache_ttl = cache_ttl
        self.metadata = {
            'serialized_at': datetime.utcnow(),
            'strategy': strategy.__class__.__name__,
            'version': '1.0'
        }
    
    async def serialize_with_context(self, data: Any) -> Any:
        """Serialize data with context metadata."""
        payload = data
        
        if self.include_metadata:
            payload = {
                'data': data,
                'metadata': self.metadata
            }
        
        serialized = await self.strategy.serialize(payload)
        
        if self.compression:
            serialized = await self._compress(serialized)
        
        if self.encryption:
            serialized = await self._encrypt(serialized)
        
        return serialized
    
    async def deserialize_with_context(self, serialized_data: Any) -> Any:
        """Deserialize data and extract context."""
        data = serialized_data
        
        if self.encryption:
            data = await self._decrypt(data)
        
        if self.compression:
            data = await self._decompress(data)
        
        deserialized = await self.strategy.deserialize(data)
        
        if self.include_metadata and isinstance(deserialized, dict) and 'data' in deserialized:
            return deserialized['data']
        
        return deserialized
    
    async def _compress(self, data: Union[str, bytes]) -> bytes:
        """Compress data using gzip."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return gzip.compress(data)
    
    async def _decompress(self, data: bytes) -> bytes:
        """Decompress gzip data."""
        return gzip.decompress(data)
    
    async def _encrypt(self, data: Union[str, bytes]) -> bytes:
        """Encrypt data (placeholder for actual encryption)."""
        # Implement actual encryption here
        if isinstance(data, str):
            data = data.encode('utf-8')
        return data
    
    async def _decrypt(self, data: bytes) -> bytes:
        """Decrypt data (placeholder for actual decryption)."""
        # Implement actual decryption here
        return data
```

### Document-to-API Model Transformation
```python
class DocumentTransformer:
    """Transform Elasticsearch documents to API response models."""
    
    def __init__(self):
        self.transformation_rules = {}
        self.field_processors = {}
    
    def register_transformer(
        self,
        document_class: type,
        response_class: type,
        transformation_func: callable = None
    ):
        """Register transformation rule for document type."""
        self.transformation_rules[document_class] = {
            'response_class': response_class,
            'transformation_func': transformation_func
        }
    
    def register_field_processor(self, field_name: str, processor: callable):
        """Register field-specific processor."""
        self.field_processors[field_name] = processor
    
    async def transform_document(
        self,
        document: AsyncDocument,
        include_score: bool = False,
        include_highlights: bool = False,
        custom_fields: Dict[str, Any] = None
    ) -> BaseModel:
        """Transform single document to response model."""
        
        doc_class = type(document)
        
        if doc_class not in self.transformation_rules:
            raise ValueError(f"No transformation rule registered for {doc_class}")
        
        rule = self.transformation_rules[doc_class]
        response_class = rule['response_class']
        transformation_func = rule['transformation_func']
        
        # Extract base data
        data = document.to_dict()
        data['id'] = document.meta.id
        
        # Add metadata if requested
        if include_score and hasattr(document.meta, 'score'):
            data['score'] = document.meta.score
        
        if include_highlights and hasattr(document.meta, 'highlight'):
            data['highlights'] = self._process_highlights(document.meta.highlight)
        
        # Process custom fields
        if custom_fields:
            data.update(custom_fields)
        
        # Apply field processors
        for field_name, value in list(data.items()):
            if field_name in self.field_processors:
                data[field_name] = await self._apply_field_processor(
                    field_name, value
                )
        
        # Apply custom transformation if provided
        if transformation_func:
            data = await transformation_func(data, document)
        
        # Create response model instance
        try:
            return response_class(**data)
        except Exception as e:
            logging.error(f"Failed to create {response_class.__name__}: {str(e)}")
            raise ValueError(f"Transformation failed: {str(e)}")
    
    async def transform_documents(
        self,
        documents: List[AsyncDocument],
        include_score: bool = False,
        include_highlights: bool = False,
        batch_size: int = 100
    ) -> List[BaseModel]:
        """Transform multiple documents in batches."""
        
        results = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self.transform_document(
                    doc,
                    include_score=include_score,
                    include_highlights=include_highlights
                )
                for doc in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and log errors
            for result in batch_results:
                if isinstance(result, Exception):
                    logging.error(f"Document transformation failed: {str(result)}")
                else:
                    results.append(result)
        
        return results
    
    def _process_highlights(self, highlights: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Process Elasticsearch highlight data."""
        processed_highlights = []
        
        for field, fragments in highlights.items():
            processed_highlights.append({
                'field': field,
                'fragments': fragments
            })
        
        return processed_highlights
    
    async def _apply_field_processor(self, field_name: str, value: Any) -> Any:
        """Apply field-specific processor."""
        processor = self.field_processors[field_name]
        
        if asyncio.iscoroutinefunction(processor):
            return await processor(value)
        else:
            return processor(value)

# Example field processors
class FieldProcessors:
    """Common field processors."""
    
    @staticmethod
    def format_currency(value: float) -> str:
        """Format numeric value as currency."""
        return f"${value:,.2f}"
    
    @staticmethod
    def truncate_text(max_length: int = 200):
        """Create text truncation processor."""
        def processor(value: str) -> str:
            if len(value) <= max_length:
                return value
            return value[:max_length] + "..."
        return processor
    
    @staticmethod
    async def resolve_user_reference(value: str) -> Dict[str, str]:
        """Resolve user ID to user information."""
        # This would typically query a user service or cache
        # Placeholder implementation
        return {
            'id': value,
            'name': f"User {value}",
            'avatar_url': f"https://example.com/avatars/{value}"
        }
    
    @staticmethod
    def process_tags(value: List[str]) -> List[Dict[str, str]]:
        """Process tag list into structured format."""
        return [
            {
                'name': tag,
                'slug': tag.lower().replace(' ', '-'),
                'url': f"/tags/{tag.lower().replace(' ', '-')}"
            }
            for tag in value
        ]
```

## Custom Serialization Methods

### Advanced Serialization Techniques
```python
class AdvancedSerializer:
    """Advanced serialization with custom logic and optimizations."""
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis_client = redis_client
        self.serialization_cache = {}
        self.compression_threshold = 1024  # Compress if data > 1KB
    
    async def serialize_search_results(
        self,
        search_response,
        response_model_class: type,
        transformation_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Serialize complete search response with optimizations."""
        
        options = transformation_options or {}
        
        # Extract metadata
        total_hits = search_response.hits.total.value
        max_score = getattr(search_response.hits, 'max_score', None)
        took_ms = getattr(search_response, 'took', 0)
        
        # Transform hits
        hits_data = []
        for hit in search_response.hits:
            hit_data = await self._serialize_hit(
                hit,
                response_model_class,
                options
            )
            hits_data.append(hit_data)
        
        # Process aggregations if present
        aggregations_data = None
        if hasattr(search_response, 'aggregations') and search_response.aggregations:
            aggregations_data = await self._serialize_aggregations(
                search_response.aggregations
            )
        
        # Build response
        response_data = {
            'total': total_hits,
            'max_score': max_score,
            'took_ms': took_ms,
            'hits': hits_data
        }
        
        if aggregations_data:
            response_data['aggregations'] = aggregations_data
        
        # Add pagination info if available
        if 'pagination' in options:
            response_data['pagination'] = options['pagination']
        
        return response_data
    
    async def _serialize_hit(
        self,
        hit,
        response_model_class: type,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Serialize individual search hit."""
        
        # Base data from source
        hit_data = hit.to_dict()
        hit_data['id'] = hit.meta.id
        
        # Add score if available
        if hasattr(hit.meta, 'score') and hit.meta.score is not None:
            hit_data['score'] = round(hit.meta.score, 4)
        
        # Add highlights
        if hasattr(hit.meta, 'highlight') and options.get('include_highlights'):
            hit_data['highlights'] = self._format_highlights(hit.meta.highlight)
        
        # Add explain information for debugging
        if hasattr(hit.meta, 'explanation') and options.get('include_explain'):
            hit_data['explanation'] = hit.meta.explanation
        
        # Apply custom transformations
        if 'transformations' in options:
            for transformation in options['transformations']:
                hit_data = await transformation(hit_data, hit)
        
        # Create model instance if provided
        if response_model_class:
            try:
                model_instance = response_model_class(**hit_data)
                return model_instance.dict()
            except Exception as e:
                logging.warning(f"Failed to create model instance: {str(e)}")
                return hit_data
        
        return hit_data
    
    async def _serialize_aggregations(
        self,
        aggregations
    ) -> Dict[str, Any]:
        """Serialize aggregation results."""
        
        aggs_data = {}
        
        for agg_name, agg_result in aggregations.to_dict().items():
            if 'buckets' in agg_result:
                # Bucket aggregation
                aggs_data[agg_name] = {
                    'type': 'bucket',
                    'buckets': [
                        {
                            'key': bucket['key'],
                            'doc_count': bucket['doc_count'],
                            'key_as_string': bucket.get('key_as_string'),
                            'sub_aggregations': self._extract_sub_aggregations(bucket)
                        }
                        for bucket in agg_result['buckets']
                    ]
                }
            
            elif 'value' in agg_result:
                # Metric aggregation
                aggs_data[agg_name] = {
                    'type': 'metric',
                    'value': agg_result['value']
                }
            
            else:
                # Other aggregation types
                aggs_data[agg_name] = {
                    'type': 'other',
                    'data': agg_result
                }
        
        return aggs_data
    
    def _extract_sub_aggregations(self, bucket: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sub-aggregations from bucket."""
        sub_aggs = {}
        
        for key, value in bucket.items():
            if key not in ['key', 'doc_count', 'key_as_string']:
                if isinstance(value, dict) and 'value' in value:
                    sub_aggs[key] = value['value']
                elif isinstance(value, dict) and 'buckets' in value:
                    sub_aggs[key] = value['buckets']
                else:
                    sub_aggs[key] = value
        
        return sub_aggs
    
    def _format_highlights(self, highlights: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Format highlight data for API response."""
        formatted_highlights = []
        
        for field_name, fragments in highlights.items():
            formatted_highlights.append({
                'field': field_name,
                'fragments': fragments,
                'fragment_count': len(fragments)
            })
        
        return formatted_highlights

class LazySerializer:
    """Lazy serialization for large datasets."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def lazy_serialize_generator(
        self,
        documents: AsyncIterator,
        serializer: callable
    ) -> AsyncIterator[Dict[str, Any]]:
        """Lazily serialize documents as they're consumed."""
        
        batch = []
        
        async for document in documents:
            batch.append(document)
            
            if len(batch) >= self.batch_size:
                # Process batch
                serialized_batch = await self._process_batch(batch, serializer)
                
                for item in serialized_batch:
                    yield item
                
                batch = []
        
        # Process remaining items
        if batch:
            serialized_batch = await self._process_batch(batch, serializer)
            for item in serialized_batch:
                yield item
    
    async def _process_batch(
        self,
        batch: List[Any],
        serializer: callable
    ) -> List[Dict[str, Any]]:
        """Process batch of documents."""
        
        tasks = [serializer(doc) for doc in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if not isinstance(result, Exception):
                valid_results.append(result)
            else:
                logging.error(f"Serialization error: {str(result)}")
        
        return valid_results

class ConditionalSerializer:
    """Serialize data based on conditions and user context."""
    
    def __init__(self):
        self.serialization_rules = {}
    
    def add_rule(
        self,
        condition: callable,
        serializer: callable,
        priority: int = 0
    ):
        """Add conditional serialization rule."""
        self.serialization_rules[condition] = {
            'serializer': serializer,
            'priority': priority
        }
    
    async def serialize_with_conditions(
        self,
        data: Any,
        context: Dict[str, Any]
    ) -> Any:
        """Serialize data based on matching conditions."""
        
        # Find matching rules
        matching_rules = []
        
        for condition, rule in self.serialization_rules.items():
            if await self._evaluate_condition(condition, data, context):
                matching_rules.append(rule)
        
        if not matching_rules:
            # Default serialization
            return data
        
        # Sort by priority and use highest priority rule
        matching_rules.sort(key=lambda x: x['priority'], reverse=True)
        selected_rule = matching_rules[0]
        
        return await selected_rule['serializer'](data, context)
    
    async def _evaluate_condition(
        self,
        condition: callable,
        data: Any,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate condition function."""
        
        if asyncio.iscoroutinefunction(condition):
            return await condition(data, context)
        else:
            return condition(data, context)

# Example conditional serialization rules
class SerializationRules:
    """Example serialization rules."""
    
    @staticmethod
    async def is_admin_user(data: Any, context: Dict[str, Any]) -> bool:
        """Check if user is admin."""
        user_role = context.get('user', {}).get('role')
        return user_role == 'admin'
    
    @staticmethod
    async def is_mobile_client(data: Any, context: Dict[str, Any]) -> bool:
        """Check if client is mobile."""
        user_agent = context.get('request_headers', {}).get('user-agent', '')
        return 'mobile' in user_agent.lower()
    
    @staticmethod
    async def admin_serializer(data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Full serialization for admin users."""
        if hasattr(data, 'dict'):
            return data.dict()
        return data
    
    @staticmethod
    async def mobile_serializer(data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Compact serialization for mobile clients."""
        if hasattr(data, 'dict'):
            full_data = data.dict()
            # Return only essential fields for mobile
            essential_fields = ['id', 'title', 'summary', 'created_date']
            return {k: v for k, v in full_data.items() if k in essential_fields}
        return data
    
    @staticmethod
    async def public_serializer(data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Public serialization - exclude sensitive fields."""
        if hasattr(data, 'dict'):
            full_data = data.dict()
            # Remove sensitive fields
            sensitive_fields = ['email', 'phone', 'internal_notes', 'audit_log']
            return {k: v for k, v in full_data.items() if k not in sensitive_fields}
        return data
```

## Response Formatting

### Structured Response Builders
```python
class ResponseBuilder:
    """Build structured API responses with consistent formatting."""
    
    def __init__(self, include_debug: bool = False):
        self.include_debug = include_debug
        self.response_metadata = {
            'api_version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
            'server': 'elasticsearch-fastapi'
        }
    
    async def build_search_response(
        self,
        hits: List[BaseModel],
        total: int,
        pagination: Dict[str, Any],
        aggregations: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[Dict[str, Any]]] = None,
        debug_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build comprehensive search response."""
        
        response = {
            'success': True,
            'data': {
                'hits': [hit.dict() if hasattr(hit, 'dict') else hit for hit in hits],
                'total': total,
                'pagination': pagination
            },
            'metadata': self.response_metadata.copy()
        }
        
        # Add optional components
        if aggregations:
            response['data']['aggregations'] = aggregations
        
        if suggestions:
            response['data']['suggestions'] = suggestions
        
        # Add debug information for development
        if debug_info and self.include_debug:
            response['debug'] = debug_info
        
        return response
    
    async def build_document_response(
        self,
        document: BaseModel,
        related_data: Optional[Dict[str, Any]] = None,
        computed_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build single document response."""
        
        response = {
            'success': True,
            'data': document.dict() if hasattr(document, 'dict') else document,
            'metadata': self.response_metadata.copy()
        }
        
        if related_data:
            response['data']['related'] = related_data
        
        if computed_fields:
            response['data']['computed'] = computed_fields
        
        return response
    
    async def build_error_response(
        self,
        error_message: str,
        error_code: str = 'GENERAL_ERROR',
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build error response."""
        
        response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': error_message,
                'timestamp': datetime.utcnow().isoformat()
            },
            'metadata': self.response_metadata.copy()
        }
        
        if details:
            response['error']['details'] = details
        
        return response
    
    async def build_bulk_response(
        self,
        successful_operations: List[Dict[str, Any]],
        failed_operations: List[Dict[str, Any]],
        operation_type: str
    ) -> Dict[str, Any]:
        """Build bulk operation response."""
        
        response = {
            'success': len(failed_operations) == 0,
            'data': {
                'operation_type': operation_type,
                'successful_count': len(successful_operations),
                'failed_count': len(failed_operations),
                'successful_operations': successful_operations,
                'failed_operations': failed_operations
            },
            'metadata': self.response_metadata.copy()
        }
        
        return response

class FieldLevelSerializer:
    """Serialize specific fields with custom logic."""
    
    def __init__(self):
        self.field_serializers = {}
    
    def register_field_serializer(
        self,
        field_name: str,
        serializer: callable,
        conditions: Optional[List[callable]] = None
    ):
        """Register field-specific serializer."""
        self.field_serializers[field_name] = {
            'serializer': serializer,
            'conditions': conditions or []
        }
    
    async def serialize_fields(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Apply field-level serialization."""
        
        context = context or {}
        serialized_data = data.copy()
        
        for field_name, value in data.items():
            if field_name in self.field_serializers:
                field_config = self.field_serializers[field_name]
                
                # Check conditions
                should_serialize = True
                for condition in field_config['conditions']:
                    if not await self._evaluate_condition(condition, value, context):
                        should_serialize = False
                        break
                
                if should_serialize:
                    serializer = field_config['serializer']
                    
                    if asyncio.iscoroutinefunction(serializer):
                        serialized_data[field_name] = await serializer(value, context)
                    else:
                        serialized_data[field_name] = serializer(value, context)
        
        return serialized_data
    
    async def _evaluate_condition(
        self,
        condition: callable,
        value: Any,
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate serialization condition."""
        
        if asyncio.iscoroutinefunction(condition):
            return await condition(value, context)
        else:
            return condition(value, context)

class HTMLSanitizer:
    """Sanitize HTML content in responses."""
    
    def __init__(self):
        try:
            import bleach
            self.bleach = bleach
            self.allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a']
            self.allowed_attributes = {'a': ['href', 'title']}
        except ImportError:
            self.bleach = None
            logging.warning("bleach not installed - HTML sanitization disabled")
    
    def sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content."""
        
        if not self.bleach:
            # Basic sanitization without bleach
            return html_content.replace('<script', '&lt;script').replace('javascript:', '')
        
        return self.bleach.clean(
            html_content,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            strip=True
        )
    
    async def sanitize_fields(
        self,
        data: Dict[str, Any],
        html_fields: List[str]
    ) -> Dict[str, Any]:
        """Sanitize HTML fields in data."""
        
        sanitized_data = data.copy()
        
        for field_name in html_fields:
            if field_name in sanitized_data:
                value = sanitized_data[field_name]
                if isinstance(value, str):
                    sanitized_data[field_name] = self.sanitize_html(value)
        
        return sanitized_data

# Response formatting utilities
class ResponseFormatters:
    """Collection of response formatting utilities."""
    
    @staticmethod
    def format_date_fields(
        data: Dict[str, Any],
        date_fields: List[str],
        format_string: str = '%Y-%m-%d %H:%M:%S'
    ) -> Dict[str, Any]:
        """Format date fields in response."""
        
        formatted_data = data.copy()
        
        for field_name in date_fields:
            if field_name in formatted_data:
                value = formatted_data[field_name]
                
                if isinstance(value, datetime):
                    formatted_data[field_name] = value.strftime(format_string)
                elif isinstance(value, str):
                    try:
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        formatted_data[field_name] = dt.strftime(format_string)
                    except ValueError:
                        pass  # Keep original value if parsing fails
        
        return formatted_data
    
    @staticmethod
    def add_computed_fields(
        data: Dict[str, Any],
        computed_fields: Dict[str, callable]
    ) -> Dict[str, Any]:
        """Add computed fields to response."""
        
        enhanced_data = data.copy()
        
        for field_name, compute_func in computed_fields.items():
            try:
                enhanced_data[field_name] = compute_func(data)
            except Exception as e:
                logging.error(f"Failed to compute field {field_name}: {str(e)}")
        
        return enhanced_data
    
    @staticmethod
    def apply_field_masks(
        data: Dict[str, Any],
        field_masks: Dict[str, str]
    ) -> Dict[str, Any]:
        """Apply field masking for sensitive data."""
        
        masked_data = data.copy()
        
        for field_name, mask_pattern in field_masks.items():
            if field_name in masked_data:
                value = str(masked_data[field_name])
                
                if mask_pattern == 'email':
                    # Mask email: example@test.com -> ex****@test.com
                    if '@' in value:
                        local, domain = value.split('@', 1)
                        masked_local = local[:2] + '*' * (len(local) - 2)
                        masked_data[field_name] = f"{masked_local}@{domain}"
                
                elif mask_pattern == 'phone':
                    # Mask phone: +1234567890 -> +123****7890
                    if len(value) > 6:
                        masked_data[field_name] = value[:3] + '*' * (len(value) - 6) + value[-3:]
                
                elif mask_pattern == 'partial':
                    # Generic partial masking
                    if len(value) > 4:
                        masked_data[field_name] = value[:2] + '*' * (len(value) - 4) + value[-2:]
        
        return masked_data
```

## Pagination Patterns

### Advanced Pagination Strategies
```python
class PaginationStrategy(ABC):
    """Abstract base class for pagination strategies."""
    
    @abstractmethod
    async def paginate(
        self,
        search: AsyncSearch,
        page_params: Dict[str, Any]
    ) -> Tuple[AsyncSearch, Dict[str, Any]]:
        """Apply pagination to search and return pagination metadata."""
        pass

class OffsetPagination(PaginationStrategy):
    """Traditional offset-based pagination."""
    
    def __init__(self, max_page_size: int = 100, default_page_size: int = 20):
        self.max_page_size = max_page_size
        self.default_page_size = default_page_size
    
    async def paginate(
        self,
        search: AsyncSearch,
        page_params: Dict[str, Any]
    ) -> Tuple[AsyncSearch, Dict[str, Any]]:
        """Apply offset pagination."""
        
        page = max(1, page_params.get('page', 1))
        size = min(
            self.max_page_size,
            max(1, page_params.get('size', self.default_page_size))
        )
        
        # Calculate offset
        offset = (page - 1) * size
        
        # Apply to search
        paginated_search = search[offset:offset + size]
        
        # Prepare metadata
        metadata = {
            'page': page,
            'size': size,
            'offset': offset,
            'pagination_type': 'offset'
        }
        
        return paginated_search, metadata

class CursorPagination(PaginationStrategy):
    """Cursor-based pagination for stable pagination."""
    
    def __init__(self, default_page_size: int = 20, max_page_size: int = 100):
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
    
    async def paginate(
        self,
        search: AsyncSearch,
        page_params: Dict[str, Any]
    ) -> Tuple[AsyncSearch, Dict[str, Any]]:
        """Apply cursor pagination."""
        
        size = min(
            self.max_page_size,
            max(1, page_params.get('size', self.default_page_size))
        )
        
        cursor_after = page_params.get('cursor_after')
        cursor_before = page_params.get('cursor_before')
        
        # Add search_after or search_before
        if cursor_after:
            search = search.extra(search_after=self._decode_cursor(cursor_after))
        elif cursor_before:
            # For backward pagination, we need to reverse sort and use search_after
            search = self._reverse_sort(search)
            search = search.extra(search_after=self._decode_cursor(cursor_before))
        
        # Set size
        paginated_search = search.extra(size=size)
        
        metadata = {
            'size': size,
            'cursor_after': cursor_after,
            'cursor_before': cursor_before,
            'pagination_type': 'cursor'
        }
        
        return paginated_search, metadata
    
    def _encode_cursor(self, sort_values: List[Any]) -> str:
        """Encode sort values into cursor."""
        import base64
        cursor_data = json.dumps(sort_values)
        return base64.b64encode(cursor_data.encode()).decode()
    
    def _decode_cursor(self, cursor: str) -> List[Any]:
        """Decode cursor into sort values."""
        import base64
        cursor_data = base64.b64decode(cursor.encode()).decode()
        return json.loads(cursor_data)
    
    def _reverse_sort(self, search: AsyncSearch) -> AsyncSearch:
        """Reverse sort order for backward pagination."""
        # This is a simplified implementation
        # In practice, you'd need to handle complex sort configurations
        return search.sort('-_score', '-_id')
    
    async def build_cursor_metadata(
        self,
        hits: List[Any],
        original_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build cursor metadata from search results."""
        
        metadata = original_metadata.copy()
        
        if hits:
            first_hit = hits[0]
            last_hit = hits[-1]
            
            # Extract sort values for cursors
            if hasattr(first_hit, 'meta') and hasattr(first_hit.meta, 'sort'):
                metadata['cursor_first'] = self._encode_cursor(first_hit.meta.sort)
                metadata['cursor_last'] = self._encode_cursor(last_hit.meta.sort)
            
            metadata['has_more'] = len(hits) == original_metadata['size']
        
        return metadata

class StreamPagination(PaginationStrategy):
    """Streaming pagination for real-time data."""
    
    def __init__(self, chunk_size: int = 50):
        self.chunk_size = chunk_size
    
    async def paginate(
        self,
        search: AsyncSearch,
        page_params: Dict[str, Any]
    ) -> Tuple[AsyncSearch, Dict[str, Any]]:
        """Apply streaming pagination."""
        
        size = page_params.get('size', self.chunk_size)
        last_timestamp = page_params.get('last_timestamp')
        
        if last_timestamp:
            # Filter for records after last timestamp
            search = search.filter('range', created_date={'gt': last_timestamp})
        
        # Sort by timestamp for consistent streaming
        search = search.sort('created_date', '_id')
        search = search.extra(size=size)
        
        metadata = {
            'size': size,
            'last_timestamp': last_timestamp,
            'pagination_type': 'stream'
        }
        
        return search, metadata

class SmartPagination:
    """Intelligent pagination that chooses strategy based on context."""
    
    def __init__(self):
        self.strategies = {
            'offset': OffsetPagination(),
            'cursor': CursorPagination(),
            'stream': StreamPagination()
        }
    
    async def paginate(
        self,
        search: AsyncSearch,
        page_params: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Tuple[AsyncSearch, Dict[str, Any]]:
        """Choose and apply appropriate pagination strategy."""
        
        context = context or {}
        
        # Determine best strategy
        strategy_name = self._choose_strategy(page_params, context)
        strategy = self.strategies[strategy_name]
        
        return await strategy.paginate(search, page_params)
    
    def _choose_strategy(
        self,
        page_params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Choose pagination strategy based on parameters and context."""
        
        # Use cursor pagination if cursor parameters present
        if 'cursor_after' in page_params or 'cursor_before' in page_params:
            return 'cursor'
        
        # Use stream pagination for real-time feeds
        if context.get('is_realtime_feed', False):
            return 'stream'
        
        # Use offset pagination for deep pagination needs
        if page_params.get('page', 1) > 100:
            return 'cursor'  # Switch to cursor for deep pagination
        
        # Default to offset pagination
        return 'offset'

class PaginationMetadata:
    """Helper for building comprehensive pagination metadata."""
    
    @staticmethod
    async def build_metadata(
        total_hits: int,
        current_page: int,
        page_size: int,
        pagination_type: str = 'offset',
        **kwargs
    ) -> Dict[str, Any]:
        """Build comprehensive pagination metadata."""
        
        if pagination_type == 'offset':
            total_pages = (total_hits + page_size - 1) // page_size
            
            metadata = {
                'total': total_hits,
                'page': current_page,
                'size': page_size,
                'total_pages': total_pages,
                'has_previous': current_page > 1,
                'has_next': current_page < total_pages,
                'previous_page': current_page - 1 if current_page > 1 else None,
                'next_page': current_page + 1 if current_page < total_pages else None,
                'offset': (current_page - 1) * page_size,
                'pagination_type': 'offset'
            }
        
        elif pagination_type == 'cursor':
            metadata = {
                'size': page_size,
                'has_more': kwargs.get('has_more', False),
                'cursor_first': kwargs.get('cursor_first'),
                'cursor_last': kwargs.get('cursor_last'),
                'pagination_type': 'cursor'
            }
        
        elif pagination_type == 'stream':
            metadata = {
                'size': page_size,
                'last_timestamp': kwargs.get('last_timestamp'),
                'has_more': kwargs.get('has_more', False),
                'pagination_type': 'stream'
            }
        
        else:
            metadata = {
                'size': page_size,
                'pagination_type': pagination_type
            }
        
        return metadata
```

## Streaming Patterns

### Async Streaming Implementation
```python
class StreamingResponseBuilder:
    """Build streaming responses for large datasets."""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
    
    async def stream_search_results(
        self,
        search: AsyncSearch,
        serializer: callable,
        response_format: str = 'json'
    ) -> AsyncIterator[str]:
        """Stream search results as they're processed."""
        
        if response_format == 'json':
            yield '{"hits": ['
            
            first_item = True
            async for hit in self._scroll_search(search):
                serialized_hit = await serializer(hit)
                
                if not first_item:
                    yield ','
                
                yield json.dumps(serialized_hit, separators=(',', ':'))
                first_item = False
            
            yield ']}'
        
        elif response_format == 'ndjson':
            # Newline-delimited JSON
            async for hit in self._scroll_search(search):
                serialized_hit = await serializer(hit)
                yield json.dumps(serialized_hit, separators=(',', ':')) + '\n'
        
        elif response_format == 'csv':
            # CSV format
            header_written = False
            
            async for hit in self._scroll_search(search):
                serialized_hit = await serializer(hit)
                
                if not header_written:
                    # Write CSV header
                    headers = list(serialized_hit.keys())
                    yield ','.join(headers) + '\n'
                    header_written = True
                
                # Write CSV row
                values = [str(serialized_hit.get(h, '')) for h in headers]
                yield ','.join(f'"{v}"' for v in values) + '\n'
    
    async def _scroll_search(self, search: AsyncSearch) -> AsyncIterator:
        """Scroll through search results."""
        
        # Use scroll API for large result sets
        search = search.extra(size=self.chunk_size)
        response = await search.execute()
        
        while response.hits:
            for hit in response.hits:
                yield hit
            
            # Get next batch
            response = await search.scroll()
            if not response.hits:
                break

class RealTimeStreaming:
    """Real-time streaming for live data updates."""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis_client = redis_client
        self.active_streams = {}
    
    async def stream_live_updates(
        self,
        stream_id: str,
        filters: Dict[str, Any] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream live updates matching filters."""
        
        self.active_streams[stream_id] = {
            'filters': filters or {},
            'start_time': datetime.utcnow()
        }
        
        try:
            # Subscribe to Redis channel for updates
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe('elasticsearch_updates')
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        update_data = json.loads(message['data'])
                        
                        # Apply filters
                        if self._matches_filters(update_data, filters):
                            yield {
                                'type': 'update',
                                'data': update_data,
                                'timestamp': datetime.utcnow().isoformat(),
                                'stream_id': stream_id
                            }
                    
                    except json.JSONDecodeError:
                        continue
        
        finally:
            # Cleanup
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
            await pubsub.unsubscribe('elasticsearch_updates')
    
    def _matches_filters(
        self,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """Check if data matches stream filters."""
        
        if not filters:
            return True
        
        for filter_key, filter_value in filters.items():
            if filter_key in data:
                if isinstance(filter_value, list):
                    if data[filter_key] not in filter_value:
                        return False
                else:
                    if data[filter_key] != filter_value:
                        return False
            else:
                return False
        
        return True
    
    async def publish_update(self, update_data: Dict[str, Any]):
        """Publish update to all streams."""
        
        message = json.dumps(update_data)
        await self.redis_client.publish('elasticsearch_updates', message)

class BatchStreamProcessor:
    """Process streams in batches for efficiency."""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.pending_items = []
        self.last_flush = datetime.utcnow()
    
    async def process_stream(
        self,
        stream: AsyncIterator[Any],
        processor: callable
    ) -> AsyncIterator[List[Any]]:
        """Process stream items in batches."""
        
        async for item in stream:
            self.pending_items.append(item)
            
            # Check if we should flush
            should_flush = (
                len(self.pending_items) >= self.batch_size or
                (datetime.utcnow() - self.last_flush).total_seconds() >= self.flush_interval
            )
            
            if should_flush and self.pending_items:
                # Process batch
                batch = self.pending_items.copy()
                self.pending_items.clear()
                self.last_flush = datetime.utcnow()
                
                processed_batch = await processor(batch)
                yield processed_batch
        
        # Process remaining items
        if self.pending_items:
            processed_batch = await processor(self.pending_items)
            yield processed_batch

class CompressionStreamWrapper:
    """Wrap streaming response with compression."""
    
    def __init__(self, compression_type: str = 'gzip'):
        self.compression_type = compression_type
    
    async def compress_stream(
        self,
        stream: AsyncIterator[str]
    ) -> AsyncIterator[bytes]:
        """Compress streaming data."""
        
        if self.compression_type == 'gzip':
            import gzip
            
            async for chunk in stream:
                if chunk:
                    compressed_chunk = gzip.compress(chunk.encode('utf-8'))
                    yield compressed_chunk
        
        else:
            # No compression - just encode to bytes
            async for chunk in stream:
                if chunk:
                    yield chunk.encode('utf-8')
```

## Caching Strategies

### Multi-Level Caching
```python
class SerializationCache:
    """Multi-level caching for serialized responses."""
    
    def __init__(
        self,
        redis_client: aioredis.Redis,
        memory_cache_size: int = 1000,
        default_ttl: int = 3600
    ):
        self.redis_client = redis_client
        self.memory_cache = {}
        self.memory_cache_size = memory_cache_size
        self.default_ttl = default_ttl
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'memory_hits': 0,
            'redis_hits': 0
        }
    
    async def get_cached_response(
        self,
        cache_key: str,
        serialization_context: SerializationContext = None
    ) -> Optional[Any]:
        """Get cached response with fallback levels."""
        
        # Level 1: Memory cache
        if cache_key in self.memory_cache:
            self.cache_stats['hits'] += 1
            self.cache_stats['memory_hits'] += 1
            return self.memory_cache[cache_key]['data']
        
        # Level 2: Redis cache
        try:
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                self.cache_stats['hits'] += 1
                self.cache_stats['redis_hits'] += 1
                
                # Deserialize if context provided
                if serialization_context:
                    if isinstance(cached_data, bytes):
                        cached_data = cached_data.decode('utf-8')
                    
                    data = await serialization_context.deserialize_with_context(cached_data)
                else:
                    data = json.loads(cached_data)
                
                # Store in memory cache for faster access
                await self._store_in_memory_cache(cache_key, data)
                
                return data
        
        except Exception as e:
            logging.error(f"Redis cache retrieval failed: {str(e)}")
        
        self.cache_stats['misses'] += 1
        return None
    
    async def cache_response(
        self,
        cache_key: str,
        data: Any,
        ttl: Optional[int] = None,
        serialization_context: SerializationContext = None
    ):
        """Cache response at multiple levels."""
        
        ttl = ttl or self.default_ttl
        
        # Store in memory cache
        await self._store_in_memory_cache(cache_key, data, ttl)
        
        # Store in Redis cache
        try:
            if serialization_context:
                serialized_data = await serialization_context.serialize_with_context(data)
            else:
                serialized_data = json.dumps(data, default=str)
            
            await self.redis_client.setex(cache_key, ttl, serialized_data)
        
        except Exception as e:
            logging.error(f"Redis cache storage failed: {str(e)}")
    
    async def _store_in_memory_cache(
        self,
        cache_key: str,
        data: Any,
        ttl: int = None
    ):
        """Store data in memory cache with LRU eviction."""
        
        # Check if memory cache is full
        if len(self.memory_cache) >= self.memory_cache_size:
            # Evict oldest item
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]['accessed_at']
            )
            del self.memory_cache[oldest_key]
        
        self.memory_cache[cache_key] = {
            'data': data,
            'created_at': datetime.utcnow(),
            'accessed_at': datetime.utcnow(),
            'ttl': ttl or self.default_ttl
        }
    
    async def invalidate_cache(self, cache_key: str):
        """Invalidate cache at all levels."""
        
        # Remove from memory cache
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        
        # Remove from Redis cache
        try:
            await self.redis_client.delete(cache_key)
        except Exception as e:
            logging.error(f"Redis cache invalidation failed: {str(e)}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        
        # Invalidate memory cache entries
        keys_to_remove = [
            key for key in self.memory_cache.keys()
            if self._matches_pattern(key, pattern)
        ]
        
        for key in keys_to_remove:
            del self.memory_cache[key]
        
        # Invalidate Redis cache entries
        try:
            matching_keys = await self.redis_client.keys(pattern)
            if matching_keys:
                await self.redis_client.delete(*matching_keys)
        except Exception as e:
            logging.error(f"Redis pattern invalidation failed: {str(e)}")
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple wildcard support)."""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_limit': self.memory_cache_size,
            **self.cache_stats
        }

class CacheKeyBuilder:
    """Build consistent cache keys for different scenarios."""
    
    @staticmethod
    def build_search_cache_key(
        query_params: Dict[str, Any],
        user_context: Dict[str, Any] = None,
        include_user_context: bool = False
    ) -> str:
        """Build cache key for search queries."""
        
        # Normalize query parameters
        normalized_params = CacheKeyBuilder._normalize_params(query_params)
        
        # Create base key
        param_string = json.dumps(normalized_params, sort_keys=True, separators=(',', ':'))
        base_key = f"search:{hash(param_string)}"
        
        # Add user context if needed
        if include_user_context and user_context:
            user_hash = hash(json.dumps(user_context, sort_keys=True))
            base_key += f":user:{user_hash}"
        
        return base_key
    
    @staticmethod
    def build_document_cache_key(
        document_id: str,
        document_type: str,
        version: Optional[str] = None
    ) -> str:
        """Build cache key for individual documents."""
        
        base_key = f"doc:{document_type}:{document_id}"
        
        if version:
            base_key += f":v{version}"
        
        return base_key
    
    @staticmethod
    def build_aggregation_cache_key(
        agg_config: Dict[str, Any],
        filters: Dict[str, Any] = None
    ) -> str:
        """Build cache key for aggregation results."""
        
        # Combine aggregation config and filters
        cache_data = {
            'aggregation': agg_config,
            'filters': filters or {}
        }
        
        normalized_data = CacheKeyBuilder._normalize_params(cache_data)
        data_string = json.dumps(normalized_data, sort_keys=True, separators=(',', ':'))
        
        return f"agg:{hash(data_string)}"
    
    @staticmethod
    def _normalize_params(params: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parameters for consistent hashing."""
        
        normalized = {}
        
        for key, value in params.items():
            if isinstance(value, list):
                # Sort lists for consistent ordering
                normalized[key] = sorted(value) if all(isinstance(v, (str, int, float)) for v in value) else value
            elif isinstance(value, dict):
                # Recursively normalize nested dictionaries
                normalized[key] = CacheKeyBuilder._normalize_params(value)
            else:
                normalized[key] = value
        
        return normalized

class SmartCacheInvalidation:
    """Intelligent cache invalidation based on data changes."""
    
    def __init__(self, cache: SerializationCache):
        self.cache = cache
        self.dependency_map = {}  # Maps document IDs to cache keys
    
    def register_cache_dependency(
        self,
        cache_key: str,
        document_ids: List[str]
    ):
        """Register dependency between cache entry and documents."""
        
        for doc_id in document_ids:
            if doc_id not in self.dependency_map:
                self.dependency_map[doc_id] = set()
            
            self.dependency_map[doc_id].add(cache_key)
    
    async def invalidate_dependent_caches(self, document_id: str):
        """Invalidate all caches dependent on a document."""
        
        if document_id in self.dependency_map:
            dependent_keys = self.dependency_map[document_id]
            
            # Invalidate all dependent cache keys
            for cache_key in dependent_keys:
                await self.cache.invalidate_cache(cache_key)
            
            # Remove dependencies
            del self.dependency_map[document_id]
    
    async def invalidate_by_tags(self, tags: List[str]):
        """Invalidate caches by tags."""
        
        for tag in tags:
            pattern = f"*:{tag}:*"
            await self.cache.invalidate_pattern(pattern)
```

## Performance Optimization

### Optimization Strategies
```python
class SerializationOptimizer:
    """Optimize serialization performance."""
    
    def __init__(self):
        self.performance_metrics = {}
        self.optimization_rules = []
    
    async def optimize_serialization(
        self,
        data: Any,
        serialization_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply performance optimizations to serialization."""
        
        optimization_plan = await self._analyze_data(data, serialization_context)
        
        optimized_data = data
        optimizations_applied = []
        
        # Apply field selection optimization
        if optimization_plan['should_filter_fields']:
            optimized_data = await self._apply_field_filtering(
                optimized_data,
                optimization_plan['essential_fields']
            )
            optimizations_applied.append('field_filtering')
        
        # Apply lazy loading optimization
        if optimization_plan['should_lazy_load']:
            optimized_data = await self._apply_lazy_loading(
                optimized_data,
                optimization_plan['lazy_fields']
            )
            optimizations_applied.append('lazy_loading')
        
        # Apply compression optimization
        if optimization_plan['should_compress']:
            optimized_data = await self._apply_compression(optimized_data)
            optimizations_applied.append('compression')
        
        return {
            'data': optimized_data,
            'optimizations_applied': optimizations_applied,
            'estimated_size_reduction': optimization_plan.get('size_reduction', 0)
        }
    
    async def _analyze_data(
        self,
        data: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data to determine optimization strategy."""
        
        analysis = {
            'data_size': self._estimate_size(data),
            'field_count': self._count_fields(data),
            'should_filter_fields': False,
            'should_lazy_load': False,
            'should_compress': False,
            'essential_fields': [],
            'lazy_fields': [],
            'size_reduction': 0
        }
        
        # Determine if field filtering would help
        if analysis['field_count'] > 20:
            analysis['should_filter_fields'] = True
            analysis['essential_fields'] = self._identify_essential_fields(data, context)
        
        # Determine if compression would help
        if analysis['data_size'] > 1024:  # 1KB threshold
            analysis['should_compress'] = True
        
        # Determine if lazy loading would help
        if self._has_large_fields(data):
            analysis['should_lazy_load'] = True
            analysis['lazy_fields'] = self._identify_large_fields(data)
        
        return analysis
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate serialized data size."""
        try:
            return len(json.dumps(data, default=str))
        except:
            return len(str(data))
    
    def _count_fields(self, data: Any) -> int:
        """Count fields in data structure."""
        if isinstance(data, dict):
            return len(data)
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            return len(data[0])
        return 0
    
    def _identify_essential_fields(
        self,
        data: Any,
        context: Dict[str, Any]
    ) -> List[str]:
        """Identify essential fields based on context."""
        
        if not isinstance(data, dict):
            return []
        
        # Always include these fields
        essential = ['id', 'title', 'name', 'created_date', 'updated_date']
        
        # Add context-specific fields
        user_type = context.get('user_type')
        if user_type == 'admin':
            essential.extend(['internal_notes', 'audit_log'])
        elif user_type == 'public':
            essential = [f for f in essential if f not in ['internal_notes', 'audit_log']]
        
        # Return only fields that exist in data
        return [field for field in essential if field in data]
    
    def _has_large_fields(self, data: Any) -> bool:
        """Check if data has large fields suitable for lazy loading."""
        if not isinstance(data, dict):
            return False
        
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 10000:  # 10KB text
                return True
            elif isinstance(value, list) and len(value) > 100:  # Large arrays
                return True
        
        return False
    
    def _identify_large_fields(self, data: Any) -> List[str]:
        """Identify fields suitable for lazy loading."""
        if not isinstance(data, dict):
            return []
        
        large_fields = []
        
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 10000:
                large_fields.append(key)
            elif isinstance(value, list) and len(value) > 100:
                large_fields.append(key)
        
        return large_fields
    
    async def _apply_field_filtering(
        self,
        data: Any,
        essential_fields: List[str]
    ) -> Any:
        """Apply field filtering optimization."""
        
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if k in essential_fields}
        elif isinstance(data, list):
            return [
                {k: v for k, v in item.items() if k in essential_fields}
                if isinstance(item, dict) else item
                for item in data
            ]
        
        return data
    
    async def _apply_lazy_loading(
        self,
        data: Any,
        lazy_fields: List[str]
    ) -> Any:
        """Apply lazy loading by replacing large fields with placeholders."""
        
        if isinstance(data, dict):
            optimized_data = data.copy()
            
            for field in lazy_fields:
                if field in optimized_data:
                    # Replace with lazy loading placeholder
                    optimized_data[field] = {
                        '_lazy': True,
                        '_field': field,
                        '_size': len(str(data[field])),
                        '_url': f"/api/lazy/{field}"
                    }
            
            return optimized_data
        
        return data
    
    async def _apply_compression(self, data: Any) -> Any:
        """Apply compression optimization."""
        
        # This would typically involve compressing large text fields
        # For this example, we'll just indicate compression was applied
        if isinstance(data, dict):
            compressed_data = data.copy()
            compressed_data['_compressed'] = True
            return compressed_data
        
        return data

class PerformanceMonitor:
    """Monitor serialization performance and provide insights."""
    
    def __init__(self):
        self.metrics = {}
        self.thresholds = {
            'slow_serialization_ms': 100,
            'large_response_kb': 100,
            'high_field_count': 50
        }
    
    async def monitor_serialization(
        self,
        operation_id: str,
        start_time: float,
        end_time: float,
        data_size: int,
        field_count: int,
        optimizations_applied: List[str]
    ):
        """Record serialization performance metrics."""
        
        duration_ms = (end_time - start_time) * 1000
        data_size_kb = data_size / 1024
        
        metric = {
            'duration_ms': duration_ms,
            'data_size_kb': data_size_kb,
            'field_count': field_count,
            'optimizations_applied': optimizations_applied,
            'timestamp': datetime.utcnow()
        }
        
        if operation_id not in self.metrics:
            self.metrics[operation_id] = []
        
        self.metrics[operation_id].append(metric)
        
        # Check for performance issues
        await self._check_performance_thresholds(operation_id, metric)
    
    async def _check_performance_thresholds(
        self,
        operation_id: str,
        metric: Dict[str, Any]
    ):
        """Check if performance thresholds are exceeded."""
        
        warnings = []
        
        if metric['duration_ms'] > self.thresholds['slow_serialization_ms']:
            warnings.append(f"Slow serialization: {metric['duration_ms']:.2f}ms")
        
        if metric['data_size_kb'] > self.thresholds['large_response_kb']:
            warnings.append(f"Large response: {metric['data_size_kb']:.2f}KB")
        
        if metric['field_count'] > self.thresholds['high_field_count']:
            warnings.append(f"High field count: {metric['field_count']}")
        
        if warnings:
            logging.warning(f"Performance warning for {operation_id}: {', '.join(warnings)}")
    
    def get_performance_report(
        self,
        operation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate performance report."""
        
        if operation_id:
            metrics = self.metrics.get(operation_id, [])
        else:
            metrics = []
            for op_metrics in self.metrics.values():
                metrics.extend(op_metrics)
        
        if not metrics:
            return {'error': 'No metrics available'}
        
        # Calculate statistics
        durations = [m['duration_ms'] for m in metrics]
        sizes = [m['data_size_kb'] for m in metrics]
        
        report = {
            'total_operations': len(metrics),
            'avg_duration_ms': sum(durations) / len(durations),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations),
            'avg_size_kb': sum(sizes) / len(sizes),
            'max_size_kb': max(sizes),
            'optimizations_frequency': self._calculate_optimization_frequency(metrics),
            'performance_trends': self._calculate_trends(metrics)
        }
        
        return report
    
    def _calculate_optimization_frequency(
        self,
        metrics: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate frequency of applied optimizations."""
        
        optimization_counts = {}
        total_operations = len(metrics)
        
        for metric in metrics:
            for optimization in metric['optimizations_applied']:
                optimization_counts[optimization] = optimization_counts.get(optimization, 0) + 1
        
        return {
            opt: (count / total_operations) * 100
            for opt, count in optimization_counts.items()
        }
    
    def _calculate_trends(self, metrics: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate performance trends."""
        
        if len(metrics) < 2:
            return {'trend': 'insufficient_data'}
        
        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m['timestamp'])
        
        # Compare first half vs second half
        mid_point = len(sorted_metrics) // 2
        first_half = sorted_metrics[:mid_point]
        second_half = sorted_metrics[mid_point:]
        
        first_avg = sum(m['duration_ms'] for m in first_half) / len(first_half)
        second_avg = sum(m['duration_ms'] for m in second_half) / len(second_half)
        
        if second_avg > first_avg * 1.1:
            trend = 'degrading'
        elif second_avg < first_avg * 0.9:
            trend = 'improving'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_percent': ((second_avg - first_avg) / first_avg) * 100
        }
```

## Error Handling

### Comprehensive Error Management
```python
class SerializationError(Exception):
    """Base exception for serialization errors."""
    
    def __init__(self, message: str, field_name: str = None, data_type: str = None):
        self.message = message
        self.field_name = field_name
        self.data_type = data_type
        super().__init__(message)

class SerializationErrorHandler:
    """Handle serialization errors with recovery strategies."""
    
    def __init__(self):
        self.error_handlers = {}
        self.fallback_strategies = {}
        self.error_log = []
    
    def register_error_handler(
        self,
        error_type: type,
        handler: callable,
        priority: int = 0
    ):
        """Register error handler for specific error type."""
        
        if error_type not in self.error_handlers:
            self.error_handlers[error_type] = []
        
        self.error_handlers[error_type].append({
            'handler': handler,
            'priority': priority
        })
        
        # Sort by priority
        self.error_handlers[error_type].sort(
            key=lambda x: x['priority'],
            reverse=True
        )
    
    def register_fallback_strategy(
        self,
        data_type: str,
        strategy: callable
    ):
        """Register fallback strategy for data type."""
        self.fallback_strategies[data_type] = strategy
    
    async def handle_serialization_error(
        self,
        error: Exception,
        data: Any,
        context: Dict[str, Any] = None
    ) -> Any:
        """Handle serialization error with recovery."""
        
        context = context or {}
        error_type = type(error)
        
        # Log error
        self._log_error(error, data, context)
        
        # Try registered handlers
        if error_type in self.error_handlers:
            for handler_info in self.error_handlers[error_type]:
                try:
                    handler = handler_info['handler']
                    
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(error, data, context)
                    else:
                        result = handler(error, data, context)
                    
                    if result is not None:
                        return result
                
                except Exception as handler_error:
                    logging.error(f"Error handler failed: {str(handler_error)}")
                    continue
        
        # Try fallback strategies
        data_type = type(data).__name__
        if data_type in self.fallback_strategies:
            try:
                fallback_strategy = self.fallback_strategies[data_type]
                
                if asyncio.iscoroutinefunction(fallback_strategy):
                    return await fallback_strategy(data, context)
                else:
                    return fallback_strategy(data, context)
            
            except Exception as fallback_error:
                logging.error(f"Fallback strategy failed: {str(fallback_error)}")
        
        # Default fallback - return error representation
        return self._create_error_representation(error, data)
    
    def _log_error(
        self,
        error: Exception,
        data: Any,
        context: Dict[str, Any]
    ):
        """Log serialization error."""
        
        error_record = {
            'timestamp': datetime.utcnow(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'data_type': type(data).__name__,
            'data_size': len(str(data)),
            'context': context
        }
        
        self.error_log.append(error_record)
        
        # Keep only last 1000 error records
        if len(self.error_log) > 1000:
            self.error_log = self.error_log[-1000:]
        
        # Log to standard logger
        logging.error(f"Serialization error: {error_record}")
    
    def _create_error_representation(
        self,
        error: Exception,
        data: Any
    ) -> Dict[str, Any]:
        """Create error representation for failed serialization."""
        
        return {
            'error': True,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'data_type': type(data).__name__,
            'timestamp': datetime.utcnow().isoformat(),
            'fallback_data': self._safe_repr(data)
        }
    
    def _safe_repr(self, data: Any, max_length: int = 200) -> str:
        """Create safe string representation of data."""
        
        try:
            repr_str = repr(data)
            if len(repr_str) > max_length:
                return repr_str[:max_length] + "..."
            return repr_str
        except:
            return f"<{type(data).__name__} object>"
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and patterns."""
        
        if not self.error_log:
            return {'total_errors': 0}
        
        # Count errors by type
        error_types = {}
        data_types = {}
        recent_errors = 0
        
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        for error_record in self.error_log:
            error_type = error_record['error_type']
            data_type = error_record['data_type']
            timestamp = error_record['timestamp']
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            data_types[data_type] = data_types.get(data_type, 0) + 1
            
            if timestamp > one_hour_ago:
                recent_errors += 1
        
        return {
            'total_errors': len(self.error_log),
            'recent_errors_1h': recent_errors,
            'error_types': error_types,
            'data_types': data_types,
            'error_rate_1h': recent_errors / 60  # Errors per minute
        }

# Example error handlers
class SerializationErrorHandlers:
    """Collection of error handlers for common serialization issues."""
    
    @staticmethod
    async def handle_json_error(
        error: json.JSONDecodeError,
        data: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle JSON serialization errors."""
        
        return {
            'json_error': True,
            'position': error.pos if hasattr(error, 'pos') else None,
            'safe_data': str(data)[:1000]  # Truncated safe representation
        }
    
    @staticmethod
    async def handle_unicode_error(
        error: UnicodeError,
        data: Any,
        context: Dict[str, Any]
    ) -> str:
        """Handle Unicode encoding errors."""
        
        if isinstance(data, str):
            # Try to clean the string
            return data.encode('utf-8', errors='replace').decode('utf-8')
        
        return str(data)
    
    @staticmethod
    async def handle_circular_reference(
        error: ValueError,
        data: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle circular reference errors."""
        
        if 'circular reference' in str(error).lower():
            return {
                'circular_reference_error': True,
                'data_type': type(data).__name__,
                'safe_repr': repr(data)[:500]
            }
        
        return None
    
    @staticmethod
    async def handle_memory_error(
        error: MemoryError,
        data: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle memory errors during serialization."""
        
        return {
            'memory_error': True,
            'data_size_estimate': len(str(data)),
            'recommendation': 'Use streaming serialization or pagination'
        }

# Fallback strategies
class FallbackStrategies:
    """Fallback strategies for different data types."""
    
    @staticmethod
    async def dict_fallback(data: dict, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy for dictionary serialization."""
        
        safe_dict = {}
        
        for key, value in data.items():
            try:
                # Try to serialize each field individually
                json.dumps(value, default=str)
                safe_dict[str(key)] = value
            except:
                # Use safe representation for problematic fields
                safe_dict[str(key)] = f"<{type(value).__name__} - serialization failed>"
        
        return safe_dict
    
    @staticmethod
    async def list_fallback(data: list, context: Dict[str, Any]) -> List[Any]:
        """Fallback strategy for list serialization."""
        
        safe_list = []
        
        for item in data:
            try:
                json.dumps(item, default=str)
                safe_list.append(item)
            except:
                safe_list.append(f"<{type(item).__name__} - serialization failed>")
        
        return safe_list
    
    @staticmethod
    async def object_fallback(data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy for complex objects."""
        
        return {
            'object_type': type(data).__name__,
            'string_representation': str(data)[:1000],
            'serialization_failed': True,
            'timestamp': datetime.utcnow().isoformat()
        }
```

## Next Steps

1. **[Performance Optimization](../06-production-patterns/03_performance-optimization.md)** - Advanced performance tuning techniques
2. **[Testing Strategies](../07-testing-deployment/01_testing-strategies.md)** - Testing serialization and API responses
3. **[Monitoring & Logging](../06-production-patterns/01_monitoring-logging.md)** - Production monitoring and observability

## Additional Resources

- **JSON Serialization Best Practices**: [docs.python.org/3/library/json.html](https://docs.python.org/3/library/json.html)
- **FastAPI Response Models**: [fastapi.tiangolo.com/tutorial/response-model](https://fastapi.tiangolo.com/tutorial/response-model/)
- **Pydantic Serialization**: [pydantic-docs.helpmanual.io/usage/exporting_models](https://pydantic-docs.helpmanual.io/usage/exporting_models/)