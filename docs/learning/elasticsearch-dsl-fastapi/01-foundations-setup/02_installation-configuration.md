# Installation & Configuration

Setting up your development environment for FastAPI + Elasticsearch-DSL with modern Python tooling.

## Table of Contents
- [System Requirements](#system-requirements)
- [Python Environment Setup](#python-environment-setup)
- [Installing Dependencies](#installing-dependencies)
- [Elasticsearch Setup](#elasticsearch-setup)
- [Project Structure](#project-structure)
- [Configuration Management](#configuration-management)
- [Development Tools](#development-tools)
- [Next Steps](#next-steps)

## System Requirements

### Python Version
- **Python 3.8+** (recommended: Python 3.11+ for best async performance)
- **pip** or **uv** for package management

### System Dependencies
```bash
# macOS with Homebrew
brew install python3 docker docker-compose

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip docker.io docker-compose

# Windows with Chocolatey
choco install python docker-desktop
```

### Development Tools
- **Docker & Docker Compose** - For running Elasticsearch locally
- **Git** - Version control
- **VS Code** or **PyCharm** - IDE with Python support

## Python Environment Setup

### Using uv (Recommended)
```bash
# Install uv (modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project directory
mkdir search-api && cd search-api

# Initialize Python project with uv
uv init --python 3.11

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows
```

### Using venv (Alternative)
```bash
# Create project directory
mkdir search-api && cd search-api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows

# Upgrade pip
pip install --upgrade pip
```

## Installing Dependencies

### Core Dependencies with uv
```bash
# Add core dependencies
uv add "fastapi[all]"
uv add "elasticsearch-dsl>=8.0.0"
uv add "uvicorn[standard]"
uv add "pydantic>=2.0.0"

# Add development dependencies
uv add --dev "pytest"
uv add --dev "pytest-asyncio"
uv add --dev "httpx"  # For testing FastAPI
uv add --dev "ruff"   # Linting and formatting
uv add --dev "mypy"   # Type checking
```

### Core Dependencies with pip
```bash
# Create requirements.txt
cat > requirements.txt << EOF
fastapi[all]>=0.104.0
elasticsearch-dsl>=8.0.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6
EOF

# Create dev-requirements.txt
cat > dev-requirements.txt << EOF
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
ruff>=0.1.0
mypy>=1.6.0
EOF

# Install dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

### Project Configuration Files

**pyproject.toml** (for uv and modern Python tooling):
```toml
[project]
name = "search-api"
version = "0.1.0"
description = "FastAPI + Elasticsearch-DSL search application"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "fastapi[all]>=0.104.0",
    "elasticsearch-dsl>=8.0.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.0.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
    "ruff>=0.1.0",
    "mypy>=1.6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py38"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "ANN", "S", "B", "A", "COM", "DTZ", "EM", "ISC", "ICN", "G", "PIE", "T20", "PT", "Q", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]
ignore = ["ANN101", "ANN102", "COM812", "ISC001"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

## Elasticsearch Setup

### Using Docker Compose (Recommended)
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - elastic

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - elastic

volumes:
  elasticsearch_data:

networks:
  elastic:
    driver: bridge
```

### Start Elasticsearch
```bash
# Start services
docker-compose up -d

# Verify Elasticsearch is running
curl http://localhost:9200

# Expected response:
{
  "name" : "elasticsearch",
  "cluster_name" : "docker-cluster",
  "cluster_uuid" : "...",
  "version" : {
    "number" : "8.11.0",
    ...
  }
}

# Verify Kibana (optional)
# Open http://localhost:5601 in browser
```

### Alternative: Elasticsearch Cloud
For production or cloud development:
```python
# Configuration for Elastic Cloud
ELASTICSEARCH_CONFIG = {
    'hosts': ['https://your-deployment.es.region.aws.found.io:9243'],
    'http_auth': ('elastic', 'your-password'),
    'use_ssl': True,
    'verify_certs': True,
}
```

## Project Structure

Create a well-organized project structure:
```bash
mkdir -p app/{core,models,routers,services,utils}
mkdir -p tests/{unit,integration}
mkdir -p docs

# Create initial files
touch app/__init__.py
touch app/main.py
touch app/core/{__init__.py,config.py,database.py}
touch app/models/{__init__.py,documents.py}
touch app/routers/{__init__.py,search.py}
touch app/services/{__init__.py,search_service.py}
touch tests/__init__.py
touch tests/conftest.py
```

**Final structure:**
```
search-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── documents.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── search.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── search_service.py
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── .env
```

## Configuration Management

### Environment Configuration
Create `.env` file:
```env
# Application settings
APP_NAME="Search API"
APP_VERSION="1.0.0"
DEBUG=true

# Elasticsearch settings
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX_PREFIX=dev_

# API settings
API_V1_STR="/api/v1"
SECRET_KEY="your-secret-key-here"

# Development settings
RELOAD=true
LOG_LEVEL=debug
```

### Configuration Class
Create `app/core/config.py`:
```python
from pydantic import BaseSettings, Field
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="Search API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Elasticsearch
    elasticsearch_host: str = Field(default="localhost", env="ELASTICSEARCH_HOST")
    elasticsearch_port: int = Field(default=9200, env="ELASTICSEARCH_PORT")
    elasticsearch_index_prefix: str = Field(default="", env="ELASTICSEARCH_INDEX_PREFIX")
    
    # API
    api_v1_str: str = Field(default="/api/v1", env="API_V1_STR")
    secret_key: str = Field(env="SECRET_KEY")
    
    # Development
    reload: bool = Field(default=False, env="RELOAD")
    log_level: str = Field(default="info", env="LOG_LEVEL")
    
    @property
    def elasticsearch_url(self) -> str:
        """Construct Elasticsearch URL from components."""
        return f"http://{self.elasticsearch_host}:{self.elasticsearch_port}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

### Database Connection Setup
Create `app/core/database.py`:
```python
from elasticsearch_dsl.connections import connections
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def connect_to_elasticsearch():
    """Initialize Elasticsearch connection."""
    try:
        connections.configure(
            default={
                'hosts': [settings.elasticsearch_url],
                'timeout': 20,
                'max_retries': 3,
                'retry_on_timeout': True,
            }
        )
        
        # Test connection
        client = connections.get_connection()
        cluster_info = await client.info()
        
        logger.info(
            f"Connected to Elasticsearch cluster: {cluster_info['cluster_name']} "
            f"(version {cluster_info['version']['number']})"
        )
        
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        raise

async def close_elasticsearch_connection():
    """Close Elasticsearch connection."""
    try:
        client = connections.get_connection()
        await client.close()
        logger.info("Elasticsearch connection closed")
    except Exception as e:
        logger.error(f"Error closing Elasticsearch connection: {e}")
```

### Basic Application Setup
Create `app/main.py`:
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import connect_to_elasticsearch, close_elasticsearch_connection
from app.routers import search
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await connect_to_elasticsearch()
    yield
    # Shutdown
    await close_elasticsearch_connection()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Include routers
app.include_router(search.router, prefix=settings.api_v1_str, tags=["search"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.reload,
        log_level=settings.log_level
    )
```

## Development Tools

### Code Quality Setup
```bash
# Format code with Ruff
uv run ruff format .

# Lint code with Ruff
uv run ruff check . --fix

# Type checking with MyPy
uv run mypy app/

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=app tests/
```

### VS Code Configuration
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "ruff",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### Git Configuration
Create `.gitignore`:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
.venv/
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# Environment variables
.env
.env.local
.env.*.local

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
.pytest_cache/
htmlcov/

# MyPy
.mypy_cache/
.dmypy.json
dmypy.json
```

## Verification

### Test Installation
```bash
# Start Elasticsearch
docker-compose up -d

# Create a simple test file
cat > test_setup.py << EOF
import asyncio
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import AsyncDocument, Text

# Configure connection
connections.configure(default={'hosts': ['localhost:9200']})

class TestDoc(AsyncDocument):
    content = Text()
    
    class Index:
        name = 'test_index'

async def test_connection():
    # Test connection
    client = connections.get_connection()
    info = await client.info()
    print(f"Connected to: {info['cluster_name']}")
    
    # Test document operations
    await TestDoc.init()
    
    doc = TestDoc(content="Hello World")
    await doc.save()
    print("Document saved successfully!")
    
    # Cleanup
    await TestDoc._index.delete()
    print("Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_connection())
EOF

# Run test
uv run python test_setup.py

# Clean up test file
rm test_setup.py
```

### Run Development Server
```bash
# Start development server
uv run uvicorn app.main:app --reload

# Or use the main.py script
uv run python app/main.py

# Visit http://localhost:8000/docs for API documentation
```

## Common Issues and Solutions

### Connection Refused Error
```bash
# Ensure Elasticsearch is running
docker-compose ps

# Check Elasticsearch logs
docker-compose logs elasticsearch

# Restart if needed
docker-compose restart elasticsearch
```

### Import Errors
```bash
# Verify virtual environment is activated
which python  # Should point to .venv/bin/python

# Reinstall dependencies
uv sync --reinstall
```

### Permission Issues (Linux/macOS)
```bash
# Fix Elasticsearch data directory permissions
sudo chown -R 1000:1000 $(pwd)/docker-data/elasticsearch
```

## Next Steps

1. **[Async Patterns](03_async-patterns.md)** - Master async/await with Elasticsearch
2. **[Development Environment](04_development-environment.md)** - Configure advanced tooling and workflow

## Additional Resources

- **uv Documentation**: [docs.astral.sh/uv](https://docs.astral.sh/uv)
- **FastAPI Installation Guide**: [fastapi.tiangolo.com/tutorial](https://fastapi.tiangolo.com/tutorial)
- **Elasticsearch Docker**: [elastic.co/guide/en/elasticsearch/reference/current/docker.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)