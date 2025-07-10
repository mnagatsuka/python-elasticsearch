# Mapping & Field Types

**Master document schemas and data types in Elasticsearch**

*Estimated reading time: 35 minutes*

## Overview

Mapping defines how documents and their fields are stored and indexed. It's like a schema in traditional databases but with much more flexibility. Understanding mapping is crucial for optimizing search performance and ensuring data is indexed correctly.

## 📋 Table of Contents

1. [What is Mapping?](#what-is-mapping)
2. [Dynamic vs Explicit Mapping](#dynamic-vs-explicit-mapping)
3. [Core Field Types](#core-field-types)
4. [Text Analysis](#text-analysis)
5. [Complex Field Types](#complex-field-types)
6. [Mapping Parameters](#mapping-parameters)
7. [Index Templates](#index-templates)
8. [Best Practices](#best-practices)

## 🗺️ What is Mapping?

Mapping is the process of defining how documents and their fields are stored and indexed. It determines:

- **Field data types** (text, keyword, date, etc.)
- **How text is analyzed** (tokenization, stemming, etc.)
- **Which fields are searchable** or aggregatable
- **Storage and indexing options**

### Viewing Current Mapping

```bash
# View mapping for an index
curl "localhost:9200/blog/_mapping?pretty"

# View mapping for specific fields
curl "localhost:9200/blog/_mapping/field/title?pretty"
```

**Example Response:**
```json
{
  "blog": {
    "mappings": {
      "properties": {
        "title": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "author": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "published_date": {
          "type": "date"
        },
        "view_count": {
          "type": "long"
        }
      }
    }
  }
}
```

## 🔄 Dynamic vs Explicit Mapping

### Dynamic Mapping

Elasticsearch automatically detects field types when you index documents:

```bash
# Index document without predefined mapping
curl -X POST "localhost:9200/auto-blog/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Auto-detected Fields",      // → text + keyword
  "author": "John Doe",                // → text + keyword  
  "age": 30,                          // → long
  "price": 99.99,                     // → float
  "published": true,                  // → boolean
  "created_at": "2024-01-18",         // → date
  "tags": ["tech", "tutorial"]        // → text + keyword array
}
'

# Check auto-generated mapping
curl "localhost:9200/auto-blog/_mapping?pretty"
```

### Dynamic Mapping Rules

| JSON Type | Elasticsearch Type |
|-----------|-------------------|
| `string` | `text` + `keyword` multi-field |
| `integer` | `long` |
| `float` | `float` |
| `boolean` | `boolean` |
| `date string` | `date` |
| `array` | Depends on first non-null value |
| `object` | `object` |
| `null` | No field added |

### Explicit Mapping

Define mapping before indexing for better control:

```bash
# Create index with explicit mapping
curl -X PUT "localhost:9200/blog" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "standard"
      },
      "author": {
        "type": "keyword"
      },
      "content": {
        "type": "text",
        "analyzer": "english"
      },
      "tags": {
        "type": "keyword"
      },
      "published_date": {
        "type": "date",
        "format": "yyyy-MM-dd||yyyy-MM-dd HH:mm:ss||epoch_millis"
      },
      "view_count": {
        "type": "integer"
      },
      "rating": {
        "type": "float"
      },
      "is_featured": {
        "type": "boolean"
      }
    }
  }
}
'
```

## 📊 Core Field Types

### Text Types

**Text Field (for full-text search):**
```json
{
  "title": {
    "type": "text",
    "analyzer": "standard"
  }
}
```

**Keyword Field (for exact match):**
```json
{
  "status": {
    "type": "keyword"
  }
}
```

**Multi-field (both text and keyword):**
```json
{
  "title": {
    "type": "text",
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      },
      "suggest": {
        "type": "completion"
      }
    }
  }
}
```

### Numeric Types

```json
{
  "properties": {
    "age": {"type": "byte"},           // -128 to 127
    "score": {"type": "short"},        // -32,768 to 32,767  
    "population": {"type": "integer"}, // -2^31 to 2^31-1
    "distance": {"type": "long"},      // -2^63 to 2^63-1
    "price": {"type": "float"},        // 32-bit IEEE 754
    "rating": {"type": "double"},      // 64-bit IEEE 754
    "percentage": {"type": "half_float"}, // 16-bit IEEE 754
    "precise_price": {"type": "scaled_float", "scaling_factor": 100}
  }
}
```

### Date Types

```json
{
  "published_date": {
    "type": "date",
    "format": "yyyy-MM-dd||yyyy-MM-dd HH:mm:ss||epoch_millis"
  },
  "created_at": {
    "type": "date",
    "format": "strict_date_optional_time||epoch_millis"
  }
}
```

**Date Format Examples:**
```bash
# Index documents with different date formats
curl -X POST "localhost:9200/events/_doc/1" -H 'Content-Type: application/json' -d'
{
  "title": "Conference 2024",
  "start_date": "2024-06-15",                    // yyyy-MM-dd
  "end_date": "2024-06-17 18:00:00",            // yyyy-MM-dd HH:mm:ss
  "registration_deadline": 1717200000000         // epoch milliseconds
}
'
```

### Boolean Type

```json
{
  "is_published": {"type": "boolean"},
  "is_featured": {"type": "boolean"}
}
```

**Boolean Values:**
- `true`, `false`
- `"true"`, `"false"` (strings)
- `"on"`, `"off"`
- `"yes"`, `"no"`
- `1`, `0`

## 🔍 Text Analysis

### Analyzers

Analyzers determine how text is processed for indexing and searching:

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "custom_english": {
          "type": "standard",
          "stopwords": ["the", "and", "or", "but"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "title": {
        "type": "text",
        "analyzer": "custom_english"
      },
      "content": {
        "type": "text",
        "analyzer": "english"
      }
    }
  }
}
```

### Built-in Analyzers

**Standard Analyzer (default):**
```bash
# Test analyzer
curl -X POST "localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "standard",
  "text": "The Quick Brown Fox Jumps Over the Lazy Dog!"
}
'

# Response: ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
```

**Language Analyzers:**
```json
{
  "content_en": {"type": "text", "analyzer": "english"},
  "content_es": {"type": "text", "analyzer": "spanish"},
  "content_fr": {"type": "text", "analyzer": "french"}
}
```

**Other Analyzers:**
```json
{
  "exact_match": {"type": "text", "analyzer": "keyword"},
  "simple_text": {"type": "text", "analyzer": "simple"},
  "whitespace_only": {"type": "text", "analyzer": "whitespace"}
}
```

## 🏗️ Complex Field Types

### Object Type

```bash
# Create mapping with nested object
curl -X PUT "localhost:9200/users" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "name": {"type": "text"},
      "address": {
        "properties": {
          "street": {"type": "text"},
          "city": {"type": "keyword"},
          "state": {"type": "keyword"},
          "zip_code": {"type": "keyword"},
          "coordinates": {
            "type": "geo_point"
          }
        }
      }
    }
  }
}
'

# Index document with nested object
curl -X POST "localhost:9200/users/_doc/1" -H 'Content-Type: application/json' -d'
{
  "name": "John Doe",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "coordinates": {
      "lat": 40.7128,
      "lon": -74.0060
    }
  }
}
'
```

### Nested Type

For arrays of objects that need to maintain their relationships:

```bash
curl -X PUT "localhost:9200/products" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "name": {"type": "text"},
      "reviews": {
        "type": "nested",
        "properties": {
          "reviewer": {"type": "keyword"},
          "rating": {"type": "integer"},
          "comment": {"type": "text"},
          "date": {"type": "date"}
        }
      }
    }
  }
}
'

# Index product with reviews
curl -X POST "localhost:9200/products/_doc/1" -H 'Content-Type: application/json' -d'
{
  "name": "Wireless Headphones",
  "reviews": [
    {
      "reviewer": "alice",
      "rating": 5,
      "comment": "Excellent sound quality",
      "date": "2024-01-15"
    },
    {
      "reviewer": "bob", 
      "rating": 4,
      "comment": "Good value for money",
      "date": "2024-01-16"
    }
  ]
}
'
```

### Array Type

Elasticsearch handles arrays automatically:

```json
{
  "tags": ["elasticsearch", "search", "analytics"],
  "scores": [95, 87, 92, 78],
  "categories": [
    {"name": "technology", "weight": 0.8},
    {"name": "tutorial", "weight": 0.6}
  ]
}
```

### Geo Types

**Geo Point:**
```json
{
  "location": {
    "type": "geo_point"
  }
}
```

**Geo Shape:**
```json
{
  "area": {
    "type": "geo_shape"
  }
}
```

**Examples:**
```bash
curl -X POST "localhost:9200/locations/_doc/1" -H 'Content-Type: application/json' -d'
{
  "name": "Central Park",
  "location": {
    "lat": 40.7829,
    "lon": -73.9654
  },
  "area": {
    "type": "polygon",
    "coordinates": [[
      [-73.9857, 40.7484],
      [-73.9857, 40.8007],
      [-73.9487, 40.8007],
      [-73.9487, 40.7484],
      [-73.9857, 40.7484]
    ]]
  }
}
'
```

## ⚙️ Mapping Parameters

### Common Parameters

**index**: Control if field is searchable
```json
{
  "secret_field": {
    "type": "keyword", 
    "index": false
  }
}
```

**store**: Store original field value
```json
{
  "large_content": {
    "type": "text",
    "store": true
  }
}
```

**doc_values**: Enable aggregations and sorting
```json
{
  "category": {
    "type": "keyword",
    "doc_values": false  // Disable for memory savings
  }
}
```

**ignore_above**: Ignore long strings for keyword fields
```json
{
  "tags": {
    "type": "keyword",
    "ignore_above": 100
  }
}
```

### Text-specific Parameters

```json
{
  "content": {
    "type": "text",
    "analyzer": "english",
    "search_analyzer": "english",
    "term_vector": "with_positions_offsets",
    "fielddata": true,
    "fields": {
      "keyword": {
        "type": "keyword",
        "ignore_above": 256
      }
    }
  }
}
```

### Numeric Parameters

```json
{
  "price": {
    "type": "scaled_float",
    "scaling_factor": 100,
    "null_value": 0,
    "coerce": true
  }
}
```

## 📋 Index Templates

Create templates for consistent mappings across multiple indices:

```bash
# Create index template
curl -X PUT "localhost:9200/_index_template/blog_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["blog-*"],
  "priority": 1,
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1
    },
    "mappings": {
      "properties": {
        "title": {
          "type": "text",
          "fields": {"keyword": {"type": "keyword"}}
        },
        "author": {"type": "keyword"},
        "content": {"type": "text", "analyzer": "english"},
        "published_date": {"type": "date"},
        "tags": {"type": "keyword"},
        "view_count": {"type": "integer"},
        "is_published": {"type": "boolean"}
      }
    }
  }
}
'

# Create index matching pattern - template will be applied
curl -X PUT "localhost:9200/blog-2024-01"

# Verify template was applied
curl "localhost:9200/blog-2024-01/_mapping?pretty"
```

### Component Templates

Create reusable mapping components:

```bash
# Create component template for common fields
curl -X PUT "localhost:9200/_component_template/common_fields" -H 'Content-Type: application/json' -d'
{
  "template": {
    "mappings": {
      "properties": {
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "version": {"type": "integer"},
        "active": {"type": "boolean"}
      }
    }
  }
}
'

# Use component template in index template
curl -X PUT "localhost:9200/_index_template/content_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["content-*"],
  "composed_of": ["common_fields"],
  "template": {
    "mappings": {
      "properties": {
        "title": {"type": "text"},
        "body": {"type": "text"}
      }
    }
  }
}
'
```

## 🎯 Real-world Examples

### E-commerce Product Catalog

```bash
curl -X PUT "localhost:9200/products" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "standard",
        "fields": {
          "keyword": {"type": "keyword"},
          "suggest": {"type": "completion"}
        }
      },
      "description": {
        "type": "text", 
        "analyzer": "english"
      },
      "category": {
        "type": "keyword"
      },
      "brand": {
        "type": "keyword"
      },
      "price": {
        "type": "scaled_float",
        "scaling_factor": 100
      },
      "discount_price": {
        "type": "scaled_float",
        "scaling_factor": 100
      },
      "rating": {
        "type": "half_float"
      },
      "review_count": {
        "type": "integer"
      },
      "in_stock": {
        "type": "boolean"
      },
      "stock_quantity": {
        "type": "integer"
      },
      "attributes": {
        "type": "nested",
        "properties": {
          "name": {"type": "keyword"},
          "value": {"type": "keyword"}
        }
      },
      "images": {
        "type": "object",
        "properties": {
          "url": {"type": "keyword", "index": false},
          "alt_text": {"type": "text"}
        }
      },
      "created_at": {"type": "date"},
      "updated_at": {"type": "date"}
    }
  }
}
'
```

### Log Analysis Schema

```bash
curl -X PUT "localhost:9200/application-logs" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "@timestamp": {"type": "date"},
      "level": {"type": "keyword"},
      "logger": {"type": "keyword"},
      "message": {
        "type": "text",
        "analyzer": "standard"
      },
      "service": {"type": "keyword"},
      "environment": {"type": "keyword"},
      "host": {
        "properties": {
          "name": {"type": "keyword"},
          "ip": {"type": "ip"}
        }
      },
      "user": {
        "properties": {
          "id": {"type": "keyword"},
          "name": {"type": "keyword"}
        }
      },
      "request": {
        "properties": {
          "method": {"type": "keyword"},
          "url": {"type": "keyword"},
          "status_code": {"type": "short"},
          "duration_ms": {"type": "integer"},
          "size_bytes": {"type": "long"}
        }
      },
      "error": {
        "properties": {
          "type": {"type": "keyword"},
          "message": {"type": "text"},
          "stack_trace": {"type": "text", "index": false}
        }
      },
      "tags": {"type": "keyword"}
    }
  }
}
'
```

## 🚀 Best Practices

### Field Type Selection

```json
{
  // ✅ Use keyword for exact match, aggregations, sorting
  "status": {"type": "keyword"},
  "user_id": {"type": "keyword"},
  
  // ✅ Use text for full-text search
  "title": {"type": "text"},
  "description": {"type": "text"},
  
  // ✅ Use appropriate numeric types
  "age": {"type": "byte"},        // Small numbers
  "price": {"type": "scaled_float"}, // Currency
  "timestamp": {"type": "date"},
  
  // ✅ Multi-field for different use cases
  "name": {
    "type": "text",
    "fields": {
      "keyword": {"type": "keyword"},    // For aggregations
      "suggest": {"type": "completion"}  // For autocomplete
    }
  }
}
```

### Performance Optimization

```json
{
  // ✅ Disable unnecessary features
  "internal_id": {
    "type": "keyword",
    "doc_values": false,  // No aggregations needed
    "index": false        // No search needed
  },
  
  // ✅ Use ignore_above for long strings
  "tags": {
    "type": "keyword",
    "ignore_above": 100
  },
  
  // ✅ Disable fielddata for text fields unless needed
  "content": {
    "type": "text",
    "fielddata": false
  }
}
```

### Dynamic Template Patterns

```bash
curl -X PUT "localhost:9200/dynamic_example" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "dynamic_templates": [
      {
        "strings_as_keywords": {
          "match_mapping_type": "string",
          "match": "*_id",
          "mapping": {
            "type": "keyword"
          }
        }
      },
      {
        "strings_as_text": {
          "match_mapping_type": "string",
          "mapping": {
            "type": "text",
            "fields": {
              "keyword": {"type": "keyword", "ignore_above": 256}
            }
          }
        }
      }
    ]
  }
}
'
```

## ❌ Common Pitfalls

### Wrong Field Types

```json
// ❌ Bad: Using text for exact match
{
  "status": {"type": "text"}  // Will be analyzed
}

// ✅ Good: Using keyword for exact match
{
  "status": {"type": "keyword"}  // Exact match
}
```

### Missing Multi-fields

```json
// ❌ Bad: Only text (no aggregations possible)
{
  "category": {"type": "text"}
}

// ✅ Good: Multi-field for different use cases
{
  "category": {
    "type": "text",
    "fields": {
      "keyword": {"type": "keyword"}
    }
  }
}
```

### Inappropriate Analyzers

```json
// ❌ Bad: Using English analyzer for names
{
  "author_name": {"type": "text", "analyzer": "english"}
}

// ✅ Good: Using standard analyzer for names
{
  "author_name": {"type": "text", "analyzer": "standard"}
}
```

## 🔗 Next Steps

Now that you understand mapping and field types, let's explore index management:

1. **[Index Lifecycle](index-lifecycle.md)** - Manage indices effectively
2. **[Query DSL Basics](../03-search-fundamentals/query-dsl-basics.md)** - Search your structured data
3. **[Full-text Search](../04-advanced-search/full-text-search.md)** - Advanced text search techniques

## 📚 Key Takeaways

- ✅ **Choose appropriate field types** for your data and use cases
- ✅ **Use explicit mapping** for production systems
- ✅ **Leverage multi-fields** for different search and aggregation needs
- ✅ **Select proper analyzers** for text processing
- ✅ **Use index templates** for consistent mappings
- ✅ **Optimize field parameters** for performance
- ✅ **Plan for nested objects** when relationships matter
- ✅ **Test your mappings** with sample data before production

Ready to learn about index management? Continue with [Index Lifecycle](index-lifecycle.md) to master index operations!