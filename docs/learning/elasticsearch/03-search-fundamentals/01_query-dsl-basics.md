# Query DSL Basics

**Master Elasticsearch's powerful query language for precise data retrieval**

*Estimated reading time: 30 minutes*

## Overview

The Query DSL (Domain Specific Language) is Elasticsearch's flexible, JSON-based query language. It allows you to build complex queries that combine full-text search, term-level queries, compound queries, and more. Understanding Query DSL is essential for effective search implementation.

## 📋 Table of Contents

1. [Query Structure](#query-structure)
2. [Query Context vs Filter Context](#query-context-vs-filter-context)
3. [Full-text Queries](#full-text-queries)
4. [Term-level Queries](#term-level-queries)
5. [Compound Queries](#compound-queries)
6. [Query Execution](#query-execution)
7. [Performance Considerations](#performance-considerations)

## 🏗️ Query Structure

### Basic Query Anatomy

Every Elasticsearch query follows this structure:

```json
{
  "query": {
    "query_type": {
      "field_name": {
        "value": "search_term",
        "parameter": "value"
      }
    }
  }
}
```

### Simple Query Example

```bash
# Basic match query
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": "elasticsearch tutorial"
    }
  }
}
'
```

**Response Structure:**
```json
{
  "took": 5,
  "timed_out": false,
  "_shards": {
    "total": 1,
    "successful": 1,
    "skipped": 0,
    "failed": 0
  },
  "hits": {
    "total": {"value": 2, "relation": "eq"},
    "max_score": 1.2039728,
    "hits": [
      {
        "_index": "blog",
        "_id": "1",
        "_score": 1.2039728,
        "_source": {
          "title": "Elasticsearch Tutorial for Beginners",
          "content": "Learn the basics of Elasticsearch..."
        }
      }
    ]
  }
}
```

## ⚖️ Query Context vs Filter Context

Understanding the difference between query and filter context is crucial for performance and relevance.

### Query Context

Queries in query context:
- **Calculate relevance scores** (`_score`)
- **Answer**: "How well does this document match?"
- **Use for**: Full-text search, ranked results

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "content": "elasticsearch performance"
    }
  }
}'
```

### Filter Context

Queries in filter context:
- **No scoring** (binary yes/no)
- **Answer**: "Does this document match?"
- **Use for**: Exact matches, ranges, existence checks
- **Cacheable** for better performance

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"status": "published"}},
        {"range": {"publish_date": {"gte": "2024-01-01"}}}
      ]
    }
  }
}'
```

### Combining Both Contexts

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"content": "elasticsearch"}}  // Query context (scored)
      ],
      "filter": [
        {"term": {"status": "published"}},      // Filter context (not scored)
        {"range": {"view_count": {"gte": 100}}} // Filter context (not scored)
      ]
    }
  }
}'
```

## 📝 Full-text Queries

Full-text queries analyze the query string and search for analyzed terms.

### Match Query

The most common full-text query:

```bash
# Basic match
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": "elasticsearch tutorial"
    }
  }
}'

# Match with operator
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": {
        "query": "elasticsearch tutorial",
        "operator": "and"  // Default is "or"
      }
    }
  }
}'

# Match with minimum_should_match
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "content": {
        "query": "elasticsearch performance optimization tuning",
        "minimum_should_match": "75%"
      }
    }
  }
}'
```

### Match Phrase Query

Searches for exact phrase:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_phrase": {
      "content": "search engine"
    }
  }
}
'

# Match phrase with slop (word distance)
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_phrase": {
      "content": {
        "query": "elasticsearch powerful",
        "slop": 2  // Allow up to 2 words between
      }
    }
  }
}'
```

### Match Phrase Prefix

For autocomplete and prefix matching:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_phrase_prefix": {
      "title": {
        "query": "elasticsearch tut",
        "max_expansions": 10
      }
    }
  }
}'
```

### Multi Match Query

Search across multiple fields:

```bash
# Basic multi-match
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch tutorial",
      "fields": ["title", "content"]
    }
  }
}'

# Multi-match with field boosting
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch",
      "fields": ["title^3", "content", "tags^2"]  // title is 3x more important
    }
  }
}'

# Multi-match types
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "elasticsearch tutorial",
      "fields": ["title", "content"],
      "type": "best_fields"  // Options: best_fields, most_fields, cross_fields, phrase, phrase_prefix
    }
  }
}'
```

## 🎯 Term-level Queries

Term-level queries find documents containing exact terms (not analyzed).

### Term Query

Exact match for a single term:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "status": "published"
    }
  }
}'

# Term with boost
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "category": {
        "value": "tutorial",
        "boost": 2.0
      }
    }
  }
}'
```

### Terms Query

Match any of multiple terms:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "terms": {
      "tags": ["elasticsearch", "search", "analytics"]
    }
  }
}'
```

### Range Query

Find documents within a range:

```bash
# Numeric range
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {
      "view_count": {
        "gte": 100,
        "lte": 1000
      }
    }
  }
}'

# Date range
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {
      "publish_date": {
        "gte": "2024-01-01",
        "lte": "now"
      }
    }
  }
}'

# Date math
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "range": {
      "publish_date": {
        "gte": "now-7d/d",  // 7 days ago, rounded to day
        "lte": "now/d"      // Today, rounded to day
      }
    }
  }
}'
```

### Exists Query

Find documents where a field exists:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "exists": {
      "field": "featured_image"
    }
  }
}'
```

### Prefix Query

Find terms starting with a prefix:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "prefix": {
      "author": "john"
    }
  }
}'
```

### Wildcard Query

Use wildcards (* and ?) for pattern matching:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "wildcard": {
      "title": "*elasticsearch*"
    }
  }
}'
```

### Fuzzy Query

Find terms similar to the search term:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "fuzzy": {
      "title": {
        "value": "elasticsearh",  // Typo in "elasticsearch"
        "fuzziness": "AUTO"
      }
    }
  }
}'
```

## 🔧 Compound Queries

Combine multiple queries using boolean logic.

### Bool Query

The most important compound query:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"content": "elasticsearch"}}
      ],
      "filter": [
        {"term": {"status": "published"}},
        {"range": {"publish_date": {"gte": "2024-01-01"}}}
      ],
      "should": [
        {"match": {"tags": "tutorial"}},
        {"match": {"tags": "guide"}}
      ],
      "must_not": [
        {"term": {"category": "deprecated"}}
      ]
    }
  }
}'
```

**Bool Query Clauses:**
- **`must`**: Documents MUST match (scored)
- **`filter`**: Documents MUST match (not scored)
- **`should`**: Documents SHOULD match (optional, but boost score)
- **`must_not`**: Documents MUST NOT match (not scored)

### Boosting Query

Boost positive queries and diminish negative ones:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "boosting": {
      "positive": {
        "match": {"content": "elasticsearch"}
      },
      "negative": {
        "match": {"content": "deprecated"}
      },
      "negative_boost": 0.2
    }
  }
}'
```

### Constant Score Query

Wrap filter queries to give them a constant score:

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "constant_score": {
      "filter": {
        "term": {"status": "published"}
      },
      "boost": 1.5
    }
  }
}'
```

### Dis Max Query

Find documents matching any of the queries (disjunction max):

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "dis_max": {
      "queries": [
        {"match": {"title": "elasticsearch"}},
        {"match": {"content": "elasticsearch"}},
        {"match": {"tags": "elasticsearch"}}
      ],
      "tie_breaker": 0.3
    }
  }
}'
```

## ⚡ Query Execution

### Query with Size and From

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "elasticsearch"}
  },
  "from": 0,
  "size": 10
}'
```

### Query with Source Filtering

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "elasticsearch"}
  },
  "_source": ["title", "author", "publish_date"],
  "size": 5
}'
```

### Query with Highlighting

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "elasticsearch"}
  },
  "highlight": {
    "fields": {
      "content": {}
    }
  }
}'
```

### Query with Sorting

```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"content": "elasticsearch"}
  },
  "sort": [
    {"publish_date": {"order": "desc"}},
    {"_score": {"order": "desc"}}
  ]
}
'
```

## 🎯 Practical Examples

### Blog Search Implementation

```bash
# Create sample blog index
curl -X PUT "localhost:9200/blog" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
      "content": {"type": "text"},
      "author": {"type": "keyword"},
      "tags": {"type": "keyword"},
      "category": {"type": "keyword"},
      "status": {"type": "keyword"},
      "publish_date": {"type": "date"},
      "view_count": {"type": "integer"},
      "featured": {"type": "boolean"}
    }
  }
}
'

# Add sample documents
curl -X POST "localhost:9200/blog/_bulk" -H 'Content-Type: application/json' -d'
{"index": {"_id": "1"}}
{"title": "Getting Started with Elasticsearch", "content": "Elasticsearch is a powerful search engine that helps you find information quickly", "author": "jane", "tags": ["elasticsearch", "tutorial"], "category": "technology", "status": "published", "publish_date": "2024-01-15", "view_count": 1250, "featured": true}
{"index": {"_id": "2"}}
{"title": "Advanced Search Techniques", "content": "Learn advanced elasticsearch features like aggregations and complex queries", "author": "bob", "tags": ["elasticsearch", "advanced"], "category": "technology", "status": "published", "publish_date": "2024-01-20", "view_count": 850, "featured": false}
{"index": {"_id": "3"}}
{"title": "Python Programming Basics", "content": "Introduction to Python programming language and basic concepts", "author": "alice", "tags": ["python", "programming"], "category": "programming", "status": "published", "publish_date": "2024-01-10", "view_count": 2100, "featured": true}
'
```

### Complex Search Scenarios

**1. Featured posts about Elasticsearch:**
```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"content": "elasticsearch"}}
      ],
      "filter": [
        {"term": {"featured": true}},
        {"term": {"status": "published"}}
      ]
    }
  }
}
'
```

**2. Popular posts by specific author:**
```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"author": "jane"}},
        {"range": {"view_count": {"gte": 1000}}}
      ]
    }
  },
  "sort": [{"view_count": {"order": "desc"}}]
}
'
```

**3. Recent posts with fuzzy title search:**
```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "title": {
              "query": "elasticsearh tutorial",  // Typo
              "fuzziness": "AUTO"
            }
          }
        }
      ],
      "filter": [
        {"range": {"publish_date": {"gte": "now-30d"}}}
      ]
    }
  }
}
'
```

**4. Multi-category search with boosting:**
```bash
curl -X GET "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "should": [
        {"term": {"category": {"value": "technology", "boost": 2.0}}},
        {"term": {"category": "programming"}}
      ],
      "minimum_should_match": 1,
      "filter": [
        {"term": {"status": "published"}}
      ]
    }
  }
}
'
```

## 🚀 Performance Considerations

### Use Filters for Exact Matches

```bash
# ✅ Good: Use filter for exact matches (cacheable)
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"status": "published"}}
      ]
    }
  }
}

# ❌ Bad: Use query for exact matches (not cacheable)
{
  "query": {
    "term": {"status": "published"}
  }
}
```

### Optimize Bool Queries

```bash
# ✅ Good: Put cheaper filters first
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"status": "published"}},      // Cheap
        {"range": {"view_count": {"gte": 100}}}, // More expensive
        {"geo_distance": {...}}                  // Most expensive
      ]
    }
  }
}
```

### Avoid Expensive Queries

```bash
# ❌ Expensive: Leading wildcards
{"wildcard": {"title": "*elasticsearch"}}

# ❌ Expensive: Large fuzzy distance
{"fuzzy": {"title": {"value": "test", "fuzziness": 5}}}

# ✅ Better: Use appropriate analyzers and proper field types
```

### Use Query String Sparingly

```bash
# ⚠️ Use carefully: query_string (can be slow and error-prone)
{
  "query": {
    "query_string": {
      "query": "elasticsearch AND (tutorial OR guide)",
      "fields": ["title", "content"]
    }
  }
}

# ✅ Better: Use structured queries
{
  "query": {
    "bool": {
      "must": [
        {"match": {"content": "elasticsearch"}}
      ],
      "should": [
        {"match": {"content": "tutorial"}},
        {"match": {"content": "guide"}}
      ]
    }
  }
}
```

## 🔗 Next Steps

Now that you understand Query DSL basics, let's explore how to use them effectively:

1. **[Search Operations](search-operations.md)** - Learn the Search API and request structure
2. **[Filtering & Sorting](filtering-sorting.md)** - Master result refinement techniques
3. **[Full-text Search](../04-advanced-search/full-text-search.md)** - Advanced text search patterns

## 📚 Key Takeaways

- ✅ **Understand query vs filter context** for proper scoring and performance
- ✅ **Use full-text queries** for analyzed text fields
- ✅ **Use term-level queries** for exact matches and structured data
- ✅ **Master bool queries** to combine multiple conditions
- ✅ **Apply filters for better performance** on exact matches
- ✅ **Choose appropriate query types** based on your use case
- ✅ **Structure complex queries** using compound queries
- ✅ **Consider performance implications** of different query types

Ready to learn search operations? Continue with [Search Operations](search-operations.md) to master the Search API!