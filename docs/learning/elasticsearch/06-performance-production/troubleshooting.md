# Troubleshooting

**Diagnose and resolve common Elasticsearch issues with systematic approaches**

*Estimated reading time: 40 minutes*

## Overview

Troubleshooting Elasticsearch requires a systematic approach to identify, diagnose, and resolve issues. This guide covers common problems, diagnostic techniques, performance issues, cluster problems, and emergency procedures for maintaining healthy Elasticsearch deployments.

## 📋 Table of Contents

1. [Troubleshooting Methodology](#troubleshooting-methodology)
2. [Common Issues](#common-issues)
3. [Performance Problems](#performance-problems)
4. [Cluster Issues](#cluster-issues)
5. [Search and Indexing Problems](#search-and-indexing-problems)
6. [Memory and Resource Issues](#memory-and-resource-issues)
7. [Emergency Procedures](#emergency-procedures)

## 🔍 Troubleshooting Methodology

### Systematic Approach

1. **Identify Symptoms** - What is the observed problem?
2. **Gather Information** - Collect logs, metrics, and cluster state
3. **Analyze Data** - Look for patterns and correlations
4. **Form Hypothesis** - Develop theories about the root cause
5. **Test Solutions** - Implement fixes and monitor results
6. **Document Resolution** - Record findings for future reference

### Initial Diagnostic Commands

**Quick Health Check:**
```bash
# Cluster health overview
curl -X GET "localhost:9200/_cluster/health?pretty"

# Node status
curl -X GET "localhost:9200/_cat/nodes?v&h=name,heap.percent,ram.percent,cpu,load_1m,node.role,master"

# Index status
curl -X GET "localhost:9200/_cat/indices?v&h=health,status,index,pri,rep,docs.count,store.size"

# Shard allocation
curl -X GET "localhost:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason"
```

### Information Gathering

**Comprehensive Diagnostics:**
```bash
#!/bin/bash

ES_HOST="localhost:9200"
OUTPUT_DIR="/tmp/es_diagnostics_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "Gathering Elasticsearch diagnostics..."

# Cluster info
curl -s "$ES_HOST/_cluster/health?pretty" > "$OUTPUT_DIR/cluster_health.json"
curl -s "$ES_HOST/_cluster/stats?pretty" > "$OUTPUT_DIR/cluster_stats.json"
curl -s "$ES_HOST/_cluster/settings?pretty" > "$OUTPUT_DIR/cluster_settings.json"

# Node info
curl -s "$ES_HOST/_nodes?pretty" > "$OUTPUT_DIR/nodes_info.json"
curl -s "$ES_HOST/_nodes/stats?pretty" > "$OUTPUT_DIR/nodes_stats.json"
curl -s "$ES_HOST/_nodes/hot_threads?threads=10" > "$OUTPUT_DIR/hot_threads.txt"

# Index info
curl -s "$ES_HOST/_cat/indices?v" > "$OUTPUT_DIR/indices.txt"
curl -s "$ES_HOST/_cat/shards?v" > "$OUTPUT_DIR/shards.txt"
curl -s "$ES_HOST/_cat/allocation?v" > "$OUTPUT_DIR/allocation.txt"

# Pending tasks
curl -s "$ES_HOST/_cat/pending_tasks?v" > "$OUTPUT_DIR/pending_tasks.txt"

# Thread pools
curl -s "$ES_HOST/_cat/thread_pool?v" > "$OUTPUT_DIR/thread_pools.txt"

echo "Diagnostics saved to: $OUTPUT_DIR"
```

## 🚨 Common Issues

### Cluster Status Red/Yellow

**Red Cluster:**
```bash
# Check unassigned shards
curl -X GET "localhost:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason" | grep UNASSIGNED

# Get cluster allocation explanation
curl -X GET "localhost:9200/_cluster/allocation/explain?pretty"

# Check for disk space issues
curl -X GET "localhost:9200/_cat/allocation?v&h=node,disk.used_percent"
```

**Common Causes and Solutions:**
```bash
# 1. Disk space issues
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "cluster.routing.allocation.disk.watermark.flood_stage": "99%"
  }
}
'

# 2. Force shard allocation
curl -X POST "localhost:9200/_cluster/reroute" -H 'Content-Type: application/json' -d'
{
  "commands": [
    {
      "allocate_primary": {
        "index": "my_index",
        "shard": 0,
        "node": "node_name",
        "accept_data_loss": true
      }
    }
  ]
}
'

# 3. Cancel stuck shard allocation
curl -X POST "localhost:9200/_cluster/reroute" -H 'Content-Type: application/json' -d'
{
  "commands": [
    {
      "cancel": {
        "index": "my_index",
        "shard": 0,
        "node": "node_name"
      }
    }
  ]
}
'
```

### Split Brain Prevention

**Master Node Issues:**
```bash
# Check master node
curl -X GET "localhost:9200/_cat/master?v"

# Check discovery settings
grep -E "discovery|cluster.initial_master_nodes" /etc/elasticsearch/elasticsearch.yml

# Proper master node configuration
echo "discovery.seed_hosts: [\"master1\", \"master2\", \"master3\"]" >> elasticsearch.yml
echo "cluster.initial_master_nodes: [\"master1\", \"master2\", \"master3\"]" >> elasticsearch.yml
```

### Node Not Joining Cluster

**Diagnostic Steps:**
```bash
# Check node logs
tail -f /var/log/elasticsearch/my-cluster.log | grep -E "discovery|cluster"

# Verify network connectivity
telnet master_node_ip 9300

# Check cluster name consistency
grep "cluster.name" /etc/elasticsearch/elasticsearch.yml

# Verify node roles
grep "node.roles" /etc/elasticsearch/elasticsearch.yml
```

## ⚡ Performance Problems

### Slow Search Queries

**Identify Slow Queries:**
```bash
# Enable search slow log
curl -X PUT "localhost:9200/_settings" -H 'Content-Type: application/json' -d'
{
  "index.search.slowlog.threshold.query.warn": "2s",
  "index.search.slowlog.threshold.query.info": "1s",
  "index.search.slowlog.threshold.fetch.warn": "1s"
}
'

# Check slow log
tail -f /var/log/elasticsearch/my-cluster_index_search_slowlog.log
```

**Query Optimization:**
```bash
# Use query profiler
curl -X POST "localhost:9200/my_index/_search" -H 'Content-Type: application/json' -d'
{
  "profile": true,
  "query": {
    "match": {
      "field": "value"
    }
  }
}
'

# Analyze query with explain
curl -X POST "localhost:9200/my_index/_explain/doc_id" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "field": "value"
    }
  }
}
'
```

### High Indexing Latency

**Indexing Performance Issues:**
```bash
# Check indexing stats
curl -X GET "localhost:9200/_stats/indexing?pretty"

# Monitor thread pools
curl -X GET "localhost:9200/_cat/thread_pool?v&h=name,active,queue,rejected&s=name"

# Optimize indexing settings
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.refresh_interval": "30s",
  "index.translog.durability": "async",
  "index.translog.sync_interval": "30s"
}
'
```

### Memory Issues

**High Heap Usage:**
```bash
# Check JVM stats
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty"

# Monitor garbage collection
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty" | jq '.nodes[].jvm.gc'

# Check field data usage
curl -X GET "localhost:9200/_nodes/stats/indices/fielddata?pretty"
```

**Memory Optimization:**
```bash
# Clear field data cache
curl -X POST "localhost:9200/_cache/clear?fielddata=true"

# Adjust circuit breakers
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "indices.breaker.fielddata.limit": "30%",
    "indices.breaker.request.limit": "40%",
    "indices.breaker.total.limit": "70%"
  }
}
'
```

## 🏘️ Cluster Issues

### Shard Allocation Problems

**Unassigned Shards:**
```bash
# Get allocation explanation
curl -X GET "localhost:9200/_cluster/allocation/explain?pretty" -H 'Content-Type: application/json' -d'
{
  "index": "my_index",
  "shard": 0,
  "primary": true
}
'

# Enable shard allocation
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.enable": "all"
  }
}
'

# Retry failed allocations
curl -X POST "localhost:9200/_cluster/reroute?retry_failed=true"
```

### Recovery Issues

**Monitor Recovery:**
```bash
# Check recovery status
curl -X GET "localhost:9200/_cat/recovery?v&active_only=true"

# Adjust recovery settings
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "indices.recovery.max_bytes_per_sec": "200mb",
    "cluster.routing.allocation.node_concurrent_recoveries": 6,
    "cluster.routing.allocation.cluster_concurrent_rebalance": 4
  }
}
'
```

### Disk Space Management

**Disk Space Issues:**
```bash
# Check disk usage
curl -X GET "localhost:9200/_cat/allocation?v&h=node,disk.used_percent,disk.avail"

# Temporary disk threshold adjustment
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "cluster.routing.allocation.disk.watermark.low": "95%",
    "cluster.routing.allocation.disk.watermark.high": "97%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "99%"
  }
}
'

# Force index deletion
curl -X DELETE "localhost:9200/old_index_*"
```

## 🔍 Search and Indexing Problems

### Search Errors

**Common Search Issues:**
```bash
# Too many clauses error
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "indices.query.bool.max_clause_count": 2048
  }
}
'

# Search result window too large
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.max_result_window": 50000
}
'

# Too many buckets in aggregation
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "search.max_buckets": 20000
  }
}
'
```

### Indexing Failures

**Bulk Indexing Issues:**
```bash
# Check bulk thread pool
curl -X GET "localhost:9200/_cat/thread_pool/write?v"

# Monitor rejected requests
curl -X GET "localhost:9200/_nodes/stats/thread_pool?pretty" | grep rejected

# Adjust bulk queue size
echo "thread_pool.write.queue_size: 1000" >> elasticsearch.yml
```

**Document Version Conflicts:**
```bash
# Use external versioning
curl -X PUT "localhost:9200/my_index/_doc/1?version=2&version_type=external" -H 'Content-Type: application/json' -d'
{
  "field": "value"
}
'

# Ignore version conflicts in bulk operations
curl -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' -d'
{"index": {"_index": "my_index", "_id": "1", "version_type": "external_gte", "version": 1}}
{"field": "value"}
'
```

### Mapping Issues

**Mapping Conflicts:**
```bash
# Check mapping conflicts
curl -X GET "localhost:9200/my_index/_mapping?pretty"

# Resolve with reindex
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "old_index"
  },
  "dest": {
    "index": "new_index"
  },
  "script": {
    "source": "ctx._source.fixed_field = ctx._source.problematic_field.toString()"
  }
}
'
```

## 🧠 Memory and Resource Issues

### Out of Memory Errors

**JVM Heap Issues:**
```bash
# Check heap usage
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty" | jq '.nodes[].jvm.mem'

# Analyze heap dumps
jmap -dump:format=b,file=heap.hprof <pid>

# Adjust JVM settings
echo "-Xms16g" > config/jvm.options.d/heap.options
echo "-Xmx16g" >> config/jvm.options.d/heap.options
```

**Memory Pressure Solutions:**
```bash
# Disable swap
swapoff -a
echo 'vm.swappiness=1' >> /etc/sysctl.conf

# Optimize GC settings
echo "-XX:+UseG1GC" >> config/jvm.options.d/gc.options
echo "-XX:MaxGCPauseMillis=250" >> config/jvm.options.d/gc.options

# Monitor GC logs
tail -f logs/gc.log
```

### CPU Issues

**High CPU Usage:**
```bash
# Check hot threads
curl -X GET "localhost:9200/_nodes/hot_threads?threads=10&interval=500ms"

# Monitor specific operations
curl -X GET "localhost:9200/_tasks?pretty"

# Check system CPU
top -p $(pgrep -f elasticsearch)
```

### File Descriptor Limits

**Too Many Open Files:**
```bash
# Check current limits
ulimit -n

# Set higher limits
echo "elasticsearch soft nofile 65536" >> /etc/security/limits.conf
echo "elasticsearch hard nofile 65536" >> /etc/security/limits.conf

# Systemd service limits
echo "LimitNOFILE=65536" >> /etc/systemd/system/elasticsearch.service.d/override.conf
systemctl daemon-reload
```

## 🚨 Emergency Procedures

### Cluster Recovery

**Force Primary Shard Allocation:**
```bash
# When cluster is red and data loss is acceptable
curl -X POST "localhost:9200/_cluster/reroute" -H 'Content-Type: application/json' -d'
{
  "commands": [
    {
      "allocate_empty_primary": {
        "index": "lost_index",
        "shard": 0,
        "node": "node_name",
        "accept_data_loss": true
      }
    }
  ]
}
'
```

### Emergency Index Operations

**Force Delete Stuck Index:**
```bash
# Close index first
curl -X POST "localhost:9200/stuck_index/_close"

# Force delete
curl -X DELETE "localhost:9200/stuck_index"
```

**Emergency Disk Space:**
```bash
# Disable allocation temporarily
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.enable": "primaries"
  }
}
'

# Delete old indices quickly
curl -X DELETE "localhost:9200/logs-2023-*"

# Re-enable allocation
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.enable": "all"
  }
}
'
```

### Node Recovery

**Restart Problematic Node:**
```bash
# Graceful node shutdown
curl -X POST "localhost:9200/_cluster/nodes/_local/_shutdown"

# Force restart if needed
systemctl restart elasticsearch

# Monitor rejoining
curl -X GET "localhost:9200/_cat/nodes?v"
```

### Data Recovery

**Restore from Snapshot:**
```bash
# Close current index
curl -X POST "localhost:9200/corrupted_index/_close"

# Restore from snapshot
curl -X POST "localhost:9200/_snapshot/my_repo/snapshot_name/_restore" -H 'Content-Type: application/json' -d'
{
  "indices": "corrupted_index",
  "ignore_unavailable": true,
  "include_global_state": false
}
'
```

### Circuit Breaker Tripped

**Reset Circuit Breakers:**
```bash
# Check circuit breaker status
curl -X GET "localhost:9200/_nodes/stats/breaker?pretty"

# Clear caches to reduce memory pressure
curl -X POST "localhost:9200/_cache/clear"

# Adjust breaker limits temporarily
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "indices.breaker.total.limit": "80%"
  }
}
'
```

## 🛠️ Diagnostic Tools

### Log Analysis Scripts

**Parse Elasticsearch Logs:**
```bash
#!/bin/bash

LOG_FILE="/var/log/elasticsearch/my-cluster.log"

echo "=== Error Analysis ==="
grep -E "ERROR|WARN" "$LOG_FILE" | tail -20

echo -e "\n=== GC Analysis ==="
grep "GC" "$LOG_FILE" | tail -10

echo -e "\n=== Slow Operations ==="
grep -E "slow|took.*ms" "$LOG_FILE" | tail -10

echo -e "\n=== Shard Operations ==="
grep -E "shard|allocation" "$LOG_FILE" | tail -10
```

### Performance Monitoring Script

**Real-time Performance Monitor:**
```python
#!/usr/bin/env python3

import requests
import time
import json
from datetime import datetime

class ESMonitor:
    def __init__(self, host='localhost:9200'):
        self.host = host
        self.url = f'http://{host}'
    
    def get_cluster_stats(self):
        response = requests.get(f'{self.url}/_cluster/stats')
        return response.json()
    
    def get_node_stats(self):
        response = requests.get(f'{self.url}/_nodes/stats')
        return response.json()
    
    def monitor_performance(self):
        while True:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                # Get stats
                cluster_stats = self.get_cluster_stats()
                node_stats = self.get_node_stats()
                
                # Extract key metrics
                indices = cluster_stats['indices']
                search_rate = indices['search']['query_total']
                index_rate = indices['indexing']['index_total']
                
                print(f"[{timestamp}] Search: {search_rate}, Index: {index_rate}")
                
                # Check for issues
                for node_id, node in node_stats['nodes'].items():
                    heap_percent = node['jvm']['mem']['heap_used_percent']
                    if heap_percent > 85:
                        print(f"WARNING: High heap usage on {node['name']}: {heap_percent}%")
                
            except Exception as e:
                print(f"[{timestamp}] Error: {e}")
            
            time.sleep(10)

if __name__ == "__main__":
    monitor = ESMonitor()
    monitor.monitor_performance()
```

### Health Check Automation

**Comprehensive Health Check:**
```bash
#!/bin/bash

ES_HOST="localhost:9200"

check_health() {
    local status=$(curl -s "$ES_HOST/_cluster/health" | jq -r '.status')
    case $status in
        "green")
            echo "✅ Cluster health: GREEN"
            return 0
            ;;
        "yellow")
            echo "⚠️  Cluster health: YELLOW"
            return 1
            ;;
        "red")
            echo "🚨 Cluster health: RED"
            return 2
            ;;
        *)
            echo "❌ Unable to determine cluster health"
            return 3
            ;;
    esac
}

check_disk_space() {
    local high_usage=$(curl -s "$ES_HOST/_cat/allocation?h=node,disk.used_percent" | awk '$2 > 85 {print $1 ": " $2 "%"}')
    if [ -n "$high_usage" ]; then
        echo "⚠️  High disk usage:"
        echo "$high_usage"
        return 1
    else
        echo "✅ Disk usage normal"
        return 0
    fi
}

check_memory() {
    local high_heap=$(curl -s "$ES_HOST/_nodes/stats/jvm" | jq -r '.nodes[] | select(.jvm.mem.heap_used_percent > 85) | .name + ": " + (.jvm.mem.heap_used_percent|tostring) + "%"')
    if [ -n "$high_heap" ]; then
        echo "⚠️  High heap usage:"
        echo "$high_heap"
        return 1
    else
        echo "✅ Memory usage normal"
        return 0
    fi
}

# Run checks
echo "=== Elasticsearch Health Check ==="
check_health
health_status=$?

check_disk_space
disk_status=$?

check_memory
memory_status=$?

# Overall status
if [ $health_status -eq 0 ] && [ $disk_status -eq 0 ] && [ $memory_status -eq 0 ]; then
    echo "✅ All systems healthy"
    exit 0
else
    echo "⚠️  Issues detected"
    exit 1
fi
```

## 🔗 Next Steps

You've now completed the comprehensive Elasticsearch learning documentation! Here are suggested next steps:

1. **[Examples Section](../examples/)** - Explore real-world implementation examples
2. **Practice Labs** - Set up your own cluster and practice troubleshooting
3. **Advanced Topics** - Explore specific use cases for your domain
4. **Community Resources** - Join Elasticsearch forums and communities

## 📚 Key Takeaways

- ✅ **Follow systematic troubleshooting** methodology for consistent results
- ✅ **Gather comprehensive diagnostics** before attempting fixes
- ✅ **Monitor key metrics** continuously to prevent issues
- ✅ **Document solutions** for future reference and team knowledge
- ✅ **Practice emergency procedures** in test environments
- ✅ **Understand root causes** rather than just symptoms
- ✅ **Use proper logging** and monitoring to aid diagnosis
- ✅ **Test changes carefully** in non-production environments first
- ✅ **Keep backups current** for data recovery scenarios
- ✅ **Automate health checks** for proactive issue detection

Congratulations on completing the Elasticsearch learning journey! You now have comprehensive knowledge of Elasticsearch from fundamentals to advanced production operations.