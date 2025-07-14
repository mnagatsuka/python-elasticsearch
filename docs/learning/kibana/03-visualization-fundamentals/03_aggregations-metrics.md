# Aggregations & Metrics

Master data summarization techniques to extract meaningful insights from large datasets using Elasticsearch aggregations.

## 🎯 What You'll Learn

Transform raw data into actionable insights:

- **Aggregation Types** - Metric, bucket, and pipeline aggregations
- **Metric Calculations** - Statistical functions and custom formulas
- **Bucket Grouping** - Categorizing and organizing data
- **Advanced Techniques** - Nested aggregations and complex calculations

## 🔍 Understanding Aggregations

Aggregations are the foundation of data analysis in Elasticsearch and Kibana, enabling you to summarize, group, and calculate statistics from your data.

### Types of Aggregations

**1. Metric Aggregations**
- Calculate statistics from numeric fields
- Return single values or simple statistics
- Examples: count, sum, average, min, max

**2. Bucket Aggregations**
- Group documents into buckets
- Each bucket contains documents sharing common criteria
- Examples: terms, date histogram, range

**3. Pipeline Aggregations**
- Operate on the output of other aggregations
- Perform calculations on aggregated data
- Examples: moving average, derivative, cumulative sum

## 🏗️ Before You Begin

**Prerequisites:**
- Complete [Kibana Lens Basics](01_kibana-lens-basics.md)
- Understanding of your data field types
- Basic knowledge of statistical concepts

**Required Setup:**
- Access to Kibana with numeric and categorical data
- Data views configured with appropriate field types

## 📊 Metric Aggregations

### 1. **Basic Statistical Functions**

**Count Aggregation:**
```bash
# Document count
Purpose: Count total number of documents
Use cases: 
- Total events
- Request volume
- Error frequency
- User sessions

Configuration in Lens:
Y-axis: Count of documents
No additional configuration needed
```

**Sum Aggregation:**
```bash
# Total values
Purpose: Sum all values in a numeric field
Use cases:
- Total revenue
- Total bytes transferred
- Total processing time
- Accumulated costs

Configuration in Lens:
Y-axis: field_name (Sum)
Field type: Numeric
```

**Average Aggregation:**
```bash
# Mean values
Purpose: Calculate arithmetic mean
Use cases:
- Average response time
- Mean order value
- Average CPU usage
- Typical session duration

Configuration in Lens:
Y-axis: field_name (Average)
Field type: Numeric
```

**Min/Max Aggregations:**
```bash
# Extreme values
Purpose: Find minimum or maximum values
Use cases:
- Peak performance metrics
- Lowest/highest prices
- First/last timestamps
- Range boundaries

Configuration in Lens:
Y-axis: field_name (Min) or field_name (Max)
Field type: Numeric or Date
```

### 2. **Advanced Statistical Functions**

**Unique Count (Cardinality):**
```bash
# Distinct values
Purpose: Count unique values in a field
Use cases:
- Unique users
- Distinct IP addresses
- Different product categories
- Unique error types

Configuration in Lens:
Y-axis: field_name (Unique count)
Field type: Any type
Precision: Configurable (default: 3000)
```

**Percentiles:**
```bash
# Distribution analysis
Purpose: Calculate percentile values
Use cases:
- Response time SLAs (95th percentile)
- Performance benchmarks
- Quality metrics
- Distribution analysis

Configuration in Lens:
Y-axis: field_name (Percentile)
Percentile: 50, 90, 95, 99 (common values)
Field type: Numeric
```

**Standard Deviation:**
```bash
# Variability measurement
Purpose: Measure data spread
Use cases:
- Performance consistency
- Quality control
- Anomaly detection
- Risk assessment

Configuration in Lens:
Y-axis: field_name (Standard deviation)
Field type: Numeric
```

### 3. **Practical Metric Examples**

**Web Analytics:**
```bash
# Page load performance
Average response time: response_time (Average)
95th percentile: response_time (95th percentile)
Total requests: Count of documents
Unique visitors: client_ip (Unique count)
```

**E-commerce Metrics:**
```bash
# Sales performance
Total revenue: order_value (Sum)
Average order value: order_value (Average)
Conversion rate: Formula: count(kql='status:"completed"') / count()
Unique customers: customer_id (Unique count)
```

**System Monitoring:**
```bash
# Resource utilization
CPU usage: cpu.percent (Average)
Memory usage: memory.used_bytes (Sum)
Peak memory: memory.used_bytes (Max)
Active processes: process_id (Unique count)
```

## 🗂️ Bucket Aggregations

### 1. **Terms Aggregation**

**Purpose**: Group documents by field values
**Best For**: Categorical data analysis

```bash
# Top categories analysis
Configuration:
X-axis: category_field (Terms)
Size: Top 10 (configurable)
Order by: Count (descending)

Use cases:
- Top selling products
- Most frequent errors
- Popular pages
- Leading regions
```

**Advanced Terms Configuration:**
```bash
# Custom ordering
Order by: Metric value (ascending/descending)
Missing values: Include/exclude
Other bucket: Include remaining categories

# Terms with custom size
Size: 20 (show top 20)
Other bucket: Show "Other" category
```

### 2. **Date Histogram Aggregation**

**Purpose**: Group documents by time intervals
**Best For**: Time series analysis

```bash
# Time-based analysis
Configuration:
X-axis: @timestamp (Date histogram)
Interval: Auto, 1m, 1h, 1d, 1w, 1M (configurable)

Use cases:
- Traffic patterns over time
- Sales trends
- System performance monitoring
- Event frequency analysis
```

**Date Histogram Intervals:**
```bash
# Common intervals
1m, 5m, 15m, 30m  # Minute intervals
1h, 6h, 12h       # Hour intervals
1d, 7d            # Day intervals
1w, 2w, 4w        # Week intervals
1M, 3M, 6M, 1y    # Month/year intervals

# Auto interval
Automatically adjusts based on time range
Provides optimal granularity
```

### 3. **Range Aggregation**

**Purpose**: Group documents by numeric ranges
**Best For**: Distribution analysis

```bash
# Performance categorization
Configuration:
X-axis: response_time (Range)
Ranges: 
  - 0 to 100ms (Fast)
  - 100 to 500ms (Medium)
  - 500 to 1000ms (Slow)
  - 1000+ ms (Very Slow)

Use cases:
- Performance buckets
- Age groups
- Price ranges
- Score categories
```

### 4. **Histogram Aggregation**

**Purpose**: Group numeric data into equal-width buckets
**Best For**: Distribution visualization

```bash
# Value distribution
Configuration:
X-axis: numeric_field (Histogram)
Interval: 10, 100, 1000 (depends on data range)

Use cases:
- Response time distribution
- File size distribution
- Score distribution
- Measurement analysis
```

## 🔗 Nested and Multi-Level Aggregations

### 1. **Multi-Dimensional Analysis**

**Terms within Terms:**
```bash
# Regional sales by product
X-axis: region (Terms, Top 10)
Break down by: product_category (Terms, Top 5)
Y-axis: revenue (Sum)

Result: Stacked bar chart showing revenue by region and product
```

**Date Histogram with Terms:**
```bash
# Error trends by type
X-axis: @timestamp (Date histogram, 1h)
Break down by: error.type (Terms, Top 5)
Y-axis: Count of documents

Result: Stacked area chart showing error trends by type
```

### 2. **Pipeline Aggregations**

**Moving Average:**
```bash
# Smoothed trend analysis
Base aggregation: response_time (Average) by @timestamp
Pipeline: Moving average (window: 7 days)

Use cases:
- Smoothing noisy data
- Identifying trends
- Forecasting patterns
```

**Derivative:**
```bash
# Rate of change
Base aggregation: total_sales (Sum) by @timestamp
Pipeline: Derivative (change rate)

Use cases:
- Growth rates
- Acceleration metrics
- Change analysis
```

**Cumulative Sum:**
```bash
# Running totals
Base aggregation: daily_sales (Sum) by @timestamp
Pipeline: Cumulative sum

Use cases:
- Running totals
- Cumulative metrics
- Progress tracking
```

## 🧮 Custom Formulas in Lens

### 1. **Basic Formula Functions**

**Mathematical Operations:**
```bash
# Percentage calculations
(count(kql='status:"success"') / count()) * 100

# Ratio calculations
sum(field1) / sum(field2)

# Difference calculations
max(current_value) - min(previous_value)

# Growth rate
(sum(current_period) - sum(previous_period)) / sum(previous_period) * 100
```

**Conditional Aggregations:**
```bash
# Success rate
count(kql='status:"success"') / count()

# Error rate
count(kql='status:"error"') / count()

# Conversion rate
count(kql='action:"purchase"') / count(kql='action:"view"')
```

### 2. **Advanced Formula Examples**

**Performance Metrics:**
```bash
# Apdex Score (Application Performance Index)
(count(kql='response_time <= 100') + 
 count(kql='response_time > 100 AND response_time <= 400') * 0.5) / count()

# Availability percentage
(count() - count(kql='status:"error"')) / count() * 100

# Efficiency ratio
sum(successful_transactions) / sum(total_processing_time)
```

**Business Metrics:**
```bash
# Customer lifetime value
sum(order_value) / unique_count(customer_id)

# Average session duration
sum(session_duration) / unique_count(session_id)

# Bounce rate
count(kql='page_views:1') / unique_count(session_id) * 100
```

## 💡 Best Practices

### Aggregation Performance

**1. Optimize Field Types**
```bash
# Use appropriate field types
Numbers: long, double, float
Categories: keyword (not text)
Dates: date type with proper format
Booleans: boolean type
```

**2. Index Considerations**
```bash
# Performance tips
- Use doc_values for aggregations
- Consider field cardinality
- Implement proper index templates
- Monitor query performance
```

### Data Accuracy

**1. Handle Missing Values**
```bash
# Address null values
- Use exists queries to filter
- Consider default values
- Document missing data handling
- Use appropriate aggregation types
```

**2. Time Zone Considerations**
```bash
# Date histogram accuracy
- Set appropriate time zones
- Consider daylight saving time
- Use consistent time formats
- Handle time zone conversions
```

### Visualization Choices

**1. Aggregation-Chart Alignment**
```bash
# Match aggregation to chart type
Count/Sum → Bar charts, line charts
Average → Line charts, metric displays
Percentiles → Box plots, line charts
Terms → Bar charts, pie charts
```

**2. Bucket Size Optimization**
```bash
# Optimal bucket sizes
Terms: 5-20 categories
Date histogram: Match to time range
Range: 3-10 ranges
Histogram: 10-50 buckets
```

## 🚨 Common Pitfalls

### Performance Issues
- **Too many buckets**: Limit bucket count for performance
- **High cardinality fields**: Use sampling or filtering
- **Deep nesting**: Avoid excessive aggregation levels
- **Large time ranges**: Use appropriate intervals

### Data Interpretation
- **Misleading averages**: Consider using median or percentiles
- **Incomplete data**: Account for missing values
- **Time zone confusion**: Ensure consistent time handling
- **Sampling bias**: Understand data completeness

## 🔗 Next Steps

After mastering aggregations:

1. **Time Series Analysis**: [Time Series Basics](04_time-series-basics.md)
2. **Advanced Visualizations**: [Advanced Lens Features](../04-advanced-visualizations/05_advanced-lens-features.md)
3. **Dashboard Building**: [Dashboard Creation](../05-dashboards-collaboration/01_dashboard-creation.md)

## 📚 Additional Resources

- [Elasticsearch Aggregations Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/search-aggregations.html)
- [Kibana Lens Formulas](https://www.elastic.co/guide/en/kibana/9.0/lens-formulas.html)
- [Performance Optimization Guide](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/tune-for-search-speed.html)

---

**Analysis Tip:** Start with simple aggregations and gradually build complexity. Always validate your results with sample data to ensure accuracy.