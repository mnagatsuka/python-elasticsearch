# Schema Design

Designing efficient Elasticsearch schemas for optimal search performance in FastAPI applications with strategic field mapping and index architecture.

## Table of Contents
- [Index Design Principles](#index-design-principles)
- [Field Type Selection](#field-type-selection)
- [Multi-Field Mapping](#multi-field-mapping)
- [Analyzer Selection](#analyzer-selection)
- [Schema Versioning](#schema-versioning)
- [Performance Optimization](#performance-optimization)
- [Template Management](#template-management)
- [Migration Strategies](#migration-strategies)
- [Next Steps](#next-steps)

## Index Design Principles

### Core Design Principles
```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Integer, Float, Date, Boolean, Object, Nested
from elasticsearch_dsl.analysis import StandardAnalyzer, KeywordAnalyzer, CustomAnalyzer
from elasticsearch_dsl.connections import connections
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import asyncio

class SchemaDesignPrinciples:
    """Core principles for Elasticsearch schema design."""
    
    # 1. Query-driven design
    QUERY_DRIVEN = "Design schemas based on query patterns, not just data structure"
    
    # 2. Denormalization for performance
    DENORMALIZE_FOR_READS = "Duplicate data to optimize for read operations"
    
    # 3. Field type optimization
    OPTIMIZE_FIELD_TYPES = "Use most specific field types for better performance"
    
    # 4. Index per use case
    INDEX_PER_USE_CASE = "Separate indices for different query patterns"
    
    # 5. Minimize mapping changes
    MINIMIZE_MAPPING_CHANGES = "Design for future needs to avoid costly reindexing"
    
    @staticmethod
    def get_design_checklist() -> List[str]:
        """Get schema design checklist."""
        return [
            "Identify primary query patterns",
            "Choose appropriate field types",
            "Plan for search, aggregation, and sorting needs",
            "Consider data volume and growth",
            "Design for scalability and performance",
            "Plan schema evolution strategy",
            "Optimize for storage efficiency",
            "Consider security and access patterns"
        ]

class QueryPatternAnalyzer:
    """Analyze query patterns to inform schema design."""
    
    def __init__(self):
        self.query_patterns = {
            'full_text_search': {
                'description': 'Search across multiple text fields',
                'field_requirements': ['Text fields with appropriate analyzers'],
                'performance_impact': 'Medium',
                'schema_considerations': ['Multi-field mapping', 'Analyzer selection']
            },
            'exact_matching': {
                'description': 'Exact term or phrase matching',
                'field_requirements': ['Keyword fields'],
                'performance_impact': 'Low',
                'schema_considerations': ['Keyword mapping', 'Case sensitivity']
            },
            'range_queries': {
                'description': 'Date, numeric, or lexicographic ranges',
                'field_requirements': ['Date, numeric, or keyword fields'],
                'performance_impact': 'Low to Medium',
                'schema_considerations': ['Appropriate data types', 'Index optimization']
            },
            'aggregations': {
                'description': 'Statistical analysis and faceting',
                'field_requirements': ['Keyword or numeric fields'],
                'performance_impact': 'Medium to High',
                'schema_considerations': ['Field data loading', 'Doc values']
            },
            'geospatial': {
                'description': 'Location-based queries',
                'field_requirements': ['Geo-point or geo-shape fields'],
                'performance_impact': 'Medium',
                'schema_considerations': ['Coordinate precision', 'Spatial indexing']
            },
            'nested_queries': {
                'description': 'Queries on nested objects',
                'field_requirements': ['Nested field mapping'],
                'performance_impact': 'High',
                'schema_considerations': ['Nested document structure', 'Query complexity']
            }
        }
    
    def recommend_schema(self, query_patterns: List[str], data_characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend schema based on query patterns."""
        recommendations = {
            'field_mappings': {},
            'index_settings': {},
            'performance_notes': [],
            'trade_offs': []
        }
        
        for pattern in query_patterns:
            if pattern in self.query_patterns:
                pattern_info = self.query_patterns[pattern]
                recommendations['performance_notes'].append(
                    f"{pattern}: {pattern_info['performance_impact']} impact"
                )
        
        # Analyze data characteristics
        if data_characteristics.get('volume') == 'high':
            recommendations['index_settings']['number_of_shards'] = 3
            recommendations['trade_offs'].append("Multiple shards for high volume data")
        
        if 'full_text_search' in query_patterns:
            recommendations['field_mappings']['search_fields'] = 'Use Text with multi-field keyword'
            
        if 'aggregations' in query_patterns:
            recommendations['field_mappings']['agg_fields'] = 'Use Keyword fields for aggregations'
            recommendations['performance_notes'].append("Enable fielddata for Text aggregations carefully")
        
        return recommendations
```

### Schema Design Patterns
```python
class SchemaPattern:
    """Common schema design patterns."""
    
    @staticmethod
    def create_search_optimized_document():
        """Document optimized for search operations."""
        
        class SearchOptimizedDocument(AsyncDocument):
            # Primary content fields with multi-field mapping
            title = Text(
                analyzer='standard',
                fields={
                    'keyword': Keyword(),  # For exact matching and aggregations
                    'suggest': Text(analyzer='simple'),  # For autocomplete
                    'raw': Keyword(normalizer='lowercase')  # For case-insensitive exact match
                }
            )
            
            content = Text(
                analyzer='standard',
                fields={
                    'keyword': Keyword(),
                    'english': Text(analyzer='english'),  # Language-specific analysis
                    'stemmed': Text(analyzer='snowball')  # Stemming for better recall
                }
            )
            
            # Categorical fields for filtering and aggregations
            category = Keyword()
            tags = Keyword()  # Array of keywords
            
            # Temporal fields for range queries
            created_date = Date()
            updated_date = Date()
            
            # Numeric fields for scoring and aggregations
            popularity_score = Float()
            view_count = Integer()
            
            # Boolean fields for filtering
            is_published = Boolean()
            is_featured = Boolean()
            
            # Hierarchical data
            category_path = Keyword()  # e.g., "technology/programming/python"
            
            class Index:
                name = 'search_optimized'
                settings = {
                    'number_of_shards': 1,
                    'number_of_replicas': 1,
                    'analysis': {
                        'normalizer': {
                            'lowercase': {
                                'type': 'custom',
                                'filter': ['lowercase']
                            }
                        },
                        'analyzer': {
                            'english': {
                                'type': 'english'
                            },
                            'snowball': {
                                'type': 'snowball',
                                'language': 'English'
                            }
                        }
                    }
                }
        
        return SearchOptimizedDocument
    
    @staticmethod
    def create_analytics_optimized_document():
        """Document optimized for analytics and aggregations."""
        
        class AnalyticsDocument(AsyncDocument):
            # Dimensions for aggregations (all keywords)
            user_id = Keyword()
            session_id = Keyword()
            page_url = Keyword()
            referrer = Keyword()
            user_agent = Keyword()
            country = Keyword()
            city = Keyword()
            device_type = Keyword()
            
            # Metrics for calculations
            page_load_time = Float()
            time_on_page = Integer()
            scroll_depth = Float()
            
            # Temporal dimensions
            timestamp = Date()
            hour_of_day = Integer()
            day_of_week = Keyword()
            
            # Hierarchical dimensions
            content_category = Keyword()
            content_subcategory = Keyword()
            
            # Boolean flags
            is_bounce = Boolean()
            is_conversion = Boolean()
            
            class Index:
                name = 'analytics'
                settings = {
                    'number_of_shards': 2,
                    'number_of_replicas': 0,  # Analytics data often doesn't need replication
                    'refresh_interval': '30s',  # Less frequent refresh for better indexing performance
                    'index': {
                        'codec': 'best_compression'  # Optimize for storage
                    }
                }
        
        return AnalyticsDocument
    
    @staticmethod
    def create_e_commerce_document():
        """Document optimized for e-commerce search."""
        
        class ProductDocument(AsyncDocument):
            # Core product information
            name = Text(
                analyzer='standard',
                fields={
                    'keyword': Keyword(),
                    'suggest': Text(analyzer='simple'),
                    'search': Text(analyzer='custom_product_analyzer')
                }
            )
            
            description = Text(analyzer='standard')
            
            # Product identification
            sku = Keyword()
            brand = Keyword()
            model = Keyword()
            
            # Categorization
            category = Keyword()
            subcategory = Keyword()
            category_hierarchy = Keyword()  # Full path
            
            # Pricing and inventory
            price = Float()
            sale_price = Float()
            currency = Keyword()
            in_stock = Boolean()
            stock_quantity = Integer()
            
            # Product attributes for faceted search
            color = Keyword()
            size = Keyword()
            material = Keyword()
            features = Keyword()  # Array of features
            
            # Ratings and reviews
            average_rating = Float()
            review_count = Integer()
            
            # Temporal data
            release_date = Date()
            last_updated = Date()
            
            # Search optimization
            search_keywords = Text(analyzer='keyword')  # Manually curated keywords
            popularity_score = Float()  # For boosting popular products
            
            class Index:
                name = 'products'
                settings = {
                    'number_of_shards': 1,
                    'number_of_replicas': 1,
                    'analysis': {
                        'analyzer': {
                            'custom_product_analyzer': {
                                'type': 'custom',
                                'tokenizer': 'standard',
                                'filter': [
                                    'lowercase',
                                    'stop',
                                    'synonym_filter',
                                    'stemmer'
                                ]
                            }
                        },
                        'filter': {
                            'synonym_filter': {
                                'type': 'synonym',
                                'synonyms': [
                                    'laptop,notebook,computer',
                                    'mobile,phone,smartphone',
                                    'tv,television,display'
                                ]
                            }
                        }
                    }
                }
        
        return ProductDocument
```

## Field Type Selection

### Field Type Decision Matrix
```python
class FieldTypeSelector:
    """Helper for selecting appropriate field types."""
    
    @staticmethod
    def get_field_type_matrix() -> Dict[str, Dict[str, Any]]:
        """Get comprehensive field type selection matrix."""
        return {
            'text': {
                'use_cases': ['Full-text search', 'Natural language content'],
                'features': ['Analyzed', 'Searchable', 'Not aggregatable by default'],
                'performance': 'Good for search, poor for aggregations',
                'storage': 'Higher due to analysis',
                'examples': ['Article content', 'Product descriptions', 'Comments']
            },
            'keyword': {
                'use_cases': ['Exact matching', 'Aggregations', 'Sorting'],
                'features': ['Not analyzed', 'Exact match only', 'Aggregatable'],
                'performance': 'Excellent for exact match and aggregations',
                'storage': 'Lower, stored as-is',
                'examples': ['IDs', 'Status values', 'Categories', 'Tags']
            },
            'integer': {
                'use_cases': ['Whole numbers', 'Counts', 'Rankings'],
                'features': ['Numeric operations', 'Range queries', 'Aggregatable'],
                'performance': 'Excellent for numeric operations',
                'storage': 'Efficient',
                'examples': ['Age', 'Quantity', 'Score', 'Year']
            },
            'float': {
                'use_cases': ['Decimal numbers', 'Measurements', 'Scores'],
                'features': ['Precision handling', 'Numeric operations'],
                'performance': 'Good, slightly slower than integer',
                'storage': 'Efficient',
                'examples': ['Price', 'Rating', 'Distance', 'Percentage']
            },
            'date': {
                'use_cases': ['Timestamps', 'Date ranges', 'Time-based queries'],
                'features': ['Date parsing', 'Range queries', 'Date math'],
                'performance': 'Good for temporal queries',
                'storage': 'Efficient (stored as long)',
                'examples': ['Created date', 'Event time', 'Expiry date']
            },
            'boolean': {
                'use_cases': ['True/false values', 'Flags', 'Binary states'],
                'features': ['Boolean logic', 'Filtering'],
                'performance': 'Excellent',
                'storage': 'Very efficient',
                'examples': ['Is active', 'Is featured', 'Has discount']
            },
            'geo_point': {
                'use_cases': ['Geographic coordinates', 'Location-based search'],
                'features': ['Geospatial queries', 'Distance calculations'],
                'performance': 'Good for geo queries',
                'storage': 'Moderate',
                'examples': ['Store location', 'User position', 'Event venue']
            },
            'nested': {
                'use_cases': ['Complex objects', 'One-to-many relationships'],
                'features': ['Independent object queries', 'Complex relationships'],
                'performance': 'Higher query cost',
                'storage': 'Higher due to separate documents',
                'examples': ['Order items', 'Comments with metadata', 'Product variants']
            }
        }
    
    @staticmethod
    def recommend_field_type(
        data_type: str,
        use_cases: List[str],
        data_characteristics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recommend field type based on requirements."""
        
        recommendations = {
            'primary_type': None,
            'multi_field_suggestions': [],
            'reasoning': [],
            'performance_notes': []
        }
        
        # Basic type mapping
        type_mapping = {
            'string': 'text',
            'number': 'integer' if data_characteristics.get('is_integer') else 'float',
            'datetime': 'date',
            'boolean': 'boolean',
            'location': 'geo_point',
            'array_of_objects': 'nested'
        }
        
        recommendations['primary_type'] = type_mapping.get(data_type, 'keyword')
        
        # Add multi-field suggestions based on use cases
        if 'search' in use_cases and recommendations['primary_type'] == 'text':
            recommendations['multi_field_suggestions'].append('keyword')
            recommendations['reasoning'].append('Keyword field for exact matching and aggregations')
        
        if 'aggregation' in use_cases and recommendations['primary_type'] == 'text':
            recommendations['multi_field_suggestions'].append('keyword')
            recommendations['reasoning'].append('Keyword field required for aggregations')
        
        if 'sorting' in use_cases and recommendations['primary_type'] == 'text':
            recommendations['multi_field_suggestions'].append('keyword')
            recommendations['reasoning'].append('Keyword field for efficient sorting')
        
        if 'autocomplete' in use_cases:
            recommendations['multi_field_suggestions'].append('completion')
            recommendations['reasoning'].append('Completion field for fast autocomplete')
        
        # Performance considerations
        if data_characteristics.get('high_cardinality'):
            recommendations['performance_notes'].append(
                'High cardinality field - consider impact on aggregations'
            )
        
        if data_characteristics.get('frequent_updates'):
            recommendations['performance_notes'].append(
                'Frequent updates - minimize complex field mappings'
            )
        
        return recommendations

class FieldMappingBuilder:
    """Builder for creating optimized field mappings."""
    
    def __init__(self):
        self.mappings = {}
    
    def add_search_field(
        self,
        field_name: str,
        analyzer: str = 'standard',
        include_keyword: bool = True,
        include_suggest: bool = False
    ) -> 'FieldMappingBuilder':
        """Add a field optimized for search."""
        
        field_config = Text(analyzer=analyzer)
        multi_fields = {}
        
        if include_keyword:
            multi_fields['keyword'] = Keyword()
        
        if include_suggest:
            multi_fields['suggest'] = Text(analyzer='simple')
        
        if multi_fields:
            field_config = Text(analyzer=analyzer, fields=multi_fields)
        
        self.mappings[field_name] = field_config
        return self
    
    def add_categorical_field(
        self,
        field_name: str,
        include_text_search: bool = False
    ) -> 'FieldMappingBuilder':
        """Add a categorical field for filtering and aggregations."""
        
        if include_text_search:
            self.mappings[field_name] = Keyword(
                fields={
                    'text': Text(analyzer='standard')
                }
            )
        else:
            self.mappings[field_name] = Keyword()
        
        return self
    
    def add_numeric_field(
        self,
        field_name: str,
        field_type: str = 'integer',
        include_keyword: bool = False
    ) -> 'FieldMappingBuilder':
        """Add a numeric field."""
        
        field_class = Integer if field_type == 'integer' else Float
        
        if include_keyword:
            self.mappings[field_name] = field_class(
                fields={
                    'keyword': Keyword()
                }
            )
        else:
            self.mappings[field_name] = field_class()
        
        return self
    
    def add_date_field(
        self,
        field_name: str,
        format_string: str = None,
        include_keyword: bool = False
    ) -> 'FieldMappingBuilder':
        """Add a date field."""
        
        field_config = Date()
        if format_string:
            field_config = Date(format=format_string)
        
        if include_keyword:
            field_config = Date(
                format=format_string,
                fields={
                    'keyword': Keyword()
                }
            )
        
        self.mappings[field_name] = field_config
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the final mapping configuration."""
        return self.mappings
```

## Multi-Field Mapping

### Advanced Multi-Field Strategies
```python
class MultiFieldStrategy:
    """Strategies for multi-field mapping."""
    
    @staticmethod
    def create_comprehensive_text_field(field_name: str, content_type: str = 'general') -> Dict[str, Any]:
        """Create comprehensive text field with multiple analysis strategies."""
        
        base_config = {
            'type': 'text',
            'analyzer': 'standard',
            'fields': {}
        }
        
        # Always include keyword for exact matching
        base_config['fields']['keyword'] = {'type': 'keyword'}
        
        # Content-specific configurations
        if content_type == 'product':
            base_config['fields'].update({
                'search': {
                    'type': 'text',
                    'analyzer': 'product_search_analyzer'
                },
                'suggest': {
                    'type': 'completion',
                    'max_input_length': 50
                },
                'ngram': {
                    'type': 'text',
                    'analyzer': 'ngram_analyzer'
                }
            })
        
        elif content_type == 'article':
            base_config['fields'].update({
                'english': {
                    'type': 'text',
                    'analyzer': 'english'
                },
                'stemmed': {
                    'type': 'text',
                    'analyzer': 'stemmed_analyzer'
                },
                'exact': {
                    'type': 'text',
                    'analyzer': 'keyword'
                }
            })
        
        elif content_type == 'user_content':
            base_config['fields'].update({
                'clean': {
                    'type': 'text',
                    'analyzer': 'clean_text_analyzer'
                },
                'hashtags': {
                    'type': 'text',
                    'analyzer': 'hashtag_analyzer'
                },
                'mentions': {
                    'type': 'text',
                    'analyzer': 'mention_analyzer'
                }
            })
        
        return {field_name: base_config}
    
    @staticmethod
    def create_hierarchical_field(field_name: str, levels: List[str]) -> Dict[str, Any]:
        """Create field for hierarchical data (e.g., category paths)."""
        
        field_config = {
            'type': 'keyword',
            'fields': {
                'tree': {
                    'type': 'text',
                    'analyzer': 'path_hierarchy'
                }
            }
        }
        
        # Add level-specific fields
        for i, level in enumerate(levels):
            field_config['fields'][f'level_{i}'] = {
                'type': 'keyword'
            }
        
        return {field_name: field_config}
    
    @staticmethod
    def create_searchable_id_field(field_name: str) -> Dict[str, Any]:
        """Create ID field that supports both exact matching and partial search."""
        
        return {
            field_name: {
                'type': 'keyword',
                'fields': {
                    'search': {
                        'type': 'text',
                        'analyzer': 'id_search_analyzer'
                    },
                    'prefix': {
                        'type': 'text',
                        'analyzer': 'prefix_analyzer'
                    }
                }
            }
        }

class AdvancedMappingDocument(AsyncDocument):
    """Document demonstrating advanced multi-field mapping strategies."""
    
    # Comprehensive title field for different search strategies
    title = Text(
        analyzer='standard',
        fields={
            'keyword': Keyword(),  # Exact matching
            'suggest': Text(analyzer='simple'),  # Autocomplete
            'english': Text(analyzer='english'),  # Language-specific
            'shingles': Text(analyzer='shingle_analyzer'),  # Phrase matching
            'edge_ngram': Text(analyzer='edge_ngram_analyzer'),  # Partial matching
            'raw': Keyword(normalizer='lowercase')  # Case-insensitive exact
        }
    )
    
    # Content field with language and style analysis
    content = Text(
        analyzer='standard',
        fields={
            'keyword': Keyword(),
            'english': Text(analyzer='english'),
            'stemmed': Text(analyzer='stemmer'),
            'phonetic': Text(analyzer='phonetic_analyzer'),  # Sound-alike matching
            'minimal': Text(analyzer='minimal_analyzer')  # Minimal processing
        }
    )
    
    # Hierarchical category field
    category = Keyword(
        fields={
            'hierarchy': Text(analyzer='path_hierarchy'),  # For hierarchical queries
            'suggest': Text(analyzer='completion')  # For category suggestions
        }
    )
    
    # Numeric field with string representation
    price = Float(
        fields={
            'keyword': Keyword(),  # For exact price matching
            'range': Keyword()  # For price range labels
        }
    )
    
    # Date field with multiple formats
    created_date = Date(
        fields={
            'year': Date(format='yyyy'),
            'month': Date(format='yyyy-MM'),
            'keyword': Keyword()  # For exact date matching
        }
    )
    
    # Complex user field
    author = Keyword(
        fields={
            'search': Text(analyzer='name_analyzer'),  # For name searching
            'suggest': Text(analyzer='completion'),  # For author suggestions
            'initials': Keyword(normalizer='initials_normalizer')  # For initial matching
        }
    )
    
    class Index:
        name = 'advanced_mapping'
        settings = {
            'analysis': {
                'analyzer': {
                    'shingle_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'shingle_filter']
                    },
                    'edge_ngram_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'edge_ngram_filter']
                    },
                    'phonetic_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'phonetic_filter']
                    },
                    'path_hierarchy': {
                        'type': 'custom',
                        'tokenizer': 'path_hierarchy_tokenizer'
                    },
                    'name_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['lowercase', 'name_filter']
                    }
                },
                'filter': {
                    'shingle_filter': {
                        'type': 'shingle',
                        'min_shingle_size': 2,
                        'max_shingle_size': 3
                    },
                    'edge_ngram_filter': {
                        'type': 'edge_ngram',
                        'min_gram': 1,
                        'max_gram': 20
                    },
                    'phonetic_filter': {
                        'type': 'phonetic',
                        'encoder': 'double_metaphone'
                    },
                    'name_filter': {
                        'type': 'word_delimiter_graph',
                        'preserve_original': True
                    }
                },
                'tokenizer': {
                    'path_hierarchy_tokenizer': {
                        'type': 'path_hierarchy',
                        'delimiter': '/'
                    }
                },
                'normalizer': {
                    'lowercase': {
                        'type': 'custom',
                        'filter': ['lowercase']
                    },
                    'initials_normalizer': {
                        'type': 'custom',
                        'filter': ['uppercase', 'initials_filter']
                    }
                }
            }
        }
```

## Analyzer Selection

### Custom Analyzer Design
```python
class AnalyzerDesigner:
    """Design custom analyzers for specific use cases."""
    
    @staticmethod
    def create_search_analyzer(domain: str) -> Dict[str, Any]:
        """Create domain-specific search analyzer."""
        
        analyzers = {
            'ecommerce': {
                'product_search': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'stop',
                        'synonym_filter',
                        'stemmer',
                        'product_specific_filter'
                    ]
                }
            },
            'content': {
                'article_search': {
                    'type': 'custom',
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'stop',
                        'stemmer',
                        'language_specific_filter'
                    ]
                }
            },
            'social': {
                'social_content': {
                    'type': 'custom',
                    'tokenizer': 'whitespace',
                    'filter': [
                        'lowercase',
                        'hashtag_filter',
                        'mention_filter',
                        'emoticon_filter'
                    ]
                }
            }
        }
        
        return analyzers.get(domain, {})
    
    @staticmethod
    def create_autocomplete_analyzer() -> Dict[str, Any]:
        """Create analyzer optimized for autocomplete functionality."""
        
        return {
            'autocomplete_index': {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': [
                    'lowercase',
                    'edge_ngram_autocomplete'
                ]
            },
            'autocomplete_search': {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': [
                    'lowercase'
                ]
            }
        }
    
    @staticmethod
    def create_multilingual_analyzer(languages: List[str]) -> Dict[str, Any]:
        """Create analyzer for multilingual content."""
        
        analyzers = {}
        
        for lang in languages:
            analyzers[f'{lang}_analyzer'] = {
                'type': lang if lang in ['english', 'spanish', 'french', 'german'] else 'standard',
                'stopwords': f'_{lang}_' if lang != 'english' else '_english_'
            }
        
        # Universal analyzer for mixed content
        analyzers['universal'] = {
            'type': 'custom',
            'tokenizer': 'icu_tokenizer',
            'filter': [
                'icu_folding',
                'icu_normalizer',
                'lowercase'
            ]
        }
        
        return analyzers

class AnalyzerService:
    """Service for managing analyzer performance and optimization."""
    
    @staticmethod
    async def test_analyzer_performance(
        index_name: str,
        analyzer_name: str,
        test_texts: List[str]
    ) -> Dict[str, Any]:
        """Test analyzer performance with sample texts."""
        
        try:
            from elasticsearch import AsyncElasticsearch
            es = AsyncElasticsearch()
            
            results = {
                'analyzer': analyzer_name,
                'test_results': [],
                'performance_metrics': {}
            }
            
            total_tokens = 0
            total_time = 0
            
            for text in test_texts:
                start_time = asyncio.get_event_loop().time()
                
                response = await es.indices.analyze(
                    index=index_name,
                    body={
                        'analyzer': analyzer_name,
                        'text': text
                    }
                )
                
                end_time = asyncio.get_event_loop().time()
                processing_time = end_time - start_time
                
                tokens = response['tokens']
                
                results['test_results'].append({
                    'input_text': text[:100] + '...' if len(text) > 100 else text,
                    'input_length': len(text),
                    'token_count': len(tokens),
                    'processing_time_ms': processing_time * 1000,
                    'tokens': [token['token'] for token in tokens[:10]]  # First 10 tokens
                })
                
                total_tokens += len(tokens)
                total_time += processing_time
            
            results['performance_metrics'] = {
                'avg_tokens_per_text': total_tokens / len(test_texts),
                'avg_processing_time_ms': (total_time / len(test_texts)) * 1000,
                'tokens_per_second': total_tokens / total_time if total_time > 0 else 0
            }
            
            return results
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Analyzer testing failed: {str(e)}"
            )
    
    @staticmethod
    def recommend_analyzer_optimizations(
        analyzer_config: Dict[str, Any],
        use_case: str,
        performance_requirements: Dict[str, Any]
    ) -> List[str]:
        """Recommend analyzer optimizations."""
        
        recommendations = []
        
        # Performance-based recommendations
        if performance_requirements.get('speed') == 'high':
            recommendations.append("Consider using simpler tokenizers")
            recommendations.append("Reduce number of filters in analyzer chain")
            recommendations.append("Use built-in analyzers when possible")
        
        if performance_requirements.get('accuracy') == 'high':
            recommendations.append("Add synonym filters for better matching")
            recommendations.append("Include language-specific stemming")
            recommendations.append("Consider phonetic matching for names")
        
        # Use case specific recommendations
        if use_case == 'autocomplete':
            recommendations.append("Use edge n-gram tokenizer")
            recommendations.append("Avoid heavy stemming for autocomplete")
            recommendations.append("Consider completion suggester instead")
        
        elif use_case == 'search':
            recommendations.append("Include stemming for better recall")
            recommendations.append("Add stop word removal")
            recommendations.append("Consider shingle tokens for phrase matching")
        
        elif use_case == 'aggregation':
            recommendations.append("Use keyword fields instead of analyzed text")
            recommendations.append("Consider normalizers for case-insensitive aggregation")
        
        return recommendations
```

## Schema Versioning

### Version Management Strategy
```python
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class SchemaVersion:
    """Schema version management."""
    
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.version_string = f"{major}.{minor}.{patch}"
    
    def __str__(self):
        return self.version_string
    
    def is_compatible_with(self, other: 'SchemaVersion') -> bool:
        """Check if this version is compatible with another."""
        # Major version changes are breaking
        if self.major != other.major:
            return False
        
        # Minor version increases are backward compatible
        if self.minor > other.minor:
            return True
        
        # Same minor version, patch differences are compatible
        return self.minor == other.minor

class SchemaChange:
    """Represents a schema change."""
    
    def __init__(
        self,
        change_type: str,
        field_name: str,
        old_config: Optional[Dict[str, Any]] = None,
        new_config: Optional[Dict[str, Any]] = None,
        requires_reindex: bool = False
    ):
        self.change_type = change_type  # 'add', 'remove', 'modify'
        self.field_name = field_name
        self.old_config = old_config
        self.new_config = new_config
        self.requires_reindex = requires_reindex
        self.timestamp = datetime.utcnow()

class SchemaEvolutionManager:
    """Manage schema evolution and migrations."""
    
    def __init__(self):
        self.version_history = {}
        self.change_log = []
    
    def add_schema_version(
        self,
        version: SchemaVersion,
        schema_definition: Dict[str, Any],
        changes: List[SchemaChange] = None
    ):
        """Add a new schema version."""
        
        self.version_history[version.version_string] = {
            'version': version,
            'schema': schema_definition,
            'changes': changes or [],
            'created_date': datetime.utcnow()
        }
        
        if changes:
            self.change_log.extend(changes)
    
    def plan_migration(
        self,
        from_version: SchemaVersion,
        to_version: SchemaVersion
    ) -> Dict[str, Any]:
        """Plan migration between schema versions."""
        
        migration_plan = {
            'from_version': from_version.version_string,
            'to_version': to_version.version_string,
            'requires_reindex': False,
            'migration_steps': [],
            'breaking_changes': [],
            'warnings': []
        }
        
        # Find changes between versions
        from_schema = self.version_history.get(from_version.version_string)
        to_schema = self.version_history.get(to_version.version_string)
        
        if not from_schema or not to_schema:
            raise ValueError("Version not found in history")
        
        # Analyze changes
        for change in to_schema['changes']:
            if change.requires_reindex:
                migration_plan['requires_reindex'] = True
                migration_plan['migration_steps'].append({
                    'type': 'reindex',
                    'reason': f"Field {change.field_name} {change.change_type}"
                })
            
            if change.change_type == 'remove':
                migration_plan['breaking_changes'].append({
                    'type': 'field_removed',
                    'field': change.field_name,
                    'impact': 'Data loss possible'
                })
            
            elif change.change_type == 'modify':
                migration_plan['warnings'].append({
                    'type': 'field_modified',
                    'field': change.field_name,
                    'recommendation': 'Test queries and applications'
                })
        
        return migration_plan
    
    def validate_schema_compatibility(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate compatibility between schema versions."""
        
        compatibility_report = {
            'is_compatible': True,
            'breaking_changes': [],
            'warnings': [],
            'recommendations': []
        }
        
        old_fields = old_schema.get('properties', {})
        new_fields = new_schema.get('properties', {})
        
        # Check for removed fields
        for field_name in old_fields:
            if field_name not in new_fields:
                compatibility_report['is_compatible'] = False
                compatibility_report['breaking_changes'].append({
                    'type': 'field_removed',
                    'field': field_name,
                    'impact': 'Existing queries may fail'
                })
        
        # Check for field type changes
        for field_name, field_config in new_fields.items():
            if field_name in old_fields:
                old_config = old_fields[field_name]
                
                # Check type changes
                if old_config.get('type') != field_config.get('type'):
                    compatibility_report['warnings'].append({
                        'type': 'field_type_changed',
                        'field': field_name,
                        'old_type': old_config.get('type'),
                        'new_type': field_config.get('type')
                    })
        
        return compatibility_report

class VersionedDocument(AsyncDocument):
    """Base class for versioned documents."""
    
    # Schema metadata
    schema_version = Keyword()
    schema_created_date = Date()
    schema_migration_history = Object()
    
    @classmethod
    def get_current_version(cls) -> SchemaVersion:
        """Get current schema version."""
        # This would be implemented by subclasses
        return SchemaVersion(1, 0, 0)
    
    @classmethod
    async def migrate_document(
        cls,
        doc_id: str,
        from_version: SchemaVersion,
        to_version: SchemaVersion
    ) -> bool:
        """Migrate a document between schema versions."""
        try:
            # Get existing document
            doc = await cls.get(doc_id)
            
            # Apply migration logic based on version differences
            migration_applied = False
            
            if from_version.major < to_version.major:
                # Major version migration - custom logic needed
                migration_applied = await cls._apply_major_migration(doc, from_version, to_version)
            
            elif from_version.minor < to_version.minor:
                # Minor version migration - usually additive
                migration_applied = await cls._apply_minor_migration(doc, from_version, to_version)
            
            if migration_applied:
                # Update version metadata
                doc.schema_version = to_version.version_string
                doc.schema_migration_history = {
                    'last_migration': datetime.utcnow(),
                    'from_version': from_version.version_string,
                    'to_version': to_version.version_string
                }
                
                await doc.save()
            
            return migration_applied
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Document migration failed: {str(e)}"
            )
    
    @classmethod
    async def _apply_major_migration(
        cls,
        doc: 'VersionedDocument',
        from_version: SchemaVersion,
        to_version: SchemaVersion
    ) -> bool:
        """Apply major version migration logic."""
        # Implement custom migration logic
        return False
    
    @classmethod
    async def _apply_minor_migration(
        cls,
        doc: 'VersionedDocument',
        from_version: SchemaVersion,
        to_version: SchemaVersion
    ) -> bool:
        """Apply minor version migration logic."""
        # Implement custom migration logic
        return False
```

## Performance Optimization

### Query Performance Optimization
```python
class QueryPerformanceOptimizer:
    """Optimize queries for better performance."""
    
    @staticmethod
    def optimize_search_query(
        query_config: Dict[str, Any],
        index_characteristics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize search query based on index characteristics."""
        
        optimized_query = query_config.copy()
        optimizations_applied = []
        
        # Optimize based on data volume
        if index_characteristics.get('document_count', 0) > 1000000:
            # Large index optimizations
            optimized_query['timeout'] = '30s'
            optimized_query['terminate_after'] = 100000
            optimizations_applied.append("Added timeout and terminate_after for large index")
        
        # Optimize based on field characteristics
        if index_characteristics.get('high_cardinality_fields'):
            # Avoid aggregations on high cardinality fields
            if 'aggs' in optimized_query:
                for agg_name, agg_config in optimized_query['aggs'].items():
                    if agg_config.get('field') in index_characteristics['high_cardinality_fields']:
                        optimized_query['aggs'][agg_name]['size'] = 10  # Limit bucket size
                        optimizations_applied.append(f"Limited aggregation size for {agg_name}")
        
        # Optimize source filtering
        if not optimized_query.get('_source'):
            optimized_query['_source'] = {
                'excludes': ['large_text_field', 'binary_data', 'debug_info']
            }
            optimizations_applied.append("Added source filtering to exclude large fields")
        
        # Add query optimizations
        if 'query' in optimized_query:
            optimized_query['query'] = QueryPerformanceOptimizer._optimize_query_clause(
                optimized_query['query']
            )
            optimizations_applied.append("Optimized query clauses")
        
        return {
            'optimized_query': optimized_query,
            'optimizations_applied': optimizations_applied
        }
    
    @staticmethod
    def _optimize_query_clause(query_clause: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize individual query clauses."""
        
        optimized_clause = query_clause.copy()
        
        # Optimize bool queries
        if 'bool' in query_clause:
            bool_query = query_clause['bool']
            
            # Move filters to filter context for better caching
            if 'must' in bool_query:
                must_clauses = bool_query['must']
                filter_clauses = bool_query.get('filter', [])
                
                # Move exact match queries to filter context
                new_must = []
                for clause in must_clauses:
                    if 'term' in clause or 'terms' in clause or 'range' in clause:
                        filter_clauses.append(clause)
                    else:
                        new_must.append(clause)
                
                optimized_clause['bool']['must'] = new_must
                optimized_clause['bool']['filter'] = filter_clauses
        
        # Optimize wildcard queries
        if 'wildcard' in query_clause:
            # Suggest prefix query instead of wildcard when possible
            wildcard_value = list(query_clause['wildcard'].values())[0]
            if isinstance(wildcard_value, str) and wildcard_value.endswith('*') and '*' not in wildcard_value[:-1]:
                field_name = list(query_clause['wildcard'].keys())[0]
                optimized_clause = {
                    'prefix': {
                        field_name: wildcard_value[:-1]
                    }
                }
        
        return optimized_clause

class IndexPerformanceAnalyzer:
    """Analyze and optimize index performance."""
    
    @staticmethod
    async def analyze_index_performance(index_name: str) -> Dict[str, Any]:
        """Analyze index performance characteristics."""
        
        try:
            from elasticsearch import AsyncElasticsearch
            es = AsyncElasticsearch()
            
            # Get index stats
            stats = await es.indices.stats(index=index_name)
            index_stats = stats['indices'][index_name]
            
            # Get mapping info
            mapping = await es.indices.get_mapping(index=index_name)
            index_mapping = mapping[index_name]['mappings']
            
            analysis = {
                'index_name': index_name,
                'performance_metrics': {},
                'field_analysis': {},
                'recommendations': []
            }
            
            # Analyze performance metrics
            total_docs = index_stats['total']['docs']['count']
            total_size = index_stats['total']['store']['size_in_bytes']
            
            analysis['performance_metrics'] = {
                'document_count': total_docs,
                'index_size_mb': total_size / (1024 * 1024),
                'avg_document_size': total_size / total_docs if total_docs > 0 else 0,
                'search_latency': index_stats['total']['search']['query_time_in_millis'] / max(index_stats['total']['search']['query_total'], 1)
            }
            
            # Analyze field usage
            properties = index_mapping.get('properties', {})
            for field_name, field_config in properties.items():
                field_type = field_config.get('type', 'unknown')
                
                analysis['field_analysis'][field_name] = {
                    'type': field_type,
                    'has_multi_fields': 'fields' in field_config,
                    'is_searchable': field_type in ['text', 'keyword'],
                    'is_aggregatable': field_type in ['keyword', 'integer', 'float', 'date', 'boolean']
                }
            
            # Generate recommendations
            if total_docs > 10000000:  # 10M documents
                analysis['recommendations'].append("Consider using multiple shards for better parallelism")
            
            if analysis['performance_metrics']['avg_document_size'] > 1024 * 1024:  # 1MB
                analysis['recommendations'].append("Large documents detected - consider source filtering")
            
            text_fields = [name for name, config in analysis['field_analysis'].items() if config['type'] == 'text']
            if len(text_fields) > 20:
                analysis['recommendations'].append("Many text fields detected - consider consolidating or using multi-fields")
            
            return analysis
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Index analysis failed: {str(e)}"
            )
    
    @staticmethod
    def recommend_shard_strategy(
        document_count: int,
        index_size_mb: float,
        query_patterns: List[str]
    ) -> Dict[str, Any]:
        """Recommend sharding strategy."""
        
        recommendations = {
            'shard_count': 1,
            'replica_count': 1,
            'reasoning': [],
            'considerations': []
        }
        
        # Base shard count on data size and volume
        if document_count > 50000000 or index_size_mb > 50000:  # 50M docs or 50GB
            recommendations['shard_count'] = 5
            recommendations['reasoning'].append("High data volume requires multiple shards")
        elif document_count > 10000000 or index_size_mb > 10000:  # 10M docs or 10GB
            recommendations['shard_count'] = 3
            recommendations['reasoning'].append("Medium data volume benefits from multiple shards")
        
        # Adjust based on query patterns
        if 'aggregations' in query_patterns:
            recommendations['considerations'].append("Aggregations perform better with fewer shards")
            if recommendations['shard_count'] > 3:
                recommendations['shard_count'] = 3
        
        if 'real_time_search' in query_patterns:
            recommendations['replica_count'] = 2
            recommendations['reasoning'].append("Real-time search benefits from replicas for load distribution")
        
        # Ensure shard size guidelines
        if index_size_mb / recommendations['shard_count'] > 50000:  # 50GB per shard
            recommendations['shard_count'] = int(index_size_mb / 30000) + 1  # Target 30GB per shard
            recommendations['reasoning'].append("Adjusted shard count to maintain optimal shard size")
        
        return recommendations
```

## Template Management

### Dynamic Template Strategy
```python
class TemplateManager:
    """Manage index templates for consistent schema application."""
    
    @staticmethod
    async def create_dynamic_template(
        template_name: str,
        index_pattern: str,
        base_mapping: Dict[str, Any],
        settings: Dict[str, Any] = None
    ) -> bool:
        """Create dynamic template for automatic index creation."""
        
        try:
            from elasticsearch import AsyncElasticsearch
            es = AsyncElasticsearch()
            
            template_body = {
                'index_patterns': [index_pattern],
                'template': {
                    'mappings': base_mapping
                },
                'priority': 200,  # Higher priority than default templates
                'version': 1,
                'composed_of': []  # Component templates if using composable templates
            }
            
            if settings:
                template_body['template']['settings'] = settings
            
            # Create the template
            await es.indices.put_index_template(
                name=template_name,
                body=template_body
            )
            
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Template creation failed: {str(e)}"
            )
    
    @staticmethod
    def create_time_based_template() -> Dict[str, Any]:
        """Create template for time-based indices."""
        
        return {
            'template': {
                'mappings': {
                    'properties': {
                        '@timestamp': {
                            'type': 'date'
                        },
                        'message': {
                            'type': 'text',
                            'fields': {
                                'keyword': {
                                    'type': 'keyword',
                                    'ignore_above': 256
                                }
                            }
                        },
                        'level': {
                            'type': 'keyword'
                        },
                        'service': {
                            'type': 'keyword'
                        },
                        'host': {
                            'type': 'keyword'
                        },
                        'tags': {
                            'type': 'keyword'
                        },
                        'fields': {
                            'type': 'object',
                            'dynamic': True
                        }
                    }
                },
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 1,
                    'index.lifecycle.name': 'log_policy',
                    'index.lifecycle.rollover_alias': 'logs'
                }
            },
            'index_patterns': ['logs-*'],
            'priority': 150
        }
    
    @staticmethod
    def create_application_template(app_name: str) -> Dict[str, Any]:
        """Create application-specific template."""
        
        return {
            'template': {
                'mappings': {
                    'properties': {
                        'app_name': {
                            'type': 'keyword',
                            'value': app_name
                        },
                        'created_date': {
                            'type': 'date'
                        },
                        'updated_date': {
                            'type': 'date'
                        },
                        'version': {
                            'type': 'keyword'
                        },
                        'metadata': {
                            'type': 'object',
                            'dynamic': True
                        }
                    }
                },
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 1,
                    'analysis': {
                        'analyzer': {
                            f'{app_name}_analyzer': {
                                'type': 'custom',
                                'tokenizer': 'standard',
                                'filter': ['lowercase', 'stop']
                            }
                        }
                    }
                }
            },
            'index_patterns': [f'{app_name}-*'],
            'priority': 100
        }

class ComposableTemplateManager:
    """Manage composable templates for flexible schema composition."""
    
    @staticmethod
    async def create_component_templates() -> List[str]:
        """Create reusable component templates."""
        
        try:
            from elasticsearch import AsyncElasticsearch
            es = AsyncElasticsearch()
            
            created_templates = []
            
            # Base fields component
            base_component = {
                'template': {
                    'mappings': {
                        'properties': {
                            'id': {'type': 'keyword'},
                            'created_date': {'type': 'date'},
                            'updated_date': {'type': 'date'},
                            'version': {'type': 'integer'},
                            'active': {'type': 'boolean'}
                        }
                    }
                }
            }
            
            await es.cluster.put_component_template(
                name='base_fields',
                body=base_component
            )
            created_templates.append('base_fields')
            
            # Search fields component
            search_component = {
                'template': {
                    'mappings': {
                        'properties': {
                            'title': {
                                'type': 'text',
                                'fields': {
                                    'keyword': {'type': 'keyword'},
                                    'suggest': {'type': 'completion'}
                                }
                            },
                            'content': {
                                'type': 'text',
                                'fields': {
                                    'keyword': {'type': 'keyword'}
                                }
                            },
                            'tags': {'type': 'keyword'},
                            'category': {'type': 'keyword'}
                        }
                    }
                }
            }
            
            await es.cluster.put_component_template(
                name='search_fields',
                body=search_component
            )
            created_templates.append('search_fields')
            
            # Analytics component
            analytics_component = {
                'template': {
                    'mappings': {
                        'properties': {
                            'view_count': {'type': 'integer'},
                            'like_count': {'type': 'integer'},
                            'share_count': {'type': 'integer'},
                            'engagement_score': {'type': 'float'},
                            'last_viewed': {'type': 'date'}
                        }
                    }
                }
            }
            
            await es.cluster.put_component_template(
                name='analytics_fields',
                body=analytics_component
            )
            created_templates.append('analytics_fields')
            
            return created_templates
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Component template creation failed: {str(e)}"
            )
    
    @staticmethod
    async def create_composable_template(
        template_name: str,
        index_pattern: str,
        component_templates: List[str],
        additional_mappings: Dict[str, Any] = None
    ) -> bool:
        """Create composable template from component templates."""
        
        try:
            from elasticsearch import AsyncElasticsearch
            es = AsyncElasticsearch()
            
            template_body = {
                'index_patterns': [index_pattern],
                'composed_of': component_templates,
                'priority': 300
            }
            
            if additional_mappings:
                template_body['template'] = {
                    'mappings': additional_mappings
                }
            
            await es.indices.put_index_template(
                name=template_name,
                body=template_body
            )
            
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Composable template creation failed: {str(e)}"
            )
```

## Migration Strategies

### Zero-Downtime Migration
```python
class ZeroDowntimeMigration:
    """Implement zero-downtime schema migrations."""
    
    def __init__(self):
        self.migration_status = {}
    
    async def execute_alias_migration(
        self,
        old_index: str,
        new_index: str,
        alias_name: str
    ) -> Dict[str, Any]:
        """Execute migration using index aliases."""
        
        try:
            from elasticsearch import AsyncElasticsearch
            es = AsyncElasticsearch()
            
            migration_id = f"migration_{old_index}_to_{new_index}"
            self.migration_status[migration_id] = {
                'status': 'started',
                'start_time': datetime.utcnow(),
                'steps_completed': []
            }
            
            # Step 1: Create new index with updated mapping
            await self._create_new_index(es, new_index)
            self.migration_status[migration_id]['steps_completed'].append('new_index_created')
            
            # Step 2: Start reindexing from old to new
            reindex_task = await self._start_reindex(es, old_index, new_index)
            self.migration_status[migration_id]['reindex_task_id'] = reindex_task
            self.migration_status[migration_id]['steps_completed'].append('reindex_started')
            
            # Step 3: Wait for reindexing to complete
            await self._wait_for_reindex(es, reindex_task)
            self.migration_status[migration_id]['steps_completed'].append('reindex_completed')
            
            # Step 4: Switch alias atomically
            await self._switch_alias(es, old_index, new_index, alias_name)
            self.migration_status[migration_id]['steps_completed'].append('alias_switched')
            
            # Step 5: Verify data integrity
            verification_result = await self._verify_migration(es, old_index, new_index)
            self.migration_status[migration_id]['verification'] = verification_result
            
            if verification_result['success']:
                self.migration_status[migration_id]['status'] = 'completed'
                # Step 6: Clean up old index (optional)
                # await es.indices.delete(index=old_index)
            else:
                self.migration_status[migration_id]['status'] = 'verification_failed'
                # Rollback alias
                await self._rollback_alias(es, old_index, new_index, alias_name)
            
            return self.migration_status[migration_id]
            
        except Exception as e:
            self.migration_status[migration_id]['status'] = 'failed'
            self.migration_status[migration_id]['error'] = str(e)
            raise HTTPException(
                status_code=500,
                detail=f"Migration failed: {str(e)}"
            )
    
    async def _create_new_index(self, es, new_index: str):
        """Create new index with updated mapping."""
        
        # This would use the new schema definition
        new_mapping = {
            'mappings': {
                'properties': {
                    # Updated field definitions
                }
            },
            'settings': {
                'number_of_shards': 1,
                'number_of_replicas': 0  # No replicas during migration
            }
        }
        
        await es.indices.create(index=new_index, body=new_mapping)
    
    async def _start_reindex(self, es, source_index: str, dest_index: str) -> str:
        """Start reindexing process."""
        
        reindex_body = {
            'source': {
                'index': source_index
            },
            'dest': {
                'index': dest_index
            },
            'conflicts': 'proceed'  # Continue on version conflicts
        }
        
        response = await es.reindex(
            body=reindex_body,
            wait_for_completion=False,
            refresh=True
        )
        
        return response['task']
    
    async def _wait_for_reindex(self, es, task_id: str):
        """Wait for reindex task to complete."""
        
        while True:
            task_status = await es.tasks.get(task_id=task_id)
            
            if task_status['completed']:
                if task_status.get('error'):
                    raise Exception(f"Reindex failed: {task_status['error']}")
                break
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def _switch_alias(self, es, old_index: str, new_index: str, alias_name: str):
        """Atomically switch alias from old to new index."""
        
        actions = [
            {'remove': {'index': old_index, 'alias': alias_name}},
            {'add': {'index': new_index, 'alias': alias_name}}
        ]
        
        await es.indices.update_aliases(body={'actions': actions})
    
    async def _verify_migration(self, es, old_index: str, new_index: str) -> Dict[str, Any]:
        """Verify migration data integrity."""
        
        # Count documents
        old_count = await es.count(index=old_index)
        new_count = await es.count(index=new_index)
        
        verification = {
            'success': old_count['count'] == new_count['count'],
            'old_count': old_count['count'],
            'new_count': new_count['count'],
            'difference': abs(old_count['count'] - new_count['count'])
        }
        
        # Sample verification - check a few random documents
        if verification['success'] and old_count['count'] > 0:
            sample_verification = await self._verify_sample_documents(es, old_index, new_index)
            verification['sample_check'] = sample_verification
            verification['success'] = verification['success'] and sample_verification['success']
        
        return verification
    
    async def _verify_sample_documents(self, es, old_index: str, new_index: str) -> Dict[str, Any]:
        """Verify a sample of documents."""
        
        # Get random sample from old index
        sample_query = {
            'size': 10,
            'query': {
                'function_score': {
                    'query': {'match_all': {}},
                    'random_score': {}
                }
            }
        }
        
        old_sample = await es.search(index=old_index, body=sample_query)
        
        mismatches = 0
        total_checked = 0
        
        for hit in old_sample['hits']['hits']:
            doc_id = hit['_id']
            old_doc = hit['_source']
            
            try:
                new_doc_response = await es.get(index=new_index, id=doc_id)
                new_doc = new_doc_response['_source']
                
                # Simple comparison - in practice, you might need more sophisticated comparison
                if old_doc != new_doc:
                    mismatches += 1
                
                total_checked += 1
                
            except Exception:
                mismatches += 1
                total_checked += 1
        
        return {
            'success': mismatches == 0,
            'total_checked': total_checked,
            'mismatches': mismatches
        }
    
    async def _rollback_alias(self, es, old_index: str, new_index: str, alias_name: str):
        """Rollback alias switch."""
        
        actions = [
            {'remove': {'index': new_index, 'alias': alias_name}},
            {'add': {'index': old_index, 'alias': alias_name}}
        ]
        
        await es.indices.update_aliases(body={'actions': actions})

class IncrementalMigration:
    """Handle incremental schema migrations."""
    
    async def add_field_migration(
        self,
        index_name: str,
        field_name: str,
        field_mapping: Dict[str, Any],
        default_value: Any = None
    ) -> bool:
        """Add new field to existing index."""
        
        try:
            from elasticsearch import AsyncElasticsearch
            es = AsyncElasticsearch()
            
            # Add field to mapping
            mapping_update = {
                'properties': {
                    field_name: field_mapping
                }
            }
            
            await es.indices.put_mapping(
                index=index_name,
                body=mapping_update
            )
            
            # If default value provided, update existing documents
            if default_value is not None:
                update_script = {
                    'script': {
                        'source': f'ctx._source.{field_name} = params.default_value',
                        'params': {
                            'default_value': default_value
                        }
                    },
                    'query': {
                        'bool': {
                            'must_not': {
                                'exists': {
                                    'field': field_name
                                }
                            }
                        }
                    }
                }
                
                await es.update_by_query(
                    index=index_name,
                    body=update_script,
                    conflicts='proceed'
                )
            
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Field addition failed: {str(e)}"
            )
```

## Next Steps

1. **[Serialization Patterns](04_serialization-patterns.md)** - Learn data transformation and serialization techniques
2. **[Performance Optimization](../06-production-patterns/03_performance-optimization.md)** - Advanced performance tuning
3. **[Testing Strategies](../07-testing-deployment/01_testing-strategies.md)** - Testing schema changes and migrations

## Additional Resources

- **Elasticsearch Mapping Guide**: [elastic.co/guide/en/elasticsearch/reference/current/mapping.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html)
- **Index Templates**: [elastic.co/guide/en/elasticsearch/reference/current/index-templates.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-templates.html)
- **Schema Design Best Practices**: [elastic.co/blog/found-elasticsearch-mapping-introduction](https://www.elastic.co/blog/found-elasticsearch-mapping-introduction)