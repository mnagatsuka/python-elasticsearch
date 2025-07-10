# Learning Hub

Welcome to the comprehensive learning documentation for Elasticsearch and Kibana. This guide is designed for developers who want to learn and implement these technologies in their applications.

## 🎯 Learning Paths

### 📊 Elasticsearch Learning Path
**Master the search and analytics engine**

[📖 **Start Elasticsearch Learning →**](elasticsearch/README.md)

**What you'll learn:**
- Core concepts and architecture
- Document management and indexing
- Search operations and query DSL
- Advanced search capabilities
- Modern features like vector search and semantic search
- Performance optimization and production best practices

**Prerequisites:** Basic understanding of REST APIs and JSON
**Total estimated time:** 8-12 hours

### 📈 Kibana Learning Path
**Coming Soon**

Kibana learning documentation will be added to help you master data visualization and analytics dashboards.

## 🚀 Quick Start

If you're new to the Elastic Stack, we recommend starting with:

1. [What is Elasticsearch?](elasticsearch/01-foundations/what-is-elasticsearch.md)
2. [Installation and Setup](elasticsearch/01-foundations/installation-setup.md)
3. [Basic API Interactions](elasticsearch/01-foundations/basic-api-interactions.md)

## 🛠️ Development Environment

This project includes a complete development environment with:
- **Elasticsearch 9.0.2** (LTS) - Search and analytics engine
- **Kibana 9.0.2** (LTS) - Data visualization and management
- **FastAPI** - Python web framework for API development
- **Docker** - Containerized development environment

### Getting Started with the Environment

```bash
# Start the development environment
docker compose up -d

# Verify services are running
curl http://localhost:9200  # Elasticsearch
curl http://localhost:5601  # Kibana
curl http://localhost:8000  # FastAPI
```

## 📚 Learning Resources

### By Skill Level

**Beginner (New to Elasticsearch)**
- [Foundations](elasticsearch/01-foundations/README.md)
- [Basic API Interactions](elasticsearch/01-foundations/basic-api-interactions.md)
- [Core Concepts](elasticsearch/01-foundations/core-concepts.md)

**Intermediate (Some search experience)**
- [Search Fundamentals](elasticsearch/03-search-fundamentals/README.md)
- [Data Management](elasticsearch/02-data-management/README.md)
- [Advanced Search](elasticsearch/04-advanced-search/README.md)

**Advanced (Production implementation)**
- [Modern Capabilities](elasticsearch/05-modern-capabilities/README.md)
- [Performance & Production](elasticsearch/06-performance-production/README.md)
- [Examples & Patterns](elasticsearch/examples/README.md)

### By Use Case

**Building Search Applications**
- [Full-text Search](elasticsearch/04-advanced-search/full-text-search.md)
- [Vector Search](elasticsearch/05-modern-capabilities/vector-search.md)
- [Semantic Search](elasticsearch/05-modern-capabilities/semantic-search.md)

**Data Analytics & Reporting**
- [Aggregations](elasticsearch/04-advanced-search/aggregations.md)
- [ES|QL Basics](elasticsearch/05-modern-capabilities/esql-basics.md)

**Production Deployment**
- [Performance Optimization](elasticsearch/06-performance-production/optimization-strategies.md)
- [Security Best Practices](elasticsearch/06-performance-production/security-best-practices.md)
- [Monitoring & Operations](elasticsearch/06-performance-production/monitoring-operations.md)

## 🤝 Integration Examples

Learn how to integrate Elasticsearch with popular technologies:

- **Python**: FastAPI + Elasticsearch examples
- **JavaScript**: Node.js client examples
- **Java**: Spring Boot integration patterns
- **Docker**: Containerized deployment strategies

## 🎓 Learning Tips

1. **Hands-on Practice**: All examples are designed to be copy-paste ready
2. **Incremental Learning**: Each section builds on previous knowledge
3. **Real-world Examples**: We use realistic data and scenarios
4. **Best Practices**: Learn the "why" behind each recommendation

## 📖 Documentation Standards

- **Practical Focus**: Every concept includes working code examples
- **Version Current**: Documentation covers Elasticsearch 9.0+ features
- **Developer-Friendly**: Clear, concise, and actionable content
- **Cross-Referenced**: Easy navigation between related topics

## 🔗 External Resources

- [Official Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Elasticsearch Python Client](https://elasticsearch-py.readthedocs.io/)
- [Kibana User Guide](https://www.elastic.co/guide/en/kibana/current/)

---

**Ready to start learning?** Choose your path above and begin your journey with Elasticsearch and Kibana!