# Troubleshooting Guide

**Debug and resolve common Elasticsearch issues**

*Estimated reading time: 25 minutes*

## Overview

This guide provides systematic approaches to diagnose and resolve common Elasticsearch problems. From connectivity issues to performance bottlenecks, learn how to identify root causes and implement effective solutions.

## 📋 Table of Contents

1. [Diagnostic Methodology](#diagnostic-methodology)
2. [Connection Issues](#connection-issues)
3. [Index and Mapping Problems](#index-and-mapping-problems)
4. [Query Performance Issues](#query-performance-issues)
5. [Cluster Health Problems](#cluster-health-problems)
6. [Memory and Resource Issues](#memory-and-resource-issues)
7. [Data Ingestion Problems](#data-ingestion-problems)

## 🔍 Diagnostic Methodology

### Step-by-Step Troubleshooting Process

1. **Identify the Problem** - Gather symptoms and error messages
2. **Check Basic Health** - Cluster status and connectivity
3. **Examine Logs** - Review Elasticsearch and application logs
4. **Analyze Metrics** - CPU, memory, disk usage
5. **Test Components** - Isolate the problematic component
6. **Implement Solution** - Apply fixes systematically
7. **Verify Resolution** - Confirm the issue is resolved

### Essential Diagnostic Commands

```bash
# Cluster health overview
curl http://localhost:9200/_cluster/health?pretty

# Node statistics
curl http://localhost:9200/_nodes/stats?pretty

# Index information
curl http://localhost:9200/_cat/indices?v&s=store.size:desc

# Thread pool status
curl http://localhost:9200/_cat/thread_pool?v

# Pending tasks
curl http://localhost:9200/_cluster/pending_tasks?pretty
```

## 🔌 Connection Issues

### Problem: Cannot Connect to Elasticsearch

**Symptoms:**
- Connection refused errors
- Timeouts when accessing Elasticsearch
- Application cannot reach the cluster

**Diagnostic Steps:**

```bash
# Test basic connectivity
curl -v http://localhost:9200

# Check if Elasticsearch is running
ps aux | grep elasticsearch

# Verify network binding
netstat -tulpn | grep :9200

# Check Docker container status
docker ps | grep elasticsearch
docker logs elasticsearch
```

**Common Solutions:**

1. **Service Not Running:**
```bash
# Start Elasticsearch service
sudo systemctl start elasticsearch

# Or start Docker container
docker compose up elasticsearch
```

2. **Wrong URL/Port:**
```bash
# Check configuration
grep "http.port" /etc/elasticsearch/elasticsearch.yml
grep "network.host" /etc/elasticsearch/elasticsearch.yml
```

3. **Firewall Issues:**
```bash
# Check firewall rules
sudo ufw status
sudo iptables -L

# Allow Elasticsearch port
sudo ufw allow 9200
```

### Problem: Authentication Failures

**Symptoms:**
- 401 Unauthorized responses
- Authentication errors in logs

**Solutions:**

```bash
# Reset elastic user password
bin/elasticsearch-reset-password -u elastic

# Check security configuration
grep "xpack.security" /etc/elasticsearch/elasticsearch.yml

# Test with credentials
curl -u elastic:password http://localhost:9200/_cluster/health
```

## 📊 Index and Mapping Problems

### Problem: Mapping Conflicts

**Symptoms:**
- Documents rejected during indexing
- "mapper_parsing_exception" errors
- Data type conflicts

**Diagnostic Commands:**

```bash
# Check current mapping
curl http://localhost:9200/my_index/_mapping?pretty

# Check field types
curl http://localhost:9200/my_index/_mapping/field/problem_field?pretty

# Review rejected documents
curl http://localhost:9200/my_index/_search?q=_exists_:error
```

**Solutions:**

1. **Reindex with Correct Mapping:**
```bash
# Create new index with correct mapping
curl -X PUT "localhost:9200/my_index_v2" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "timestamp": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
      "amount": {"type": "float"},
      "status": {"type": "keyword"}
    }
  }
}'

# Reindex data
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {"index": "my_index"},
  "dest": {"index": "my_index_v2"}
}'
```

2. **Use Index Templates:**
```bash
# Create template to prevent future conflicts
curl -X PUT "localhost:9200/_index_template/my_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["my_index*"],
  "template": {
    "mappings": {
      "properties": {
        "timestamp": {"type": "date"},
        "amount": {"type": "float"}
      }
    }
  }
}'
```

### Problem: Index Corruption

**Symptoms:**
- Red cluster status
- Unassigned shards
- Search failures on specific indices

**Diagnostic Steps:**

```bash
# Check shard allocation
curl http://localhost:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason

# Check allocation explain
curl -X GET "localhost:9200/_cluster/allocation/explain?pretty"

# Force allocation (use cautiously)
curl -X POST "localhost:9200/_cluster/reroute" -H 'Content-Type: application/json' -d'
{
  "commands": [
    {
      "allocate_empty_primary": {
        "index": "my_index",
        "shard": 0,
        "node": "node-1",
        "accept_data_loss": true
      }
    }
  ]
}'
```

## ⚡ Query Performance Issues

### Problem: Slow Search Queries

**Symptoms:**
- High response times
- Query timeouts
- Poor user experience

**Performance Analysis:**

```bash
# Enable slow query logging
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.search.slowlog.threshold.query.warn": "2s",
  "index.search.slowlog.threshold.query.info": "1s",
  "index.search.slowlog.threshold.fetch.warn": "1s"
}'

# Profile queries
curl -X POST "localhost:9200/my_index/_search" -H 'Content-Type: application/json' -d'
{
  "profile": true,
  "query": {
    "match": {"title": "search term"}
  }
}'

# Check field data usage
curl http://localhost:9200/_nodes/stats/indices/fielddata?pretty
```

**Optimization Solutions:**

1. **Optimize Query Structure:**
```json
// ❌ Slow - wildcard at beginning
{"query": {"wildcard": {"title": "*search*"}}}

// ✅ Fast - use match query instead
{"query": {"match": {"title": "search"}}}

// ❌ Slow - script in filter
{"query": {"script": {"script": "doc['price'].value > 100"}}}

// ✅ Fast - use range query
{"query": {"range": {"price": {"gt": 100}}}}
```

2. **Add Proper Indexing:**
```bash
# Create optimized mapping
curl -X PUT "localhost:9200/optimized_index" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "category": {"type": "keyword"},
      "price": {"type": "float"},
      "timestamp": {"type": "date"}
    }
  }
}'
```

### Problem: High Memory Usage from Aggregations

**Symptoms:**
- OutOfMemoryError during aggregations
- Slow aggregation responses
- Circuit breaker errors

**Solutions:**

1. **Use Sampling:**
```json
{
  "aggs": {
    "sample": {
      "sampler": {"shard_size": 1000},
      "aggs": {
        "expensive_agg": {
          "terms": {"field": "category", "size": 100}
        }
      }
    }
  }
}
```

2. **Partition Large Aggregations:**
```json
{
  "aggs": {
    "partitioned_categories": {
      "terms": {
        "field": "category",
        "include": {
          "partition": 0,
          "num_partitions": 10
        }
      }
    }
  }
}
```

## 🏥 Cluster Health Problems

### Problem: Red Cluster Status

**Symptoms:**
- Cluster health shows red
- Data unavailable
- Search failures

**Investigation:**

```bash
# Detailed cluster health
curl "http://localhost:9200/_cluster/health?level=indices&pretty"

# Check unassigned shards
curl "http://localhost:9200/_cat/shards?h=index,shard,prirep,state,unassigned.reason&v"

# Node information
curl "http://localhost:9200/_cat/nodes?v&h=name,node.role,master,ip,heap.percent,ram.percent,cpu,load_1m,disk.used_percent"
```

**Common Fixes:**

1. **Disk Space Issues:**
```bash
# Check disk usage
df -h

# Increase disk watermark thresholds temporarily
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "cluster.routing.allocation.disk.watermark.low": "95%",
    "cluster.routing.allocation.disk.watermark.high": "97%"
  }
}'
```

2. **Node Failures:**
```bash
# Check node status
curl "http://localhost:9200/_cat/nodes?v"

# Exclude failed node temporarily
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "cluster.routing.allocation.exclude._name": "failed-node-name"
  }
}'
```

### Problem: Split Brain / Master Election Issues

**Symptoms:**
- Multiple master nodes
- Cluster instability
- Frequent master re-elections

**Prevention and Resolution:**

```bash
# Check master eligibility settings
curl "http://localhost:9200/_cat/nodes?h=name,master,node.role&v"

# Verify minimum master nodes (should be (N/2) + 1)
curl "http://localhost:9200/_cluster/settings?pretty"

# Set proper minimum master nodes
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "discovery.zen.minimum_master_nodes": 2
  }
}'
```

## 💾 Memory and Resource Issues

### Problem: High Memory Usage

**Symptoms:**
- OutOfMemoryError exceptions
- Frequent garbage collection
- Slow performance

**Memory Analysis:**

```bash
# Check heap usage
curl "http://localhost:9200/_nodes/stats/jvm?pretty"

# Check field data usage
curl "http://localhost:9200/_nodes/stats/indices/fielddata?pretty"

# Check query cache
curl "http://localhost:9200/_nodes/stats/indices/query_cache?pretty"

# Circuit breaker status
curl "http://localhost:9200/_nodes/stats/breaker?pretty"
```

**Memory Optimization:**

1. **Clear Field Data Cache:**
```bash
# Clear field data cache
curl -X POST "localhost:9200/_cache/clear?fielddata=true"

# Set field data cache size
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "indices.fielddata.cache.size": "20%"
  }
}'
```

2. **Optimize JVM Settings:**
```bash
# In jvm.options file
-Xms4g
-Xmx4g
-XX:+UseG1GC
-XX:MaxGCPauseMillis=400
```

### Problem: High CPU Usage

**Symptoms:**
- High system load
- Slow query responses
- Thread pool rejections

**CPU Analysis:**

```bash
# Check thread pools
curl "http://localhost:9200/_cat/thread_pool?v&h=name,active,queue,rejected,completed"

# Hot threads analysis
curl "http://localhost:9200/_nodes/hot_threads"

# System metrics
top -p $(pgrep java)
```

**CPU Optimization:**

```bash
# Increase thread pool sizes if needed
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "thread_pool.search.queue_size": 2000,
    "thread_pool.index.queue_size": 1000
  }
}'
```

## 📥 Data Ingestion Problems

### Problem: Bulk Indexing Failures

**Symptoms:**
- High rejection rates
- Slow indexing performance
- Queue overflow errors

**Bulk Indexing Optimization:**

```python
# Python optimization example
from elasticsearch.helpers import bulk
import time

def optimized_bulk_index(es, documents):
    def generate_docs():
        for doc in documents:
            yield {
                "_index": "my_index",
                "_source": doc
            }
    
    try:
        success, failed = bulk(
            es,
            generate_docs(),
            chunk_size=1000,  # Adjust based on document size
            request_timeout=60,
            max_retries=3,
            initial_backoff=2,
            max_backoff=600
        )
        return success, failed
    except Exception as e:
        print(f"Bulk indexing error: {e}")
        return 0, len(documents)

# Monitor bulk performance
def check_bulk_queue():
    response = es.cat.thread_pool(
        thread_pool_patterns=["bulk"],
        v=True,
        h=["node_name", "name", "active", "queue", "rejected"]
    )
    print(response)
```

### Problem: Pipeline Processing Failures

**Symptoms:**
- Documents not processed correctly
- Pipeline execution errors
- Missing or incorrect field transformations

**Pipeline Debugging:**

```bash
# Test pipeline with sample document
curl -X POST "localhost:9200/_ingest/pipeline/my_pipeline/_simulate" -H 'Content-Type: application/json' -d'
{
  "docs": [
    {
      "_source": {
        "message": "2024-01-15 10:30:00 ERROR Database connection failed"
      }
    }
  ]
}'

# Check pipeline stats
curl "http://localhost:9200/_nodes/stats/ingest?pretty"

# Update pipeline with better error handling
curl -X PUT "localhost:9200/_ingest/pipeline/robust_pipeline" -H 'Content-Type: application/json' -d'
{
  "processors": [
    {
      "grok": {
        "field": "message",
        "patterns": ["%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:msg}"],
        "on_failure": [
          {
            "set": {
              "field": "parse_error",
              "value": "grok_failure"
            }
          }
        ]
      }
    }
  ]
}'
```

## 🔧 Common Quick Fixes

### Performance Quick Wins

```bash
# Refresh interval optimization for bulk loading
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{"refresh_interval": "30s"}'

# Disable replicas during bulk loading
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{"number_of_replicas": 0}'

# Force merge after bulk loading
curl -X POST "localhost:9200/my_index/_forcemerge?max_num_segments=1"

# Re-enable replicas
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{"number_of_replicas": 1}'
```

### Emergency Recovery

```bash
# Enable read-only mode to prevent further damage
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.blocks.read_only": true
  }
}'

# Disable allocation to prevent shard movement
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.enable": "none"
  }
}'

# Take cluster snapshot
curl -X PUT "localhost:9200/_snapshot/emergency_backup/snapshot_$(date +%Y%m%d_%H%M%S)"
```

## 📊 Monitoring and Alerting Setup

### Essential Monitoring Queries

```bash
# Monitor query latency
curl -X POST "localhost:9200/.monitoring-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {"timestamp": {"gte": "now-1h"}}
  },
  "aggs": {
    "avg_query_time": {
      "avg": {"field": "indices_stats.primaries.search.query_time_in_millis"}
    }
  }
}'

# Monitor memory usage
curl -X POST "localhost:9200/.monitoring-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {"timestamp": {"gte": "now-1h"}}
  },
  "aggs": {
    "max_heap_used": {
      "max": {"field": "node_stats.jvm.mem.heap_used_percent"}
    }
  }
}'
```

### Automated Health Checks

```python
#!/usr/bin/env python3
import requests
import time
import logging

def elasticsearch_health_check():
    try:
        # Basic connectivity
        response = requests.get('http://localhost:9200')
        if response.status_code != 200:
            logging.error("Elasticsearch not responding")
            return False
        
        # Cluster health
        health = requests.get('http://localhost:9200/_cluster/health').json()
        if health['status'] == 'red':
            logging.error(f"Cluster health is RED: {health}")
            return False
        
        # Check for unassigned shards
        if health['unassigned_shards'] > 0:
            logging.warning(f"Unassigned shards: {health['unassigned_shards']}")
        
        # Memory check
        stats = requests.get('http://localhost:9200/_nodes/stats/jvm').json()
        for node_id, node in stats['nodes'].items():
            heap_percent = node['jvm']['mem']['heap_used_percent']
            if heap_percent > 85:
                logging.warning(f"High heap usage on {node['name']}: {heap_percent}%")
        
        return True
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    while True:
        if elasticsearch_health_check():
            logging.info("Elasticsearch health check passed")
        time.sleep(60)
```

## 🔗 Next Steps

After troubleshooting issues, consider these preventive measures:

1. **[Monitoring & Operations](../06-performance-production/02_monitoring-operations.md)** - Set up proactive monitoring
2. **[Performance Optimization](../06-performance-production/01_optimization-strategies.md)** - Prevent performance issues
3. **[Security Best Practices](../06-performance-production/03_security-best-practices.md)** - Secure your deployment

## 📚 Key Takeaways

- ✅ **Use systematic approach** for troubleshooting
- ✅ **Check basics first** - connectivity, health, logs
- ✅ **Monitor proactively** to prevent issues
- ✅ **Document solutions** for future reference
- ✅ **Test fixes carefully** before applying to production
- ✅ **Keep regular backups** for emergency recovery
- ✅ **Understand your workload** to optimize accordingly
- ✅ **Set up alerting** for critical issues

Remember: Most issues can be prevented with proper monitoring and maintenance!