# Canvas Presentations

Create pixel-perfect infographics, presentations, and custom reports with Kibana's powerful Canvas application.

## 🎯 What You'll Learn

Master the art of data storytelling with Canvas:

- **Canvas Interface** - Workpad creation and element management
- **Data Elements** - Connecting visualizations to live data
- **Design Principles** - Creating compelling visual narratives
- **Expression Language** - Advanced data transformations

## 🎨 Understanding Canvas

Canvas is Kibana's presentation layer that allows you to create pixel-perfect, dynamic displays by combining data visualizations with custom layouts, images, and styling.

### Key Concepts

**Workpad**: The main Canvas document containing your presentation
**Elements**: Individual components (charts, text, images, shapes)
**Pages**: Multiple slides within a single workpad
**Expression Language**: Powerful data transformation syntax

### Canvas vs. Dashboards

**Canvas Advantages:**
- Pixel-perfect design control
- Custom layouts and branding
- Rich text and image integration
- Presentation-ready formats

**Dashboard Advantages:**
- Faster creation process
- Built-in responsive design
- Standard interaction patterns
- Easier maintenance

## 🏗️ Before You Begin

**Prerequisites:**
- Complete [Kibana Lens Basics](../03-visualization-fundamentals/01_kibana-lens-basics.md)
- Understanding of your data structure
- Basic design and layout principles

**Required Setup:**
- Access to Kibana with Canvas enabled
- Data views with meaningful data
- Optional: Brand assets (logos, colors, fonts)

## 🖼️ Canvas Interface Overview

### 1. **Workpad Management**

**Creating a New Workpad:**
```bash
# Navigation
Kibana Home → Analytics → Canvas → Create workpad

# Workpad Options
Blank workpad: Start from scratch
Templates: Pre-built layouts
Clone existing: Copy from another workpad
```

**Workpad Settings:**
```bash
# Basic Configuration
Name: Descriptive title
Description: Purpose and audience
Tags: Categorization and search

# Layout Settings
Size: Custom dimensions or standard formats
Background: Color, gradient, or image
Grid: Alignment assistance
```

### 2. **Element Management**

**Adding Elements:**
```bash
# From toolbar
Charts: Pre-built visualization types
Text: Static or dynamic text blocks
Images: Logos, icons, backgrounds
Shapes: Rectangles, circles, lines

# From sidebar
Asset library: Reusable components
Saved visualizations: Import from other apps
```

**Element Properties:**
```bash
# Position and Size
X/Y coordinates: Precise positioning
Width/Height: Exact dimensions
Rotation: Angle adjustments
Z-index: Layer ordering

# Styling
Fill: Colors, gradients, patterns
Border: Style, width, color
Shadow: Depth and dimension
Opacity: Transparency effects
```

## 📊 Data Integration

### 1. **Connecting to Data Sources**

**Elasticsearch Integration:**
```bash
# Data source configuration
Data source: Elasticsearch index
Time filter: Dynamic time range
Filters: KQL queries for data subset
Fields: Select relevant fields
```

**Data Source Expression:**
```bash
# Basic Elasticsearch query
essql query="SELECT * FROM your_index WHERE @timestamp > NOW() - INTERVAL 1 DAY"

# Filtered data
filters | essql query="SELECT field1, field2 FROM your_index" | head 100

# Aggregated data
filters | essql query="SELECT COUNT(*) as count, field1 FROM your_index GROUP BY field1"
```

### 2. **Data Transformation**

**Basic Transformations:**
```bash
# Filtering
filters | essql query="SELECT * FROM index WHERE status = 'active'"

# Sorting
filters | essql query="SELECT * FROM index ORDER BY timestamp DESC"

# Limiting
filters | essql query="SELECT * FROM index LIMIT 50"

# Grouping
filters | essql query="SELECT category, COUNT(*) as count FROM index GROUP BY category"
```

**Advanced Transformations:**
```bash
# Mathematical operations
filters | essql query="SELECT value * 100 as percentage FROM index"

# Date formatting
filters | essql query="SELECT DATE_FORMAT(timestamp, 'yyyy-MM-dd') as date FROM index"

# Conditional logic
filters | essql query="SELECT CASE WHEN value > 100 THEN 'High' ELSE 'Low' END as category FROM index"
```

## 🎨 Design Elements

### 1. **Chart Elements**

**Area Chart:**
```bash
# Configuration
Data source: Elasticsearch query
X-axis: Time field
Y-axis: Numeric aggregation
Color: Series differentiation
Style: Fill opacity, line thickness
```

**Bar Chart:**
```bash
# Configuration
Data source: Aggregated data
Categories: Grouping field
Values: Numeric values
Orientation: Vertical or horizontal
Colors: Category-based coloring
```

**Metric Display:**
```bash
# Single value display
Data source: Aggregated metric
Value: Primary number
Label: Descriptive text
Format: Currency, percentage, custom
Font: Size, weight, color
```

**Data Table:**
```bash
# Tabular data display
Data source: Detailed records
Columns: Field selection
Sorting: Column-based ordering
Pagination: Row limiting
Styling: Fonts, colors, borders
```

### 2. **Text Elements**

**Static Text:**
```bash
# Fixed content
Title: Large, bold headers
Subtitle: Secondary information
Body: Detailed explanations
Footer: Disclaimers, sources

# Styling options
Font: Family, size, weight
Color: Text and background
Alignment: Left, center, right
Spacing: Line height, margins
```

**Dynamic Text:**
```bash
# Data-driven content
filters | essql query="SELECT COUNT(*) as total FROM index"
| math "total"
| formatnumber "0,0"
| markdown "**Total Records:** {{value}}"

# Conditional text
filters | essql query="SELECT AVG(value) as avg FROM index"
| if condition={gt 100} then="Performance is Good" else="Performance Needs Improvement"
```

### 3. **Image Elements**

**Static Images:**
```bash
# Logo placement
Asset library: Upload company logos
URL: Link to external images
Base64: Embedded image data

# Styling
Size: Width and height
Position: Absolute positioning
Opacity: Transparency
Filters: Grayscale, blur, contrast
```

**Dynamic Images:**
```bash
# Conditional images
filters | essql query="SELECT status FROM index LIMIT 1"
| switch case="active" then={asset id="green-icon"}
         case="inactive" then={asset id="red-icon"}
         default={asset id="gray-icon"}
```

### 4. **Shape Elements**

**Basic Shapes:**
```bash
# Rectangle
Fill: Solid color or gradient
Border: Style and color
Corner radius: Rounded edges
Shadow: Depth effect

# Circle
Fill: Background color
Border: Outline styling
Size: Diameter specification
Position: Center coordinates
```

**Advanced Shapes:**
```bash
# Progress bars
Rectangle with dynamic width based on data
Color coding for different value ranges
Text overlay for percentage display

# Status indicators
Circles with conditional coloring
Size variations based on importance
Tooltip information on hover
```

## 🎭 Canvas Templates and Layouts

### 1. **Executive Dashboard Template**

**Layout Components:**
```bash
# Header section
Company logo (top-left)
Dashboard title (center)
Time range indicator (top-right)
Navigation menu (full width)

# Key metrics row
KPI cards with large numbers
Trend indicators (up/down arrows)
Comparison to previous period
Color coding for performance

# Main content area
Primary chart (60% width)
Secondary charts (40% width)
Data table for details
Footer with update time
```

### 2. **Monitoring Dashboard Template**

**Layout Components:**
```bash
# Status overview
System health indicators
Service availability metrics
Alert count and severity
Current time and timezone

# Performance metrics
Response time trends
Resource utilization charts
Error rate indicators
Throughput measurements

# Detailed analysis
Host-specific breakdowns
Service dependency maps
Historical comparison charts
Diagnostic information
```

### 3. **Sales Report Template**

**Layout Components:**
```bash
# Report header
Company branding
Report title and period
Generation timestamp
Audience information

# Summary section
Total revenue metric
Growth rate indicator
Top performing products
Regional breakdown

# Detailed analysis
Monthly trend charts
Category performance
Customer segmentation
Forecast projections
```

## 🔧 Advanced Canvas Features

### 1. **Multi-Page Workpads**

**Page Navigation:**
```bash
# Page management
Add new pages: Duplicate or blank
Page transitions: Smooth animations
Navigation controls: Previous/Next buttons
Page indicators: Dots or numbers

# Auto-advance
Timer: Automatic page progression
Loop: Continuous cycling
Pause: Manual control
Speed: Configurable intervals
```

### 2. **Interactive Elements**

**Filters and Controls:**
```bash
# Time filter
Time picker integration
Custom time ranges
Relative time options
Timezone handling

# Dropdown filters
Category selection
Multi-select options
Dynamic option loading
Filter persistence
```

### 3. **Real-time Updates**

**Auto-refresh Configuration:**
```bash
# Refresh settings
Interval: 30s, 1m, 5m, 15m
Scope: Entire workpad or specific elements
Pause: Manual control
Visual indicators: Last update timestamp

# Performance optimization
Efficient queries
Minimal data transfer
Caching strategies
Connection pooling
```

## 💡 Best Practices

### Design Principles

**Visual Hierarchy:**
```bash
# Typography
Headers: Large, bold fonts
Subheaders: Medium weight
Body text: Readable size
Captions: Smaller, subdued

# Color usage
Primary: Main brand colors
Secondary: Supporting colors
Accent: Highlight important data
Neutral: Background and text
```

**Layout Guidelines:**
```bash
# Grid system
Consistent spacing
Aligned elements
Proper margins
Balanced composition

# White space
Breathing room around elements
Logical grouping
Visual separation
Clean, uncluttered design
```

### Performance Optimization

**Data Efficiency:**
```bash
# Query optimization
Limit result sets
Use appropriate aggregations
Filter early in pipeline
Cache frequently used data

# Element optimization
Minimize complex calculations
Use efficient visualization types
Optimize image sizes
Reduce unnecessary updates
```

### Content Strategy

**Storytelling:**
```bash
# Narrative structure
Problem statement
Supporting evidence
Key insights
Actionable recommendations

# Progressive disclosure
High-level overview first
Drill-down capabilities
Contextual information
Supporting details
```

## 🚨 Common Canvas Pitfalls

### Design Issues
- **Information overload**: Too many elements on one page
- **Inconsistent branding**: Mixed fonts, colors, and styles
- **Poor contrast**: Hard to read text and unclear visuals
- **Misaligned elements**: Unprofessional appearance

### Technical Problems
- **Slow performance**: Complex queries and large datasets
- **Data freshness**: Outdated information
- **Responsive issues**: Fixed layouts on different screen sizes
- **Expression errors**: Incorrect syntax in transformations

### User Experience
- **Unclear navigation**: Difficult to find information
- **Missing context**: Lack of time ranges and filters
- **Overwhelming detail**: Too much information at once
- **Static content**: No interactivity or updates

## 🔗 Next Steps

After mastering Canvas:

1. **Advanced Visualizations**: [Maps & Geospatial](02_maps-geospatial.md)
2. **Dashboard Integration**: [Dashboard Creation](../05-dashboards-collaboration/01_dashboard-creation.md)
3. **Sharing and Collaboration**: [Sharing & Embedding](../05-dashboards-collaboration/03_sharing-embedding.md)

## 📚 Additional Resources

- [Canvas Documentation](https://www.elastic.co/guide/en/kibana/9.0/canvas.html)
- [Canvas Expression Language](https://www.elastic.co/guide/en/kibana/9.0/canvas-expression-language.html)
- [Canvas Function Reference](https://www.elastic.co/guide/en/kibana/9.0/canvas-function-reference.html)

---

**Design Tip:** Canvas is powerful but requires thoughtful design. Start with a clear story and purpose, then build the visual elements to support that narrative.