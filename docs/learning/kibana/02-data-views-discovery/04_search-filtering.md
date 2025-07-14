# Search & Filtering in Kibana

Advanced search techniques using KQL (Kibana Query Language) and filters to efficiently explore and analyze your data.

## 🎯 What You'll Learn

Master Kibana's search and filtering capabilities to quickly find insights in your data:

- **KQL Query Language** - Write powerful search queries
- **Filter Controls** - Create reusable filter components
- **Advanced Search Patterns** - Complex queries and combinations
- **Query Performance** - Optimize search for large datasets

## 🔍 Understanding Kibana Query Language (KQL)

KQL is Kibana's simplified query language designed for interactive data exploration.

### Basic KQL Syntax

```kql
# Simple field searches
status: "error"
user.name: "john.doe"
response_time > 1000

# Boolean operators
status: "error" AND user.name: "john.doe"
status: "error" OR status: "warning"
NOT status: "success"

# Wildcards and patterns
user.name: "john*"
message: *exception*
status: error OR warning

# Range queries
response_time >= 500 AND response_time < 1000
@timestamp >= "2024-01-01" AND @timestamp < "2024-02-01"
```

### Advanced KQL Features

```kql
# Nested field queries
user.address.city: "New York"
products.category: "electronics"

# Array field queries
tags: ("urgent" OR "critical")
user.roles: "admin"

# Existence checks
user.email: *
NOT user.phone: *

# Escape special characters
message: "User said: \"Hello world\""
path: "C\\:\\Users\\Documents"
```

## 🏗️ Before You Begin

**Prerequisites:**
- Complete [Discover Application](02_discover-application.md)
- Understanding of your data structure and field types
- Basic knowledge of boolean logic

**Required Setup:**
- Access to Kibana with sample data or your own indices
- Data view configured for your target indices

## 🔧 Building Effective Search Queries

### 1. **Field-Based Searches**

Target specific fields for precise results:

```kql
# Text field exact matches
user.name: "john.doe"
status: "error"

# Numeric field ranges
response_time > 1000
cpu_usage >= 80

# IP address searches
client.ip: "192.168.1.100"
client.ip: "192.168.1.0/24"

# Date/time searches
@timestamp >= "2024-01-01T00:00:00.000Z"
@timestamp: "2024-01-01"
```

### 2. **Text Search Patterns**

```kql
# Full-text search across all fields
"database connection failed"

# Phrase searches
message: "user authentication failed"

# Wildcard searches
user.name: john*
message: *timeout*
url.path: */api/v1/*

# Case-insensitive searches (KQL is case-insensitive by default)
status: ERROR  # matches "error", "Error", "ERROR"
```

### 3. **Boolean Logic Combinations**

```kql
# AND operations (all conditions must be true)
status: "error" AND user.name: "john.doe"
response_time > 1000 AND url.path: "/api/*"

# OR operations (any condition can be true)
status: "error" OR status: "warning"
method: "GET" OR method: "POST"

# NOT operations (exclude conditions)
NOT status: "success"
user.name: * AND NOT user.name: "anonymous"

# Grouping with parentheses
(status: "error" OR status: "warning") AND user.name: john*
```

### 4. **Advanced Range Queries**

```kql
# Numeric ranges
response_time >= 100 AND response_time < 500
cpu_usage: [80 TO 100]

# Date ranges
@timestamp >= "2024-01-01" AND @timestamp < "2024-02-01"
@timestamp: ["2024-01-01T00:00:00" TO "2024-01-01T23:59:59"]

# Combined range conditions
response_time > 1000 AND @timestamp >= "now-1h"
```

## 🎛️ Using Kibana Filters

### Filter Types and Controls

**1. Field Filters**
- **Phrase Filter**: Exact field value matches
- **Phrases Filter**: Multiple exact values (OR logic)
- **Range Filter**: Numeric or date ranges
- **Exists Filter**: Field presence/absence

**2. Filter Actions**
```bash
# From Discover field list
1. Click field name → "Filter for value" or "Filter out value"
2. Use "+" or "-" icons next to field values
3. Right-click field values for filter options

# From visualization interactions
1. Click chart segments to filter
2. Use brush selection on time series
3. Click map regions or data points
```

### Managing Filters

**Filter Controls Panel:**
- **Enable/Disable**: Toggle filters on/off
- **Pin/Unpin**: Keep filters across different apps
- **Edit**: Modify filter conditions
- **Delete**: Remove unwanted filters

**Filter Combinations:**
```kql
# Filters are combined with AND logic by default
Filter 1: status: "error"
Filter 2: user.name: "john.doe"
# Result: status: "error" AND user.name: "john.doe"
```

## 📊 Practical Search Examples

### Web Application Monitoring

```kql
# Find error responses in the last hour
status >= 400 AND @timestamp >= "now-1h"

# Identify slow API endpoints
response_time > 5000 AND url.path: "/api/*"

# Track user authentication failures
message: "authentication failed" OR message: "login failed"

# Monitor specific user activity
user.name: "admin" AND NOT url.path: "/health"
```

### System Log Analysis

```kql
# Find critical system errors
level: "ERROR" AND service: "database"

# Identify service outages
message: *timeout* OR message: *connection* OR message: *unavailable*

# Monitor resource usage patterns
cpu_usage > 90 OR memory_usage > 85

# Track deployment issues
message: *deployment* AND (status: "failed" OR level: "ERROR")
```

### Security Monitoring

```kql
# Detect suspicious login patterns
event.type: "authentication" AND event.outcome: "failure"

# Monitor privilege escalation attempts
user.roles: "admin" AND NOT user.name: ("admin" OR "root")

# Track unusual access patterns
@timestamp >= "now-24h" AND user.name: * AND NOT user.name: "service-account"
```

## ⚡ Search Performance Optimization

### Query Optimization Tips

**1. Use Specific Field Names**
```kql
# Optimized: Target specific fields
user.name: "john.doe"
response_time > 1000

# Avoid: Generic text searches
"john.doe"  # Searches all fields
```

**2. Leverage Index Patterns**
```kql
# Use time-based filtering first
@timestamp >= "now-24h" AND status: "error"

# Combine with specific field filters
@timestamp >= "now-1h" AND user.name: "admin" AND status: "error"
```

**3. Optimize Range Queries**
```kql
# Efficient range queries
response_time: [100 TO 500]
@timestamp: ["now-24h" TO "now"]

# Avoid open-ended ranges when possible
response_time > 0  # Less efficient
```

### Data Volume Considerations

**Large Dataset Strategies:**
- Use time-based filtering as the primary constraint
- Combine multiple specific field filters
- Leverage data view field filtering
- Consider using index patterns for data organization

## 🚨 Common Search Pitfalls

### Troubleshooting Search Issues

**1. No Results Found**
```kql
# Check field names and values
user.name: "john.doe"  # Correct field name?
status: "Error"        # Correct case and value?

# Verify field existence
user.email: *          # Does field exist?
```

**2. Unexpected Results**
```kql
# Check for partial matches
user.name: john*       # Might match "johnsmith"
message: *error*       # Might match "terrorizing"

# Use exact phrase matching
message: "connection error"  # Exact phrase
```

**3. Performance Issues**
```kql
# Add time constraints
@timestamp >= "now-24h" AND your_query_here

# Use field-specific searches
user.name: "john.doe" AND status: "error"
# Instead of: "john.doe error"
```

## 💡 Best Practices

### Query Writing Guidelines

**1. Structure Your Queries**
```kql
# Start with time constraints
@timestamp >= "now-24h"

# Add specific field filters
AND status: "error"
AND user.name: "john.doe"

# Include contextual information
AND url.path: "/api/users"
```

**2. Use Clear Field Names**
```kql
# Descriptive and specific
user.authentication.status: "failed"
api.response.time: > 1000

# Avoid ambiguous searches
status: "error"  # Which status field?
```

**3. Document Complex Queries**
```kql
# Complex monitoring query for API performance
(
  # API endpoints with slow response times
  (url.path: "/api/*" AND response_time > 5000)
  OR
  # Authentication failures
  (user.authentication.status: "failed")
  OR
  # Database connection errors
  (message: "database" AND level: "ERROR")
)
AND @timestamp >= "now-24h"
```

### Filter Management

**1. Organize Filters Effectively**
- Pin frequently used filters
- Use descriptive filter names
- Group related filters together
- Remove unused filters regularly

**2. Save Common Queries**
- Create saved searches for repeated queries
- Use descriptive names and descriptions
- Share useful queries with team members
- Version control important query sets

## 🔗 Next Steps

After mastering search and filtering:

1. **Explore Visualization**: [Kibana Lens Basics](../03-visualization-fundamentals/01_kibana-lens-basics.md)
2. **Learn Advanced Techniques**: [Aggregations & Metrics](../03-visualization-fundamentals/03_aggregations-metrics.md)
3. **Practice with Real Data**: [Sample Dashboards](../examples/01_sample-dashboards.md)

## 📚 Additional Resources

- [KQL Documentation](https://www.elastic.co/guide/en/kibana/9.0/kuery-query.html)
- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/query-dsl.html)
- [Kibana Filters Reference](https://www.elastic.co/guide/en/kibana/9.0/filters.html)

---

**Practice Tip:** Start with simple queries and gradually add complexity. Use the query bar's auto-complete feature to discover available fields and values in your data.