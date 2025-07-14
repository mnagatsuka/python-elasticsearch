# Discover Application

**Master data exploration and analysis with Kibana's powerful search and discovery interface**

*Estimated reading time: 30 minutes*

## Overview

The Discover application is Kibana's primary data exploration tool, providing an intuitive interface for searching, filtering, and analyzing your Elasticsearch data. It serves as the foundation for understanding your data structure, identifying patterns, and creating the insights that drive visualizations and dashboards.

## 🎯 Core Purpose

Discover transforms raw Elasticsearch data into actionable insights by providing:

- **Interactive Data Exploration** - Search and filter through millions of documents
- **Real-time Analysis** - Live data updates and instant search results
- **Pattern Recognition** - Identify trends, anomalies, and data relationships
- **Field-Level Insights** - Analyze individual fields and their distributions
- **Collaborative Discovery** - Save and share searches with team members

## 🏗️ Interface Layout and Navigation

### Main Interface Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Kibana Header                              │
├─────────────────────────────────────────────────────────────────┤
│ Search Bar                                     Time Range      │
├─────────────────────────────────────────────────────────────────┤
│ Fields   │                                                     │
│ Sidebar  │              Document Table                        │
│          │                                                     │
│ Available│              - Timestamp                           │
│ Fields   │              - Source Data                         │
│          │              - Expanded Documents                  │
│ Popular  │                                                     │
│ Fields   │                                                     │
│          │                                                     │
│ Selected │                                                     │
│ Fields   │                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Navigation Elements

| Component | Purpose | Location |
|-----------|---------|----------|
| **Data View Selector** | Choose data source | Top-left dropdown |
| **Search Bar** | Enter KQL queries | Center top |
| **Time Range Picker** | Set time filters | Top-right |
| **Fields Sidebar** | Explore field data | Left panel |
| **Document Table** | View search results | Main area |
| **Histogram** | Time distribution | Above table |

### Interface Navigation Path

**Access Discover:**
```
Kibana → Analytics → Discover
```

**Alternative Access:**
```
Main Menu (☰) → Analytics → Discover
```

## 🔍 Document Table Exploration

### Document Table Overview

The document table is the heart of Discover, displaying search results in a structured, interactive format that allows deep exploration of your data.

#### Table Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Time                    │ Source Document                       │
├─────────────────────────┼───────────────────────────────────────┤
│ 2024-01-15 10:30:00    │ {                                     │
│                         │   "@timestamp": "2024-01-15T10:30:00Z" │
│                         │   "message": "User login successful"  │
│                         │   "user.id": "user123"               │
│                         │   "source.ip": "192.168.1.100"       │
│                         │ }                                     │
├─────────────────────────┼───────────────────────────────────────┤
│ 2024-01-15 10:29:45    │ { ... }                               │
└─────────────────────────┴───────────────────────────────────────┘
```

#### Document Display Modes

**1. Table View (Default)**
- Structured columns for selected fields
- Sortable by any field
- Compact view for large datasets
- Quick field addition/removal

**2. Document View**
- Full JSON document display
- Expandable/collapsible sections
- Field-by-field analysis
- Copy/export individual documents

**3. Source View**
- Raw Elasticsearch _source
- Formatted JSON with syntax highlighting
- Complete document structure
- Ideal for debugging and analysis

### Document Interaction Features

#### Expanding Documents

**Quick Expand:**
```
Click the (▶) arrow next to any document
└── Shows formatted JSON structure
└── Reveals all available fields
└── Provides field-level actions
```

**Field-Level Actions:**
- **Filter for Value** - Add positive filter
- **Filter Out Value** - Add negative filter
- **Column Toggle** - Show/hide field as column
- **Copy Field** - Copy field name or value

#### Document Actions

| Action | Purpose | Usage |
|--------|---------|-------|
| **View Details** | Full document examination | Click expand arrow |
| **Filter** | Create filters from values | Click filter icons |
| **Copy** | Copy document content | Right-click menu |
| **Share** | Share specific document | Document permalink |

### Advanced Document Analysis

#### Multi-Document Comparison

**Comparison Workflow:**
1. **Select Documents** - Use checkboxes to select multiple documents
2. **Compare View** - Click "Compare" to see side-by-side analysis
3. **Field Differences** - Highlight varying field values
4. **Pattern Analysis** - Identify common patterns and anomalies

#### Document Sampling

**Sample Controls:**
```
Sample Size Options:
├── 500 documents (default)
├── 1,000 documents
├── 5,000 documents
├── 10,000 documents
└── All documents (use with caution)
```

**Sampling Strategies:**
- **Random Sampling** - Representative data sample
- **Time-based Sampling** - Recent data priority
- **Filtered Sampling** - Sample from filtered results
- **Stratified Sampling** - Sample across different categories

## ⏰ Time-Based Filtering and Analysis

### Time Range Selection

#### Quick Time Ranges

| Range | Description | Use Case |
|-------|-------------|----------|
| **Last 15 minutes** | Real-time monitoring | Live troubleshooting |
| **Last 1 hour** | Recent activity | Current session analysis |
| **Last 24 hours** | Daily operations | Daily reports |
| **Last 7 days** | Weekly trends | Weekly summaries |
| **Last 30 days** | Monthly analysis | Business reporting |
| **Last 90 days** | Quarterly view | Long-term trends |

#### Custom Time Ranges

**Absolute Time Selection:**
```
Start: 2024-01-15 09:00:00
End:   2024-01-15 17:00:00
Purpose: Specific business hours analysis
```

**Relative Time Selection:**
```
From: now-4h    (4 hours ago)
To:   now       (current time)
Purpose: Rolling window analysis
```

### Time-Based Analysis Features

#### Histogram Visualization

**Time Distribution Chart:**
```
Document Count
│
│     ▄▄▄
│    ▄█▄▄▄
│   ▄██▄▄▄▄
│  ▄███▄▄▄▄▄
│ ▄████▄▄▄▄▄▄
└─────────────────> Time
  09:00    17:00
```

**Histogram Interactions:**
- **Brush Selection** - Drag to zoom into time range
- **Click to Filter** - Click bar to filter to that time bucket
- **Hover Details** - Show exact count and time range
- **Interval Control** - Adjust time bucket size

#### Time-Based Patterns

**Peak Analysis:**
```kql
# Find peak activity hours
@timestamp >= "2024-01-15T00:00:00" and @timestamp <= "2024-01-15T23:59:59"

# Analyze by hour
@timestamp >= "now-1d" and message: "error"
```

**Trend Analysis:**
```kql
# Compare time periods
@timestamp >= "2024-01-01" and @timestamp <= "2024-01-07"  # Week 1
@timestamp >= "2024-01-08" and @timestamp <= "2024-01-14"  # Week 2
```

### Auto-Refresh Configuration

#### Real-Time Monitoring

**Refresh Intervals:**
| Interval | Purpose | Performance Impact |
|----------|---------|-------------------|
| **5 seconds** | Critical monitoring | High |
| **30 seconds** | Active monitoring | Medium |
| **1 minute** | Regular updates | Low |
| **5 minutes** | Periodic checks | Minimal |
| **15 minutes** | Batch updates | Minimal |

**Auto-Refresh Setup:**
```
Time Range Picker → Auto-refresh → Select Interval
├── Enable auto-refresh toggle
├── Choose refresh frequency
├── Monitor performance impact
└── Adjust based on data volume
```

## 📊 Field Sidebar and Analysis

### Field Sidebar Overview

The field sidebar provides comprehensive field-level analysis and quick access to data insights.

#### Sidebar Sections

```
┌─────────────────────┐
│  🔍 Search Fields   │
│                     │
│  📌 Selected Fields │
│  ├── @timestamp     │
│  ├── message        │
│  └── user.id        │
│                     │
│  📈 Available Fields│
│  ├── source.ip      │
│  ├── response_time  │
│  ├── status_code    │
│  └── ... (500+ more)│
│                     │
│  ⭐ Popular Fields  │
│  ├── @timestamp     │
│  ├── log.level      │
│  └── host.name      │
└─────────────────────┘
```

### Field Analysis Features

#### Field Statistics

**Hover Analysis:**
```
Field: status_code
├── Type: keyword
├── Aggregatable: Yes
├── Searchable: Yes
├── Top Values:
│   ├── 200: 45% (1,234 docs)
│   ├── 404: 30% (823 docs)
│   ├── 500: 15% (412 docs)
│   └── 301: 10% (275 docs)
└── Unique Values: 12
```

**Field Distribution:**
```
Field: response_time
├── Type: number
├── Min: 12ms
├── Max: 5,432ms
├── Average: 245ms
├── Median: 156ms
└── Distribution: [histogram visualization]
```

#### Field Actions

**Field Management:**
| Action | Purpose | Method |
|--------|---------|--------|
| **Add to Table** | Show as column | Click field name |
| **Filter** | Filter by field values | Click filter icon |
| **Visualize** | Create quick chart | Click visualize icon |
| **Edit** | Modify field properties | Click edit icon |

### Field Type Analysis

#### Text Fields

**Text Field Analysis:**
```
Field: message
├── Type: text
├── Searchable: Yes
├── Aggregatable: No
├── Common Terms:
│   ├── "error": 1,234 occurrences
│   ├── "success": 987 occurrences
│   ├── "warning": 456 occurrences
│   └── "info": 321 occurrences
└── Character Length: 50-200 chars
```

#### Numeric Fields

**Numeric Field Analysis:**
```
Field: bytes_sent
├── Type: long
├── Count: 2,744 documents
├── Min: 0 bytes
├── Max: 1,048,576 bytes
├── Average: 45,678 bytes
├── Percentiles:
│   ├── 50th: 32,768 bytes
│   ├── 90th: 98,304 bytes
│   └── 95th: 131,072 bytes
└── Distribution: Normal curve
```

#### Date Fields

**Date Field Analysis:**
```
Field: created_date
├── Type: date
├── Earliest: 2024-01-01T00:00:00Z
├── Latest: 2024-01-15T23:59:59Z
├── Span: 15 days
├── Gaps: None detected
└── Timezone: UTC
```

### Field Filtering and Selection

#### Smart Field Selection

**Auto-Selection Criteria:**
- Most frequently occurring fields
- Fields with high cardinality
- Time-based fields
- Fields with interesting patterns

**Manual Selection:**
```
Field Selection Strategy:
├── Business Critical Fields
│   ├── customer_id
│   ├── transaction_amount
│   └── order_status
├── Technical Fields
│   ├── @timestamp
│   ├── host.name
│   └── response_code
└── Analysis Fields
    ├── error_type
    ├── performance_metric
    └── user_agent
```

## 💾 Saved Searches and Sharing

### Creating Saved Searches

#### Save Search Workflow

**Basic Save Process:**
```
1. Configure Search
   ├── Set data view
   ├── Apply filters
   ├── Configure time range
   └── Select fields

2. Save Search
   ├── Click "Save" button
   ├── Enter descriptive name
   ├── Add description/tags
   └── Choose sharing options

3. Manage Saved Searches
   ├── View in Saved Objects
   ├── Edit search parameters
   ├── Update permissions
   └── Archive old searches
```

#### Saved Search Configuration

**Search Properties:**
```json
{
  "name": "High-Value Customer Transactions",
  "description": "Orders over $500 from premium customers",
  "data_view": "ecommerce-orders-*",
  "query": {
    "kql": "order_total > 500 and customer_tier: premium"
  },
  "filters": [
    {
      "field": "order_status",
      "value": "completed"
    }
  ],
  "time_range": {
    "from": "now-30d",
    "to": "now"
  },
  "selected_fields": [
    "customer_id",
    "order_total",
    "product_category",
    "order_date"
  ]
}
```

### Sharing Capabilities

#### Share Options

| Method | Purpose | Audience |
|--------|---------|----------|
| **Direct Link** | Quick sharing | Team members |
| **Embedded Link** | Integration | External systems |
| **Export CSV** | Data analysis | Spreadsheet users |
| **Export JSON** | Programming | Developers |
| **Dashboard Integration** | Visualization | Stakeholders |

#### Link Sharing

**Shareable URL Structure:**
```
https://kibana.company.com/app/discover#/
?_g=(time:(from:now-7d,to:now))
&_a=(discover:(columns:!(message,user.id),query:(kql:'error')))
```

**Link Parameters:**
- `_g`: Global state (time range, filters)
- `_a`: App-specific state (query, columns)
- Encoded for URL safety
- Preserves exact search state

#### Collaboration Features

**Team Collaboration:**
```
Sharing Workflow:
├── Create and Test Search
├── Save with Descriptive Name
├── Add Detailed Description
├── Tag for Categorization
├── Share Link with Team
├── Monitor Usage Statistics
└── Update Based on Feedback
```

**Permission Management:**
- **Read Access** - View saved searches
- **Edit Access** - Modify search parameters
- **Share Access** - Share with others
- **Delete Access** - Remove saved searches

### Export and Integration

#### Data Export Options

**CSV Export:**
```
Export Configuration:
├── Field Selection: All visible fields
├── Row Limit: 10,000 documents
├── Format: CSV with headers
├── Encoding: UTF-8
└── Compression: Optional ZIP
```

**JSON Export:**
```json
{
  "export_format": "json",
  "include_metadata": true,
  "document_limit": 10000,
  "fields": ["@timestamp", "message", "user.id"],
  "sort": [{"@timestamp": "desc"}]
}
```

#### API Integration

**Search API Usage:**
```bash
# Export search results programmatically
curl -X POST "localhost:5601/api/saved_objects/_export" \
  -H "Content-Type: application/json" \
  -H "kbn-xsrf: true" \
  -d '{
    "type": "search",
    "objects": [{"id": "search-id"}]
  }'
```

## 🔧 Advanced Search Techniques and KQL

### Kibana Query Language (KQL) Fundamentals

#### Basic KQL Syntax

**Simple Field Queries:**
```kql
# Exact match
user.name: "john.doe"

# Wildcard matching
user.name: john*

# Field existence
user.email: *

# Numeric comparisons
response_time > 1000
age >= 18 and age <= 65

# Boolean values
is_active: true
has_errors: false
```

**Logical Operators:**
```kql
# AND operator
status: "success" and response_time < 500

# OR operator
log.level: "error" or log.level: "warning"

# NOT operator
not log.level: "debug"

# Complex combinations
(status: "error" or status: "warning") and service.name: "api"
```

### Advanced KQL Patterns

#### Range Queries

**Numeric Ranges:**
```kql
# Price range
price >= 10 and price <= 100

# Response time analysis
response_time > 500 and response_time < 2000

# Age demographics
customer_age >= 25 and customer_age <= 45
```

**Date Ranges:**
```kql
# Specific date range
@timestamp >= "2024-01-01" and @timestamp <= "2024-01-31"

# Relative time
@timestamp >= "now-7d"

# Business hours
@timestamp >= "now/d+9h" and @timestamp <= "now/d+17h"
```

#### Text Search Patterns

**Partial Matching:**
```kql
# Prefix matching
user.name: admin*

# Suffix matching
file.name: *.log

# Contains matching
message: *error*

# Multiple wildcards
path: */logs/*/application.log
```

**Case Sensitivity:**
```kql
# Case-sensitive (keyword fields)
status.keyword: "Success"

# Case-insensitive (text fields)
message: "ERROR"  # Matches "error", "Error", "ERROR"
```

### Complex Query Examples

#### E-commerce Analytics

**High-Value Customer Analysis:**
```kql
# Premium customers with large orders
customer_tier: "premium" and order_total > 500 and order_status: "completed"

# Abandoned cart analysis
cart_status: "abandoned" and cart_value > 100 and @timestamp >= "now-7d"

# Product performance
product_category: "electronics" and (rating >= 4.5 or review_count > 100)
```

#### Log Analysis

**Error Investigation:**
```kql
# Critical errors in production
log.level: "ERROR" and environment: "production" and @timestamp >= "now-1h"

# Performance issues
response_time > 5000 or (status_code >= 500 and status_code < 600)

# Security events
event.category: "authentication" and event.outcome: "failure"
```

#### Infrastructure Monitoring

**Resource Usage:**
```kql
# High CPU usage
cpu.usage > 80 and @timestamp >= "now-30m"

# Memory alerts
memory.usage > 90 or swap.usage > 50

# Disk space warnings
disk.usage > 85 and host.name: prod-*
```

### KQL Best Practices

#### Performance Optimization

**Efficient Queries:**
```kql
# Good: Specific field targeting
status.keyword: "error"

# Bad: Broad text search
message: error

# Good: Combine filters efficiently
host.name: "web-01" and @timestamp >= "now-1h"

# Bad: Multiple separate queries
host.name: "web-01"
# ... then apply time filter separately
```

#### Query Structure

**Readable Query Format:**
```kql
# Multi-line for complex queries
(
  service.name: "api" or 
  service.name: "web"
) and (
  response_time > 1000 or 
  status_code >= 500
) and 
@timestamp >= "now-24h"
```

## 🔗 Integration with Other Kibana Applications

### Discover to Visualizations

#### Quick Visualization Creation

**From Field Analysis:**
```
Workflow:
├── Hover over field in sidebar
├── Click "Visualize" button
├── Choose visualization type
├── Auto-configure based on field type
└── Refine in Lens editor
```

**Supported Visualizations:**
- **Numeric Fields** → Line charts, bar charts, metrics
- **Keyword Fields** → Pie charts, data tables, word clouds
- **Date Fields** → Time series, calendars, heatmaps
- **Geographic Fields** → Maps, coordinate plots

#### Lens Integration

**Seamless Transition:**
```
Discover → Lens Workflow:
├── Select interesting fields
├── Apply relevant filters
├── Click "Visualize" from field
├── Lens opens with:
│   ├── Pre-configured data view
│   ├── Applied filters
│   ├── Selected fields
│   └── Suggested chart type
└── Customize visualization
```

### Dashboard Integration

#### Dashboard Creation from Discover

**Search to Dashboard:**
```
Integration Process:
├── Create and save search
├── Navigate to Dashboard
├── Add saved search panel
├── Configure display options
├── Combine with other visualizations
└── Save dashboard
```

**Dashboard Panel Options:**
- **Search Results Table** - Show raw search results
- **Aggregated Metrics** - Summary statistics
- **Field Distributions** - Top values and counts
- **Time Series** - Trend analysis over time

### Canvas Integration

#### Pixel-Perfect Reports

**Canvas Data Integration:**
```
Discover → Canvas:
├── Create detailed search
├── Save search for reuse
├── Open Canvas workpad
├── Add Discover element
├── Configure display format
└── Style for presentation
```

**Canvas Use Cases:**
- **Executive Reports** - Formatted data presentations
- **Operational Dashboards** - Real-time status displays
- **Custom Layouts** - Branded reporting templates
- **Infographics** - Visual data storytelling

### Machine Learning Integration

#### Anomaly Detection

**ML Job Creation:**
```
Discover → ML Workflow:
├── Identify interesting patterns
├── Create ML job based on search
├── Configure anomaly detection
├── Monitor for deviations
└── Alert on anomalies
```

**ML Analysis Types:**
- **Single Metric** - Monitor one field for anomalies
- **Multi-Metric** - Monitor multiple related fields
- **Population** - Compare entities within population
- **Advanced** - Custom ML configurations

### Alerting and Monitoring

#### Watcher Integration

**Alert Creation:**
```kql
# Create alert based on Discover search
# Alert when error rate exceeds threshold
log.level: "ERROR" and @timestamp >= "now-5m"

# Trigger when count > 10 in 5 minutes
# Email notification to ops team
```

**Alerting Workflow:**
```
Discover → Alerting:
├── Identify critical search patterns
├── Create watcher rule
├── Configure trigger conditions
├── Set up notification channels
└── Monitor alert effectiveness
```

## 🎯 Real-World Use Cases

### Use Case 1: E-commerce Order Analysis

**Scenario**: Analyze customer ordering patterns and identify high-value transactions

**Search Strategy:**
```kql
# Find high-value orders from premium customers
customer_tier: "premium" and order_total > 500 and order_status: "completed"

# Analyze seasonal patterns
product_category: "seasonal" and @timestamp >= "2024-12-01" and @timestamp <= "2024-12-31"

# Identify shipping issues
shipping_status: "delayed" and order_total > 100
```

**Analysis Workflow:**
1. **Time Range**: Set to business-relevant period
2. **Field Selection**: customer_id, order_total, product_category, shipping_status
3. **Filters**: Apply customer tier and order status filters
4. **Export**: Generate CSV for spreadsheet analysis
5. **Visualization**: Create charts showing order trends

### Use Case 2: Application Performance Monitoring

**Scenario**: Monitor web application performance and identify bottlenecks

**Search Strategy:**
```kql
# Find slow API responses
service.name: "api" and response_time > 5000 and @timestamp >= "now-1h"

# Identify error patterns
log.level: "ERROR" and service.name: "web" and @timestamp >= "now-24h"

# Monitor database performance
component: "database" and query_time > 1000
```

**Analysis Workflow:**
1. **Real-time Monitoring**: Set 30-second auto-refresh
2. **Field Focus**: response_time, error_message, endpoint, user_count
3. **Time Analysis**: Use histogram to identify peak error times
4. **Correlation**: Compare error rates with response times
5. **Alerting**: Set up alerts for performance degradation

### Use Case 3: Security Event Investigation

**Scenario**: Investigate potential security incidents and user behavior anomalies

**Search Strategy:**
```kql
# Failed authentication attempts
event.category: "authentication" and event.outcome: "failure" and @timestamp >= "now-24h"

# Unusual access patterns
source.ip: * and user.name: admin* and @timestamp >= "now-7d"

# Data access monitoring
event.action: "data_access" and classification: "sensitive"
```

**Analysis Workflow:**
1. **Time Correlation**: Look for patterns in failed attempts
2. **IP Analysis**: Identify source IPs with multiple failures
3. **User Behavior**: Analyze normal vs. anomalous user patterns
4. **Geographic Analysis**: Check access locations
5. **Incident Response**: Export findings for security team

### Use Case 4: IoT Device Monitoring

**Scenario**: Monitor IoT device health and detect maintenance needs

**Search Strategy:**
```kql
# Device performance issues
device.type: "sensor" and battery.level < 20 and status: "active"

# Communication failures
event.type: "communication" and event.outcome: "failure" and @timestamp >= "now-4h"

# Maintenance scheduling
device.age > 365 and last_maintenance < "now-90d"
```

**Analysis Workflow:**
1. **Device Filtering**: Focus on specific device types or locations
2. **Health Metrics**: Monitor battery, connectivity, and performance
3. **Predictive Analysis**: Identify devices needing maintenance
4. **Geographic Distribution**: Map device issues by location
5. **Maintenance Reports**: Generate device health reports

## 🚀 Performance Tips and Best Practices

### Query Performance Optimization

#### Efficient Search Patterns

**Fast Queries:**
```kql
# Good: Use specific field names
status.keyword: "error"

# Good: Combine filters efficiently
host.name: "web-01" and @timestamp >= "now-1h"

# Good: Use appropriate wildcards
user.name: john*
```

**Slow Queries to Avoid:**
```kql
# Bad: Broad text searches
message: error

# Bad: Leading wildcards
user.name: *admin

# Bad: Too many OR conditions
field1: value1 or field2: value2 or field3: value3 or ...
```

#### Time Range Optimization

**Performance Guidelines:**
- **Limit Time Ranges** - Avoid queries spanning months
- **Use Relative Times** - "now-1h" is more efficient than absolute times
- **Leverage Index Patterns** - Use date-based index patterns
- **Monitor Query Performance** - Watch for slow queries

### Data Volume Management

#### Large Dataset Strategies

**Sampling Techniques:**
```
Large Dataset Handling:
├── Use representative time samples
├── Apply selective filters early
├── Limit document count (< 10,000)
├── Use aggregations instead of raw docs
└── Consider data tiers for old data
```

**Index Management:**
```
Performance Optimization:
├── Hot/Warm/Cold Architecture
├── Regular index rollovers
├── Appropriate shard sizing
├── Field mapping optimization
└── Query-focused index design
```

### Memory and Resource Management

#### Browser Performance

**Client-Side Optimization:**
- **Limit Selected Fields** - Only show necessary columns
- **Use Compact View** - Reduce visual complexity
- **Close Unused Tabs** - Free browser memory
- **Regular Cache Clearing** - Prevent memory leaks

**Server-Side Optimization:**
- **Appropriate Heap Size** - Size Elasticsearch heap correctly
- **Circuit Breakers** - Prevent OOM conditions
- **Query Caching** - Leverage Elasticsearch caches
- **Resource Monitoring** - Monitor CPU and memory usage

## 🔧 Troubleshooting Common Issues

### Search Performance Issues

#### Issue: "Search takes too long to complete"

**Symptoms:**
- Queries timeout after 30 seconds
- High CPU usage during searches
- Slow response times in Discover

**Solutions:**
```kql
# 1. Narrow time range
@timestamp >= "now-1h"  # Instead of "now-7d"

# 2. Add specific filters
service.name: "api" and log.level: "ERROR"  # Instead of broad search

# 3. Use field-specific queries
status.keyword: "error"  # Instead of message: error
```

#### Issue: "No results found"

**Symptoms:**
- Empty result set despite data existence
- Filters returning no matches
- Time range issues

**Solutions:**
```bash
# 1. Check time range
Expand time range to "Last 7 days"

# 2. Verify data view
Confirm correct index pattern selected

# 3. Check field mappings
GET /your-index/_mapping

# 4. Test basic queries
*  # Search for all documents
@timestamp: *  # Check time field existence
```

### Field Display Issues

#### Issue: "Field not showing in sidebar"

**Symptoms:**
- Expected fields missing from field list
- Field search returns no results
- Mapping appears correct

**Solutions:**
```bash
# 1. Refresh field list
Data View → Refresh field list

# 2. Check field mapping
GET /your-index/_mapping/field/your-field

# 3. Verify index pattern
Ensure pattern matches indices with field

# 4. Check document sampling
Increase sample size to capture field
```

### Export and Sharing Issues

#### Issue: "Export fails or incomplete"

**Symptoms:**
- CSV export shows fewer rows than expected
- Export process hangs or fails
- Missing fields in exported data

**Solutions:**
```bash
# 1. Reduce export size
Limit to 10,000 documents maximum

# 2. Simplify field selection
Export only essential fields

# 3. Check memory limits
Monitor Kibana memory usage during export

# 4. Use API for large exports
Use Elasticsearch scroll API directly
```

## 📚 Quick Reference

### Essential KQL Patterns

```kql
# Basic patterns
field: value
field: "exact phrase"
field: prefix*
field: *suffix
field: *contains*

# Numeric comparisons
field > 100
field >= 50 and field <= 200
field < 1000

# Date queries
@timestamp >= "2024-01-01"
@timestamp >= "now-1d"
@timestamp >= "now/d-1d"

# Boolean logic
field1: value1 and field2: value2
field1: value1 or field2: value2
not field: value

# Existence checks
field: *
not field: *
```

### Common Field Types and Uses

| Field Type | KQL Example | Best For |
|------------|-------------|----------|
| `keyword` | `status.keyword: "success"` | Exact matching, aggregations |
| `text` | `message: "error occurred"` | Full-text search |
| `date` | `@timestamp >= "now-1h"` | Time-based filtering |
| `long` | `response_time > 1000` | Numeric comparisons |
| `boolean` | `is_active: true` | Binary conditions |
| `ip` | `source.ip: "192.168.1.100"` | IP address matching |

### Keyboard Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| `Ctrl/Cmd + Enter` | Execute search | Search bar |
| `Ctrl/Cmd + /` | Focus search bar | Global |
| `Ctrl/Cmd + S` | Save search | Discover |
| `Ctrl/Cmd + O` | Open saved search | Discover |
| `Escape` | Clear search | Search bar |

## 🔗 Next Steps

Now that you've mastered the Discover application:

1. **Create Visualizations** → [Kibana Lens Basics](../03-visualization-fundamentals/kibana-lens-basics.md)
2. **Build Dashboards** → [Dashboard Creation](../05-dashboards-collaboration/dashboard-creation.md)
3. **Advanced Analytics** → [Machine Learning](../06-advanced-features/machine-learning.md)
4. **Performance Monitoring** → [Monitoring and Alerting](../07-production-performance/monitoring-alerting.md)

## 📝 Key Takeaways

- **Discover is your data exploration foundation** - Master it before building visualizations
- **Field analysis drives insights** - Use the sidebar extensively for understanding data
- **KQL is powerful but requires practice** - Start simple and build complexity gradually
- **Time-based analysis is crucial** - Always consider temporal patterns in your data
- **Saved searches enable collaboration** - Share insights with descriptive names and documentation
- **Performance matters** - Optimize queries for speed and resource efficiency

The Discover application is your gateway to understanding and exploring Elasticsearch data. Master these concepts to build a solid foundation for advanced Kibana analytics and visualization capabilities!