# Claude Code Prompt: Create Kibana Learning Documentation

## Task Overview
Create comprehensive Kibana learning documentation in the `/docs` directory for developers and data analysts. The documentation should be based on the official Kibana learning agenda and structured for easy consumption, focusing on practical data visualization and dashboard creation skills.

## Directory Structure Requirements
Create the following structure in `/docs/learning`:

```
/docs/
├── README.md (main project documentation index)
└── learning/
    ├── README.md (main learning index with navigation to both Elasticsearch and Kibana)
    ├── elasticsearch/ (created separately)
    └── kibana/
        ├── README.md (Kibana learning index)
        ├── 01-kibana-foundations/
        │   ├── what-is-kibana.md
        │   ├── kibana-9-new-features.md
        │   ├── installation-setup.md
        │   └── interface-navigation.md
        ├── 02-data-views-discovery/
        │   ├── data-views-index-patterns.md
        │   ├── discover-application.md
        │   ├── field-management.md
        │   └── search-filtering.md
        ├── 03-visualization-fundamentals/
        │   ├── kibana-lens-basics.md
        │   ├── chart-types-overview.md
        │   ├── aggregations-metrics.md
        │   └── time-series-basics.md
        ├── 04-advanced-visualizations/
        │   ├── canvas-presentations.md
        │   ├── maps-geospatial.md
        │   ├── timelion-time-series.md
        │   └── advanced-lens-features.md
        ├── 05-dashboards-collaboration/
        │   ├── dashboard-creation.md
        │   ├── dashboard-interactions.md
        │   ├── sharing-embedding.md
        │   └── spaces-access-control.md
        ├── 06-advanced-features/
        │   ├── machine-learning-anomalies.md
        │   ├── alerting-notifications.md
        │   ├── apm-monitoring.md
        │   └── case-management.md
        ├── 07-production-performance/
        │   ├── performance-optimization.md
        │   ├── security-governance.md
        │   ├── api-integration.md
        │   └── troubleshooting.md
        └── examples/
            ├── sample-dashboards.md
            ├── visualization-patterns.md
            └── common-use-cases.md
```

## Content Guidelines

### Page Size and Readability
- Keep each markdown file focused on a single topic (one section from the agenda)
- Target 200-500 lines per file maximum to avoid overwhelming users
- Use clear headings, step-by-step instructions, and visual descriptions
- Include practical examples that users can follow along

### Content Requirements for Each Page
1. **Brief introduction** (2-3 sentences explaining the feature/concept)
2. **Key concepts** (bullet points of main ideas and terminology)
3. **Step-by-step instructions** (detailed procedures with UI navigation)
4. **Practical examples** (real-world scenarios and use cases)
5. **Best practices** (tips for effective visualization and dashboard design)
6. **Troubleshooting** (common issues and solutions)
7. **Next steps** (links to related topics)

### Kibana-Specific Content Focus
- UI navigation instructions (click paths, menu locations)
- Visual descriptions of interface elements
- Screenshot placeholders with detailed descriptions
- Field selection and drag-and-drop procedures
- Query and filter examples with KQL (Kibana Query Language)

### Code Examples and Configurations
- KQL query examples for filtering and searching
- JSON configurations for visualizations and dashboards
- REST API calls for automation and integration
- Sample data patterns and index configurations
- Canvas expression language examples

### Documentation Style
- Use action-oriented language (Click, Select, Drag, Configure)
- Include "Before you begin" prerequisites for each section
- Add warning callouts for important configuration notes
- Cross-reference related visualization types and features
- Use consistent terminology throughout (e.g., "data view" not "index pattern")

### Special Requirements for Kibana 9.0
- Highlight new UI theme and improved dark mode features
- Cover updated security model with internal API restrictions
- Include simplified saved query privilege management
- Document new dashboard interaction improvements
- Reference Canvas and Lens integration capabilities

## Content Focus Areas

### Visualization and Dashboard Creation
- Lens drag-and-drop functionality with smart suggestions
- Canvas workpad creation for presentations
- Maps configuration for geospatial data
- Dashboard layout and interaction design
- Multi-layer visualization strategies

### Data Exploration and Analysis
- Discover app usage for data exploration
- Field analysis and data distribution understanding
- Time-based filtering and date range controls
- Advanced search techniques with KQL
- Data view management and field customization

### Collaboration and Sharing
- Kibana Spaces setup and management
- Dashboard sharing methods (embed, URL, export)
- Role-based access control configuration
- Report generation and scheduling
- Integration with external tools

### Production and Operations
- Performance optimization for large datasets
- Security configuration and authentication
- Alerting and notification setup
- Machine learning feature implementation
- API usage for automation

## Exclusions
- Do not include detailed Elasticsearch administration topics
- Avoid covering deprecated features from older versions
- Skip advanced cluster management (focus on Kibana usage)
- Exclude marketing content about Elastic Cloud pricing

## Output Format
- All files should be in Markdown format
- Use consistent formatting with clear headings (H1, H2, H3)
- Include code blocks with appropriate syntax highlighting
- Add tables for feature comparisons and configuration options
- Use callout boxes for warnings, tips, and important notes

## Validation Criteria
Each page should answer:
1. What is this Kibana feature/capability?
2. When would you use it for data visualization or analysis?
3. How do you configure and use it? (with step-by-step instructions)
4. What are the best practices for effective implementation?
5. How does it integrate with other Kibana features?

## Navigation and User Experience
- Main project README.md should reference the learning documentation in `/docs/learning/`
- Learning README.md should provide a clear learning path progression for both Elasticsearch and Kibana
- Kibana README.md should provide navigation within the Kibana learning path  
- Include estimated time to complete each section
- Add prerequisite knowledge requirements (including relevant Elasticsearch concepts)
- Cross-link related topics and features between Elasticsearch and Kibana documentation
- Provide multiple entry points for different user types (analyst, developer, admin)
- Reference Elasticsearch concepts where Kibana depends on them (indices, mappings, queries)

Create documentation that serves as a practical guide for users who need to build effective data visualizations, dashboards, and analytics workflows using Kibana, emphasizing hands-on learning with real-world applications.