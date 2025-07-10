# Core Concepts

**Master the fundamental building blocks of Elasticsearch**

*Estimated reading time: 20 minutes*

## Overview

Understanding Elasticsearch's core concepts is essential for building effective search and analytics solutions. This guide covers the key components that make Elasticsearch powerful and scalable.

## 📄 Documents

**The basic unit of information in Elasticsearch**

### What is a Document?
A document is a JSON object that represents a single record or piece of data. Think of it like a row in a traditional database, but with much more flexibility.

```json
{
  "_index": "blog_posts",
  "_id": "1",
  "_version": 1,
  "_source": {
    "title": "Getting Started with Elasticsearch",
    "author": "John Doe",
    "content": "Elasticsearch is a powerful search engine...",
    "tags": ["elasticsearch", "tutorial", "search"],
    "published_date": "2024-01-15T10:30:00Z",
    "view_count": 1250,
    "is_featured": true
  }
}
```

### Document Structure
- **`_index`**: Which index contains the document
- **`_id`**: Unique identifier for the document
- **`_version`**: Version number (for conflict resolution)
- **`_source`**: The original JSON document you stored

### Document Types
```json
// Text content
{
  "title": "Product Review",
  "content": "This product is amazing..."
}

// Structured data
{
  "user_id": 12345,
  "purchase_date": "2024-01-15",
  "items": [
    {"name": "Laptop", "price": 999.99},
    {"name": "Mouse", "price": 25.50}
  ]
}

// Geolocation data
{
  "location": {
    "lat": 40.7128,
    "lon": -74.0060
  },
  "city": "New York"
}
```

## 📚 Indices

**Collections of documents with similar characteristics**

### What is an Index?
An index is like a database table that holds documents with similar structure or purpose. However, unlike SQL tables, indices are more flexible with their schema.

```bash
# Examples of indices
blog_posts          # Blog articles
products           # E-commerce products
user_activity      # User behavior logs
error_logs         # Application errors
```

### Index Characteristics
- **Name**: Must be lowercase, no spaces
- **Documents**: Contains similar types of documents
- **Mappings**: Defines how documents are indexed
- **Settings**: Configuration like number of shards

### Index Examples
```bash
# Create an index
curl -X PUT "localhost:9200/products" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  }
}'

# Add document to index
curl -X POST "localhost:9200/products/_doc/1" -H 'Content-Type: application/json' -d'
{
  "name": "Wireless Headphones",
  "category": "electronics",
  "price": 99.99
}'
```

## 🔧 Shards

**How Elasticsearch scales horizontally**

### What are Shards?
Shards are the way Elasticsearch distributes data across multiple nodes. Each index is divided into shards, allowing for horizontal scaling and parallel processing.

### Primary vs Replica Shards

**Primary Shards**
- Hold the original data
- Handle write operations
- Number is fixed when index is created

**Replica Shards**
- Copies of primary shards
- Provide redundancy and fault tolerance
- Can be changed after index creation
- Handle read operations

```bash
# Index with 3 primary shards and 2 replicas
curl -X PUT "localhost:9200/large_dataset" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 3,      # Primary shards
    "number_of_replicas": 2     # Replica shards per primary
  }
}'
```

### Shard Distribution
```
Node 1: [P0] [R1] [R2]
Node 2: [P1] [R0] [R2]  
Node 3: [P2] [R0] [R1]

P = Primary shard
R = Replica shard
Numbers = Shard ID
```

## 🌐 Cluster

**Collection of nodes working together**

### What is a Cluster?
A cluster is one or more nodes (servers) that together hold your data and provide indexing and search capabilities. Each cluster has a unique name.

```bash
# Check cluster health
curl "localhost:9200/_cluster/health?pretty"

# Response:
{
  "cluster_name": "elasticsearch",
  "status": "green",
  "number_of_nodes": 3,
  "number_of_data_nodes": 3,
  "active_primary_shards": 15,
  "active_shards": 30
}
```

### Cluster Status
- **🟢 Green**: All shards are active
- **🟡 Yellow**: All primary shards are active, some replicas are not
- **🔴 Red**: Some primary shards are not active

## 🖥️ Nodes

**Individual servers in a cluster**

### What is a Node?
A node is a single server that is part of your cluster. It stores data and participates in the cluster's indexing and search capabilities.

### Node Types

**Master Node**
- Manages cluster state
- Handles node join/leave operations
- Creates/deletes indices

**Data Node**
- Stores data and executes queries
- Handles CRUD operations
- Performs aggregations

**Coordinating Node**
- Routes requests to appropriate nodes
- Gathers results from multiple nodes
- Acts as load balancer

```bash
# Check node information
curl "localhost:9200/_nodes?pretty"

# Response shows node details:
{
  "nodes": {
    "node_id": {
      "name": "node-1",
      "roles": ["master", "data", "ingest"],
      "version": "9.0.2"
    }
  }
}
```

## 🗺️ Mappings

**How documents are structured and indexed**

### What is Mapping?
Mapping defines how documents and their fields are stored and indexed. It's like a schema in a traditional database, but more flexible.

### Dynamic vs Explicit Mapping

**Dynamic Mapping** (Automatic)
```json
// Elasticsearch automatically detects field types
{
  "title": "Product Review",        // → text
  "price": 99.99,                  // → float
  "created_at": "2024-01-15",      // → date
  "in_stock": true                 // → boolean
}
```

**Explicit Mapping** (Manual)
```bash
curl -X PUT "localhost:9200/products/_mapping" -H 'Content-Type: application/json' -d'
{
  "properties": {
    "title": {
      "type": "text",
      "analyzer": "standard"
    },
    "price": {
      "type": "float"
    },
    "category": {
      "type": "keyword"
    },
    "created_at": {
      "type": "date",
      "format": "yyyy-MM-dd"
    }
  }
}'
```

### Common Field Types

| Type | Description | Example |
|------|-------------|---------|
| `text` | Full-text search | "Product description" |
| `keyword` | Exact match | "electronics" |
| `integer` | Whole numbers | 42 |
| `float` | Decimal numbers | 99.99 |
| `date` | Date/time | "2024-01-15" |
| `boolean` | True/false | true |
| `object` | Nested JSON | {"name": "value"} |
| `geo_point` | Latitude/longitude | {"lat": 40.7, "lon": -74.0} |

## 🔍 Analyzers

**How text is processed for search**

### What is an Analyzer?
An analyzer processes text fields to make them searchable. It breaks text into tokens and applies transformations.

### Analyzer Components

**Character Filters**
- Remove HTML tags
- Convert characters
- Pattern replacement

**Tokenizers**
- Split text into tokens
- Handle whitespace, punctuation
- Language-specific rules

**Token Filters**
- Lowercase transformation
- Remove stop words
- Stemming

### Example Analysis
```bash
# Test analyzer
curl -X POST "localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "standard",
  "text": "The Quick Brown Fox Jumps!"
}'

# Response:
{
  "tokens": [
    {"token": "the", "start_offset": 0, "end_offset": 3},
    {"token": "quick", "start_offset": 4, "end_offset": 9},
    {"token": "brown", "start_offset": 10, "end_offset": 15},
    {"token": "fox", "start_offset": 16, "end_offset": 19},
    {"token": "jumps", "start_offset": 20, "end_offset": 25}
  ]
}
```

## 📊 Understanding Data Flow

### Document Lifecycle
```
1. Document → 2. Analyzer → 3. Tokens → 4. Inverted Index → 5. Search Ready
```

### Search Process
```
1. Query → 2. Parse → 3. Execute → 4. Score → 5. Results
```

## 🔍 Practical Example

Let's create a complete example that demonstrates these concepts:

```bash
# 1. Create index with explicit mapping
curl -X PUT "localhost:9200/blog" -H 'Content-Type: application/json' -d'
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "title": {"type": "text"},
      "author": {"type": "keyword"},
      "content": {"type": "text"},
      "tags": {"type": "keyword"},
      "published": {"type": "date"},
      "views": {"type": "integer"}
    }
  }
}'

# 2. Add documents
curl -X POST "localhost:9200/blog/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Elasticsearch Fundamentals",
  "author": "Jane Smith",
  "content": "Learn the core concepts of Elasticsearch including documents, indices, and shards.",
  "tags": ["elasticsearch", "tutorial"],
  "published": "2024-01-15",
  "views": 1520
}'

# 3. Search documents
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "content": "core concepts"
    }
  }
}'
```

## 🎯 Key Relationships

### Hierarchy
```
Cluster
├── Node 1
├── Node 2
└── Node 3
    ├── Index A
    │   ├── Shard 0 (Primary)
    │   └── Shard 1 (Replica)
    └── Index B
        ├── Shard 0 (Primary)
        └── Shard 1 (Replica)
```

### Document Structure
```
Document
├── Metadata (_index, _id, _version)
└── Source
    ├── Field 1 (analyzed by mapping)
    ├── Field 2 (analyzed by mapping)
    └── Field N (analyzed by mapping)
```

## 🚀 Best Practices

### Index Design
- **Purpose-based**: Create indices for specific data types
- **Time-based**: Use date-based indices for time-series data
- **Size management**: Keep indices at reasonable sizes (GB to TB)

### Shard Strategy
- **Start simple**: Begin with 1-2 shards per node
- **Monitor performance**: Adjust based on data volume and query patterns
- **Avoid over-sharding**: Too many small shards hurt performance

### Mapping Guidelines
- **Explicit is better**: Define mappings for production systems
- **Text vs Keyword**: Use `text` for search, `keyword` for exact match
- **Analyze carefully**: Choose appropriate analyzers for your use case

## ❌ Common Pitfalls

### Over-sharding
```bash
# ❌ Bad: Too many shards for small dataset
"number_of_shards": 10  # For 1GB of data

# ✅ Good: Reasonable sharding
"number_of_shards": 2   # For 1GB of data
```

### Wrong Field Types
```json
// ❌ Bad: Using text for exact match
{
  "status": {
    "type": "text"  // Will be analyzed
  }
}

// ✅ Good: Using keyword for exact match
{
  "status": {
    "type": "keyword"  // Exact match
  }
}
```

## 🔗 Next Steps

Now that you understand the core concepts, let's get hands-on:

1. **[Installation & Setup](installation-setup.md)** - Set up your development environment
2. **[Basic API Interactions](basic-api-interactions.md)** - Practice with real commands
3. **[Document Operations](../02-data-management/document-operations.md)** - Learn CRUD operations

## 📚 Key Takeaways

- ✅ **Documents** are JSON objects that hold your data
- ✅ **Indices** are collections of similar documents
- ✅ **Shards** enable horizontal scaling and parallel processing
- ✅ **Clusters** are collections of nodes working together
- ✅ **Mappings** define how documents are structured and indexed
- ✅ **Analyzers** process text to make it searchable
- ✅ Understanding these concepts is crucial for effective Elasticsearch usage

Ready to get your hands dirty? Continue with [Installation & Setup](installation-setup.md) to start building with Elasticsearch!