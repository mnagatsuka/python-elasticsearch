# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a FastAPI + Elasticsearch project using modern Python tooling. The stack includes:
- **FastAPI**: Web framework for building APIs
- **Elasticsearch**: Search and analytics engine
- **elasticsearch-dsl**: High-level library for Elasticsearch queries
- **Docker Compose**: Container orchestration for local development
- **uv**: Fast Python package manager
- **ruff**: Fast Python linter and formatter
- **pytest**: Testing framework

## Development Environment Setup
```bash
# Start services (Elasticsearch, Kibana, FastAPI)
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild containers
docker-compose up --build
```

## Development Commands
```bash
# Install project dependencies
uv sync

# Install with development dependencies
uv sync --dev

# Run FastAPI development server
uv run uvicorn main:app --reload

# Run tests
uv run pytest
# Run specific test
uv run pytest tests/test_specific.py::test_function_name
# Run with coverage
uv run pytest --cov=app tests/

# Lint and format code
uv run ruff check .
uv run ruff format .
# Fix auto-fixable issues
uv run ruff check --fix .

# Add new dependencies
uv add fastapi
uv add --dev pytest

# Update dependencies
uv sync --upgrade
```

## Docker Services
The project uses Docker Compose with these services:
- **Elasticsearch**: Port 9200 (LTS version)
- **Kibana**: Port 5601 (LTS version)
- **FastAPI**: Port 8000

## Architecture Notes
- Use FastAPI dependency injection for Elasticsearch client
- Implement Elasticsearch connection as a FastAPI dependency
- Use elasticsearch-dsl for query building and document modeling
- Structure the codebase with:
  - `/app`: FastAPI application code
  - `/app/models`: Elasticsearch document models using elasticsearch-dsl
  - `/app/services`: Business logic and Elasticsearch operations
  - `/app/routers`: FastAPI route handlers
  - `/tests`: Test modules

## Common Patterns
- Use elasticsearch-dsl `Document` classes for type-safe document operations
- Implement proper error handling for Elasticsearch exceptions
- Use FastAPI's dependency injection for database connections
- Implement health checks for Elasticsearch connectivity
- Use bulk operations for large dataset operations
- Leverage FastAPI's automatic OpenAPI documentation

## uv Best Practices
- Use `uv sync` to install dependencies from pyproject.toml
- Use `uv add` to add new dependencies (automatically updates pyproject.toml)
- Use `uv run` to run commands with project dependencies
- Commit uv.lock for reproducible builds
- Use `uv sync --dev` for development dependencies
- Run `uv sync --upgrade` to update all dependencies