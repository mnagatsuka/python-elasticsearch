# Claude Code Prompt: Create Elasticsearch-DSL with FastAPI Learning Documentation

## Task Overview
Create comprehensive Elasticsearch-DSL with FastAPI learning documentation in the `/docs/learning` directory for developers building modern search applications. The documentation should focus on practical integration patterns, async programming, and production-ready implementations.

## Directory Structure Requirements
Create the following structure in `/docs/learning`:

```
/docs/
├── README.md (main project documentation index)
└── learning/
    ├── README.md (main learning index)
    ├── elasticsearch/ (created separately)
    ├── kibana/ (created separately)
    └── elasticsearch-dsl-fastapi/
        ├── README.md (Elasticsearch-DSL with FastAPI learning index)
        ├── 01-foundations-setup/
        │   ├── 01_ecosystem-overview.md
        │   ├── 02_installation-configuration.md
        │   ├── 03_async-patterns.md
        │   └── 04_development-environment.md
        ├── 02-elasticsearch-dsl-integration/
        │   ├── 01_document-models-mapping.md
        │   ├── 02_async-document-operations.md
        │   ├── 03_index-management.md
        │   └── 04_migration-strategies.md
        ├── 03-fastapi-integration/
        │   ├── 01_query-builder-patterns.md
        │   ├── 02_api-endpoint-design.md
        │   ├── 03_pydantic-integration.md
        │   └── 04_dependency-injection.md
        ├── 04-advanced-search/
        │   ├── 01_complex-queries.md
        │   ├── 02_async-search-performance.md
        │   ├── 03_aggregations-faceting.md
        │   └── 04_geospatial-vector-search.md
        ├── 05-data-modeling/
        │   ├── 01_pydantic-validation.md
        │   ├── 02_document-relationships.md
        │   ├── 03_schema-design.md
        │   └── 04_serialization-patterns.md
        ├── 06-production-patterns/
        │   ├── 01_monitoring-logging.md
        │   ├── 02_security-authentication.md
        │   ├── 03_performance-optimization.md
        │   └── 04_error-handling.md
        ├── 07-testing-deployment/
        │   ├── 01_testing-strategies.md
        │   ├── 02_deployment-patterns.md
        │   ├── 03_ci-cd-integration.md
        │   └── 04_operational-monitoring.md
        └── examples/
            ├── 01_basic-patterns.md
            ├── 02_search-applications.md
            └── 03_integration-examples.md
```

## Content Guidelines

### Page Size and Readability
- Keep each markdown file focused on a single topic (200-400 lines max)
- Emphasize practical code examples and implementation patterns
- Use clear step-by-step instructions with code snippets
- Include working examples that developers can copy and adapt

### Content Requirements for Each Page
1. **Brief introduction** (2-3 sentences explaining the concept/pattern)
2. **Key concepts** (bullet points of main ideas and terminology)
3. **Implementation examples** (working code with async/await patterns)
4. **Best practices** (production-ready recommendations)
5. **Common pitfalls** (what to avoid and troubleshooting tips)
6. **Integration points** (how it connects to other components)
7. **Next steps** (links to related topics)

### FastAPI + Elasticsearch-DSL Specific Content
- Async/await patterns throughout all examples
- Dependency injection using FastAPI's `Depends`
- Pydantic model integration for request/response validation
- Error handling with FastAPI exception handlers
- OpenAPI documentation integration
- Connection management and lifecycle patterns

### Code Examples and Configurations
- Complete FastAPI application examples with async Elasticsearch
- Document model definitions using elasticsearch-dsl
- API endpoint implementations with proper async patterns
- Query builder patterns using fastapi-elasticsearch decorators
- Pydantic models for request/response validation
- Docker and docker-compose configurations
- Test examples with async test clients

### Documentation Style
- Use async/await syntax consistently in all examples
- Include proper type hints and modern Python patterns
- Show complete working examples, not just fragments
- Add performance considerations and optimization tips
- Cross-reference FastAPI and Elasticsearch documentation
- Use consistent naming conventions (snake_case for Python)

### Special Requirements for Latest elasticsearch-dsl (8.18.0+)
- Highlight that elasticsearch-dsl is now part of the main client
- Cover migration from separate package installation
- Document new async capabilities and patterns
- Include proper connection management with app lifecycle
- Show integration with FastAPI's background tasks

## Content Focus Areas

### Modern Development Patterns
- FastAPI async/await best practices with Elasticsearch
- Dependency injection patterns for Elasticsearch clients
- Pydantic integration for data validation and serialization
- Background task processing for indexing operations
- Health checks and monitoring endpoints

### Search Application Architecture
- RESTful API design for search operations
- Query parameter validation and transformation
- Response formatting and pagination patterns
- Caching strategies for search results
- Rate limiting and performance considerations

### Production Implementation
- Connection pooling and resource management
- Error handling and retry strategies
- Logging and monitoring integration
- Security patterns and authentication
- Deployment with Docker and orchestration

### Integration Patterns
- Elasticsearch index lifecycle management
- Bulk operations with async processing
- Real-time indexing with FastAPI background tasks
- Search result transformation and aggregation
- Multi-index and cross-cluster search patterns

## Examples Section Guidelines
The examples/ directory should contain **moderate-sized, focused examples**:

### examples/01_basic-patterns.md (Essential)
- Simple FastAPI + Elasticsearch-DSL setup
- Basic CRUD operations with async patterns
- Query parameter handling and validation
- Response formatting examples

### examples/02_search-applications.md (Moderate)
- Complete search API implementation
- Faceted search with aggregations
- Auto-complete and suggestion endpoints
- Search result highlighting and scoring

### examples/03_integration-examples.md (Optional - can be removed if space is limited)
- Authentication integration patterns
- Monitoring and health check implementations
- Background task examples for indexing
- Error handling and logging patterns

**Note**: If documentation becomes too large, prioritize removing `03_integration-examples.md` first, then reduce content in `02_search-applications.md` to essential patterns only.

## Exclusions
- Do not include detailed DevOps or infrastructure management
- Avoid covering deprecated elasticsearch-dsl patterns
- Skip basic Python or FastAPI tutorials (assume developer knowledge)
- Exclude comprehensive Elasticsearch cluster administration

## Output Format
- All files should be in Markdown format
- Use syntax highlighting for Python, JSON, and YAML code blocks
- Include table of contents for longer files
- Add callout boxes for important warnings and tips
- Use consistent code formatting with proper indentation

## Validation Criteria
Each page should answer:
1. How do you implement this pattern with async FastAPI and Elasticsearch?
2. What are the performance and scalability considerations?
3. How does this integrate with other FastAPI and Elasticsearch features?
4. What are the common mistakes and how to avoid them?
5. How do you test and monitor this functionality?

## Navigation and User Experience
- Main project README.md should reference the learning documentation
- Learning README.md should provide clear progression through all three technologies
- Elasticsearch-DSL-FastAPI README.md should outline the learning path and prerequisites
- Include estimated time to complete each section (assume intermediate Python knowledge)
- Cross-link with pure Elasticsearch and Kibana documentation where relevant
- Provide multiple entry points for different experience levels

Create documentation that serves as a practical guide for developers building production-ready search applications using FastAPI with Elasticsearch-DSL, emphasizing modern async patterns, type safety, and scalable architecture design.