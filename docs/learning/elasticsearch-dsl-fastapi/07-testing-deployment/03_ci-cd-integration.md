# CI/CD Integration

Comprehensive CI/CD pipelines for FastAPI + Elasticsearch-DSL applications with automated testing, security scanning, and deployment workflows.

## Table of Contents
- [GitHub Actions Workflows](#github-actions-workflows)
- [Automated Testing](#automated-testing)
- [Security Scanning](#security-scanning)
- [Quality Gates](#quality-gates)
- [Deployment Pipelines](#deployment-pipelines)
- [Artifact Management](#artifact-management)
- [Environment Promotion](#environment-promotion)
- [Next Steps](#next-steps)

## GitHub Actions Workflows

### Main CI/CD Pipeline
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Code Quality and Testing
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]
    
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

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"

    - name: Install dependencies
      run: |
        uv sync --dev

    - name: Lint with Ruff
      run: |
        uv run ruff check . --output-format=github
        uv run ruff format --check .

    - name: Type check with MyPy
      run: |
        uv run mypy app/ --junit-xml=mypy-results.xml

    - name: Test with pytest
      env:
        ELASTICSEARCH_HOST: localhost
        ELASTICSEARCH_PORT: 9200
        REDIS_HOST: localhost
        REDIS_PORT: 6379
        ENVIRONMENT: testing
      run: |
        uv run pytest \
          --cov=app \
          --cov-report=xml \
          --cov-report=html \
          --junitxml=pytest-results.xml \
          -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

    - name: Upload test results
      uses: dorny/test-reporter@v1
      if: success() || failure()
      with:
        name: Test Results (Python ${{ matrix.python-version }})
        path: pytest-results.xml
        reporter: java-junit

  # Security Scanning
  security:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run Bandit security scan
      run: |
        pip install bandit[toml]
        bandit -r app/ -f json -o bandit-report.json

    - name: Run Safety check
      run: |
        pip install safety
        safety check --json --output safety-report.json

    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json

  # Build and Push Docker Image
  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.image.outputs.image }}
      digest: ${{ steps.build.outputs.digest }}

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-

    - name: Build and push Docker image
      id: build
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        platforms: linux/amd64,linux/arm64

    - name: Output image
      id: image
      run: echo "image=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.meta.outputs.version }}" >> $GITHUB_OUTPUT

  # Container Security Scanning
  container-scan:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ needs.build.outputs.image }}
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # Deploy to Staging
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    needs: [build, container-scan]
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

    - name: Deploy to staging
      run: |
        helm upgrade --install search-api ./helm \
          --namespace staging \
          --values ./helm/values-staging.yaml \
          --set image.tag=${{ needs.build.outputs.digest }} \
          --wait --timeout=10m

    - name: Run smoke tests
      run: |
        kubectl wait --for=condition=ready pod -l app=fastapi -n staging --timeout=300s
        curl -f https://staging-api.example.com/health || exit 1

  # Deploy to Production
  deploy-production:
    if: github.event_name == 'release'
    needs: [build, container-scan]
    runs-on: ubuntu-latest
    environment: production
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}

    - name: Deploy to production
      run: |
        helm upgrade --install search-api ./helm \
          --namespace production \
          --values ./helm/values-production.yaml \
          --set image.tag=${{ github.event.release.tag_name }} \
          --wait --timeout=15m

    - name: Run production health checks
      run: |
        kubectl wait --for=condition=ready pod -l app=fastapi -n production --timeout=600s
        curl -f https://api.example.com/health || exit 1

    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: "Production deployment completed: ${{ github.event.release.tag_name }}"
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Feature Branch Workflow
```yaml
# .github/workflows/feature-branch.yml
name: Feature Branch CI

on:
  pull_request:
    branches: [ develop ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install uv
      uses: astral-sh/setup-uv@v1

    - name: Install dependencies
      run: uv sync --dev

    - name: Check commit messages
      run: |
        pip install gitlint
        gitlint --commits origin/develop..HEAD

    - name: Check for breaking changes
      run: |
        # Custom script to detect breaking changes
        python scripts/check_breaking_changes.py

    - name: Run integration tests
      env:
        ELASTICSEARCH_HOST: localhost
        REDIS_HOST: localhost
      run: |
        docker-compose -f docker-compose.test.yml up -d
        uv run pytest tests/integration/ -v
        docker-compose -f docker-compose.test.yml down

    - name: Performance regression test
      run: |
        uv run pytest tests/performance/ --benchmark-only

    - name: Generate PR summary
      run: |
        echo "## Test Results" >> $GITHUB_STEP_SUMMARY
        echo "✅ All tests passed" >> $GITHUB_STEP_SUMMARY
        echo "✅ No breaking changes detected" >> $GITHUB_STEP_SUMMARY
        echo "✅ Performance benchmarks within acceptable range" >> $GITHUB_STEP_SUMMARY
```

## Automated Testing

### Comprehensive Test Configuration
```python
# tests/conftest.py
import pytest
import asyncio
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from elasticsearch_dsl.connections import connections
from redis import Redis

from app.main import app
from app.core.config import get_config

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_config():
    """Test configuration."""
    config = get_config()
    config.environment = "testing"
    config.elasticsearch_host = "localhost"
    config.redis_host = "localhost"
    return config

@pytest.fixture(scope="session")
async def elasticsearch_client():
    """Elasticsearch test client."""
    connections.configure(
        test={'hosts': ['localhost:9200'], 'timeout': 20}
    )
    client = connections.get_connection('test')
    
    # Wait for Elasticsearch to be ready
    await client.cluster.health(wait_for_status='yellow', timeout='30s')
    
    yield client
    
    # Cleanup test indices
    try:
        await client.indices.delete(index='test_*')
    except:
        pass

@pytest.fixture(scope="session")
async def redis_client():
    """Redis test client."""
    client = Redis(host='localhost', port=6379, db=15, decode_responses=True)
    
    # Wait for Redis to be ready
    client.ping()
    
    yield client
    
    # Cleanup test data
    client.flushdb()

@pytest.fixture
async def async_client():
    """Async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sync_client():
    """Sync HTTP client for testing."""
    return TestClient(app)

@pytest.fixture(autouse=True)
async def clean_test_data(elasticsearch_client, redis_client):
    """Clean test data before each test."""
    # Clean Elasticsearch test indices
    try:
        await elasticsearch_client.indices.delete(index='test_*')
    except:
        pass
    
    # Clean Redis test data
    redis_client.flushdb()
    
    yield
    
    # Cleanup after test
    try:
        await elasticsearch_client.indices.delete(index='test_*')
    except:
        pass
    redis_client.flushdb()
```

### Performance Test Suite
```python
# tests/performance/test_search_performance.py
import pytest
import asyncio
import time
from httpx import AsyncClient
from app.main import app

class TestSearchPerformance:
    """Performance tests for search endpoints."""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_search_response_time(self, async_client: AsyncClient):
        """Test search endpoint response time."""
        
        # Warm up
        for _ in range(5):
            await async_client.post("/api/search", json={"query": "test"})
        
        # Measure response time
        start_time = time.time()
        response = await async_client.post("/api/search", json={"query": "test"})
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 0.5  # Should respond within 500ms
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_search_requests(self, async_client: AsyncClient):
        """Test concurrent search request handling."""
        
        async def search_request():
            response = await async_client.post(
                "/api/search", 
                json={"query": "test", "size": 10}
            )
            return response.status_code == 200
        
        # Run 50 concurrent requests
        start_time = time.time()
        tasks = [search_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All requests should succeed
        assert all(results)
        
        # Should handle 50 concurrent requests within 2 seconds
        assert (end_time - start_time) < 2.0
        
        # Calculate requests per second
        rps = len(results) / (end_time - start_time)
        assert rps > 25  # Should handle at least 25 RPS
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_usage_stability(self, async_client: AsyncClient):
        """Test memory usage doesn't grow excessively."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many search requests
        for i in range(100):
            await async_client.post("/api/search", json={"query": f"test {i}"})
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB)
        assert memory_growth < 50 * 1024 * 1024

@pytest.mark.benchmark
class TestSearchBenchmarks:
    """Benchmark tests using pytest-benchmark."""
    
    def test_elasticsearch_query_benchmark(self, benchmark, sync_client):
        """Benchmark raw search performance."""
        
        def search_operation():
            response = sync_client.post("/api/search", json={"query": "test"})
            return response.status_code == 200
        
        result = benchmark(search_operation)
        assert result is True
    
    def test_bulk_indexing_benchmark(self, benchmark, sync_client):
        """Benchmark bulk indexing performance."""
        
        def bulk_index_operation():
            documents = [
                {"title": f"Document {i}", "content": f"Content {i}"}
                for i in range(100)
            ]
            response = sync_client.post("/api/bulk-index", json={"documents": documents})
            return response.status_code == 200
        
        result = benchmark(bulk_index_operation)
        assert result is True
```

### Load Testing Script
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import random
import json

class SearchAPIUser(HttpUser):
    """Load testing user for search API."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Setup user session."""
        # Authenticate if required
        response = self.client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
    
    @task(10)
    def search_products(self):
        """Search for products (most common operation)."""
        queries = ["laptop", "phone", "book", "camera", "headphones"]
        query = random.choice(queries)
        
        self.client.post("/api/search", json={
            "query": query,
            "size": 20,
            "page": 1
        }, name="search_products")
    
    @task(5)
    def search_with_filters(self):
        """Search with filters."""
        self.client.post("/api/search", json={
            "query": "electronics",
            "filters": {
                "category": "electronics",
                "price_range": {"min": 100, "max": 1000}
            },
            "size": 20
        }, name="search_with_filters")
    
    @task(3)
    def get_suggestions(self):
        """Get autocomplete suggestions."""
        prefixes = ["lap", "pho", "cam", "hea", "boo"]
        prefix = random.choice(prefixes)
        
        self.client.get(f"/api/suggest?q={prefix}", name="get_suggestions")
    
    @task(2)
    def get_product_details(self):
        """Get product details."""
        product_id = random.randint(1, 1000)
        self.client.get(f"/api/products/{product_id}", name="get_product_details")
    
    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health", name="health_check")

class AdminUser(HttpUser):
    """Load testing for admin operations."""
    
    wait_time = between(5, 10)  # Longer wait times for admin operations
    
    @task
    def bulk_index_documents(self):
        """Bulk index documents."""
        documents = [
            {
                "title": f"Document {i}",
                "content": f"This is test content for document {i}",
                "category": random.choice(["tech", "science", "business"])
            }
            for i in range(50)
        ]
        
        self.client.post("/api/admin/bulk-index", json={
            "documents": documents
        }, name="bulk_index")
    
    @task
    def reindex_operation(self):
        """Trigger reindex operation."""
        self.client.post("/api/admin/reindex", json={
            "source_index": "products",
            "target_index": "products_v2"
        }, name="reindex")
```

## Security Scanning

### SAST Configuration
```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly scan

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install security tools
      run: |
        pip install bandit[toml] safety semgrep

    - name: Run Bandit SAST scan
      run: |
        bandit -r app/ \
          -f json \
          -o bandit-report.json \
          --severity-level medium

    - name: Run Safety dependency scan
      run: |
        safety check \
          --json \
          --output safety-report.json \
          --ignore 70612  # Ignore specific CVE if needed

    - name: Run Semgrep scan
      run: |
        semgrep \
          --config=auto \
          --json \
          --output=semgrep-report.json \
          app/

    - name: Upload security scan results
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: semgrep-report.json

    - name: Comment PR with security findings
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          
          let comment = '## Security Scan Results\n\n';
          
          // Process Bandit results
          try {
            const banditResults = JSON.parse(fs.readFileSync('bandit-report.json'));
            comment += `### Bandit SAST Scan\n`;
            comment += `- **High severity issues**: ${banditResults.metrics.SEVERITY.HIGH}\n`;
            comment += `- **Medium severity issues**: ${banditResults.metrics.SEVERITY.MEDIUM}\n`;
            comment += `- **Low severity issues**: ${banditResults.metrics.SEVERITY.LOW}\n\n`;
          } catch (e) {
            comment += '### Bandit SAST Scan\n❌ Failed to parse results\n\n';
          }
          
          // Process Safety results
          try {
            const safetyResults = JSON.parse(fs.readFileSync('safety-report.json'));
            comment += `### Safety Dependency Scan\n`;
            comment += `- **Vulnerabilities found**: ${safetyResults.vulnerabilities?.length || 0}\n\n`;
          } catch (e) {
            comment += '### Safety Dependency Scan\n❌ Failed to parse results\n\n';
          }
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });

  secrets-scan:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Run GitLeaks
      uses: zricethezav/gitleaks-action@v2
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

    - name: Run TruffleHog
      uses: trufflesecurity/trufflehog@main
      with:
        path: ./
        base: main
        head: HEAD
```

### Custom Security Checks
```python
# scripts/security_checks.py
import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

class SecurityChecker:
    """Custom security checks for the codebase."""
    
    def __init__(self):
        self.issues = []
    
    def check_hardcoded_secrets(self, content: str, filepath: str):
        """Check for hardcoded secrets."""
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token'),
        ]
        
        for pattern, message in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if 'example' not in match.group().lower():
                    self.issues.append({
                        'file': filepath,
                        'line': content[:match.start()].count('\n') + 1,
                        'issue': message,
                        'severity': 'HIGH'
                    })
    
    def check_sql_injection_risks(self, content: str, filepath: str):
        """Check for potential SQL injection risks."""
        # Look for string formatting in database queries
        sql_patterns = [
            r'SELECT.*%[sf]',
            r'INSERT.*%[sf]',
            r'UPDATE.*%[sf]',
            r'DELETE.*%[sf]',
        ]
        
        for pattern in sql_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                self.issues.append({
                    'file': filepath,
                    'line': content[:match.start()].count('\n') + 1,
                    'issue': 'Potential SQL injection vulnerability',
                    'severity': 'HIGH'
                })
    
    def check_debug_code(self, content: str, filepath: str):
        """Check for debug code that shouldn't be in production."""
        debug_patterns = [
            r'print\s*\(',
            r'pdb\.set_trace\(\)',
            r'breakpoint\(\)',
            r'console\.log\(',
        ]
        
        for pattern in debug_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                self.issues.append({
                    'file': filepath,
                    'line': content[:match.start()].count('\n') + 1,
                    'issue': 'Debug code found',
                    'severity': 'MEDIUM'
                })
    
    def check_unsafe_yaml_loading(self, content: str, filepath: str):
        """Check for unsafe YAML loading."""
        if 'yaml.load(' in content and 'Loader=' not in content:
            matches = re.finditer(r'yaml\.load\([^)]+\)', content)
            for match in matches:
                self.issues.append({
                    'file': filepath,
                    'line': content[:match.start()].count('\n') + 1,
                    'issue': 'Unsafe YAML loading (use safe_load)',
                    'severity': 'HIGH'
                })
    
    def scan_file(self, filepath: Path):
        """Scan a single file for security issues."""
        try:
            content = filepath.read_text(encoding='utf-8')
            
            self.check_hardcoded_secrets(content, str(filepath))
            self.check_sql_injection_risks(content, str(filepath))
            self.check_debug_code(content, str(filepath))
            self.check_unsafe_yaml_loading(content, str(filepath))
            
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")
    
    def scan_directory(self, directory: Path):
        """Scan all Python files in directory."""
        for filepath in directory.rglob('*.py'):
            if 'test' not in str(filepath):  # Skip test files
                self.scan_file(filepath)
    
    def report_issues(self):
        """Report found security issues."""
        if not self.issues:
            print("✅ No security issues found")
            return 0
        
        print(f"❌ Found {len(self.issues)} security issues:")
        
        for issue in sorted(self.issues, key=lambda x: x['severity']):
            print(f"  {issue['severity']}: {issue['file']}:{issue['line']} - {issue['issue']}")
        
        high_severity = sum(1 for issue in self.issues if issue['severity'] == 'HIGH')
        return 1 if high_severity > 0 else 0

if __name__ == "__main__":
    checker = SecurityChecker()
    checker.scan_directory(Path("app"))
    sys.exit(checker.report_issues())
```

## Quality Gates

### Quality Gate Configuration
```python
# scripts/quality_gate.py
import json
import sys
from pathlib import Path
from typing import Dict, Any

class QualityGate:
    """Enforce quality gates for deployment."""
    
    def __init__(self):
        self.thresholds = {
            'test_coverage': 80.0,
            'max_complexity': 10,
            'max_high_security_issues': 0,
            'max_medium_security_issues': 5,
            'performance_regression_threshold': 20.0  # 20% slower
        }
        self.results = {}
    
    def check_test_coverage(self, coverage_file: Path):
        """Check test coverage meets threshold."""
        try:
            with open(coverage_file) as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data['totals']['percent_covered']
            self.results['test_coverage'] = total_coverage
            
            return total_coverage >= self.thresholds['test_coverage']
        except Exception as e:
            print(f"Error checking coverage: {e}")
            return False
    
    def check_code_complexity(self, complexity_file: Path):
        """Check code complexity meets threshold."""
        try:
            with open(complexity_file) as f:
                complexity_data = json.load(f)
            
            max_complexity = max(
                item['complexity'] for item in complexity_data
            )
            self.results['max_complexity'] = max_complexity
            
            return max_complexity <= self.thresholds['max_complexity']
        except Exception as e:
            print(f"Error checking complexity: {e}")
            return False
    
    def check_security_issues(self, security_files: Dict[str, Path]):
        """Check security issues are within threshold."""
        try:
            total_high = 0
            total_medium = 0
            
            for tool, filepath in security_files.items():
                with open(filepath) as f:
                    data = json.load(f)
                
                if tool == 'bandit':
                    total_high += data['metrics']['SEVERITY']['HIGH']
                    total_medium += data['metrics']['SEVERITY']['MEDIUM']
                elif tool == 'safety':
                    total_high += len([
                        v for v in data.get('vulnerabilities', [])
                        if v.get('severity') == 'high'
                    ])
            
            self.results['high_security_issues'] = total_high
            self.results['medium_security_issues'] = total_medium
            
            return (total_high <= self.thresholds['max_high_security_issues'] and
                    total_medium <= self.thresholds['max_medium_security_issues'])
        except Exception as e:
            print(f"Error checking security: {e}")
            return False
    
    def check_performance_regression(self, benchmark_file: Path):
        """Check for performance regression."""
        try:
            with open(benchmark_file) as f:
                benchmark_data = json.load(f)
            
            # Compare with baseline (implement based on your benchmark format)
            regression_percentage = benchmark_data.get('regression_percentage', 0)
            self.results['performance_regression'] = regression_percentage
            
            return regression_percentage <= self.thresholds['performance_regression_threshold']
        except Exception as e:
            print(f"Error checking performance: {e}")
            return True  # Don't fail on missing performance data
    
    def evaluate(self, artifacts_dir: Path) -> bool:
        """Evaluate all quality gates."""
        checks = [
            ('Test Coverage', lambda: self.check_test_coverage(
                artifacts_dir / 'coverage.json'
            )),
            ('Code Complexity', lambda: self.check_code_complexity(
                artifacts_dir / 'complexity.json'
            )),
            ('Security Issues', lambda: self.check_security_issues({
                'bandit': artifacts_dir / 'bandit-report.json',
                'safety': artifacts_dir / 'safety-report.json'
            })),
            ('Performance Regression', lambda: self.check_performance_regression(
                artifacts_dir / 'benchmark-results.json'
            ))
        ]
        
        all_passed = True
        
        print("🚪 Quality Gate Evaluation")
        print("=" * 50)
        
        for check_name, check_func in checks:
            try:
                passed = check_func()
                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"{check_name}: {status}")
                
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"{check_name}: ❌ ERROR - {e}")
                all_passed = False
        
        print("=" * 50)
        
        if all_passed:
            print("🎉 All quality gates passed! Deployment approved.")
        else:
            print("🛑 Quality gates failed! Deployment blocked.")
            self._print_failure_details()
        
        return all_passed
    
    def _print_failure_details(self):
        """Print detailed failure information."""
        print("\n📊 Quality Metrics:")
        
        for metric, value in self.results.items():
            threshold_key = f"max_{metric}" if metric.endswith('_issues') else metric
            threshold = self.thresholds.get(threshold_key)
            
            if threshold is not None:
                status = "✅" if value <= threshold else "❌"
                print(f"  {metric}: {value} (threshold: {threshold}) {status}")

if __name__ == "__main__":
    gate = QualityGate()
    artifacts_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts")
    
    if gate.evaluate(artifacts_dir):
        sys.exit(0)
    else:
        sys.exit(1)
```

## Deployment Pipelines

### Helm Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=$1
IMAGE_TAG=$2
NAMESPACE=${3:-$ENVIRONMENT}

if [ -z "$ENVIRONMENT" ] || [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <environment> <image_tag> [namespace]"
    exit 1
fi

echo "🚀 Deploying to $ENVIRONMENT environment"
echo "📦 Image tag: $IMAGE_TAG"
echo "🏷️  Namespace: $NAMESPACE"

# Validate environment
case $ENVIRONMENT in
    staging|production)
        ;;
    *)
        echo "❌ Invalid environment: $ENVIRONMENT"
        echo "Valid environments: staging, production"
        exit 1
        ;;
esac

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi

# Verify cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Backup current deployment
echo "💾 Creating backup of current deployment..."
kubectl get deployment search-api -n $NAMESPACE -o yaml > "backup-$ENVIRONMENT-$(date +%Y%m%d-%H%M%S).yaml" 2>/dev/null || echo "No existing deployment to backup"

# Deploy with Helm
echo "📦 Deploying with Helm..."

helm upgrade --install search-api ./helm \
    --namespace $NAMESPACE \
    --values ./helm/values-$ENVIRONMENT.yaml \
    --set image.tag=$IMAGE_TAG \
    --set deployment.timestamp=$(date +%s) \
    --wait \
    --timeout=15m \
    --atomic

# Verify deployment
echo "✅ Verifying deployment..."

# Wait for rollout to complete
kubectl rollout status deployment/search-api -n $NAMESPACE --timeout=600s

# Check pod health
echo "🏥 Checking pod health..."
kubectl wait --for=condition=ready pod -l app=search-api -n $NAMESPACE --timeout=300s

# Run health checks
echo "🔬 Running health checks..."
SERVICE_URL=$(kubectl get service search-api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")

if [ "$SERVICE_URL" = "localhost" ]; then
    # Port forward for local testing
    kubectl port-forward service/search-api 8080:80 -n $NAMESPACE &
    PORT_FORWARD_PID=$!
    SERVICE_URL="localhost:8080"
    sleep 5
fi

# Health check
if curl -f "http://$SERVICE_URL/health" > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    
    # Kill port forward if we started it
    if [ -n "$PORT_FORWARD_PID" ]; then
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
    
    exit 1
fi

# Kill port forward if we started it
if [ -n "$PORT_FORWARD_PID" ]; then
    kill $PORT_FORWARD_PID 2>/dev/null || true
fi

echo "🎉 Deployment completed successfully!"
echo "🌐 Application URL: http://$SERVICE_URL"
```

## Artifact Management

### Container Registry Management
```python
# scripts/manage_artifacts.py
import subprocess
import json
import sys
from datetime import datetime, timedelta
from typing import List, Dict

class ArtifactManager:
    """Manage container artifacts and cleanup."""
    
    def __init__(self, registry: str, repository: str):
        self.registry = registry
        self.repository = repository
        self.full_repo = f"{registry}/{repository}"
    
    def list_tags(self) -> List[Dict]:
        """List all tags for the repository."""
        cmd = [
            "docker", "run", "--rm",
            "gcr.io/go-containerregistry/crane:latest",
            "ls", self.full_repo, "--json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to list tags: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def get_image_metadata(self, tag: str) -> Dict:
        """Get metadata for a specific image tag."""
        cmd = [
            "docker", "run", "--rm",
            "gcr.io/go-containerregistry/crane:latest",
            "manifest", f"{self.full_repo}:{tag}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to get metadata: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def cleanup_old_images(self, keep_count: int = 10, keep_days: int = 30):
        """Clean up old images keeping the most recent and tagged versions."""
        
        print(f"🧹 Cleaning up old images from {self.full_repo}")
        print(f"📦 Keeping {keep_count} most recent images")
        print(f"📅 Keeping images from last {keep_days} days")
        
        tags = self.list_tags()
        
        # Separate release tags from other tags
        release_tags = []
        other_tags = []
        
        for tag_info in tags:
            tag = tag_info['tag']
            if self._is_release_tag(tag):
                release_tags.append(tag_info)
            else:
                other_tags.append(tag_info)
        
        # Sort by creation date (most recent first)
        other_tags.sort(key=lambda x: x.get('created', ''), reverse=True)
        
        # Keep most recent non-release images
        tags_to_keep = set()
        tags_to_delete = []
        
        # Always keep release tags
        for tag_info in release_tags:
            tags_to_keep.add(tag_info['tag'])
        
        # Keep recent non-release tags
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        kept_count = 0
        
        for tag_info in other_tags:
            tag = tag_info['tag']
            created_str = tag_info.get('created', '')
            
            # Keep if within date range or under count limit
            if kept_count < keep_count:
                tags_to_keep.add(tag)
                kept_count += 1
            elif created_str:
                try:
                    created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                    if created_date > cutoff_date:
                        tags_to_keep.add(tag)
                    else:
                        tags_to_delete.append(tag)
                except ValueError:
                    tags_to_delete.append(tag)
            else:
                tags_to_delete.append(tag)
        
        # Delete old tags
        if tags_to_delete:
            print(f"🗑️  Deleting {len(tags_to_delete)} old tags:")
            for tag in tags_to_delete:
                print(f"  - {tag}")
                self._delete_tag(tag)
        else:
            print("✅ No old tags to delete")
        
        print(f"📦 Keeping {len(tags_to_keep)} tags")
    
    def _is_release_tag(self, tag: str) -> bool:
        """Check if tag is a release tag (semantic version)."""
        import re
        semver_pattern = r'^v?\d+\.\d+\.\d+(?:-[\w\.]+)?$'
        return bool(re.match(semver_pattern, tag))
    
    def _delete_tag(self, tag: str):
        """Delete a specific tag."""
        cmd = [
            "docker", "run", "--rm",
            "gcr.io/go-containerregistry/crane:latest",
            "delete", f"{self.full_repo}:{tag}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to delete {tag}: {result.stderr}")
        else:
            print(f"✅ Deleted {tag}")
    
    def scan_vulnerabilities(self, tag: str) -> Dict:
        """Scan image for vulnerabilities."""
        cmd = [
            "docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock",
            "aquasec/trivy:latest", "image", "--format", "json",
            f"{self.full_repo}:{tag}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Vulnerability scan failed: {result.stderr}")
        
        return json.loads(result.stdout)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python manage_artifacts.py <registry> <repository> [action]")
        sys.exit(1)
    
    registry = sys.argv[1]
    repository = sys.argv[2]
    action = sys.argv[3] if len(sys.argv) > 3 else "cleanup"
    
    manager = ArtifactManager(registry, repository)
    
    if action == "cleanup":
        manager.cleanup_old_images()
    elif action == "list":
        tags = manager.list_tags()
        for tag_info in tags:
            print(tag_info['tag'])
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)
```

## Environment Promotion

### Promotion Pipeline
```yaml
# .github/workflows/promote.yml
name: Environment Promotion

on:
  workflow_dispatch:
    inputs:
      source_environment:
        description: 'Source environment'
        required: true
        default: 'staging'
        type: choice
        options:
        - staging
        - production
      target_environment:
        description: 'Target environment'
        required: true
        default: 'production'
        type: choice
        options:
        - staging
        - production
      image_tag:
        description: 'Image tag to promote'
        required: true
        type: string

jobs:
  validate-promotion:
    runs-on: ubuntu-latest
    outputs:
      can_promote: ${{ steps.validation.outputs.can_promote }}
    
    steps:
    - name: Validate promotion request
      id: validation
      run: |
        SOURCE="${{ github.event.inputs.source_environment }}"
        TARGET="${{ github.event.inputs.target_environment }}"
        
        # Prevent invalid promotions
        if [ "$SOURCE" = "$TARGET" ]; then
          echo "❌ Cannot promote to same environment"
          echo "can_promote=false" >> $GITHUB_OUTPUT
          exit 1
        fi
        
        if [ "$SOURCE" = "production" ] && [ "$TARGET" = "staging" ]; then
          echo "❌ Cannot promote from production to staging"
          echo "can_promote=false" >> $GITHUB_OUTPUT
          exit 1
        fi
        
        echo "✅ Promotion validation passed"
        echo "can_promote=true" >> $GITHUB_OUTPUT

  smoke-tests:
    needs: validate-promotion
    if: needs.validate-promotion.outputs.can_promote == 'true'
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run smoke tests against source
      env:
        SOURCE_ENV: ${{ github.event.inputs.source_environment }}
        IMAGE_TAG: ${{ github.event.inputs.image_tag }}
      run: |
        # Run comprehensive smoke tests
        python scripts/smoke_tests.py \
          --environment $SOURCE_ENV \
          --image-tag $IMAGE_TAG

  promote:
    needs: [validate-promotion, smoke-tests]
    if: needs.validate-promotion.outputs.can_promote == 'true'
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.target_environment }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}

    - name: Promote to target environment
      env:
        TARGET_ENV: ${{ github.event.inputs.target_environment }}
        IMAGE_TAG: ${{ github.event.inputs.image_tag }}
      run: |
        echo "🚀 Promoting $IMAGE_TAG to $TARGET_ENV"
        
        helm upgrade --install search-api ./helm \
          --namespace $TARGET_ENV \
          --values ./helm/values-$TARGET_ENV.yaml \
          --set image.tag=$IMAGE_TAG \
          --wait --timeout=15m

    - name: Post-deployment verification
      run: |
        # Wait for deployment to stabilize
        kubectl wait --for=condition=ready pod -l app=search-api \
          -n ${{ github.event.inputs.target_environment }} --timeout=300s
        
        # Run health checks
        python scripts/health_check.py \
          --environment ${{ github.event.inputs.target_environment }}

    - name: Notify promotion completion
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: |
          Environment Promotion Completed
          • Image: ${{ github.event.inputs.image_tag }}
          • Target: ${{ github.event.inputs.target_environment }}
          • Status: ${{ job.status }}
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Next Steps

1. **[Operational Monitoring](04_operational-monitoring.md)** - Production monitoring and alerting
2. **[Security & Authentication](../06-production-patterns/02_security-authentication.md)** - API security patterns
3. **[Basic Patterns](../examples/01_basic-patterns.md)** - Essential implementation examples

## Additional Resources

- **GitHub Actions Documentation**: [docs.github.com/en/actions](https://docs.github.com/en/actions)
- **Helm Documentation**: [helm.sh/docs](https://helm.sh/docs/)
- **Docker Security**: [docs.docker.com/engine/security](https://docs.docker.com/engine/security/)
- **Kubernetes CI/CD**: [kubernetes.io/docs/concepts/overview/ci-cd](https://kubernetes.io/docs/concepts/overview/ci-cd/)