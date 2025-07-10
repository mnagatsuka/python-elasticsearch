# Index Management

**Master advanced index lifecycle management, optimization, and maintenance strategies**

*Estimated reading time: 35 minutes*

## Overview

Effective index management is crucial for maintaining optimal performance and controlling storage costs in production Elasticsearch clusters. This guide covers index lifecycle management (ILM), index templates, rollover strategies, and advanced optimization techniques.

## 📋 Table of Contents

1. [Index Lifecycle Management](#index-lifecycle-management)
2. [Index Templates](#index-templates)
3. [Rollover Strategies](#rollover-strategies)
4. [Index Optimization](#index-optimization)
5. [Data Tiers](#data-tiers)
6. [Maintenance Operations](#maintenance-operations)
7. [Best Practices](#best-practices)

## 🔄 Index Lifecycle Management

### ILM Overview

Index Lifecycle Management (ILM) automates index management through predefined phases:
- **Hot**: Active indexing and searching
- **Warm**: Reduced indexing, continued searching
- **Cold**: Infrequent searching, compressed storage
- **Frozen**: Very infrequent access, minimal resources
- **Delete**: Removal from cluster

### Basic ILM Policy

**Create ILM Policy:**
```bash
curl -X PUT "localhost:9200/_ilm/policy/logs_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "50gb",
            "max_age": "7d",
            "max_docs": 100000000
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "7d",
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
        "min_age": "30d",
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
        "min_age": "90d"
      }
    }
  }
}
'
```

### Advanced ILM Configuration

**Complex ILM Policy:**
```bash
curl -X PUT "localhost:9200/_ilm/policy/advanced_logs_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "30gb",
            "max_age": "1d"
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
            "number_of_replicas": 0,
            "include": {
              "_tier_preference": "data_warm"
            }
          },
          "forcemerge": {
            "max_num_segments": 1
          },
          "shrink": {
            "number_of_shards": 1
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
      "frozen": {
        "min_age": "30d",
        "actions": {
          "freeze": {}
        }
      },
      "delete": {
        "min_age": "365d"
      }
    }
  }
}
'
```

### ILM Policy Management

**Apply Policy to Index:**
```bash
curl -X PUT "localhost:9200/logs-000001/_settings" -H 'Content-Type: application/json' -d'
{
  "index.lifecycle.name": "logs_policy",
  "index.lifecycle.rollover_alias": "logs"
}
'
```

**Check ILM Status:**
```bash
curl -X GET "localhost:9200/_ilm/status"
curl -X GET "localhost:9200/logs-*/_ilm/explain"
```

**Start/Stop ILM:**
```bash
# Stop ILM
curl -X POST "localhost:9200/_ilm/stop"

# Start ILM
curl -X POST "localhost:9200/_ilm/start"
```

## 📋 Index Templates

### Composable Index Templates

**Create Index Template:**
```bash
curl -X PUT "localhost:9200/_index_template/logs_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["logs-*"],
  "priority": 200,
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs_policy",
      "index.lifecycle.rollover_alias": "logs",
      "index.refresh_interval": "30s",
      "index.codec": "best_compression"
    },
    "mappings": {
      "properties": {
        "@timestamp": {
          "type": "date",
          "format": "epoch_millis||strict_date_optional_time"
        },
        "level": {
          "type": "keyword"
        },
        "message": {
          "type": "text",
          "norms": false
        },
        "service": {
          "type": "keyword"
        },
        "host": {
          "type": "keyword"
        }
      }
    }
  },
  "composed_of": ["logs_component_template"],
  "version": 1,
  "meta": {
    "description": "Template for application logs"
  }
}
'
```

### Component Templates

**Create Component Template:**
```bash
curl -X PUT "localhost:9200/_component_template/logs_component_template" -H 'Content-Type: application/json' -d'
{
  "template": {
    "settings": {
      "index.mapping.total_fields.limit": 1000,
      "index.refresh_interval": "30s"
    },
    "mappings": {
      "properties": {
        "labels": {
          "type": "object",
          "dynamic": true
        },
        "tags": {
          "type": "keyword"
        }
      }
    }
  },
  "version": 1,
  "meta": {
    "description": "Common settings for log indices"
  }
}
'
```

### Dynamic Templates

**Dynamic Field Mapping:**
```bash
curl -X PUT "localhost:9200/_index_template/metrics_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["metrics-*"],
  "template": {
    "mappings": {
      "dynamic_templates": [
        {
          "strings_as_keywords": {
            "match_mapping_type": "string",
            "match": "*_id",
            "mapping": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        {
          "longs_as_floats": {
            "match_mapping_type": "long",
            "mapping": {
              "type": "float"
            }
          }
        },
        {
          "date_fields": {
            "match": "*_time",
            "mapping": {
              "type": "date",
              "format": "epoch_millis"
            }
          }
        }
      ]
    }
  }
}
'
```

## 🔄 Rollover Strategies

### Alias-based Rollover

**Setup Rollover Alias:**
```bash
# Create initial index
curl -X PUT "localhost:9200/logs-000001" -H 'Content-Type: application/json' -d'
{
  "aliases": {
    "logs": {
      "is_write_index": true
    }
  }
}
'

# Manual rollover
curl -X POST "localhost:9200/logs/_rollover" -H 'Content-Type: application/json' -d'
{
  "conditions": {
    "max_age": "7d",
    "max_size": "50gb",
    "max_docs": 100000000
  }
}
'
```

### Automatic Rollover

**ILM-based Rollover:**
```bash
curl -X PUT "localhost:9200/_ilm/policy/auto_rollover_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "30gb",
            "max_age": "1d",
            "max_docs": 50000000
          }
        }
      }
    }
  }
}
'
```

### Time-based Rollover

**Daily Indices:**
```bash
curl -X PUT "localhost:9200/_index_template/daily_logs_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "index.lifecycle.name": "daily_logs_policy"
    }
  }
}
'

curl -X PUT "localhost:9200/_ilm/policy/daily_logs_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_age": "1d"
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

## ⚡ Index Optimization

### Force Merge

**Optimize Segments:**
```bash
# Force merge to single segment
curl -X POST "localhost:9200/logs-2024-01/_forcemerge?max_num_segments=1"

# Force merge with wait for completion
curl -X POST "localhost:9200/logs-*/_forcemerge?max_num_segments=1&wait_for_completion=true"

# Only merge deletes
curl -X POST "localhost:9200/logs-*/_forcemerge?only_expunge_deletes=true"
```

### Shrink Operations

**Shrink Index:**
```bash
# Step 1: Prepare index for shrinking
curl -X PUT "localhost:9200/source_index/_settings" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.routing.allocation.require._name": "specific_node_name",
    "index.blocks.write": true
  }
}
'

# Step 2: Shrink the index
curl -X POST "localhost:9200/source_index/_shrink/target_index" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.number_of_replicas": 1,
    "index.number_of_shards": 1,
    "index.codec": "best_compression"
  }
}
'
```

### Split Operations

**Split Index:**
```bash
# Prepare index for splitting
curl -X PUT "localhost:9200/source_index/_settings" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.blocks.write": true
  }
}
'

# Split the index
curl -X POST "localhost:9200/source_index/_split/target_index" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "index.number_of_shards": 4
  }
}
'
```

### Reindex Operations

**Basic Reindex:**
```bash
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "old_index"
  },
  "dest": {
    "index": "new_index"
  }
}
'
```

**Reindex with Transformation:**
```bash
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "old_index",
    "query": {
      "range": {
        "@timestamp": {
          "gte": "2024-01-01"
        }
      }
    }
  },
  "dest": {
    "index": "new_index"
  },
  "script": {
    "source": "ctx._source.new_field = ctx._source.old_field * 2"
  }
}
'
```

## 🏢 Data Tiers

### Tier Configuration

**Configure Data Tiers:**
```yaml
# Hot tier nodes
node.roles: [data_hot, data_content]
node.attr.data: hot

# Warm tier nodes  
node.roles: [data_warm, data_content]
node.attr.data: warm

# Cold tier nodes
node.roles: [data_cold, data_content]
node.attr.data: cold
```

### Tier Allocation

**Move Index Between Tiers:**
```bash
# Move to warm tier
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.routing.allocation.include._tier_preference": "data_warm"
}
'

# Move to cold tier
curl -X PUT "localhost:9200/my_index/_settings" -H 'Content-Type: application/json' -d'
{
  "index.routing.allocation.include._tier_preference": "data_cold"
}
'
```

### Automatic Tier Migration

**ILM Tier Migration:**
```bash
curl -X PUT "localhost:9200/_ilm/policy/tier_migration_policy" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_age": "1d",
            "max_size": "50gb"
          }
        }
      },
      "warm": {
        "min_age": "3d",
        "actions": {
          "allocate": {
            "include": {
              "_tier_preference": "data_warm"
            },
            "number_of_replicas": 0
          },
          "forcemerge": {
            "max_num_segments": 1
          }
        }
      },
      "cold": {
        "min_age": "14d",
        "actions": {
          "allocate": {
            "include": {
              "_tier_preference": "data_cold"
            }
          }
        }
      }
    }
  }
}
'
```

## 🔧 Maintenance Operations

### Index Health Monitoring

**Check Index Health:**
```bash
# Index health overview
curl -X GET "localhost:9200/_cat/indices?v&h=health,status,index,pri,rep,docs.count,store.size"

# Detailed index stats
curl -X GET "localhost:9200/_stats?level=indices&pretty"

# Shard allocation
curl -X GET "localhost:9200/_cat/shards?v&h=index,shard,prirep,state,unassigned.reason"
```

### Index Recovery

**Monitor Recovery:**
```bash
curl -X GET "localhost:9200/_cat/recovery?v&h=index,stage,time,source_node,target_node,bytes_percent"
```

**Control Recovery Speed:**
```bash
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "transient": {
    "indices.recovery.max_bytes_per_sec": "100mb",
    "cluster.routing.allocation.node_concurrent_recoveries": 4
  }
}
'
```

### Disk Space Management

**Disk-based Allocation:**
```bash
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d'
{
  "persistent": {
    "cluster.routing.allocation.disk.threshold_enabled": true,
    "cluster.routing.allocation.disk.watermark.low": "85%",
    "cluster.routing.allocation.disk.watermark.high": "90%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "95%"
  }
}
'
```

### Index Cleanup

**Cleanup Script:**
```bash
#!/bin/bash

ES_HOST="localhost:9200"
RETENTION_DAYS=30

echo "=== Index Cleanup Script ==="
echo "Retention period: $RETENTION_DAYS days"

# Get indices older than retention period
OLD_INDICES=$(curl -s "$ES_HOST/_cat/indices?h=index,creation.date.string" | \
    awk -v cutoff="$(date -d "$RETENTION_DAYS days ago" '+%Y-%m-%d')" \
    '$2 < cutoff && $1 ~ /^logs-/ {print $1}')

if [ -z "$OLD_INDICES" ]; then
    echo "No indices to clean up."
    exit 0
fi

echo "Indices to delete:"
echo "$OLD_INDICES"

# Confirm deletion
read -p "Proceed with deletion? (y/N): " confirm
if [[ $confirm == [yY] ]]; then
    for index in $OLD_INDICES; do
        echo "Deleting index: $index"
        curl -X DELETE "$ES_HOST/$index"
    done
    echo "Cleanup complete."
else
    echo "Cleanup cancelled."
fi
```

## 📝 Best Practices

### Index Naming Conventions

**Recommended Patterns:**
```bash
# Time-based indices
logs-2024.01.01
metrics-2024-01-01
events-2024.01.01-000001

# Application-based indices
app-logs-prod-2024.01.01
user-events-staging-2024.01.01
system-metrics-dev-2024.01.01
```

### Performance Optimization

**Index Settings:**
```bash
curl -X PUT "localhost:9200/optimized_index" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "refresh_interval": "30s",
    "index.codec": "best_compression",
    "index.mapping.total_fields.limit": 1000,
    "index.max_result_window": 100000,
    "index.translog.durability": "async",
    "index.translog.sync_interval": "30s"
  }
}
'
```

### Security Considerations

**Index-level Security:**
```bash
# Set index permissions
curl -X POST "localhost:9200/_security/role/logs_reader" -H 'Content-Type: application/json' -d'
{
  "indices": [
    {
      "names": ["logs-*"],
      "privileges": ["read", "view_index_metadata"]
    }
  ]
}
'
```

### Monitoring Index Management

**ILM Monitoring:**
```bash
# Monitor ILM execution
curl -X GET "localhost:9200/_ilm/explain"

# Check policy execution
curl -X GET "localhost:9200/logs-*/_ilm/explain?only_managed=true&only_errors=true"
```

### Automation Scripts

**Index Management Automation:**
```python
#!/usr/bin/env python3

import requests
import json
from datetime import datetime, timedelta

class IndexManager:
    def __init__(self, es_host='localhost:9200'):
        self.es_host = es_host
        self.base_url = f'http://{es_host}'
    
    def get_indices(self, pattern='*'):
        response = requests.get(f'{self.base_url}/_cat/indices/{pattern}?format=json')
        return response.json()
    
    def delete_old_indices(self, pattern, retention_days):
        indices = self.get_indices(pattern)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        deleted = []
        for index in indices:
            index_name = index['index']
            creation_date = datetime.fromtimestamp(int(index['creation.date']) / 1000)
            
            if creation_date < cutoff_date:
                print(f"Deleting old index: {index_name}")
                response = requests.delete(f'{self.base_url}/{index_name}')
                if response.status_code == 200:
                    deleted.append(index_name)
                    
        return deleted
    
    def optimize_indices(self, pattern, max_segments=1):
        indices = self.get_indices(pattern)
        
        for index in indices:
            index_name = index['index']
            if index['status'] == 'open':
                print(f"Force merging index: {index_name}")
                requests.post(f'{self.base_url}/{index_name}/_forcemerge?max_num_segments={max_segments}')
    
    def check_shard_allocation(self):
        response = requests.get(f'{self.base_url}/_cat/shards?format=json')
        shards = response.json()
        
        issues = []
        for shard in shards:
            if shard['state'] == 'UNASSIGNED':
                issues.append(f"Unassigned shard: {shard['index']} shard {shard['shard']}")
                
        return issues

if __name__ == "__main__":
    manager = IndexManager()
    
    # Delete old log indices
    deleted = manager.delete_old_indices('logs-*', retention_days=30)
    print(f"Deleted {len(deleted)} old indices")
    
    # Optimize old indices
    manager.optimize_indices('logs-*')
    
    # Check for shard issues
    issues = manager.check_shard_allocation()
    if issues:
        print("Shard allocation issues:")
        for issue in issues:
            print(f"  - {issue}")
```

## 🔗 Next Steps

Now that you've mastered index management, let's explore troubleshooting:

1. **[Troubleshooting](troubleshooting.md)** - Diagnose and resolve common issues
2. **[Security & Authentication](security-authentication.md)** - Secure your cluster
3. **[Performance Tuning](../examples/performance-tuning.md)** - Real-world optimization examples

## 📚 Key Takeaways

- ✅ **Implement ILM policies** for automated index lifecycle management
- ✅ **Use index templates** for consistent configuration across indices
- ✅ **Plan rollover strategies** based on size, age, and document count
- ✅ **Optimize indices** with force merge and compression
- ✅ **Leverage data tiers** for cost-effective storage
- ✅ **Monitor index health** continuously
- ✅ **Automate maintenance tasks** with scripts and policies
- ✅ **Follow naming conventions** for better organization
- ✅ **Implement proper cleanup** to manage disk space
- ✅ **Test ILM policies** in non-production environments first

Ready to learn troubleshooting techniques? Continue with [Troubleshooting](troubleshooting.md) to master issue diagnosis and resolution!