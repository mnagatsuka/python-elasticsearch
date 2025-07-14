# Sample Queries

**Copy-paste ready Elasticsearch queries for common use cases**

*Estimated reading time: 20 minutes*

## Overview

This collection provides ready-to-use Elasticsearch queries covering the most common search scenarios. All examples are production-tested and can be copied directly into your applications.

## 📋 Table of Contents

1. [Basic Search Queries](#basic-search-queries)
2. [Text Search Queries](#text-search-queries)
3. [Filter Queries](#filter-queries)
4. [Aggregation Queries](#aggregation-queries)
5. [Date Range Queries](#date-range-queries)
6. [Geospatial Queries](#geospatial-queries)
7. [Advanced Queries](#advanced-queries)

## 🔍 Basic Search Queries

### Match All Documents

```json
{
  "query": {
    "match_all": {}
  }
}
```

### Get Specific Document by ID

```json
{
  "query": {
    "ids": {
      "values": ["doc_id_1", "doc_id_2"]
    }
  }
}
```

### Simple Term Match

```json
{
  "query": {
    "term": {
      "status": "published"
    }
  }
}
```

### Multiple Terms Match

```json
{
  "query": {
    "terms": {
      "category": ["technology", "science", "programming"]
    }
  }
}
```

### Range Query

```json
{
  "query": {
    "range": {
      "price": {
        "gte": 10,
        "lte": 100
      }
    }
  }
}
```

## 📝 Text Search Queries

### Simple Text Search

```json
{
  "query": {
    "match": {
      "title": "elasticsearch tutorial"
    }
  }
}
```

### Multi-Field Text Search

```json
{
  "query": {
    "multi_match": {
      "query": "machine learning",
      "fields": ["title^2", "content", "tags"]
    }
  }
}
```

### Phrase Search

```json
{
  "query": {
    "match_phrase": {
      "content": "artificial intelligence"
    }
  }
}
```

### Fuzzy Search (Typo Tolerance)

```json
{
  "query": {
    "match": {
      "title": {
        "query": "elasticserch",
        "fuzziness": "AUTO"
      }
    }
  }
}
```

### Prefix Search

```json
{
  "query": {
    "prefix": {
      "title": "elast"
    }
  }
}
```

### Wildcard Search

```json
{
  "query": {
    "wildcard": {
      "email": "*@gmail.com"
    }
  }
}
```

## 🔧 Filter Queries

### Bool Query with Multiple Conditions

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"category": "technology"}},
        {"range": {"publish_date": {"gte": "2024-01-01"}}}
      ],
      "must_not": [
        {"term": {"status": "draft"}}
      ],
      "should": [
        {"match": {"tags": "featured"}},
        {"match": {"tags": "trending"}}
      ],
      "minimum_should_match": 1
    }
  }
}
```

### Filter Context (No Scoring)

```json
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"status": "published"}},
        {"range": {"price": {"gte": 10}}},
        {"exists": {"field": "description"}}
      ]
    }
  }
}
```

### Nested Object Query

```json
{
  "query": {
    "nested": {
      "path": "reviews",
      "query": {
        "bool": {
          "must": [
            {"range": {"reviews.rating": {"gte": 4}}},
            {"match": {"reviews.comment": "excellent"}}
          ]
        }
      }
    }
  }
}
```

### Exists Query (Non-null Values)

```json
{
  "query": {
    "exists": {
      "field": "description"
    }
  }
}
```

## 📊 Aggregation Queries

### Terms Aggregation (Group By)

```json
{
  "size": 0,
  "aggs": {
    "categories": {
      "terms": {
        "field": "category",
        "size": 10
      }
    }
  }
}
```

### Date Histogram

```json
{
  "size": 0,
  "aggs": {
    "sales_over_time": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "month"
      },
      "aggs": {
        "total_sales": {
          "sum": {
            "field": "amount"
          }
        }
      }
    }
  }
}
```

### Statistical Aggregations

```json
{
  "size": 0,
  "aggs": {
    "price_stats": {
      "stats": {
        "field": "price"
      }
    },
    "price_percentiles": {
      "percentiles": {
        "field": "price",
        "percents": [25, 50, 75, 95, 99]
      }
    }
  }
}
```

### Range Aggregation

```json
{
  "size": 0,
  "aggs": {
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
  }
}
```

### Nested Aggregations

```json
{
  "size": 0,
  "aggs": {
    "categories": {
      "terms": {
        "field": "category"
      },
      "aggs": {
        "avg_price": {
          "avg": {
            "field": "price"
          }
        },
        "brands": {
          "terms": {
            "field": "brand",
            "size": 5
          }
        }
      }
    }
  }
}
```

## 📅 Date Range Queries

### Last 24 Hours

```json
{
  "query": {
    "range": {
      "timestamp": {
        "gte": "now-24h"
      }
    }
  }
}
```

### Specific Date Range

```json
{
  "query": {
    "range": {
      "publish_date": {
        "gte": "2024-01-01",
        "lte": "2024-12-31",
        "format": "yyyy-MM-dd"
      }
    }
  }
}
```

### Relative Date Ranges

```json
{
  "query": {
    "bool": {
      "should": [
        {"range": {"created_at": {"gte": "now-1d", "lte": "now"}}},
        {"range": {"updated_at": {"gte": "now-7d", "lte": "now-1d"}}}
      ]
    }
  }
}
```

### Date Math Examples

```json
{
  "query": {
    "range": {
      "timestamp": {
        "gte": "now-1M/M",  // Start of last month
        "lte": "now/M"      // Start of current month
      }
    }
  }
}
```

## 🌍 Geospatial Queries

### Geo Distance Query

```json
{
  "query": {
    "geo_distance": {
      "distance": "10km",
      "location": {
        "lat": 40.7128,
        "lon": -74.0060
      }
    }
  }
}
```

### Geo Bounding Box

```json
{
  "query": {
    "geo_bounding_box": {
      "location": {
        "top_left": {
          "lat": 40.8,
          "lon": -74.1
        },
        "bottom_right": {
          "lat": 40.7,
          "lon": -74.0
        }
      }
    }
  }
}
```

### Geo Polygon Query

```json
{
  "query": {
    "geo_polygon": {
      "location": {
        "points": [
          {"lat": 40.8, "lon": -74.1},
          {"lat": 40.8, "lon": -74.0},
          {"lat": 40.7, "lon": -74.0},
          {"lat": 40.7, "lon": -74.1}
        ]
      }
    }
  }
}
```

## 🚀 Advanced Queries

### Function Score Query

```json
{
  "query": {
    "function_score": {
      "query": {
        "match": {"title": "elasticsearch"}
      },
      "functions": [
        {
          "field_value_factor": {
            "field": "popularity",
            "factor": 0.1,
            "modifier": "log1p"
          }
        },
        {
          "filter": {"match": {"featured": true}},
          "weight": 2
        }
      ],
      "score_mode": "sum",
      "boost_mode": "multiply"
    }
  }
}
```

### Script Query

```json
{
  "query": {
    "script": {
      "script": {
        "source": "doc['price'].value > params.min_price && doc['rating'].value >= params.min_rating",
        "params": {
          "min_price": 100,
          "min_rating": 4.0
        }
      }
    }
  }
}
```

### More Like This Query

```json
{
  "query": {
    "more_like_this": {
      "fields": ["title", "content"],
      "like": [
        {
          "_index": "articles",
          "_id": "1"
        }
      ],
      "min_term_freq": 1,
      "min_doc_freq": 1
    }
  }
}
```

### Pinned Query (Promote Specific Results)

```json
{
  "query": {
    "pinned": {
      "ids": ["featured_1", "featured_2"],
      "organic": {
        "match": {
          "content": "search query"
        }
      }
    }
  }
}
```

### Highlight Search Results

```json
{
  "query": {
    "match": {
      "content": "elasticsearch"
    }
  },
  "highlight": {
    "fields": {
      "content": {
        "fragment_size": 150,
        "number_of_fragments": 3
      }
    }
  }
}
```

### Search with Suggestions

```json
{
  "query": {
    "match": {
      "title": "elasticsearh"  // Typo
    }
  },
  "suggest": {
    "title_suggestion": {
      "text": "elasticsearh",
      "term": {
        "field": "title"
      }
    }
  }
}
```

## 🔀 Search Templates

### Create Search Template

```json
PUT _scripts/product_search
{
  "script": {
    "lang": "mustache",
    "source": {
      "query": {
        "bool": {
          "must": [
            {"match": {"{{field}}": "{{query}}"}}
          ],
          "filter": [
            {"range": {"price": {"gte": "{{min_price||}}", "lte": "{{max_price||}}"}}}
          ]
        }
      },
      "size": "{{size||10}}"
    }
  }
}
```

### Use Search Template

```json
{
  "id": "product_search",
  "params": {
    "field": "name",
    "query": "smartphone",
    "min_price": 100,
    "max_price": 1000,
    "size": 20
  }
}
```

## 📖 Query Combinations

### E-commerce Product Search

```json
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
        {"range": {"price": {"gte": 50, "lte": 300}}},
        {"terms": {"category": ["electronics", "audio"]}}
      ]
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"popularity": {"order": "desc"}}
  ],
  "aggs": {
    "brands": {
      "terms": {"field": "brand", "size": 10}
    },
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          {"key": "Under $100", "to": 100},
          {"key": "$100-$200", "from": 100, "to": 200},
          {"key": "Over $200", "from": 200}
        ]
      }
    }
  }
}
```

### Log Analysis Query

```json
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1h"}}},
        {"term": {"level": "ERROR"}}
      ],
      "should": [
        {"match": {"message": "database"}},
        {"match": {"message": "timeout"}}
      ]
    }
  },
  "aggs": {
    "error_timeline": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "5m"
      }
    },
    "top_errors": {
      "terms": {
        "field": "error_type",
        "size": 10
      }
    }
  }
}
```

### User Activity Analysis

```json
{
  "query": {
    "bool": {
      "filter": [
        {"range": {"timestamp": {"gte": "now-7d"}}},
        {"term": {"event_type": "page_view"}}
      ]
    }
  },
  "aggs": {
    "daily_activity": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "day"
      },
      "aggs": {
        "unique_users": {
          "cardinality": {"field": "user_id"}
        },
        "page_views": {
          "sum": {"field": "view_count"}
        }
      }
    },
    "top_pages": {
      "terms": {
        "field": "page_url",
        "size": 20
      }
    }
  }
}
```

## 💡 Query Optimization Tips

### Use Filter Context When Possible

```json
// ✅ Good - Uses filter context (cacheable, no scoring)
{
  "query": {
    "bool": {
      "must": [
        {"match": {"title": "search term"}}
      ],
      "filter": [
        {"term": {"status": "published"}},
        {"range": {"date": {"gte": "2024-01-01"}}}
      ]
    }
  }
}

// ❌ Less optimal - Everything in must (scoring overhead)
{
  "query": {
    "bool": {
      "must": [
        {"match": {"title": "search term"}},
        {"term": {"status": "published"}},
        {"range": {"date": {"gte": "2024-01-01"}}}
      ]
    }
  }
}
```

### Limit Source Fields

```json
{
  "query": {"match_all": {}},
  "_source": ["title", "summary", "date"],
  // or exclude large fields
  "_source": {
    "excludes": ["full_content", "metadata"]
  }
}
```

### Use Search After for Deep Pagination

```json
{
  "query": {"match_all": {}},
  "sort": [
    {"date": "desc"},
    {"_id": "desc"}
  ],
  "search_after": ["2024-01-15T10:30:00", "doc_123"],
  "size": 20
}
```

## 🔗 Related Documentation

- **[Query DSL Basics](../03-search-fundamentals/01_query-dsl-basics.md)** - Understanding query structure
- **[Search Operations](../03-search-fundamentals/02_search-operations.md)** - Search API details
- **[Aggregations](../04-advanced-search/02_aggregations.md)** - Advanced analytics
- **[Performance Optimization](../06-performance-production/01_optimization-strategies.md)** - Query performance tuning

## 📚 Quick Reference

### Most Common Query Patterns

1. **Text Search**: `match`, `multi_match`, `match_phrase`
2. **Exact Matches**: `term`, `terms`, `exists`
3. **Ranges**: `range` for numbers, dates, geo coordinates
4. **Combinations**: `bool` query with `must`, `should`, `must_not`, `filter`
5. **Analytics**: Date histograms, terms aggregations, metrics

### Performance Best Practices

- Use `filter` context for exact matches
- Limit `_source` fields in responses
- Use `search_after` instead of `from`/`size` for deep pagination
- Cache filter queries when possible
- Use appropriate field types in mappings

Ready to implement these queries in your application? Copy any example and adapt it to your specific use case!