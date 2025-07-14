# Machine Learning & Anomalies

Leverage Elastic's machine learning capabilities to automatically detect anomalies, patterns, and outliers in your data.

## 🎯 What You'll Learn

Master automated anomaly detection and pattern recognition:

- **Anomaly Detection** - Identify unusual patterns in your data
- **Time Series Analysis** - Detect trends and seasonal patterns
- **Outlier Detection** - Find data points that deviate from normal
- **Alerting Integration** - Set up automated notifications

## 🤖 Understanding Elastic Machine Learning

Elastic's ML capabilities use unsupervised learning algorithms to automatically identify patterns and anomalies in your data without requiring labeled training data.

### Key Concepts

**Anomaly Detection**: Identifies unusual patterns in time series data
**Data Frame Analytics**: Performs outlier detection and regression analysis
**Inference**: Applies pre-trained models to new data
**Natural Language Processing**: Analyzes text data for patterns

### ML Job Types

**Single Metric Jobs**: Monitor one metric for anomalies
**Multi-Metric Jobs**: Monitor multiple metrics simultaneously
**Population Jobs**: Compare individuals against a population
**Advanced Jobs**: Complex analysis with custom functions

## 🏗️ Before You Begin

**Prerequisites:**
- Complete [Time Series Basics](../03-visualization-fundamentals/04_time-series-basics.md)
- Understanding of your data patterns and normal behavior
- Basic knowledge of statistical concepts

**Required Setup:**
- Elasticsearch cluster with ML features enabled
- Sufficient data for training (typically 2-4 weeks)
- Appropriate data views and time fields

**License Requirements:**
- Basic license: Limited ML features
- Gold/Platinum license: Full ML capabilities
- Enterprise license: Advanced features

## 🔍 Anomaly Detection

### 1. **Single Metric Anomaly Detection**

**Use Cases:**
- Website response time monitoring
- System CPU usage patterns
- Sales volume fluctuations
- Error rate spikes

**Job Configuration:**
```bash
# Basic setup
Job ID: response_time_anomaly
Index: web_logs
Time field: @timestamp
Metric: response_time (mean)

# Advanced settings
Bucket span: 15m (data collection interval)
Detector: Mean response time anomaly
Influence threshold: 75 (sensitivity)
```

**Creating Single Metric Jobs:**
```bash
# Navigation
Kibana → Machine Learning → Anomaly Detection → Create job

# Job wizard steps
1. Choose data source and time range
2. Select metric and aggregation
3. Configure bucket span
4. Set detector function
5. Review and create job
```

### 2. **Multi-Metric Anomaly Detection**

**Use Cases:**
- System performance monitoring (CPU, memory, disk)
- Business metric correlation (sales, traffic, conversions)
- Multi-dimensional analysis
- Comprehensive health monitoring

**Job Configuration:**
```bash
# Multi-metric setup
Job ID: system_performance_anomaly
Index: system_metrics
Time field: @timestamp

# Detectors
Detector 1: Mean CPU usage by host
Detector 2: Mean memory usage by host
Detector 3: Mean disk usage by host

# Influence analysis
Partition field: host.name
Influence threshold: 50
```

**Advanced Multi-Metric Configuration:**
```bash
# Complex detector functions
High mean: Detect only high values
Low mean: Detect only low values
High/Low mean: Detect both high and low
Non-zero count: Detect presence/absence
Rare: Detect infrequent events
```

### 3. **Population Analysis**

**Use Cases:**
- User behavior analysis
- Geographic pattern detection
- Comparative performance analysis
- Identifying outlier entities

**Job Configuration:**
```bash
# Population job setup
Job ID: user_behavior_population
Index: user_activity
Time field: @timestamp

# Population configuration
Detector: Mean session_duration
Over field: user_id (population)
By field: page_category (split)
Partition field: region (group)
```

**Population Analysis Examples:**
```bash
# E-commerce user behavior
Detector: Mean purchase_amount
Over field: user_id
By field: product_category
Population: All users

# System performance by host
Detector: Mean response_time
Over field: host.name
By field: service_name
Population: All hosts
```

## 📊 Anomaly Detection Visualization

### 1. **Anomaly Explorer**

**Key Features:**
- Interactive timeline of anomalies
- Severity scoring and ranking
- Drill-down capabilities
- Contextual information

**Navigation:**
```bash
# Access anomaly explorer
Machine Learning → Anomaly Detection → Anomaly Explorer

# View options
Timeline view: Chronological anomaly display
Swimlane view: By job, influencer, or partition
Table view: Detailed anomaly list
```

### 2. **Single Metric Viewer**

**Features:**
- Detailed view of specific job results
- Anomaly scoring and confidence intervals
- Forecast capabilities
- Raw data overlay

**Usage:**
```bash
# Access single metric viewer
Machine Learning → Anomaly Detection → Single Metric Viewer

# Configuration
Job selection: Choose specific job
Time range: Focus on specific period
Detector: Select specific detector
Forecast: Enable/disable predictions
```

### 3. **Dashboard Integration**

**Anomaly Visualizations:**
```bash
# ML anomaly charts
Visualization type: ML anomaly charts
Job selection: Choose relevant jobs
Time range: Dashboard time picker
Threshold: Anomaly score threshold

# Anomaly count metrics
Metric: Anomaly count
Filters: Severity levels
Aggregation: Count by time period
Alerts: Threshold notifications
```

## 🎯 Data Frame Analytics

### 1. **Outlier Detection**

**Use Cases:**
- Fraud detection
- Quality control
- Data validation
- Behavioral analysis

**Job Configuration:**
```bash
# Outlier detection setup
Job ID: transaction_outliers
Source index: financial_transactions
Destination index: transaction_outliers
Analysis type: Outlier detection

# Feature selection
Analyzed fields: amount, merchant_category, time_of_day
Excluded fields: transaction_id, user_id
Outlier fraction: 0.05 (5% of data)
```

**Outlier Analysis Results:**
```bash
# Result interpretation
Outlier score: 0.0 (normal) to 1.0 (highly anomalous)
Feature influence: Contributing factors
Outlier reasons: Explanation of anomaly
Visual exploration: Scatter plots and distributions
```

### 2. **Regression Analysis**

**Use Cases:**
- Predictive modeling
- Feature importance analysis
- Trend analysis
- Performance optimization

**Job Configuration:**
```bash
# Regression setup
Job ID: sales_prediction
Source index: historical_sales
Dependent variable: sales_amount
Independent variables: season, region, marketing_spend
Analysis type: Regression

# Model validation
Training percentage: 80%
Validation method: Cross-validation
Metrics: R-squared, RMSE, MAE
```

## 🔔 Alerting and Notifications

### 1. **Anomaly Detection Alerts**

**Watch Configuration:**
```bash
# Watcher setup
Watch ID: high_severity_anomalies
Trigger: Schedule (every 5 minutes)
Input: Elasticsearch query for anomalies
Condition: Anomaly score > 75
Actions: Email, webhook, index

# Query example
{
  "query": {
    "bool": {
      "must": [
        {"term": {"job_id": "response_time_anomaly"}},
        {"range": {"record_score": {"gte": 75}}},
        {"range": {"timestamp": {"gte": "now-5m"}}}
      ]
    }
  }
}
```

### 2. **Kibana Alerting Integration**

**Alert Rules:**
```bash
# Navigation
Kibana → Stack Management → Rules and Connectors

# ML alert types
Anomaly detection alert: Based on ML jobs
Threshold alert: Custom thresholds
Index threshold: Query-based alerts

# Configuration
Anomaly detection alert:
- Job selection: Choose ML job
- Severity threshold: Score threshold
- Lookback period: Time window
- Top N: Number of influencers
```

## 💡 Best Practices

### 1. **Job Configuration**

**Data Preparation:**
```bash
# Data quality
Clean data: Remove duplicates and errors
Consistent timestamps: Proper time field formatting
Sufficient volume: 2-4 weeks of historical data
Regular intervals: Consistent data collection

# Field selection
Relevant fields: Focus on meaningful metrics
Numeric fields: Use appropriate aggregations
Categorical fields: Limit cardinality
Time fields: Proper date formatting
```

**Bucket Span Selection:**
```bash
# Guidelines
High-frequency data: 1-15 minutes
Medium-frequency data: 15 minutes - 1 hour
Low-frequency data: 1 hour - 1 day
Batch data: 1 day or more

# Considerations
Data collection frequency
Business requirements
Computational resources
Alert response time
```

### 2. **Model Training**

**Training Period:**
```bash
# Recommendations
Minimum: 2 weeks of data
Optimal: 4-8 weeks of data
Maximum: 12 weeks of data
Seasonal data: Full seasonal cycle

# Training considerations
Include normal patterns
Avoid known anomalies
Represent typical behavior
Account for seasonal variations
```

### 3. **Threshold Tuning**

**Anomaly Scoring:**
```bash
# Score interpretation
0-25: Minor anomaly
25-50: Moderate anomaly
50-75: Major anomaly
75-100: Critical anomaly

# Threshold adjustment
Conservative: Score > 75
Balanced: Score > 50
Sensitive: Score > 25
Custom: Based on use case
```

## 🚨 Common ML Pitfalls

### Data Issues
- **Insufficient data**: Not enough historical data for training
- **Data quality**: Dirty or inconsistent data
- **Seasonal patterns**: Not accounting for regular patterns
- **Data drift**: Changes in data patterns over time

### Configuration Problems
- **Wrong bucket span**: Inappropriate time intervals
- **Field selection**: Including irrelevant or noisy fields
- **Threshold settings**: Too sensitive or too conservative
- **Resource allocation**: Insufficient computational resources

### Interpretation Errors
- **False positives**: Normal behavior flagged as anomalous
- **False negatives**: Missing actual anomalies
- **Context ignorance**: Not considering business context
- **Correlation confusion**: Mistaking correlation for causation

## 🔗 Next Steps

After mastering ML anomaly detection:

1. **Advanced Alerting**: [Alerting & Notifications](02_alerting-notifications.md)
2. **Performance Monitoring**: [APM Monitoring](03_apm-monitoring.md)
3. **Production Optimization**: [Performance Optimization](../07-production-performance/01_performance-optimization.md)

## 📚 Additional Resources

- [Elastic ML Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/xpack-ml.html)
- [ML API Reference](https://www.elastic.co/guide/en/elasticsearch/reference/9.0/ml-apis.html)
- [Anomaly Detection Best Practices](https://www.elastic.co/guide/en/machine-learning/9.0/ml-best-practices.html)

---

**ML Tip:** Machine learning is most effective when combined with domain expertise. Use ML to identify patterns, but always validate results with business knowledge.