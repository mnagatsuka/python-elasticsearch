# Filtering & Sorting

**Refine and order search results for optimal user experience**

*Estimated reading time: 20 minutes*

## Overview

Filtering and sorting are essential for creating useful search applications. This guide covers how to filter results precisely, implement various sorting strategies, and combine them effectively for optimal user experience and performance.

## 📋 Table of Contents

1. [Filtering Fundamentals](#filtering-fundamentals)
2. [Sort Strategies](#sort-strategies)
3. [Combined Filtering & Sorting](#combined-filtering--sorting)
4. [Performance Considerations](#performance-considerations)
5. [Real-world Examples](#real-world-examples)
6. [Best Practices](#best-practices)

## 🔍 Filtering Fundamentals

### Filter vs Query Context

Understanding when to use filters vs queries is crucial for performance:

```bash
# ✅ Use filters for exact matches (cacheable, no scoring)
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"description": "wireless headphones"}}  // Query context (scored)
      ],
      "filter": [
        {"term": {"in_stock": true}},                      // Filter context (cached)
        {"range": {"price": {"gte": 50, "lte": 200}}},     // Filter context (cached)
        {"term": {"brand": "sony"}}                        // Filter context (cached)
      ]
    }
  }
}
'
```

### Common Filter Types

**Term Filter (Exact Match):**
```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"category": "electronics"}},
        {"term": {"status": "published"}}
      ]
    }
  }
}
'
```

**Terms Filter (Multiple Values):**
```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"terms": {"brand": ["apple", "samsung", "sony"]}},
        {"terms": {"color": ["black", "white", "silver"]}}
      ]
    }
  }
}
'
```

**Range Filter:**
```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "price": {
              "gte": 100,
              "lte": 500
            }
          }
        },
        {
          "range": {
            "created_date": {
              "gte": "2024-01-01",
              "lte": "now"
            }
          }
        }
      ]
    }
  }
}
'
```

**Exists Filter:**
```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"exists": {"field": "discount_price"}},    // Has discount
        {"exists": {"field": "images"}}             // Has images
      ]
    }
  }
}
'
```

**Missing Values Filter:**
```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must_not": [
        {"exists": {"field": "discontinued_date"}}  // Not discontinued
      ]
    }
  }
}
'
```

**Geo Distance Filter:**
```bash
curl -X POST "localhost:9200/stores/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {
          "geo_distance": {
            "distance": "10km",
            "location": {
              "lat": 40.7128,
              "lon": -74.0060
            }
          }
        }
      ]
    }
  }
}
'
```

### Complex Filter Combinations

**Nested Boolean Logic:**
```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {
          "bool": {
            "should": [
              {"term": {"category": "electronics"}},
              {"term": {"category": "accessories"}}
            ]
          }
        },
        {
          "bool": {
            "must": [
              {"range": {"price": {"gte": 50}}},
              {"term": {"in_stock": true}}
            ]
          }
        }
      ]
    }
  }
}
'
```

**Date Range with Math:**
```bash
curl -X POST "localhost:9200/events/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {
          "range": {
            "event_date": {
              "gte": "now/d",           // Today, start of day
              "lte": "now+7d/d"         // 7 days from now, end of day
            }
          }
        }
      ]
    }
  }
}
'
```

## 📊 Sort Strategies

### Basic Sorting

**Single Field Sort:**
```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "sort": [
    {"price": {"order": "asc"}}
  ]
}
'
```

**Multiple Field Sort:**
```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "sort": [
    {"category": {"order": "asc"}},      // Primary sort
    {"price": {"order": "asc"}},         // Secondary sort
    {"created_date": {"order": "desc"}}  // Tertiary sort
  ]
}
'
```

### Sort by Score

```bash
# Default: sort by relevance score
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"description": "wireless headphones"}
  }
}
'

# Explicit score sorting
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {"description": "wireless headphones"}
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"price": {"order": "asc"}}
  ]
}
'
```

### Sort with Missing Values

```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "sort": [
    {
      "discount_price": {
        "order": "asc",
        "missing": "_last"  // Options: "_first", "_last", or custom value
      }
    }
  ]
}
'
```

### Nested Field Sorting

```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "sort": [
    {
      "reviews.rating": {
        "order": "desc",
        "nested": {
          "path": "reviews",
          "filter": {
            "range": {
              "reviews.date": {
                "gte": "2024-01-01"
              }
            }
          }
        },
        "mode": "avg"  // Options: min, max, avg, sum
      }
    }
  ]
}
'
```

### Script-based Sorting

```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "sort": [
    {
      "_script": {
        "type": "number",
        "script": {
          "source": "doc['\''price'\''].value * (1 - doc['\''discount'\''].value)"
        },
        "order": "desc"
      }
    }
  ]
}
'
```

### Geo Distance Sorting

```bash
curl -X POST "localhost:9200/stores/_search" -H 'Content-Type: application/json' -d'
{
  "query": {"match_all": {}},
  "sort": [
    {
      "_geo_distance": {
        "location": {
          "lat": 40.7128,
          "lon": -74.0060
        },
        "order": "asc",
        "unit": "km",
        "distance_type": "arc"
      }
    }
  ]
}
'
```

## 🔄 Combined Filtering & Sorting

### E-commerce Product Listing

```bash
# Products: filter by category, price range, and availability; sort by relevance and price
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "wireless bluetooth",
            "fields": ["name^3", "description", "brand^2"],
            "type": "best_fields"
          }
        }
      ],
      "filter": [
        {"term": {"category": "electronics"}},
        {"term": {"in_stock": true}},
        {"range": {"price": {"gte": 50, "lte": 300}}},
        {"term": {"condition": "new"}}
      ]
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},        // Relevance first
    {"rating": {"order": "desc"}},        // Then by rating
    {"price": {"order": "asc"}}          // Then by price
  ],
  "from": 0,
  "size": 20
}
'
```

### Blog Post Search

```bash
# Blog posts: filter by publication status and date; sort by publication date
curl -X POST "localhost:9200/blog/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "content": "elasticsearch tutorial"
          }
        }
      ],
      "filter": [
        {"term": {"status": "published"}},
        {"term": {"featured": true}},
        {
          "range": {
            "publish_date": {
              "gte": "2023-01-01",
              "lte": "now"
            }
          }
        }
      ]
    }
  },
  "sort": [
    {"publish_date": {"order": "desc"}},
    {"_score": {"order": "desc"}}
  ]
}
'
```

### Event Search with Location

```bash
# Events: filter by date and location; sort by date and distance
curl -X POST "localhost:9200/events/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"title": "conference"}}
      ],
      "filter": [
        {
          "range": {
            "start_date": {
              "gte": "now",
              "lte": "now+30d"
            }
          }
        },
        {
          "geo_distance": {
            "distance": "50km",
            "location": {
              "lat": 40.7128,
              "lon": -74.0060
            }
          }
        }
      ]
    }
  },
  "sort": [
    {"start_date": {"order": "asc"}},
    {
      "_geo_distance": {
        "location": {"lat": 40.7128, "lon": -74.0060},
        "order": "asc",
        "unit": "km"
      }
    }
  ]
}
'
```

## ⚡ Performance Considerations

### Filter Performance

**Order Filters by Selectivity:**
```bash
# ✅ Good: Most selective filters first
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"user_id": "12345"}},          // Very selective
        {"term": {"status": "active"}},          // Moderately selective  
        {"range": {"created_date": {"gte": "2024-01-01"}}}  // Less selective
      ]
    }
  }
}
```

**Use Constant Score for Filter-only Queries:**
```bash
# ✅ Good: When you don't need scoring
{
  "query": {
    "constant_score": {
      "filter": {
        "bool": {
          "must": [
            {"term": {"category": "electronics"}},
            {"range": {"price": {"gte": 100}}}
          ]
        }
      }
    }
  }
}
```

### Sort Performance

**Use Doc Values Fields:**
```bash
# ✅ Good: Sort on keyword fields (doc values enabled)
{
  "sort": [
    {"category": {"order": "asc"}},     // keyword field
    {"price": {"order": "asc"}}         // numeric field
  ]
}

# ❌ Bad: Sort on analyzed text fields
{
  "sort": [
    {"title": {"order": "asc"}}         // text field - expensive
  ]
}
```

**Limit Sort Fields:**
```bash
# ✅ Good: Minimal sort criteria
{
  "sort": [
    {"date": {"order": "desc"}},
    {"_id": {"order": "asc"}}  // Tiebreaker
  ]
}

# ❌ Bad: Too many sort fields
{
  "sort": [
    {"field1": {"order": "desc"}},
    {"field2": {"order": "desc"}},
    {"field3": {"order": "desc"}},
    {"field4": {"order": "desc"}}
  ]
}
```

### Memory Optimization

```bash
# Use track_total_hits wisely
{
  "query": {"match_all": {}},
  "track_total_hits": 100,  // Only accurate up to 100
  "size": 10
}

# Disable source when not needed
{
  "query": {"match_all": {}},
  "_source": false,
  "stored_fields": ["id", "title"]
}
```

## 🎯 Real-world Examples

### Faceted Search Implementation

```bash
# E-commerce faceted search with filters and aggregations
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"name": "laptop"}}
      ],
      "filter": [
        {"terms": {"brand": ["apple", "dell"]}},
        {"range": {"price": {"gte": 500, "lte": 2000}}},
        {"term": {"in_stock": true}}
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
          {"to": 500},
          {"from": 500, "to": 1000},
          {"from": 1000, "to": 2000},
          {"from": 2000}
        ]
      }
    },
    "avg_rating": {
      "avg": {"field": "rating"}
    }
  },
  "sort": [
    {"_score": {"order": "desc"}},
    {"rating": {"order": "desc"}},
    {"price": {"order": "asc"}}
  ],
  "size": 20
}
'
```

### Time-series Data Filtering

```bash
# Log analysis with time-based filtering and sorting
curl -X POST "localhost:9200/logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"match": {"message": "error"}}
      ],
      "filter": [
        {"term": {"level": "ERROR"}},
        {"term": {"service": "payment-service"}},
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
  "sort": [
    {"@timestamp": {"order": "desc"}}
  ],
  "aggs": {
    "error_timeline": {
      "date_histogram": {
        "field": "@timestamp",
        "interval": "5m"
      }
    }
  },
  "size": 100
}
'
```

### User Activity Analysis

```bash
# Filter and sort user activities
curl -X POST "localhost:9200/user_activities/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"user_id": "user123"}},
        {"terms": {"action": ["login", "purchase", "view"]}},
        {
          "range": {
            "timestamp": {
              "gte": "now-7d",
              "lte": "now"
            }
          }
        }
      ]
    }
  },
  "sort": [
    {"timestamp": {"order": "desc"}}
  ],
  "aggs": {
    "actions": {
      "terms": {"field": "action"}
    },
    "daily_activity": {
      "date_histogram": {
        "field": "timestamp",
        "interval": "1d"
      }
    }
  }
}
'
```

## 🚀 Best Practices

### Filter Design

```bash
# ✅ Good: Use appropriate field types
{
  "filter": [
    {"term": {"status": "published"}},           // keyword field
    {"range": {"price": {"gte": 100}}},          // numeric field  
    {"range": {"date": {"gte": "2024-01-01"}}}   // date field
  ]
}

# ❌ Bad: Wrong field types
{
  "filter": [
    {"match": {"status": "published"}},          // analyzed text query
    {"term": {"description": "electronics"}}     // analyzed text field
  ]
}
```

### Sort Strategy

```bash
# ✅ Good: Logical sort order
{
  "sort": [
    {"featured": {"order": "desc"}},     // Featured items first
    {"_score": {"order": "desc"}},       // Then by relevance
    {"price": {"order": "asc"}}          // Then by price
  ]
}

# ✅ Good: Consistent tiebreakers
{
  "sort": [
    {"date": {"order": "desc"}},
    {"_id": {"order": "asc"}}            // Ensures consistent ordering
  ]
}
```

### Performance Optimization

```bash
# ✅ Good: Use post_filter for faceted search
{
  "query": {
    "match": {"name": "laptop"}
  },
  "post_filter": {
    "term": {"brand": "apple"}
  },
  "aggs": {
    "all_brands": {
      "terms": {"field": "brand"}        // Shows all brands, not just filtered
    }
  }
}
```

## ❌ Common Pitfalls

### Inefficient Filtering

```bash
# ❌ Bad: Using query context for exact matches
{
  "query": {
    "bool": {
      "must": [
        {"term": {"status": "published"}},    // Should be in filter
        {"term": {"category": "electronics"}} // Should be in filter
      ]
    }
  }
}

# ✅ Good: Use filter context
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"status": "published"}},
        {"term": {"category": "electronics"}}
      ]
    }
  }
}
```

### Expensive Sorting

```bash
# ❌ Bad: Sorting on analyzed text
{
  "sort": [
    {"title": {"order": "asc"}}          // Analyzed text field
  ]
}

# ✅ Good: Sort on keyword subfield
{
  "sort": [
    {"title.keyword": {"order": "asc"}}  // Keyword subfield
  ]
}
```

## 🔗 Next Steps

Now that you've mastered filtering and sorting, let's explore advanced search capabilities:

1. **[Full-text Search](../04-advanced-search/full-text-search.md)** - Advanced text search patterns
2. **[Aggregations](../04-advanced-search/aggregations.md)** - Analyze and summarize your data
3. **[Relevance Scoring](../04-advanced-search/relevance-scoring.md)** - Control search result ranking

## 📚 Key Takeaways

- ✅ **Use filter context** for exact matches and better performance
- ✅ **Order filters** by selectivity (most selective first)
- ✅ **Choose appropriate sort fields** (use keyword fields, not analyzed text)
- ✅ **Combine multiple sort criteria** logically for best user experience
- ✅ **Include tiebreakers** for consistent pagination
- ✅ **Consider performance implications** of complex filters and sorts
- ✅ **Use post_filter** for faceted search scenarios
- ✅ **Test filter combinations** with your actual data patterns

Ready to dive into advanced search? Continue with [Full-text Search](../04-advanced-search/full-text-search.md) to master text analysis and search patterns!