# Chart Types Overview

Comprehensive guide to selecting and configuring the right visualization for your data and audience.

## 🎯 What You'll Learn

Master the art of choosing appropriate visualizations:

- **Chart Type Selection** - When to use each visualization type
- **Data Compatibility** - Match chart types to your data structure
- **Audience Considerations** - Visualizations for different stakeholders
- **Best Practices** - Design principles for effective charts

## 📊 Chart Type Categories

### Comparison Charts
Perfect for comparing values across categories or time periods.

### Trend Analysis Charts
Ideal for showing patterns and changes over time.

### Composition Charts
Best for showing parts of a whole or hierarchical relationships.

### Distribution Charts
Effective for showing data spread and frequency patterns.

### Correlation Charts
Useful for displaying relationships between variables.

## 🏗️ Before You Begin

**Prerequisites:**
- Complete [Kibana Lens Basics](01_kibana-lens-basics.md)
- Understanding of your data types and structure
- Basic knowledge of data visualization principles

**Required Setup:**
- Access to Kibana with diverse data types
- Sample data or production data with various field types

## 📈 Detailed Chart Type Guide

### 1. **Bar Charts (Vertical & Horizontal)**

**Best Used For:**
- Comparing discrete categories
- Showing rankings or top performers
- Displaying survey results
- Comparing time periods

**Data Requirements:**
- **X-axis**: Categorical field (terms, date histogram)
- **Y-axis**: Numeric field (count, sum, average)
- **Optimal Categories**: 3-20 categories for readability

**Configuration Examples:**
```bash
# Website traffic by page
X-axis: url.path (Terms, Top 10)
Y-axis: Count of documents
Chart Type: Horizontal bar chart

# Monthly sales comparison
X-axis: @timestamp (Date histogram, 1 month)
Y-axis: revenue (Sum)
Chart Type: Vertical bar chart
```

**When to Use:**
- ✅ Comparing discrete values
- ✅ Showing rankings
- ✅ Limited number of categories
- ❌ Too many categories (>20)
- ❌ Continuous time series trends

### 2. **Line Charts**

**Best Used For:**
- Time series analysis
- Trend identification
- Continuous data patterns
- Multiple metric comparison

**Data Requirements:**
- **X-axis**: Time field (date histogram) or ordered categories
- **Y-axis**: Numeric field (any aggregation)
- **Optimal Points**: 10-100 data points for clarity

**Configuration Examples:**
```bash
# System performance over time
X-axis: @timestamp (Date histogram, 5 minutes)
Y-axis: cpu.usage (Average)
Chart Type: Line chart

# Multiple metrics comparison
X-axis: @timestamp (Date histogram, 1 hour)
Y-axis: [response_time (Average), error_rate (Count)]
Chart Type: Line chart (multi-series)
```

**When to Use:**
- ✅ Time series data
- ✅ Trend analysis
- ✅ Multiple related metrics
- ❌ Categorical comparisons
- ❌ Non-continuous data

### 3. **Area Charts**

**Best Used For:**
- Cumulative values over time
- Stacked categories showing total and parts
- Volume and magnitude emphasis
- Multiple series with total context

**Data Requirements:**
- **X-axis**: Time field (date histogram)
- **Y-axis**: Numeric field (sum, count recommended)
- **Categories**: 2-7 categories for stacked areas

**Configuration Examples:**
```bash
# Network traffic by protocol
X-axis: @timestamp (Date histogram, 1 hour)
Y-axis: bytes_transferred (Sum)
Break down by: protocol (Terms, Top 5)
Chart Type: Area chart (stacked)

# Cumulative sales by region
X-axis: @timestamp (Date histogram, 1 day)
Y-axis: revenue (Sum)
Break down by: region (Terms, Top 3)
Chart Type: Area chart (stacked)
```

**When to Use:**
- ✅ Cumulative totals
- ✅ Part-to-whole over time
- ✅ Volume emphasis
- ❌ Precise value reading
- ❌ Many overlapping categories

### 4. **Pie Charts & Donut Charts**

**Best Used For:**
- Part-to-whole relationships
- Percentage distributions
- Simple categorical breakdowns
- High-level overviews

**Data Requirements:**
- **Slice By**: Categorical field (terms)
- **Size By**: Numeric field (count, sum)
- **Optimal Slices**: 3-7 categories maximum

**Configuration Examples:**
```bash
# Error distribution by type
Slice by: error.type (Terms, Top 5)
Size by: Count of documents
Chart Type: Pie chart

# Revenue by product category
Slice by: product.category (Terms, Top 6)
Size by: revenue (Sum)
Chart Type: Donut chart
```

**When to Use:**
- ✅ Part-to-whole relationships
- ✅ Simple comparisons
- ✅ Percentage focus
- ❌ Too many categories (>7)
- ❌ Precise value comparisons
- ❌ Negative values

### 5. **Data Tables**

**Best Used For:**
- Detailed data exploration
- Precise value display
- Multi-dimensional analysis
- Export and sharing raw data

**Data Requirements:**
- **Rows**: Any field type
- **Columns**: Multiple metrics and dimensions
- **Optimal Rows**: 10-100 for screen viewing

**Configuration Examples:**
```bash
# User activity summary
Rows: user.name (Terms, Top 20)
Columns: [Count, login_count (Sum), last_activity (Max)]
Chart Type: Data table

# Sales performance by region
Rows: region (Terms, All)
Columns: [revenue (Sum), orders (Count), avg_order_value (Average)]
Chart Type: Data table
```

**When to Use:**
- ✅ Detailed data analysis
- ✅ Precise values needed
- ✅ Multi-dimensional data
- ❌ High-level overviews
- ❌ Trend visualization

### 6. **Metric Displays**

**Best Used For:**
- Key performance indicators (KPIs)
- Single value highlights
- Goal tracking
- Dashboard summaries

**Data Requirements:**
- **Primary Metric**: Single numeric aggregation
- **Secondary Metric**: Optional comparison value
- **Trend Indicator**: Optional time-based comparison

**Configuration Examples:**
```bash
# Total revenue KPI
Primary metric: revenue (Sum)
Secondary metric: revenue (Sum, Previous month)
Chart Type: Metric

# System uptime percentage
Primary metric: uptime_percentage (Average)
Format: Percentage
Chart Type: Metric
```

**When to Use:**
- ✅ Key performance indicators
- ✅ Single important values
- ✅ Goal monitoring
- ❌ Detailed breakdowns
- ❌ Trend analysis

### 7. **Heatmaps**

**Best Used For:**
- Two-dimensional correlations
- Pattern identification
- Density visualization
- Matrix-style data

**Data Requirements:**
- **X-axis**: Categorical or time field
- **Y-axis**: Categorical field
- **Cell Value**: Numeric aggregation
- **Optimal Size**: 3-20 categories per axis

**Configuration Examples:**
```bash
# Website activity by hour and day
X-axis: @timestamp (Date histogram, 1 hour)
Y-axis: day_of_week (Terms)
Cell value: Count of documents
Chart Type: Heatmap

# Error patterns by service and environment
X-axis: service.name (Terms, Top 10)
Y-axis: environment (Terms, All)
Cell value: Count of documents
Chart Type: Heatmap
```

**When to Use:**
- ✅ Two-dimensional patterns
- ✅ Correlation analysis
- ✅ Matrix-style data
- ❌ Single-dimension analysis
- ❌ Precise value reading

## 🎨 Chart Selection Decision Tree

### Step 1: Identify Your Data Structure

**Time Series Data:**
- **Single Metric**: Line chart or area chart
- **Multiple Metrics**: Multi-series line chart
- **Categories Over Time**: Stacked area chart or grouped bar chart

**Categorical Data:**
- **Compare Categories**: Bar chart (vertical or horizontal)
- **Show Proportions**: Pie chart or donut chart
- **Detailed Analysis**: Data table

**Two-Dimensional Data:**
- **Correlations**: Heatmap or scatter plot
- **Matrix Analysis**: Heatmap
- **Cross-tabulation**: Data table

### Step 2: Consider Your Audience

**Executive Dashboard:**
- **KPIs**: Metric displays
- **Trends**: Line charts
- **Comparisons**: Bar charts
- **Proportions**: Pie charts

**Analyst Dashboard:**
- **Detailed Data**: Data tables
- **Patterns**: Heatmaps
- **Trends**: Line charts with multiple series
- **Distributions**: Histograms

**Operational Dashboard:**
- **Real-time Metrics**: Metric displays
- **Status Monitoring**: Bar charts
- **Alerts**: Conditional formatting
- **Trends**: Area charts

### Step 3: Match Chart to Purpose

**Comparison**: Bar charts, horizontal bar charts
**Trend**: Line charts, area charts
**Composition**: Pie charts, stacked area charts
**Distribution**: Histograms, box plots
**Correlation**: Scatter plots, heatmaps

## 💡 Best Practices by Chart Type

### Bar Charts
```bash
✅ Do:
- Sort categories by value when possible
- Use consistent colors
- Start Y-axis at zero
- Label axes clearly

❌ Don't:
- Use too many categories (>20)
- Use 3D effects
- Truncate Y-axis inappropriately
- Mix positive and negative values poorly
```

### Line Charts
```bash
✅ Do:
- Use distinct colors for multiple series
- Add data point markers for few points
- Include trend lines when helpful
- Maintain consistent time intervals

❌ Don't:
- Use too many series (>5)
- Connect unrelated data points
- Use area charts for multiple overlapping series
- Ignore missing data points
```

### Pie Charts
```bash
✅ Do:
- Limit to 3-7 slices maximum
- Order slices by size
- Use distinct colors
- Include percentages in labels

❌ Don't:
- Use for too many categories
- Use 3D effects
- Compare multiple pie charts
- Use for negative values
```

### Data Tables
```bash
✅ Do:
- Sort by most important column
- Use consistent formatting
- Highlight key values
- Include totals and averages

❌ Don't:
- Show too many columns
- Use inconsistent precision
- Ignore null values
- Hide important metadata
```

## 🚨 Common Mistakes to Avoid

### Inappropriate Chart Selection
- **Pie charts with too many slices**: Use bar charts instead
- **Line charts for categories**: Use bar charts for discrete comparisons
- **3D charts**: Avoid unless absolutely necessary
- **Dual-axis confusion**: Only use when scales are related

### Poor Data Representation
- **Truncated axes**: Start bar charts at zero
- **Inconsistent scales**: Use same scale for comparisons
- **Too much data**: Aggregate or filter appropriately
- **Missing context**: Include time ranges and filters

### Design Issues
- **Color overuse**: Limit color palette
- **Cluttered legends**: Position and size appropriately
- **Unclear labels**: Use descriptive titles and axis labels
- **Poor contrast**: Ensure accessibility

## 🔗 Next Steps

After mastering chart types:

1. **Learn Data Preparation**: [Aggregations & Metrics](03_aggregations-metrics.md)
2. **Explore Time Series**: [Time Series Basics](04_time-series-basics.md)
3. **Build Complex Visualizations**: [Advanced Lens Features](../04-advanced-visualizations/05_advanced-lens-features.md)

## 📚 Additional Resources

- [Kibana Chart Types Documentation](https://www.elastic.co/guide/en/kibana/9.0/lens.html)
- [Data Visualization Best Practices](https://www.elastic.co/guide/en/kibana/9.0/visualization-best-practices.html)
- [Chart Selection Guide](https://www.elastic.co/guide/en/kibana/9.0/chart-selection-guide.html)

---

**Design Tip:** Always consider your audience and the story you want to tell with your data. The best chart is the one that clearly communicates your insights.