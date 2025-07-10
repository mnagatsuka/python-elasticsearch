# Aggregations

**Analyze and summarize data with powerful analytics operations**

*Estimated reading time: 40 minutes*

## Overview

Aggregations are Elasticsearch's analytics framework, allowing you to group, calculate, and analyze data in real-time. This guide covers metric aggregations, bucket aggregations, pipeline aggregations, and advanced patterns for building dashboards and reports.

## 📋 Table of Contents

1. [Aggregation Fundamentals](#aggregation-fundamentals)
2. [Metric Aggregations](#metric-aggregations)
3. [Bucket Aggregations](#bucket-aggregations)
4. [Pipeline Aggregations](#pipeline-aggregations)
5. [Advanced Patterns](#advanced-patterns)
6. [Performance Optimization](#performance-optimization)
7. [Real-world Examples](#real-world-examples)

## 📊 Aggregation Fundamentals

### Basic Aggregation Structure

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,  // Don'\''t return documents, only aggregations
  "aggs": {
    "aggregation_name": {
      "aggregation_type": {
        "field": "field_name"
      }
    }
  }
}
'
```

### Aggregation Response Structure

```json
{
  "hits": {
    "total": {"value": 1000},
    "hits": []
  },
  "aggregations": {
    "aggregation_name": {
      "value": 12345,
      "buckets": [],
      "doc_count": 100
    }
  }
}
```

### Setup Sample Data

```bash
# Create sales index with sample data
curl -X PUT "localhost:9200/sales" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "product": {"type": "keyword"},
      "category": {"type": "keyword"},
      "brand": {"type": "keyword"},
      "price": {"type": "float"},
      "quantity": {"type": "integer"},
      "revenue": {"type": "float"},
      "date": {"type": "date"},
      "customer_age": {"type": "integer"},
      "region": {"type": "keyword"},
      "salesperson": {"type": "keyword"}
    }
  }
}
'

# Add sample data
curl -X POST "localhost:9200/sales/_bulk" -H 'Content-Type: application/json' -d'
{"index": {}}
{"product": "Laptop", "category": "Electronics", "brand": "Apple", "price": 1299.99, "quantity": 2, "revenue": 2599.98, "date": "2024-01-15", "customer_age": 32, "region": "North", "salesperson": "John"}
{"index": {}}
{"product": "Mouse", "category": "Electronics", "brand": "Logitech", "price": 29.99, "quantity": 5, "revenue": 149.95, "date": "2024-01-15", "customer_age": 28, "region": "South", "salesperson": "Jane"}
{"index": {}}
{"product": "Book", "category": "Education", "brand": "Penguin", "price": 19.99, "quantity": 3, "revenue": 59.97, "date": "2024-01-16", "customer_age": 45, "region": "East", "salesperson": "Bob"}
{"index": {}}
{"product": "Headphones", "category": "Electronics", "brand": "Sony", "price": 199.99, "quantity": 1, "revenue": 199.99, "date": "2024-01-17", "customer_age": 25, "region": "West", "salesperson": "Alice"}
'
```

## 📈 Metric Aggregations

Calculate statistics on numeric fields.

### Basic Metrics

**Average:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "avg_price": {
      "avg": {"field": "price"}
    },
    "avg_revenue": {
      "avg": {"field": "revenue"}
    }
  }
}
'
```

**Sum:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "total_revenue": {
      "sum": {"field": "revenue"}
    },
    "total_quantity": {
      "sum": {"field": "quantity"}
    }
  }
}
'
```

**Min/Max:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "min_price": {
      "min": {"field": "price"}
    },
    "max_price": {
      "max": {"field": "price"}
    },
    "price_range": {
      "stats": {"field": "price"}  // Returns min, max, avg, sum, count
    }
  }
}
'
```

### Extended Stats

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "price_extended_stats": {
      "extended_stats": {
        "field": "price",
        "sigma": 2  // Standard deviation multiplier
      }
    }
  }
}
'
```

**Response includes:**
- count, min, max, avg, sum
- sum_of_squares, variance, std_deviation
- std_deviation_bounds (upper/lower)

### Percentiles and Ranks

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "price_percentiles": {
      "percentiles": {
        "field": "price",
        "percents": [25, 50, 75, 90, 95, 99]
      }
    },
    "price_percentile_ranks": {
      "percentile_ranks": {
        "field": "price",
        "values": [50, 100, 200, 500]
      }
    }
  }
}
'
```

### Cardinality (Unique Count)

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "unique_customers": {
      "cardinality": {
        "field": "customer_id",
        "precision_threshold": 3000  // Trade accuracy for performance
      }
    },
    "unique_products": {
      "cardinality": {"field": "product"}
    }
  }
}
'
```

### Value Count

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sales_count": {
      "value_count": {"field": "revenue"}
    }
  }
}
'
```

## 🪣 Bucket Aggregations

Group documents into buckets based on criteria.

### Terms Aggregation

**Basic Terms:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "top_categories": {
      "terms": {
        "field": "category",
        "size": 10,
        "order": {"_count": "desc"}
      }
    }
  }
}
'
```

**Terms with Sub-aggregations:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "categories": {
      "terms": {"field": "category"},
      "aggs": {
        "total_revenue": {
          "sum": {"field": "revenue"}
        },
        "avg_price": {
          "avg": {"field": "price"}
        },
        "top_brands": {
          "terms": {
            "field": "brand",
            "size": 3
          }
        }
      }
    }
  }
}
'
```

### Range Aggregations

**Numeric Range:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          {"to": 50},
          {"from": 50, "to": 200},
          {"from": 200, "to": 500},
          {"from": 500}
        ]
      },
      "aggs": {
        "sales_in_range": {
          "sum": {"field": "revenue"}
        }
      }
    }
  }
}
'
```

**Date Range:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sales_periods": {
      "date_range": {
        "field": "date",
        "ranges": [
          {"to": "2024-01-15"},
          {"from": "2024-01-15", "to": "2024-01-20"},
          {"from": "2024-01-20"}
        ]
      }
    }
  }
}
'
```

### Date Histogram

**Time-based Buckets:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sales_over_time": {
      "date_histogram": {
        "field": "date",
        "calendar_interval": "day",
        "time_zone": "America/New_York",
        "min_doc_count": 1
      },
      "aggs": {
        "daily_revenue": {
          "sum": {"field": "revenue"}
        },
        "unique_customers": {
          "cardinality": {"field": "customer_id"}
        }
      }
    }
  }
}
'
```

**Fixed Interval:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "hourly_sales": {
      "date_histogram": {
        "field": "timestamp",
        "fixed_interval": "1h",
        "extended_bounds": {
          "min": "2024-01-01T00:00:00",
          "max": "2024-01-31T23:59:59"
        }
      }
    }
  }
}
'
```

### Histogram

**Numeric Histogram:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "price_distribution": {
      "histogram": {
        "field": "price",
        "interval": 100,
        "min_doc_count": 1
      }
    }
  }
}
'
```

### Filters Aggregation

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sales_segments": {
      "filters": {
        "filters": {
          "high_value": {"range": {"price": {"gte": 500}}},
          "medium_value": {"range": {"price": {"gte": 100, "lt": 500}}},
          "low_value": {"range": {"price": {"lt": 100}}}
        }
      },
      "aggs": {
        "segment_revenue": {
          "sum": {"field": "revenue"}
        }
      }
    }
  }
}
'
```

### Nested Aggregations

```bash
curl -X POST "localhost:9200/products/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "reviews_analysis": {
      "nested": {"path": "reviews"},
      "aggs": {
        "avg_rating": {
          "avg": {"field": "reviews.rating"}
        },
        "rating_distribution": {
          "histogram": {
            "field": "reviews.rating",
            "interval": 1
          }
        }
      }
    }
  }
}
'
```

## 🔄 Pipeline Aggregations

Calculate metrics on the outputs of other aggregations.

### Bucket Selectors

**Having Clause Equivalent:**
```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "categories": {
      "terms": {"field": "category"},
      "aggs": {
        "total_revenue": {
          "sum": {"field": "revenue"}
        },
        "high_revenue_filter": {
          "bucket_selector": {
            "buckets_path": {
              "totalRevenue": "total_revenue"
            },
            "script": "params.totalRevenue > 1000"
          }
        }
      }
    }
  }
}
'
```

### Moving Average

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sales_over_time": {
      "date_histogram": {
        "field": "date",
        "calendar_interval": "day"
      },
      "aggs": {
        "daily_sales": {
          "sum": {"field": "revenue"}
        },
        "moving_avg": {
          "moving_avg": {
            "buckets_path": "daily_sales",
            "window": 7,
            "model": "simple"
          }
        }
      }
    }
  }
}
'
```

### Derivative

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sales_over_time": {
      "date_histogram": {
        "field": "date",
        "calendar_interval": "day"
      },
      "aggs": {
        "daily_sales": {
          "sum": {"field": "revenue"}
        },
        "sales_growth": {
          "derivative": {
            "buckets_path": "daily_sales"
          }
        }
      }
    }
  }
}
'
```

### Cumulative Sum

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sales_over_time": {
      "date_histogram": {
        "field": "date",
        "calendar_interval": "day"
      },
      "aggs": {
        "daily_sales": {
          "sum": {"field": "revenue"}
        },
        "cumulative_sales": {
          "cumulative_sum": {
            "buckets_path": "daily_sales"
          }
        }
      }
    }
  }
}
'
```

### Bucket Sort

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "categories": {
      "terms": {"field": "category", "size": 100},
      "aggs": {
        "total_revenue": {
          "sum": {"field": "revenue"}
        },
        "top_categories": {
          "bucket_sort": {
            "sort": [{"total_revenue": {"order": "desc"}}],
            "size": 5
          }
        }
      }
    }
  }
}
'
```

## 🎯 Advanced Patterns

### Multi-level Grouping

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "by_region": {
      "terms": {"field": "region"},
      "aggs": {
        "by_category": {
          "terms": {"field": "category"},
          "aggs": {
            "by_brand": {
              "terms": {"field": "brand"},
              "aggs": {
                "total_revenue": {"sum": {"field": "revenue"}},
                "avg_price": {"avg": {"field": "price"}},
                "total_quantity": {"sum": {"field": "quantity"}}
              }
            }
          }
        }
      }
    }
  }
}
'
```

### Composite Aggregations

For efficient pagination through large aggregation results:

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "my_composite": {
      "composite": {
        "size": 100,
        "sources": [
          {"region": {"terms": {"field": "region"}}},
          {"category": {"terms": {"field": "category"}}},
          {"date": {"date_histogram": {"field": "date", "calendar_interval": "month"}}}
        ]
      },
      "aggs": {
        "total_revenue": {"sum": {"field": "revenue"}}
      }
    }
  }
}
'

# Continue pagination using after
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "my_composite": {
      "composite": {
        "size": 100,
        "sources": [
          {"region": {"terms": {"field": "region"}}},
          {"category": {"terms": {"field": "category"}}},
          {"date": {"date_histogram": {"field": "date", "calendar_interval": "month"}}}
        ],
        "after": {"region": "North", "category": "Electronics", "date": 1704067200000}
      }
    }
  }
}
'
```

### Significant Terms

Find unusual or interesting terms:

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {"region": "North"}
  },
  "size": 0,
  "aggs": {
    "significant_brands": {
      "significant_terms": {
        "field": "brand",
        "size": 10,
        "min_doc_count": 3
      }
    }
  }
}
'
```

### Sampler Aggregation

Analyze a sample of data for performance:

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "sample": {
      "sampler": {
        "shard_size": 200
      },
      "aggs": {
        "keywords": {
          "significant_terms": {
            "field": "product",
            "size": 10
          }
        }
      }
    }
  }
}
'
```

## ⚡ Performance Optimization

### Doc Values and Fielddata

```bash
# Optimized mapping for aggregations
curl -X PUT "localhost:9200/optimized_sales" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "category": {
        "type": "keyword",
        "doc_values": true  // Enable for aggregations (default)
      },
      "description": {
        "type": "text",
        "fielddata": false  // Disable for large text fields
      },
      "tags": {
        "type": "keyword",
        "eager_global_ordinals": true  // Preload for frequent aggregations
      }
    }
  }
}
'
```

### Aggregation Optimization

```bash
# ✅ Good: Efficient aggregation order
{
  "aggs": {
    "categories": {
      "terms": {"field": "category", "size": 5},  // Limit buckets early
      "aggs": {
        "revenue": {"sum": {"field": "revenue"}}
      }
    }
  }
}

# ❌ Bad: Too many buckets
{
  "aggs": {
    "all_products": {
      "terms": {"field": "product", "size": 10000}  // Too many buckets
    }
  }
}
```

### Memory Considerations

```bash
# Use execution hints for large cardinality fields
{
  "aggs": {
    "user_ids": {
      "terms": {
        "field": "user_id",
        "size": 100,
        "execution_hint": "map"  // Options: map, global_ordinals
      }
    }
  }
}
```

## 🎯 Real-world Examples

### Sales Dashboard

```bash
curl -X POST "localhost:9200/sales/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "query": {
    "range": {
      "date": {
        "gte": "2024-01-01",
        "lte": "2024-01-31"
      }
    }
  },
  "aggs": {
    "summary_metrics": {
      "global": {},
      "aggs": {
        "total_revenue": {"sum": {"field": "revenue"}},
        "total_orders": {"value_count": {"field": "order_id"}},
        "avg_order_value": {"avg": {"field": "revenue"}},
        "unique_customers": {"cardinality": {"field": "customer_id"}}
      }
    },
    "revenue_over_time": {
      "date_histogram": {
        "field": "date",
        "calendar_interval": "day"
      },
      "aggs": {
        "daily_revenue": {"sum": {"field": "revenue"}},
        "daily_orders": {"value_count": {"field": "order_id"}}
      }
    },
    "top_categories": {
      "terms": {"field": "category", "size": 10},
      "aggs": {
        "category_revenue": {"sum": {"field": "revenue"}},
        "category_orders": {"value_count": {"field": "order_id"}},
        "top_products": {
          "terms": {"field": "product", "size": 5},
          "aggs": {
            "product_revenue": {"sum": {"field": "revenue"}}
          }
        }
      }
    },
    "regional_performance": {
      "terms": {"field": "region"},
      "aggs": {
        "region_revenue": {"sum": {"field": "revenue"}},
        "avg_customer_age": {"avg": {"field": "customer_age"}},
        "top_salesperson": {
          "terms": {"field": "salesperson", "size": 1}
        }
      }
    },
    "price_segments": {
      "range": {
        "field": "price",
        "ranges": [
          {"key": "Budget", "to": 50},
          {"key": "Mid-range", "from": 50, "to": 200},
          {"key": "Premium", "from": 200}
        ]
      },
      "aggs": {
        "segment_revenue": {"sum": {"field": "revenue"}},
        "segment_margin": {"avg": {"field": "profit_margin"}}
      }
    }
  }
}
'
```

### Website Analytics

```bash
curl -X POST "localhost:9200/web_analytics/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "query": {
    "range": {
      "timestamp": {
        "gte": "now-7d"
      }
    }
  },
  "aggs": {
    "traffic_overview": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "hour"
      },
      "aggs": {
        "page_views": {"value_count": {"field": "page"}},
        "unique_visitors": {"cardinality": {"field": "visitor_id"}},
        "bounce_rate": {
          "bucket_script": {
            "buckets_path": {
              "single_page": "single_page_sessions",
              "total": "total_sessions"
            },
            "script": "params.single_page / params.total * 100"
          }
        }
      }
    },
    "top_pages": {
      "terms": {"field": "page", "size": 20},
      "aggs": {
        "page_views": {"value_count": {"field": "page"}},
        "unique_visitors": {"cardinality": {"field": "visitor_id"}},
        "avg_time_on_page": {"avg": {"field": "time_on_page"}}
      }
    },
    "traffic_sources": {
      "terms": {"field": "referrer_domain"},
      "aggs": {
        "source_visitors": {"cardinality": {"field": "visitor_id"}},
        "conversion_rate": {
          "bucket_script": {
            "buckets_path": {
              "conversions": "conversions",
              "visitors": "source_visitors"
            },
            "script": "params.conversions / params.visitors * 100"
          }
        }
      }
    },
    "device_breakdown": {
      "terms": {"field": "device_type"},
      "aggs": {
        "os_breakdown": {
          "terms": {"field": "operating_system"}
        },
        "browser_breakdown": {
          "terms": {"field": "browser"}
        }
      }
    }
  }
}
'
```

### Log Analysis

```bash
curl -X POST "localhost:9200/logs-*/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-24h"
      }
    }
  },
  "aggs": {
    "log_levels": {
      "terms": {"field": "level"},
      "aggs": {
        "timeline": {
          "date_histogram": {
            "field": "@timestamp",
            "fixed_interval": "1h"
          }
        },
        "top_services": {
          "terms": {"field": "service", "size": 10}
        }
      }
    },
    "error_analysis": {
      "filter": {"term": {"level": "ERROR"}},
      "aggs": {
        "error_timeline": {
          "date_histogram": {
            "field": "@timestamp",
            "fixed_interval": "15m"
          },
          "aggs": {
            "error_rate": {
              "bucket_script": {
                "buckets_path": {
                  "errors": "_count"
                },
                "script": "params.errors"
              }
            }
          }
        },
        "top_error_messages": {
          "significant_terms": {
            "field": "message.keyword",
            "size": 10
          }
        },
        "affected_services": {
          "terms": {"field": "service"}
        }
      }
    },
    "response_time_analysis": {
      "range": {
        "field": "response_time",
        "ranges": [
          {"key": "Fast", "to": 100},
          {"key": "Normal", "from": 100, "to": 500},
          {"key": "Slow", "from": 500, "to": 2000},
          {"key": "Very Slow", "from": 2000}
        ]
      },
      "aggs": {
        "services_in_range": {
          "terms": {"field": "service"}
        }
      }
    }
  }
}
'
```

## 🔗 Next Steps

Now that you've mastered aggregations, let's explore relevance optimization:

1. **[Relevance Scoring](relevance-scoring.md)** - Fine-tune search result ranking
2. **[Vector Search](../05-modern-capabilities/vector-search.md)** - Modern semantic search capabilities
3. **[Performance Optimization](../06-performance-production/optimization-strategies.md)** - Scale your analytics

## 📚 Key Takeaways

- ✅ **Use appropriate aggregation types** for your analysis needs
- ✅ **Combine metric and bucket aggregations** for comprehensive analysis
- ✅ **Leverage pipeline aggregations** for advanced calculations
- ✅ **Optimize field mappings** for aggregation performance
- ✅ **Use composite aggregations** for large result sets
- ✅ **Consider memory implications** of high-cardinality aggregations
- ✅ **Structure nested aggregations** logically for readability
- ✅ **Test aggregation performance** with realistic data volumes

Ready to optimize search relevance? Continue with [Relevance Scoring](relevance-scoring.md) to learn advanced ranking techniques!