# Basic API Interactions

**Learn essential Elasticsearch commands through hands-on practice**

*Estimated reading time: 25 minutes*

## Overview

This guide provides hands-on experience with Elasticsearch's RESTful API. You'll learn the fundamental operations that form the building blocks of all Elasticsearch interactions.

## 🚀 Prerequisites

Before starting, ensure you have:
- Elasticsearch running (see [Installation & Setup](installation-setup.md))
- Access to command line (Terminal/Command Prompt)
- Basic understanding of HTTP methods (GET, POST, PUT, DELETE)

## 📋 Table of Contents

1. [Cluster Information](#cluster-information)
2. [Index Operations](#index-operations)
3. [Document Operations](#document-operations)
4. [Search Operations](#search-operations)
5. [Practical Examples](#practical-examples)
6. [Common Patterns](#common-patterns)

## 🔍 Cluster Information

### Check Cluster Health

```bash
# Basic cluster info
curl http://localhost:9200

# Detailed cluster health
curl http://localhost:9200/_cluster/health?pretty

# Cluster stats
curl http://localhost:9200/_cluster/stats?pretty
```

**Example Response:**
```json
{
  "cluster_name" : "elasticsearch",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 1,
  "number_of_data_nodes" : 1,
  "active_primary_shards" : 0,
  "active_shards" : 0,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0
}
```

### Node Information

```bash
# List all nodes
curl http://localhost:9200/_nodes?pretty

# Node stats
curl http://localhost:9200/_nodes/stats?pretty

# Compact node info
curl http://localhost:9200/_cat/nodes?v
```

## 📚 Index Operations

### Create Index

```bash
# Create a simple index
curl -X PUT "localhost:9200/my-first-index"

# Create index with settings
curl -X PUT "localhost:9200/blog" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1
  }
}
'
```

### List Indices

```bash
# List all indices
curl http://localhost:9200/_cat/indices?v

# Get specific index info
curl http://localhost:9200/blog?pretty

# Check if index exists
curl -I http://localhost:9200/blog
```

**Example Response:**
```
health status index uuid                   pri rep docs.count docs.deleted store.size pri.store.size
yellow open   blog  5fAOtEGTQg6wMaVvnZ4dxw   1   1          0            0       260b           260b
```

### Delete Index

```bash
# Delete an index
curl -X DELETE "localhost:9200/my-first-index"

# Delete multiple indices
curl -X DELETE "localhost:9200/index1,index2"

# Delete with pattern (be careful!)
curl -X DELETE "localhost:9200/test-*"
```

## 📄 Document Operations

### Create Documents

**With Auto-generated ID:**
```bash
curl -X POST "localhost:9200/blog/_doc/" -H 'Content-Type: application/json' -d'
{
  "title": "My First Blog Post",
  "author": "John Doe",
  "content": "This is my first blog post about Elasticsearch!",
  "tags": ["elasticsearch", "tutorial"],
  "published_date": "2024-01-15T10:30:00Z"
}
'
```

**With Specific ID:**
```bash
curl -X PUT "localhost:9200/blog/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Getting Started with Elasticsearch",
  "author": "Jane Smith",
  "content": "Elasticsearch is a powerful search engine that can help you find information quickly.",
  "tags": ["elasticsearch", "beginners"],
  "published_date": "2024-01-10T09:00:00Z",
  "view_count": 0
}
'
```

### Read Documents

```bash
# Get document by ID
curl http://localhost:9200/blog/_doc/1?pretty

# Get only source
curl http://localhost:9200/blog/_doc/1/_source?pretty

# Get specific fields
curl "http://localhost:9200/blog/_doc/1?_source=title,author&pretty"
```

**Example Response:**
```json
{
  "_index" : "blog",
  "_id" : "1",
  "_version" : 1,
  "_seq_no" : 0,
  "_primary_term" : 1,
  "found" : true,
  "_source" : {
    "title" : "Getting Started with Elasticsearch",
    "author" : "Jane Smith",
    "content" : "Elasticsearch is a powerful search engine...",
    "tags" : ["elasticsearch", "beginners"],
    "published_date" : "2024-01-10T09:00:00Z",
    "view_count" : 0
  }
}
```

### Update Documents

**Partial Update:**
```bash
curl -X POST "localhost:9200/blog/_update/1" -H 'Content-Type: application/json' -d'
{
  "doc": {
    "view_count": 100,
    "last_updated": "2024-01-16T14:30:00Z"
  }
}
'
```

**Script Update:**
```bash
curl -X POST "localhost:9200/blog/_update/1" -H 'Content-Type: application/json' -d'
{
  "script": {
    "source": "ctx._source.view_count += params.increment",
    "params": {
      "increment": 1
    }
  }
}
'
```

**Upsert (Update or Insert):**
```bash
curl -X POST "localhost:9200/blog/_update/2" -H 'Content-Type: application/json' -d'
{
  "doc": {
    "title": "Advanced Elasticsearch",
    "author": "Bob Wilson"
  },
  "upsert": {
    "title": "Advanced Elasticsearch",
    "author": "Bob Wilson",
    "content": "Advanced concepts in Elasticsearch",
    "tags": ["elasticsearch", "advanced"],
    "published_date": "2024-01-16T15:00:00Z",
    "view_count": 0
  }
}
'
```

### Delete Documents

```bash
# Delete by ID
curl -X DELETE "localhost:9200/blog/_doc/1"

# Delete by query
curl -X POST "localhost:9200/blog/_delete_by_query" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "author": "John Doe"
    }
  }
}
'
```

## 🔍 Search Operations

### Basic Search

```bash
# Search all documents
curl http://localhost:9200/blog/_search?pretty

# Search with query parameter
curl "http://localhost:9200/blog/_search?q=elasticsearch&pretty"

# Search across multiple indices
curl "http://localhost:9200/blog,news/_search?pretty"
```

### Query DSL Search

**Match Query:**
```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}
'
```

**Multi-field Search:**
```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch tutorial",
      "fields": ["title", "content"]
    }
  }
}
'
```

**Boolean Query:**
```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"title": "elasticsearch"}}
      ],
      "filter": [
        {"term": {"author.keyword": "Jane Smith"}}
      ]
    }
  }
}
'
```

### Search with Filters and Sorting

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_all": {}
  },
  "sort": [
    {"published_date": {"order": "desc"}},
    {"view_count": {"order": "desc"}}
  ],
  "from": 0,
  "size": 10
}
'
```

## 🛠️ Practical Examples

### Example 1: Building a Product Catalog

```bash
# Create products index
curl -X PUT "localhost:9200/products" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "name": {"type": "text"},
      "category": {"type": "keyword"},
      "price": {"type": "float"},
      "description": {"type": "text"},
      "in_stock": {"type": "boolean"},
      "created_at": {"type": "date"}
    }
  }
}
'

# Add products
curl -X POST "localhost:9200/products/_doc/" -H 'Content-Type: application/json' -d'
{
  "name": "Wireless Headphones",
  "category": "electronics",
  "price": 99.99,
  "description": "High-quality wireless headphones with noise cancellation",
  "in_stock": true,
  "created_at": "2024-01-15T10:00:00Z"
}
'

curl -X POST "localhost:9200/products/_doc/" -H 'Content-Type: application/json' -d'
{
  "name": "Running Shoes",
  "category": "sports",
  "price": 129.99,
  "description": "Comfortable running shoes for daily exercise",
  "in_stock": true,
  "created_at": "2024-01-14T15:30:00Z"
}
'

# Search products
curl -X GET "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"description": "comfortable"}}
      ],
      "filter": [
        {"term": {"in_stock": true}},
        {"range": {"price": {"lte": 150}}}
      ]
    }
  },
  "sort": [{"price": {"order": "asc"}}]
}
'
```

### Example 2: Log Analysis

```bash
# Create logs index
curl -X PUT "localhost:9200/app-logs" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "timestamp": {"type": "date"},
      "level": {"type": "keyword"},
      "message": {"type": "text"},
      "service": {"type": "keyword"},
      "user_id": {"type": "keyword"}
    }
  }
}
'

# Add log entries
curl -X POST "localhost:9200/app-logs/_doc/" -H 'Content-Type: application/json' -d'
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "ERROR",
  "message": "Database connection failed",
  "service": "user-service",
  "user_id": "user123"
}
'

curl -X POST "localhost:9200/app-logs/_doc/" -H 'Content-Type: application/json' -d'
{
  "timestamp": "2024-01-15T10:31:00Z",
  "level": "INFO",
  "message": "User logged in successfully",
  "service": "auth-service",
  "user_id": "user456"
}
'

# Search for errors
curl -X GET "localhost:9200/app-logs/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}}
      ],
      "filter": [
        {
          "range": {
            "timestamp": {
              "gte": "2024-01-15T00:00:00Z",
              "lte": "2024-01-15T23:59:59Z"
            }
          }
        }
      ]
    }
  }
}
'
```

## 📊 Bulk Operations

### Bulk Index

```bash
curl -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' -d'
{"index": {"_index": "blog", "_id": "3"}}
{"title": "Elasticsearch Bulk Operations", "author": "Mike Johnson", "content": "Learn how to use bulk operations efficiently"}
{"index": {"_index": "blog", "_id": "4"}}
{"title": "Advanced Search Techniques", "author": "Sarah Davis", "content": "Master advanced search capabilities"}
{"update": {"_index": "blog", "_id": "1"}}
{"doc": {"view_count": 150}}
{"delete": {"_index": "blog", "_id": "2"}}
'
```

### Bulk from File

```bash
# Create bulk_data.json
cat > bulk_data.json << 'EOF'
{"index": {"_index": "products", "_id": "1"}}
{"name": "Laptop", "category": "electronics", "price": 999.99}
{"index": {"_index": "products", "_id": "2"}}
{"name": "Mouse", "category": "electronics", "price": 25.50}
EOF

# Execute bulk operation
curl -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' --data-binary @bulk_data.json
```

## 🔍 Common Patterns

### Health Check Pattern

```bash
# Simple health check
health_check() {
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9200)
  if [ $response -eq 200 ]; then
    echo "Elasticsearch is healthy"
  else
    echo "Elasticsearch is not responding"
  fi
}

health_check
```

### Index Existence Check

```bash
# Check if index exists
index_exists() {
  local index=$1
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9200/$index)
  if [ $response -eq 200 ]; then
    echo "Index $index exists"
    return 0
  else
    echo "Index $index does not exist"
    return 1
  fi
}

index_exists "blog"
```

### Document Count

```bash
# Count documents in index
curl "http://localhost:9200/blog/_count?pretty"

# Count with query
curl -X GET "localhost:9200/blog/_count" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "author": "Jane Smith"
    }
  }
}
'
```

## 🐛 Debugging and Troubleshooting

### Explain API

```bash
# Explain why a document matches
curl -X GET "localhost:9200/blog/_explain/1" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}
'
```

### Validate Query

```bash
# Validate query without executing
curl -X GET "localhost:9200/blog/_validate/query?explain" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}
'
```

### Profile API

```bash
# Profile query performance
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "profile": true,
  "query": {
    "match": {
      "title": "elasticsearch"
    }
  }
}
'
```

## 🔧 Useful Commands Reference

### Quick Commands

```bash
# Cluster health
curl http://localhost:9200/_cluster/health

# List indices
curl http://localhost:9200/_cat/indices?v

# List shards
curl http://localhost:9200/_cat/shards?v

# Node info
curl http://localhost:9200/_cat/nodes?v

# Pending tasks
curl http://localhost:9200/_cat/pending_tasks?v

# Thread pool stats
curl http://localhost:9200/_cat/thread_pool?v
```

### JSON Pretty Printing

```bash
# Using jq for better formatting
curl -s http://localhost:9200/blog/_search | jq '.'

# Using Python for formatting
curl -s http://localhost:9200/blog/_search | python -m json.tool
```

## ⚠️ Best Practices

### DO's

```bash
# ✅ Use meaningful index names
curl -X PUT "localhost:9200/user-profiles-2024"

# ✅ Include Content-Type header
curl -X POST "localhost:9200/blog/_doc/" -H 'Content-Type: application/json' -d'...'

# ✅ Use bulk operations for multiple documents
curl -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' -d'...'

# ✅ Check response status codes
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9200)
```

### DON'Ts

```bash
# ❌ Don't use DELETE without specific index
# curl -X DELETE "localhost:9200/*"  # This deletes EVERYTHING!

# ❌ Don't skip Content-Type header for JSON
# curl -X POST "localhost:9200/blog/_doc/" -d'{"title": "test"}'

# ❌ Don't use synchronous operations for large datasets
# for i in {1..1000}; do curl -X POST ...; done  # Use bulk instead
```

## 🔗 Next Steps

Now that you've mastered the basics, let's explore more advanced topics:

1. **[Document Operations](../02-data-management/document-operations.md)** - Deep dive into CRUD operations
2. **[Mapping & Field Types](../02-data-management/mapping-field-types.md)** - Learn about data schemas
3. **[Query DSL Basics](../03-search-fundamentals/query-dsl-basics.md)** - Master Elasticsearch queries

## 📚 Key Takeaways

- ✅ **Elasticsearch uses REST API** with standard HTTP methods
- ✅ **Always include Content-Type header** for JSON requests
- ✅ **Use bulk operations** for multiple documents
- ✅ **Check cluster health** regularly
- ✅ **Pretty print responses** for better readability
- ✅ **Use meaningful index names** and IDs
- ✅ **Validate queries** before running in production
- ✅ **Profile queries** to understand performance

Ready to dive deeper? Continue with [Document Operations](../02-data-management/document-operations.md) to learn advanced CRUD operations!