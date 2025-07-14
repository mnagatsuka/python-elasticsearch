# Migration Strategies

Comprehensive guide to schema evolution, data migration, and version management patterns for Elasticsearch with zero-downtime operations.

## Table of Contents
- [Schema Evolution Patterns](#schema-evolution-patterns)
- [Zero-downtime Migrations](#zero-downtime-migrations)
- [Data Transformation Strategies](#data-transformation-strategies)
- [Version Management](#version-management)
- [Rollback Procedures](#rollback-procedures)
- [Testing Migration Strategies](#testing-migration-strategies)
- [Production Migration Workflows](#production-migration-workflows)
- [Next Steps](#next-steps)

## Schema Evolution Patterns

### Document Version Management
```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Integer, Date, Object
from elasticsearch_dsl.connections import connections
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import asyncio
import json

class BaseVersionedDocument(AsyncDocument):
    """Base document with built-in versioning support."""
    
    # Version tracking fields
    schema_version = Keyword()
    created_at = Date()
    updated_at = Date()
    migrated_from_version = Keyword()
    migration_timestamp = Date()
    
    class Meta:
        abstract = True
    
    def get_schema_version(self) -> str:
        """Get current schema version."""
        return getattr(self.__class__, '_schema_version', '1.0')
    
    async def save(self, **kwargs):
        """Override save to add version tracking."""
        now = datetime.utcnow()
        
        if not self.created_at:
            self.created_at = now
        
        self.updated_at = now
        self.schema_version = self.get_schema_version()
        
        return await super().save(**kwargs)
    
    @classmethod
    def get_migration_map(cls) -> Dict[str, callable]:
        """Get mapping of version migrations."""
        return getattr(cls, '_migration_map', {})
    
    async def migrate_to_latest(self) -> 'BaseVersionedDocument':
        """Migrate document to latest schema version."""
        current_version = self.schema_version
        target_version = self.get_schema_version()
        
        if current_version == target_version:
            return self
        
        migration_map = self.get_migration_map()
        migration_path = self._find_migration_path(current_version, target_version, migration_map)
        
        if not migration_path:
            raise ValueError(f"No migration path from {current_version} to {target_version}")
        
        # Apply migrations in sequence
        migrated_doc = self
        for from_version, to_version in migration_path:
            migration_key = f"{from_version}_to_{to_version}"
            if migration_key in migration_map:
                migrated_doc = await migration_map[migration_key](migrated_doc)
        
        # Update migration metadata
        migrated_doc.migrated_from_version = current_version
        migrated_doc.migration_timestamp = datetime.utcnow()
        
        return migrated_doc
    
    def _find_migration_path(self, current: str, target: str, 
                           migration_map: Dict[str, callable]) -> List[tuple]:
        """Find migration path between versions."""
        # Simple implementation - in production, use graph traversal
        available_migrations = []
        for key in migration_map.keys():
            from_v, to_v = key.split('_to_')
            available_migrations.append((from_v, to_v))
        
        # For now, assume direct migration exists
        if f"{current}_to_{target}" in migration_map:
            return [(current, target)]
        
        # TODO: Implement proper path finding for multi-step migrations
        return []

class BlogPostV1(BaseVersionedDocument):
    """Blog post schema version 1.0."""
    
    _schema_version = '1.0'
    
    title = Text()
    content = Text()
    author = Keyword()
    created_date = Date()
    
    class Index:
        name = 'blog_posts_v1'

class BlogPostV2(BaseVersionedDocument):
    """Blog post schema version 2.0 - added categories and tags."""
    
    _schema_version = '2.0'
    
    title = Text(boost=2.0)
    content = Text()
    author = Keyword()
    category = Keyword()
    tags = Keyword(multi=True)
    created_date = Date()  # Keep for backward compatibility
    published_date = Date()  # New field
    
    # Migration definitions
    _migration_map = {
        '1.0_to_2.0': lambda self, doc: self._migrate_v1_to_v2(doc)
    }
    
    @classmethod
    async def _migrate_v1_to_v2(cls, v1_doc: BlogPostV1) -> 'BlogPostV2':
        """Migrate from v1 to v2 schema."""
        
        v2_doc = cls(
            meta={'id': v1_doc.meta.id},
            title=v1_doc.title,
            content=v1_doc.content,
            author=v1_doc.author,
            created_date=v1_doc.created_date,
            published_date=v1_doc.created_date,  # Use created_date as published_date
            category='general',  # Default category
            tags=[]  # Start with empty tags
        )
        
        # Extract tags from content (simple implementation)
        if v1_doc.content:
            # Look for hashtags in content
            import re
            hashtags = re.findall(r'#(\w+)', v1_doc.content)
            v2_doc.tags = hashtags[:5]  # Limit to 5 tags
        
        return v2_doc
    
    class Index:
        name = 'blog_posts_v2'

class BlogPostV3(BaseVersionedDocument):
    """Blog post schema version 3.0 - added nested metadata."""
    
    _schema_version = '3.0'
    
    title = Text(boost=2.0)
    content = Text()
    author = Keyword()
    category = Keyword()
    tags = Keyword(multi=True)
    published_date = Date()
    
    # New nested metadata structure
    metadata = Object(
        properties={
            'word_count': Integer(),
            'reading_time': Integer(),
            'language': Keyword(),
            'seo_score': Integer(),
            'last_updated': Date()
        }
    )
    
    # Social engagement metrics
    engagement = Object(
        properties={
            'views': Integer(),
            'likes': Integer(),
            'shares': Integer(),
            'comments_count': Integer()
        }
    )
    
    _migration_map = {
        '1.0_to_2.0': lambda self, doc: BlogPostV2._migrate_v1_to_v2(doc),
        '2.0_to_3.0': lambda self, doc: self._migrate_v2_to_v3(doc)
    }
    
    @classmethod
    async def _migrate_v2_to_v3(cls, v2_doc: BlogPostV2) -> 'BlogPostV3':
        """Migrate from v2 to v3 schema."""
        
        # Calculate metadata
        word_count = len(v2_doc.content.split()) if v2_doc.content else 0
        reading_time = max(1, word_count // 200)  # Assume 200 words per minute
        
        v3_doc = cls(
            meta={'id': v2_doc.meta.id},
            title=v2_doc.title,
            content=v2_doc.content,
            author=v2_doc.author,
            category=v2_doc.category,
            tags=v2_doc.tags,
            published_date=v2_doc.published_date,
            metadata={
                'word_count': word_count,
                'reading_time': reading_time,
                'language': 'en',  # Default to English
                'seo_score': 75,   # Default SEO score
                'last_updated': datetime.utcnow()
            },
            engagement={
                'views': 0,
                'likes': 0,
                'shares': 0,
                'comments_count': 0
            }
        )
        
        return v3_doc
    
    class Index:
        name = 'blog_posts_v3'

# Schema evolution manager
class SchemaEvolutionManager:
    """Manager for handling schema evolution."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def detect_schema_versions(self, index_pattern: str) -> Dict[str, List[str]]:
        """Detect different schema versions in indices."""
        
        from elasticsearch_dsl import AsyncSearch
        
        search = AsyncSearch(index=index_pattern)
        search.aggs.bucket('schema_versions', 'terms', field='schema_version', size=100)
        search = search[:0]  # Don't need actual documents
        
        response = await search.execute()
        
        versions = {}
        for bucket in response.aggregations.schema_versions.buckets:
            version = bucket.key
            doc_count = bucket.doc_count
            
            if version not in versions:
                versions[version] = []
            versions[version].append({
                'count': doc_count,
                'index_pattern': index_pattern
            })
        
        return versions
    
    async def plan_migration(self, source_index: str, target_version: str) -> Dict[str, Any]:
        """Plan migration strategy for index."""
        
        # Analyze current data
        current_versions = await self.detect_schema_versions(source_index)
        
        # Estimate migration effort
        total_docs = sum(
            version_info[0]['count'] 
            for version_info in current_versions.values()
        )
        
        migration_plan = {
            'source_index': source_index,
            'target_version': target_version,
            'current_versions': current_versions,
            'total_documents': total_docs,
            'estimated_time_minutes': total_docs // 1000,  # Rough estimate
            'requires_reindex': True,
            'steps': [
                'Create new index with target schema',
                'Run migration script with reindex',
                'Validate migrated data',
                'Switch alias to new index',
                'Clean up old index'
            ]
        }
        
        return migration_plan
    
    async def validate_migration(self, source_index: str, 
                               target_index: str) -> Dict[str, Any]:
        """Validate migration results."""
        
        # Compare document counts
        source_count = await self._get_document_count(source_index)
        target_count = await self._get_document_count(target_index)
        
        # Sample documents for validation
        validation_results = {
            'document_count_match': source_count == target_count,
            'source_count': source_count,
            'target_count': target_count,
            'sample_validation': await self._validate_sample_documents(source_index, target_index)
        }
        
        return validation_results
    
    async def _get_document_count(self, index: str) -> int:
        """Get document count for index."""
        try:
            result = await self.client.count(index=index)
            return result['count']
        except Exception:
            return 0
    
    async def _validate_sample_documents(self, source_index: str, 
                                       target_index: str) -> Dict[str, Any]:
        """Validate sample of migrated documents."""
        
        from elasticsearch_dsl import AsyncSearch
        import random
        
        # Get sample IDs from source
        source_search = AsyncSearch(index=source_index)
        source_search = source_search[:100]
        source_response = await source_search.execute()
        
        if not source_response.hits:
            return {'status': 'no_documents_to_validate'}
        
        # Randomly sample some documents
        sample_size = min(10, len(source_response.hits))
        sample_ids = random.sample([hit.meta.id for hit in source_response.hits], sample_size)
        
        validation_results = []
        
        for doc_id in sample_ids:
            try:
                # Get source document
                source_doc = await self.client.get(index=source_index, id=doc_id)
                
                # Get target document
                target_doc = await self.client.get(index=target_index, id=doc_id)
                
                # Basic validation
                validation_results.append({
                    'document_id': doc_id,
                    'exists_in_target': True,
                    'has_schema_version': 'schema_version' in target_doc['_source'],
                    'title_preserved': source_doc['_source'].get('title') == target_doc['_source'].get('title')
                })
                
            except Exception as e:
                validation_results.append({
                    'document_id': doc_id,
                    'exists_in_target': False,
                    'error': str(e)
                })
        
        return {
            'sample_size': len(validation_results),
            'results': validation_results,
            'success_rate': sum(1 for r in validation_results if r.get('exists_in_target', False)) / len(validation_results)
        }
```

## Zero-downtime Migrations

### Blue-Green Migration Pattern
```python
class ZeroDowntimeMigrator:
    """Zero-downtime migration using blue-green deployment pattern."""
    
    def __init__(self):
        self.client = connections.get_connection()
        self.schema_manager = SchemaEvolutionManager()
    
    async def blue_green_migration(self, service_name: str, 
                                 old_document_class: type,
                                 new_document_class: type,
                                 batch_size: int = 1000) -> Dict[str, Any]:
        """Execute blue-green migration."""
        
        migration_id = f"migration_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Step 1: Create new index (green)
            green_index = f"{service_name}_green_{migration_id}"
            await new_document_class.init(index=green_index)
            
            # Step 2: Migrate data
            migration_result = await self._migrate_data(
                old_document_class.Index.name,
                green_index,
                old_document_class,
                new_document_class,
                batch_size
            )
            
            if not migration_result['success']:
                return {
                    'success': False,
                    'error': 'Data migration failed',
                    'details': migration_result
                }
            
            # Step 3: Validate migration
            validation_result = await self.schema_manager.validate_migration(
                old_document_class.Index.name,
                green_index
            )
            
            if not validation_result['document_count_match']:
                return {
                    'success': False,
                    'error': 'Validation failed - document count mismatch',
                    'validation': validation_result
                }
            
            # Step 4: Switch traffic (alias swap)
            current_alias = f"{service_name}_current"
            switch_result = await self._atomic_alias_switch(
                current_alias,
                old_document_class.Index.name,
                green_index
            )
            
            if not switch_result['success']:
                return {
                    'success': False,
                    'error': 'Alias switch failed',
                    'switch_result': switch_result
                }
            
            # Step 5: Update document class to use new index
            new_document_class._index._name = current_alias
            
            return {
                'success': True,
                'migration_id': migration_id,
                'old_index': old_document_class.Index.name,
                'new_index': green_index,
                'current_alias': current_alias,
                'migrated_documents': migration_result['migrated_count'],
                'validation': validation_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'migration_id': migration_id
            }
    
    async def _migrate_data(self, source_index: str, target_index: str,
                          source_class: type, target_class: type,
                          batch_size: int) -> Dict[str, Any]:
        """Migrate data from source to target index."""
        
        from elasticsearch.helpers import async_scan, async_bulk
        
        try:
            migrated_count = 0
            errors = []
            
            # Scan through all documents in source index
            async for doc in async_scan(
                self.client,
                index=source_index,
                size=batch_size,
                scroll='5m'
            ):
                try:
                    # Create source document instance
                    source_doc = source_class.from_dict(doc['_source'])
                    source_doc.meta.id = doc['_id']
                    
                    # Migrate to target schema
                    if hasattr(source_doc, 'migrate_to_latest'):
                        target_doc = await source_doc.migrate_to_latest()
                    else:
                        # Direct migration
                        target_doc = await self._direct_migration(source_doc, target_class)
                    
                    # Index migrated document
                    target_doc.meta.id = source_doc.meta.id
                    target_doc._index._name = target_index
                    await target_doc.save()
                    
                    migrated_count += 1
                    
                    # Log progress
                    if migrated_count % 1000 == 0:
                        print(f"Migrated {migrated_count} documents...")
                    
                except Exception as e:
                    errors.append({
                        'document_id': doc.get('_id'),
                        'error': str(e)
                    })
            
            return {
                'success': len(errors) == 0,
                'migrated_count': migrated_count,
                'error_count': len(errors),
                'errors': errors[:10]  # Return first 10 errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _direct_migration(self, source_doc, target_class):
        """Direct migration when no migrate_to_latest method available."""
        
        # Extract common fields
        source_dict = source_doc.to_dict()
        
        # Create target document with available fields
        target_doc = target_class()
        
        for field_name in target_class._doc_type.mapping:
            if field_name in source_dict:
                setattr(target_doc, field_name, source_dict[field_name])
        
        return target_doc
    
    async def _atomic_alias_switch(self, alias_name: str, 
                                 old_index: str, new_index: str) -> Dict[str, Any]:
        """Atomically switch alias from old to new index."""
        
        try:
            # Check if alias exists
            alias_exists = await self.client.indices.exists_alias(name=alias_name)
            
            actions = []
            
            if alias_exists:
                actions.append({'remove': {'index': old_index, 'alias': alias_name}})
            
            actions.append({'add': {'index': new_index, 'alias': alias_name}})
            
            response = await self.client.indices.update_aliases(body={'actions': actions})
            
            return {
                'success': True,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Rolling migration for minimal downtime
class RollingMigrator:
    """Rolling migration with minimal service disruption."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def rolling_migration(self, index_pattern: str,
                              migration_function: callable,
                              batch_size: int = 500) -> Dict[str, Any]:
        """Execute rolling migration with live traffic."""
        
        from elasticsearch_dsl import AsyncSearch
        
        try:
            # Track migration progress
            total_migrated = 0
            errors = []
            
            # Use scroll to process all documents
            search = AsyncSearch(index=index_pattern)
            search = search.params(scroll='2m', size=batch_size)
            
            async for hit in search.scan():
                try:
                    # Apply migration to individual document
                    migrated_doc = await migration_function(hit)
                    
                    if migrated_doc:
                        # Update document in place
                        await self.client.index(
                            index=hit.meta.index,
                            id=hit.meta.id,
                            body=migrated_doc.to_dict(),
                            refresh='wait_for'
                        )
                        total_migrated += 1
                    
                    # Small delay to reduce load
                    if total_migrated % 100 == 0:
                        await asyncio.sleep(0.1)
                        print(f"Rolling migration: {total_migrated} documents processed")
                
                except Exception as e:
                    errors.append({
                        'document_id': hit.meta.id,
                        'error': str(e)
                    })
            
            return {
                'success': len(errors) == 0,
                'total_migrated': total_migrated,
                'error_count': len(errors),
                'errors': errors[:10]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def incremental_migration(self, index_name: str,
                                  migration_function: callable,
                                  timestamp_field: str = 'updated_at',
                                  checkpoint_interval: int = 3600) -> Dict[str, Any]:
        """Incremental migration based on timestamps."""
        
        from elasticsearch_dsl import AsyncSearch, Q
        
        # Get last checkpoint
        last_checkpoint = await self._get_migration_checkpoint(index_name)
        
        if not last_checkpoint:
            last_checkpoint = datetime.utcnow() - timedelta(days=365)  # Start from 1 year ago
        
        current_time = datetime.utcnow()
        
        # Query documents updated since last checkpoint
        search = AsyncSearch(index=index_name)
        search = search.filter(
            'range',
            **{timestamp_field: {'gte': last_checkpoint, 'lte': current_time}}
        )
        search = search.sort(timestamp_field)
        
        migrated_count = 0
        errors = []
        
        async for hit in search.scan():
            try:
                migrated_doc = await migration_function(hit)
                
                if migrated_doc:
                    await self.client.index(
                        index=hit.meta.index,
                        id=hit.meta.id,
                        body=migrated_doc.to_dict()
                    )
                    migrated_count += 1
                
            except Exception as e:
                errors.append({
                    'document_id': hit.meta.id,
                    'error': str(e)
                })
        
        # Update checkpoint
        await self._update_migration_checkpoint(index_name, current_time)
        
        return {
            'success': len(errors) == 0,
            'migrated_count': migrated_count,
            'checkpoint_updated': current_time.isoformat(),
            'errors': errors
        }
    
    async def _get_migration_checkpoint(self, index_name: str) -> Optional[datetime]:
        """Get last migration checkpoint."""
        try:
            checkpoint_doc = await self.client.get(
                index='migration_checkpoints',
                id=index_name
            )
            return datetime.fromisoformat(checkpoint_doc['_source']['last_checkpoint'])
        except Exception:
            return None
    
    async def _update_migration_checkpoint(self, index_name: str, checkpoint: datetime):
        """Update migration checkpoint."""
        try:
            await self.client.index(
                index='migration_checkpoints',
                id=index_name,
                body={
                    'index_name': index_name,
                    'last_checkpoint': checkpoint.isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
            )
        except Exception:
            pass  # Checkpoint update is not critical
```

## Data Transformation Strategies

### Complex Data Transformations
```python
from typing import Callable, Any
import re
from dataclasses import dataclass

@dataclass
class TransformationRule:
    """Definition of a data transformation rule."""
    field_path: str
    transformation: Callable[[Any], Any]
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    description: str = ""

class DataTransformer:
    """Advanced data transformation engine."""
    
    def __init__(self):
        self.rules: List[TransformationRule] = []
    
    def add_rule(self, rule: TransformationRule):
        """Add transformation rule."""
        self.rules.append(rule)
    
    def add_field_mapping(self, old_field: str, new_field: str, 
                         transform_func: Callable = None):
        """Add simple field mapping rule."""
        
        def mapping_transform(doc_dict: Dict[str, Any]) -> Dict[str, Any]:
            if old_field in doc_dict:
                value = doc_dict[old_field]
                if transform_func:
                    value = transform_func(value)
                doc_dict[new_field] = value
                
                # Remove old field if different from new field
                if old_field != new_field:
                    del doc_dict[old_field]
            
            return doc_dict
        
        rule = TransformationRule(
            field_path=old_field,
            transformation=mapping_transform,
            description=f"Map {old_field} to {new_field}"
        )
        
        self.add_rule(rule)
    
    def add_computed_field(self, field_name: str, computation: Callable):
        """Add computed field rule."""
        
        def compute_transform(doc_dict: Dict[str, Any]) -> Dict[str, Any]:
            doc_dict[field_name] = computation(doc_dict)
            return doc_dict
        
        rule = TransformationRule(
            field_path=field_name,
            transformation=compute_transform,
            description=f"Compute field {field_name}"
        )
        
        self.add_rule(rule)
    
    def add_conditional_transform(self, condition: Callable, 
                                transform: Callable, description: str = ""):
        """Add conditional transformation."""
        
        rule = TransformationRule(
            field_path="*",
            transformation=transform,
            condition=condition,
            description=description
        )
        
        self.add_rule(rule)
    
    async def transform_document(self, doc_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all transformation rules to document."""
        
        result = doc_dict.copy()
        
        for rule in self.rules:
            # Check condition if specified
            if rule.condition and not rule.condition(result):
                continue
            
            # Apply transformation
            try:
                result = await self._apply_transformation(rule, result)
            except Exception as e:
                print(f"Transformation error in rule '{rule.description}': {e}")
                # Continue with other rules
        
        return result
    
    async def _apply_transformation(self, rule: TransformationRule, 
                                  doc_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply single transformation rule."""
        
        if rule.field_path == "*":
            # Global transformation
            return rule.transformation(doc_dict)
        else:
            # Field-specific transformation
            return rule.transformation(doc_dict)

# Predefined transformation functions
class StandardTransformations:
    """Collection of standard transformation functions."""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text field."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML tags (basic)
        text = re.sub(r'<[^>]+>', '', text)
        
        return text
    
    @staticmethod
    def extract_tags_from_content(content: str) -> List[str]:
        """Extract hashtags from content."""
        if not content:
            return []
        
        hashtags = re.findall(r'#(\w+)', content)
        return list(set(hashtags))  # Remove duplicates
    
    @staticmethod
    def calculate_reading_time(content: str, wpm: int = 200) -> int:
        """Calculate reading time in minutes."""
        if not content:
            return 0
        
        word_count = len(content.split())
        return max(1, word_count // wpm)
    
    @staticmethod
    def categorize_by_keywords(title: str, content: str) -> str:
        """Auto-categorize based on keywords."""
        text = f"{title} {content}".lower()
        
        categories = {
            'technology': ['tech', 'software', 'programming', 'api', 'database'],
            'tutorial': ['how to', 'guide', 'tutorial', 'step by step'],
            'news': ['news', 'update', 'announcement', 'release'],
            'review': ['review', 'opinion', 'rating', 'evaluation']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'general'
    
    @staticmethod
    def extract_metadata(doc_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from document."""
        content = doc_dict.get('content', '')
        title = doc_dict.get('title', '')
        
        return {
            'word_count': len(content.split()) if content else 0,
            'char_count': len(content) if content else 0,
            'reading_time': StandardTransformations.calculate_reading_time(content),
            'has_title': bool(title),
            'estimated_seo_score': min(100, max(0, len(title) * 2 + len(content) // 10))
        }

# Example migration with transformations
class BlogPostMigrationV2ToV3:
    """Migration from BlogPost V2 to V3 with transformations."""
    
    def __init__(self):
        self.transformer = DataTransformer()
        self._setup_transformation_rules()
    
    def _setup_transformation_rules(self):
        """Setup transformation rules for V2 to V3 migration."""
        
        # Add metadata computation
        self.transformer.add_computed_field(
            'metadata',
            StandardTransformations.extract_metadata
        )
        
        # Normalize text fields
        self.transformer.add_rule(TransformationRule(
            field_path='title',
            transformation=lambda doc: {
                **doc,
                'title': StandardTransformations.normalize_text(doc.get('title', ''))
            },
            description='Normalize title text'
        ))
        
        self.transformer.add_rule(TransformationRule(
            field_path='content',
            transformation=lambda doc: {
                **doc,
                'content': StandardTransformations.normalize_text(doc.get('content', ''))
            },
            description='Normalize content text'
        ))
        
        # Extract tags from content if tags are empty
        self.transformer.add_rule(TransformationRule(
            field_path='tags',
            transformation=lambda doc: {
                **doc,
                'tags': (doc.get('tags') or 
                        StandardTransformations.extract_tags_from_content(doc.get('content', '')))
            },
            condition=lambda doc: not doc.get('tags'),
            description='Extract tags from content if empty'
        ))
        
        # Auto-categorize if category is 'general'
        self.transformer.add_rule(TransformationRule(
            field_path='category',
            transformation=lambda doc: {
                **doc,
                'category': StandardTransformations.categorize_by_keywords(
                    doc.get('title', ''), doc.get('content', '')
                )
            },
            condition=lambda doc: doc.get('category') == 'general',
            description='Auto-categorize based on content'
        ))
        
        # Add engagement metrics
        self.transformer.add_computed_field(
            'engagement',
            lambda doc: {
                'views': 0,
                'likes': 0,
                'shares': 0,
                'comments_count': 0
            }
        )
        
        # Convert created_date to published_date if missing
        self.transformer.add_rule(TransformationRule(
            field_path='published_date',
            transformation=lambda doc: {
                **doc,
                'published_date': doc.get('published_date') or doc.get('created_date')
            },
            condition=lambda doc: not doc.get('published_date'),
            description='Use created_date as published_date if missing'
        ))
    
    async def migrate_document(self, v2_doc_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate single document from V2 to V3."""
        
        # Apply all transformations
        v3_doc_dict = await self.transformer.transform_document(v2_doc_dict)
        
        # Add schema version
        v3_doc_dict['schema_version'] = '3.0'
        v3_doc_dict['migrated_from_version'] = v2_doc_dict.get('schema_version', '2.0')
        v3_doc_dict['migration_timestamp'] = datetime.utcnow().isoformat()
        
        return v3_doc_dict

# Bulk transformation service
class BulkTransformationService:
    """Service for bulk data transformations."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def transform_index(self, source_index: str, target_index: str,
                            transformer: DataTransformer,
                            batch_size: int = 1000) -> Dict[str, Any]:
        """Transform entire index using provided transformer."""
        
        from elasticsearch.helpers import async_scan, async_bulk
        
        try:
            transformed_count = 0
            errors = []
            
            # Prepare bulk actions
            async def generate_actions():
                async for doc in async_scan(
                    self.client,
                    index=source_index,
                    size=batch_size
                ):
                    try:
                        # Transform document
                        transformed_doc = await transformer.transform_document(doc['_source'])
                        
                        yield {
                            '_index': target_index,
                            '_id': doc['_id'],
                            '_source': transformed_doc
                        }
                        
                    except Exception as e:
                        errors.append({
                            'document_id': doc['_id'],
                            'error': str(e)
                        })
            
            # Execute bulk transformation
            success_count, failed_items = await async_bulk(
                self.client,
                generate_actions(),
                chunk_size=batch_size
            )
            
            return {
                'success': True,
                'transformed_count': success_count,
                'transformation_errors': len(errors),
                'bulk_errors': len(failed_items),
                'total_errors': len(errors) + len(failed_items)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def preview_transformation(self, index: str, transformer: DataTransformer,
                                   sample_size: int = 10) -> Dict[str, Any]:
        """Preview transformation results on sample documents."""
        
        from elasticsearch_dsl import AsyncSearch
        
        # Get sample documents
        search = AsyncSearch(index=index)
        search = search[:sample_size]
        
        response = await search.execute()
        
        previews = []
        
        for hit in response.hits:
            original = hit.to_dict()
            
            try:
                transformed = await transformer.transform_document(original)
                
                previews.append({
                    'document_id': hit.meta.id,
                    'original': original,
                    'transformed': transformed,
                    'changes': self._identify_changes(original, transformed)
                })
                
            except Exception as e:
                previews.append({
                    'document_id': hit.meta.id,
                    'error': str(e)
                })
        
        return {
            'sample_size': len(previews),
            'previews': previews
        }
    
    def _identify_changes(self, original: Dict[str, Any], 
                         transformed: Dict[str, Any]) -> List[str]:
        """Identify changes between original and transformed documents."""
        
        changes = []
        
        # Check for new fields
        new_fields = set(transformed.keys()) - set(original.keys())
        for field in new_fields:
            changes.append(f"Added field: {field}")
        
        # Check for removed fields
        removed_fields = set(original.keys()) - set(transformed.keys())
        for field in removed_fields:
            changes.append(f"Removed field: {field}")
        
        # Check for modified fields
        for field in set(original.keys()) & set(transformed.keys()):
            if original[field] != transformed[field]:
                changes.append(f"Modified field: {field}")
        
        return changes
```

## Version Management

### Semantic Versioning for Schemas
```python
from dataclasses import dataclass
from typing import List, Dict, Optional
import semver

@dataclass
class SchemaVersion:
    """Schema version with semantic versioning."""
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @classmethod
    def from_string(cls, version_str: str) -> 'SchemaVersion':
        """Create version from string."""
        parts = version_str.split('.')
        return cls(
            major=int(parts[0]),
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0
        )
    
    def is_compatible_with(self, other: 'SchemaVersion') -> bool:
        """Check if this version is backward compatible with other."""
        # Same major version = compatible
        return self.major == other.major
    
    def requires_migration(self, other: 'SchemaVersion') -> bool:
        """Check if migration is required from other version."""
        return self.major != other.major or self.minor != other.minor

@dataclass
class SchemaChange:
    """Description of a schema change."""
    version: SchemaVersion
    change_type: str  # 'field_added', 'field_removed', 'field_modified', 'breaking_change'
    description: str
    migration_required: bool
    rollback_procedure: Optional[str] = None

class VersionManager:
    """Manager for schema versioning."""
    
    def __init__(self):
        self.schema_history: Dict[str, List[SchemaChange]] = {}
        self.current_versions: Dict[str, SchemaVersion] = {}
    
    def register_schema_change(self, document_type: str, change: SchemaChange):
        """Register a schema change."""
        if document_type not in self.schema_history:
            self.schema_history[document_type] = []
        
        self.schema_history[document_type].append(change)
        self.current_versions[document_type] = change.version
    
    def get_migration_path(self, document_type: str, 
                         from_version: SchemaVersion,
                         to_version: SchemaVersion) -> List[SchemaChange]:
        """Get migration path between versions."""
        
        if document_type not in self.schema_history:
            return []
        
        history = self.schema_history[document_type]
        
        # Find changes between versions
        migration_path = []
        
        for change in history:
            # Include changes that are between from_version and to_version
            if (change.version.major > from_version.major or
                (change.version.major == from_version.major and 
                 change.version.minor > from_version.minor)):
                
                if (change.version.major < to_version.major or
                    (change.version.major == to_version.major and 
                     change.version.minor <= to_version.minor)):
                    
                    migration_path.append(change)
        
        return migration_path
    
    def validate_upgrade_path(self, document_type: str,
                            target_version: SchemaVersion) -> Dict[str, Any]:
        """Validate if upgrade path is safe."""
        
        current_version = self.current_versions.get(document_type)
        if not current_version:
            return {
                'valid': False,
                'error': 'No current version found'
            }
        
        migration_path = self.get_migration_path(
            document_type, current_version, target_version
        )
        
        # Check for breaking changes
        breaking_changes = [
            change for change in migration_path 
            if change.change_type == 'breaking_change'
        ]
        
        # Check if all changes have migration procedures
        missing_migrations = [
            change for change in migration_path 
            if change.migration_required and not change.rollback_procedure
        ]
        
        return {
            'valid': len(breaking_changes) == 0 and len(missing_migrations) == 0,
            'breaking_changes': breaking_changes,
            'missing_migrations': missing_migrations,
            'migration_path': migration_path,
            'requires_migration': any(change.migration_required for change in migration_path)
        }

# Example usage with blog post evolution
class BlogPostVersionManager:
    """Version manager for blog post schema."""
    
    def __init__(self):
        self.version_manager = VersionManager()
        self._setup_version_history()
    
    def _setup_version_history(self):
        """Setup version history for blog posts."""
        
        # Version 1.0 -> 2.0 changes
        v2_changes = [
            SchemaChange(
                version=SchemaVersion(2, 0, 0),
                change_type='field_added',
                description='Added category field',
                migration_required=False
            ),
            SchemaChange(
                version=SchemaVersion(2, 0, 0),
                change_type='field_added',
                description='Added tags field',
                migration_required=False
            ),
            SchemaChange(
                version=SchemaVersion(2, 0, 0),
                change_type='field_added',
                description='Added published_date field',
                migration_required=True,
                rollback_procedure='Copy created_date to published_date'
            )
        ]
        
        # Version 2.0 -> 3.0 changes
        v3_changes = [
            SchemaChange(
                version=SchemaVersion(3, 0, 0),
                change_type='field_added',
                description='Added metadata nested object',
                migration_required=True,
                rollback_procedure='Calculate metadata from existing fields'
            ),
            SchemaChange(
                version=SchemaVersion(3, 0, 0),
                change_type='field_added',
                description='Added engagement metrics',
                migration_required=False
            ),
            SchemaChange(
                version=SchemaVersion(3, 0, 0),
                change_type='field_modified',
                description='Enhanced text analysis for title and content',
                migration_required=True,
                rollback_procedure='Re-analyze text fields with new analyzers'
            )
        ]
        
        # Register changes
        for change in v2_changes:
            self.version_manager.register_schema_change('blog_post', change)
        
        for change in v3_changes:
            self.version_manager.register_schema_change('blog_post', change)
    
    def plan_upgrade(self, from_version_str: str, 
                    to_version_str: str) -> Dict[str, Any]:
        """Plan upgrade between versions."""
        
        from_version = SchemaVersion.from_string(from_version_str)
        to_version = SchemaVersion.from_string(to_version_str)
        
        validation = self.version_manager.validate_upgrade_path(
            'blog_post', to_version
        )
        
        if not validation['valid']:
            return {
                'can_upgrade': False,
                'issues': validation
            }
        
        migration_path = validation['migration_path']
        
        return {
            'can_upgrade': True,
            'from_version': from_version_str,
            'to_version': to_version_str,
            'requires_migration': validation['requires_migration'],
            'changes': [
                {
                    'version': str(change.version),
                    'type': change.change_type,
                    'description': change.description,
                    'requires_migration': change.migration_required
                }
                for change in migration_path
            ],
            'estimated_downtime': 'minimal' if not validation['requires_migration'] else 'moderate'
        }
```

## Rollback Procedures

### Safe Rollback Mechanisms
```python
class RollbackManager:
    """Manager for safe rollback operations."""
    
    def __init__(self):
        self.client = connections.get_connection()
        self.backup_indices: Dict[str, str] = {}
    
    async def create_rollback_point(self, service_name: str, 
                                  current_index: str) -> Dict[str, Any]:
        """Create rollback point before migration."""
        
        rollback_id = f"rollback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        backup_index = f"{service_name}_backup_{rollback_id}"
        
        try:
            # Create backup index
            current_mapping = await self.client.indices.get_mapping(index=current_index)
            current_settings = await self.client.indices.get_settings(index=current_index)
            
            # Extract mapping and settings
            index_mapping = current_mapping[current_index]['mappings']
            index_settings = current_settings[current_index]['settings']['index']
            
            # Remove non-copyable settings
            copyable_settings = {
                k: v for k, v in index_settings.items()
                if k not in ['uuid', 'creation_date', 'provided_name', 'version']
            }
            
            await self.client.indices.create(
                index=backup_index,
                body={
                    'mappings': index_mapping,
                    'settings': copyable_settings
                }
            )
            
            # Copy data using reindex
            reindex_result = await self.client.reindex(
                body={
                    'source': {'index': current_index},
                    'dest': {'index': backup_index}
                },
                wait_for_completion=True
            )
            
            # Store rollback point info
            rollback_info = {
                'rollback_id': rollback_id,
                'service_name': service_name,
                'original_index': current_index,
                'backup_index': backup_index,
                'created_at': datetime.utcnow().isoformat(),
                'document_count': reindex_result.get('total', 0)
            }
            
            await self.client.index(
                index='rollback_points',
                id=rollback_id,
                body=rollback_info
            )
            
            self.backup_indices[service_name] = backup_index
            
            return {
                'success': True,
                'rollback_id': rollback_id,
                'backup_index': backup_index,
                'document_count': reindex_result.get('total', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_rollback(self, rollback_id: str) -> Dict[str, Any]:
        """Execute rollback to previous state."""
        
        try:
            # Get rollback point info
            rollback_doc = await self.client.get(
                index='rollback_points',
                id=rollback_id
            )
            
            rollback_info = rollback_doc['_source']
            service_name = rollback_info['service_name']
            backup_index = rollback_info['backup_index']
            current_alias = f"{service_name}_current"
            
            # Get current index
            current_indices = await self._get_indices_for_alias(current_alias)
            
            if not current_indices:
                return {
                    'success': False,
                    'error': 'No current index found for service'
                }
            
            current_index = current_indices[0]
            
            # Create new index from backup
            rollback_index = f"{service_name}_rollback_{rollback_id}"
            
            # Copy backup data to rollback index
            backup_mapping = await self.client.indices.get_mapping(index=backup_index)
            backup_settings = await self.client.indices.get_settings(index=backup_index)
            
            await self.client.indices.create(
                index=rollback_index,
                body={
                    'mappings': backup_mapping[backup_index]['mappings'],
                    'settings': backup_settings[backup_index]['settings']['index']
                }
            )
            
            reindex_result = await self.client.reindex(
                body={
                    'source': {'index': backup_index},
                    'dest': {'index': rollback_index}
                },
                wait_for_completion=True
            )
            
            # Switch alias to rollback index
            await self.client.indices.update_aliases(
                body={
                    'actions': [
                        {'remove': {'index': current_index, 'alias': current_alias}},
                        {'add': {'index': rollback_index, 'alias': current_alias}}
                    ]
                }
            )
            
            # Update rollback point
            rollback_info['executed_at'] = datetime.utcnow().isoformat()
            rollback_info['rollback_index'] = rollback_index
            rollback_info['restored_document_count'] = reindex_result.get('total', 0)
            
            await self.client.index(
                index='rollback_points',
                id=rollback_id,
                body=rollback_info
            )
            
            return {
                'success': True,
                'rollback_id': rollback_id,
                'rollback_index': rollback_index,
                'restored_documents': reindex_result.get('total', 0),
                'previous_index': current_index
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cleanup_rollback_points(self, days_to_keep: int = 7) -> Dict[str, Any]:
        """Clean up old rollback points."""
        
        from elasticsearch_dsl import AsyncSearch, Q
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Find old rollback points
        search = AsyncSearch(index='rollback_points')
        search = search.filter(
            'range',
            created_at={'lt': cutoff_date.isoformat()}
        )
        
        cleaned_up = []
        errors = []
        
        async for hit in search.scan():
            try:
                rollback_info = hit.to_dict()
                
                # Delete backup index
                if 'backup_index' in rollback_info:
                    await self.client.indices.delete(
                        index=rollback_info['backup_index'],
                        ignore=[404]
                    )
                
                # Delete rollback index if exists
                if 'rollback_index' in rollback_info:
                    await self.client.indices.delete(
                        index=rollback_info['rollback_index'],
                        ignore=[404]
                    )
                
                # Delete rollback point document
                await self.client.delete(
                    index='rollback_points',
                    id=hit.meta.id
                )
                
                cleaned_up.append(rollback_info['rollback_id'])
                
            except Exception as e:
                errors.append({
                    'rollback_id': hit.meta.id,
                    'error': str(e)
                })
        
        return {
            'success': len(errors) == 0,
            'cleaned_up_count': len(cleaned_up),
            'cleaned_up_ids': cleaned_up,
            'errors': errors
        }
    
    async def _get_indices_for_alias(self, alias_name: str) -> List[str]:
        """Get indices for alias."""
        try:
            aliases = await self.client.indices.get_alias(name=alias_name)
            return list(aliases.keys())
        except Exception:
            return []
    
    async def list_rollback_points(self, service_name: str = None) -> Dict[str, Any]:
        """List available rollback points."""
        
        from elasticsearch_dsl import AsyncSearch
        
        search = AsyncSearch(index='rollback_points')
        
        if service_name:
            search = search.filter('term', service_name=service_name)
        
        search = search.sort('-created_at')
        
        rollback_points = []
        
        async for hit in search.scan():
            rollback_info = hit.to_dict()
            rollback_points.append({
                'rollback_id': rollback_info['rollback_id'],
                'service_name': rollback_info['service_name'],
                'created_at': rollback_info['created_at'],
                'document_count': rollback_info.get('document_count', 0),
                'executed': 'executed_at' in rollback_info
            })
        
        return {
            'rollback_points': rollback_points,
            'total_count': len(rollback_points)
        }

# Automated rollback triggers
class AutomatedRollbackTrigger:
    """Automated rollback based on health metrics."""
    
    def __init__(self, rollback_manager: RollbackManager):
        self.rollback_manager = rollback_manager
        self.health_thresholds = {
            'error_rate_threshold': 0.05,  # 5% error rate
            'response_time_threshold': 1000,  # 1 second
            'availability_threshold': 0.99  # 99% availability
        }
    
    async def monitor_and_rollback(self, service_name: str, 
                                 rollback_id: str,
                                 monitoring_duration: int = 300) -> Dict[str, Any]:
        """Monitor service health and trigger rollback if needed."""
        
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=monitoring_duration)
        
        while datetime.utcnow() < end_time:
            # Check health metrics
            health_check = await self._check_service_health(service_name)
            
            if not health_check['healthy']:
                # Trigger rollback
                print(f"Health check failed for {service_name}, triggering rollback...")
                
                rollback_result = await self.rollback_manager.execute_rollback(rollback_id)
                
                return {
                    'rollback_triggered': True,
                    'trigger_reason': health_check['issues'],
                    'rollback_result': rollback_result
                }
            
            # Wait before next check
            await asyncio.sleep(30)  # Check every 30 seconds
        
        return {
            'rollback_triggered': False,
            'monitoring_completed': True,
            'final_health_check': health_check
        }
    
    async def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check service health metrics."""
        
        # This would integrate with actual monitoring systems
        # For now, simulate health check
        
        try:
            # Check if index exists and is responsive
            alias_name = f"{service_name}_current"
            
            # Simple query to test responsiveness
            start_time = datetime.utcnow()
            
            search_result = await self.client.search(
                index=alias_name,
                body={'query': {'match_all': {}}, 'size': 1}
            )
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            issues = []
            
            # Check response time
            if response_time > self.health_thresholds['response_time_threshold']:
                issues.append(f"High response time: {response_time}ms")
            
            # Check if search succeeded
            if not search_result.get('hits'):
                issues.append("Search query failed")
            
            return {
                'healthy': len(issues) == 0,
                'response_time_ms': response_time,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'issues': [f"Health check error: {str(e)}"]
            }
```

## Testing Migration Strategies

### Migration Testing Framework
```python
import pytest
from typing import Generator, Dict, Any

class MigrationTestFramework:
    """Framework for testing migrations."""
    
    def __init__(self):
        self.test_indices: List[str] = []
        self.client = connections.get_connection()
    
    async def setup_test_data(self, index_name: str, 
                            documents: List[Dict[str, Any]]) -> str:
        """Setup test data for migration testing."""
        
        test_index = f"test_{index_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.test_indices.append(test_index)
        
        # Create test index
        await self.client.indices.create(
            index=test_index,
            body={
                'mappings': {
                    'properties': {
                        'title': {'type': 'text'},
                        'content': {'type': 'text'},
                        'author': {'type': 'keyword'},
                        'created_date': {'type': 'date'}
                    }
                }
            }
        )
        
        # Index test documents
        for i, doc in enumerate(documents):
            await self.client.index(
                index=test_index,
                id=str(i),
                body=doc
            )
        
        await self.client.indices.refresh(index=test_index)
        
        return test_index
    
    async def cleanup_test_indices(self):
        """Clean up test indices."""
        for index in self.test_indices:
            try:
                await self.client.indices.delete(index=index)
            except Exception:
                pass
        self.test_indices.clear()
    
    async def test_migration_integrity(self, migration_function: callable,
                                     test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test migration data integrity."""
        
        # Setup test data
        source_index = await self.setup_test_data('migration_test', test_data)
        target_index = f"{source_index}_migrated"
        
        # Create target index
        await self.client.indices.create(
            index=target_index,
            body={
                'mappings': {
                    'properties': {
                        'title': {'type': 'text'},
                        'content': {'type': 'text'},
                        'author': {'type': 'keyword'},
                        'category': {'type': 'keyword'},
                        'tags': {'type': 'keyword'},
                        'published_date': {'type': 'date'},
                        'schema_version': {'type': 'keyword'}
                    }
                }
            }
        )
        
        self.test_indices.append(target_index)
        
        # Execute migration
        migration_result = await migration_function(source_index, target_index)
        
        # Validate results
        source_count = await self._get_document_count(source_index)
        target_count = await self._get_document_count(target_index)
        
        # Check document preservation
        sample_validation = await self._validate_document_samples(
            source_index, target_index
        )
        
        return {
            'migration_successful': migration_result.get('success', False),
            'document_count_preserved': source_count == target_count,
            'source_count': source_count,
            'target_count': target_count,
            'sample_validation': sample_validation,
            'migration_details': migration_result
        }
    
    async def test_rollback_functionality(self, service_name: str,
                                        rollback_manager: RollbackManager) -> Dict[str, Any]:
        """Test rollback functionality."""
        
        # Create test data
        test_data = [
            {'title': 'Test Post 1', 'content': 'Content 1', 'author': 'user1'},
            {'title': 'Test Post 2', 'content': 'Content 2', 'author': 'user2'}
        ]
        
        original_index = await self.setup_test_data('rollback_test', test_data)
        
        # Create rollback point
        rollback_result = await rollback_manager.create_rollback_point(
            service_name, original_index
        )
        
        if not rollback_result['success']:
            return {
                'test_passed': False,
                'error': 'Failed to create rollback point'
            }
        
        rollback_id = rollback_result['rollback_id']
        
        # Simulate changes to original index
        await self.client.index(
            index=original_index,
            id='new_doc',
            body={'title': 'New Document', 'content': 'New Content', 'author': 'new_user'}
        )
        
        # Execute rollback
        rollback_execution = await rollback_manager.execute_rollback(rollback_id)
        
        if not rollback_execution['success']:
            return {
                'test_passed': False,
                'error': 'Failed to execute rollback'
            }
        
        # Validate rollback
        rollback_index = rollback_execution['rollback_index']
        rollback_count = await self._get_document_count(rollback_index)
        
        return {
            'test_passed': rollback_count == len(test_data),
            'original_count': len(test_data),
            'rollback_count': rollback_count,
            'rollback_details': rollback_execution
        }
    
    async def performance_test_migration(self, migration_function: callable,
                                       document_count: int = 10000) -> Dict[str, Any]:
        """Test migration performance with large dataset."""
        
        # Generate test data
        test_data = [
            {
                'title': f'Test Document {i}',
                'content': f'This is test content for document {i}' * 10,
                'author': f'user_{i % 100}',
                'created_date': (datetime.utcnow() - timedelta(days=i % 365)).isoformat()
            }
            for i in range(document_count)
        ]
        
        source_index = await self.setup_test_data('performance_test', test_data)
        target_index = f"{source_index}_migrated"
        
        # Measure migration time
        start_time = datetime.utcnow()
        migration_result = await migration_function(source_index, target_index)
        end_time = datetime.utcnow()
        
        migration_time = (end_time - start_time).total_seconds()
        
        return {
            'document_count': document_count,
            'migration_time_seconds': migration_time,
            'documents_per_second': document_count / migration_time,
            'migration_successful': migration_result.get('success', False)
        }
    
    async def _get_document_count(self, index: str) -> int:
        """Get document count for index."""
        try:
            result = await self.client.count(index=index)
            return result['count']
        except Exception:
            return 0
    
    async def _validate_document_samples(self, source_index: str, 
                                       target_index: str) -> Dict[str, Any]:
        """Validate sample documents."""
        
        from elasticsearch_dsl import AsyncSearch
        
        # Get sample from source
        source_search = AsyncSearch(index=source_index)
        source_search = source_search[:5]
        source_response = await source_search.execute()
        
        validation_results = []
        
        for hit in source_response.hits:
            try:
                # Get corresponding document from target
                target_doc = await self.client.get(
                    index=target_index,
                    id=hit.meta.id
                )
                
                validation_results.append({
                    'document_id': hit.meta.id,
                    'exists_in_target': True,
                    'title_preserved': hit.title == target_doc['_source'].get('title')
                })
                
            except Exception:
                validation_results.append({
                    'document_id': hit.meta.id,
                    'exists_in_target': False
                })
        
        success_rate = sum(1 for r in validation_results if r['exists_in_target']) / len(validation_results)
        
        return {
            'samples_checked': len(validation_results),
            'success_rate': success_rate,
            'results': validation_results
        }

# Pytest fixtures and tests
@pytest.fixture
async def migration_test_framework():
    """Pytest fixture for migration testing."""
    framework = MigrationTestFramework()
    yield framework
    await framework.cleanup_test_indices()

@pytest.mark.asyncio
async def test_blog_post_v2_to_v3_migration(migration_test_framework):
    """Test blog post migration from v2 to v3."""
    
    test_data = [
        {
            'title': 'Test Blog Post',
            'content': 'This is test content with #tag1 and #tag2',
            'author': 'test_author',
            'category': 'general',
            'created_date': '2024-01-01T00:00:00Z'
        }
    ]
    
    async def migration_function(source_index, target_index):
        migrator = BlogPostMigrationV2ToV3()
        transformer_service = BulkTransformationService()
        
        return await transformer_service.transform_index(
            source_index, target_index, migrator.transformer
        )
    
    result = await migration_test_framework.test_migration_integrity(
        migration_function, test_data
    )
    
    assert result['migration_successful']
    assert result['document_count_preserved']
    assert result['sample_validation']['success_rate'] == 1.0

@pytest.mark.asyncio
async def test_rollback_functionality(migration_test_framework):
    """Test rollback functionality."""
    
    rollback_manager = RollbackManager()
    
    result = await migration_test_framework.test_rollback_functionality(
        'test_service', rollback_manager
    )
    
    assert result['test_passed']
    assert result['original_count'] == result['rollback_count']
```

## Production Migration Workflows

### Production-Ready Migration Pipeline
```python
class ProductionMigrationPipeline:
    """Complete production migration pipeline."""
    
    def __init__(self):
        self.client = connections.get_connection()
        self.migrator = ZeroDowntimeMigrator()
        self.rollback_manager = RollbackManager()
        self.health_monitor = AutomatedRollbackTrigger(self.rollback_manager)
    
    async def execute_production_migration(self, 
                                         migration_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete production migration with monitoring."""
        
        service_name = migration_config['service_name']
        old_document_class = migration_config['old_document_class']
        new_document_class = migration_config['new_document_class']
        
        migration_log = []
        
        try:
            # Step 1: Pre-migration validation
            migration_log.append({
                'step': 'pre_validation',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'started'
            })
            
            validation_result = await self._pre_migration_validation(
                old_document_class.Index.name
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'stage': 'pre_validation',
                    'error': validation_result['issues'],
                    'migration_log': migration_log
                }
            
            migration_log[-1]['status'] = 'completed'
            migration_log[-1]['result'] = validation_result
            
            # Step 2: Create rollback point
            migration_log.append({
                'step': 'create_rollback_point',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'started'
            })
            
            rollback_result = await self.rollback_manager.create_rollback_point(
                service_name, old_document_class.Index.name
            )
            
            if not rollback_result['success']:
                return {
                    'success': False,
                    'stage': 'rollback_point_creation',
                    'error': rollback_result['error'],
                    'migration_log': migration_log
                }
            
            rollback_id = rollback_result['rollback_id']
            migration_log[-1]['status'] = 'completed'
            migration_log[-1]['rollback_id'] = rollback_id
            
            # Step 3: Execute migration
            migration_log.append({
                'step': 'execute_migration',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'started'
            })
            
            migration_result = await self.migrator.blue_green_migration(
                service_name, old_document_class, new_document_class
            )
            
            if not migration_result['success']:
                # Attempt rollback
                await self.rollback_manager.execute_rollback(rollback_id)
                
                return {
                    'success': False,
                    'stage': 'migration_execution',
                    'error': migration_result['error'],
                    'rollback_executed': True,
                    'migration_log': migration_log
                }
            
            migration_log[-1]['status'] = 'completed'
            migration_log[-1]['result'] = migration_result
            
            # Step 4: Post-migration monitoring
            migration_log.append({
                'step': 'post_migration_monitoring',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'started'
            })
            
            monitoring_result = await self.health_monitor.monitor_and_rollback(
                service_name, rollback_id, monitoring_duration=600  # 10 minutes
            )
            
            migration_log[-1]['status'] = 'completed'
            migration_log[-1]['result'] = monitoring_result
            
            if monitoring_result['rollback_triggered']:
                return {
                    'success': False,
                    'stage': 'post_migration_monitoring',
                    'error': 'Health check failed, rollback triggered',
                    'monitoring_result': monitoring_result,
                    'migration_log': migration_log
                }
            
            # Step 5: Cleanup
            migration_log.append({
                'step': 'cleanup',
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'started'
            })
            
            # Optional: Clean up old index after successful migration
            cleanup_delay = migration_config.get('cleanup_delay_hours', 24)
            
            migration_log[-1]['status'] = 'scheduled'
            migration_log[-1]['cleanup_scheduled_for'] = (
                datetime.utcnow() + timedelta(hours=cleanup_delay)
            ).isoformat()
            
            return {
                'success': True,
                'migration_id': migration_result['migration_id'],
                'rollback_id': rollback_id,
                'migrated_documents': migration_result['migrated_documents'],
                'migration_log': migration_log
            }
            
        except Exception as e:
            # Emergency rollback
            try:
                await self.rollback_manager.execute_rollback(rollback_id)
                emergency_rollback = True
            except:
                emergency_rollback = False
            
            return {
                'success': False,
                'stage': 'unexpected_error',
                'error': str(e),
                'emergency_rollback_executed': emergency_rollback,
                'migration_log': migration_log
            }
    
    async def _pre_migration_validation(self, index_name: str) -> Dict[str, Any]:
        """Validate system before migration."""
        
        issues = []
        
        try:
            # Check cluster health
            health = await self.client.cluster.health()
            if health['status'] == 'red':
                issues.append('Cluster status is RED')
            
            # Check disk space
            stats = await self.client.cluster.stats()
            disk_usage = (
                (stats['nodes']['fs']['total_in_bytes'] - 
                 stats['nodes']['fs']['available_in_bytes']) / 
                stats['nodes']['fs']['total_in_bytes'] * 100
            )
            
            if disk_usage > 80:
                issues.append(f'High disk usage: {disk_usage:.1f}%')
            
            # Check index health
            index_stats = await self.client.indices.stats(index=index_name)
            if not index_stats.get('indices', {}).get(index_name):
                issues.append(f'Index {index_name} not found')
            
            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'cluster_health': health['status'],
                'disk_usage_percent': disk_usage
            }
            
        except Exception as e:
            return {
                'valid': False,
                'issues': [f'Validation error: {str(e)}']
            }
    
    async def schedule_migration(self, migration_config: Dict[str, Any],
                               scheduled_time: datetime) -> Dict[str, Any]:
        """Schedule migration for specific time."""
        
        import asyncio
        
        delay_seconds = (scheduled_time - datetime.utcnow()).total_seconds()
        
        if delay_seconds <= 0:
            return await self.execute_production_migration(migration_config)
        
        # Schedule the migration
        async def delayed_migration():
            await asyncio.sleep(delay_seconds)
            return await self.execute_production_migration(migration_config)
        
        # In production, this would use a proper task scheduler
        task = asyncio.create_task(delayed_migration())
        
        return {
            'migration_scheduled': True,
            'scheduled_time': scheduled_time.isoformat(),
            'delay_seconds': delay_seconds
        }

# Usage example
async def production_migration_example():
    """Example of production migration execution."""
    
    pipeline = ProductionMigrationPipeline()
    
    migration_config = {
        'service_name': 'blog_service',
        'old_document_class': BlogPostV2,
        'new_document_class': BlogPostV3,
        'cleanup_delay_hours': 48  # Keep old index for 48 hours
    }
    
    # Execute migration
    result = await pipeline.execute_production_migration(migration_config)
    
    if result['success']:
        print(f"Migration completed successfully!")
        print(f"Migration ID: {result['migration_id']}")
        print(f"Migrated documents: {result['migrated_documents']}")
    else:
        print(f"Migration failed at stage: {result['stage']}")
        print(f"Error: {result['error']}")
    
    return result
```

## Next Steps

1. **[FastAPI Integration](../03-fastapi-integration/01_query-builder-patterns.md)** - Integrating with FastAPI applications
2. **[Production Patterns](../06-production-patterns/01_performance-optimization.md)** - Production-ready configurations
3. **[Testing & Deployment](../07-testing-deployment/01_testing-strategies.md)** - Comprehensive testing approaches

## Additional Resources

- **Elasticsearch Reindex API**: [elastic.co/guide/en/elasticsearch/reference/current/docs-reindex.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-reindex.html)
- **Index Aliases**: [elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html)
- **Mapping Evolution**: [elastic.co/guide/en/elasticsearch/reference/current/mapping.html#mapping-limit-settings](https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html#mapping-limit-settings)