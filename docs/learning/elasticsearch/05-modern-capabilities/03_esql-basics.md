# ES|QL Basics

**Query and analyze data with SQL-like syntax for modern analytics**

*Estimated reading time: 35 minutes*

## Overview

ES|QL (Elasticsearch Query Language) is a powerful query language that combines the flexibility of SQL with the scalability of Elasticsearch. It provides a familiar interface for data analysts and engineers to query, transform, and analyze data in real-time.

## 📋 Table of Contents

1. [ES|QL Fundamentals](#esql-fundamentals)
2. [Basic Syntax](#basic-syntax)
3. [Data Selection](#data-selection)
4. [Filtering and Conditions](#filtering-and-conditions)
5. [Aggregations and Grouping](#aggregations-and-grouping)
6. [Functions and Expressions](#functions-and-expressions)
7. [Advanced Queries](#advanced-queries)

## 🎯 ES|QL Fundamentals

### What is ES|QL?

ES|QL is a query language that allows you to:
- Write SQL-like queries against Elasticsearch indices
- Perform complex aggregations and transformations
- Build analytics pipelines with pipe operations
- Leverage Elasticsearch's distributed architecture

### Key Features

- **Familiar SQL syntax** with modern enhancements
- **Pipe-based operations** for data transformation
- **Built-in functions** for common operations
- **Real-time processing** on live data
- **Scalable execution** across clusters

### Basic Query Structure

```bash
# Basic ES|QL query structure
POST /_query
{
  "query": "FROM index_name | OPERATION | OPERATION | ..."
}
```

## 🔤 Basic Syntax

### Simple Query

```bash
# Basic data retrieval
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | LIMIT 10"
}
'
```

### Pipe Operations

ES|QL uses pipes (|) to chain operations:

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | WHERE price > 100 | SORT date DESC | LIMIT 5"
}
'
```

### Comments

```bash
# Query with comments
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales // Get sales data\n| WHERE region = \"North\" // Filter by region\n| STATS total_revenue = SUM(revenue) // Calculate total"
}
'
```

## 📊 Data Selection

### FROM Clause

**Single Index:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales"
}
'
```

**Multiple Indices:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales, orders, customers"
}
'
```

**Index Patterns:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM logs-2024-*"
}
'
```

### Field Selection

**All Fields:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM products | KEEP *"
}
'
```

**Specific Fields:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM products | KEEP product_name, price, category"
}
'
```

**Exclude Fields:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM products | DROP internal_id, debug_info"
}
'
```

### Field Aliases

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | EVAL total_amount = price * quantity, profit = revenue - cost | KEEP product, total_amount, profit"
}
'
```

## 🔍 Filtering and Conditions

### WHERE Clause

**Basic Conditions:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | WHERE price > 100"
}
'
```

**Multiple Conditions:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | WHERE price > 100 AND region = \"North\" AND date >= \"2024-01-01\""
}
'
```

**OR Conditions:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | WHERE category = \"Electronics\" OR category = \"Computers\""
}
'
```

### Comparison Operators

```bash
# Numeric comparisons
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM products | WHERE price >= 50 AND price <= 500"
}
'

# String comparisons
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM products | WHERE product_name LIKE \"iPhone*\""
}
'

# Range queries
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM logs | WHERE @timestamp >= NOW() - INTERVAL 1 HOUR"
}
'
```

### IN and NOT IN

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | WHERE region IN (\"North\", \"South\", \"East\")"
}
'

curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM products | WHERE category NOT IN (\"Discontinued\", \"Out of Stock\")"
}
'
```

### NULL Handling

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM customers | WHERE email IS NOT NULL"
}
'

curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM orders | WHERE discount IS NULL"
}
'
```

## 📈 Aggregations and Grouping

### STATS Command

**Basic Aggregations:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS total_revenue = SUM(revenue), avg_price = AVG(price), order_count = COUNT(*)"
}
'
```

**Multiple Metrics:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS total_revenue = SUM(revenue), min_price = MIN(price), max_price = MAX(price), unique_customers = COUNT_DISTINCT(customer_id)"
}
'
```

### GROUP BY

**Single Field Grouping:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS total_revenue = SUM(revenue) BY region"
}
'
```

**Multiple Field Grouping:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS total_revenue = SUM(revenue), avg_price = AVG(price) BY region, category"
}
'
```

**Time-based Grouping:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS daily_revenue = SUM(revenue) BY DATE_TRUNC(\"day\", date)"
}
'
```

### Having Clause

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS total_revenue = SUM(revenue) BY region | WHERE total_revenue > 10000"
}
'
```

## 🔧 Functions and Expressions

### Mathematical Functions

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | EVAL profit_margin = (revenue - cost) / revenue * 100, rounded_price = ROUND(price, 2)"
}
'
```

### String Functions

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM products | EVAL product_upper = UPPER(product_name), product_length = LENGTH(product_name), first_char = LEFT(product_name, 1)"
}
'
```

### Date Functions

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | EVAL year = DATE_EXTRACT(\"year\", date), month = DATE_EXTRACT(\"month\", date), day_of_week = DATE_EXTRACT(\"dayofweek\", date)"
}
'
```

### Conditional Functions

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | EVAL price_category = CASE WHEN price < 50 THEN \"Low\" WHEN price < 200 THEN \"Medium\" ELSE \"High\" END"
}
'
```

### Type Conversion

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM logs | EVAL response_time_int = TO_INTEGER(response_time), log_level_str = TO_STRING(log_level)"
}
'
```

## 🎯 Advanced Queries

### Sorting

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | SORT revenue DESC, date ASC"
}
'
```

### Limiting Results

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM products | SORT price DESC | LIMIT 10"
}
'
```

### Window Functions

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | EVAL running_total = SUM(revenue) OVER (ORDER BY date), rank = ROW_NUMBER() OVER (PARTITION BY region ORDER BY revenue DESC)"
}
'
```

### Subqueries and CTEs

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | WHERE region IN (FROM top_regions | KEEP region)"
}
'
```

### Complex Analytics

**Moving Averages:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS daily_revenue = SUM(revenue) BY DATE_TRUNC(\"day\", date) | EVAL moving_avg = AVG(daily_revenue) OVER (ORDER BY DATE_TRUNC ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)"
}
'
```

**Cohort Analysis:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM users | EVAL signup_month = DATE_TRUNC(\"month\", signup_date), activity_month = DATE_TRUNC(\"month\", last_activity) | STATS user_count = COUNT(*) BY signup_month, activity_month"
}
'
```

**Percentile Calculations:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS p50 = PERCENTILE(revenue, 50), p90 = PERCENTILE(revenue, 90), p99 = PERCENTILE(revenue, 99) BY region"
}
'
```

### Real-time Analytics

**Recent Activity:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM logs | WHERE @timestamp >= NOW() - INTERVAL 15 MINUTE | STATS error_count = COUNT(*) BY level, service | WHERE level = \"ERROR\""
}
'
```

**Rate Calculations:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM web_requests | STATS request_count = COUNT(*) BY DATE_TRUNC(\"minute\", @timestamp) | EVAL requests_per_second = request_count / 60"
}
'
```

### Performance Monitoring

**Response Time Analysis:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM api_logs | STATS avg_response_time = AVG(response_time), p95_response_time = PERCENTILE(response_time, 95), error_rate = AVG(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 100 BY endpoint"
}
'
```

**System Metrics:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM system_metrics | WHERE @timestamp >= NOW() - INTERVAL 1 HOUR | STATS avg_cpu = AVG(cpu_usage), max_memory = MAX(memory_usage), disk_usage = AVG(disk_usage) BY host"
}
'
```

### Business Intelligence

**Sales Funnel Analysis:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM user_events | STATS visitors = COUNT_DISTINCT(user_id) BY event_type | EVAL conversion_rate = visitors / LAG(visitors, 1) OVER (ORDER BY event_type) * 100"
}
'
```

**Customer Segmentation:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM customers | EVAL customer_segment = CASE WHEN total_spend > 5000 THEN \"VIP\" WHEN total_spend > 1000 THEN \"Premium\" ELSE \"Standard\" END | STATS customer_count = COUNT(*), avg_spend = AVG(total_spend) BY customer_segment"
}
'
```

**Product Performance:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS total_revenue = SUM(revenue), units_sold = SUM(quantity), avg_price = AVG(price) BY product | EVAL revenue_per_unit = total_revenue / units_sold | SORT total_revenue DESC"
}
'
```

### Data Quality Checks

**Missing Data Analysis:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM customers | STATS total_records = COUNT(*), missing_email = COUNT(*) - COUNT(email), missing_phone = COUNT(*) - COUNT(phone) | EVAL email_completeness = (total_records - missing_email) / total_records * 100"
}
'
```

**Duplicate Detection:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM orders | STATS record_count = COUNT(*) BY order_id | WHERE record_count > 1"
}
'
```

### Time Series Analysis

**Trend Analysis:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | STATS monthly_revenue = SUM(revenue) BY DATE_TRUNC(\"month\", date) | EVAL revenue_growth = (monthly_revenue - LAG(monthly_revenue, 1) OVER (ORDER BY DATE_TRUNC)) / LAG(monthly_revenue, 1) OVER (ORDER BY DATE_TRUNC) * 100"
}
'
```

**Seasonality Detection:**
```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM sales | EVAL month = DATE_EXTRACT(\"month\", date), year = DATE_EXTRACT(\"year\", date) | STATS avg_monthly_revenue = AVG(revenue) BY month | SORT month"
}
'
```

## 🎭 Practical Examples

### E-commerce Analytics

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM ecommerce_orders | WHERE order_date >= \"2024-01-01\" | EVAL order_value_segment = CASE WHEN total_amount < 50 THEN \"Low\" WHEN total_amount < 200 THEN \"Medium\" ELSE \"High\" END | STATS order_count = COUNT(*), total_revenue = SUM(total_amount), avg_order_value = AVG(total_amount) BY order_value_segment, customer_segment"
}
'
```

### Log Analysis

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM application_logs | WHERE @timestamp >= NOW() - INTERVAL 24 HOUR | STATS error_count = COUNT(*) BY level, service | WHERE level IN (\"ERROR\", \"WARN\") | SORT error_count DESC"
}
'
```

### User Behavior Analysis

```bash
curl -X POST "localhost:9200/_query" -H 'Content-Type: application/json' -d'
{
  "query": "FROM user_sessions | EVAL session_duration_minutes = session_duration / 60, bounce = CASE WHEN page_views = 1 THEN 1 ELSE 0 END | STATS avg_session_duration = AVG(session_duration_minutes), bounce_rate = AVG(bounce) * 100, avg_page_views = AVG(page_views) BY traffic_source"
}
'
```

## 🔗 Next Steps

Now that you've mastered ES|QL basics, let's explore performance and production considerations:

1. **[Performance Optimization](../06-performance-production/optimization-strategies.md)** - Scale your queries and optimize performance
2. **[Monitoring & Operations](../06-performance-production/monitoring-operations.md)** - Monitor query performance and system health
3. **[Index Management](../06-performance-production/index-management.md)** - Manage indices for optimal query performance

## 📚 Key Takeaways

- ✅ **Use familiar SQL syntax** with ES|QL for data analysis
- ✅ **Leverage pipe operations** for data transformation workflows
- ✅ **Apply built-in functions** for common calculations and transformations
- ✅ **Implement real-time analytics** with time-based queries
- ✅ **Optimize query performance** with proper filtering and aggregations
- ✅ **Use window functions** for advanced analytics patterns
- ✅ **Structure complex queries** with proper grouping and sorting
- ✅ **Monitor query execution** for performance optimization

Ready to optimize your Elasticsearch deployment? Continue with [Performance Optimization](../06-performance-production/optimization-strategies.md) to learn about scaling and performance tuning!