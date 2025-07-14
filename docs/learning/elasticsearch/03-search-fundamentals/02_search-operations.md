# Search Operations

**Master the Search API and request structure for effective data retrieval**

*Estimated reading time: 25 minutes*

## Overview

The Search API is the core of Elasticsearch functionality. This guide covers how to structure search requests, handle responses, implement pagination, and optimize search performance for real-world applications.

## 📋 Table of Contents

1. [Search API Basics](#search-api-basics)
2. [Request Structure](#request-structure)
3. [Response Structure](#response-structure)
4. [Pagination Strategies](#pagination-strategies)
5. [Source Filtering](#source-filtering)
6. [Highlighting](#highlighting)
7. [Search Templates](#search-templates)
8. [Performance Optimization](#performance-optimization)

## 🔍 Search API Basics

### Basic Search Syntax

```bash
# Search all documents
curl "localhost:9200/blog/_search"

# Search with query parameter
curl "localhost:9200/blog/_search?q=elasticsearch"

# Search multiple indices
curl "localhost:9200/blog,news/_search"

# Search all indices
curl "localhost:9200/_search"

# Search with index patterns
curl "localhost:9200/blog-*/_search"
```

### HTTP Methods

```bash
# GET request (preferred for simple queries)
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}}
}
'

# POST request (required for large query bodies)
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}}
}
'
```

## 🏗️ Request Structure

### Complete Search Request

```bash
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"content": "elasticsearch"}}
      ],
      "filter": [
        {"term": {"status": "published"}}
      ]
    }
  },
  "from": 0,
  "size": 10,
  "sort": [
    {"publish_date": {"order": "desc"}},
    "_score"
  ],
  "_source": ["title", "author", "publish_date"],
  "highlight": {
    "fields": {
      "content": {}
    }
  },
  "aggs": {
    "categories": {
      "terms": {"field": "category"}
    }
  }
}
'
```

### Request Parameters

**Core Parameters:**
```json
{
  "query": {},           // Query definition
  "from": 0,            // Starting document (default: 0)
  "size": 10,           // Number of documents (default: 10, max: 10000)
  "sort": [],           // Sort criteria
  "_source": [],        // Source filtering
  "timeout": "1s"       // Search timeout
}
```

**Additional Parameters:**
```json
{
  "min_score": 0.5,          // Minimum score threshold
  "terminate_after": 1000,    // Early termination after N docs
  "track_total_hits": true,   // Accurate total count
  "version": true,            // Include document versions
  "seq_no_primary_term": true // Include sequence numbers
}
```

## 📊 Response Structure

### Complete Response Example

```json
{
  "took": 5,                    // Time in milliseconds
  "timed_out": false,           // Whether request timed out
  "_shards": {
    "total": 3,
    "successful": 3,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {
      "value": 1250,           // Total matching documents
      "relation": "eq"         // "eq" (exact) or "gte" (≥10,000)
    },
    "max_score": 2.4159274,    // Highest relevance score
    "hits": [                  // Array of matching documents
      {
        "_index": "blog",
        "_id": "1",
        "_score": 2.4159274,
        "_source": {
          "title": "Elasticsearch Guide",
          "content": "Complete guide to elasticsearch..."
        },
        "highlight": {
          "content": ["Complete guide to <em>elasticsearch</em>..."]
        }
      }
    ]
  },
  "aggregations": {            // Aggregation results
    "categories": {
      "buckets": [
        {"key": "technology", "doc_count": 450},
        {"key": "tutorial", "doc_count": 320}
      ]
    }
  }
}
```

### Response Field Explanation

**Timing and Metadata:**
- **`took`**: Search execution time in milliseconds
- **`timed_out`**: Whether the search exceeded timeout
- **`_shards`**: Information about shard execution

**Results:**
- **`hits.total`**: Total number of matching documents
- **`hits.max_score`**: Highest relevance score
- **`hits.hits`**: Array of returned documents

**Document Fields:**
- **`_index`**: Index containing the document
- **`_id`**: Document identifier
- **`_score`**: Relevance score (null in filter context)
- **`_source`**: Original document content

## 📄 Pagination Strategies

### From/Size Pagination

Standard pagination for small result sets:

```bash
# Page 1 (documents 0-9)
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "from": 0,
  "size": 10
}
'

# Page 2 (documents 10-19)
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "from": 10,
  "size": 10
}
'

# Page 10 (documents 90-99)
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "from": 90,
  "size": 10
}
'
```

**Limitations:**
- Default max: `from + size ≤ 10,000`
- Performance degrades with deep pagination
- Memory usage increases with offset

### Scroll API

For large result sets and data export:

```bash
# Initial scroll request
curl -X POST "localhost:9200/blog/_search?scroll=1m" -H 'Content-Type: application/json' -d'
{
  "size": 100,
  "query": {"match_all": {}}
}
'

# Response includes scroll_id
{
  "_scroll_id": "DXF1ZXJ5QW5kRmV0Y2g...",
  "hits": {
    "total": {"value": 10000},
    "hits": [...]
  }
}

# Continue scrolling
curl -X POST "localhost:9200/_search/scroll" -H 'Content-Type: application/json' -d'
{
  "scroll": "1m",
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2g..."
}
'

# Clear scroll context
curl -X DELETE "localhost:9200/_search/scroll" -H 'Content-Type: application/json' -d'
{
  "scroll_id": "DXF1ZXJ5QW5kRmV0Y2g..."
}
'
```

### Search After

Efficient pagination for real-time data:

```bash
# Initial search with sort
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "size": 10,
  "query": {"match_all": {}},
  "sort": [
    {"publish_date": "desc"},
    {"_id": "asc"}  // Tiebreaker for consistent ordering
  ]
}
'

# Response includes sort values
{
  "hits": {
    "hits": [
      {
        "_id": "doc1",
        "_source": {...},
        "sort": ["2024-01-20T10:00:00Z", "doc1"]
      }
    ]
  }
}

# Next page using search_after
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "size": 10,
  "query": {"match_all": {}},
  "sort": [
    {"publish_date": "desc"},
    {"_id": "asc"}
  ],
  "search_after": ["2024-01-20T10:00:00Z", "doc1"]
}
'
```

### Point in Time (PIT)

Consistent pagination across index changes:

```bash
# Create point in time
curl -X POST "localhost:9200/blog/_pit?keep_alive=1m"

# Response
{
  "id": "46ToAwMDaWR4BXV1aWQyKwZub2RlXzMAAAAAAAAAAA=="
}

# Search with PIT
curl -X POST "localhost:9200/_search" -H 'Content-Type: application/json' -d'
{
  "size": 10,
  "query": {"match_all": {}},
  "sort": [{"_shard_doc": "asc"}],
  "pit": {
    "id": "46ToAwMDaWR4BXV1aWQyKwZub2RlXzMAAAAAAAAAAA==",
    "keep_alive": "1m"
  }
}
'

# Close PIT
curl -X DELETE "localhost:9200/_pit" -H 'Content-Type: application/json' -d'
{
  "id": "46ToAwMDaWR4BXV1aWQyKwZub2RlXzMAAAAAAAAAAA=="
}
'
```

## 🎯 Source Filtering

Control which fields are returned in the response:

### Include/Exclude Fields

```bash
# Include specific fields
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "_source": ["title", "author", "publish_date"]
}
'

# Exclude specific fields
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "_source": {
    "excludes": ["content", "internal_notes"]
  }
}
'

# Include and exclude patterns
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "_source": {
    "includes": ["title", "author", "meta.*"],
    "excludes": ["meta.internal_*"]
  }
}
'

# Disable source
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "_source": false
}
'
```

### Stored Fields

Return stored field values instead of source:

```bash
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "_source": false,
  "stored_fields": ["title", "tags"]
}
'
```

## 🎨 Highlighting

Highlight matching terms in search results:

### Basic Highlighting

```bash
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "elasticsearch tutorial"}
  },
  "highlight": {
    "fields": {
      "content": {}
    }
  }
}
'
```

### Advanced Highlighting

```bash
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch tutorial",
      "fields": ["title", "content"]
    }
  },
  "highlight": {
    "pre_tags": ["<mark>"],
    "post_tags": ["</mark>"],
    "fragment_size": 150,
    "number_of_fragments": 3,
    "fields": {
      "title": {
        "number_of_fragments": 0  // Return entire field
      },
      "content": {
        "fragment_size": 200,
        "number_of_fragments": 2
      }
    }
  }
}
'
```

### Highlighting Options

```json
{
  "highlight": {
    "pre_tags": ["<em>"],           // Opening tag
    "post_tags": ["</em>"],         // Closing tag
    "fragment_size": 100,           // Fragment character length
    "number_of_fragments": 3,       // Max fragments per field
    "fragmenter": "span",           // Fragmenter type
    "order": "score",               // Fragment ordering
    "require_field_match": false,   // Highlight any matching field
    "boundary_scanner": "sentence", // Boundary detection
    "max_analyzed_offset": 1000000, // Analysis limit
    "fields": {
      "content": {
        "type": "unified"           // Highlighter type
      }
    }
  }
}
```

## 📝 Search Templates

Store and reuse common search patterns:

### Create Search Template

```bash
curl -X PUT "localhost:9200/_scripts/blog_search" -H 'Content-Type: application/json' -d'
{
  "script": {
    "lang": "mustache",
    "source": {
      "query": {
        "bool": {
          "must": [
            {{#query}}
            {"match": {"{{field}}": "{{query}}"}}
            {{/query}}
          ],
          "filter": [
            {{#status}}
            {"term": {"status": "{{status}}"}}
            {{/status}}
            {{#date_range}}
            {
              "range": {
                "publish_date": {
                  "gte": "{{from}}",
                  "lte": "{{to}}"
                }
              }
            }
            {{/date_range}}
          ]
        }
      },
      "sort": [{"{{sort_field}}": {"order": "{{sort_order}}"}}],
      "from": {{from}},
      "size": {{size}}
    }
  }
}
'
```

### Use Search Template

```bash
curl -X POST "localhost:9200/blog/_search/template" -H 'Content-Type: application/json' -d'
{
  "id": "blog_search",
  "params": {
    "query": "elasticsearch",
    "field": "content",
    "status": "published",
    "sort_field": "publish_date",
    "sort_order": "desc",
    "from": 0,
    "size": 10
  }
}
'
```

### Inline Template

```bash
curl -X POST "localhost:9200/blog/_search/template" -H 'Content-Type: application/json' -d'
{
  "source": {
    "query": {
      "match": {"{{field}}": "{{query}}"}
    }
  },
  "params": {
    "field": "title",
    "query": "elasticsearch"
  }
}
'
```

## 🎯 Real-world Examples

### E-commerce Product Search

```bash
# Product search with filters and facets
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "wireless headphones",
            "fields": ["name^3", "description", "brand^2"]
          }
        }
      ],
      "filter": [
        {"term": {"in_stock": true}},
        {"range": {"price": {"gte": 50, "lte": 200}}},
        {"terms": {"category": ["electronics", "audio"]}}
      ]
    }
  },
  "aggs": {
    "brands": {
      "terms": {"field": "brand", "size": 10}
    },
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          {"to": 50},
          {"from": 50, "to": 100},
          {"from": 100, "to": 200},
          {"from": 200}
        ]
      }
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"rating": {"order": "desc"}},
    {"price": {"order": "asc"}}
  ],
  "from": 0,
  "size": 20,
  "_source": ["name", "price", "brand", "rating", "image_url"],
  "highlight": {
    "fields": {
      "name": {},
      "description": {"fragment_size": 100}
    }
  }
}
'
```

### Log Analysis Search

```bash
# Error log analysis with time filtering
curl -X POST "localhost:9200/logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"message": "error exception"}}
      ],
      "filter": [
        {"term": {"level": "ERROR"}},
        {
          "range": {
            "@timestamp": {
              "gte": "now-1h",
              "lte": "now"
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "services": {
      "terms": {"field": "service", "size": 20}
    },
    "error_timeline": {
      "date_histogram": {
        "field": "@timestamp",
        "interval": "5m"
      }
    }
  },
  "sort": [{"@timestamp": {"order": "desc"}}],
  "size": 50,
  "_source": ["@timestamp", "level", "service", "message"],
  "highlight": {
    "fields": {
      "message": {"fragment_size": 200}
    }
  }
}
'
```

## 🚀 Performance Optimization

### Query Optimization

```bash
# ✅ Good: Use filters for exact matches
{
  "query": {
    "bool": {
      "must": [
        {"match": {"content": "elasticsearch"}}  // Query context
      ],
      "filter": [
        {"term": {"status": "published"}},       // Filter context
        {"range": {"date": {"gte": "2024-01-01"}}}
      ]
    }
  }
}

# ❌ Bad: Everything in query context
{
  "query": {
    "bool": {
      "must": [
        {"match": {"content": "elasticsearch"}},
        {"term": {"status": "published"}},
        {"range": {"date": {"gte": "2024-01-01"}}}
      ]
    }
  }
}
```

### Source Filtering

```bash
# ✅ Good: Only return needed fields
{
  "query": {"match_all": {}},
  "_source": ["title", "author", "date"]
}

# ❌ Bad: Return all fields when not needed
{
  "query": {"match_all": {}},
  "_source": true  // Returns everything
}
```

### Request Size

```bash
# ✅ Good: Reasonable page size
{
  "query": {"match_all": {}},
  "size": 20
}

# ❌ Bad: Too large page size
{
  "query": {"match_all": {}},
  "size": 10000  // Heavy on memory and network
}
```

### Timeout Settings

```bash
# Set reasonable timeouts
curl -X POST "localhost:9200/blog/_search?timeout=1s" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "timeout": "1s"
}
'
```

## 🔗 Next Steps

Now that you understand search operations, let's learn about result refinement:

1. **[Filtering & Sorting](filtering-sorting.md)** - Master result refinement techniques
2. **[Full-text Search](../04-advanced-search/full-text-search.md)** - Advanced text search patterns
3. **[Aggregations](../04-advanced-search/aggregations.md)** - Analyze your search results

## 📚 Key Takeaways

- ✅ **Use appropriate pagination** based on your use case
- ✅ **Filter source fields** to reduce response size
- ✅ **Implement highlighting** for better user experience
- ✅ **Use search templates** for reusable query patterns
- ✅ **Set reasonable timeouts** to prevent long-running queries
- ✅ **Optimize requests** by using filter context appropriately
- ✅ **Handle large result sets** with scroll or search_after
- ✅ **Structure responses properly** for your application needs

Ready to learn about filtering and sorting? Continue with [Filtering & Sorting](filtering-sorting.md) to master result refinement!