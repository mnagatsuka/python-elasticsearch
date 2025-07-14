# Kibana Lens Basics

Master the drag-and-drop visualization builder that makes creating charts and graphs intuitive and powerful.

## 🎯 What You'll Learn

Build stunning visualizations with Kibana's modern Lens interface:

- **Drag-and-Drop Creation** - Intuitive chart building
- **Smart Suggestions** - AI-powered visualization recommendations
- **Chart Types** - When to use different visualization types
- **Field Configuration** - Customize dimensions and metrics

## 🔍 Understanding Kibana Lens

Lens is Kibana's modern visualization builder that uses drag-and-drop functionality to create charts without requiring knowledge of complex query syntax.

### Key Concepts

**Lens Components:**
- **Data View**: Connection to your Elasticsearch data
- **Field Lists**: Available fields from your data
- **Chart Types**: Different visualization options
- **Configuration Panel**: Customize chart appearance and behavior

**Core Workflow:**
1. **Choose Data View** → Select your data source
2. **Drag Fields** → Add dimensions and metrics
3. **Select Chart Type** → Choose appropriate visualization
4. **Configure** → Customize appearance and behavior
5. **Save** → Add to dashboards or save as standalone

## 🏗️ Before You Begin

**Prerequisites:**
- Complete [Data Views & Index Patterns](../02-data-views-discovery/01_data-views-index-patterns.md)
- Understanding of your data structure and field types
- Basic knowledge of metrics and dimensions

**Required Setup:**
- Access to Kibana with data views configured
- Sample data or your own indices with meaningful fields

## 🔧 Creating Your First Lens Visualization

### 1. **Access Lens Interface**

```bash
# Navigation path
Kibana Home → Analytics → Lens
# Or from any dashboard: "Create visualization" → "Lens"
```

**Interface Overview:**
- **Left Panel**: Field lists and chart type selector
- **Center Canvas**: Visualization preview
- **Right Panel**: Configuration options
- **Top Bar**: Save, share, and time range controls

### 2. **Basic Chart Creation Workflow**

**Step 1: Select Data View**
```bash
1. Click "Change data view" if needed
2. Select your target data view
3. Review available fields in the left panel
```

**Step 2: Add Metrics (Y-axis)**
```bash
1. Drag numeric field to "Vertical axis" drop zone
2. Or click "+" next to field name → "Add to visualization"
3. Choose aggregation function:
   - Count: Number of documents
   - Sum: Total of all values
   - Average: Mean value
   - Max/Min: Highest/lowest values
   - Unique Count: Distinct values
```

**Step 3: Add Dimensions (X-axis)**
```bash
1. Drag categorical field to "Horizontal axis" drop zone
2. Configure bucketing:
   - Terms: Top values (categories)
   - Date Histogram: Time intervals
   - Histogram: Numeric ranges
   - Filters: Custom groupings
```

**Step 4: Choose Chart Type**
```bash
1. Click chart type selector (bar chart icon)
2. Select from available options:
   - Bar charts (vertical/horizontal)
   - Line charts
   - Area charts
   - Pie charts
   - Data tables
   - Metric displays
```

### 3. **Smart Suggestions Feature**

Lens automatically suggests appropriate visualizations based on your data:

**How Suggestions Work:**
- **Field Type Analysis**: Considers numeric vs. categorical fields
- **Data Patterns**: Analyzes data distribution and cardinality
- **Common Practices**: Recommends standard visualization patterns
- **Context Awareness**: Adapts suggestions based on existing fields

**Using Suggestions:**
```bash
1. Add your first field to any drop zone
2. Notice suggestion chips appear at the top
3. Click suggestion to auto-configure visualization
4. Modify as needed
```

## 📊 Common Visualization Patterns

### Web Analytics Dashboard

**Page Views Over Time:**
```bash
Data View: web_logs
X-axis: @timestamp (Date histogram, 1 hour interval)
Y-axis: Count of documents
Chart Type: Line chart
```

**Top Pages by Traffic:**
```bash
Data View: web_logs
X-axis: url.path (Terms, Top 10)
Y-axis: Count of documents
Chart Type: Horizontal bar chart
```

**Response Time Distribution:**
```bash
Data View: web_logs
X-axis: response_time (Histogram, interval: 100ms)
Y-axis: Count of documents
Chart Type: Vertical bar chart
```

### System Monitoring Dashboard

**CPU Usage Trends:**
```bash
Data View: system_metrics
X-axis: @timestamp (Date histogram, 5 minute interval)
Y-axis: system.cpu.usage (Average)
Chart Type: Area chart
```

**Memory Usage by Host:**
```bash
Data View: system_metrics
X-axis: host.name (Terms, Top 10)
Y-axis: system.memory.used.pct (Average)
Chart Type: Horizontal bar chart
```

**Disk Space Distribution:**
```bash
Data View: system_metrics
Slice by: host.name
Size by: system.disk.used.pct (Average)
Chart Type: Pie chart
```

### Business Analytics Dashboard

**Sales Revenue by Region:**
```bash
Data View: sales_data
X-axis: region (Terms, Top 10)
Y-axis: revenue (Sum)
Chart Type: Vertical bar chart
```

**Monthly Sales Trends:**
```bash
Data View: sales_data
X-axis: @timestamp (Date histogram, 1 month interval)
Y-axis: revenue (Sum)
Chart Type: Line chart
```

**Product Performance:**
```bash
Data View: sales_data
X-axis: product_category (Terms, Top 5)
Y-axis: quantity_sold (Sum)
Chart Type: Donut chart
```

## 🎛️ Advanced Lens Features

### 1. **Multi-Layer Visualizations**

**Adding Reference Lines:**
```bash
1. Click "Add layer" in configuration panel
2. Select "Reference line"
3. Configure value (static number or dynamic calculation)
4. Customize appearance (color, style, label)
```

**Multiple Metrics on Same Chart:**
```bash
1. Add first metric to Y-axis
2. Click "Add" button in vertical axis section
3. Add second metric with different aggregation
4. Lens automatically creates dual-axis chart
```

### 2. **Formula Fields**

Create custom calculations using Lens formulas:

**Basic Formula Examples:**
```bash
# Conversion rate calculation
count(kql='status: "success"') / count()

# Average response time in seconds
average(response_time) / 1000

# Percentage calculation
(sum(field1) / sum(field2)) * 100

# Difference between two periods
average(current_value) - average(previous_value)
```

**Creating Formula Fields:**
```bash
1. Click "Add" in Y-axis configuration
2. Select "Formula"
3. Enter formula using available functions
4. Add descriptive label
5. Format as needed (percentage, currency, etc.)
```

### 3. **Dynamic Bucketing**

**Date Histogram Auto-Interval:**
```bash
1. Drag date field to X-axis
2. Select "Date histogram"
3. Choose "Auto" interval
4. Lens automatically adjusts based on time range
```

**Custom Interval Calculations:**
```bash
# Adaptive bucketing based on data volume
- Small datasets: Minute intervals
- Medium datasets: Hour intervals  
- Large datasets: Day intervals
```

## 🎨 Customization Options

### Visual Appearance

**Color Schemes:**
```bash
1. Click "Appearance" tab in configuration
2. Select color palette:
   - Default: Kibana standard colors
   - Categorical: Distinct colors for categories
   - Sequential: Gradient for continuous values
   - Diverging: Center-focused for comparisons
```

**Axis Configuration:**
```bash
1. Expand axis configuration in right panel
2. Customize:
   - Title and labels
   - Scale type (linear, log)
   - Range (auto or manual)
   - Tick intervals
```

**Legend and Labels:**
```bash
1. Configure legend position and styling
2. Add data labels to show values
3. Customize tooltip information
4. Set chart title and description
```

### Interaction Behaviors

**Drill-Down Configuration:**
```bash
1. Enable "Allow drill-downs" in configuration
2. Configure drill-down actions:
   - Navigate to dashboard
   - Apply filters
   - Show underlying data
```

**Brush Selection:**
```bash
1. Enable for time series charts
2. Users can select time ranges by dragging
3. Automatically applies filters to dashboard
```

## 💡 Best Practices

### Chart Selection Guidelines

**Choose Appropriate Chart Types:**
- **Bar Charts**: Compare categories or show changes over time
- **Line Charts**: Show trends and patterns over time
- **Pie Charts**: Show proportions (limit to 5-7 categories)
- **Area Charts**: Show cumulative values over time
- **Tables**: Display precise values and details

**Avoid Common Mistakes:**
- Don't use pie charts for too many categories
- Avoid 3D charts that distort perception
- Don't use dual-axis charts unless necessary
- Limit colors to maintain readability

### Data Preparation Tips

**Field Selection:**
```bash
# Choose meaningful dimensions
✓ Geographic locations (country, region)
✓ Time periods (hour, day, month)
✓ Categories (product type, user segment)
✓ Status values (success, error, warning)

# Select appropriate metrics
✓ Counts and sums for totals
✓ Averages for typical values
✓ Percentiles for distribution analysis
✓ Unique counts for cardinality
```

**Performance Optimization:**
```bash
# Limit data volume
✓ Use time-based filtering
✓ Limit category counts (top 10-20)
✓ Aggregate appropriately
✓ Use sampling for large datasets
```

## 🚨 Troubleshooting Common Issues

### Data Display Problems

**1. Empty Visualization**
```bash
Symptoms: No data appears in chart
Solutions:
- Check time range settings
- Verify field selections
- Confirm data view has data
- Review any applied filters
```

**2. Unexpected Aggregations**
```bash
Symptoms: Wrong totals or calculations
Solutions:
- Check aggregation function (sum vs. average)
- Verify field data types
- Review bucket configuration
- Check for null values
```

**3. Performance Issues**
```bash
Symptoms: Slow loading or timeouts
Solutions:
- Reduce time range
- Limit bucket size
- Use sampling
- Optimize underlying queries
```

### Configuration Errors

**1. Missing Fields**
```bash
Symptoms: Expected fields don't appear
Solutions:
- Refresh field list in data view
- Check field mappings
- Verify index patterns
- Confirm data ingestion
```

**2. Chart Type Unavailable**
```bash
Symptoms: Desired chart type is grayed out
Solutions:
- Check field type compatibility
- Verify required field combinations
- Review aggregation requirements
- Add missing dimensions or metrics
```

## 🔗 Next Steps

After mastering Lens basics:

1. **Explore Chart Types**: [Chart Types Overview](02_chart-types-overview.md)
2. **Learn Advanced Features**: [Advanced Lens Features](../04-advanced-visualizations/05_advanced-lens-features.md)
3. **Build Dashboards**: [Dashboard Creation](../05-dashboards-collaboration/01_dashboard-creation.md)

## 📚 Additional Resources

- [Lens Documentation](https://www.elastic.co/guide/en/kibana/9.0/lens.html)
- [Formula Functions Reference](https://www.elastic.co/guide/en/kibana/9.0/lens-formulas.html)
- [Visualization Best Practices](https://www.elastic.co/guide/en/kibana/9.0/visualization-best-practices.html)

---

**Practice Tip:** Start with simple visualizations and gradually experiment with advanced features. The drag-and-drop interface makes it easy to try different configurations without risk.