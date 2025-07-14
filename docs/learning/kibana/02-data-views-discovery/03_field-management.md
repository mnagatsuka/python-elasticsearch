# Field Management

**Master advanced field operations, customizations, and optimizations for effective data analysis**

*Estimated reading time: 20 minutes*

## Overview

Field management in Kibana is a critical skill that transforms raw Elasticsearch data into meaningful, analyzable information. This guide covers advanced field operations, from basic customizations to complex runtime calculations, helping you optimize data presentation and analysis performance.

## 🎯 Field Types and Visualization Impact

### Understanding Field Types in Kibana

Field types fundamentally determine how data can be analyzed and visualized. Each Elasticsearch field type has specific characteristics that affect aggregation capabilities, visualization options, and performance.

#### Core Field Types and Their Properties

```
Field Type Hierarchy:
├── Text Fields
│   ├── text: Full-text search, not aggregatable
│   ├── keyword: Exact matching, aggregatable
│   └── search_as_you_type: Autocomplete functionality
├── Numeric Fields
│   ├── long/integer: Whole numbers, range queries
│   ├── float/double: Decimal numbers, mathematical operations
│   └── scaled_float: Precision-controlled decimals
├── Date Fields
│   ├── date: ISO timestamps, time-based analysis
│   ├── date_nanos: Nanosecond precision timestamps
│   └── date_range: Time period representations
├── Boolean Fields
│   ├── boolean: True/false binary values
│   └── Binary visualization options
└── Specialized Fields
    ├── ip: IP address analysis and geographic mapping
    ├── geo_point: Geographic coordinates, map visualizations
    ├── geo_shape: Complex geographic shapes
    └── nested: Object hierarchies, complex data structures
```

### Visualization Impact by Field Type

#### Text vs Keyword Fields

**Text Fields:**
```json
{
  "product_description": {
    "type": "text",
    "analyzer": "standard"
  }
}
```

**Visualization Limitations:**
- ❌ Cannot be used in aggregations
- ❌ Not suitable for terms visualizations
- ❌ Cannot create pie charts or bar charts
- ✅ Excellent for full-text search
- ✅ Supports text analysis and highlighting

**Keyword Fields:**
```json
{
  "product_category": {
    "type": "keyword"
  }
}
```

**Visualization Capabilities:**
- ✅ Terms aggregations (pie charts, bar charts)
- ✅ Unique count calculations
- ✅ Top values analysis
- ✅ Filtering and faceting
- ❌ Limited full-text search capabilities

#### Multi-Field Mappings

**Best Practice Configuration:**
```json
{
  "mappings": {
    "properties": {
      "product_name": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 256
          }
        }
      }
    }
  }
}
```

**Usage in Visualizations:**
```kql
# Full-text search
product_name: "smartphone"

# Exact matching and aggregations
product_name.keyword: "iPhone 15 Pro"
```

### Numeric Field Analysis

#### Integer vs Float Considerations

**Integer Fields (long/integer):**
```json
{
  "user_age": {
    "type": "integer"
  },
  "order_count": {
    "type": "long"
  }
}
```

**Visualization Strengths:**
- Histogram aggregations
- Range queries
- Mathematical calculations
- Percentile analysis

**Float Fields (float/double):**
```json
{
  "product_price": {
    "type": "float"
  },
  "cpu_usage": {
    "type": "double"
  }
}
```

**Precision Considerations:**
- **float**: 32-bit precision, suitable for most metrics
- **double**: 64-bit precision, financial calculations
- **scaled_float**: Fixed decimal places, currency values

#### Scaled Float for Financial Data

**Configuration:**
```json
{
  "order_amount": {
    "type": "scaled_float",
    "scaling_factor": 100
  }
}
```

**Benefits:**
- Exact decimal representation
- Consistent currency formatting
- Efficient storage and processing
- Precise mathematical operations

### Date Field Optimization

#### Date Format Configuration

**Multiple Format Support:**
```json
{
  "event_timestamp": {
    "type": "date",
    "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
  }
}
```

**Format Options:**
- **ISO 8601**: `2024-01-15T10:30:00Z`
- **Custom**: `yyyy-MM-dd HH:mm:ss`
- **Epoch**: `1705320600000`
- **Multiple**: Support various incoming formats

#### Time Zone Handling

**Index-Time Configuration:**
```json
{
  "created_at": {
    "type": "date",
    "format": "yyyy-MM-dd HH:mm:ss",
    "time_zone": "America/New_York"
  }
}
```

**Query-Time Adjustment:**
```json
{
  "range": {
    "created_at": {
      "gte": "2024-01-15 09:00:00",
      "lte": "2024-01-15 17:00:00",
      "time_zone": "America/New_York"
    }
  }
}
```

## 🏷️ Custom Field Labels and Formatting

### Field Label Customization

#### Business-Friendly Labels

**Default vs Custom Labels:**
```
Technical Field Names → Business-Friendly Labels
├── user_id → "Customer ID"
├── response_time_ms → "Response Time (milliseconds)"
├── geo.coordinates → "Geographic Location"
├── event.category → "Event Type"
├── bytes_sent → "Data Transmitted"
└── cpu.usage.percent → "CPU Utilization %"
```

**Configuration Process:**
1. **Navigate to Data View Management**
   ```
   Stack Management → Data Views → Select Data View
   ```

2. **Edit Field Properties**
   ```
   Field List → Find Field → Click Edit Icon (✏️)
   ```

3. **Set Custom Label**
   ```
   Custom Label: "Customer Identification Number"
   Description: "Unique identifier for customer records"
   ```

### Advanced Field Formatting

#### Numeric Format Options

**Currency Formatting:**
```json
{
  "field_name": "order_total",
  "format": {
    "id": "currency",
    "params": {
      "currency": "USD",
      "pattern": "$0,0.00"
    }
  }
}
```

**Percentage Formatting:**
```json
{
  "field_name": "conversion_rate",
  "format": {
    "id": "percent",
    "params": {
      "pattern": "0.00%"
    }
  }
}
```

**Bytes Formatting:**
```json
{
  "field_name": "file_size",
  "format": {
    "id": "bytes",
    "params": {
      "pattern": "0.0 b"
    }
  }
}
```

#### Date Format Customization

**Common Date Patterns:**
```javascript
// Standard formats
'YYYY-MM-DD HH:mm:ss'     // 2024-01-15 10:30:00
'MMM DD, YYYY @ HH:mm'    // Jan 15, 2024 @ 10:30
'dddd, MMMM Do YYYY'      // Monday, January 15th 2024
'YYYY-MM-DD'              // 2024-01-15
'HH:mm:ss'                // 10:30:00

// Relative formats
'fromNow'                 // 2 hours ago
'toNow'                   // in 3 days
```

**Business Context Formatting:**
```javascript
// Fiscal year formatting
'YYYY-MM-DD [FY]YYYY'     // 2024-01-15 FY2024

// Quarter formatting
'YYYY [Q]Q'               // 2024 Q1

// Week formatting
'YYYY-[W]ww'              // 2024-W03
```

#### URL Field Templates

**Basic URL Templates:**
```bash
# User profile links
https://crm.company.com/users/{{value}}

# Product detail pages
https://catalog.company.com/products/{{product_id}}

# Log investigation links
https://logs.company.com/search?query={{error_code}}&time={{timestamp}}
```

**Advanced URL Templates:**
```bash
# Multi-parameter URLs
https://dashboard.company.com/analysis?
  user={{user_id}}&
  product={{product_id}}&
  date={{order_date}}&
  amount={{order_total}}

# Conditional URL formatting
{{#if is_premium}}
  https://premium.company.com/customer/{{customer_id}}
{{else}}
  https://standard.company.com/customer/{{customer_id}}
{{/if}}
```

### Field Display Optimization

#### Field Order and Grouping

**Strategic Field Ordering:**
```
Field Display Priority:
├── Primary Identifiers (customer_id, order_id)
├── Key Metrics (amount, quantity, score)
├── Temporal Data (timestamps, dates)
├── Categorical Data (status, type, category)
├── Technical Fields (source_ip, user_agent)
└── Metadata (created_by, updated_at)
```

**Field Grouping Strategies:**
```json
{
  "field_groups": {
    "customer_info": [
      "customer_id",
      "customer_name",
      "customer_tier",
      "customer_location"
    ],
    "transaction_data": [
      "order_id",
      "order_total",
      "order_date",
      "payment_method"
    ],
    "technical_metrics": [
      "response_time",
      "error_count",
      "success_rate"
    ]
  }
}
```

## ⚡ Runtime Fields and Calculated Fields

### Runtime Fields Overview

Runtime fields provide dynamic field calculation without reindexing, offering flexibility for evolving business requirements and complex data transformations.

#### Runtime Field vs Stored Field Comparison

```
Runtime Fields vs Stored Fields:
├── Runtime Fields:
│   ├── ✅ No reindexing required
│   ├── ✅ Dynamic calculations
│   ├── ✅ Flexible business logic
│   ├── ❌ Query-time computation overhead
│   └── ❌ Limited performance for heavy calculations
└── Stored Fields:
    ├── ✅ Fast query performance
    ├── ✅ Efficient aggregations
    ├── ❌ Requires reindexing for changes
    └── ❌ Storage overhead
```

### Creating Runtime Fields

#### Basic Runtime Field Syntax

**Full Name Calculation:**
```json
{
  "runtime_mappings": {
    "full_name": {
      "type": "keyword",
      "script": {
        "source": """
          if (doc['first_name'].size() > 0 && doc['last_name'].size() > 0) {
            emit(doc['first_name'].value + ' ' + doc['last_name'].value);
          }
        """
      }
    }
  }
}
```

**Age Calculation:**
```json
{
  "runtime_mappings": {
    "age": {
      "type": "long",
      "script": {
        "source": """
          if (doc['birth_date'].size() > 0) {
            LocalDate birthDate = LocalDate.parse(doc['birth_date'].value);
            LocalDate today = LocalDate.now();
            emit(Period.between(birthDate, today).getYears());
          }
        """
      }
    }
  }
}
```

#### Advanced Runtime Field Examples

**Business Logic Implementation:**
```json
{
  "runtime_mappings": {
    "customer_segment": {
      "type": "keyword",
      "script": {
        "source": """
          double total = doc['total_orders'].value;
          double avg_order = doc['avg_order_value'].value;
          
          if (total > 50 && avg_order > 500) {
            emit('VIP');
          } else if (total > 20 && avg_order > 200) {
            emit('Premium');
          } else if (total > 5) {
            emit('Regular');
          } else {
            emit('New');
          }
        """
      }
    }
  }
}
```

**Performance Metrics:**
```json
{
  "runtime_mappings": {
    "response_time_category": {
      "type": "keyword",
      "script": {
        "source": """
          long responseTime = doc['response_time_ms'].value;
          
          if (responseTime < 100) {
            emit('Excellent');
          } else if (responseTime < 500) {
            emit('Good');
          } else if (responseTime < 1000) {
            emit('Average');
          } else if (responseTime < 5000) {
            emit('Poor');
          } else {
            emit('Critical');
          }
        """
      }
    }
  }
}
```

### Mathematical Calculations

#### Financial Calculations

**Profit Margin Calculation:**
```json
{
  "runtime_mappings": {
    "profit_margin_percent": {
      "type": "double",
      "script": {
        "source": """
          if (doc['revenue'].size() > 0 && doc['cost'].size() > 0) {
            double revenue = doc['revenue'].value;
            double cost = doc['cost'].value;
            
            if (revenue > 0) {
              emit(((revenue - cost) / revenue) * 100);
            } else {
              emit(0);
            }
          }
        """
      }
    }
  }
}
```

**Tax Calculation:**
```json
{
  "runtime_mappings": {
    "tax_amount": {
      "type": "double",
      "script": {
        "source": """
          if (doc['subtotal'].size() > 0 && doc['tax_rate'].size() > 0) {
            double subtotal = doc['subtotal'].value;
            double taxRate = doc['tax_rate'].value;
            emit(subtotal * (taxRate / 100));
          }
        """
      }
    }
  }
}
```

#### Statistical Calculations

**Z-Score Calculation:**
```json
{
  "runtime_mappings": {
    "performance_zscore": {
      "type": "double",
      "script": {
        "source": """
          if (doc['individual_score'].size() > 0 && 
              doc['team_average'].size() > 0 && 
              doc['team_stddev'].size() > 0) {
            
            double individual = doc['individual_score'].value;
            double average = doc['team_average'].value;
            double stddev = doc['team_stddev'].value;
            
            if (stddev > 0) {
              emit((individual - average) / stddev);
            } else {
              emit(0);
            }
          }
        """
      }
    }
  }
}
```

### String Manipulation

#### Text Processing Functions

**Domain Extraction:**
```json
{
  "runtime_mappings": {
    "email_domain": {
      "type": "keyword",
      "script": {
        "source": """
          if (doc['email'].size() > 0) {
            String email = doc['email'].value;
            int atIndex = email.indexOf('@');
            if (atIndex > 0 && atIndex < email.length() - 1) {
              emit(email.substring(atIndex + 1));
            }
          }
        """
      }
    }
  }
}
```

**URL Path Extraction:**
```json
{
  "runtime_mappings": {
    "api_endpoint": {
      "type": "keyword",
      "script": {
        "source": """
          if (doc['url'].size() > 0) {
            String url = doc['url'].value;
            int pathStart = url.indexOf('/', 8); // Skip protocol
            if (pathStart > 0) {
              String path = url.substring(pathStart);
              int queryStart = path.indexOf('?');
              if (queryStart > 0) {
                emit(path.substring(0, queryStart));
              } else {
                emit(path);
              }
            }
          }
        """
      }
    }
  }
}
```

### Date and Time Calculations

#### Business Day Calculations

**Working Hours Detection:**
```json
{
  "runtime_mappings": {
    "is_business_hours": {
      "type": "boolean",
      "script": {
        "source": """
          if (doc['@timestamp'].size() > 0) {
            ZonedDateTime timestamp = doc['@timestamp'].value;
            int hour = timestamp.getHour();
            int dayOfWeek = timestamp.getDayOfWeek().getValue();
            
            // Monday = 1, Sunday = 7
            boolean isWeekday = dayOfWeek >= 1 && dayOfWeek <= 5;
            boolean isBusinessHour = hour >= 9 && hour <= 17;
            
            emit(isWeekday && isBusinessHour);
          }
        """
      }
    }
  }
}
```

**Time Since Last Event:**
```json
{
  "runtime_mappings": {
    "hours_since_last_login": {
      "type": "double",
      "script": {
        "source": """
          if (doc['last_login'].size() > 0) {
            ZonedDateTime lastLogin = doc['last_login'].value;
            ZonedDateTime now = ZonedDateTime.now();
            
            long millisDiff = now.toInstant().toEpochMilli() - 
                             lastLogin.toInstant().toEpochMilli();
            
            emit(millisDiff / (1000.0 * 60 * 60)); // Convert to hours
          }
        """
      }
    }
  }
}
```

## 🔧 Field Conflict Resolution

### Understanding Field Conflicts

Field conflicts occur when the same field name exists across multiple indices with different mappings, creating ambiguity in data interpretation and visualization.

#### Common Conflict Scenarios

**Type Conflicts:**
```json
// Index 1: logs-app-2024-01
{
  "user_id": {
    "type": "keyword"
  }
}

// Index 2: logs-app-2024-02
{
  "user_id": {
    "type": "long"
  }
}
```

**Format Conflicts:**
```json
// Index 1: events-2024-01
{
  "timestamp": {
    "type": "date",
    "format": "yyyy-MM-dd"
  }
}

// Index 2: events-2024-02
{
  "timestamp": {
    "type": "date",
    "format": "epoch_millis"
  }
}
```

### Conflict Detection and Analysis

#### Identifying Field Conflicts

**Data View Field List Indicators:**
```
Field Conflict Indicators:
├── ⚠️ Yellow warning icon next to field name
├── "Conflicting types" message in field details
├── Multiple type indicators (e.g., "keyword, long")
├── Inconsistent field statistics
└── Visualization errors with the field
```

**API-Based Conflict Detection:**
```bash
# Check field capabilities across indices
GET /logs-*/_field_caps?fields=user_id,timestamp,amount

# Response shows conflicts
{
  "fields": {
    "user_id": {
      "keyword": {
        "type": "keyword",
        "indices": ["logs-app-2024-01"]
      },
      "long": {
        "type": "long",
        "indices": ["logs-app-2024-02"]
      }
    }
  }
}
```

### Resolution Strategies

#### Strategy 1: Index Template Standardization

**Create Consistent Index Template:**
```json
{
  "index_patterns": ["logs-*"],
  "template": {
    "mappings": {
      "properties": {
        "user_id": {
          "type": "keyword"
        },
        "timestamp": {
          "type": "date",
          "format": "yyyy-MM-dd HH:mm:ss||epoch_millis"
        },
        "amount": {
          "type": "scaled_float",
          "scaling_factor": 100
        }
      }
    }
  }
}
```

#### Strategy 2: Reindexing with Consistent Mappings

**Reindex with Data Transformation:**
```json
{
  "source": {
    "index": "logs-app-2024-02"
  },
  "dest": {
    "index": "logs-app-2024-02-fixed"
  },
  "script": {
    "source": """
      // Convert numeric user_id to string
      if (ctx._source.user_id instanceof Number) {
        ctx._source.user_id = ctx._source.user_id.toString();
      }
      
      // Ensure consistent timestamp format
      if (ctx._source.timestamp instanceof Long) {
        ctx._source.timestamp = new Date(ctx._source.timestamp);
      }
    """
  }
}
```

#### Strategy 3: Field Aliasing

**Create Field Aliases:**
```json
{
  "mappings": {
    "properties": {
      "user_identifier": {
        "type": "alias",
        "path": "user_id"
      },
      "event_timestamp": {
        "type": "alias",
        "path": "timestamp"
      }
    }
  }
}
```

### Mapping Migration Strategies

#### Gradual Migration Approach

**Phase 1: Prepare New Mapping**
```json
{
  "template": {
    "mappings": {
      "properties": {
        "user_id": {
          "type": "keyword",
          "fields": {
            "numeric": {
              "type": "long"
            }
          }
        }
      }
    }
  }
}
```

**Phase 2: Dual-Write Strategy**
```python
# Application code adaptation
def index_document(doc):
    # Write to both old and new field formats
    if 'user_id' in doc:
        doc['user_id_string'] = str(doc['user_id'])
        doc['user_id_numeric'] = int(doc['user_id'])
    
    # Index with both formats
    es.index(index="logs-app", body=doc)
```

**Phase 3: Data View Updates**
```json
{
  "runtime_mappings": {
    "user_id_unified": {
      "type": "keyword",
      "script": {
        "source": """
          if (doc['user_id_string'].size() > 0) {
            emit(doc['user_id_string'].value);
          } else if (doc['user_id_numeric'].size() > 0) {
            emit(doc['user_id_numeric'].value.toString());
          }
        """
      }
    }
  }
}
```

## 👁️ Field Visibility and Organization

### Field Visibility Controls

#### Hiding Irrelevant Fields

**Hide Fields from Data View:**
```json
{
  "field_attributes": {
    "internal_metadata": {
      "customLabel": "Internal Metadata",
      "count": 0,
      "visibility": "hidden"
    },
    "debug_info": {
      "visibility": "hidden"
    },
    "system_timestamp": {
      "visibility": "hidden"
    }
  }
}
```

**Hide via Field Patterns:**
```bash
# Hide all fields starting with underscore
_*

# Hide all debug fields
debug.*

# Hide system internals
system.internal.*
```

#### Popular Fields Management

**Auto-Popular Field Criteria:**
```
Popular Field Algorithm:
├── Field appears in > 80% of documents
├── Field has been used in visualizations
├── Field has unique values (high cardinality)
├── Field has been manually marked as popular
└── Field is frequently searched/filtered
```

**Manual Popular Field Configuration:**
```json
{
  "popular_fields": [
    "@timestamp",
    "user.id",
    "event.action",
    "source.ip",
    "response.status_code"
  ]
}
```

### Field Organization Strategies

#### Logical Field Grouping

**Business Domain Organization:**
```
Customer Analytics:
├── customer_id
├── customer_tier
├── customer_location
├── customer_lifetime_value
└── customer_acquisition_date

Product Analytics:
├── product_id
├── product_category
├── product_price
├── product_ratings
└── product_inventory

Transaction Analytics:
├── order_id
├── order_total
├── order_date
├── payment_method
└── order_status
```

#### Field Naming Conventions

**Consistent Naming Patterns:**
```
Naming Convention Standards:
├── Timestamps: {entity}_{action}_timestamp
│   ├── user_created_timestamp
│   ├── order_processed_timestamp
│   └── payment_confirmed_timestamp
├── Identifiers: {entity}_id
│   ├── customer_id
│   ├── product_id
│   └── session_id
├── Metrics: {entity}_{metric}_{unit}
│   ├── response_time_ms
│   ├── file_size_bytes
│   └── cpu_usage_percent
└── Categories: {entity}_{property}
    ├── user_status
    ├── order_type
    └── payment_method
```

### Field Documentation and Metadata

#### Field Description Standards

**Comprehensive Field Documentation:**
```json
{
  "field_metadata": {
    "customer_lifetime_value": {
      "description": "Total revenue generated by customer over their entire relationship",
      "calculation": "Sum of all completed orders minus refunds",
      "business_owner": "Customer Success Team",
      "data_quality": "Updated daily via batch process",
      "example_values": ["1250.50", "3400.75", "850.25"]
    },
    "response_time_ms": {
      "description": "Time taken to process HTTP request",
      "measurement": "Milliseconds from request received to response sent",
      "thresholds": {
        "excellent": "< 100ms",
        "good": "100-500ms",
        "poor": "> 2000ms"
      },
      "monitoring": "Real-time via application metrics"
    }
  }
}
```

## 📊 Scripted Fields vs Runtime Fields

### Comparison Analysis

#### Scripted Fields (Legacy Approach)

**Characteristics:**
```
Scripted Fields:
├── ✅ Stored in data view configuration
├── ✅ Painless scripting language
├── ✅ Field-level caching
├── ❌ Limited to single data view
├── ❌ Cannot be reused across data views
├── ❌ Stored in Kibana saved objects
└── ❌ Being deprecated in favor of runtime fields
```

**Example Scripted Field:**
```javascript
// Scripted field for full name
if (doc['first_name'].size() > 0 && doc['last_name'].size() > 0) {
  return doc['first_name'].value + ' ' + doc['last_name'].value;
}
return '';
```

#### Runtime Fields (Modern Approach)

**Characteristics:**
```
Runtime Fields:
├── ✅ Defined at index mapping level
├── ✅ Reusable across multiple data views
├── ✅ Can be shared via index templates
├── ✅ Better performance optimization
├── ✅ Elasticsearch-native feature
├── ✅ Future-proof technology
└── ❌ Requires Elasticsearch 7.11+
```

**Example Runtime Field:**
```json
{
  "runtime_mappings": {
    "full_name": {
      "type": "keyword",
      "script": {
        "source": """
          if (doc['first_name'].size() > 0 && doc['last_name'].size() > 0) {
            emit(doc['first_name'].value + ' ' + doc['last_name'].value);
          }
        """
      }
    }
  }
}
```

### Migration from Scripted to Runtime Fields

#### Migration Strategy

**Step 1: Audit Existing Scripted Fields**
```bash
# Export all scripted fields
GET .kibana/_search
{
  "query": {
    "term": {
      "type": "index-pattern"
    }
  },
  "_source": ["index-pattern.fields"]
}
```

**Step 2: Convert Script Logic**
```javascript
// Old scripted field syntax
if (doc['amount'].size() > 0) {
  return doc['amount'].value * 1.1;
}

// New runtime field syntax
if (doc['amount'].size() > 0) {
  emit(doc['amount'].value * 1.1);
}
```

**Step 3: Test and Validate**
```json
{
  "query": {
    "match_all": {}
  },
  "runtime_mappings": {
    "test_field": {
      "type": "double",
      "script": {
        "source": "emit(doc['amount'].value * 1.1)"
      }
    }
  },
  "fields": ["test_field"],
  "size": 10
}
```

## 🚀 Performance Considerations

### Field Operation Performance

#### Query Performance Impact

**Performance Hierarchy:**
```
Field Operation Performance (Fast → Slow):
├── 1. Stored Fields (keyword, numeric)
├── 2. doc_values Fields (aggregation-optimized)
├── 3. Runtime Fields (simple calculations)
├── 4. Runtime Fields (complex calculations)
├── 5. Scripted Fields (legacy)
└── 6. Full-text Search on text fields
```

#### Optimization Strategies

**Efficient Field Design:**
```json
{
  "mappings": {
    "properties": {
      "status": {
        "type": "keyword",
        "doc_values": true,     // Enable fast aggregations
        "index": true           // Enable fast filtering
      },
      "description": {
        "type": "text",
        "index": true,          // Enable search
        "doc_values": false     // Disable aggregations (not needed)
      },
      "amount": {
        "type": "scaled_float",
        "scaling_factor": 100,
        "doc_values": true      // Enable numeric aggregations
      }
    }
  }
}
```

### Runtime Field Performance

#### Optimization Techniques

**Caching Strategy:**
```json
{
  "runtime_mappings": {
    "optimized_calculation": {
      "type": "keyword",
      "script": {
        "source": """
          // Cache expensive calculations
          if (doc['expensive_field'].size() > 0) {
            String cached = doc['expensive_field'].value;
            // Perform calculation once
            emit(cached.substring(0, 10));
          }
        """
      }
    }
  }
}
```

**Conditional Logic Optimization:**
```json
{
  "runtime_mappings": {
    "smart_calculation": {
      "type": "keyword",
      "script": {
        "source": """
          // Early exit for performance
          if (doc['type'].size() == 0) {
            return;
          }
          
          String type = doc['type'].value;
          
          // Use switch-like logic for performance
          if (type.equals('A')) {
            emit('Category A');
          } else if (type.equals('B')) {
            emit('Category B');
          } else {
            emit('Other');
          }
        """
      }
    }
  }
}
```

### Memory and Resource Management

#### Field Count Optimization

**Index Settings:**
```json
{
  "settings": {
    "index": {
      "mapping": {
        "total_fields": {
          "limit": 1000        // Limit total fields
        },
        "nested_fields": {
          "limit": 50          // Limit nested fields
        },
        "depth": {
          "limit": 20          // Limit object depth
        }
      }
    }
  }
}
```

**Field Filtering:**
```json
{
  "mappings": {
    "properties": {
      "metadata": {
        "type": "object",
        "enabled": false       // Disable indexing/searching
      },
      "debug_info": {
        "type": "text",
        "index": false         // Store but don't index
      }
    }
  }
}
```

## 📈 Field Analysis and Statistics

### Field Distribution Analysis

#### Statistical Summaries

**Numeric Field Statistics:**
```json
{
  "aggs": {
    "amount_stats": {
      "stats": {
        "field": "order_amount"
      }
    },
    "amount_percentiles": {
      "percentiles": {
        "field": "order_amount",
        "percents": [25, 50, 75, 90, 95, 99]
      }
    }
  }
}
```

**Response Format:**
```json
{
  "amount_stats": {
    "count": 10000,
    "min": 5.99,
    "max": 2499.99,
    "avg": 156.78,
    "sum": 1567800.00
  },
  "amount_percentiles": {
    "values": {
      "25.0": 49.99,
      "50.0": 99.99,
      "75.0": 199.99,
      "90.0": 399.99,
      "95.0": 599.99,
      "99.0": 1199.99
    }
  }
}
```

#### Cardinality Analysis

**Field Uniqueness Assessment:**
```json
{
  "aggs": {
    "unique_customers": {
      "cardinality": {
        "field": "customer_id.keyword"
      }
    },
    "unique_products": {
      "cardinality": {
        "field": "product_id.keyword"
      }
    }
  }
}
```

### Data Quality Assessment

#### Field Completeness Analysis

**Missing Value Detection:**
```json
{
  "aggs": {
    "total_docs": {
      "value_count": {
        "field": "_id"
      }
    },
    "non_null_email": {
      "value_count": {
        "field": "email.keyword"
      }
    },
    "email_completeness": {
      "bucket_script": {
        "buckets_path": {
          "total": "total_docs",
          "non_null": "non_null_email"
        },
        "script": "params.non_null / params.total * 100"
      }
    }
  }
}
```

#### Data Pattern Analysis

**Format Consistency Checking:**
```json
{
  "runtime_mappings": {
    "email_format_valid": {
      "type": "boolean",
      "script": {
        "source": """
          if (doc['email'].size() > 0) {
            String email = doc['email'].value;
            // Simple email validation
            emit(email.contains('@') && email.contains('.'));
          } else {
            emit(false);
          }
        """
      }
    }
  }
}
```

### Performance Monitoring

#### Field Usage Analytics

**Query Performance Tracking:**
```json
{
  "aggs": {
    "field_usage_stats": {
      "terms": {
        "field": "field_name",
        "size": 100
      },
      "aggs": {
        "avg_query_time": {
          "avg": {
            "field": "query_duration_ms"
          }
        }
      }
    }
  }
}
```

## 🔧 Practical Implementation Examples

### E-commerce Analytics Implementation

#### Product Performance Analysis

**Data Structure:**
```json
{
  "product_id": "PROD-12345",
  "product_name": "Wireless Headphones",
  "category": "Electronics",
  "price": 199.99,
  "cost": 89.99,
  "orders_count": 150,
  "revenue": 29998.50,
  "rating": 4.3,
  "reviews_count": 87,
  "launch_date": "2024-01-15"
}
```

**Runtime Field Calculations:**
```json
{
  "runtime_mappings": {
    "profit_margin": {
      "type": "double",
      "script": {
        "source": """
          if (doc['price'].size() > 0 && doc['cost'].size() > 0) {
            double price = doc['price'].value;
            double cost = doc['cost'].value;
            emit(((price - cost) / price) * 100);
          }
        """
      }
    },
    "performance_score": {
      "type": "double",
      "script": {
        "source": """
          if (doc['orders_count'].size() > 0 && doc['rating'].size() > 0) {
            double orders = doc['orders_count'].value;
            double rating = doc['rating'].value;
            // Weighted score: 70% orders, 30% rating
            emit((orders * 0.7) + (rating * 20 * 0.3));
          }
        """
      }
    },
    "product_lifecycle": {
      "type": "keyword",
      "script": {
        "source": """
          if (doc['launch_date'].size() > 0) {
            LocalDate launch = LocalDate.parse(doc['launch_date'].value);
            LocalDate now = LocalDate.now();
            long daysSinceLaunch = ChronoUnit.DAYS.between(launch, now);
            
            if (daysSinceLaunch < 30) {
              emit('New');
            } else if (daysSinceLaunch < 90) {
              emit('Growing');
            } else if (daysSinceLaunch < 365) {
              emit('Mature');
            } else {
              emit('Legacy');
            }
          }
        """
      }
    }
  }
}
```

### Security Event Analysis

#### Threat Detection Fields

**Security Event Structure:**
```json
{
  "event_id": "SEC-2024-001",
  "timestamp": "2024-01-15T10:30:00Z",
  "source_ip": "192.168.1.100",
  "destination_ip": "10.0.0.50",
  "event_type": "authentication",
  "outcome": "failure",
  "user_agent": "Mozilla/5.0...",
  "failed_attempts": 5,
  "geo_location": "New York, US"
}
```

**Security Runtime Fields:**
```json
{
  "runtime_mappings": {
    "threat_level": {
      "type": "keyword",
      "script": {
        "source": """
          int attempts = doc['failed_attempts'].value;
          String outcome = doc['outcome'].value;
          
          if (outcome.equals('failure')) {
            if (attempts > 10) {
              emit('Critical');
            } else if (attempts > 5) {
              emit('High');
            } else if (attempts > 2) {
              emit('Medium');
            } else {
              emit('Low');
            }
          } else {
            emit('Normal');
          }
        """
      }
    },
    "ip_reputation": {
      "type": "keyword",
      "script": {
        "source": """
          String sourceIp = doc['source_ip'].value;
          
          // Check for private IP ranges
          if (sourceIp.startsWith('192.168.') || 
              sourceIp.startsWith('10.') || 
              sourceIp.startsWith('172.16.')) {
            emit('Internal');
          } else {
            emit('External');
          }
        """
      }
    },
    "time_based_anomaly": {
      "type": "boolean",
      "script": {
        "source": """
          if (doc['@timestamp'].size() > 0) {
            ZonedDateTime timestamp = doc['@timestamp'].value;
            int hour = timestamp.getHour();
            
            // Flag events outside business hours as anomalous
            emit(hour < 7 || hour > 19);
          }
        """
      }
    }
  }
}
```

### IoT Device Monitoring

#### Device Health Metrics

**Device Data Structure:**
```json
{
  "device_id": "IOT-SENSOR-001",
  "device_type": "temperature_sensor",
  "location": "Building A - Floor 3",
  "temperature": 22.5,
  "humidity": 45.2,
  "battery_level": 87,
  "signal_strength": -65,
  "last_maintenance": "2024-01-01",
  "firmware_version": "1.2.3"
}
```

**IoT Runtime Fields:**
```json
{
  "runtime_mappings": {
    "device_health": {
      "type": "keyword",
      "script": {
        "source": """
          int battery = doc['battery_level'].value;
          int signal = doc['signal_strength'].value;
          
          if (battery > 70 && signal > -70) {
            emit('Excellent');
          } else if (battery > 50 && signal > -80) {
            emit('Good');
          } else if (battery > 30 && signal > -90) {
            emit('Fair');
          } else {
            emit('Poor');
          }
        """
      }
    },
    "maintenance_due": {
      "type": "boolean",
      "script": {
        "source": """
          if (doc['last_maintenance'].size() > 0) {
            LocalDate lastMaintenance = LocalDate.parse(doc['last_maintenance'].value);
            LocalDate now = LocalDate.now();
            long daysSinceMaintenance = ChronoUnit.DAYS.between(lastMaintenance, now);
            
            emit(daysSinceMaintenance > 90);
          }
        """
      }
    },
    "environmental_status": {
      "type": "keyword",
      "script": {
        "source": """
          if (doc['temperature'].size() > 0 && doc['humidity'].size() > 0) {
            double temp = doc['temperature'].value;
            double humidity = doc['humidity'].value;
            
            if (temp < 18 || temp > 26 || humidity < 30 || humidity > 70) {
              emit('Out of Range');
            } else {
              emit('Normal');
            }
          }
        """
      }
    }
  }
}
```

## 📚 Best Practices Summary

### Field Design Principles

1. **Consistent Naming**: Use standardized field naming conventions
2. **Type Optimization**: Choose appropriate field types for intended use
3. **Performance First**: Consider query performance in field design
4. **Documentation**: Maintain comprehensive field documentation
5. **Future-Proofing**: Design for evolving business requirements

### Runtime Field Guidelines

1. **Simple Calculations**: Keep runtime field logic simple for performance
2. **Null Handling**: Always handle null values gracefully
3. **Caching**: Cache expensive operations when possible
4. **Testing**: Thoroughly test runtime fields before production use
5. **Migration**: Plan migration from scripted to runtime fields

### Performance Optimization

1. **Index Templates**: Use consistent mappings across indices
2. **Field Limits**: Monitor and control field count
3. **Query Optimization**: Design fields for query patterns
4. **Resource Monitoring**: Track field operation performance
5. **Regular Maintenance**: Review and optimize field usage regularly

Field management is fundamental to effective Kibana analytics. Master these concepts to create efficient, maintainable, and performant data analysis workflows that scale with your organization's needs.