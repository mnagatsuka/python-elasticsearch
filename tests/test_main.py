import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI Elasticsearch App is running!"}


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health/")
    # Note: This might fail if Elasticsearch is not running
    assert response.status_code in [200, 503]


def test_elasticsearch_health():
    """Test Elasticsearch health endpoint"""
    response = client.get("/health/elasticsearch")
    assert response.status_code == 200
    assert "elasticsearch" in response.json()