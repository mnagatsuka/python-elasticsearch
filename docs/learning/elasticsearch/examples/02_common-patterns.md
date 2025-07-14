# Common Patterns

**Proven solutions for typical Elasticsearch scenarios**

*Estimated reading time: 30 minutes*

## Overview

This guide provides battle-tested patterns and solutions for common Elasticsearch use cases. Each pattern includes implementation details, best practices, and real-world examples.

## 📋 Table of Contents

1. [Search Patterns](#search-patterns)
2. [Data Modeling Patterns](#data-modeling-patterns)
3. [Indexing Patterns](#indexing-patterns)
4. [Analytics Patterns](#analytics-patterns)
5. [Performance Patterns](#performance-patterns)
6. [Operational Patterns](#operational-patterns)

## 🔍 Search Patterns

### 1. Faceted Search Pattern

**Use Case:** E-commerce product filtering, content categorization

**Implementation:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"description": "laptop"}}
      ],
      "filter": [
        {"terms": {"brand": ["Apple", "Dell"]}},
        {"range": {"price": {"gte": 500, "lte": 2000}}}
      ]
    }
  },
  "aggs": {
    "brands": {
      "terms": {"field": "brand", "size": 20}
    },
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          {"key": "Budget", "to": 800},
          {"key": "Mid-range", "from": 800, "to": 1500},
          {"key": "Premium", "from": 1500}
        ]
      }
    },
    "categories": {
      "terms": {"field": "category", "size": 10}
    }
  }
}
```

**Key Benefits:**
- Fast filtering with cached filters
- Real-time facet counts
- Intuitive user navigation

### 2. Auto-suggestion Pattern

**Use Case:** Search-as-you-type, autocomplete functionality

**Mapping Setup:**
```json
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "fields": {
          "suggest": {
            "type": "completion",
            "analyzer": "simple",
            "preserve_separators": true,
            "preserve_position_increments": true,
            "max_input_length": 50
          }
        }
      }
    }
  }
}
```

**Query:**
```json
{
  "suggest": {
    "title_suggest": {
      "prefix": "elast",
      "completion": {
        "field": "title.suggest",
        "size": 10,
        "contexts": {
          "category": ["technology"]
        }
      }
    }
  }
}
```

### 3. Fuzzy Search Pattern

**Use Case:** Handle typos and misspellings

**Implementation:**
```json
{
  "query": {
    "multi_match": {
      "query": "elasticserch tutorail",
      "fields": ["title^2", "content"],
      "fuzziness": "AUTO",
      "prefix_length": 2,
      "max_expansions": 50
    }
  }
}
```

**Advanced Fuzzy with Boosting:**
```json
{
  "query": {
    "bool": {
      "should": [
        {
          "multi_match": {
            "query": "elasticsearch tutorial",
            "fields": ["title^3", "content"],
            "type": "best_fields",
            "boost": 3
          }
        },
        {
          "multi_match": {
            "query": "elasticsearch tutorial",
            "fields": ["title^2", "content"],
            "fuzziness": "AUTO",
            "boost": 1
          }
        }
      ]
    }
  }
}
```

### 4. Personalized Search Pattern

**Use Case:** User-specific search results

**Implementation:**
```json
{
  "query": {
    "function_score": {
      "query": {
        "multi_match": {
          "query": "machine learning",
          "fields": ["title", "content"]
        }
      },
      "functions": [
        {
          "filter": {
            "terms": {"category": ["user_preferred_categories"]}
          },
          "weight": 2.0
        },
        {
          "filter": {
            "terms": {"author": ["user_followed_authors"]}
          },
          "weight": 1.5
        },
        {
          "field_value_factor": {
            "field": "user_engagement_score",
            "factor": 0.1,
            "modifier": "log1p"
          }
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply"
    }
  }
}
```

## 📊 Data Modeling Patterns

### 1. Parent-Child Relationship Pattern

**Use Case:** Blog posts with comments, products with reviews

**Mapping:**
```json
{
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "content": {"type": "text"},
      "relationship": {
        "type": "join",
        "relations": {
          "post": "comment"
        }
      }
    }
  }
}
```

**Index Parent:**
```json
{
  "title": "Elasticsearch Tutorial",
  "content": "Learn Elasticsearch basics...",
  "relationship": {
    "name": "post"
  }
}
```

**Index Child:**
```json
{
  "comment_text": "Great tutorial!",
  "author": "John Doe",
  "relationship": {
    "name": "comment",
    "parent": "post_1"
  }
}
```

**Query:**
```json
{
  "query": {
    "has_child": {
      "type": "comment",
      "query": {
        "match": {"comment_text": "great"}
      },
      "score_mode": "avg"
    }
  }
}
```

### 2. Nested Objects Pattern

**Use Case:** Product variants, user addresses, complex attributes

**Mapping:**
```json
{
  "mappings": {
    "properties": {
      "name": {"type": "text"},
      "variants": {
        "type": "nested",
        "properties": {
          "size": {"type": "keyword"},
          "color": {"type": "keyword"},
          "price": {"type": "float"},
          "stock": {"type": "integer"}
        }
      }
    }
  }
}
```

**Document:**
```json
{
  "name": "T-Shirt",
  "variants": [
    {"size": "S", "color": "red", "price": 19.99, "stock": 10},
    {"size": "M", "color": "red", "price": 19.99, "stock": 5},
    {"size": "L", "color": "blue", "price": 21.99, "stock": 0}
  ]
}
```

**Query:**
```json
{
  "query": {
    "nested": {
      "path": "variants",
      "query": {
        "bool": {
          "must": [
            {"term": {"variants.color": "red"}},
            {"range": {"variants.stock": {"gt": 0}}}
          ]
        }
      }
    }
  }
}
```

### 3. Time-Series Data Pattern

**Use Case:** Logs, metrics, events with time-based access

**Index Naming Strategy:**
```
logs-2024-01-15
logs-2024-01-16
logs-2024-01-17
```

**Index Template:**
```json
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs_policy"
    },
    "mappings": {
      "properties": {
        "@timestamp": {"type": "date"},
        "level": {"type": "keyword"},
        "message": {"type": "text", "norms": false},
        "service": {"type": "keyword"},
        "host": {"type": "keyword"}
      }
    }
  }
}
```

**ILM Policy:**
```json
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "5gb",
            "max_age": "1d"
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "allocate": {"number_of_replicas": 0}
        }
      },
      "delete": {
        "min_age": "30d"
      }
    }
  }
}
```

## 📝 Indexing Patterns

### 1. Bulk Indexing Pattern

**Use Case:** High-throughput data ingestion

**Python Implementation:**
```python
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

def bulk_index_documents(es, documents, index_name, batch_size=1000):
    def generate_docs():
        for doc in documents:
            yield {
                "_index": index_name,
                "_source": doc
            }
    
    # Process in batches
    success_count = 0
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        try:
            success, failed = bulk(
                es,
                generate_docs(),
                chunk_size=batch_size,
                request_timeout=60
            )
            success_count += success
            print(f"Indexed {success} documents")
        except Exception as e:
            print(f"Bulk indexing error: {e}")
    
    return success_count

# Usage
es = Elasticsearch(['localhost:9200'])
documents = [{"title": f"Document {i}", "content": f"Content {i}"} for i in range(10000)]
bulk_index_documents(es, documents, "my_index")
```

### 2. Upsert Pattern

**Use Case:** Update existing documents or create if not exists

**Implementation:**
```json
{
  "doc": {
    "last_updated": "2024-01-15T10:30:00",
    "view_count": 150
  },
  "doc_as_upsert": true
}
```

**Python Example:**
```python
def upsert_document(es, index, doc_id, doc):
    try:
        es.update(
            index=index,
            id=doc_id,
            body={
                "doc": doc,
                "doc_as_upsert": True
            }
        )
    except Exception as e:
        print(f"Upsert error: {e}")
```

### 3. Pipeline Processing Pattern

**Use Case:** Data transformation during ingestion

**Create Pipeline:**
```json
{
  "description": "Parse and enrich log data",
  "processors": [
    {
      "grok": {
        "field": "message",
        "patterns": ["%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:log_message}"]
      }
    },
    {
      "date": {
        "field": "timestamp",
        "formats": ["ISO8601"]
      }
    },
    {
      "set": {
        "field": "processed_at",
        "value": "{{_ingest.timestamp}}"
      }
    },
    {
      "remove": {
        "field": "message"
      }
    }
  ]
}
```

**Use Pipeline:**
```bash
curl -X POST "localhost:9200/logs/_doc?pipeline=log_processing" \
  -H 'Content-Type: application/json' \
  -d '{"message": "2024-01-15T10:30:00 ERROR Database connection failed"}'
```

## 📈 Analytics Patterns

### 1. Real-time Dashboard Pattern

**Use Case:** Live metrics and KPI monitoring

**Query for Real-time Metrics:**
```json
{
  "query": {
    "range": {
      "@timestamp": {"gte": "now-5m"}
    }
  },
  "aggs": {
    "metrics_over_time": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "30s"
      },
      "aggs": {
        "error_rate": {
          "filter": {"term": {"level": "ERROR"}},
          "aggs": {
            "percentage": {
              "bucket_script": {
                "buckets_path": {
                  "errors": "_count",
                  "total": "_parent>_count"
                },
                "script": "params.errors / params.total * 100"
              }
            }
          }
        },
        "avg_response_time": {
          "avg": {"field": "response_time"}
        }
      }
    }
  }
}
```

### 2. Trend Analysis Pattern

**Use Case:** Identifying patterns over time

**Moving Average:**
```json
{
  "aggs": {
    "sales_over_time": {
      "date_histogram": {
        "field": "date",
        "calendar_interval": "day"
      },
      "aggs": {
        "daily_sales": {
          "sum": {"field": "amount"}
        },
        "moving_avg": {
          "moving_avg": {
            "buckets_path": "daily_sales",
            "window": 7,
            "model": "simple"
          }
        }
      }
    }
  }
}
```

### 3. Cohort Analysis Pattern

**Use Case:** User retention, customer lifetime value

**Implementation:**
```json
{
  "query": {
    "range": {
      "signup_date": {
        "gte": "2024-01-01",
        "lte": "2024-01-31"
      }
    }
  },
  "aggs": {
    "cohorts": {
      "date_histogram": {
        "field": "signup_date",
        "calendar_interval": "week"
      },
      "aggs": {
        "week_0": {
          "filter": {
            "range": {
              "last_activity": {
                "gte": "signup_date",
                "lte": "signup_date||+7d"
              }
            }
          }
        },
        "week_1": {
          "filter": {
            "range": {
              "last_activity": {
                "gte": "signup_date||+7d",
                "lte": "signup_date||+14d"
              }
            }
          }
        }
      }
    }
  }
}
```

## ⚡ Performance Patterns

### 1. Index Warming Pattern

**Use Case:** Prepare indices for optimal query performance

**Implementation:**
```python
def warm_index(es, index_name):
    """Warm up index by running common queries"""
    warming_queries = [
        {"match_all": {}},
        {"range": {"timestamp": {"gte": "now-1d"}}},
        {"terms": {"category": ["popular", "categories"]}}
    ]
    
    for query in warming_queries:
        try:
            es.search(
                index=index_name,
                body={"query": query, "size": 1},
                request_cache=True
            )
        except Exception as e:
            print(f"Warming query failed: {e}")
```

### 2. Circuit Breaker Pattern

**Use Case:** Prevent memory issues with large aggregations

**Implementation:**
```python
def safe_aggregation(es, index, agg_query, max_buckets=10000):
    """Execute aggregation with safety checks"""
    
    # Check estimated bucket count first
    sample_query = {
        "size": 0,
        "aggs": {
            "sample": {
                "sampler": {"shard_size": 1000},
                "aggs": agg_query["aggs"]
            }
        }
    }
    
    try:
        sample_result = es.search(index=index, body=sample_query)
        estimated_buckets = estimate_bucket_count(sample_result)
        
        if estimated_buckets > max_buckets:
            raise ValueError(f"Estimated buckets ({estimated_buckets}) exceeds limit")
        
        return es.search(index=index, body=agg_query)
        
    except Exception as e:
        print(f"Aggregation safety check failed: {e}")
        return None
```

### 3. Caching Pattern

**Use Case:** Improve performance for repeated queries

**Request Cache Usage:**
```python
def cached_search(es, index, query, cache_key=None):
    """Execute search with caching"""
    
    search_body = {
        "query": query,
        "size": 20
    }
    
    try:
        response = es.search(
            index=index,
            body=search_body,
            request_cache=True,  # Enable request cache
            preference=cache_key  # Use consistent routing
        )
        return response
    except Exception as e:
        print(f"Cached search failed: {e}")
        return None
```

## 🔧 Operational Patterns

### 1. Health Check Pattern

**Use Case:** Monitor cluster and application health

**Implementation:**
```python
def comprehensive_health_check(es):
    """Comprehensive Elasticsearch health check"""
    
    health_status = {
        "cluster": False,
        "indices": False,
        "queries": False,
        "ingestion": False
    }
    
    try:
        # Cluster health
        cluster_health = es.cluster.health()
        health_status["cluster"] = cluster_health["status"] in ["green", "yellow"]
        
        # Index health
        indices_health = es.cat.indices(format="json")
        unhealthy_indices = [idx for idx in indices_health if idx["health"] == "red"]
        health_status["indices"] = len(unhealthy_indices) == 0
        
        # Query performance
        start_time = time.time()
        test_query = es.search(index="_all", body={"query": {"match_all": {}}, "size": 1})
        query_time = time.time() - start_time
        health_status["queries"] = query_time < 1.0  # Under 1 second
        
        # Test ingestion
        test_doc = {"timestamp": datetime.now().isoformat(), "test": True}
        es.index(index="health_test", body=test_doc)
        health_status["ingestion"] = True
        
    except Exception as e:
        print(f"Health check error: {e}")
    
    return health_status
```

### 2. Rolling Restart Pattern

**Use Case:** Update cluster without downtime

**Implementation:**
```bash
#!/bin/bash
# Rolling restart script

NODES=("node1" "node2" "node3")

for node in "${NODES[@]}"; do
    echo "Restarting $node..."
    
    # Disable shard allocation
    curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
    {
      "persistent": {
        "cluster.routing.allocation.enable": "primaries"
      }
    }'
    
    # Stop node
    ssh $node "sudo systemctl stop elasticsearch"
    
    # Wait for node to leave cluster
    sleep 30
    
    # Start node
    ssh $node "sudo systemctl start elasticsearch"
    
    # Wait for node to join
    sleep 60
    
    # Re-enable allocation
    curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
    {
      "persistent": {
        "cluster.routing.allocation.enable": "all"
      }
    }'
    
    # Wait for cluster to stabilize
    while true; do
        status=$(curl -s "localhost:9200/_cluster/health" | jq -r '.status')
        if [ "$status" = "green" ]; then
            break
        fi
        sleep 10
    done
    
    echo "$node restarted successfully"
done
```

### 3. Backup and Restore Pattern

**Use Case:** Data protection and disaster recovery

**Implementation:**
```python
def automated_backup(es, repository, indices_pattern="*"):
    """Automated backup with retention"""
    
    snapshot_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Create snapshot
        es.snapshot.create(
            repository=repository,
            snapshot=snapshot_name,
            body={
                "indices": indices_pattern,
                "ignore_unavailable": True,
                "include_global_state": False,
                "metadata": {
                    "taken_by": "automated_backup",
                    "taken_because": "scheduled_backup"
                }
            }
        )
        
        # Clean up old snapshots (keep last 7)
        snapshots = es.snapshot.get(repository=repository, snapshot="_all")
        sorted_snapshots = sorted(
            snapshots["snapshots"], 
            key=lambda x: x["start_time"]
        )
        
        if len(sorted_snapshots) > 7:
            old_snapshots = sorted_snapshots[:-7]
            for snapshot in old_snapshots:
                es.snapshot.delete(
                    repository=repository,
                    snapshot=snapshot["snapshot"]
                )
        
        return True
        
    except Exception as e:
        print(f"Backup failed: {e}")
        return False
```

## 🔗 Pattern Selection Guide

### Choose Patterns Based on Use Case

| Use Case | Recommended Patterns |
|----------|---------------------|
| **E-commerce Search** | Faceted Search, Personalized Search, Auto-suggestion |
| **Log Analytics** | Time-series Data, Bulk Indexing, Real-time Dashboard |
| **Content Management** | Fuzzy Search, Nested Objects, Full-text Search |
| **User Analytics** | Cohort Analysis, Trend Analysis, Real-time Dashboard |
| **High-Volume Ingestion** | Bulk Indexing, Pipeline Processing, Circuit Breaker |
| **Production Operations** | Health Check, Rolling Restart, Backup and Restore |

### Performance Considerations

1. **Search-Heavy Workloads**: Focus on caching patterns and query optimization
2. **Write-Heavy Workloads**: Use bulk indexing and pipeline processing
3. **Mixed Workloads**: Balance read and write optimization with proper indexing strategies

## 📚 Next Steps

- **[Sample Queries](sample-queries.md)** - Ready-to-use query examples
- **[Troubleshooting](troubleshooting.md)** - Debug common issues
- **[E-commerce Example](ecommerce-search.md)** - Complete implementation
- **[Log Analytics Example](log-analytics.md)** - Full ELK stack solution

These patterns provide a solid foundation for building robust Elasticsearch applications. Adapt them to your specific requirements and always test in your environment before production deployment!