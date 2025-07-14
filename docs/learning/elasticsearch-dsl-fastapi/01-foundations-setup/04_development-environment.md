# Development Environment

Configuring advanced tooling, testing, and workflow for FastAPI + Elasticsearch-DSL development.

## Table of Contents
- [IDE Configuration](#ide-configuration)
- [Testing Environment](#testing-environment)
- [Docker Development](#docker-development)
- [Code Quality Tools](#code-quality-tools)
- [Debugging and Profiling](#debugging-and-profiling)
- [Development Workflow](#development-workflow)
- [CI/CD Integration](#cicd-integration)
- [Next Steps](#next-steps)

## IDE Configuration

### VS Code Setup
Install essential extensions and configure optimal settings for FastAPI + Elasticsearch development.

**Essential Extensions:**
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "ms-python.mypy-type-checker",
    "ms-vscode.vscode-json",
    "yzhang.markdown-all-in-one",
    "ms-vscode.test-adapter-converter",
    "littlefoxteam.vscode-python-test-adapter",
    "ms-azuretools.vscode-docker"
  ]
}
```

**Workspace Settings (`.vscode/settings.json`):**
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  
  // Linting and Formatting
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "ruff.args": ["--config", "pyproject.toml"],
  
  // Type Checking
  "python.analysis.typeCheckingMode": "strict",
  "mypy-type-checker.args": ["--config-file", "pyproject.toml"],
  
  // Testing
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests",
    "--verbose",
    "--tb=short"
  ],
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  
  // Editor Settings
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true,
      "source.fixAll.ruff": true
    },
    "editor.rulers": [88],
    "editor.tabSize": 4
  },
  
  // File Associations
  "files.associations": {
    "*.env*": "dotenv",
    "docker-compose*.yml": "dockercompose"
  },
  
  // Search Exclusions
  "search.exclude": {
    "**/.venv": true,
    "**/node_modules": true,
    "**/.pytest_cache": true,
    "**/__pycache__": true,
    "**/.mypy_cache": true
  }
}
```

**Debug Configuration (`.vscode/launch.json`):**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/app/main.py",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "DEBUG": "true"
      },
      "args": []
    },
    {
      "name": "FastAPI with Uvicorn",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "DEBUG": "true"
      }
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests",
        "-v",
        "--tb=short"
      ],
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

### PyCharm Configuration
**Run Configurations:**
1. **FastAPI Server:**
   - Script path: `app/main.py`
   - Environment variables: `DEBUG=true;PYTHONPATH=.`
   - Working directory: Project root

2. **Uvicorn Server:**
   - Module name: `uvicorn`
   - Parameters: `app.main:app --reload --host 0.0.0.0 --port 8000`

**External Tools for Ruff:**
```
Name: Ruff Format
Program: uv
Arguments: run ruff format $FilePath$
Working directory: $ProjectFileDir$

Name: Ruff Check
Program: uv
Arguments: run ruff check $FilePath$ --fix
Working directory: $ProjectFileDir$
```

## Testing Environment

### Pytest Configuration
Create comprehensive testing setup with async support and Elasticsearch testing.

**pytest.ini:**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test* *Tests
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    -ra
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    elasticsearch: Tests requiring Elasticsearch
    api: API endpoint tests
asyncio_mode = auto
```

**Conftest for Test Setup (`tests/conftest.py`):**
```python
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import AsyncDocument, Text

from app.main import app
from app.core.config import settings

# Test document for isolated testing
class TestDocument(AsyncDocument):
    content = Text()
    
    class Index:
        name = 'test_documents'

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def elasticsearch_client():
    """Setup test Elasticsearch connection."""
    # Configure test connection
    connections.configure(
        test={
            'hosts': [f"http://{settings.elasticsearch_host}:{settings.elasticsearch_port}"],
            'timeout': 20
        }
    )
    
    client = connections.get_connection('test')
    
    # Verify connection
    await client.ping()
    
    yield client
    
    # Cleanup
    await client.close()

@pytest.fixture
async def clean_elasticsearch(elasticsearch_client):
    """Clean test indices before and after tests."""
    # Setup: Delete any existing test indices
    try:
        await elasticsearch_client.indices.delete(index='test_*')
    except:
        pass
    
    yield
    
    # Teardown: Clean up test indices
    try:
        await elasticsearch_client.indices.delete(index='test_*')
    except:
        pass

@pytest.fixture
async def test_document_index(clean_elasticsearch):
    """Create test document index."""
    await TestDocument.init(using='test')
    yield
    await TestDocument._index.delete(using='test')

@pytest.fixture
def client():
    """Synchronous test client for simple tests."""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async test client for advanced testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def sample_documents(test_document_index):
    """Create sample test documents."""
    documents = [
        TestDocument(content="Python programming guide"),
        TestDocument(content="FastAPI development tutorial"),
        TestDocument(content="Elasticsearch search engine")
    ]
    
    for doc in documents:
        await doc.save(using='test')
    
    # Refresh index to make documents searchable
    await TestDocument._index.refresh(using='test')
    
    return documents
```

### Unit Tests Example
```python
# tests/unit/test_search_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.search_service import SearchService

@pytest.mark.unit
class TestSearchService:
    
    @pytest.fixture
    def search_service(self):
        return SearchService()
    
    async def test_search_posts_basic_query(self, search_service):
        """Test basic search functionality."""
        with patch('app.services.search_service.AsyncSearch') as mock_search:
            # Setup mock
            mock_response = AsyncMock()
            mock_response.hits.total.value = 2
            mock_response.hits = [
                type('Hit', (), {'meta': type('Meta', (), {'id': '1', 'score': 1.0}), 
                               'title': 'Test Post 1'}),
                type('Hit', (), {'meta': type('Meta', (), {'id': '2', 'score': 0.8}), 
                               'title': 'Test Post 2'})
            ]
            
            mock_search_instance = AsyncMock()
            mock_search_instance.query.return_value = mock_search_instance
            mock_search_instance.execute.return_value = mock_response
            mock_search.return_value = mock_search_instance
            
            # Execute
            result = await search_service.search_posts("test query")
            
            # Verify
            assert result['total'] == 2
            assert len(result['posts']) == 2
            assert result['posts'][0]['title'] == 'Test Post 1'
            
            # Verify mock calls
            mock_search_instance.query.assert_called_once_with('match', title='test query')
            mock_search_instance.execute.assert_called_once()
```

### Integration Tests Example
```python
# tests/integration/test_search_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.elasticsearch
class TestSearchAPI:
    
    async def test_search_endpoint_success(self, async_client: AsyncClient, sample_documents):
        """Test search endpoint with real Elasticsearch."""
        response = await async_client.post(
            "/api/v1/search",
            json={
                "query": "Python",
                "page": 1,
                "size": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "posts" in data
        assert data["total"] > 0
        assert len(data["posts"]) > 0
        
        # Verify post structure
        post = data["posts"][0]
        assert "id" in post
        assert "title" in post
        assert "score" in post
    
    async def test_search_endpoint_no_results(self, async_client: AsyncClient, sample_documents):
        """Test search with no matching results."""
        response = await async_client.post(
            "/api/v1/search",
            json={
                "query": "nonexistent term xyz",
                "page": 1,
                "size": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert data["posts"] == []
    
    async def test_search_endpoint_validation_error(self, async_client: AsyncClient):
        """Test search endpoint with invalid input."""
        response = await async_client.post(
            "/api/v1/search",
            json={
                "query": "",  # Empty query
                "page": 0,    # Invalid page
                "size": -1    # Invalid size
            }
        )
        
        assert response.status_code == 422  # Validation error
```

## Docker Development

### Development Docker Compose
Create a comprehensive Docker setup for development with hot reloading.

**docker-compose.dev.yml:**
```yaml
version: '3.8'

services:
  # FastAPI Development Server
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
      target: development
    container_name: search_api_dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/.venv  # Exclude venv from volume mount
    environment:
      - DEBUG=true
      - RELOAD=true
      - ELASTICSEARCH_HOST=elasticsearch
      - ELASTICSEARCH_PORT=9200
    depends_on:
      elasticsearch:
        condition: service_healthy
    networks:
      - dev-network
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  # Elasticsearch for Development
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch_dev
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch_dev_data:/usr/share/elasticsearch/data
    networks:
      - dev-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Kibana for Development
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana_dev
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - XPACK_SECURITY_ENABLED=false
    ports:
      - "5601:5601"
    depends_on:
      elasticsearch:
        condition: service_healthy
    networks:
      - dev-network

  # Redis for Caching (Optional)
  redis:
    image: redis:7-alpine
    container_name: redis_dev
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    networks:
      - dev-network

volumes:
  elasticsearch_dev_data:
  redis_dev_data:

networks:
  dev-network:
    driver: bridge
```

**Dockerfile.dev:**
```dockerfile
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /app

# Development stage
FROM base as development

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with dev extras
RUN uv sync --dev

# Copy application code
COPY . .

# Development command (overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Production command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Development Scripts
Create utility scripts for common development tasks.

**scripts/dev.sh:**
```bash
#!/bin/bash
set -e

# Development utility script

case "$1" in
  "start")
    echo "Starting development environment..."
    docker-compose -f docker-compose.dev.yml up -d
    echo "Services started. API: http://localhost:8000, Kibana: http://localhost:5601"
    ;;
  
  "stop")
    echo "Stopping development environment..."
    docker-compose -f docker-compose.dev.yml down
    ;;
  
  "restart")
    echo "Restarting development environment..."
    docker-compose -f docker-compose.dev.yml restart
    ;;
  
  "logs")
    docker-compose -f docker-compose.dev.yml logs -f "${2:-api}"
    ;;
  
  "shell")
    docker-compose -f docker-compose.dev.yml exec api bash
    ;;
  
  "test")
    echo "Running tests..."
    docker-compose -f docker-compose.dev.yml exec api uv run pytest "${@:2}"
    ;;
  
  "format")
    echo "Formatting code..."
    docker-compose -f docker-compose.dev.yml exec api uv run ruff format .
    ;;
  
  "lint")
    echo "Linting code..."
    docker-compose -f docker-compose.dev.yml exec api uv run ruff check . --fix
    ;;
  
  "typecheck")
    echo "Type checking..."
    docker-compose -f docker-compose.dev.yml exec api uv run mypy app/
    ;;
  
  "clean")
    echo "Cleaning up..."
    docker-compose -f docker-compose.dev.yml down -v
    docker system prune -f
    ;;
  
  *)
    echo "Usage: $0 {start|stop|restart|logs|shell|test|format|lint|typecheck|clean}"
    echo ""
    echo "Commands:"
    echo "  start     - Start development environment"
    echo "  stop      - Stop development environment"
    echo "  restart   - Restart development environment"
    echo "  logs      - Show logs (optional service name)"
    echo "  shell     - Open shell in API container"
    echo "  test      - Run tests (pass additional pytest args)"
    echo "  format    - Format code with Ruff"
    echo "  lint      - Lint code with Ruff"
    echo "  typecheck - Type check with MyPy"
    echo "  clean     - Clean up containers and volumes"
    exit 1
    ;;
esac
```

Make the script executable:
```bash
chmod +x scripts/dev.sh
```

## Code Quality Tools

### Pre-commit Hooks
Setup automated code quality checks.

**Install pre-commit:**
```bash
uv add --dev pre-commit
```

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--config-file, pyproject.toml]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        types: [python]
        stages: [pre-push]
```

**Setup pre-commit:**
```bash
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
```

### Makefile for Common Tasks
**Makefile:**
```makefile
.PHONY: help install test lint format typecheck clean dev-start dev-stop

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync --dev

test:  ## Run tests
	uv run pytest

test-cov:  ## Run tests with coverage
	uv run pytest --cov=app --cov-report=html

lint:  ## Lint code
	uv run ruff check . --fix

format:  ## Format code
	uv run ruff format .

typecheck:  ## Type check
	uv run mypy app/

quality: format lint typecheck test  ## Run all quality checks

clean:  ## Clean cache files
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/

dev-start:  ## Start development environment
	./scripts/dev.sh start

dev-stop:  ## Stop development environment
	./scripts/dev.sh stop

dev-logs:  ## Show development logs
	./scripts/dev.sh logs

dev-shell:  ## Open shell in development container
	./scripts/dev.sh shell
```

## Debugging and Profiling

### FastAPI Debug Configuration
```python
# app/core/debug.py
import logging
import time
from fastapi import Request, Response
from typing import Callable

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Performance monitoring middleware
async def performance_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to monitor request performance."""
    start_time = time.time()
    
    # Log request
    logging.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate timing
    process_time = time.time() - start_time
    
    # Log response
    logging.info(f"Response: {response.status_code} in {process_time:.4f}s")
    
    # Add timing header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Elasticsearch query logging
class ElasticsearchLogger:
    @staticmethod
    def log_query(query_dict: dict, execution_time: float = None):
        """Log Elasticsearch queries for debugging."""
        logger = logging.getLogger("elasticsearch.query")
        logger.debug(f"Query: {query_dict}")
        if execution_time:
            logger.debug(f"Execution time: {execution_time:.4f}s")
```

### Memory and Performance Profiling
```python
# app/utils/profiling.py
import cProfile
import pstats
import io
from functools import wraps
import psutil
import os

def profile_function(func):
    """Decorator to profile function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        
        result = func(*args, **kwargs)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats()
        
        print(f"Profile for {func.__name__}:")
        print(s.getvalue())
        
        return result
    return wrapper

def memory_usage():
    """Get current memory usage."""
    process = psutil.Process(os.getpid())
    return {
        'memory_mb': process.memory_info().rss / 1024 / 1024,
        'cpu_percent': process.cpu_percent()
    }

# Usage in FastAPI endpoints
@app.middleware("http")
async def monitor_resources(request: Request, call_next):
    """Monitor resource usage per request."""
    start_memory = memory_usage()
    
    response = await call_next(request)
    
    end_memory = memory_usage()
    
    # Log resource usage
    logging.info(f"Memory usage: {end_memory['memory_mb']:.2f}MB")
    logging.info(f"CPU usage: {end_memory['cpu_percent']:.2f}%")
    
    return response
```

## Development Workflow

### Git Workflow with Hooks
**scripts/git-hooks/pre-commit:**
```bash
#!/bin/bash
# Pre-commit hook

echo "Running pre-commit checks..."

# Run code formatting
echo "Formatting code..."
uv run ruff format .

# Run linting
echo "Linting code..."
uv run ruff check . --fix

# Run type checking
echo "Type checking..."
uv run mypy app/

# Run tests
echo "Running tests..."
uv run pytest tests/unit/ -v

echo "Pre-commit checks completed!"
```

### Environment Management
```bash
# scripts/env-setup.sh
#!/bin/bash

# Environment setup script

echo "Setting up development environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher required. Found: $python_version"
    exit 1
fi

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

# Create virtual environment
echo "Creating virtual environment..."
uv venv

# Install dependencies
echo "Installing dependencies..."
uv sync --dev

# Setup pre-commit hooks
echo "Setting up pre-commit hooks..."
uv run pre-commit install

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

echo "Development environment setup complete!"
echo "Run './scripts/dev.sh start' to start the development server"
```

## CI/CD Integration

### GitHub Actions Workflow
**.github/workflows/ci.yml:**
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    services:
      elasticsearch:
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
        env:
          discovery.type: single-node
          xpack.security.enabled: false
          ES_JAVA_OPTS: -Xms512m -Xmx512m
        ports:
          - 9200:9200
        options: >-
          --health-cmd "curl -f http://localhost:9200/_cluster/health || exit 1"
          --health-interval 30s
          --health-timeout 10s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"
    
    - name: Set up Python ${{ matrix.python-version }}
      run: uv python install ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: uv sync --dev
    
    - name: Lint with Ruff
      run: uv run ruff check .
    
    - name: Format check with Ruff
      run: uv run ruff format --check .
    
    - name: Type check with MyPy
      run: uv run mypy app/
    
    - name: Test with pytest
      env:
        ELASTICSEARCH_HOST: localhost
        ELASTICSEARCH_PORT: 9200
      run: uv run pytest --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Next Steps

1. **[Document Models & Mapping](../02-elasticsearch-dsl-integration/01_document-models-mapping.md)** - Start building type-safe Elasticsearch documents
2. **[Query Builder Patterns](../03-fastapi-integration/01_query-builder-patterns.md)** - Learn advanced query construction

## Additional Resources

- **VS Code Python Tutorial**: [code.visualstudio.com/docs/python](https://code.visualstudio.com/docs/python)
- **pytest Documentation**: [docs.pytest.org](https://docs.pytest.org)
- **Docker Compose**: [docs.docker.com/compose](https://docs.docker.com/compose/)
- **Pre-commit**: [pre-commit.com](https://pre-commit.com/)