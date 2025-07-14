# Time Series Basics

Master time-based data analysis and visualization techniques for temporal patterns, trends, and anomalies.

## 🎯 What You'll Learn

Unlock the power of time series analysis:

- **Time-Based Visualization** - Chart types optimized for temporal data
- **Date Histogram Configuration** - Optimal time interval selection
- **Trend Analysis** - Identifying patterns and seasonality
- **Comparative Analysis** - Time-over-time comparisons

## ⏰ Understanding Time Series Data

Time series data consists of data points collected or recorded at successive time intervals. It's fundamental to monitoring, analytics, and business intelligence.

### Key Characteristics

**Temporal Ordering**: Data points have a natural chronological sequence
**Regular Intervals**: Data is typically collected at consistent time intervals
**Trends**: Long-term movement patterns in the data
**Seasonality**: Regular patterns that repeat over time
**Anomalies**: Unusual patterns that deviate from normal behavior

### Common Time Series Use Cases

**System Monitoring**: CPU usage, memory consumption, network traffic
**Business Analytics**: Sales trends, user engagement, conversion rates
**IoT Applications**: Sensor readings, device performance, environmental data
**Financial Analysis**: Stock prices, revenue tracking, cost monitoring

## 🏗️ Before You Begin

**Prerequisites:**
- Complete [Aggregations & Metrics](03_aggregations-metrics.md)
- Understanding of date/time fields in your data
- Basic knowledge of statistical concepts

**Required Setup:**
- Data with timestamp fields
- Properly configured date fields in your data view
- Sufficient time range for meaningful analysis

## 📊 Time Series Visualization Types

### 1. **Line Charts**

**Best For**: Continuous trends and patterns over time
**Optimal Use Cases**: System metrics, performance monitoring, KPI tracking

```bash
# Basic time series line chart
X-axis: @timestamp (Date histogram)
Y-axis: metric_value (Average, Sum, Count)
Chart Type: Line chart

# Example: Website traffic over time
X-axis: @timestamp (Date histogram, 1 hour)
Y-axis: Count of documents
Chart Type: Line chart
```

**Configuration Options:**
```bash
# Time intervals
Auto: Automatically adjusts based on time range
Fixed: 1m, 5m, 15m, 1h, 1d, 1w, 1M

# Line styling
Smooth curves: Enable for trend emphasis
Data points: Show/hide individual markers
Line thickness: Adjust for visibility
```

### 2. **Area Charts**

**Best For**: Volume emphasis and stacked comparisons
**Optimal Use Cases**: Traffic volume, resource utilization, cumulative metrics

```bash
# Stacked area chart
X-axis: @timestamp (Date histogram, 1 hour)
Y-axis: bytes_transferred (Sum)
Break down by: protocol (Terms, Top 5)
Chart Type: Area chart (stacked)

# Example: Network traffic by protocol
Shows total traffic volume with protocol breakdown
```

### 3. **Bar Charts (Time-Based)**

**Best For**: Discrete time periods and comparisons
**Optimal Use Cases**: Daily summaries, weekly reports, monthly comparisons

```bash
# Time-based bar chart
X-axis: @timestamp (Date histogram, 1 day)
Y-axis: revenue (Sum)
Chart Type: Vertical bar chart

# Example: Daily revenue comparison
Shows discrete daily values for easy comparison
```

### 4. **Heatmaps (Time-Based)**

**Best For**: Two-dimensional time patterns
**Optimal Use Cases**: Hour-of-day patterns, day-of-week analysis

```bash
# Time-based heatmap
X-axis: @timestamp (Date histogram, 1 hour)
Y-axis: day_of_week (Terms)
Cell value: Count of documents
Chart Type: Heatmap

# Example: Website activity patterns
Shows activity intensity by hour and day
```

## 🕐 Date Histogram Configuration

### 1. **Interval Selection**

**Auto Interval**: Kibana automatically selects optimal interval
```bash
# When to use auto
- Exploring data with unknown patterns
- Dashboard with dynamic time ranges
- General purpose visualizations

# How it works
- Considers total time range
- Aims for 50-100 data points
- Balances detail with performance
```

**Fixed Intervals**: Manual interval selection
```bash
# Short-term monitoring (minutes to hours)
1m, 5m, 15m, 30m, 1h, 6h, 12h

# Medium-term analysis (hours to days)
1h, 6h, 12h, 1d

# Long-term trends (days to months)
1d, 7d, 1w, 1M, 3M, 6M, 1y
```

### 2. **Time Zone Handling**

**UTC vs Local Time**:
```bash
# UTC (Coordinated Universal Time)
- Consistent across all users
- No daylight saving time issues
- Recommended for global applications

# Local Time
- Matches user's local context
- Handles daylight saving time
- Better for regional applications
```

**Configuration in Kibana**:
```bash
# Data view level
Management → Data Views → [Your Data View] → Time field
Set time zone: UTC, Browser, or specific time zone

# Visualization level
Date histogram → Advanced → Time zone override
```

### 3. **Offset Configuration**

**Time Offset**: Shift time buckets by specified amount
```bash
# Use cases
- Align with business hours
- Account for data collection delays
- Synchronize with external systems

# Configuration
Date histogram → Advanced → Time offset
Examples: +1h, -30m, +1d
```

## 📈 Time Series Analysis Techniques

### 1. **Trend Analysis**

**Identifying Trends**:
```bash
# Long-term trend visualization
X-axis: @timestamp (Date histogram, 1w)
Y-axis: metric_value (Average)
Add: Trend line (if available)

# Moving average for smoothing
Use pipeline aggregations or formulas
Window size: 7 days, 30 days (depends on data)
```

**Growth Rate Calculation**:
```bash
# Period-over-period growth
Formula: (current_value - previous_value) / previous_value * 100

# Example: Monthly revenue growth
current_month_revenue = sum(revenue, kql='@timestamp >= "now-1M"')
previous_month_revenue = sum(revenue, kql='@timestamp >= "now-2M" AND @timestamp < "now-1M"')
growth_rate = (current_month_revenue - previous_month_revenue) / previous_month_revenue * 100
```

### 2. **Seasonal Pattern Detection**

**Hour-of-Day Patterns**:
```bash
# Daily activity patterns
X-axis: @timestamp (Date histogram, 1 hour)
Y-axis: Count of documents
Time range: Last 30 days
Look for: Peak hours, low activity periods

# Business hours analysis
Filter: @timestamp >= "06:00" AND @timestamp <= "22:00"
```

**Day-of-Week Patterns**:
```bash
# Weekly patterns
X-axis: day_of_week (Terms, ordered)
Y-axis: Count of documents
Time range: Last 3 months
Look for: Weekday vs weekend patterns

# Heatmap visualization
X-axis: day_of_week (Terms)
Y-axis: hour_of_day (Terms)
Cell value: Count of documents
```

**Monthly/Seasonal Patterns**:
```bash
# Monthly comparison
X-axis: month (Terms, ordered)
Y-axis: metric_value (Average)
Time range: Last 2 years
Look for: Seasonal trends, cyclical patterns
```

### 3. **Anomaly Detection**

**Visual Anomaly Identification**:
```bash
# Statistical thresholds
Calculate: mean ± 2 standard deviations
Add reference lines to charts
Identify points outside normal range

# Percentile-based detection
Use 95th or 99th percentile as threshold
Compare current values to historical percentiles
```

**Comparative Analysis**:
```bash
# Year-over-year comparison
Current year: @timestamp >= "now-1y"
Previous year: @timestamp >= "now-2y" AND @timestamp < "now-1y"
Overlay both series on same chart
```

## 🔍 Advanced Time Series Techniques

### 1. **Multi-Series Analysis**

**Comparing Multiple Metrics**:
```bash
# Dual-axis visualization
Primary axis: response_time (Average)
Secondary axis: error_rate (Count)
Chart type: Line chart with dual axis

# Multiple series line chart
Y-axis: [cpu_usage (Average), memory_usage (Average), disk_usage (Average)]
Break down by: host.name (Terms, Top 5)
```

### 2. **Time-Based Aggregations**

**Rolling Window Calculations**:
```bash
# Moving average (7-day window)
Base: daily_metric (Average) by @timestamp (1d)
Pipeline: Moving average (window: 7)

# Cumulative sum
Base: daily_sales (Sum) by @timestamp (1d)
Pipeline: Cumulative sum
```

**Time-Shifted Comparisons**:
```bash
# Previous period comparison
Current period: @timestamp >= "now-7d"
Previous period: @timestamp >= "now-14d" AND @timestamp < "now-7d"
Display both on same chart for comparison
```

### 3. **Forecasting and Predictions**

**Trend Extrapolation**:
```bash
# Linear trend projection
Use historical data to identify trend
Extend trend line into future
Add confidence intervals if possible

# Seasonal adjustment
Account for known seasonal patterns
Adjust future predictions based on seasonal factors
```

## 🎨 Time Series Visualization Best Practices

### 1. **Chart Design**

**Color and Styling**:
```bash
# Use consistent color schemes
- Single series: One primary color
- Multiple series: Distinct, accessible colors
- Negative values: Red or contrasting colors
- Trend lines: Subtle, secondary colors
```

**Axis Configuration**:
```bash
# Y-axis
- Start at zero for count/sum aggregations
- Use appropriate scale for percentages
- Include units in axis labels
- Consider log scale for wide ranges

# X-axis (time)
- Show appropriate time labels
- Use consistent time intervals
- Consider timezone implications
- Include time range in title
```

### 2. **Interactive Features**

**Brush Selection**:
```bash
# Enable time range selection
Allow users to select time ranges by brushing
Automatically zoom to selected period
Maintain context with overview chart
```

**Tooltips and Details**:
```bash
# Rich tooltip information
- Exact timestamp
- Precise values
- Relevant context
- Comparison to previous period
```

### 3. **Performance Optimization**

**Data Sampling**:
```bash
# Large dataset handling
Use sampling for very large time ranges
Aggregate to appropriate intervals
Consider data retention policies
Balance detail with performance
```

**Interval Optimization**:
```bash
# Optimal interval selection
Short term (< 1 day): 1m - 1h intervals
Medium term (1 day - 1 month): 1h - 1d intervals
Long term (> 1 month): 1d - 1w intervals
```

## 🚨 Common Time Series Pitfalls

### Data Quality Issues
- **Missing timestamps**: Handle gaps in data
- **Irregular intervals**: Account for inconsistent collection
- **Time zone confusion**: Ensure consistent time handling
- **Daylight saving time**: Plan for time changes

### Visualization Mistakes
- **Inappropriate intervals**: Too granular or too aggregated
- **Misleading scales**: Inappropriate axis ranges
- **Overplotting**: Too many series on one chart
- **Missing context**: Lack of time range information

### Analysis Errors
- **Correlation vs causation**: Don't assume causation from correlation
- **Survivorship bias**: Account for missing or filtered data
- **Seasonal ignorance**: Don't ignore seasonal patterns
- **Trend misinterpretation**: Distinguish between noise and trends

## 🔗 Next Steps

After mastering time series basics:

1. **Advanced Visualizations**: [Advanced Lens Features](../04-advanced-visualizations/05_advanced-lens-features.md)
2. **Dashboard Integration**: [Dashboard Creation](../05-dashboards-collaboration/01_dashboard-creation.md)
3. **Monitoring Applications**: [APM Monitoring](../06-advanced-features/03_apm-monitoring.md)

## 📚 Additional Resources

- [Elasticsearch Date Histogram Aggregation](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/search-aggregations-bucket-datehistogram-aggregation.html)
- [Kibana Time Series Visual Builder](https://www.elastic.co/guide/en/kibana/9.0/TSVB.html)
- [Time Series Analysis Best Practices](https://www.elastic.co/guide/en/kibana/9.0/time-series-analysis.html)

---

**Analysis Tip:** Time series analysis is most effective when you understand your data collection patterns and business context. Always validate patterns with domain knowledge.