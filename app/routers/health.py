from fastapi import APIRouter, HTTPException
from app.core.elasticsearch import check_elasticsearch_health

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check endpoint"""
    es_healthy = await check_elasticsearch_health()
    
    if not es_healthy:
        raise HTTPException(status_code=503, detail="Elasticsearch is not healthy")
    
    return {
        "status": "healthy",
        "elasticsearch": "connected"
    }


@router.get("/elasticsearch")
async def elasticsearch_health():
    """Elasticsearch-specific health check"""
    es_healthy = await check_elasticsearch_health()
    
    return {
        "elasticsearch": "healthy" if es_healthy else "unhealthy"
    }