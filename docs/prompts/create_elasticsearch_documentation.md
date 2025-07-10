# Claude Code Prompt: Create Elasticsearch Learning Documentation

## Task Overview
Create comprehensive Elasticsearch learning documentation in the `/docs` directory for developers. The documentation should be based on the official Elasticsearch learning agenda and structured for easy consumption.

## Directory Structure Requirements
Create the following structure in `/docs/learning`:

```
/docs/
├── README.md (main project documentation index)
└── learning/
    ├── README.md (main learning index with navigation to both Elasticsearch and Kibana)
    ├── elasticsearch/
    │   ├── README.md (Elasticsearch learning index)
    │   ├── 01-foundations/
    │   │   ├── what-is-elasticsearch.md
    │   │   ├── core-concepts.md
    │   │   ├── installation-setup.md
    │   │   └── basic-api-interactions.md
    │   ├── 02-data-management/
    │   │   ├── document-operations.md
    │   │   ├── mapping-field-types.md
    │   │   └── index-lifecycle.md
    │   ├── 03-search-fundamentals/
    │   │   ├── query-dsl-basics.md
    │   │   ├── search-operations.md
    │   │   └── filtering-sorting.md
    │   ├── 04-advanced-search/
    │   │   ├── full-text-search.md
    │   │   ├── aggregations.md
    │   │   └── relevance-scoring.md
    │   ├── 05-modern-capabilities/
    │   │   ├── vector-search.md
    │   │   ├── semantic-search.md
    │   │   └── esql-basics.md
    │   ├── 06-performance-production/
    │   │   ├── optimization-strategies.md
    │   │   ├── monitoring-operations.md
    │   │   └── security-best-practices.md
    │   └── examples/
    │       ├── sample-queries.md
    │       ├── common-patterns.md
    │       └── troubleshooting.md
    └── kibana/ (to be created separately)
```

## Content Guidelines

### Page Size and Readability
- Keep each markdown file focused on a single topic (one section from the agenda)
- Target 200-500 lines per file maximum to avoid overwhelming developers
- Use clear headings, code blocks, and examples
- Include practical examples that developers can copy and run

### Content Requirements for Each Page
1. **Brief introduction** (2-3 sentences explaining the topic)
2. **Key concepts** (bullet points of main ideas)
3. **Practical examples** (working code snippets with explanations)
4. **Common use cases** (real-world scenarios)
5. **Best practices** (dos and don'ts)
6. **Next steps** (links to related topics)

### Code Examples
- Include working curl commands and REST API examples
- Provide JSON request/response examples
- Add language-specific client examples (Python, Java, JavaScript)
- Use realistic data in examples (not just "foo", "bar")

### Documentation Style
- Use developer-friendly language (concise, technical, actionable)
- Include command-line examples that can be copy-pasted
- Add troubleshooting tips for common issues
- Cross-reference related concepts with internal links

### Special Requirements
- Main project README.md should reference the learning documentation in `/docs/learning/`
- Learning README.md should serve as a navigation hub with learning paths for both Elasticsearch and Kibana
- Elasticsearch README.md should provide navigation within the Elasticsearch learning path
- Include cross-references between Elasticsearch and Kibana topics where relevant (e.g., index creation in Elasticsearch → data views in Kibana)
- Include version information (focus on Elasticsearch 9.0+ features)
- Add prerequisite knowledge for each section
- Include estimated reading/practice time for each page

## Content Focus Areas

### Based on Elasticsearch 9.0 Official Features
- Entitlements system (replacing Java SecurityManager)
- rank_vectors field type for late-interaction ranking
- semantic_text field (now GA)
- ES|QL LOOKUP JOIN (technical preview)
- Vector database capabilities
- Hybrid search functionality

### Developer-Oriented Topics
- RESTful API usage patterns
- Performance optimization techniques
- Integration with modern development stacks
- Docker and cloud deployment patterns
- Monitoring and debugging approaches

## Exclusions
- Do not include detailed system administration topics
- Avoid covering deprecated features from older versions
- Skip advanced cluster management (focus on development usage)
- Exclude marketing content or business case discussions

## Output Format
- All files should be in Markdown format
- Use consistent formatting and code block syntax highlighting
- Include a table of contents in longer files
- Add metadata headers where appropriate

## Validation Criteria
Each page should answer:
1. What is this concept/feature?
2. Why would a developer use it?
3. How do you implement it? (with examples)
4. What are the common pitfalls?
5. Where can you learn more?

Create documentation that serves as a practical reference guide for developers who need to implement Elasticsearch in their applications, focusing on hands-on learning rather than theoretical concepts.