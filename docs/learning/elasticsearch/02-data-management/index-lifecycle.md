# Index Lifecycle

**Master index management, aliases, and templates for scalable Elasticsearch deployments**

*Estimated reading time: 25 minutes*

## Overview

Index lifecycle management is crucial for maintaining healthy Elasticsearch clusters. This guide covers index creation, management, aliases, templates, and lifecycle policies that help you organize data efficiently and manage storage costs.

## 📋 Table of Contents

1. [Index Creation & Settings](#index-creation--settings)
2. [Index Aliases](#index-aliases)
3. [Index Templates](#index-templates)
4. [Reindexing](#reindexing)
5. [Index Lifecycle Management (ILM)](#index-lifecycle-management-ilm)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Best Practices](#best-practices)

## 🏗️ Index Creation & Settings

### Basic Index Creation

```bash
# Create simple index
curl -X PUT "localhost:9200/my-index"

# Create index with settings
curl -X PUT "localhost:9200/blog" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "refresh_interval": "1s",
    "max_result_window": 10000
  }
}
'
```

### Index Settings Explained

**Core Settings:**
```json
{
  "settings": {
    "number_of_shards": 1,        // Primary shards (fixed at creation)
    "number_of_replicas": 1,      // Replica shards (can be changed)
    "refresh_interval": "1s",     // How often to refresh index
    "max_result_window": 10000,   // Maximum from + size for search
    "max_rescore_window": 10000   // Maximum rescore window
  }
}
```

**Analysis Settings:**
```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "custom_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop"]
        }
      },
      "tokenizer": {
        "custom_tokenizer": {
          "type": "pattern",
          "pattern": "[\\W]+"
        }
      }
    }
  }
}
```

### Update Index Settings

```bash
# Update dynamic settings
curl -X PUT "localhost:9200/blog/_settings" -H 'Content-Type: application/json' -d'
{
  "number_of_replicas": 2,
  "refresh_interval": "30s"
}
'

# Close index to update static settings
curl -X POST "localhost:9200/blog/_close"

curl -X PUT "localhost:9200/blog/_settings" -H 'Content-Type: application/json' -d'
{
  "analysis": {
    "analyzer": {
      "new_analyzer": {
        "type": "keyword"
      }
    }
  }
}
'

# Reopen index
curl -X POST "localhost:9200/blog/_open"
```

## 🔗 Index Aliases

Aliases provide a way to refer to indices with alternate names and enable zero-downtime reindexing.

### Creating Aliases

```bash
# Create simple alias
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {
      "add": {
        "index": "blog-2024-01",
        "alias": "blog-current"
      }
    }
  ]
}
'

# Create alias with filter
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {
      "add": {
        "index": "blog-2024-01",
        "alias": "published-posts",
        "filter": {
          "term": {
            "status": "published"
          }
        }
      }
    }
  ]
}
'
```

### Multiple Index Operations

```bash
# Atomic alias operations
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {
      "remove": {
        "index": "blog-2024-01",
        "alias": "blog-current"
      }
    },
    {
      "add": {
        "index": "blog-2024-02", 
        "alias": "blog-current"
      }
    }
  ]
}
'

# Point alias to multiple indices
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {
      "add": {
        "indices": ["blog-2024-01", "blog-2024-02"],
        "alias": "blog-all"
      }
    }
  ]
}
'
```

### Alias Management

```bash
# List all aliases
curl "localhost:9200/_alias?pretty"

# Get specific alias
curl "localhost:9200/_alias/blog-current?pretty"

# Get aliases for index
curl "localhost:9200/blog-2024-01/_alias?pretty"

# Check if alias exists
curl -I "localhost:9200/_alias/blog-current"
```

### Write Index for Aliases

```bash
# Set write index for rollover
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {
      "add": {
        "index": "blog-2024-01",
        "alias": "blog",
        "is_write_index": false
      }
    },
    {
      "add": {
        "index": "blog-2024-02",
        "alias": "blog", 
        "is_write_index": true
      }
    }
  ]
}
'
```

## 📋 Index Templates

Templates automatically apply settings and mappings to new indices that match a pattern.

### Index Templates (v2)

```bash
# Create index template
curl -X PUT "localhost:9200/_index_template/blog_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["blog-*"],
  "priority": 100,
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "refresh_interval": "5s"
    },
    "mappings": {
      "properties": {
        "title": {
          "type": "text",
          "fields": {
            "keyword": {"type": "keyword"}
          }
        },
        "author": {"type": "keyword"},
        "content": {"type": "text"},
        "published_date": {"type": "date"},
        "tags": {"type": "keyword"},
        "view_count": {"type": "integer"}
      }
    },
    "aliases": {
      "blog-search": {}
    }
  }
}
'
```

### Component Templates

```bash
# Create component template for common settings
curl -X PUT "localhost:9200/_component_template/common_settings" -H 'Content-Type: application/json' -d'
{
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    }
  }
}
'

# Create component template for common mappings
curl -X PUT "localhost:9200/_component_template/timestamp_mapping" -H 'Content-Type: application/json' -d'
{
  "template": {
    "mappings": {
      "properties": {
        "@timestamp": {"type": "date"},
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"}
      }
    }
  }
}
'

# Use component templates in index template
curl -X PUT "localhost:9200/_index_template/logs_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["logs-*"],
  "composed_of": ["common_settings", "timestamp_mapping"],
  "priority": 200,
  "template": {
    "mappings": {
      "properties": {
        "message": {"type": "text"},
        "level": {"type": "keyword"}
      }
    }
  }
}
'
```

### Template Management

```bash
# List index templates
curl "localhost:9200/_index_template?pretty"

# Get specific template
curl "localhost:9200/_index_template/blog_template?pretty"

# Delete template
curl -X DELETE "localhost:9200/_index_template/blog_template"

# Simulate template application
curl -X POST "localhost:9200/_index_template/_simulate_index/blog-2024-03?pretty"
```

## 🔄 Reindexing

Reindexing allows you to copy documents from one index to another, often with changes to mapping or settings.

### Basic Reindexing

```bash
# Reindex from source to destination
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "old-blog"
  },
  "dest": {
    "index": "new-blog"
  }
}
'
```

### Reindexing with Query

```bash
# Reindex subset of documents
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "blog",
    "query": {
      "range": {
        "published_date": {
          "gte": "2024-01-01"
        }
      }
    }
  },
  "dest": {
    "index": "blog-2024"
  }
}
'
```

### Reindexing with Script

```bash
# Transform documents during reindex
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "old-products"
  },
  "dest": {
    "index": "new-products"
  },
  "script": {
    "source": "ctx._source.price = ctx._source.price * 1.1; ctx._source.updated_at = '\'2024-01-18T10:00:00Z\''"
  }
}
'
```

### Remote Reindexing

```bash
# Reindex from remote cluster
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "remote": {
      "host": "http://remote-cluster:9200",
      "username": "user",
      "password": "pass"
    },
    "index": "remote-index"
  },
  "dest": {
    "index": "local-index"
  }
}
'
```

### Async Reindexing

```bash
# Start async reindex task
curl -X POST "localhost:9200/_reindex?wait_for_completion=false" -H 'Content-Type: application/json' -d'
{
  "source": {"index": "large-index"},
  "dest": {"index": "new-large-index"}
}
'

# Response includes task ID
{
  "task": "r1A2WoRbTwKZ516z6NEs5A:36619"
}

# Check task status
curl "localhost:9200/_tasks/r1A2WoRbTwKZ516z6NEs5A:36619?pretty"

# Cancel task if needed
curl -X POST "localhost:9200/_tasks/r1A2WoRbTwKZ516z6NEs5A:36619/_cancel"
```

## ⏰ Index Lifecycle Management (ILM)

ILM automatically manages indices through their lifecycle phases.

### ILM Policy Creation

```bash
# Create ILM policy
curl -X PUT "localhost:9200/_ilm/policy/blog_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_size": "1GB",
            "max_age": "7d",
            "max_docs": 100000
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "allocate": {
            "number_of_replicas": 0
          },
          "set_priority": {
            "priority": 50
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
'
```

### Bootstrap Index with ILM

```bash
# Create index template with ILM
curl -X PUT "localhost:9200/_index_template/blog_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["blog-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "blog_policy",
      "index.lifecycle.rollover_alias": "blog"
    }
  }
}
'

# Create initial index
curl -X PUT "localhost:9200/blog-000001" -H 'Content-Type: application/json' -d'
{
  "aliases": {
    "blog": {
      "is_write_index": true
    }
  }
}
'
```

### ILM Management

```bash
# Get ILM policy
curl "localhost:9200/_ilm/policy/blog_policy?pretty"

# Get ILM status
curl "localhost:9200/_ilm/status?pretty"

# Start/stop ILM
curl -X POST "localhost:9200/_ilm/start"
curl -X POST "localhost:9200/_ilm/stop"

# Explain index lifecycle
curl "localhost:9200/blog-000001/_ilm/explain?pretty"

# Manually move to next phase
curl -X POST "localhost:9200/_ilm/move/blog-000001" -H 'Content-Type: application/json' -d'
{
  "current_step": {
    "phase": "hot",
    "action": "rollover",
    "name": "check-rollover-ready"
  },
  "next_step": {
    "phase": "warm",
    "action": "allocate",
    "name": "allocate"
  }
}
'
```

## 📊 Monitoring & Maintenance

### Index Statistics

```bash
# Get index stats
curl "localhost:9200/_stats?pretty"

# Get specific index stats
curl "localhost:9200/blog/_stats?pretty"

# Get stats for specific metrics
curl "localhost:9200/blog/_stats/indexing,search?pretty"
```

### Health Monitoring

```bash
# Cluster health
curl "localhost:9200/_cluster/health?pretty"

# Index health
curl "localhost:9200/_cluster/health/blog?pretty"

# Shard allocation
curl "localhost:9200/_cat/shards/blog?v"

# Recovery status
curl "localhost:9200/_recovery/blog?pretty"
```

### Index Operations

```bash
# Force merge (optimize)
curl -X POST "localhost:9200/blog/_forcemerge?max_num_segments=1"

# Refresh index
curl -X POST "localhost:9200/blog/_refresh"

# Flush index
curl -X POST "localhost:9200/blog/_flush"

# Clear cache
curl -X POST "localhost:9200/blog/_cache/clear"
```

### Shrinking Indices

```bash
# Prepare index for shrinking
curl -X PUT "localhost:9200/blog/_settings" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.routing.allocation.require._name": "shrink_node",
    "index.blocks.write": true
  }
}
'

# Shrink index
curl -X POST "localhost:9200/blog/_shrink/blog-shrunk" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "index.routing.allocation.require._name": null,
    "index.blocks.write": null
  }
}
'
```

## 🎯 Real-world Examples

### Time-based Index Strategy

```bash
# Create template for daily indices
curl -X PUT "localhost:9200/_index_template/logs_daily" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs_policy",
      "index.lifecycle.rollover_alias": "logs"
    },
    "mappings": {
      "properties": {
        "@timestamp": {"type": "date"},
        "level": {"type": "keyword"},
        "message": {"type": "text"},
        "service": {"type": "keyword"}
      }
    }
  }
}
'

# Create ILM policy for logs
curl -X PUT "localhost:9200/_ilm/policy/logs_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "5GB",
            "max_age": "1d"
          }
        }
      },
      "warm": {
        "min_age": "1d",
        "actions": {
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
'
```

### Blue-Green Deployment Pattern

```bash
# Current production index
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {
      "add": {
        "index": "products-v1",
        "alias": "products"
      }
    }
  ]
}
'

# Prepare new version
curl -X PUT "localhost:9200/products-v2" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "name": {"type": "text"},
      "new_field": {"type": "keyword"}
    }
  }
}
'

# Reindex with updates
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {"index": "products-v1"},
  "dest": {"index": "products-v2"},
  "script": {
    "source": "ctx._source.new_field = '\''default_value'\''"
  }
}
'

# Switch alias atomically
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {"remove": {"index": "products-v1", "alias": "products"}},
    {"add": {"index": "products-v2", "alias": "products"}}
  ]
}
'
```

## 🚀 Best Practices

### Index Naming

```bash
# ✅ Good: Descriptive with version/date
blog-posts-2024-01
user-profiles-v2
application-logs-2024-01-18

# ❌ Bad: Generic or unclear
index1
data
logs
```

### Shard Strategy

```bash
# ✅ Good: Reasonable shard count
curl -X PUT "localhost:9200/medium-dataset" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 3,    // For ~10GB dataset
    "number_of_replicas": 1
  }
}
'

# ❌ Bad: Over-sharding
curl -X PUT "localhost:9200/small-dataset" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 20,   // Too many for 1GB dataset
    "number_of_replicas": 1
  }
}
'
```

### Alias Usage

```bash
# ✅ Good: Always use aliases for applications
# Application connects to "products" alias, not direct index
curl "localhost:9200/products/_search"

# ✅ Good: Filtered aliases for security
curl -X POST "localhost:9200/_aliases" -H 'Content-Type: application/json' -d'
{
  "actions": [
    {
      "add": {
        "index": "all-products",
        "alias": "public-products",
        "filter": {
          "term": {"visibility": "public"}
        }
      }
    }
  ]
}
'
```

## ❌ Common Pitfalls

### Direct Index Usage

```bash
# ❌ Bad: Application uses index directly
curl "localhost:9200/products-v1/_search"

# ✅ Good: Application uses alias
curl "localhost:9200/products/_search"
```

### Missing Rollover Strategy

```bash
# ❌ Bad: Single growing index
curl -X POST "localhost:9200/logs/_doc/" # Grows forever

# ✅ Good: Rollover strategy
curl -X POST "localhost:9200/logs/_doc/" # Uses ILM rollover
```

### Improper Template Priority

```bash
# ❌ Bad: Conflicting templates with same priority
# Template 1: priority 0, pattern "log-*"
# Template 2: priority 0, pattern "*"

# ✅ Good: Clear priority hierarchy
# Template 1: priority 100, pattern "app-logs-*"
# Template 2: priority 50, pattern "logs-*"
# Template 3: priority 10, pattern "*"
```

## 🔗 Next Steps

Now that you understand index lifecycle management, let's move to search operations:

1. **[Query DSL Basics](../03-search-fundamentals/query-dsl-basics.md)** - Start searching your data
2. **[Search Operations](../03-search-fundamentals/search-operations.md)** - Learn search API patterns
3. **[Aggregations](../04-advanced-search/aggregations.md)** - Analyze your data

## 📚 Key Takeaways

- ✅ **Use aliases** for all application connections to indices
- ✅ **Implement proper index templates** for consistent structure
- ✅ **Plan rollover strategy** before indices grow too large
- ✅ **Use ILM policies** to automate lifecycle management
- ✅ **Monitor index health** and performance regularly
- ✅ **Design appropriate shard strategy** based on data size
- ✅ **Implement reindexing strategy** for mapping changes
- ✅ **Use time-based indices** for time-series data

Ready to start searching? Continue with [Query DSL Basics](../03-search-fundamentals/query-dsl-basics.md) to learn how to query your well-structured data!