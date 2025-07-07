from elasticsearch_dsl import connections
from elasticsearch import Elasticsearch
from fastapi import HTTPException
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def init_elasticsearch():
    """Initialize Elasticsearch connection"""
    try:
        connections.create_connection(
            alias='default',
            hosts=[settings.elasticsearch_url],
            timeout=20,
            max_retries=10,
            retry_on_timeout=True
        )
        logger.info(f"Connected to Elasticsearch at {settings.elasticsearch_url}")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {e}")
        raise


def get_elasticsearch_client() -> Elasticsearch:
    """Get Elasticsearch client instance"""
    try:
        return connections.get_connection('default')
    except Exception as e:
        logger.error(f"Failed to get Elasticsearch connection: {e}")
        raise HTTPException(status_code=500, detail="Elasticsearch connection failed")


async def check_elasticsearch_health() -> bool:
    """Check if Elasticsearch is healthy"""
    try:
        client = get_elasticsearch_client()
        health = client.cluster.health()
        return health['status'] in ['green', 'yellow']
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        return False