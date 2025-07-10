# Monitoring & Operations

**Monitor cluster health, performance metrics, and operational best practices for production Elasticsearch**

*Estimated reading time: 40 minutes*

## Overview

Effective monitoring is essential for maintaining healthy Elasticsearch clusters in production. This guide covers cluster health monitoring, performance metrics, alerting strategies, log analysis, and operational procedures for ensuring reliable service.

## 📋 Table of Contents

1. [Monitoring Fundamentals](#monitoring-fundamentals)
2. [Cluster Health Monitoring](#cluster-health-monitoring)
3. [Performance Metrics](#performance-metrics)
4. [Alerting and Notifications](#alerting-and-notifications)
5. [Log Analysis](#log-analysis)
6. [Operational Procedures](#operational-procedures)
7. [Monitoring Tools](#monitoring-tools)

## 📊 Monitoring Fundamentals

### Key Monitoring Principles

- **Proactive Monitoring**: Detect issues before they impact users
- **Comprehensive Coverage**: Monitor all cluster components
- **Meaningful Alerts**: Reduce noise, focus on actionable alerts
- **Historical Tracking**: Maintain metrics for trend analysis
- **Automated Response**: Implement self-healing where possible

### Monitoring Stack Components

```bash
# Core monitoring components
1. Elasticsearch Monitoring (X-Pack)
2. Metricbeat for system metrics
3. Filebeat for log collection
4. Kibana for visualization
5. External monitoring (Prometheus, Grafana)
```

## 🏥 Cluster Health Monitoring

### Cluster Health API

**Basic Health Check:**
```bash
curl -X GET "localhost:9200/_cluster/health?pretty"
```

**Response Analysis:**
```json
{
  "cluster_name": "my-cluster",
  "status": "green",           // green, yellow, red
  "timed_out": false,
  "number_of_nodes": 3,
  "number_of_data_nodes": 3,
  "active_primary_shards": 15,
  "active_shards": 30,
  "relocating_shards": 0,
  "initializing_shards": 0,
  "unassigned_shards": 0,
  "delayed_unassigned_shards": 0,
  "number_of_pending_tasks": 0,
  "number_of_in_flight_fetch": 0,
  "task_max_waiting_in_queue_millis": 0,
  "active_shards_percent_as_number": 100.0
}
```

### Detailed Health Monitoring

**Index-level Health:**
```bash
curl -X GET "localhost:9200/_cluster/health?level=indices&pretty"
```

**Shard-level Health:**
```bash
curl -X GET "localhost:9200/_cluster/health?level=shards&pretty"
```

**Wait for Status:**
```bash
# Wait for green status
curl -X GET "localhost:9200/_cluster/health?wait_for_status=green&timeout=30s"

# Wait for specific number of nodes
curl -X GET "localhost:9200/_cluster/health?wait_for_nodes=3&timeout=30s"
```

### Node Health Monitoring

**Node Stats:**
```bash
curl -X GET "localhost:9200/_nodes/stats?pretty"
```

**Node Information:**
```bash
curl -X GET "localhost:9200/_nodes?pretty"
curl -X GET "localhost:9200/_cat/nodes?v&h=name,heap.percent,ram.percent,cpu,load_1m,node.role,master"
```

**Hot Threads Detection:**
```bash
curl -X GET "localhost:9200/_nodes/hot_threads?threads=5&interval=1s"
```

## 📈 Performance Metrics

### Index Performance

**Indexing Metrics:**
```bash
curl -X GET "localhost:9200/_stats/indexing?pretty"
```

**Key Indexing Metrics:**
```json
{
  "indexing": {
    "index_total": 1000000,
    "index_time_in_millis": 45000,
    "index_current": 5,
    "index_failed": 0,
    "delete_total": 1000,
    "delete_time_in_millis": 500,
    "delete_current": 0,
    "throttle_time_in_millis": 0
  }
}
```

### Search Performance

**Search Metrics:**
```bash
curl -X GET "localhost:9200/_stats/search?pretty"
```

**Key Search Metrics:**
```json
{
  "search": {
    "open_contexts": 2,
    "query_total": 50000,
    "query_time_in_millis": 125000,
    "query_current": 3,
    "fetch_total": 25000,
    "fetch_time_in_millis": 15000,
    "fetch_current": 1,
    "scroll_total": 100,
    "scroll_time_in_millis": 5000,
    "scroll_current": 0
  }
}
```

### JVM Performance

**JVM Stats:**
```bash
curl -X GET "localhost:9200/_nodes/stats/jvm?pretty"
```

**GC Monitoring:**
```json
{
  "jvm": {
    "mem": {
      "heap_used_percent": 45,
      "heap_used_in_bytes": 1073741824,
      "heap_max_in_bytes": 2147483648
    },
    "gc": {
      "collectors": {
        "young": {
          "collection_count": 1000,
          "collection_time_in_millis": 5000
        },
        "old": {
          "collection_count": 10,
          "collection_time_in_millis": 2000
        }
      }
    }
  }
}
```

### System Resource Monitoring

**OS Stats:**
```bash
curl -X GET "localhost:9200/_nodes/stats/os?pretty"
```

**File System Stats:**
```bash
curl -X GET "localhost:9200/_nodes/stats/fs?pretty"
```

**Thread Pool Stats:**
```bash
curl -X GET "localhost:9200/_nodes/stats/thread_pool?pretty"
```

## 🚨 Alerting and Notifications

### Critical Alerts

**Cluster Status Alerts:**
```bash
# Monitor cluster status
if [ "$(curl -s localhost:9200/_cluster/health | jq -r '.status')" != "green" ]; then
  echo "ALERT: Cluster status is not green"
  # Send notification
fi
```

**Disk Space Monitoring:**
```bash
# Check disk usage
curl -X GET "localhost:9200/_cat/allocation?v&h=node,disk.used_percent" | awk '$2 > 85 {print "ALERT: High disk usage on " $1 ": " $2 "%"}'
```

**Memory Usage Alerts:**
```bash
# Monitor JVM heap usage
curl -X GET "localhost:9200/_nodes/stats/jvm" | jq '.nodes[] | select(.jvm.mem.heap_used_percent > 85) | {name: .name, heap_percent: .jvm.mem.heap_used_percent}'
```

### Watcher Configuration

**Cluster Health Watcher:**
```bash
curl -X PUT "localhost:9200/_watcher/watch/cluster_health_watch" -H 'Content-Type: application/json' -d'
{
  "trigger": {
    "schedule": {
      "interval": "30s"
    }
  },
  "input": {
    "http": {
      "request": {
        "host": "localhost",
        "port": 9200,
        "path": "/_cluster/health"
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.status": {
        "ne": "green"
      }
    }
  },
  "actions": {
    "send_email": {
      "email": {
        "to": ["admin@company.com"],
        "subject": "Elasticsearch Cluster Health Alert",
        "body": "Cluster status is {{ctx.payload.status}}"
      }
    }
  }
}
'
```

**Search Performance Watcher:**
```bash
curl -X PUT "localhost:9200/_watcher/watch/search_performance_watch" -H 'Content-Type: application/json' -d'
{
  "trigger": {
    "schedule": {
      "interval": "1m"
    }
  },
  "input": {
    "search": {
      "request": {
        "indices": "_all",
        "body": {
          "size": 0,
          "aggs": {
            "avg_search_time": {
              "avg": {
                "field": "took"
              }
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.aggregations.avg_search_time.value": {
        "gt": 1000
      }
    }
  },
  "actions": {
    "log_alert": {
      "logging": {
        "text": "High search latency detected: {{ctx.payload.aggregations.avg_search_time.value}}ms"
      }
    }
  }
}
'
```

### Alertmanager Integration

**Prometheus Alert Rules:**
```yaml
groups:
- name: elasticsearch
  rules:
  - alert: ElasticsearchClusterRed
    expr: elasticsearch_cluster_health_status{color="red"} == 1
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "Elasticsearch cluster status is red"
      
  - alert: ElasticsearchHighHeapUsage
    expr: elasticsearch_jvm_memory_used_bytes{area="heap"} / elasticsearch_jvm_memory_max_bytes{area="heap"} > 0.85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Elasticsearch node heap usage is high"
      
  - alert: ElasticsearchLowDiskSpace
    expr: elasticsearch_filesystem_data_available_bytes / elasticsearch_filesystem_data_size_bytes < 0.15
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Elasticsearch node disk space is low"
```

## 📋 Log Analysis

### Elasticsearch Logs

**Log Levels and Configuration:**
```yaml
# log4j2.properties
logger.action.name = org.elasticsearch.action
logger.action.level = debug

logger.index.name = org.elasticsearch.index
logger.index.level = info

logger.discovery.name = org.elasticsearch.discovery
logger.discovery.level = info

appender.console.type = Console
appender.console.name = console
appender.console.layout.type = PatternLayout
appender.console.layout.pattern = [%d{ISO8601}][%-5p][%-25c{1.}] [%node_name]%marker %m%n
```

**Common Log Patterns:**
```bash
# Search for errors
grep "ERROR" /var/log/elasticsearch/my-cluster.log

# Monitor GC logs
grep "GC" /var/log/elasticsearch/gc.log

# Check for slow queries
grep "slow_log" /var/log/elasticsearch/my-cluster_index_search_slowlog.log
```

### Slow Log Configuration

**Search Slow Log:**
```bash
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.search.slowlog.threshold.query.warn": "10s",
  "index.search.slowlog.threshold.query.info": "5s",
  "index.search.slowlog.threshold.query.debug": "2s",
  "index.search.slowlog.threshold.query.trace": "500ms",
  "index.search.slowlog.threshold.fetch.warn": "1s",
  "index.search.slowlog.threshold.fetch.info": "800ms",
  "index.search.slowlog.threshold.fetch.debug": "500ms",
  "index.search.slowlog.threshold.fetch.trace": "200ms"
}
'
```

**Index Slow Log:**
```bash
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.indexing.slowlog.threshold.index.warn": "10s",
  "index.indexing.slowlog.threshold.index.info": "5s",
  "index.indexing.slowlog.threshold.index.debug": "2s",
  "index.indexing.slowlog.threshold.index.trace": "500ms"
}
'
```

### Log Aggregation with ELK

**Filebeat Configuration:**
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/elasticsearch/*.log
  fields:
    service: elasticsearch
    environment: production
  fields_under_root: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "elasticsearch-logs-%{+yyyy.MM.dd}"

setup.template.name: "elasticsearch-logs"
setup.template.pattern: "elasticsearch-logs-*"
```

**Logstash Pipeline:**
```ruby
input {
  beats {
    port => 5044
  }
}

filter {
  if [service] == "elasticsearch" {
    grok {
      match => { 
        "message" => "\[%{TIMESTAMP_ISO8601:timestamp}\]\[%{WORD:level}\s*\]\[%{DATA:logger}\] \[%{DATA:node}\] %{GREEDYDATA:msg}" 
      }
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    if [level] == "ERROR" or [level] == "WARN" {
      mutate {
        add_tag => [ "alert" ]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "elasticsearch-logs-%{+YYYY.MM.dd}"
  }
}
```

## 🔧 Operational Procedures

### Health Check Scripts

**Comprehensive Health Check:**
```bash
#!/bin/bash

# Elasticsearch Health Check Script
ES_HOST="localhost:9200"

echo "=== Elasticsearch Health Check ==="
echo "Timestamp: $(date)"

# Cluster health
echo -e "\n1. Cluster Health:"
CLUSTER_STATUS=$(curl -s "$ES_HOST/_cluster/health" | jq -r '.status')
echo "Status: $CLUSTER_STATUS"

if [ "$CLUSTER_STATUS" != "green" ]; then
    echo "⚠️  Cluster is not healthy!"
    curl -s "$ES_HOST/_cluster/health?pretty"
fi

# Node count
echo -e "\n2. Node Status:"
NODE_COUNT=$(curl -s "$ES_HOST/_cat/nodes?h=name" | wc -l)
echo "Active nodes: $NODE_COUNT"

# Disk usage
echo -e "\n3. Disk Usage:"
curl -s "$ES_HOST/_cat/allocation?v&h=node,disk.used_percent" | awk 'NR>1 {
    if ($2 > 85) print "⚠️  " $1 ": " $2 "% (HIGH)"
    else print "✅ " $1 ": " $2 "%"
}'

# Memory usage
echo -e "\n4. Memory Usage:"
curl -s "$ES_HOST/_nodes/stats/jvm" | jq -r '.nodes[] | "Node: " + .name + " - Heap: " + (.jvm.mem.heap_used_percent|tostring) + "%"'

# Index status
echo -e "\n5. Index Status:"
YELLOW_INDICES=$(curl -s "$ES_HOST/_cat/indices?h=health,index" | grep yellow | wc -l)
RED_INDICES=$(curl -s "$ES_HOST/_cat/indices?h=health,index" | grep red | wc -l)

echo "Yellow indices: $YELLOW_INDICES"
echo "Red indices: $RED_INDICES"

if [ "$RED_INDICES" -gt 0 ]; then
    echo "🚨 Red indices found:"
    curl -s "$ES_HOST/_cat/indices?h=health,index" | grep red
fi

# Pending tasks
echo -e "\n6. Pending Tasks:"
PENDING_TASKS=$(curl -s "$ES_HOST/_cluster/health" | jq -r '.number_of_pending_tasks')
echo "Pending tasks: $PENDING_TASKS"

if [ "$PENDING_TASKS" -gt 0 ]; then
    echo "⚠️  Tasks pending:"
    curl -s "$ES_HOST/_cat/pending_tasks?v"
fi

echo -e "\n=== Health Check Complete ==="
```

### Maintenance Scripts

**Cluster Maintenance:**
```bash
#!/bin/bash

# Elasticsearch Maintenance Script
ES_HOST="localhost:9200"

echo "=== Starting Elasticsearch Maintenance ==="

# 1. Clear old logs
echo "1. Clearing old indices..."
INDICES_TO_DELETE=$(curl -s "$ES_HOST/_cat/indices?h=index,creation.date.string" | \
    awk -v cutoff="$(date -d '30 days ago' '+%Y-%m-%d')" '$2 < cutoff {print $1}')

for index in $INDICES_TO_DELETE; do
    echo "Deleting old index: $index"
    curl -X DELETE "$ES_HOST/$index"
done

# 2. Force merge old indices
echo -e "\n2. Force merging indices..."
OLD_INDICES=$(curl -s "$ES_HOST/_cat/indices?h=index,creation.date.string" | \
    awk -v cutoff="$(date -d '7 days ago' '+%Y-%m-%d')" '$2 < cutoff {print $1}')

for index in $OLD_INDICES; do
    echo "Force merging index: $index"
    curl -X POST "$ES_HOST/$index/_forcemerge?max_num_segments=1" &
done
wait

# 3. Clear cache
echo -e "\n3. Clearing caches..."
curl -X POST "$ES_HOST/_cache/clear"

# 4. Optimize allocation
echo -e "\n4. Optimizing shard allocation..."
curl -X PUT "$ES_HOST/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "cluster.routing.rebalance.enable": "all"
  }
}'

echo -e "\n=== Maintenance Complete ==="
```

### Backup Procedures

**Automated Backup Script:**
```bash
#!/bin/bash

# Elasticsearch Backup Script
ES_HOST="localhost:9200"
REPO_NAME="backup_repo"
SNAPSHOT_NAME="snapshot_$(date +%Y%m%d_%H%M%S)"

echo "=== Creating Elasticsearch Snapshot ==="

# Create snapshot
echo "Creating snapshot: $SNAPSHOT_NAME"
curl -X PUT "$ES_HOST/_snapshot/$REPO_NAME/$SNAPSHOT_NAME?wait_for_completion=true" -H 'Content-Type: application/json' -d'
{
  "indices": "*",
  "ignore_unavailable": true,
  "include_global_state": false,
  "metadata": {
    "taken_by": "backup_script",
    "taken_because": "scheduled_backup"
  }
}
'

# Verify snapshot
echo -e "\nVerifying snapshot..."
SNAPSHOT_STATUS=$(curl -s "$ES_HOST/_snapshot/$REPO_NAME/$SNAPSHOT_NAME" | jq -r '.snapshots[0].state')

if [ "$SNAPSHOT_STATUS" == "SUCCESS" ]; then
    echo "✅ Snapshot created successfully"
else
    echo "❌ Snapshot failed: $SNAPSHOT_STATUS"
    exit 1
fi

# Cleanup old snapshots
echo -e "\nCleaning up old snapshots..."
OLD_SNAPSHOTS=$(curl -s "$ES_HOST/_snapshot/$REPO_NAME/_all" | \
    jq -r --arg cutoff "$(date -d '7 days ago' '+%Y-%m-%dT%H:%M:%S')" \
    '.snapshots[] | select(.start_time < $cutoff) | .snapshot')

for snapshot in $OLD_SNAPSHOTS; do
    echo "Deleting old snapshot: $snapshot"
    curl -X DELETE "$ES_HOST/_snapshot/$REPO_NAME/$snapshot"
done

echo -e "\n=== Backup Complete ==="
```

## 🛠️ Monitoring Tools

### Built-in Monitoring

**Enable X-Pack Monitoring:**
```yaml
# elasticsearch.yml
xpack.monitoring.collection.enabled: true
xpack.monitoring.collection.interval: 10s
xpack.monitoring.exporters:
  id1:
    type: http
    host: ["monitoring-cluster:9200"]
```

### Prometheus Integration

**Elasticsearch Exporter:**
```bash
# Run elasticsearch_exporter
./elasticsearch_exporter \
  --es.uri=http://localhost:9200 \
  --es.all \
  --es.indices \
  --es.shards \
  --web.listen-address=":9114"
```

**Prometheus Configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['localhost:9114']
    scrape_interval: 30s
    metrics_path: /metrics
```

### Grafana Dashboards

**Key Dashboard Panels:**
```json
{
  "dashboard": {
    "title": "Elasticsearch Monitoring",
    "panels": [
      {
        "title": "Cluster Health",
        "type": "stat",
        "targets": [
          {
            "expr": "elasticsearch_cluster_health_status"
          }
        ]
      },
      {
        "title": "Search Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(elasticsearch_indices_search_query_total[5m])"
          }
        ]
      },
      {
        "title": "Index Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(elasticsearch_indices_indexing_index_total[5m])"
          }
        ]
      },
      {
        "title": "JVM Heap Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "elasticsearch_jvm_memory_used_bytes{area=\"heap\"} / elasticsearch_jvm_memory_max_bytes{area=\"heap\"} * 100"
          }
        ]
      }
    ]
  }
}
```

### Custom Monitoring Scripts

**Performance Monitoring:**
```python
#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

class ElasticsearchMonitor:
    def __init__(self, host='localhost:9200'):
        self.host = host
        self.base_url = f'http://{host}'
    
    def get_cluster_health(self):
        response = requests.get(f'{self.base_url}/_cluster/health')
        return response.json()
    
    def get_node_stats(self):
        response = requests.get(f'{self.base_url}/_nodes/stats')
        return response.json()
    
    def get_index_stats(self):
        response = requests.get(f'{self.base_url}/_stats')
        return response.json()
    
    def check_performance(self):
        stats = self.get_node_stats()
        alerts = []
        
        for node_id, node in stats['nodes'].items():
            node_name = node['name']
            
            # Check heap usage
            heap_percent = node['jvm']['mem']['heap_used_percent']
            if heap_percent > 85:
                alerts.append(f"High heap usage on {node_name}: {heap_percent}%")
            
            # Check CPU usage
            if 'cpu' in node['os']:
                cpu_percent = node['os']['cpu']['percent']
                if cpu_percent > 80:
                    alerts.append(f"High CPU usage on {node_name}: {cpu_percent}%")
            
            # Check disk usage
            for fs in node['fs']['data']:
                disk_usage = (fs['total_in_bytes'] - fs['available_in_bytes']) / fs['total_in_bytes'] * 100
                if disk_usage > 85:
                    alerts.append(f"High disk usage on {node_name}: {disk_usage:.1f}%")
        
        return alerts
    
    def monitor_loop(self, interval=60):
        while True:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Check cluster health
            health = self.get_cluster_health()
            print(f"[{timestamp}] Cluster Status: {health['status']}")
            
            # Check performance issues
            alerts = self.check_performance()
            for alert in alerts:
                print(f"[{timestamp}] ALERT: {alert}")
            
            if not alerts:
                print(f"[{timestamp}] All systems normal")
            
            time.sleep(interval)

if __name__ == "__main__":
    monitor = ElasticsearchMonitor()
    monitor.monitor_loop()
```

## 🔗 Next Steps

Now that you've learned about monitoring and operations, let's explore index management:

1. **[Index Management](index-management.md)** - Advanced index lifecycle and optimization
2. **[Troubleshooting](troubleshooting.md)** - Diagnose and resolve common issues
3. **[Security & Authentication](security-authentication.md)** - Secure your cluster

## 📚 Key Takeaways

- ✅ **Monitor cluster health** continuously with automated checks
- ✅ **Set up meaningful alerts** that are actionable and reduce noise
- ✅ **Track performance metrics** for indexing, search, and system resources
- ✅ **Implement log aggregation** for centralized monitoring
- ✅ **Create operational procedures** for maintenance and emergency response
- ✅ **Use external monitoring tools** like Prometheus and Grafana
- ✅ **Monitor slow queries** to identify performance bottlenecks
- ✅ **Automate routine tasks** like snapshots and maintenance
- ✅ **Document procedures** for troubleshooting and incident response
- ✅ **Test monitoring systems** regularly to ensure they work when needed

Ready to learn about advanced index management? Continue with [Index Management](index-management.md) to master index lifecycle and optimization techniques!