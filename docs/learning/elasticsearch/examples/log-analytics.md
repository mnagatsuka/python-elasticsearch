# Log Analytics Implementation

**Build a centralized logging and monitoring solution with real-time analysis and alerting**

*Implementation time: 2-3 hours*

## Overview

This example demonstrates building a comprehensive log analytics platform using the ELK Stack (Elasticsearch, Logstash, Kibana) with real-time log ingestion, analysis, alerting, and visualization capabilities commonly found in production monitoring systems.

## 🎯 Features Implemented

- **Centralized Log Ingestion** - Collect logs from multiple sources and applications
- **Real-time Processing** - Parse, enrich, and index logs in near real-time
- **Advanced Search** - Full-text search across all log data with filtering
- **Analytics Dashboards** - Visual insights into application health and performance
- **Alerting System** - Automated alerts for errors, anomalies, and SLA breaches
- **Log Retention** - Automated lifecycle management and archival

## 🏗️ Architecture Overview

```
Applications → Filebeat → Logstash → Elasticsearch → Kibana
     ↓              ↓         ↓           ↓          ↓
Log Files    Collection  Processing   Storage   Visualization
```

## 📋 Prerequisites

- Elasticsearch 8.x cluster
- Logstash 8.x
- Filebeat 8.x
- Kibana 8.x
- Docker and Docker Compose
- Sample application logs

## 🚀 Quick Start

### 1. Docker Compose Setup

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - node.name=elasticsearch
      - cluster.name=log-analytics-cluster
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=false
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - elk

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: logstash
    volumes:
      - ./logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
    ports:
      - "5044:5044"
      - "5000:5000/tcp"
      - "5000:5000/udp"
      - "9600:9600"
    environment:
      LS_JAVA_OPTS: "-Xmx1g -Xms1g"
    networks:
      - elk
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_URL: http://elasticsearch:9200
      ELASTICSEARCH_HOSTS: '["http://elasticsearch:9200"]'
    networks:
      - elk
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: filebeat
    user: root
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./logs:/var/log/app:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: filebeat -e -strict.perms=false
    networks:
      - elk
    depends_on:
      - logstash

volumes:
  elasticsearch_data:
    driver: local

networks:
  elk:
    driver: bridge
```

### 2. Logstash Configuration

**logstash/config/logstash.yml:**
```yaml
http.host: "0.0.0.0"
xpack.monitoring.elasticsearch.hosts: [ "http://elasticsearch:9200" ]
path.config: /usr/share/logstash/pipeline
```

**logstash/pipeline/logstash.conf:**
```ruby
input {
  beats {
    port => 5044
  }
  
  # Direct log input for testing
  tcp {
    port => 5000
    codec => json_lines
  }
  
  # HTTP input for API logs
  http {
    port => 8080
    codec => json
  }
}

filter {
  # Parse JSON logs
  if [message] =~ /^\{.*\}$/ {
    json {
      source => "message"
    }
  }
  
  # Parse common log formats
  if [fields][log_type] == "nginx" {
    grok {
      match => { 
        "message" => "%{NGINXACCESS}"
      }
    }
    
    date {
      match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
    }
    
    mutate {
      convert => { 
        "response" => "integer"
        "bytes" => "integer"
        "responsetime" => "float"
      }
    }
  }
  
  # Parse application logs
  if [fields][log_type] == "application" {
    grok {
      match => { 
        "message" => "\[%{TIMESTAMP_ISO8601:timestamp}\] %{LOGLEVEL:level} %{GREEDYDATA:logger}: %{GREEDYDATA:log_message}"
      }
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
  
  # Parse Docker container logs
  if [container] {
    mutate {
      add_field => { "service" => "%{[container][name]}" }
    }
  }
  
  # Enrich with GeoIP for access logs
  if [clientip] {
    geoip {
      source => "clientip"
      target => "geoip"
    }
  }
  
  # Add common fields
  mutate {
    add_field => { 
      "[@metadata][target_index]" => "logs-%{+YYYY.MM.dd}"
      "ingestion_timestamp" => "%{@timestamp}"
    }
  }
  
  # Classify log levels
  if [level] {
    if [level] in ["ERROR", "FATAL", "error", "fatal"] {
      mutate { add_tag => ["error"] }
    } else if [level] in ["WARN", "WARNING", "warn", "warning"] {
      mutate { add_tag => ["warning"] }
    } else if [level] in ["INFO", "info"] {
      mutate { add_tag => ["info"] }
    } else if [level] in ["DEBUG", "debug"] {
      mutate { add_tag => ["debug"] }
    }
  }
  
  # Extract error patterns
  if "error" in [tags] {
    grok {
      match => { 
        "log_message" => "(?<error_type>Exception|Error|Fault).*?(?<error_class>[A-Za-z][A-Za-z0-9]*(?:Exception|Error))"
      }
      tag_on_failure => []
    }
  }
  
  # Performance monitoring
  if [responsetime] {
    if [responsetime] > 5000 {
      mutate { add_tag => ["slow_response"] }
    }
  }
  
  # Security monitoring
  if [response] {
    if [response] >= 400 and [response] < 500 {
      mutate { add_tag => ["client_error"] }
    } else if [response] >= 500 {
      mutate { add_tag => ["server_error"] }
    }
  }
  
  # Rate limiting detection
  if [response] == 429 {
    mutate { add_tag => ["rate_limited"] }
  }
  
  # Remove unwanted fields
  mutate {
    remove_field => ["agent", "ecs", "input", "log"]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][target_index]}"
    template_name => "logs"
    template_pattern => "logs-*"
    template => "/usr/share/logstash/templates/logs-template.json"
    template_overwrite => true
  }
  
  # Debug output (remove in production)
  if "error" in [tags] {
    stdout { 
      codec => rubydebug 
    }
  }
}
```

### 3. Index Template

**logstash/templates/logs-template.json:**
```json
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs_policy",
      "index.lifecycle.rollover_alias": "logs",
      "refresh_interval": "5s",
      "codec": "best_compression"
    },
    "mappings": {
      "properties": {
        "@timestamp": {
          "type": "date"
        },
        "level": {
          "type": "keyword"
        },
        "logger": {
          "type": "keyword"
        },
        "service": {
          "type": "keyword"
        },
        "host": {
          "type": "keyword"
        },
        "environment": {
          "type": "keyword"
        },
        "message": {
          "type": "text",
          "norms": false
        },
        "log_message": {
          "type": "text",
          "norms": false
        },
        "error_type": {
          "type": "keyword"
        },
        "error_class": {
          "type": "keyword"
        },
        "stack_trace": {
          "type": "text",
          "norms": false,
          "index": false
        },
        "clientip": {
          "type": "ip"
        },
        "response": {
          "type": "integer"
        },
        "bytes": {
          "type": "long"
        },
        "responsetime": {
          "type": "float"
        },
        "request": {
          "type": "keyword"
        },
        "verb": {
          "type": "keyword"
        },
        "referrer": {
          "type": "keyword"
        },
        "agent": {
          "type": "text",
          "norms": false
        },
        "geoip": {
          "properties": {
            "location": {
              "type": "geo_point"
            },
            "country_name": {
              "type": "keyword"
            },
            "city_name": {
              "type": "keyword"
            },
            "continent_code": {
              "type": "keyword"
            }
          }
        },
        "container": {
          "properties": {
            "name": {
              "type": "keyword"
            },
            "id": {
              "type": "keyword"
            }
          }
        },
        "kubernetes": {
          "properties": {
            "namespace": {
              "type": "keyword"
            },
            "pod": {
              "type": "keyword"
            },
            "container": {
              "type": "keyword"
            }
          }
        }
      }
    }
  }
}
```

### 4. Filebeat Configuration

**filebeat/filebeat.yml:**
```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/app/*.log
    - /var/log/app/**/*.log
  fields:
    log_type: application
    environment: production
  fields_under_root: true
  multiline.pattern: '^\['
  multiline.negate: true
  multiline.match: after

- type: log
  enabled: true
  paths:
    - /var/log/nginx/access.log
  fields:
    log_type: nginx
    service: nginx
  fields_under_root: true

- type: docker
  containers.ids:
    - "*"
  processors:
    - add_docker_metadata:
        host: "unix:///var/run/docker.sock"

processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  - drop_fields:
      fields: ["beat", "offset", "prospector"]

output.logstash:
  hosts: ["logstash:5044"]

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

### 5. Index Lifecycle Management

**ILM Policy Setup:**
```bash
curl -X PUT "localhost:9200/_ilm/policy/logs_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "10gb",
            "max_age": "1d",
            "max_docs": 10000000
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "1d",
        "actions": {
          "set_priority": {
            "priority": 50
          },
          "allocate": {
            "number_of_replicas": 0
          },
          "forcemerge": {
            "max_num_segments": 1
          }
        }
      },
      "cold": {
        "min_age": "7d",
        "actions": {
          "set_priority": {
            "priority": 0
          },
          "allocate": {
            "include": {
              "_tier_preference": "data_cold"
            }
          }
        }
      },
      "delete": {
        "min_age": "30d"
      }
    }
  }
}
'
```

## 📊 Analytics and Monitoring

### 1. Log Analytics API

**Python FastAPI Service:**
```python
#!/usr/bin/env python3

from fastapi import FastAPI, Query, HTTPException
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

app = FastAPI(title="Log Analytics API")
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

@app.get("/logs/search")
async def search_logs(
    q: Optional[str] = Query(None, description="Search query"),
    level: Optional[str] = Query(None, description="Log level filter"),
    service: Optional[str] = Query(None, description="Service filter"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    size: int = Query(100, ge=1, le=1000, description="Number of results"),
    page: int = Query(1, ge=1, description="Page number")
):
    """Search logs with filters and pagination"""
    
    # Build query
    query = {"bool": {"must": [], "filter": []}}
    
    # Text search
    if q:
        query["bool"]["must"].append({
            "multi_match": {
                "query": q,
                "fields": ["message^2", "log_message^2", "logger", "error_type"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        })
    else:
        query["bool"]["must"].append({"match_all": {}})
    
    # Level filter
    if level:
        query["bool"]["filter"].append({"term": {"level": level.upper()}})
    
    # Service filter
    if service:
        query["bool"]["filter"].append({"term": {"service": service}})
    
    # Time range filter
    if start_time or end_time:
        time_range = {}
        if start_time:
            time_range["gte"] = start_time
        if end_time:
            time_range["lte"] = end_time
        query["bool"]["filter"].append({"range": {"@timestamp": time_range}})
    
    # Search request
    search_body = {
        "query": query,
        "sort": [{"@timestamp": {"order": "desc"}}],
        "from": (page - 1) * size,
        "size": size,
        "aggs": {
            "levels": {"terms": {"field": "level"}},
            "services": {"terms": {"field": "service"}},
            "error_types": {"terms": {"field": "error_type"}}
        }
    }
    
    try:
        response = es.search(index="logs-*", body=search_body)
        
        logs = []
        for hit in response['hits']['hits']:
            log_entry = hit['_source']
            log_entry['_id'] = hit['_id']
            log_entry['_score'] = hit['_score']
            logs.append(log_entry)
        
        return {
            "logs": logs,
            "total": response['hits']['total']['value'],
            "page": page,
            "size": size,
            "aggregations": {
                "levels": [
                    {"level": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in response.get('aggregations', {}).get('levels', {}).get('buckets', [])
                ],
                "services": [
                    {"service": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in response.get('aggregations', {}).get('services', {}).get('buckets', [])
                ],
                "error_types": [
                    {"error_type": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in response.get('aggregations', {}).get('error_types', {}).get('buckets', [])
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/logs/stats")
async def get_log_stats(
    time_range: str = Query("1h", description="Time range: 1h, 24h, 7d, 30d")
):
    """Get log statistics and metrics"""
    
    # Calculate time range
    time_deltas = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    
    since_time = datetime.now() - time_deltas.get(time_range, timedelta(hours=1))
    
    search_body = {
        "query": {
            "range": {
                "@timestamp": {
                    "gte": since_time.isoformat()
                }
            }
        },
        "size": 0,
        "aggs": {
            "log_levels": {
                "terms": {"field": "level", "size": 10}
            },
            "services": {
                "terms": {"field": "service", "size": 20}
            },
            "error_rate": {
                "filter": {"terms": {"level": ["ERROR", "FATAL"]}},
                "aggs": {
                    "over_time": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "fixed_interval": "1m"
                        }
                    }
                }
            },
            "response_codes": {
                "terms": {"field": "response", "size": 10}
            },
            "top_errors": {
                "filter": {"terms": {"level": ["ERROR", "FATAL"]}},
                "aggs": {
                    "error_types": {
                        "terms": {"field": "error_type", "size": 10}
                    }
                }
            },
            "performance": {
                "filter": {"exists": {"field": "responsetime"}},
                "aggs": {
                    "avg_response_time": {"avg": {"field": "responsetime"}},
                    "p95_response_time": {"percentiles": {"field": "responsetime", "percents": [95]}},
                    "slow_requests": {
                        "filter": {"range": {"responsetime": {"gte": 1000}}}
                    }
                }
            }
        }
    }
    
    try:
        response = es.search(index="logs-*", body=search_body)
        aggs = response.get('aggregations', {})
        
        # Calculate error rate
        total_logs = response['hits']['total']['value']
        error_logs = aggs.get('error_rate', {}).get('doc_count', 0)
        error_rate = (error_logs / total_logs * 100) if total_logs > 0 else 0
        
        # Performance metrics
        perf = aggs.get('performance', {})
        avg_response_time = perf.get('avg_response_time', {}).get('value', 0)
        p95_response_time = perf.get('p95_response_time', {}).get('values', {}).get('95.0', 0)
        slow_requests = perf.get('slow_requests', {}).get('doc_count', 0)
        
        return {
            "time_range": time_range,
            "total_logs": total_logs,
            "error_rate": round(error_rate, 2),
            "log_levels": [
                {"level": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs.get('log_levels', {}).get('buckets', [])
            ],
            "services": [
                {"service": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs.get('services', {}).get('buckets', [])
            ],
            "response_codes": [
                {"code": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs.get('response_codes', {}).get('buckets', [])
            ],
            "top_errors": [
                {"error_type": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggs.get('top_errors', {}).get('error_types', {}).get('buckets', [])
            ],
            "performance": {
                "avg_response_time": round(avg_response_time, 2) if avg_response_time else None,
                "p95_response_time": round(p95_response_time, 2) if p95_response_time else None,
                "slow_requests": slow_requests
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.get("/logs/alerts")
async def check_alerts():
    """Check for alert conditions"""
    
    alerts = []
    
    # High error rate alert
    error_rate_query = {
        "query": {
            "bool": {
                "filter": [
                    {"range": {"@timestamp": {"gte": "now-5m"}}},
                    {"terms": {"level": ["ERROR", "FATAL"]}}
                ]
            }
        },
        "size": 0
    }
    
    try:
        error_response = es.search(index="logs-*", body=error_rate_query)
        error_count = error_response['hits']['total']['value']
        
        if error_count > 10:  # Alert if more than 10 errors in 5 minutes
            alerts.append({
                "type": "high_error_rate",
                "severity": "warning" if error_count <= 50 else "critical",
                "message": f"High error rate detected: {error_count} errors in the last 5 minutes",
                "count": error_count,
                "timestamp": datetime.now().isoformat()
            })
        
        # Slow response time alert
        slow_response_query = {
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"@timestamp": {"gte": "now-5m"}}},
                        {"range": {"responsetime": {"gte": 5000}}}
                    ]
                }
            },
            "size": 0
        }
        
        slow_response = es.search(index="logs-*", body=slow_response_query)
        slow_count = slow_response['hits']['total']['value']
        
        if slow_count > 5:  # Alert if more than 5 slow responses in 5 minutes
            alerts.append({
                "type": "slow_response_time",
                "severity": "warning",
                "message": f"Slow response times detected: {slow_count} requests >5s in the last 5 minutes",
                "count": slow_count,
                "timestamp": datetime.now().isoformat()
            })
        
        # Service down alert (no logs for a service)
        services_query = {
            "query": {"range": {"@timestamp": {"gte": "now-1h"}}},
            "size": 0,
            "aggs": {
                "services": {"terms": {"field": "service", "size": 100}}
            }
        }
        
        services_response = es.search(index="logs-*", body=services_query)
        active_services = [
            bucket["key"] 
            for bucket in services_response.get('aggregations', {}).get('services', {}).get('buckets', [])
        ]
        
        expected_services = ["web-app", "api-server", "database", "cache"]  # Configure as needed
        missing_services = set(expected_services) - set(active_services)
        
        for service in missing_services:
            alerts.append({
                "type": "service_down",
                "severity": "critical",
                "message": f"Service '{service}' has not logged any messages in the last hour",
                "service": service,
                "timestamp": datetime.now().isoformat()
            })
        
        return {"alerts": alerts}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alerts error: {str(e)}")

@app.post("/logs/ingest")
async def ingest_log(log_data: dict):
    """Manually ingest a log entry"""
    
    # Add timestamp if not present
    if '@timestamp' not in log_data:
        log_data['@timestamp'] = datetime.now().isoformat()
    
    # Determine index name
    index_name = f"logs-{datetime.now().strftime('%Y.%m.%d')}"
    
    try:
        response = es.index(index=index_name, body=log_data)
        return {"status": "indexed", "id": response['_id']}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Sample Log Generator

**Generate Test Logs:**
```python
#!/usr/bin/env python3

import json
import random
import time
import requests
from datetime import datetime, timedelta
import threading

class LogGenerator:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.services = ["web-app", "api-server", "database", "cache", "auth-service"]
        self.log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
        self.error_types = [
            "ConnectionException", "TimeoutException", "ValidationError", 
            "DatabaseException", "AuthenticationError", "ServiceUnavailable"
        ]
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        
    def generate_application_log(self):
        """Generate application log entry"""
        level = random.choice(self.log_levels)
        service = random.choice(self.services)
        
        if level == "ERROR":
            error_type = random.choice(self.error_types)
            message = f"Exception occurred in {service}: {error_type}"
            log_message = f"Failed to process request: {random.choice(['timeout', 'invalid input', 'connection refused'])}"
        elif level == "WARN":
            message = f"Warning in {service}"
            log_message = f"Performance degradation detected: response time {random.randint(1000, 5000)}ms"
        else:
            message = f"Operation completed in {service}"
            log_message = f"Successfully processed request in {random.randint(10, 500)}ms"
        
        return {
            "@timestamp": datetime.now().isoformat(),
            "level": level,
            "service": service,
            "logger": f"{service}.{random.choice(['controller', 'service', 'repository'])}",
            "message": message,
            "log_message": log_message,
            "host": f"server-{random.randint(1, 5)}",
            "environment": "production",
            "thread": f"thread-{random.randint(1, 20)}",
            "session_id": f"sess_{random.randint(100000, 999999)}"
        }
    
    def generate_access_log(self):
        """Generate HTTP access log entry"""
        methods = ["GET", "POST", "PUT", "DELETE"]
        paths = ["/api/users", "/api/orders", "/api/products", "/health", "/metrics"]
        response_codes = [200, 201, 400, 401, 404, 500, 503]
        
        response_code = random.choice(response_codes)
        response_time = random.randint(10, 2000)
        
        # Increase response time for errors
        if response_code >= 500:
            response_time = random.randint(1000, 10000)
        
        return {
            "@timestamp": datetime.now().isoformat(),
            "service": "nginx",
            "clientip": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "verb": random.choice(methods),
            "request": random.choice(paths),
            "response": response_code,
            "bytes": random.randint(100, 10000),
            "responsetime": response_time,
            "referrer": "https://example.com",
            "agent": random.choice(self.user_agents),
            "host": "web-server",
            "environment": "production"
        }
    
    def send_log(self, log_entry):
        """Send log to ingestion endpoint"""
        try:
            response = requests.post(
                f"{self.api_url}/logs/ingest",
                json=log_entry,
                timeout=5
            )
            if response.status_code == 200:
                print(f"✓ Sent {log_entry['level'] if 'level' in log_entry else 'ACCESS'} log")
            else:
                print(f"✗ Failed to send log: {response.status_code}")
        except Exception as e:
            print(f"✗ Error sending log: {e}")
    
    def generate_continuous_logs(self, interval=1):
        """Generate logs continuously"""
        print(f"Starting continuous log generation (interval: {interval}s)")
        
        while True:
            try:
                # Generate application log
                if random.random() < 0.7:  # 70% application logs
                    log = self.generate_application_log()
                else:  # 30% access logs
                    log = self.generate_access_log()
                
                self.send_log(log)
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\nStopping log generation...")
                break
            except Exception as e:
                print(f"Error in log generation: {e}")
                time.sleep(interval)
    
    def generate_burst_logs(self, count=100):
        """Generate a burst of logs"""
        print(f"Generating {count} logs...")
        
        for i in range(count):
            log = self.generate_application_log() if random.random() < 0.8 else self.generate_access_log()
            self.send_log(log)
            
            if i % 10 == 0:
                print(f"Generated {i}/{count} logs")
        
        print(f"Completed generating {count} logs")

if __name__ == "__main__":
    generator = LogGenerator()
    
    # Generate initial burst of logs
    generator.generate_burst_logs(50)
    
    # Start continuous generation
    generator.generate_continuous_logs(interval=0.5)
```

## 📈 Kibana Dashboards

### 1. Dashboard Configuration

**Create Index Pattern:**
```bash
curl -X POST "localhost:5601/api/saved_objects/index-pattern/logs-*" \
  -H 'Content-Type: application/json' \
  -H 'kbn-xsrf: true' \
  -d '{
    "attributes": {
      "title": "logs-*",
      "timeFieldName": "@timestamp"
    }
  }'
```

**Dashboard JSON Export:**
```json
{
  "version": "8.11.0",
  "objects": [
    {
      "id": "log-analytics-dashboard",
      "type": "dashboard",
      "attributes": {
        "title": "Log Analytics Dashboard",
        "description": "Comprehensive log monitoring and analysis",
        "panelsJSON": "[{\"version\":\"8.11.0\",\"gridData\":{\"x\":0,\"y\":0,\"w\":24,\"h\":15},\"panelIndex\":\"1\",\"embeddableConfig\":{},\"panelRefName\":\"panel_1\"}]",
        "version": 1,
        "timeRestore": false,
        "kibanaSavedObjectMeta": {
          "searchSourceJSON": "{\"query\":{\"query\":\"\",\"language\":\"kuery\"},\"filter\":[]}"
        }
      }
    }
  ]
}
```

### 2. Key Visualizations

**Error Rate Over Time:**
```json
{
  "title": "Error Rate Timeline",
  "visState": {
    "title": "Error Rate Timeline",
    "type": "line",
    "params": {
      "grid": {"categoryLines": false, "style": {"color": "#eee"}},
      "categoryAxes": [{"id": "CategoryAxis-1", "type": "category", "position": "bottom"}],
      "valueAxes": [{"id": "ValueAxis-1", "name": "LeftAxis-1", "type": "value", "position": "left"}],
      "seriesParams": [{"show": true, "type": "line", "mode": "normal", "data": {"label": "Error Count", "id": "1"}}]
    },
    "aggs": [
      {"id": "1", "enabled": true, "type": "count", "schema": "metric", "params": {}},
      {"id": "2", "enabled": true, "type": "date_histogram", "schema": "segment", "params": {"field": "@timestamp", "interval": "auto"}}
    ]
  }
}
```

**Service Health Matrix:**
```json
{
  "title": "Service Health Matrix",
  "visState": {
    "title": "Service Health Matrix",
    "type": "heatmap",
    "params": {
      "addTooltip": true,
      "addLegend": true,
      "enableHover": false,
      "legendPosition": "right",
      "times": [],
      "colorsNumber": 4,
      "colorSchema": "Reds",
      "setColorRange": false,
      "colorsRange": [],
      "invertColors": false,
      "percentageMode": false,
      "valueAxes": [{"show": false, "id": "ValueAxis-1", "type": "value", "scale": {"type": "linear", "defaultYExtents": false}, "labels": {"show": false, "rotate": 0, "color": "#555"}}]
    },
    "aggs": [
      {"id": "1", "enabled": true, "type": "count", "schema": "metric", "params": {}},
      {"id": "2", "enabled": true, "type": "terms", "schema": "segment", "params": {"field": "service", "size": 10}},
      {"id": "3", "enabled": true, "type": "terms", "schema": "group", "params": {"field": "level", "size": 5}}
    ]
  }
}
```

## 🚨 Alerting System

### Watcher Alerts

**High Error Rate Alert:**
```bash
curl -X PUT "localhost:9200/_watcher/watch/high_error_rate" -H 'Content-Type: application/json' -d'
{
  "trigger": {
    "schedule": {
      "interval": "1m"
    }
  },
  "input": {
    "search": {
      "request": {
        "search_type": "query_then_fetch",
        "indices": ["logs-*"],
        "body": {
          "query": {
            "bool": {
              "filter": [
                {"range": {"@timestamp": {"gte": "now-5m"}}},
                {"terms": {"level": ["ERROR", "FATAL"]}}
              ]
            }
          },
          "aggs": {
            "error_count": {
              "cardinality": {
                "field": "_id"
              }
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.aggregations.error_count.value": {
        "gt": 10
      }
    }
  },
  "actions": {
    "send_email": {
      "email": {
        "to": ["devops@company.com"],
        "subject": "High Error Rate Alert",
        "body": "High error rate detected: {{ctx.payload.aggregations.error_count.value}} errors in the last 5 minutes"
      }
    },
    "slack_notification": {
      "webhook": {
        "scheme": "https",
        "host": "hooks.slack.com",
        "port": 443,
        "method": "post",
        "path": "/services/YOUR/SLACK/WEBHOOK",
        "params": {},
        "headers": {
          "Content-Type": "application/json"
        },
        "body": "{\"text\": \"🚨 High error rate: {{ctx.payload.aggregations.error_count.value}} errors in 5 minutes\"}"
      }
    }
  }
}
'
```

**Service Down Alert:**
```bash
curl -X PUT "localhost:9200/_watcher/watch/service_down" -H 'Content-Type: application/json' -d'
{
  "trigger": {
    "schedule": {
      "interval": "5m"
    }
  },
  "input": {
    "search": {
      "request": {
        "indices": ["logs-*"],
        "body": {
          "query": {
            "bool": {
              "filter": [
                {"range": {"@timestamp": {"gte": "now-10m"}}},
                {"term": {"service": "critical-service"}}
              ]
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.hits.total": {
        "eq": 0
      }
    }
  },
  "actions": {
    "notify_oncall": {
      "email": {
        "to": ["oncall@company.com"],
        "subject": "Service Down Alert - critical-service",
        "body": "No logs received from critical-service in the last 10 minutes. Service may be down."
      }
    }
  }
}
'
```

## 🔧 Performance Optimization

### Index Optimization

```bash
# Force merge old indices
curl -X POST "localhost:9200/logs-2024.01.*/_forcemerge?max_num_segments=1"

# Update refresh interval for hot indices
curl -X PUT "localhost:9200/logs-$(date +%Y.%m.%d)/_settings" -H 'Content-Type: application/json' -d'
{
  "refresh_interval": "5s"
}
'

# Optimize mapping for log fields
curl -X PUT "localhost:9200/_template/logs_optimized" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["logs-*"],
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "codec": "best_compression"
  },
  "mappings": {
    "properties": {
      "message": {
        "type": "text",
        "norms": false,
        "index_options": "freqs"
      },
      "log_message": {
        "type": "text", 
        "norms": false,
        "index_options": "freqs"
      }
    }
  }
}
'
```

## 📊 Monitoring and Maintenance

### Health Check Script

```bash
#!/bin/bash

ES_HOST="localhost:9200"
KIBANA_HOST="localhost:5601"

echo "=== Log Analytics Health Check ==="

# Check Elasticsearch cluster health
echo "1. Elasticsearch Cluster Health:"
CLUSTER_STATUS=$(curl -s "$ES_HOST/_cluster/health" | jq -r '.status')
echo "   Status: $CLUSTER_STATUS"

# Check log indices
echo "2. Log Indices:"
curl -s "$ES_HOST/_cat/indices/logs-*?v&h=health,status,index,docs.count,store.size" | head -10

# Check ingestion rate
echo "3. Recent Ingestion Rate:"
RECENT_LOGS=$(curl -s "$ES_HOST/logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"range": {"@timestamp": {"gte": "now-1m"}}},
  "size": 0
}' | jq '.hits.total.value')
echo "   Logs in last minute: $RECENT_LOGS"

# Check error rate
echo "4. Current Error Rate:"
ERROR_LOGS=$(curl -s "$ES_HOST/logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"range": {"@timestamp": {"gte": "now-5m"}}},
        {"terms": {"level": ["ERROR", "FATAL"]}}
      ]
    }
  },
  "size": 0
}' | jq '.hits.total.value')
echo "   Errors in last 5 minutes: $ERROR_LOGS"

# Check Kibana
echo "5. Kibana Status:"
KIBANA_STATUS=$(curl -s "$KIBANA_HOST/api/status" | jq -r '.status.overall.state' 2>/dev/null || echo "unreachable")
echo "   Status: $KIBANA_STATUS"

echo "=== Health Check Complete ==="
```

## 🚀 Deployment and Scaling

### Production Considerations

1. **Security Configuration:**
```yaml
# elasticsearch.yml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true
```

2. **Performance Tuning:**
```yaml
# elasticsearch.yml
bootstrap.memory_lock: true
indices.memory.index_buffer_size: 30%
indices.memory.min_index_buffer_size: 96mb
thread_pool.write.queue_size: 1000
```

3. **Monitoring Integration:**
```yaml
# metricbeat.yml
metricbeat.modules:
- module: elasticsearch
  metricsets: ["node", "node_stats", "cluster_stats"]
  period: 10s
  hosts: ["localhost:9200"]

- module: logstash
  metricsets: ["node", "node_stats"]
  period: 10s
  hosts: ["localhost:9600"]
```

## 📚 Next Steps

1. **Advanced Analytics** - Implement machine learning for anomaly detection
2. **Cross-Cluster Search** - Set up multi-datacenter log aggregation
3. **Custom Plugins** - Develop domain-specific log processors
4. **Integration** - Connect with SIEM and monitoring tools
5. **Compliance** - Implement log retention and compliance features

## 🔗 Related Examples

- **[Real-time Analytics](realtime-analytics.md)** - Build live analytics dashboards
- **[Security Analytics](security-analytics.md)** - SIEM and threat detection
- **[Performance Monitoring](performance-monitoring.md)** - APM and system monitoring

This log analytics implementation provides a complete foundation for centralized logging, real-time monitoring, and operational intelligence with Elasticsearch!