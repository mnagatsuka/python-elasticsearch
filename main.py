from fastapi import FastAPI
from app.core.elasticsearch import init_elasticsearch
from app.routers import documents, health

app = FastAPI(
    title="FastAPI Elasticsearch App",
    description="A FastAPI application with Elasticsearch integration",
    version="1.0.0"
)

# Initialize Elasticsearch connection
init_elasticsearch()

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])

@app.get("/")
async def root():
    return {"message": "FastAPI Elasticsearch App is running!"}