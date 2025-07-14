# Data Views & Index Patterns

**Master the foundation of Kibana data connectivity and field management**

*Estimated reading time: 25 minutes*

## Overview

Data views (formerly known as index patterns) are the cornerstone of Kibana's data connectivity. They define how Kibana connects to your Elasticsearch indices, interprets field types, and structures data for visualization and analysis. Understanding data views is essential for effective data exploration and building meaningful dashboards.

## 🎯 What Are Data Views?

### Core Concept

A data view is a configuration layer that:
- **Connects** Kibana to one or more Elasticsearch indices
- **Maps** field types for proper visualization handling
- **Defines** time fields for time-based analysis
- **Configures** field formatting and display options
- **Enables** data exploration and visualization creation

### Data Views vs Index Patterns

```
Legacy Term: Index Patterns (Kibana < 8.0)
Modern Term: Data Views (Kibana 8.0+)

Same Functionality:
├── Connect to Elasticsearch indices
├── Define field mappings and types
├── Configure time fields
├── Set up field formatting
└── Enable data exploration
```

> **📝 Note:** While the terminology changed, the core functionality remains the same. Many users still refer to them as "index patterns."

## 🔧 How Data Views Connect Kibana to Elasticsearch

### Connection Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Kibana      │    │   Data Views    │    │ Elasticsearch   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Visualizations│ │◄──►│ │Field Mapping│ │◄──►│ │   Indices   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Discover    │ │◄──►│ │Time Field   │ │◄──►│ │   Mappings  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Dashboard   │ │◄──►│ │Index Pattern│ │◄──►│ │   Documents │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow Process

1. **Index Discovery**: Kibana queries Elasticsearch for available indices
2. **Field Mapping**: Retrieves field types and structures from index mappings
3. **Data View Creation**: Configures how fields should be displayed and used
4. **Runtime Processing**: Applies formatting and type conversions during queries
5. **Visualization Binding**: Makes data available for charts and dashboards

## 🏗️ Creating Data Views

### Prerequisites

Before creating data views, ensure you have:
- ✅ Elasticsearch running and accessible
- ✅ Data indexed in Elasticsearch
- ✅ Appropriate permissions in Kibana
- ✅ Understanding of your data structure

### Step-by-Step Creation Process

#### Method 1: Using the Data Views Management Interface

**Navigation Path:**
```
Kibana → Management → Stack Management → Data Views
```

**Creation Steps:**

1. **Access Data Views Management**
   - Click hamburger menu (☰) → Management
   - Select "Stack Management" from the Management section
   - Choose "Data Views" from the Kibana section

2. **Create New Data View**
   - Click "Create data view" button
   - Enter data view configuration details

3. **Configure Index Pattern**
   ```
   Index Pattern Examples:
   ├── Single index: "sales-2024"
   ├── Multiple indices: "logs-*"
   ├── Date-based: "application-logs-2024-*"
   ├── Multiple patterns: "sales-*,orders-*"
   └── Cross-cluster: "cluster1:logs-*,cluster2:logs-*"
   ```

4. **Select Time Field**
   - Choose timestamp field for time-based analysis
   - Common time fields: `@timestamp`, `timestamp`, `created_at`, `event_time`
   - Select "No time field" for non-time-based data

5. **Configure Advanced Options**
   - Custom data view ID
   - Namespace settings
   - Allow hidden indices

#### Method 2: From Discover Application

**Quick Creation Workflow:**

1. **Navigate to Discover**
   - Main menu → Analytics → Discover

2. **Create from Discover**
   - Click "Create data view" link
   - Follow guided setup process
   - Automatically opens in Discover after creation

#### Method 3: Using Kibana API

**Programmatic Creation:**

```bash
# Create data view via API
curl -X POST "localhost:5601/api/data_views/data_view" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{
    "data_view": {
      "title": "sales-*",
      "timeFieldName": "@timestamp",
      "name": "Sales Data"
    }
  }'
```

### Configuration Options

#### Basic Configuration

| Setting | Description | Example |
|---------|-------------|---------|
| **Name** | Display name for the data view | "Web Server Logs" |
| **Index Pattern** | Elasticsearch index pattern | "logs-nginx-*" |
| **Time Field** | Field for time-based filtering | "@timestamp" |
| **Custom ID** | Unique identifier | "web-logs-001" |

#### Advanced Configuration

```yaml
Advanced Settings:
  allow_no_index: true          # Allow pattern with no matching indices
  namespace: "default"          # Space-specific namespace
  source_filters:              # Include/exclude fields from _source
    - "password"               # Exclude sensitive fields
    - "internal.*"             # Exclude internal fields
  field_formats:               # Custom field formatting
    bytes_field: "bytes"       # Format as bytes
    price_field: "currency"    # Format as currency
  runtime_mappings:            # Dynamic field definitions
    full_name:
      type: "keyword"
      script: "emit(doc['first_name'].value + ' ' + doc['last_name'].value)"
```

## 🔍 Index Pattern Syntax and Wildcards

### Wildcard Patterns

#### Basic Wildcards

| Pattern | Description | Matches |
|---------|-------------|---------|
| `*` | Matches any characters | `logs-*` matches `logs-app`, `logs-nginx` |
| `?` | Matches single character | `log-202?` matches `log-2023`, `log-2024` |
| `[abc]` | Matches any character in brackets | `logs-[123]` matches `logs-1`, `logs-2`, `logs-3` |
| `[a-z]` | Matches character range | `logs-[a-z]` matches `logs-a` through `logs-z` |

#### Advanced Pattern Examples

```bash
# Date-based patterns
"application-logs-2024-*"           # Monthly indices
"metrics-2024-??-*"                 # Daily indices with specific format
"events-2024-[01-12]-*"             # Specific month range

# Service-based patterns
"logs-{web,api,db}-*"               # Multiple specific services
"application-{prod,staging}-*"      # Environment-specific
"*-errors-*"                        # Error logs across all services

# Complex combinations
"logs-{web,api}-{prod,staging}-202[3-4]-*"  # Multiple dimensions
"application-*-!(test|dev)-*"       # Exclude specific environments
```

### Pattern Matching Rules

#### Inclusion Patterns

```bash
# Single index
sales-2024

# Multiple related indices
logs-application-*

# Cross-service patterns
{sales,orders,inventory}-*

# Time-based rollover
application-logs-2024-*
```

#### Exclusion Patterns

```bash
# Exclude specific indices (using external tooling)
logs-* AND NOT logs-test-*

# Exclude by date range
logs-2024-* AND NOT logs-2024-01-*

# Exclude by service
application-* AND NOT application-debug-*
```

### Best Practices for Index Patterns

#### ✅ Recommended Patterns

```bash
# Good: Logical grouping
"web-logs-*"                    # Clear purpose
"sales-data-2024-*"             # Includes time scope
"metrics-{cpu,memory,disk}-*"   # Specific metrics

# Good: Consistent naming
"app-logs-prod-*"               # Environment clear
"user-events-*"                 # Purpose clear
"system-metrics-*"              # Category clear
```

#### ❌ Patterns to Avoid

```bash
# Bad: Too broad
"*"                             # Matches everything
"log*"                          # Too generic

# Bad: Inconsistent naming
"logs_some_app*"                # Mixed naming conventions
"random-pattern-*"              # Unclear purpose

# Bad: Performance issues
"*-*-*-*-*"                     # Overly complex patterns
```

## ⏰ Time Field Configuration

### Understanding Time Fields

Time fields enable:
- **Time-based filtering** in Discover and dashboards
- **Temporal visualizations** (line charts, heatmaps)
- **Time range controls** and auto-refresh
- **Time-based aggregations** and bucketing

### Common Time Field Types

#### Elasticsearch Time Field Formats

| Format | Example | Description |
|---------|---------|-------------|
| `date` | `2024-01-15T10:30:00Z` | ISO 8601 timestamp |
| `epoch_millis` | `1705320600000` | Unix timestamp in milliseconds |
| `epoch_second` | `1705320600` | Unix timestamp in seconds |
| `date_nanos` | `1705320600000000000` | Nanosecond precision |

#### Custom Date Formats

```json
{
  "mappings": {
    "properties": {
      "custom_date": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss"
      },
      "log_timestamp": {
        "type": "date",
        "format": "MMM dd, yyyy @ HH:mm:ss.SSS"
      }
    }
  }
}
```

### Time Field Selection Guidelines

#### Choosing the Right Time Field

```
Primary Time Field Selection:
├── @timestamp (most common)
├── timestamp
├── event_time
├── created_at
├── occurred_at
└── log_date

Secondary Considerations:
├── Data completeness (no null values)
├── Consistent format across documents
├── Appropriate time range coverage
└── Business relevance
```

#### Multiple Time Fields

```json
{
  "order": {
    "created_at": "2024-01-15T10:30:00Z",    # Order creation
    "updated_at": "2024-01-15T11:45:00Z",    # Last modification
    "shipped_at": "2024-01-16T09:15:00Z",    # Shipping timestamp
    "delivered_at": "2024-01-18T14:20:00Z"   # Delivery timestamp
  }
}
```

**Selection Strategy:**
- **Primary**: Use `created_at` for general time-based analysis
- **Specific**: Switch to `shipped_at` for shipping analytics
- **Runtime**: Create additional data views for different time perspectives

### Time Field Configuration

#### During Data View Creation

1. **Automatic Detection**
   - Kibana scans for date fields
   - Suggests most appropriate time field
   - Shows field statistics and distribution

2. **Manual Selection**
   - Review available date fields
   - Consider field completeness
   - Evaluate time range coverage

3. **No Time Field Option**
   - Choose for non-temporal data
   - Disables time-based filtering
   - Suitable for reference data

#### Post-Creation Modifications

```bash
# Update time field via API
curl -X POST "localhost:5601/api/data_views/data_view/{id}" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{
    "data_view": {
      "timeFieldName": "event_timestamp"
    }
  }'
```

## 🎛️ Field Management and Mapping

### Field Type Understanding

#### Elasticsearch Field Types in Kibana

| ES Type | Kibana Treatment | Visualization Options |
|---------|------------------|----------------------|
| `keyword` | Categorical/String | Terms, filters, word clouds |
| `text` | Full-text search | Search, not aggregatable |
| `long`, `integer` | Numeric | Histograms, metrics, gauges |
| `float`, `double` | Numeric | Line charts, metrics |
| `boolean` | Boolean | Binary visualizations |
| `date` | Time-based | Time series, calendars |
| `geo_point` | Geographic | Maps, geographic visualizations |
| `ip` | IP Address | Network analysis, geographic |

#### Field Properties and Metadata

```json
{
  "field_name": {
    "type": "keyword",
    "aggregatable": true,     # Can be used in aggregations
    "searchable": true,       # Can be searched
    "scripted": false,        # Is a scripted field
    "doc_values": true,       # Stored for fast aggregations
    "indexed": true,          # Included in search index
    "customLabel": "Product Category",  # Custom display name
    "format": "string"        # Display format
  }
}
```

### Field Customization

#### Custom Field Labels

**Purpose**: Improve user experience with descriptive names

```
Field Customization Examples:
├── "user_id" → "User ID"
├── "response_time_ms" → "Response Time (ms)"
├── "geo.coordinates" → "Location"
├── "event.category" → "Event Category"
└── "bytes_sent" → "Bytes Transferred"
```

**Configuration Steps:**
1. Navigate to Data Views → Select data view
2. Find field in field list
3. Click edit icon (pencil)
4. Enter custom label
5. Save changes

#### Field Formatting

**Numeric Formatting:**

| Format Type | Example Input | Formatted Output |
|-------------|---------------|------------------|
| `Number` | `1234.56` | `1,234.56` |
| `Bytes` | `1024` | `1 KB` |
| `Percent` | `0.85` | `85%` |
| `Currency` | `123.45` | `$123.45` |
| `Duration` | `3661` | `1h 1m 1s` |

**Date Formatting:**

```javascript
// Common date format patterns
'YYYY-MM-DD HH:mm:ss'     // 2024-01-15 10:30:00
'MMM DD, YYYY @ HH:mm'    // Jan 15, 2024 @ 10:30
'dddd, MMMM Do YYYY'      // Monday, January 15th 2024
'relative'                // 2 hours ago
'YYYY-MM-DD'              // 2024-01-15
```

#### URL Field Formatting

**Link Templates:**

```bash
# Basic URL template
https://example.com/user/{{value}}

# Complex URL with multiple parameters
https://dashboard.com/logs?host={{host}}&service={{service}}&time={{timestamp}}

# Search URLs
https://google.com/search?q={{value}}
```

### Scripted Fields

#### Creating Calculated Fields

**Common Use Cases:**
- Combining multiple fields
- Mathematical calculations
- String manipulations
- Conditional logic

**Examples:**

```javascript
// Full name from first and last name
if (doc['first_name'].size() > 0 && doc['last_name'].size() > 0) {
  return doc['first_name'].value + ' ' + doc['last_name'].value;
}

// Calculate response time in seconds
return doc['response_time_ms'].value / 1000;

// Categorize values
if (doc['amount'].value > 1000) {
  return 'High';
} else if (doc['amount'].value > 100) {
  return 'Medium';
} else {
  return 'Low';
}
```

#### Runtime Fields (Modern Alternative)

**Runtime Field Definition:**

```json
{
  "runtime_mappings": {
    "full_name": {
      "type": "keyword",
      "script": {
        "source": "emit(doc['first_name'].value + ' ' + doc['last_name'].value)"
      }
    },
    "response_time_seconds": {
      "type": "double",
      "script": {
        "source": "emit(doc['response_time_ms'].value / 1000.0)"
      }
    }
  }
}
```

### Field Management Best Practices

#### Organization Strategies

```
Field Organization:
├── Core Business Fields
│   ├── customer_id → "Customer ID"
│   ├── product_name → "Product Name"
│   └── order_amount → "Order Amount"
├── Technical Fields
│   ├── @timestamp → "Timestamp"
│   ├── host.name → "Server Name"
│   └── response_code → "HTTP Status"
└── Calculated Fields
    ├── full_name → "Full Name"
    ├── profit_margin → "Profit Margin %"
    └── category_group → "Category Group"
```

#### Performance Considerations

**Efficient Field Usage:**

```bash
# Good: Use doc_values for aggregations
GET /sales/_search
{
  "aggs": {
    "categories": {
      "terms": {
        "field": "category.keyword"    # Efficient aggregation
      }
    }
  }
}

# Bad: Avoid script-heavy calculations in visualizations
# Instead: Pre-calculate during indexing or use runtime fields
```

## 🔧 Best Practices for Data View Setup

### Naming Conventions

#### Descriptive Data View Names

```
Recommended Naming Patterns:
├── Purpose-Environment: "Web Logs - Production"
├── Service-Type: "API Metrics - Performance"
├── Department-Domain: "Sales - Transaction Data"
├── Time-Scope: "User Events - 2024"
└── System-Component: "Kubernetes - Pod Metrics"
```

#### Consistent Naming Standards

```yaml
Naming Standards:
  format: "{Purpose} - {Environment/Scope}"
  examples:
    - "Application Logs - Production"
    - "User Analytics - Marketing"
    - "System Metrics - Infrastructure"
    - "Security Events - SIEM"
  
  avoid:
    - Generic names: "logs", "data", "metrics"
    - Cryptic abbreviations: "app_lg_prd"
    - Inconsistent formats: "prod-logs", "LogsProduction"
```

### Index Pattern Optimization

#### Performance-Focused Patterns

**Efficient Patterns:**

```bash
# Good: Specific and targeted
"web-logs-nginx-*"              # Specific service
"metrics-cpu-{prod,staging}-*"  # Specific metrics and environments
"sales-transactions-2024-*"     # Time-bounded data

# Good: Logical grouping
"ecommerce-{orders,payments,shipping}-*"  # Related business processes
"monitoring-{alerts,metrics,traces}-*"    # Observability stack
```

**Avoid Performance Issues:**

```bash
# Bad: Too broad (impacts performance)
"*"                             # Matches all indices
"log*"                          # Too generic

# Bad: Overly complex
"*-*-*-{prod,staging,dev}-*-*"  # Complex matching
```

### Security and Access Control

#### Field-Level Security

```json
{
  "field_security": {
    "grant": ["@timestamp", "user.name", "event.action"],
    "except": ["user.password", "auth.token", "sensitive.*"]
  }
}
```

#### Role-Based Data Views

```yaml
Data View Access Strategy:
  public_views:
    - "Public Dashboard Data"
    - "General Metrics"
  
  department_views:
    - "HR - Employee Data"
    - "Finance - Transaction Data"
    - "Engineering - System Logs"
  
  admin_views:
    - "Security Events - Full Access"
    - "System Diagnostics - Complete"
```

### Data View Maintenance

#### Regular Maintenance Tasks

```bash
# Monthly Tasks:
├── Review field usage statistics
├── Update field formatting and labels
├── Clean up unused scripted fields
├── Optimize index patterns
└── Review and update time field selection

# Quarterly Tasks:
├── Audit data view permissions
├── Archive old data views
├── Update field mappings for new data
├── Review performance metrics
└── Document data view purposes
```

#### Version Control and Backup

```json
{
  "data_view_backup": {
    "export_method": "Kibana Export/Import",
    "backup_frequency": "weekly",
    "version_control": "git",
    "documentation": "required"
  }
}
```

## 🚨 Troubleshooting Common Issues

### Data View Creation Problems

#### Issue: "No matching indices found"

**Symptoms:**
- Cannot create data view with specific pattern
- Index pattern shows 0 matching indices
- Error message about missing indices

**Solutions:**

```bash
# 1. Verify indices exist
GET /_cat/indices?v

# 2. Check index pattern syntax
# Correct: logs-*
# Incorrect: logs*- (trailing dash)

# 3. Verify permissions
GET /_security/user/_privileges

# 4. Check index lifecycle
GET /logs-*/_settings
```

**Step-by-step Resolution:**

1. **Verify Index Existence**
   ```bash
   # List all indices
   curl -X GET "localhost:9200/_cat/indices?v"
   
   # Check specific pattern
   curl -X GET "localhost:9200/_cat/indices/logs-*"
   ```

2. **Validate Pattern Syntax**
   ```bash
   # Test pattern matching
   curl -X GET "localhost:9200/_resolve/index/logs-*"
   ```

3. **Check Permissions**
   - Navigate to Stack Management → Security → Roles
   - Verify user has "read" permissions on target indices
   - Check index privileges and document-level security

#### Issue: "Time field not available"

**Symptoms:**
- No time fields appear in dropdown
- Time field selection is disabled
- Created data view but time filtering doesn't work

**Solutions:**

```bash
# 1. Check field mappings
GET /your-index/_mapping

# 2. Verify date field format
GET /your-index/_search
{
  "query": {"match_all": {}},
  "size": 1,
  "_source": ["@timestamp", "timestamp"]
}

# 3. Check data types
GET /your-index/_field_caps?fields=*timestamp*
```

**Resolution Steps:**

1. **Verify Date Field Mapping**
   ```json
   {
     "mappings": {
       "properties": {
         "@timestamp": {
           "type": "date"  // Must be date type
         }
       }
     }
   }
   ```

2. **Check Data Format**
   ```bash
   # Ensure consistent date format
   "2024-01-15T10:30:00Z"  # ISO 8601 format
   "1705320600000"         # Unix timestamp
   ```

3. **Reindex if Necessary**
   ```json
   {
     "source": {"index": "old-index"},
     "dest": {"index": "new-index"},
     "script": {
       "source": "ctx._source['@timestamp'] = new Date(ctx._source['timestamp'])"
     }
   }
   ```

### Field Mapping Issues

#### Issue: "Field is not aggregatable"

**Symptoms:**
- Cannot create aggregations on text fields
- Visualization shows "field is not aggregatable"
- Charts display "No data" for text fields

**Solutions:**

```bash
# 1. Check field mapping
GET /your-index/_mapping/field/your-field

# 2. Use keyword subfield
field.keyword instead of field

# 3. Update mapping (requires reindexing)
PUT /new-index
{
  "mappings": {
    "properties": {
      "category": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword"
          }
        }
      }
    }
  }
}
```

#### Issue: "Scripted field errors"

**Symptoms:**
- Scripted fields show errors in Discover
- Visualizations fail with scripted field errors
- Performance issues with script execution

**Solutions:**

```javascript
// 1. Add null checking
if (doc['field'].size() > 0) {
  return doc['field'].value;
}
return null;

// 2. Use runtime fields instead
"runtime_mappings": {
  "calculated_field": {
    "type": "keyword",
    "script": {
      "source": "emit(doc['field1'].value + doc['field2'].value)"
    }
  }
}

// 3. Optimize script performance
if (doc.containsKey('field') && doc['field'].size() > 0) {
  return doc['field'].value;
}
```

### Performance Issues

#### Issue: "Data view loads slowly"

**Symptoms:**
- Long loading times in Discover
- Timeout errors in visualizations
- Slow field list population

**Solutions:**

```bash
# 1. Optimize index patterns
"specific-logs-*" instead of "logs-*"

# 2. Use doc_values for aggregations
"doc_values": true

# 3. Limit field count
"index.mapping.total_fields.limit": 1000

# 4. Use field filtering
"source_filtering": ["field1", "field2"]
```

#### Issue: "Too many fields in data view"

**Symptoms:**
- Slow field discovery
- Memory issues in Kibana
- Performance degradation

**Solutions:**

1. **Field Filtering**
   ```json
   {
     "index_patterns": ["logs-*"],
     "source_filters": ["@timestamp", "message", "level", "host"]
   }
   ```

2. **Multiple Focused Data Views**
   ```bash
   # Instead of one broad data view
   "logs-*" (1000+ fields)
   
   # Create focused data views
   "application-logs-*" (50 fields)
   "security-logs-*" (30 fields)
   "performance-logs-*" (20 fields)
   ```

### Common Error Messages

#### Error: "Forbidden: insufficient privileges"

**Solution:**
```bash
# Grant required permissions
POST /_security/role/kibana_user
{
  "indices": [{
    "names": ["logs-*"],
    "privileges": ["read", "view_index_metadata"]
  }]
}
```

#### Error: "Cannot read property 'value' of undefined"

**Solution:**
```javascript
// Add proper null checking in scripted fields
if (doc['field_name'].size() > 0) {
  return doc['field_name'].value;
}
return '';
```

#### Error: "Data view not found"

**Solution:**
```bash
# Check data view existence
GET /.kibana/_search
{
  "query": {
    "term": {
      "type": "index-pattern"
    }
  }
}

# Recreate if missing
POST /api/data_views/data_view
{
  "data_view": {
    "title": "your-pattern-*",
    "timeFieldName": "@timestamp"
  }
}
```

## 📊 Practical Examples

### Example 1: E-commerce Analytics Data View

**Scenario**: Online store with order, product, and customer data

**Index Structure:**
```bash
ecommerce-orders-2024-01    # Monthly order indices
ecommerce-products-*        # Product catalog
ecommerce-customers-*       # Customer data
```

**Data View Configuration:**
```json
{
  "title": "ecommerce-orders-*",
  "timeFieldName": "order_date",
  "name": "E-commerce Orders",
  "field_formats": {
    "order_total": {"format": "currency"},
    "customer_age": {"format": "number"},
    "shipping_weight": {"format": "bytes"}
  },
  "runtime_mappings": {
    "profit_margin": {
      "type": "double",
      "script": {
        "source": "emit((doc['order_total'].value - doc['cost_total'].value) / doc['order_total'].value * 100)"
      }
    }
  }
}
```

**KQL Query Examples:**
```kql
# High-value orders
order_total > 500 and customer_tier: "premium"

# Recent orders with shipping issues
order_date >= "2024-01-01" and shipping_status: "delayed"

# Product performance
product_category: "electronics" and order_total > 100
```

### Example 2: Application Monitoring Data View

**Scenario**: Microservices application with logs and metrics

**Index Structure:**
```bash
app-logs-api-prod-*         # API service logs
app-logs-web-prod-*         # Web service logs
app-metrics-*               # Application metrics
```

**Data View Configuration:**
```json
{
  "title": "app-logs-*-prod-*",
  "timeFieldName": "@timestamp",
  "name": "Production Application Logs",
  "field_formats": {
    "response_time": {"format": "duration"},
    "bytes_sent": {"format": "bytes"},
    "error_rate": {"format": "percent"}
  },
  "runtime_mappings": {
    "service_health": {
      "type": "keyword",
      "script": {
        "source": "if (doc['error_count'].value == 0) emit('healthy'); else if (doc['error_count'].value < 10) emit('warning'); else emit('critical');"
      }
    }
  }
}
```

**KQL Query Examples:**
```kql
# Error tracking
log.level: "ERROR" and service.name: "api"

# Performance monitoring
response_time > 1000 and http.response.status_code: 200

# Service health
service.name: "web" and @timestamp >= "now-1h"
```

### Example 3: Security Event Data View

**Scenario**: Security monitoring with authentication and network logs

**Index Structure:**
```bash
security-auth-*             # Authentication events
security-network-*          # Network security events
security-alerts-*           # Security alerts
```

**Data View Configuration:**
```json
{
  "title": "security-*",
  "timeFieldName": "event.created",
  "name": "Security Events",
  "field_formats": {
    "source.ip": {"format": "ip"},
    "destination.port": {"format": "number"},
    "event.risk_score": {"format": "number"}
  },
  "runtime_mappings": {
    "threat_level": {
      "type": "keyword",
      "script": {
        "source": "if (doc['event.risk_score'].value > 75) emit('high'); else if (doc['event.risk_score'].value > 50) emit('medium'); else emit('low');"
      }
    }
  }
}
```

**KQL Query Examples:**
```kql
# Failed authentication attempts
event.action: "authentication_failure" and source.ip: *

# High-risk events
event.risk_score > 75 and event.outcome: "failure"

# Network anomalies
network.protocol: "tcp" and destination.port: (22 or 3389)
```

## 🔗 Next Steps

Now that you understand data views and index patterns:

1. **Explore Your Data** → [Discover Application](discover-application.md)
2. **Create Visualizations** → [Kibana Lens Basics](../03-visualization-fundamentals/kibana-lens-basics.md)
3. **Build Dashboards** → [Dashboard Creation](../05-dashboards-collaboration/dashboard-creation.md)

## 📚 Quick Reference

### Essential Data View Commands

```bash
# Create data view
POST /api/data_views/data_view
{
  "data_view": {
    "title": "logs-*",
    "timeFieldName": "@timestamp"
  }
}

# List data views
GET /api/data_views

# Update data view
PUT /api/data_views/data_view/{id}

# Delete data view
DELETE /api/data_views/data_view/{id}
```

### Common Index Patterns

```bash
# Time-based patterns
logs-YYYY-MM-DD
metrics-YYYY-MM-*
events-YYYY-*

# Service-based patterns
app-{service}-{env}-*
{service}-logs-*
monitoring-{type}-*

# Multi-pattern combinations
{logs,metrics,traces}-*
application-{prod,staging}-*
```

### Field Type Quick Reference

| Elasticsearch Type | Kibana Usage | Best For |
|-------------------|--------------|----------|
| `keyword` | Terms aggregation | Categories, IDs |
| `text` | Full-text search | Content, descriptions |
| `date` | Time filtering | Timestamps, dates |
| `long/double` | Numeric aggregation | Metrics, counts |
| `boolean` | Binary filtering | Status, flags |
| `ip` | IP analysis | Network addresses |
| `geo_point` | Map visualization | Locations, coordinates |

Data views are your gateway to effective data analysis in Kibana. Master these concepts to unlock the full potential of your Elasticsearch data for visualization and insights!