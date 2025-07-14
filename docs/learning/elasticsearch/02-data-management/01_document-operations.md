# Document Operations

**Master CRUD operations and bulk processing in Elasticsearch**

*Estimated reading time: 30 minutes*

## Overview

Document operations are the foundation of working with Elasticsearch. This guide covers creating, reading, updating, and deleting documents, plus advanced techniques like bulk operations and optimistic concurrency control.

## 📋 Table of Contents

1. [Document Structure](#document-structure)
2. [Create Operations](#create-operations)
3. [Read Operations](#read-operations)
4. [Update Operations](#update-operations)
5. [Delete Operations](#delete-operations)
6. [Bulk Operations](#bulk-operations)
7. [Advanced Techniques](#advanced-techniques)

## 📄 Document Structure

### Understanding Document Metadata

Every document in Elasticsearch has metadata fields that provide important information:

```json
{
  "_index": "blog_posts",      // Index name
  "_id": "1",                  // Document ID
  "_version": 2,               // Version number
  "_seq_no": 3,                // Sequence number
  "_primary_term": 1,          // Primary term
  "_source": {                 // Original document
    "title": "My Blog Post",
    "content": "Content here...",
    "author": "John Doe"
  }
}
```

### Metadata Fields Explained

- **`_index`**: The index containing the document
- **`_id`**: Unique identifier within the index
- **`_version`**: Increments with each update (optimistic concurrency)
- **`_seq_no`**: Global sequence number for the operation
- **`_primary_term`**: Current primary shard term
- **`_source`**: The original JSON document you indexed

## ✏️ Create Operations

### Index with Auto-generated ID

```bash
# POST creates document with auto-generated ID
curl -X POST "localhost:9200/blog/_doc/" -H 'Content-Type: application/json' -d'
{
  "title": "Getting Started with Elasticsearch",
  "author": "Jane Smith",
  "content": "Elasticsearch is a powerful search and analytics engine...",
  "tags": ["elasticsearch", "tutorial", "beginners"],
  "published_date": "2024-01-15T10:00:00Z",
  "view_count": 0,
  "is_published": true
}
'
```

**Response:**
```json
{
  "_index": "blog",
  "_id": "AbC123XyZ",           // Auto-generated ID
  "_version": 1,
  "result": "created",
  "_shards": {
    "total": 2,
    "successful": 1,
    "failed": 0
  },
  "_seq_no": 0,
  "_primary_term": 1
}
```

### Index with Specific ID

```bash
# PUT creates document with specific ID
curl -X PUT "localhost:9200/blog/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Advanced Elasticsearch Techniques",
  "author": "Bob Wilson",
  "content": "Learn advanced search patterns and optimization techniques...",
  "tags": ["elasticsearch", "advanced", "optimization"],
  "published_date": "2024-01-16T14:30:00Z",
  "view_count": 0,
  "is_published": false
}
'
```

### Create-only Operations

```bash
# Create document only if it doesn't exist
curl -X POST "localhost:9200/blog/_create/2" -H 'Content-Type: application/json' -d'
{
  "title": "Elasticsearch Security Best Practices",
  "author": "Alice Johnson",
  "content": "Security is crucial for production deployments...",
  "tags": ["elasticsearch", "security", "production"],
  "published_date": "2024-01-17T09:15:00Z",
  "view_count": 0,
  "is_published": true
}
'
```

If document exists, you'll get a conflict error:
```json
{
  "error": {
    "type": "version_conflict_engine_exception",
    "reason": "version conflict, document already exists"
  }
}
```

## 📖 Read Operations

### Get Document by ID

```bash
# Basic document retrieval
curl "localhost:9200/blog/_doc/1?pretty"

# Get only specific fields
curl "localhost:9200/blog/_doc/1?_source=title,author&pretty"

# Get only the source (no metadata)
curl "localhost:9200/blog/_doc/1/_source?pretty"
```

### Multi-get Operations

```bash
# Get multiple documents
curl -X GET "localhost:9200/_mget" -H 'Content-Type: application/json' -d'
{
  "docs": [
    {"_index": "blog", "_id": "1"},
    {"_index": "blog", "_id": "2"},
    {"_index": "blog", "_id": "3"}
  ]
}'

# Get from same index
curl -X GET "localhost:9200/blog/_mget" -H 'Content-Type: application/json' -d'
{
  "ids": ["1", "2", "3"]
}'
```

### Check Document Existence

```bash
# Check if document exists (returns 200 or 404)
curl -I "localhost:9200/blog/_doc/1"

# HEAD request - no body returned
curl -X HEAD "localhost:9200/blog/_doc/1"
```

## 🔄 Update Operations

### Partial Document Updates

```bash
# Update specific fields
curl -X POST "localhost:9200/blog/_update/1" -H 'Content-Type: application/json' -d'
{
  "doc": {
    "view_count": 150,
    "last_viewed": "2024-01-18T16:45:00Z",
    "is_published": true
  }
}'
```

### Script-based Updates

```bash
# Increment view count
curl -X POST "localhost:9200/blog/_update/1" -H 'Content-Type: application/json' -d'
{
  "script": {
    "source": "ctx._source.view_count += params.increment",
    "params": {
      "increment": 5
    }
  }
}'

# Conditional update
curl -X POST "localhost:9200/blog/_update/1" -H 'Content-Type: application/json' -d'
{
  "script": {
    "source": "if (ctx._source.view_count < 100) { ctx._source.featured = false } else { ctx._source.featured = true }"
  }
}'

# Add to array
curl -X POST "localhost:9200/blog/_update/1" -H 'Content-Type: application/json' -d'
{
  "script": {
    "source": "if (!ctx._source.tags.contains(params.tag)) { ctx._source.tags.add(params.tag) }",
    "params": {
      "tag": "trending"
    }
  }
}'
```

### Upsert Operations

```bash
# Update if exists, create if not
curl -X POST "localhost:9200/blog/_update/5" -H 'Content-Type: application/json' -d'
{
  "doc": {
    "view_count": 50,
    "last_updated": "2024-01-18T17:00:00Z"
  },
  "upsert": {
    "title": "New Blog Post",
    "author": "Mike Davis",
    "content": "This is a new blog post created via upsert",
    "tags": ["elasticsearch", "new"],
    "published_date": "2024-01-18T17:00:00Z",
    "view_count": 50,
    "is_published": true
  }
}
'
```

### Update by Query

```bash
# Update multiple documents matching a query
curl -X POST "localhost:9200/blog/_update_by_query" -H 'Content-Type: application/json' -d'
{
  "script": {
    "source": "ctx._source.category = '\''general'\''"
  },
  "query": {
    "term": {
      "author.keyword": "Jane Smith"
    }
  }
}'

# Update with conflict handling
curl -X POST "localhost:9200/blog/_update_by_query" -H 'Content-Type: application/json' -d'
{
  "script": {
    "source": "ctx._source.updated_at = params.timestamp",
    "params": {
      "timestamp": "2024-01-18T18:00:00Z"
    }
  },
  "query": {
    "range": {
      "published_date": {
        "gte": "2024-01-01",
        "lte": "2024-01-31"
      }
    }
  },
  "conflicts": "proceed"
}'
```

## 🗑️ Delete Operations

### Delete Document by ID

```bash
# Delete specific document
curl -X DELETE "localhost:9200/blog/_doc/1"

# Response:
{
  "_index": "blog",
  "_id": "1",
  "_version": 3,
  "result": "deleted",
  "_shards": {
    "total": 2,
    "successful": 1,
    "failed": 0
  },
  "_seq_no": 5,
  "_primary_term": 1
}
```

### Delete by Query

```bash
# Delete documents matching query
curl -X POST "localhost:9200/blog/_delete_by_query" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "is_published": false
    }
  }
}'

# Delete with conflicts handling
curl -X POST "localhost:9200/blog/_delete_by_query" -H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {
      "published_date": {
        "lte": "2023-12-31"
      }
    }
  },
  "conflicts": "proceed"
}'
```

## 📦 Bulk Operations

### Bulk API Basics

The bulk API allows you to perform multiple operations in a single request, dramatically improving performance for large datasets.

```bash
# Bulk operations
curl -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' -d'
{"index": {"_index": "blog", "_id": "10"}}
{"title": "Bulk Operations Guide", "author": "Sarah Johnson", "content": "Learn how to use bulk operations efficiently"}
{"index": {"_index": "blog", "_id": "11"}}
{"title": "Performance Optimization", "author": "Tom Brown", "content": "Optimize your Elasticsearch performance"}
{"update": {"_index": "blog", "_id": "2"}}
{"doc": {"view_count": 75, "last_updated": "2024-01-18T19:00:00Z"}}
{"delete": {"_index": "blog", "_id": "3"}}
'
```

### Bulk Operations Types

**Index Operation:**
```json
{"index": {"_index": "blog", "_id": "12"}}
{"title": "Document Title", "content": "Document content"}
```

**Create Operation:**
```json
{"create": {"_index": "blog", "_id": "13"}}
{"title": "New Document", "content": "This document must not exist"}
```

**Update Operation:**
```json
{"update": {"_index": "blog", "_id": "2"}}
{"doc": {"view_count": 100}}
```

**Delete Operation:**
```json
{"delete": {"_index": "blog", "_id": "4"}}
```

### Bulk from File

```bash
# Create bulk data file
cat > bulk_data.json << 'EOF'
{"index": {"_index": "products", "_id": "1"}}
{"name": "Laptop", "category": "electronics", "price": 999.99, "in_stock": true}
{"index": {"_index": "products", "_id": "2"}}
{"name": "Mouse", "category": "electronics", "price": 25.50, "in_stock": true}
{"index": {"_index": "products", "_id": "3"}}
{"name": "Keyboard", "category": "electronics", "price": 75.00, "in_stock": false}
{"update": {"_index": "products", "_id": "1"}}
{"doc": {"featured": true, "discount": 0.1}}
EOF

# Execute bulk operation
curl -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' --data-binary @bulk_data.json
```

### Bulk Response Handling

```json
{
  "took": 30,
  "errors": false,
  "items": [
    {
      "index": {
        "_index": "blog",
        "_id": "10",
        "_version": 1,
        "result": "created",
        "status": 201
      }
    },
    {
      "update": {
        "_index": "blog",
        "_id": "2",
        "_version": 3,
        "result": "updated",
        "status": 200
      }
    },
    {
      "delete": {
        "_index": "blog",
        "_id": "3",
        "_version": 2,
        "result": "deleted",
        "status": 200
      }
    }
  ]
}
```

## 🔧 Advanced Techniques

### Optimistic Concurrency Control

```bash
# Sequence number-based concurrency (Recommended)
curl -X PUT "localhost:9200/blog/_doc/1?if_seq_no=5&if_primary_term=1" -H 'Content-Type: application/json' -d'
{
  "title": "Updated Title",
  "content": "Updated content"
}'

# Version-based concurrency control (Not Recommended)
curl -X PUT "localhost:9200/blog/_doc/1?version=2" -H 'Content-Type: application/json' -d'
{
  "title": "Updated Title",
  "content": "Updated content"
}'
```

### Routing

```bash
# Route document to specific shard
curl -X PUT "localhost:9200/blog/_doc/1?routing=user123" -H 'Content-Type: application/json' -d'
{
  "title": "User Specific Post",
  "author": "user123",
  "content": "This post is routed to a specific shard"
}'

# Retrieve with same routing
curl "localhost:9200/blog/_doc/1?routing=user123"
```

### Refresh Control

```bash
# Force refresh immediately
curl -X PUT "localhost:9200/blog/_doc/1?refresh=true" -H 'Content-Type: application/json' -d'
{
  "title": "Immediately Searchable",
  "content": "This document is immediately available for search"
}'

# Wait for refresh
curl -X PUT "localhost:9200/blog/_doc/1?refresh=wait_for" -H 'Content-Type: application/json' -d'
{
  "title": "Wait for Refresh",
  "content": "This request waits until the document is refreshed"
}'
```

### Timeout and Retry

```bash
# Set timeout for operation
curl -X POST "localhost:9200/blog/_update/1?timeout=30s" -H 'Content-Type: application/json' -d'
{
  "doc": {
    "view_count": 200
  }
}'

# Retry on conflict
curl -X POST "localhost:9200/blog/_update/1?retry_on_conflict=3" -H 'Content-Type: application/json' -d'
{
  "script": {
    "source": "ctx._source.view_count += 1"
  }
}'
```

## 🚀 Performance Best Practices

### Bulk Operations

```bash
# ✅ Good: Batch size 100-1000 documents
curl -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' --data-binary @batch_1000.json

# ❌ Bad: Single document operations in loop
for i in {1..1000}; do
  curl -X POST "localhost:9200/blog/_doc/" -H 'Content-Type: application/json' -d'{"title": "Post '$i'"}'
done
```

### Efficient Updates

```bash
# ✅ Good: Update only changed fields
curl -X POST "localhost:9200/blog/_update/1" -H 'Content-Type: application/json' -d'
{
  "doc": {
    "view_count": 150
  }
}'

# ❌ Bad: Replace entire document for small change
curl -X PUT "localhost:9200/blog/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "...",
  "content": "...",
  "view_count": 150
}'
```

### Refresh Strategy

```bash
# ✅ Good: Batch operations with single refresh
curl -X POST "localhost:9200/_bulk?refresh=true" -H 'Content-Type: application/json' --data-binary @bulk_data.json

# ❌ Bad: Refresh every operation
curl -X PUT "localhost:9200/blog/_doc/1?refresh=true" -H 'Content-Type: application/json' -d'...'
curl -X PUT "localhost:9200/blog/_doc/2?refresh=true" -H 'Content-Type: application/json' -d'...'
```

## 🐛 Error Handling

### Common Error Scenarios

**Version Conflict:**
```json
{
  "error": {
    "type": "version_conflict_engine_exception",
    "reason": "[1]: version conflict, current version [3] is different than the one provided [2]"
  }
}
```

**Document Not Found:**
```json
{
  "_index": "blog",
  "_id": "999",
  "found": false
}
```

**Index Not Found:**
```json
{
  "error": {
    "type": "index_not_found_exception",
    "reason": "no such index [missing_index]"
  }
}
```

### Handling Bulk Errors

```bash
# Check for errors in bulk response
curl -X POST "localhost:9200/_bulk" -H 'Content-Type: application/json' -d'
{"index": {"_index": "blog", "_id": "1"}}
{"title": "Valid Document"}
{"index": {"_index": "blog", "_id": "1"}}
{"invalid_field": "This will cause mapping error"}'
```

Response will include error details:
```json
{
  "took": 5,
  "errors": true,
  "items": [
    {
      "index": {
        "_index": "blog",
        "_id": "1",
        "status": 201,
        "result": "created"
      }
    },
    {
      "index": {
        "_index": "blog",
        "_id": "1",
        "status": 400,
        "error": {
          "type": "mapper_parsing_exception",
          "reason": "failed to parse field [invalid_field]"
        }
      }
    }
  ]
}
```

## 🎯 Real-world Examples

### E-commerce Product Management

```bash
# Create product with inventory tracking
curl -X PUT "localhost:9200/products/_doc/laptop-001" -H 'Content-Type: application/json' -d'
{
  "name": "Gaming Laptop",
  "category": "electronics",
  "price": 1299.99,
  "sku": "laptop-001",
  "inventory": {
    "quantity": 50,
    "reserved": 0,
    "available": 50
  },
  "created_at": "2024-01-18T10:00:00Z",
  "updated_at": "2024-01-18T10:00:00Z"
}'

# Process order (decrease inventory)
curl -X POST "localhost:9200/products/_update/laptop-001" -H 'Content-Type: application/json' -d'
{
  "script": {
    "source": "ctx._source.inventory.quantity -= params.sold; ctx._source.inventory.available = ctx._source.inventory.quantity - ctx._source.inventory.reserved; ctx._source.updated_at = params.timestamp",
    "params": {
      "sold": 2,
      "timestamp": "2024-01-18T14:30:00Z"
    }
  }
}'
```

### User Activity Logging

```bash
# Log user activity
curl -X POST "localhost:9200/user-activity/_doc/" -H 'Content-Type: application/json' -d'
{
  "user_id": "user123",
  "action": "login",
  "timestamp": "2024-01-18T15:00:00Z",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "session_id": "sess_abc123"
}'

# Update user last activity
curl -X POST "localhost:9200/users/_update/user123" -H 'Content-Type: application/json' -d'
{
  "doc": {
    "last_activity": "2024-01-18T15:00:00Z",
    "last_ip": "192.168.1.100"
  },
  "upsert": {
    "user_id": "user123",
    "first_seen": "2024-01-18T15:00:00Z",
    "last_activity": "2024-01-18T15:00:00Z",
    "last_ip": "192.168.1.100"
  }
}'
```

## 🔗 Next Steps

Now that you've mastered document operations, let's explore how to structure your data:

1. **[Mapping & Field Types](03_mapping-field-types.md)** - Define document schemas
2. **[Index Lifecycle](02_index-lifecycle.md)** - Manage indices effectively
3. **[Query DSL Basics](../03-search-fundamentals/03_query-dsl-basics.md)** - Search your documents

## 📚 Key Takeaways

- ✅ **Use bulk operations** for better performance with multiple documents
- ✅ **Implement proper error handling** for production applications
- ✅ **Leverage partial updates** to modify specific fields efficiently
- ✅ **Use optimistic concurrency control** to prevent conflicts
- ✅ **Choose appropriate refresh strategies** based on your use case
- ✅ **Handle version conflicts** gracefully in concurrent environments
- ✅ **Use routing** for better performance with large datasets
- ✅ **Monitor bulk operation responses** for errors and failures

Ready to learn about data structure? Continue with [Mapping & Field Types](mapping-field-types.md) to master document schemas!