# Optimization Strategies

**Scale your Elasticsearch deployment with proven performance optimization techniques**

*Estimated reading time: 45 minutes*

## Overview

Performance optimization is crucial for running Elasticsearch at scale. This guide covers hardware considerations, index optimization, query performance tuning, cluster scaling strategies, and monitoring techniques for production environments.

## 📋 Table of Contents

1. [Performance Fundamentals](#performance-fundamentals)
2. [Hardware Optimization](#hardware-optimization)
3. [Index Design](#index-design)
4. [Query Optimization](#query-optimization)
5. [Cluster Scaling](#cluster-scaling)
6. [Memory Management](#memory-management)
7. [Production Best Practices](#production-best-practices)

## ⚡ Performance Fundamentals

### Performance Metrics

**Key Metrics to Monitor:**
- **Indexing Rate**: Documents per second
- **Search Latency**: Query response time (p50, p95, p99)
- **Throughput**: Queries per second
- **Resource Utilization**: CPU, Memory, Disk I/O
- **Cluster Health**: Node status, shard allocation

### Performance Goals

```bash
# Typical performance targets
Indexing: 10,000-100,000 docs/sec per node
Search Latency: <100ms for p95
Query Throughput: 1,000+ queries/sec per node
Availability: 99.9%+ uptime
```

### Bottleneck Identification

```bash
# Check cluster health
curl -X GET "localhost:9200/_cluster/health?pretty"

# Monitor node stats
curl -X GET "localhost:9200/_nodes/stats?pretty"

# Check hot threads
curl -X GET "localhost:9200/_nodes/hot_threads"

# Index statistics
curl -X GET "localhost:9200/_stats?pretty"
```

## 🖥️ Hardware Optimization

### CPU Requirements

**CPU Guidelines:**
- **Indexing-heavy**: High core count (16-32 cores)
- **Search-heavy**: High clock speed (3.0+ GHz)
- **Mixed workload**: Balance cores and clock speed

```bash
# Monitor CPU usage
curl -X GET "localhost:9200/_nodes/stats/os?pretty"
```

### Memory Configuration

**JVM Heap Sizing:**
```bash
# Set JVM heap (do not exceed 32GB)
export ES_JAVA_OPTS="-Xms16g -Xmx16g"

# Alternative: Use jvm.options file
echo "-Xms16g" >> config/jvm.options
echo "-Xmx16g" >> config/jvm.options
```

**Memory Allocation Guidelines:**
- **JVM Heap**: 50% of RAM, max 32GB
- **OS Cache**: Remaining 50% for Lucene file caching
- **Minimum RAM**: 8GB per node
- **Recommended RAM**: 64GB+ for production

### Storage Optimization

**SSD Configuration:**
```bash
# Use SSDs for data nodes
# NVMe SSDs preferred for high-performance workloads

# RAID Configuration
RAID 0: Maximum performance (no redundancy)
RAID 10: Balance of performance and redundancy
```

**Storage Settings:**
```bash
# Optimize mount options
mount -o noatime,data=writeback /dev/ssd1 /var/lib/elasticsearch

# Disable swap
swapoff -a
echo 'vm.swappiness=1' >> /etc/sysctl.conf
```

### Network Optimization

```bash
# Network interface optimization
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 65536 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' >> /etc/sysctl.conf
```

## 📊 Index Design

### Shard Strategy

**Optimal Shard Sizing:**
```bash
# Target shard size: 10-50GB
# Calculate shards needed
curl -X GET "localhost:9200/_cat/indices?v&h=index,store.size,docs.count"

# Shard calculation formula
target_shard_size = 30GB
expected_data_size = 300GB
optimal_shards = expected_data_size / target_shard_size = 10 shards
```

**Shard Configuration:**
```bash
curl -X PUT "localhost:9200/optimized_index" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 10,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "index.translog.flush_threshold_size": "1gb"
  }
}
'
```

### Mapping Optimization

**Efficient Field Types:**
```bash
curl -X PUT "localhost:9200/optimized_index" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "keyword_field": {
        "type": "keyword",
        "doc_values": true,      // Enable for aggregations
        "index": false           // Disable if not searching
      },
      "text_field": {
        "type": "text",
        "index_options": "freqs", // Reduce index options if possible
        "norms": false           // Disable if not using relevance scoring
      },
      "numeric_field": {
        "type": "long",
        "doc_values": true,
        "index": false           // Disable if only aggregating
      },
      "date_field": {
        "type": "date",
        "format": "epoch_millis" // Use efficient date format
      }
    }
  }
}
'
```

**Disable Unnecessary Features:**
```bash
curl -X PUT "localhost:9200/logs_index" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "_source": {
      "enabled": false         // Disable if not needed
    },
    "_all": {
      "enabled": false         // Deprecated, but disable if present
    },
    "properties": {
      "log_message": {
        "type": "text",
        "store": false,         // Don'\''t store separately
        "norms": false         // Disable scoring norms
      }
    }
  }
}
'
```

### Index Templates

**Optimized Template:**
```bash
curl -X PUT "localhost:9200/_index_template/logs_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "refresh_interval": "30s",
      "index.codec": "best_compression",
      "index.translog.durability": "async",
      "index.translog.sync_interval": "30s"
    },
    "mappings": {
      "properties": {
        "@timestamp": {
          "type": "date",
          "format": "epoch_millis"
        },
        "level": {
          "type": "keyword"
        },
        "message": {
          "type": "text",
          "norms": false
        }
      }
    }
  }
}
'
```

## 🔍 Query Optimization

### Search Performance

**Efficient Query Structure:**
```bash
# ✅ Good: Use filters when possible
curl -X POST "localhost:9200/logs/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ],
      "must": [
        {"match": {"message": "database"}}
      ]
    }
  }
}
'

# ❌ Bad: Using must for exact matches
curl -X POST "localhost:9200/logs/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}},
        {"match": {"message": "database"}}
      ]
    }
  }
}
'
```

**Query Caching:**
```bash
# Enable query caching
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.queries.cache.enabled": true
}
'

# Use request cache for aggregations
curl -X POST "localhost:9200/sales/_search?request_cache=true" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "total_revenue": {
      "sum": {"field": "revenue"}
    }
  }
}
'
```

### Aggregation Optimization

**Efficient Aggregations:**
```bash
# ✅ Good: Limit bucket size
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "top_categories": {
      "terms": {
        "field": "category",
        "size": 10,
        "execution_hint": "global_ordinals"
      }
    }
  }
}
'

# ✅ Good: Use composite aggregations for large datasets
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sales_composite": {
      "composite": {
        "size": 1000,
        "sources": [
          {"category": {"terms": {"field": "category"}}},
          {"brand": {"terms": {"field": "brand"}}}
        ]
      }
    }
  }
}
'
```

### Search After vs From/Size

**Efficient Pagination:**
```bash
# ✅ Good: Use search_after for deep pagination
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "size": 100,
  "sort": [
    {"price": "asc"},
    {"_id": "asc"}
  ],
  "search_after": [299.99, "product_123"]
}
'

# ❌ Bad: Deep pagination with from/size
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "from": 10000,
  "size": 100
}
'
```

## 📈 Cluster Scaling

### Horizontal Scaling

**Adding Nodes:**
```bash
# Scale data nodes
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.total_shards_per_node": 1000
  }
}
'

# Monitor shard allocation
curl -X GET "localhost:9200/_cat/allocation?v"
```

**Node Roles:**
```yaml
# Master-eligible nodes
node.roles: [master]
cluster.initial_master_nodes: [master-1, master-2, master-3]

# Data nodes
node.roles: [data, data_content, data_hot, data_warm, data_cold]

# Coordinating nodes
node.roles: []

# Ingest nodes
node.roles: [ingest]
```

### Vertical Scaling

**Resource Scaling:**
```bash
# Increase JVM heap (requires restart)
echo "-Xms32g" > config/jvm.options.d/heap.options
echo "-Xmx32g" >> config/jvm.options.d/heap.options

# Monitor resource usage
curl -X GET "localhost:9200/_nodes/stats/jvm,os,fs?pretty"
```

### Hot-Warm-Cold Architecture

**Tier Configuration:**
```bash
# Hot tier (NVMe SSDs)
curl -X PUT "localhost:9200/logs-hot" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.routing.allocation.include._tier_preference": "data_hot"
  }
}
'

# Warm tier (SATA SSDs)
curl -X PUT "localhost:9200/logs-warm" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.routing.allocation.include._tier_preference": "data_warm",
    "index.codec": "best_compression"
  }
}
'

# Cold tier (HDDs)
curl -X PUT "localhost:9200/logs-cold" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.routing.allocation.include._tier_preference": "data_cold",
    "index.codec": "best_compression",
    "index.number_of_replicas": 0
  }
}
'
```

## 🧠 Memory Management

### JVM Tuning

**Garbage Collection Optimization:**
```bash
# G1GC settings (recommended for large heaps)
echo "-XX:+UseG1GC" >> config/jvm.options.d/gc.options
echo "-XX:G1HeapRegionSize=32m" >> config/jvm.options.d/gc.options
echo "-XX:MaxGCPauseMillis=250" >> config/jvm.options.d/gc.options

# Monitor GC
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty"
```

**Circuit Breakers:**
```bash
# Adjust circuit breakers
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "indices.breaker.total.limit": "70%",
    "indices.breaker.request.limit": "40%",
    "indices.breaker.fielddata.limit": "30%"
  }
}
'
```

### Field Data Management

**Field Data Settings:**
```bash
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.fielddata.cache.size": "30%",
  "index.fielddata.cache.expire": "5m"
}
'
```

### Query Cache Tuning

```bash
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "indices.queries.cache.size": "10%",
    "indices.requests.cache.size": "2%"
  }
}
'
```

## 🏭 Production Best Practices

### Index Lifecycle Management

**ILM Policy:**
```bash
curl -X PUT "localhost:9200/_ilm/policy/logs_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50gb",
            "max_age": "7d"
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "allocate": {
            "number_of_replicas": 0
          },
          "forcemerge": {
            "max_num_segments": 1
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "allocate": {
            "include": {
              "_tier_preference": "data_cold"
            }
          }
        }
      },
      "delete": {
        "min_age": "90d"
      }
    }
  }
}
'
```

### Snapshot Strategy

**Automated Snapshots:**
```bash
# Register repository
curl -X PUT "localhost:9200/_snapshot/backup_repo" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/var/backups/elasticsearch",
    "compress": true,
    "chunk_size": "1gb"
  }
}
'

# Create SLM policy
curl -X PUT "localhost:9200/_slm/policy/daily_snapshots" -H 'Content-Type: application/json' -d'
{
  "schedule": "0 2 * * *",
  "name": "<daily-snapshot-{now/d}>",
  "repository": "backup_repo",
  "config": {
    "include_global_state": false,
    "indices": ["logs-*", "metrics-*"]
  },
  "retention": {
    "expire_after": "30d",
    "min_count": 5,
    "max_count": 50
  }
}
'
```

### Security Configuration

**Security Settings:**
```bash
# Enable security
echo "xpack.security.enabled: true" >> config/elasticsearch.yml
echo "xpack.security.transport.ssl.enabled: true" >> config/elasticsearch.yml

# Configure authentication
curl -X POST "localhost:9200/_security/user/admin" -H 'Content-Type: application/json' -d'
{
  "password": "strong_password",
  "roles": ["superuser"]
}
'
```

### Monitoring Setup

**Cluster Monitoring:**
```bash
# Enable monitoring
echo "xpack.monitoring.collection.enabled: true" >> config/elasticsearch.yml

# Monitor key metrics
curl -X GET "localhost:9200/_cluster/stats?pretty"
curl -X GET "localhost:9200/_nodes/stats/indices,jvm,os,fs?pretty"
```

### Performance Testing

**Load Testing:**
```bash
# Use Rally for benchmarking
pip install esrally

# Run standard benchmark
esrally --track=geonames --target-hosts=localhost:9200

# Custom benchmark
esrally --track=custom_track --target-hosts=localhost:9200 --pipeline=benchmark-only
```

**Query Performance Testing:**
```python
import time
import requests
import statistics

def benchmark_query(query, iterations=100):
    response_times = []
    
    for i in range(iterations):
        start_time = time.time()
        response = requests.post(
            'http://localhost:9200/my_index/_search',
            json=query,
            headers={'Content-Type': 'application/json'}
        )
        end_time = time.time()
        
        if response.status_code == 200:
            response_times.append((end_time - start_time) * 1000)  # Convert to ms
    
    return {
        'avg_response_time': statistics.mean(response_times),
        'p50_response_time': statistics.median(response_times),
        'p95_response_time': statistics.quantiles(response_times, n=20)[18],
        'p99_response_time': statistics.quantiles(response_times, n=100)[98]
    }

# Test query performance
test_query = {
    "query": {
        "bool": {
            "filter": [
                {"term": {"status": "active"}},
                {"range": {"timestamp": {"gte": "now-1h"}}}
            ]
        }
    }
}

results = benchmark_query(test_query)
print(f"Average response time: {results['avg_response_time']:.2f}ms")
print(f"P95 response time: {results['p95_response_time']:.2f}ms")
```

### Resource Planning

**Capacity Planning:**
```bash
# Calculate storage requirements
daily_data_size = 100GB
retention_days = 30
replica_count = 1
compression_ratio = 0.7

total_storage = daily_data_size * retention_days * (1 + replica_count) * compression_ratio
# Result: 4.2TB

# Calculate memory requirements
active_data = daily_data_size * 7  # 1 week of active data
heap_memory = min(32, active_data * 0.1)  # 10% of active data, max 32GB
total_memory = heap_memory * 2  # 50% for heap, 50% for OS cache
```

## 🔗 Next Steps

Now that you've learned optimization strategies, let's explore monitoring and operations:

1. **[Monitoring & Operations](monitoring-operations.md)** - Monitor cluster health and performance
2. **[Index Management](index-management.md)** - Advanced index lifecycle and management
3. **[Troubleshooting](troubleshooting.md)** - Diagnose and resolve common issues

## 📚 Key Takeaways

- ✅ **Size shards appropriately** (10-50GB per shard)
- ✅ **Configure JVM heap** to 50% of RAM, max 32GB
- ✅ **Use SSDs** for data storage in production
- ✅ **Optimize mappings** by disabling unnecessary features
- ✅ **Implement proper caching** for queries and requests
- ✅ **Use filters over queries** when possible
- ✅ **Plan capacity** based on data growth and retention
- ✅ **Monitor performance metrics** continuously
- ✅ **Implement ILM policies** for data lifecycle management
- ✅ **Test performance** regularly with realistic workloads

Ready to learn about monitoring and operations? Continue with [Monitoring & Operations](monitoring-operations.md) to set up comprehensive cluster monitoring!