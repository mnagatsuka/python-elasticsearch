# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a FastAPI + Elasticsearch project using modern Python tooling with uv, ruff, and pytest.

## Development Workflow

### Common Commands
```bash
# Install dependencies
uv sync --dev

# Run development server
uv run uvicorn main:app --reload

# Run tests
uv run pytest
uv run pytest tests/test_specific.py::test_function_name
uv run pytest --cov=app tests/

# Code quality
uv run ruff check --fix .
uv run ruff format .
```

### Git Commit Guidelines
Follow Conventional Commits specification:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

Example:
```
feat: add user authentication endpoint

- Implement JWT token-based authentication
- Add user registration and login endpoints
- Include password hashing with bcrypt
```

### Architecture Patterns
- Use FastAPI dependency injection for Elasticsearch client
- Implement Elasticsearch connection as a FastAPI dependency
- Use elasticsearch-dsl for query building and document modeling
- Structure code with clear separation of concerns:
  - `/app/core`: Configuration and connections
  - `/app/models`: Document models using elasticsearch-dsl
  - `/app/services`: Business logic and operations
  - `/app/routers`: API route handlers
  - `/tests`: Test modules

### Best Practices
- Use elasticsearch-dsl `Document` classes for type-safe operations
- Implement proper error handling for Elasticsearch exceptions
- Use FastAPI's dependency injection for database connections
- Implement health checks for service connectivity
- Use bulk operations for large dataset operations
- Follow FastAPI patterns for automatic OpenAPI documentation

### uv Package Management
- Use `uv sync` to install dependencies from pyproject.toml
- Use `uv add` to add new dependencies (automatically updates pyproject.toml)
- Use `uv run` to run commands with project dependencies
- Always commit uv.lock for reproducible builds
- Use `uv sync --dev` for development dependencies
- Run `uv sync --upgrade` to update all dependencies

### Testing Strategy
- Write unit tests for services and utilities
- Write integration tests for API endpoints
- Mock Elasticsearch for unit tests when appropriate
- Use fixtures for test data setup
- Maintain test coverage above 80%