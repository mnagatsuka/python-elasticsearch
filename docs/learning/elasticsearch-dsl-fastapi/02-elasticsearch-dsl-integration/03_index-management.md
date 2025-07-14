# Index Management

Comprehensive guide to managing Elasticsearch indices, templates, and lifecycle policies with elasticsearch-dsl.

## Table of Contents
- [Index Creation & Configuration](#index-creation--configuration)
- [Index Templates & Patterns](#index-templates--patterns)
- [Lifecycle Management](#lifecycle-management)
- [Aliases & Zero-downtime Operations](#aliases--zero-downtime-operations)
- [Settings & Mapping Updates](#settings--mapping-updates)
- [Health Monitoring & Maintenance](#health-monitoring--maintenance)
- [Backup & Recovery](#backup--recovery)
- [Next Steps](#next-steps)

## Index Creation & Configuration

### Basic Index Setup
```python
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Integer, Date, Object
from elasticsearch_dsl.connections import connections
from elasticsearch.exceptions import RequestError
import asyncio
from typing import Dict, Any, Optional, List

class IndexManager:
    """Comprehensive index management service."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def create_index_with_settings(self, index_name: str, 
                                       settings: Dict[str, Any],
                                       mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Create index with custom settings and mappings."""
        
        try:
            response = await self.client.indices.create(
                index=index_name,
                body={
                    'settings': settings,
                    'mappings': mappings
                }
            )
            
            return {
                'success': True,
                'index': index_name,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except RequestError as e:
            if 'resource_already_exists_exception' in str(e):
                return {
                    'success': False,
                    'error': f'Index {index_name} already exists'
                }
            raise
    
    async def delete_index_safely(self, index_name: str, 
                                 confirm_deletion: bool = False) -> Dict[str, Any]:
        """Safely delete an index with confirmation."""
        
        if not confirm_deletion:
            return {
                'success': False,
                'error': 'Deletion not confirmed. Set confirm_deletion=True'
            }
        
        try:
            # Check if index exists first
            exists = await self.client.indices.exists(index=index_name)
            if not exists:
                return {
                    'success': False,
                    'error': f'Index {index_name} does not exist'
                }
            
            response = await self.client.indices.delete(index=index_name)
            
            return {
                'success': True,
                'index': index_name,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class ProductIndex(AsyncDocument):
    """Product document with optimized index configuration."""
    
    name = Text(
        analyzer='product_analyzer',
        search_analyzer='product_search_analyzer',
        fields={
            'keyword': Keyword(),
            'autocomplete': Text(analyzer='autocomplete_analyzer')
        }
    )
    
    description = Text(analyzer='english')
    brand = Keyword()
    category = Keyword()
    price = Object(
        properties={
            'amount': Integer(),
            'currency': Keyword()
        }
    )
    
    # Nested variants for size/color combinations
    variants = Object(
        properties={
            'sku': Keyword(),
            'size': Keyword(),
            'color': Keyword(),
            'stock': Integer()
        }
    )
    
    created_at = Date()
    updated_at = Date()
    
    class Index:
        name = 'products_v1'
        settings = {
            'number_of_shards': 2,
            'number_of_replicas': 1,
            'max_result_window': 50000,
            'analysis': {
                'analyzer': {
                    'product_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': [
                            'lowercase',
                            'asciifolding',
                            'product_synonym_filter',
                            'stop'
                        ]
                    },
                    'product_search_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': [
                            'lowercase',
                            'asciifolding',
                            'stop'
                        ]
                    },
                    'autocomplete_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'autocomplete_tokenizer',
                        'filter': ['lowercase']
                    }
                },
                'tokenizer': {
                    'autocomplete_tokenizer': {
                        'type': 'edge_ngram',
                        'min_gram': 2,
                        'max_gram': 20,
                        'token_chars': ['letter', 'digit']
                    }
                },
                'filter': {
                    'product_synonym_filter': {
                        'type': 'synonym',
                        'synonyms': [
                            'phone,mobile,smartphone',
                            'laptop,notebook,computer',
                            'tv,television,monitor'
                        ]
                    }
                }
            }
        }

# Usage examples
async def index_creation_examples():
    """Demonstrate index creation patterns."""
    
    index_manager = IndexManager()
    
    # Create product index
    await ProductIndex.init()
    
    # Create time-series index with custom settings
    time_series_settings = {
        'number_of_shards': 1,
        'number_of_replicas': 0,
        'index': {
            'codec': 'best_compression',
            'refresh_interval': '30s'
        }
    }
    
    time_series_mappings = {
        'properties': {
            'timestamp': {'type': 'date'},
            'metric_name': {'type': 'keyword'},
            'value': {'type': 'double'},
            'tags': {
                'type': 'object',
                'dynamic': True
            }
        }
    }
    
    result = await index_manager.create_index_with_settings(
        'metrics-2024',
        time_series_settings,
        time_series_mappings
    )
    
    return result
```

### Dynamic Index Creation
```python
from datetime import datetime, timedelta

class DynamicIndexManager:
    """Manager for dynamic index creation patterns."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def create_time_based_index(self, base_name: str, 
                                    date_pattern: str = '%Y-%m') -> str:
        """Create time-based index with current date."""
        
        current_date = datetime.utcnow()
        index_suffix = current_date.strftime(date_pattern)
        index_name = f"{base_name}-{index_suffix}"
        
        # Check if index already exists
        exists = await self.client.indices.exists(index=index_name)
        if exists:
            return index_name
        
        # Create index with time-series optimized settings
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1,
            'index': {
                'codec': 'best_compression',
                'refresh_interval': '30s',
                'number_of_routing_shards': 30
            }
        }
        
        mappings = {
            'properties': {
                'timestamp': {
                    'type': 'date',
                    'format': 'strict_date_optional_time||epoch_millis'
                },
                'message': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'level': {'type': 'keyword'},
                'source': {'type': 'keyword'},
                'tags': {'type': 'keyword'}
            }
        }
        
        await self.client.indices.create(
            index=index_name,
            body={
                'settings': settings,
                'mappings': mappings
            }
        )
        
        return index_name
    
    async def setup_index_rollover(self, alias_name: str, 
                                 base_pattern: str,
                                 conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Setup automatic index rollover."""
        
        initial_index = f"{base_pattern}-000001"
        
        # Create initial index
        await self.client.indices.create(
            index=initial_index,
            body={
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 1
                },
                'aliases': {
                    alias_name: {
                        'is_write_index': True
                    }
                }
            }
        )
        
        # Setup rollover policy
        policy_name = f"{alias_name}_rollover_policy"
        
        rollover_policy = {
            'policy': {
                'phases': {
                    'hot': {
                        'actions': {
                            'rollover': conditions
                        }
                    }
                }
            }
        }
        
        await self.client.ilm.put_lifecycle(
            name=policy_name,
            body=rollover_policy
        )
        
        return {
            'alias': alias_name,
            'initial_index': initial_index,
            'policy': policy_name
        }
    
    async def get_current_write_index(self, alias_name: str) -> Optional[str]:
        """Get the current write index for an alias."""
        
        try:
            aliases = await self.client.indices.get_alias(name=alias_name)
            
            for index_name, alias_info in aliases.items():
                if alias_info['aliases'][alias_name].get('is_write_index'):
                    return index_name
            
            return None
            
        except Exception:
            return None

# Time-series document class
class LogEntry(AsyncDocument):
    """Log entry for time-series data."""
    
    timestamp = Date()
    message = Text(analyzer='standard')
    level = Keyword()
    source = Keyword()
    tags = Keyword(multi=True)
    
    class Index:
        name = 'logs'  # This will be used as alias
    
    @classmethod
    async def setup_time_series_index(cls):
        """Setup time-series index structure."""
        manager = DynamicIndexManager()
        
        return await manager.setup_index_rollover(
            alias_name='logs',
            base_pattern='logs',
            conditions={
                'max_size': '1GB',
                'max_age': '7d',
                'max_docs': 1000000
            }
        )
```

## Index Templates & Patterns

### Component and Index Templates
```python
class TemplateManager:
    """Manager for Elasticsearch templates."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def create_component_template(self, name: str, 
                                      template_body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a component template for reuse."""
        
        try:
            response = await self.client.cluster.put_component_template(
                name=name,
                body=template_body
            )
            
            return {
                'success': True,
                'template_name': name,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_index_template(self, name: str, 
                                  index_patterns: List[str],
                                  composed_of: List[str] = None,
                                  template_body: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an index template."""
        
        template = {
            'index_patterns': index_patterns,
            'priority': 100
        }
        
        if composed_of:
            template['composed_of'] = composed_of
        
        if template_body:
            template.update(template_body)
        
        try:
            response = await self.client.indices.put_index_template(
                name=name,
                body=template
            )
            
            return {
                'success': True,
                'template_name': name,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def setup_application_templates(self) -> Dict[str, Any]:
        """Setup comprehensive template structure for application."""
        
        results = {}
        
        # Component template for common settings
        common_settings = {
            'template': {
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 1,
                    'refresh_interval': '1s',
                    'analysis': {
                        'analyzer': {
                            'app_text_analyzer': {
                                'type': 'custom',
                                'tokenizer': 'standard',
                                'filter': ['lowercase', 'asciifolding', 'stop']
                            }
                        }
                    }
                }
            }
        }
        
        results['common_settings'] = await self.create_component_template(
            'app_common_settings', common_settings
        )
        
        # Component template for timestamp mapping
        timestamp_mapping = {
            'template': {
                'mappings': {
                    'properties': {
                        'created_at': {'type': 'date'},
                        'updated_at': {'type': 'date'},
                        'timestamp': {'type': 'date'}
                    }
                }
            }
        }
        
        results['timestamp_mapping'] = await self.create_component_template(
            'app_timestamp_mapping', timestamp_mapping
        )
        
        # Component template for user tracking
        user_tracking_mapping = {
            'template': {
                'mappings': {
                    'properties': {
                        'created_by': {'type': 'keyword'},
                        'updated_by': {'type': 'keyword'},
                        'user_id': {'type': 'keyword'}
                    }
                }
            }
        }
        
        results['user_tracking'] = await self.create_component_template(
            'app_user_tracking', user_tracking_mapping
        )
        
        # Index template for application data
        app_template = {
            'index_patterns': ['app-*'],
            'composed_of': [
                'app_common_settings',
                'app_timestamp_mapping',
                'app_user_tracking'
            ],
            'template': {
                'settings': {
                    'index': {
                        'lifecycle': {
                            'name': 'app_data_policy'
                        }
                    }
                }
            }
        }
        
        results['app_template'] = await self.create_index_template(
            'app_data_template', 
            ['app-*'],
            template_body=app_template
        )
        
        # Index template for logs
        log_template = {
            'index_patterns': ['logs-*'],
            'composed_of': ['app_common_settings', 'app_timestamp_mapping'],
            'template': {
                'mappings': {
                    'properties': {
                        'message': {
                            'type': 'text',
                            'analyzer': 'app_text_analyzer'
                        },
                        'level': {'type': 'keyword'},
                        'source': {'type': 'keyword'},
                        'exception': {
                            'type': 'object',
                            'properties': {
                                'type': {'type': 'keyword'},
                                'message': {'type': 'text'},
                                'stack_trace': {'type': 'text'}
                            }
                        }
                    }
                }
            }
        }
        
        results['log_template'] = await self.create_index_template(
            'log_data_template',
            ['logs-*'],
            template_body=log_template
        )
        
        return results
    
    async def list_templates(self) -> Dict[str, Any]:
        """List all component and index templates."""
        
        try:
            component_templates = await self.client.cluster.get_component_template()
            index_templates = await self.client.indices.get_index_template()
            
            return {
                'component_templates': list(component_templates['component_templates'].keys()),
                'index_templates': list(index_templates['index_templates'].keys())
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
    
    async def validate_template(self, template_name: str, 
                              test_index: str) -> Dict[str, Any]:
        """Validate template by simulating index creation."""
        
        try:
            # Simulate index creation to validate template
            response = await self.client.indices.simulate_index_template(
                name=test_index
            )
            
            return {
                'valid': True,
                'resolved_settings': response.get('template', {}).get('settings', {}),
                'resolved_mappings': response.get('template', {}).get('mappings', {})
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }

# Document classes using templates
class ApplicationDocument(AsyncDocument):
    """Base document that leverages index templates."""
    
    title = Text(analyzer='app_text_analyzer')
    content = Text(analyzer='app_text_analyzer')
    
    class Meta:
        abstract = True
    
    @classmethod
    async def ensure_index_from_template(cls, index_suffix: str = None):
        """Ensure index exists using template."""
        if index_suffix:
            index_name = f"app-{cls.__name__.lower()}-{index_suffix}"
        else:
            index_name = f"app-{cls.__name__.lower()}"
        
        # Index will be created automatically with template settings
        # when first document is indexed
        cls._index._name = index_name
        return index_name

class BlogPost(ApplicationDocument):
    """Blog post using application template."""
    
    author = Keyword()
    category = Keyword()
    tags = Keyword(multi=True)
    
    class Index:
        name = 'app-blogpost'  # Will use app_data_template
```

## Lifecycle Management

### Index Lifecycle Policies
```python
class LifecycleManager:
    """Manager for index lifecycle policies."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def create_lifecycle_policy(self, policy_name: str, 
                                    policy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create an index lifecycle management policy."""
        
        try:
            response = await self.client.ilm.put_lifecycle(
                name=policy_name,
                body={'policy': policy_config}
            )
            
            return {
                'success': True,
                'policy_name': policy_name,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def setup_application_lifecycle_policies(self) -> Dict[str, Any]:
        """Setup comprehensive lifecycle policies."""
        
        results = {}
        
        # Hot-warm-cold policy for application data
        app_data_policy = {
            'phases': {
                'hot': {
                    'min_age': '0ms',
                    'actions': {
                        'rollover': {
                            'max_size': '5GB',
                            'max_age': '30d',
                            'max_docs': 10000000
                        },
                        'set_priority': {
                            'priority': 100
                        }
                    }
                },
                'warm': {
                    'min_age': '30d',
                    'actions': {
                        'allocate': {
                            'number_of_replicas': 0
                        },
                        'forcemerge': {
                            'max_num_segments': 1
                        },
                        'set_priority': {
                            'priority': 50
                        }
                    }
                },
                'cold': {
                    'min_age': '90d',
                    'actions': {
                        'allocate': {
                            'number_of_replicas': 0
                        },
                        'set_priority': {
                            'priority': 0
                        }
                    }
                },
                'delete': {
                    'min_age': '365d',
                    'actions': {
                        'delete': {}
                    }
                }
            }
        }
        
        results['app_data'] = await self.create_lifecycle_policy(
            'app_data_policy', app_data_policy
        )
        
        # Fast deletion policy for logs
        log_policy = {
            'phases': {
                'hot': {
                    'min_age': '0ms',
                    'actions': {
                        'rollover': {
                            'max_size': '1GB',
                            'max_age': '1d'
                        }
                    }
                },
                'delete': {
                    'min_age': '7d',
                    'actions': {
                        'delete': {}
                    }
                }
            }
        }
        
        results['logs'] = await self.create_lifecycle_policy(
            'log_retention_policy', log_policy
        )
        
        # Long-term retention for analytics
        analytics_policy = {
            'phases': {
                'hot': {
                    'min_age': '0ms',
                    'actions': {
                        'rollover': {
                            'max_size': '10GB',
                            'max_age': '30d'
                        }
                    }
                },
                'warm': {
                    'min_age': '30d',
                    'actions': {
                        'allocate': {
                            'number_of_replicas': 0
                        },
                        'forcemerge': {
                            'max_num_segments': 1
                        }
                    }
                },
                'cold': {
                    'min_age': '180d',
                    'actions': {
                        'searchable_snapshot': {
                            'snapshot_repository': 'backup_repository'
                        }
                    }
                }
            }
        }
        
        results['analytics'] = await self.create_lifecycle_policy(
            'analytics_retention_policy', analytics_policy
        )
        
        return results
    
    async def apply_policy_to_index(self, index_pattern: str, 
                                  policy_name: str) -> Dict[str, Any]:
        """Apply lifecycle policy to existing indices."""
        
        try:
            # Update index settings to use policy
            response = await self.client.indices.put_settings(
                index=index_pattern,
                body={
                    'settings': {
                        'index.lifecycle.name': policy_name
                    }
                }
            )
            
            return {
                'success': True,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_lifecycle_status(self, index_pattern: str) -> Dict[str, Any]:
        """Get lifecycle status for indices."""
        
        try:
            response = await self.client.ilm.explain_lifecycle(
                index=index_pattern
            )
            
            status_summary = {}
            for index_name, index_info in response['indices'].items():
                status_summary[index_name] = {
                    'policy': index_info.get('policy'),
                    'phase': index_info.get('phase'),
                    'action': index_info.get('action'),
                    'step': index_info.get('step'),
                    'age': index_info.get('age'),
                    'failed_step': index_info.get('failed_step')
                }
            
            return {
                'success': True,
                'indices': status_summary
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def manual_rollover(self, alias_name: str, 
                            conditions: Dict[str, Any] = None) -> Dict[str, Any]:
        """Manually trigger index rollover."""
        
        try:
            body = {}
            if conditions:
                body['conditions'] = conditions
            
            response = await self.client.indices.rollover(
                alias=alias_name,
                body=body
            )
            
            return {
                'success': True,
                'rolled_over': response.get('rolled_over', False),
                'old_index': response.get('old_index'),
                'new_index': response.get('new_index'),
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

### Automated Maintenance Tasks
```python
import asyncio
from datetime import datetime, timedelta

class MaintenanceScheduler:
    """Automated maintenance tasks for indices."""
    
    def __init__(self):
        self.client = connections.get_connection()
        self.lifecycle_manager = LifecycleManager()
    
    async def optimize_indices(self, index_pattern: str) -> Dict[str, Any]:
        """Optimize indices by force-merging segments."""
        
        try:
            # Get indices matching pattern
            indices = await self.client.indices.get(index=index_pattern)
            results = {}
            
            for index_name in indices.keys():
                # Check if index is in hot phase (don't optimize hot indices)
                lifecycle_status = await self.lifecycle_manager.get_lifecycle_status(index_name)
                
                if (lifecycle_status.get('success') and 
                    lifecycle_status['indices'][index_name]['phase'] != 'hot'):
                    
                    # Force merge to 1 segment
                    merge_response = await self.client.indices.forcemerge(
                        index=index_name,
                        max_num_segments=1,
                        wait_for_completion=False
                    )
                    
                    results[index_name] = {
                        'optimized': True,
                        'task_id': merge_response.get('task')
                    }
                else:
                    results[index_name] = {
                        'optimized': False,
                        'reason': 'Index in hot phase'
                    }
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cleanup_old_indices(self, patterns: List[str], 
                                age_threshold: timedelta = timedelta(days=365)) -> Dict[str, Any]:
        """Clean up old indices that exceed age threshold."""
        
        try:
            deleted_indices = []
            errors = []
            
            for pattern in patterns:
                try:
                    # Get all indices matching pattern
                    indices = await self.client.indices.get(index=pattern)
                    
                    for index_name, index_info in indices.items():
                        # Get index creation date
                        creation_date = index_info['settings']['index']['creation_date']
                        creation_datetime = datetime.fromtimestamp(int(creation_date) / 1000)
                        
                        if datetime.utcnow() - creation_datetime > age_threshold:
                            # Delete old index
                            await self.client.indices.delete(index=index_name)
                            deleted_indices.append({
                                'index': index_name,
                                'age': datetime.utcnow() - creation_datetime,
                                'creation_date': creation_datetime.isoformat()
                            })
                
                except Exception as e:
                    errors.append({
                        'pattern': pattern,
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'deleted_indices': deleted_indices,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def rebalance_shards(self) -> Dict[str, Any]:
        """Trigger cluster rebalancing."""
        
        try:
            # Enable shard allocation
            await self.client.cluster.put_settings(
                body={
                    'persistent': {
                        'cluster.routing.allocation.enable': 'all'
                    }
                }
            )
            
            # Trigger reroute
            response = await self.client.cluster.reroute(
                body={'commands': []},  # Empty commands trigger rebalancing
                retry_failed=True
            )
            
            return {
                'success': True,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def schedule_daily_maintenance(self):
        """Run daily maintenance tasks."""
        
        maintenance_tasks = [
            self.optimize_indices('logs-*'),
            self.cleanup_old_indices(['temp-*'], timedelta(days=7)),
            self.rebalance_shards()
        ]
        
        results = await asyncio.gather(*maintenance_tasks, return_exceptions=True)
        
        return {
            'optimization_result': results[0],
            'cleanup_result': results[1],
            'rebalance_result': results[2],
            'completed_at': datetime.utcnow().isoformat()
        }
```

## Aliases & Zero-downtime Operations

### Advanced Alias Management
```python
class AliasManager:
    """Advanced alias management for zero-downtime operations."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def atomic_alias_switch(self, alias_name: str, 
                                old_index: str, new_index: str) -> Dict[str, Any]:
        """Atomically switch alias from old index to new index."""
        
        try:
            # Atomic alias update
            response = await self.client.indices.update_aliases(
                body={
                    'actions': [
                        {'remove': {'index': old_index, 'alias': alias_name}},
                        {'add': {'index': new_index, 'alias': alias_name}}
                    ]
                }
            )
            
            return {
                'success': True,
                'acknowledged': response.get('acknowledged', False),
                'switched_from': old_index,
                'switched_to': new_index
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def blue_green_deployment(self, service_name: str, 
                                  new_mapping: Dict[str, Any],
                                  new_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Implement blue-green deployment pattern for index updates."""
        
        try:
            # Determine current and next indices
            current_alias = f"{service_name}_current"
            current_indices = await self.get_indices_for_alias(current_alias)
            
            if not current_indices:
                # First deployment
                blue_index = f"{service_name}_blue_v1"
                green_index = f"{service_name}_green_v1"
                version = 1
            else:
                # Determine next version
                current_index = current_indices[0]
                version = int(current_index.split('_v')[-1]) + 1
                
                if 'blue' in current_index:
                    # Switch to green
                    new_index = f"{service_name}_green_v{version}"
                    old_index = current_index
                else:
                    # Switch to blue
                    new_index = f"{service_name}_blue_v{version}"
                    old_index = current_index
            
            # Create new index
            index_body = {'mappings': new_mapping}
            if new_settings:
                index_body['settings'] = new_settings
            
            await self.client.indices.create(
                index=new_index,
                body=index_body
            )
            
            # If there's data to migrate, do it here
            if current_indices:
                await self._migrate_data(current_indices[0], new_index)
            
            # Switch alias atomically
            switch_result = await self.atomic_alias_switch(
                current_alias, 
                current_indices[0] if current_indices else None,
                new_index
            )
            
            return {
                'success': True,
                'new_index': new_index,
                'old_index': current_indices[0] if current_indices else None,
                'version': version,
                'switch_result': switch_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _migrate_data(self, source_index: str, target_index: str) -> Dict[str, Any]:
        """Migrate data from source to target index."""
        
        try:
            # Use reindex API for data migration
            response = await self.client.reindex(
                body={
                    'source': {'index': source_index},
                    'dest': {'index': target_index}
                },
                wait_for_completion=True,
                refresh=True
            )
            
            return {
                'success': True,
                'migrated_docs': response.get('total', 0),
                'took': response.get('took', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_indices_for_alias(self, alias_name: str) -> List[str]:
        """Get all indices associated with an alias."""
        
        try:
            aliases = await self.client.indices.get_alias(name=alias_name)
            return list(aliases.keys())
        except Exception:
            return []
    
    async def create_filtered_alias(self, alias_name: str, index_name: str, 
                                  filter_query: Dict[str, Any],
                                  routing: str = None) -> Dict[str, Any]:
        """Create filtered alias for data partitioning."""
        
        try:
            alias_body = {
                'filter': filter_query
            }
            
            if routing:
                alias_body['routing'] = routing
            
            response = await self.client.indices.put_alias(
                index=index_name,
                name=alias_name,
                body=alias_body
            )
            
            return {
                'success': True,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def setup_multi_tenant_aliases(self, base_index: str, 
                                       tenants: List[str]) -> Dict[str, Any]:
        """Setup filtered aliases for multi-tenant architecture."""
        
        results = {}
        
        for tenant in tenants:
            alias_name = f"{base_index}_{tenant}"
            filter_query = {
                'term': {
                    'tenant_id': tenant
                }
            }
            
            result = await self.create_filtered_alias(
                alias_name, 
                base_index, 
                filter_query,
                routing=tenant  # Route to specific shard
            )
            
            results[tenant] = result
        
        return results

# Zero-downtime document operations
class ZeroDowntimeService:
    """Service for zero-downtime operations."""
    
    def __init__(self):
        self.alias_manager = AliasManager()
    
    async def safe_mapping_update(self, service_name: str, 
                                new_mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Safely update mappings without downtime."""
        
        # Use blue-green deployment for mapping changes
        return await self.alias_manager.blue_green_deployment(
            service_name, 
            new_mappings
        )
    
    async def safe_settings_update(self, index_name: str, 
                                 new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Safely update index settings."""
        
        try:
            # Some settings can be updated on live index
            dynamic_settings = {
                'number_of_replicas': new_settings.get('number_of_replicas'),
                'refresh_interval': new_settings.get('refresh_interval'),
                'max_result_window': new_settings.get('max_result_window')
            }
            
            # Filter out None values
            dynamic_settings = {k: v for k, v in dynamic_settings.items() if v is not None}
            
            if dynamic_settings:
                response = await self.client.indices.put_settings(
                    index=index_name,
                    body={'settings': dynamic_settings}
                )
                
                return {
                    'success': True,
                    'updated_settings': dynamic_settings,
                    'acknowledged': response.get('acknowledged', False)
                }
            
            return {
                'success': True,
                'message': 'No dynamic settings to update'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

## Settings & Mapping Updates

### Dynamic Updates
```python
class SettingsManager:
    """Manager for index settings and mapping updates."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def update_dynamic_settings(self, index_pattern: str, 
                                    settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update settings that can be changed on live indices."""
        
        # Dynamic settings that can be updated
        allowed_dynamic_settings = {
            'number_of_replicas',
            'refresh_interval',
            'max_result_window',
            'max_rescore_window',
            'blocks.read_only',
            'blocks.write',
            'priority'
        }
        
        # Filter to only allowed dynamic settings
        dynamic_settings = {
            k: v for k, v in settings.items() 
            if k in allowed_dynamic_settings
        }
        
        if not dynamic_settings:
            return {
                'success': False,
                'error': 'No dynamic settings provided'
            }
        
        try:
            response = await self.client.indices.put_settings(
                index=index_pattern,
                body={'settings': dynamic_settings}
            )
            
            return {
                'success': True,
                'updated_settings': dynamic_settings,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def add_field_mapping(self, index_name: str, 
                              field_mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Add new fields to existing mapping."""
        
        try:
            response = await self.client.indices.put_mapping(
                index=index_name,
                body={
                    'properties': field_mappings
                }
            )
            
            return {
                'success': True,
                'added_fields': list(field_mappings.keys()),
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_analysis_settings(self, index_name: str,
                                     analyzers: Dict[str, Any] = None,
                                     filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update analysis settings (requires index close/open)."""
        
        try:
            # Close index
            await self.client.indices.close(index=index_name)
            
            # Prepare analysis settings
            analysis_settings = {}
            if analyzers:
                analysis_settings['analyzer'] = analyzers
            if filters:
                analysis_settings['filter'] = filters
            
            # Update settings
            response = await self.client.indices.put_settings(
                index=index_name,
                body={
                    'settings': {
                        'analysis': analysis_settings
                    }
                }
            )
            
            # Reopen index
            await self.client.indices.open(index=index_name)
            
            return {
                'success': True,
                'updated_analysis': analysis_settings,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            # Try to reopen index if something went wrong
            try:
                await self.client.indices.open(index=index_name)
            except:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def bulk_settings_update(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply multiple settings updates efficiently."""
        
        results = {}
        
        for update in updates:
            index_pattern = update['index_pattern']
            settings = update['settings']
            operation_type = update.get('type', 'dynamic')
            
            if operation_type == 'dynamic':
                result = await self.update_dynamic_settings(index_pattern, settings)
            elif operation_type == 'analysis':
                result = await self.update_analysis_settings(
                    index_pattern,
                    settings.get('analyzers'),
                    settings.get('filters')
                )
            else:
                result = {'success': False, 'error': f'Unknown operation type: {operation_type}'}
            
            results[index_pattern] = result
        
        return results

# Example usage with document classes
class EvolvingDocument(AsyncDocument):
    """Document that demonstrates mapping evolution."""
    
    # Original fields
    title = Text()
    content = Text()
    author = Keyword()
    
    class Index:
        name = 'evolving_docs'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1
        }
    
    @classmethod
    async def add_new_fields(cls):
        """Add new fields to existing mapping."""
        settings_manager = SettingsManager()
        
        new_fields = {
            'tags': {'type': 'keyword'},
            'view_count': {'type': 'integer'},
            'last_modified': {'type': 'date'},
            'metadata': {
                'type': 'object',
                'properties': {
                    'word_count': {'type': 'integer'},
                    'reading_time': {'type': 'integer'}
                }
            }
        }
        
        return await settings_manager.add_field_mapping(
            cls.Index.name,
            new_fields
        )
    
    @classmethod
    async def update_analyzers(cls):
        """Update analysis configuration."""
        settings_manager = SettingsManager()
        
        new_analyzers = {
            'content_analyzer_v2': {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': ['lowercase', 'stop', 'snowball']
            }
        }
        
        return await settings_manager.update_analysis_settings(
            cls.Index.name,
            analyzers=new_analyzers
        )
```

## Health Monitoring & Maintenance

### Comprehensive Health Monitoring
```python
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class HealthStatus(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

@dataclass
class IndexHealth:
    name: str
    status: HealthStatus
    shards_total: int
    shards_active: int
    shards_unassigned: int
    docs_count: int
    size_in_bytes: int
    
class HealthMonitor:
    """Comprehensive health monitoring service."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def get_cluster_health(self) -> Dict[str, Any]:
        """Get overall cluster health."""
        
        try:
            health = await self.client.cluster.health(
                wait_for_status='yellow',
                timeout='10s'
            )
            
            stats = await self.client.cluster.stats()
            
            return {
                'status': health['status'],
                'number_of_nodes': health['number_of_nodes'],
                'number_of_data_nodes': health['number_of_data_nodes'],
                'active_primary_shards': health['active_primary_shards'],
                'active_shards': health['active_shards'],
                'unassigned_shards': health['unassigned_shards'],
                'pending_tasks': health['number_of_pending_tasks'],
                'max_task_wait_time': health['task_max_waiting_in_queue_millis'],
                'disk_usage': {
                    'total': stats['nodes']['fs']['total_in_bytes'],
                    'available': stats['nodes']['fs']['available_in_bytes'],
                    'used_percent': (
                        (stats['nodes']['fs']['total_in_bytes'] - 
                         stats['nodes']['fs']['available_in_bytes']) / 
                        stats['nodes']['fs']['total_in_bytes'] * 100
                    )
                },
                'memory_usage': {
                    'heap_used': stats['nodes']['jvm']['mem']['heap_used_in_bytes'],
                    'heap_max': stats['nodes']['jvm']['mem']['heap_max_in_bytes'],
                    'heap_used_percent': stats['nodes']['jvm']['mem']['heap_used_percent']
                }
            }
            
        except Exception as e:
            return {
                'status': 'red',
                'error': str(e)
            }
    
    async def get_index_health(self, index_pattern: str = '*') -> List[IndexHealth]:
        """Get health status for indices."""
        
        try:
            health = await self.client.indices.stats(index=index_pattern)
            cluster_health = await self.client.cluster.health(level='indices')
            
            indices_health = []
            
            for index_name, index_stats in health['indices'].items():
                cluster_index_health = cluster_health['indices'].get(index_name, {})
                
                index_health = IndexHealth(
                    name=index_name,
                    status=HealthStatus(cluster_index_health.get('status', 'red')),
                    shards_total=cluster_index_health.get('number_of_shards', 0),
                    shards_active=cluster_index_health.get('active_shards', 0),
                    shards_unassigned=cluster_index_health.get('unassigned_shards', 0),
                    docs_count=index_stats['total']['docs']['count'],
                    size_in_bytes=index_stats['total']['store']['size_in_bytes']
                )
                
                indices_health.append(index_health)
            
            return indices_health
            
        except Exception as e:
            return []
    
    async def check_shard_allocation(self) -> Dict[str, Any]:
        """Check shard allocation issues."""
        
        try:
            allocation = await self.client.cluster.allocation_explain()
            unassigned_shards = await self.client.cat.shards(
                format='json',
                h='index,shard,prirep,state,unassigned.reason'
            )
            
            unassigned_info = [
                shard for shard in unassigned_shards 
                if shard['state'] == 'UNASSIGNED'
            ]
            
            return {
                'has_unassigned_shards': len(unassigned_info) > 0,
                'unassigned_count': len(unassigned_info),
                'unassigned_shards': unassigned_info,
                'allocation_explanation': allocation
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
    
    async def performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        
        try:
            nodes_stats = await self.client.nodes.stats(
                metric=['indices', 'os', 'process', 'jvm', 'thread_pool']
            )
            
            # Aggregate metrics across nodes
            total_search_queries = 0
            total_indexing_operations = 0
            avg_query_time = 0
            avg_indexing_time = 0
            
            node_count = len(nodes_stats['nodes'])
            
            for node_id, node_stats in nodes_stats['nodes'].items():
                indices_stats = node_stats.get('indices', {})
                
                search_stats = indices_stats.get('search', {})
                total_search_queries += search_stats.get('query_total', 0)
                avg_query_time += search_stats.get('query_time_in_millis', 0)
                
                indexing_stats = indices_stats.get('indexing', {})
                total_indexing_operations += indexing_stats.get('index_total', 0)
                avg_indexing_time += indexing_stats.get('index_time_in_millis', 0)
            
            return {
                'search': {
                    'total_queries': total_search_queries,
                    'avg_query_time_ms': avg_query_time / node_count if node_count > 0 else 0
                },
                'indexing': {
                    'total_operations': total_indexing_operations,
                    'avg_indexing_time_ms': avg_indexing_time / node_count if node_count > 0 else 0
                },
                'node_count': node_count
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check."""
        
        results = await asyncio.gather(
            self.get_cluster_health(),
            self.get_index_health(),
            self.check_shard_allocation(),
            self.performance_metrics(),
            return_exceptions=True
        )
        
        return {
            'cluster_health': results[0],
            'indices_health': results[1],
            'shard_allocation': results[2],
            'performance_metrics': results[3],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def setup_monitoring_alerts(self) -> Dict[str, Any]:
        """Setup basic monitoring alerts using watchers (if available)."""
        
        # This would integrate with Elasticsearch Watcher or external monitoring
        alert_configs = {
            'cluster_red_alert': {
                'condition': 'cluster.status == "red"',
                'action': 'send_notification',
                'message': 'Cluster status is RED - immediate attention required'
            },
            'disk_space_alert': {
                'condition': 'disk.used_percent > 85',
                'action': 'send_notification',
                'message': 'Disk space usage above 85%'
            },
            'unassigned_shards_alert': {
                'condition': 'cluster.unassigned_shards > 0',
                'action': 'send_notification',
                'message': 'Unassigned shards detected'
            }
        }
        
        return {
            'alert_configs': alert_configs,
            'note': 'Alerts would be configured in monitoring system'
        }

# Automated monitoring service
class AutomatedMonitoring:
    """Automated monitoring with scheduled checks."""
    
    def __init__(self, check_interval: int = 300):  # 5 minutes
        self.health_monitor = HealthMonitor()
        self.check_interval = check_interval
        self.is_running = False
    
    async def start_monitoring(self):
        """Start automated monitoring loop."""
        
        self.is_running = True
        
        while self.is_running:
            try:
                health_report = await self.health_monitor.run_health_check()
                await self.process_health_report(health_report)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop monitoring loop."""
        self.is_running = False
    
    async def process_health_report(self, health_report: Dict[str, Any]):
        """Process health report and take actions."""
        
        cluster_health = health_report.get('cluster_health', {})
        
        # Check for critical issues
        if cluster_health.get('status') == 'red':
            await self.handle_critical_alert('Cluster status RED', cluster_health)
        
        # Check disk usage
        disk_usage = cluster_health.get('disk_usage', {})
        if disk_usage.get('used_percent', 0) > 90:
            await self.handle_warning_alert('High disk usage', disk_usage)
        
        # Check unassigned shards
        if cluster_health.get('unassigned_shards', 0) > 0:
            await self.handle_warning_alert('Unassigned shards detected', cluster_health)
        
        # Log health report
        print(f"Health check completed: {health_report['timestamp']}")
    
    async def handle_critical_alert(self, message: str, details: Dict[str, Any]):
        """Handle critical alerts."""
        print(f"CRITICAL ALERT: {message}")
        print(f"Details: {details}")
        # Here you would integrate with alerting systems
    
    async def handle_warning_alert(self, message: str, details: Dict[str, Any]):
        """Handle warning alerts."""
        print(f"WARNING: {message}")
        print(f"Details: {details}")
        # Here you would integrate with alerting systems
```

## Backup & Recovery

### Snapshot Management
```python
class SnapshotManager:
    """Manager for backup and recovery operations."""
    
    def __init__(self):
        self.client = connections.get_connection()
    
    async def create_repository(self, repo_name: str, 
                              repo_type: str = 'fs',
                              settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create snapshot repository."""
        
        default_settings = {
            'location': f'/backup/{repo_name}'
        }
        
        if settings:
            default_settings.update(settings)
        
        try:
            response = await self.client.snapshot.create_repository(
                repository=repo_name,
                body={
                    'type': repo_type,
                    'settings': default_settings
                }
            )
            
            return {
                'success': True,
                'repository': repo_name,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_snapshot(self, repo_name: str, snapshot_name: str,
                            indices: List[str] = None,
                            include_global_state: bool = True) -> Dict[str, Any]:
        """Create snapshot of indices."""
        
        snapshot_body = {
            'include_global_state': include_global_state,
            'ignore_unavailable': True,
            'partial': False
        }
        
        if indices:
            snapshot_body['indices'] = ','.join(indices)
        
        try:
            response = await self.client.snapshot.create(
                repository=repo_name,
                snapshot=snapshot_name,
                body=snapshot_body,
                wait_for_completion=False  # Run in background
            )
            
            return {
                'success': True,
                'snapshot': snapshot_name,
                'repository': repo_name,
                'accepted': response.get('accepted', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def restore_snapshot(self, repo_name: str, snapshot_name: str,
                             indices: List[str] = None,
                             rename_pattern: str = None,
                             rename_replacement: str = None) -> Dict[str, Any]:
        """Restore snapshot."""
        
        restore_body = {
            'ignore_unavailable': True,
            'include_global_state': False
        }
        
        if indices:
            restore_body['indices'] = ','.join(indices)
        
        if rename_pattern and rename_replacement:
            restore_body['rename_pattern'] = rename_pattern
            restore_body['rename_replacement'] = rename_replacement
        
        try:
            response = await self.client.snapshot.restore(
                repository=repo_name,
                snapshot=snapshot_name,
                body=restore_body,
                wait_for_completion=False
            )
            
            return {
                'success': True,
                'snapshot': snapshot_name,
                'repository': repo_name,
                'accepted': response.get('accepted', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def list_snapshots(self, repo_name: str) -> Dict[str, Any]:
        """List all snapshots in repository."""
        
        try:
            response = await self.client.snapshot.get(
                repository=repo_name,
                snapshot='*'
            )
            
            snapshots = []
            for snapshot in response.get('snapshots', []):
                snapshots.append({
                    'name': snapshot['snapshot'],
                    'state': snapshot['state'],
                    'start_time': snapshot['start_time'],
                    'end_time': snapshot.get('end_time'),
                    'duration_in_millis': snapshot.get('duration_in_millis'),
                    'indices': snapshot['indices'],
                    'shards': snapshot['shards']
                })
            
            return {
                'success': True,
                'snapshots': snapshots
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_snapshot(self, repo_name: str, snapshot_name: str) -> Dict[str, Any]:
        """Delete snapshot."""
        
        try:
            response = await self.client.snapshot.delete(
                repository=repo_name,
                snapshot=snapshot_name
            )
            
            return {
                'success': True,
                'acknowledged': response.get('acknowledged', False)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def automated_backup_schedule(self, indices_patterns: List[str],
                                      repo_name: str = 'automated_backups') -> Dict[str, Any]:
        """Setup automated backup schedule."""
        
        from datetime import datetime, timedelta
        
        # Create repository if it doesn't exist
        await self.create_repository(repo_name)
        
        # Create daily snapshot
        today = datetime.utcnow()
        snapshot_name = f"daily-{today.strftime('%Y-%m-%d')}"
        
        result = await self.create_snapshot(
            repo_name,
            snapshot_name,
            indices_patterns
        )
        
        # Clean up old snapshots (keep last 7 days)
        snapshots_list = await self.list_snapshots(repo_name)
        
        if snapshots_list['success']:
            cutoff_date = today - timedelta(days=7)
            
            for snapshot in snapshots_list['snapshots']:
                snapshot_date_str = snapshot['name'].replace('daily-', '')
                try:
                    snapshot_date = datetime.strptime(snapshot_date_str, '%Y-%m-%d')
                    if snapshot_date < cutoff_date:
                        await self.delete_snapshot(repo_name, snapshot['name'])
                except ValueError:
                    # Skip snapshots that don't match expected format
                    continue
        
        return {
            'backup_created': result,
            'cleanup_completed': True
        }

# Usage examples
async def backup_examples():
    """Demonstrate backup and recovery operations."""
    
    snapshot_manager = SnapshotManager()
    
    # Setup repository
    repo_result = await snapshot_manager.create_repository(
        'production_backups',
        settings={'location': '/backup/production'}
    )
    
    # Create snapshot
    snapshot_result = await snapshot_manager.create_snapshot(
        'production_backups',
        'backup-2024-01-15',
        ['blog_posts*', 'user_profiles*']
    )
    
    # List snapshots
    snapshots = await snapshot_manager.list_snapshots('production_backups')
    
    return {
        'repository': repo_result,
        'snapshot': snapshot_result,
        'snapshots_list': snapshots
    }
```

## Next Steps

1. **[Migration Strategies](04_migration-strategies.md)** - Schema evolution and data migration patterns
2. **[FastAPI Integration](../03-fastapi-integration/01_query-builder-patterns.md)** - Integrating with FastAPI applications
3. **[Production Patterns](../06-production-patterns/01_performance-optimization.md)** - Production-ready configurations

## Additional Resources

- **Index Management API**: [elastic.co/guide/en/elasticsearch/reference/current/index-mgmt.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-mgmt.html)
- **Index Lifecycle Management**: [elastic.co/guide/en/elasticsearch/reference/current/index-lifecycle-management.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-lifecycle-management.html)
- **Snapshot and Restore**: [elastic.co/guide/en/elasticsearch/reference/current/snapshot-restore.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/snapshot-restore.html)