# Integration Examples

Comprehensive integration patterns for FastAPI + Elasticsearch-DSL applications including authentication, monitoring, background tasks, and error handling patterns.

## Table of Contents
- [Authentication Integration Patterns](#authentication-integration-patterns)
- [Monitoring and Health Check Implementations](#monitoring-and-health-check-implementations)
- [Background Task Examples for Indexing](#background-task-examples-for-indexing)
- [Error Handling and Logging Patterns](#error-handling-and-logging-patterns)
- [Complete Application Example](#complete-application-example)
- [Testing Integration Patterns](#testing-integration-patterns)
- [Next Steps](#next-steps)

## Authentication Integration Patterns

### JWT Authentication with Role-Based Access Control
```python
# auth_integration.py - Complete authentication integration
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Date, Boolean
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import bcrypt
import asyncio
from enum import Enum

# User document model
class UserDocument(AsyncDocument):
    """User document for authentication."""
    
    username = Keyword()
    email = Keyword()
    password_hash = Text(index=False)  # Don't index password hash
    full_name = Text()
    is_active = Boolean()
    roles = Keyword(multi=True)
    created_at = Date()
    last_login = Date()
    
    # Profile information
    department = Keyword()
    permissions = Keyword(multi=True)
    
    class Index:
        name = 'users'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 1
        }

# Authentication models
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=100)
    roles: List[UserRole] = [UserRole.USER]
    department: Optional[str] = None

# Authentication service
class AuthService:
    """Authentication and authorization service."""
    
    SECRET_KEY = "your-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @classmethod
    def create_access_token(cls, data: dict) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
    
    @classmethod
    def decode_access_token(cls, token: str) -> dict:
        """Decode JWT access token."""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# Authentication dependencies
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserDocument:
    """Get current authenticated user."""
    try:
        payload = AuthService.decode_access_token(credentials.credentials)
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from Elasticsearch
        user = await UserDocument.get(username, ignore=404)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def require_role(required_roles: List[UserRole]):
    """Dependency factory for role-based access control."""
    def role_checker(current_user: UserDocument = Depends(get_current_user)):
        user_roles = set(current_user.roles)
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Authentication endpoints
app = FastAPI(title="Authenticated Search API")

@app.post("/auth/register", response_model=dict)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = await UserDocument.search().filter("term", username=user_data.username).execute()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Create new user
        user = UserDocument(
            username=user_data.username,
            email=user_data.email,
            password_hash=AuthService.hash_password(user_data.password),
            full_name=user_data.full_name,
            is_active=True,
            roles=user_data.roles,
            department=user_data.department,
            created_at=datetime.utcnow()
        )
        
        await user.save()
        
        return {"message": "User registered successfully", "username": user_data.username}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Authenticate user and return access token."""
    try:
        # Find user
        search = UserDocument.search().filter("term", username=login_data.username)
        response = await search.execute()
        
        if not response.hits:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        user = response.hits[0]
        
        # Verify password
        if not AuthService.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await user.save()
        
        # Create access token
        token_data = {
            "sub": user.username,
            "roles": user.roles,
            "user_id": user.meta.id
        }
        access_token = AuthService.create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            expires_in=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_info={
                "username": user.username,
                "full_name": user.full_name,
                "roles": user.roles,
                "department": user.department
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/auth/me", response_model=dict)
async def get_current_user_info(current_user: UserDocument = Depends(get_current_user)):
    """Get current user information."""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "roles": current_user.roles,
        "department": current_user.department,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }

# Protected endpoint example
@app.get("/admin/users")
async def list_users(
    current_user: UserDocument = Depends(require_role([UserRole.ADMIN]))
):
    """Admin-only endpoint to list all users."""
    search = UserDocument.search()
    users = await search.execute()
    
    return {
        "users": [
            {
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "roles": user.roles,
                "is_active": user.is_active,
                "created_at": user.created_at
            }
            for user in users
        ]
    }
```

## Monitoring and Health Check Implementations

### Comprehensive Health Checks
```python
# health_monitoring.py - Health check and monitoring integration
from fastapi import FastAPI, HTTPException, status
from elasticsearch_dsl.connections import connections
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
import time
import psutil
import logging
import redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics collectors
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('elasticsearch_active_connections', 'Active Elasticsearch connections')
SEARCH_OPERATIONS = Counter('elasticsearch_search_operations_total', 'Total search operations', ['index', 'status'])

class HealthStatus(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    checks: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None

class HealthChecker:
    """Comprehensive health check service."""
    
    def __init__(self, app_version: str = "1.0.0", environment: str = "development"):
        self.app_version = app_version
        self.environment = environment
        self.redis_client = None
        self.start_time = time.time()
    
    async def check_elasticsearch(self) -> Dict[str, Any]:
        """Check Elasticsearch connectivity and cluster health."""
        try:
            client = connections.get_connection()
            
            # Test basic connectivity
            await client.ping()
            
            # Get cluster health
            health = await client.cluster.health()
            
            # Get basic stats
            stats = await client.cluster.stats()
            
            return {
                "status": "healthy" if health["status"] in ["green", "yellow"] else "unhealthy",
                "cluster_name": health["cluster_name"],
                "cluster_status": health["status"],
                "active_shards": health["active_shards"],
                "number_of_nodes": health["number_of_nodes"],
                "indices_count": stats["indices"]["count"],
                "docs_count": stats["indices"]["docs"]["count"],
                "store_size_bytes": stats["indices"]["store"]["size_in_bytes"],
                "response_time_ms": 0  # You can measure this
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and basic operations."""
        try:
            if not self.redis_client:
                self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            
            # Test basic operations
            start_time = time.time()
            await asyncio.to_thread(self.redis_client.ping)
            response_time = (time.time() - start_time) * 1000
            
            # Get memory info
            info = await asyncio.to_thread(self.redis_client.info, "memory")
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "memory_used_bytes": info.get("used_memory", 0),
                "memory_peak_bytes": info.get("used_memory_peak", 0),
                "connected_clients": info.get("connected_clients", 0)
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy" if cpu_percent < 90 and memory.percent < 90 else "warning",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_bytes": memory.available,
                "disk_percent": disk.percent,
                "disk_free_bytes": disk.free,
                "uptime_seconds": time.time() - self.start_time
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def perform_health_check(self, include_detailed: bool = False) -> HealthStatus:
        """Perform comprehensive health check."""
        checks = {}
        overall_status = "healthy"
        
        # Check all components
        elasticsearch_health = await self.check_elasticsearch()
        redis_health = await self.check_redis()
        system_health = self.check_system_resources()
        
        checks["elasticsearch"] = elasticsearch_health
        checks["redis"] = redis_health
        checks["system"] = system_health
        
        # Determine overall status
        for check_name, check_result in checks.items():
            if check_result.get("status") == "unhealthy":
                overall_status = "unhealthy"
                break
            elif check_result.get("status") == "warning" and overall_status == "healthy":
                overall_status = "warning"
        
        # Add metrics if requested
        metrics = None
        if include_detailed:
            metrics = {
                "total_requests": REQUEST_COUNT._value.sum(),
                "active_elasticsearch_connections": len(connections._conns),
                "app_uptime_seconds": time.time() - self.start_time
            }
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=self.app_version,
            environment=self.environment,
            checks=checks,
            metrics=metrics
        )

# Health check endpoints
health_checker = HealthChecker(app_version="1.0.0", environment="production")

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Basic health check endpoint."""
    return await health_checker.perform_health_check()

@app.get("/health/detailed", response_model=HealthStatus)
async def detailed_health_check():
    """Detailed health check with metrics."""
    return await health_checker.perform_health_check(include_detailed=True)

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    health = await health_checker.perform_health_check()
    if health.status == "unhealthy":
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    try:
        # Simple check that the application is responding
        return {"status": "alive", "timestamp": datetime.utcnow()}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not alive")

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()

# Middleware for metrics collection
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Collect request metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response
```

## Background Task Examples for Indexing

### Celery Integration for Background Tasks
```python
# background_tasks.py - Background task processing for indexing
from celery import Celery
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Date, Float, Integer
from elasticsearch_dsl.connections import connections
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging
import json
from pydantic import BaseModel
import redis

# Configure Celery
celery_app = Celery(
    'search_indexer',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'background_tasks.bulk_index_documents': {'queue': 'indexing'},
        'background_tasks.process_document_updates': {'queue': 'updates'},
        'background_tasks.cleanup_old_indices': {'queue': 'maintenance'},
    }
)

# Document models
class ProductDocument(AsyncDocument):
    """Product document for indexing."""
    
    name = Text(analyzer='standard')
    description = Text(analyzer='english')
    price = Float()
    category = Keyword()
    brand = Keyword()
    tags = Keyword(multi=True)
    created_at = Date()
    updated_at = Date()
    
    class Index:
        name = 'products'

class IndexingTask(BaseModel):
    """Indexing task model."""
    task_id: str
    task_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_documents: int
    processed_documents: int = 0
    failed_documents: int = 0
    error_messages: List[str] = []

# Background task functions
@celery_app.task(bind=True, max_retries=3)
def bulk_index_documents(self, documents_data: List[Dict[str, Any]], index_name: str = None):
    """Bulk index documents in the background."""
    try:
        # Set up async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _bulk_index():
            # Configure Elasticsearch connection
            connections.configure(
                default={'hosts': ['localhost:9200'], 'timeout': 20}
            )
            
            # Create documents
            documents = []
            for doc_data in documents_data:
                doc = ProductDocument(**doc_data)
                if index_name:
                    doc._index._name = index_name
                documents.append(doc)
            
            # Bulk index
            success_count = 0
            error_count = 0
            errors = []
            
            try:
                # Index in batches of 100
                batch_size = 100
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    
                    # Update progress
                    progress = min(i + batch_size, len(documents))
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': progress,
                            'total': len(documents),
                            'status': f'Processing batch {i//batch_size + 1}'
                        }
                    )
                    
                    # Index batch
                    for doc in batch:
                        try:
                            await doc.save()
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            errors.append(f"Document {doc.name}: {str(e)}")
                            logging.error(f"Failed to index document: {e}")
                
                return {
                    'status': 'completed',
                    'total_documents': len(documents),
                    'success_count': success_count,
                    'error_count': error_count,
                    'errors': errors[:10]  # Limit error messages
                }
            
            except Exception as e:
                logging.error(f"Bulk indexing failed: {e}")
                raise
        
        # Run async function
        result = loop.run_until_complete(_bulk_index())
        loop.close()
        
        return result
    
    except Exception as exc:
        logging.error(f"Task failed: {exc}")
        self.retry(countdown=60, exc=exc)

@celery_app.task(bind=True)
def process_document_updates(self, updates: List[Dict[str, Any]]):
    """Process document updates in the background."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _process_updates():
            connections.configure(
                default={'hosts': ['localhost:9200'], 'timeout': 20}
            )
            
            success_count = 0
            error_count = 0
            
            for update in updates:
                try:
                    doc_id = update.get('id')
                    doc_data = update.get('data')
                    
                    # Get existing document
                    doc = await ProductDocument.get(doc_id, ignore=404)
                    if doc:
                        # Update fields
                        for field, value in doc_data.items():
                            setattr(doc, field, value)
                        doc.updated_at = datetime.utcnow()
                        await doc.save()
                        success_count += 1
                    else:
                        error_count += 1
                        logging.warning(f"Document {doc_id} not found")
                
                except Exception as e:
                    error_count += 1
                    logging.error(f"Failed to update document {doc_id}: {e}")
            
            return {
                'status': 'completed',
                'updates_processed': len(updates),
                'success_count': success_count,
                'error_count': error_count
            }
        
        result = loop.run_until_complete(_process_updates())
        loop.close()
        
        return result
    
    except Exception as exc:
        logging.error(f"Update task failed: {exc}")
        raise

@celery_app.task
def cleanup_old_indices(days_old: int = 30):
    """Clean up old indices based on age."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def _cleanup():
            connections.configure(
                default={'hosts': ['localhost:9200'], 'timeout': 20}
            )
            
            client = connections.get_connection()
            
            # Get all indices
            indices = await client.indices.get_alias()
            cutoff_date = datetime.utcnow().timestamp() - (days_old * 24 * 60 * 60)
            
            deleted_indices = []
            
            for index_name in indices:
                try:
                    # Get index creation date
                    index_info = await client.indices.get(index_name)
                    creation_date = index_info[index_name]['settings']['index']['creation_date']
                    creation_timestamp = int(creation_date) / 1000  # Convert to seconds
                    
                    if creation_timestamp < cutoff_date:
                        await client.indices.delete(index_name)
                        deleted_indices.append(index_name)
                        logging.info(f"Deleted old index: {index_name}")
                
                except Exception as e:
                    logging.error(f"Failed to process index {index_name}: {e}")
            
            return {
                'status': 'completed',
                'deleted_indices': deleted_indices,
                'deletion_count': len(deleted_indices)
            }
        
        result = loop.run_until_complete(_cleanup())
        loop.close()
        
        return result
    
    except Exception as exc:
        logging.error(f"Cleanup task failed: {exc}")
        raise

# FastAPI integration for background tasks
from fastapi import BackgroundTasks

@app.post("/indexing/bulk")
async def trigger_bulk_indexing(
    documents: List[Dict[str, Any]],
    index_name: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    """Trigger bulk indexing task."""
    try:
        # Start background task
        task = bulk_index_documents.delay(documents, index_name)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "message": f"Bulk indexing task queued for {len(documents)} documents"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue indexing task: {str(e)}"
        )

@app.get("/indexing/status/{task_id}")
async def get_indexing_status(task_id: str):
    """Get status of indexing task."""
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task.state,
                'status': 'Task is waiting to be processed'
            }
        elif task.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 0),
                'status': task.info.get('status', '')
            }
        else:
            response = {
                'task_id': task_id,
                'state': task.state,
                'result': task.info
            }
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )

@app.post("/maintenance/cleanup")
async def trigger_cleanup(days_old: int = 30):
    """Trigger index cleanup task."""
    try:
        task = cleanup_old_indices.delay(days_old)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "message": f"Cleanup task queued for indices older than {days_old} days"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue cleanup task: {str(e)}"
        )
```

## Error Handling and Logging Patterns

### Comprehensive Error Handling
```python
# error_handling.py - Comprehensive error handling and logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from elasticsearch.exceptions import (
    ConnectionError, 
    NotFoundError, 
    RequestError, 
    TransportError,
    AuthenticationException,
    AuthorizationException
)
from pydantic import ValidationError
import logging
import traceback
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Create specialized loggers
app_logger = logging.getLogger('app')
elasticsearch_logger = logging.getLogger('elasticsearch')
auth_logger = logging.getLogger('auth')
performance_logger = logging.getLogger('performance')

class StructuredLogger:
    """Structured logging utility."""
    
    @staticmethod
    def log_request(request: Request, response_status: int, duration: float, user_id: str = None):
        """Log structured request information."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': str(uuid.uuid4()),
            'method': request.method,
            'url': str(request.url),
            'status_code': response_status,
            'duration_ms': round(duration * 1000, 2),
            'user_agent': request.headers.get('user-agent'),
            'ip_address': request.client.host,
            'user_id': user_id
        }
        
        if response_status >= 400:
            app_logger.error(f"Request failed: {json.dumps(log_data)}")
        else:
            app_logger.info(f"Request completed: {json.dumps(log_data)}")
    
    @staticmethod
    def log_elasticsearch_operation(operation: str, index: str, duration: float, 
                                   success: bool, error: str = None, doc_count: int = None):
        """Log Elasticsearch operations."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'index': index,
            'duration_ms': round(duration * 1000, 2),
            'success': success,
            'doc_count': doc_count
        }
        
        if error:
            log_data['error'] = error
            elasticsearch_logger.error(f"Elasticsearch operation failed: {json.dumps(log_data)}")
        else:
            elasticsearch_logger.info(f"Elasticsearch operation completed: {json.dumps(log_data)}")
    
    @staticmethod
    def log_authentication_event(event_type: str, username: str, success: bool, 
                                ip_address: str, error: str = None):
        """Log authentication events."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'username': username,
            'success': success,
            'ip_address': ip_address
        }
        
        if error:
            log_data['error'] = error
            auth_logger.warning(f"Authentication event: {json.dumps(log_data)}")
        else:
            auth_logger.info(f"Authentication event: {json.dumps(log_data)}")

# Custom exception classes
class SearchServiceError(Exception):
    """Base exception for search service errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "SEARCH_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class ElasticsearchConnectionError(SearchServiceError):
    """Elasticsearch connection error."""
    
    def __init__(self, message: str = "Failed to connect to Elasticsearch"):
        super().__init__(message, "ELASTICSEARCH_CONNECTION_ERROR")

class DocumentNotFoundError(SearchServiceError):
    """Document not found error."""
    
    def __init__(self, document_id: str):
        message = f"Document with ID '{document_id}' not found"
        super().__init__(message, "DOCUMENT_NOT_FOUND", {"document_id": document_id})

class InvalidQueryError(SearchServiceError):
    """Invalid search query error."""
    
    def __init__(self, query: str, validation_errors: List[str]):
        message = f"Invalid search query: {query}"
        super().__init__(
            message, 
            "INVALID_QUERY", 
            {"query": query, "validation_errors": validation_errors}
        )

# Error response models
class ErrorResponse:
    """Standard error response format."""
    
    def __init__(self, error_code: str, message: str, details: Dict[str, Any] = None, 
                 request_id: str = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "request_id": self.request_id,
                "timestamp": self.timestamp
            }
        }

# Global exception handlers
@app.exception_handler(SearchServiceError)
async def search_service_error_handler(request: Request, exc: SearchServiceError):
    """Handle custom search service errors."""
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details
    )
    
    app_logger.error(f"Search service error: {json.dumps(error_response.to_dict())}")
    
    status_code = 400
    if exc.error_code == "ELASTICSEARCH_CONNECTION_ERROR":
        status_code = 503
    elif exc.error_code == "DOCUMENT_NOT_FOUND":
        status_code = 404
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.to_dict()
    )

@app.exception_handler(ConnectionError)
async def elasticsearch_connection_error_handler(request: Request, exc: ConnectionError):
    """Handle Elasticsearch connection errors."""
    error_response = ErrorResponse(
        error_code="ELASTICSEARCH_CONNECTION_ERROR",
        message="Failed to connect to Elasticsearch cluster",
        details={"elasticsearch_error": str(exc)}
    )
    
    elasticsearch_logger.error(f"Elasticsearch connection error: {json.dumps(error_response.to_dict())}")
    
    return JSONResponse(
        status_code=503,
        content=error_response.to_dict()
    )

@app.exception_handler(NotFoundError)
async def elasticsearch_not_found_handler(request: Request, exc: NotFoundError):
    """Handle Elasticsearch document not found errors."""
    error_response = ErrorResponse(
        error_code="DOCUMENT_NOT_FOUND",
        message="Requested document was not found",
        details={"elasticsearch_error": str(exc)}
    )
    
    return JSONResponse(
        status_code=404,
        content=error_response.to_dict()
    )

@app.exception_handler(RequestError)
async def elasticsearch_request_error_handler(request: Request, exc: RequestError):
    """Handle Elasticsearch request errors (invalid queries, etc.)."""
    error_response = ErrorResponse(
        error_code="INVALID_ELASTICSEARCH_REQUEST",
        message="Invalid request to Elasticsearch",
        details={
            "elasticsearch_error": str(exc),
            "error_type": exc.__class__.__name__
        }
    )
    
    elasticsearch_logger.error(f"Elasticsearch request error: {json.dumps(error_response.to_dict())}")
    
    return JSONResponse(
        status_code=400,
        content=error_response.to_dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={
            "validation_errors": [
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"]
                }
                for error in exc.errors()
            ]
        }
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.to_dict()
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle unexpected internal server errors."""
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={
            "error_type": exc.__class__.__name__,
            "traceback": traceback.format_exc()
        }
    )
    
    app_logger.error(f"Internal server error: {json.dumps(error_response.to_dict())}")
    
    return JSONResponse(
        status_code=500,
        content=error_response.to_dict()
    )

# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests and responses."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log successful request
        StructuredLogger.log_request(
            request=request,
            response_status=response.status_code,
            duration=duration
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    except Exception as e:
        duration = time.time() - start_time
        
        # Log failed request
        StructuredLogger.log_request(
            request=request,
            response_status=500,
            duration=duration
        )
        
        # Re-raise the exception
        raise

# Circuit breaker pattern for Elasticsearch
class CircuitBreaker:
    """Circuit breaker for Elasticsearch operations."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                elasticsearch_logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise ElasticsearchConnectionError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            elasticsearch_logger.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            elasticsearch_logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

# Global circuit breaker instance
elasticsearch_circuit_breaker = CircuitBreaker()
```

## Complete Application Example

### Production-Ready Search Application
```python
# complete_app.py - Production-ready search application with all integrations
from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from elasticsearch_dsl import AsyncDocument, Text, Keyword, Float, Date, Boolean
from elasticsearch_dsl.connections import connections
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging
import time
import uvicorn

# Import our modules
from auth_integration import get_current_user, require_role, UserRole
from health_monitoring import health_checker
from background_tasks import bulk_index_documents
from error_handling import StructuredLogger, elasticsearch_circuit_breaker

# Application setup
app = FastAPI(
    title="Production Search API",
    description="Production-ready FastAPI + Elasticsearch search application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"]
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Document model
class ProductDocument(AsyncDocument):
    """Enhanced product document."""
    
    name = Text(analyzer='standard', fields={'keyword': Keyword()})
    description = Text(analyzer='english')
    price = Float()
    sale_price = Float()
    category = Keyword()
    brand = Keyword()
    tags = Keyword(multi=True)
    in_stock = Boolean()
    stock_quantity = Integer()
    average_rating = Float()
    review_count = Integer()
    created_at = Date()
    updated_at = Date()
    
    class Index:
        name = 'products_v1'
        settings = {
            'number_of_shards': 2,
            'number_of_replicas': 1,
            'refresh_interval': '5s'
        }

# Request/Response models
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    price: float = Field(..., gt=0)
    sale_price: Optional[float] = Field(None, gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=100)
    tags: List[str] = Field(default=[])
    stock_quantity: int = Field(..., ge=0)

class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    price: float
    sale_price: Optional[float]
    category: str
    brand: str
    tags: List[str]
    in_stock: bool
    stock_quantity: int
    average_rating: Optional[float]
    review_count: int
    created_at: datetime
    updated_at: datetime
    score: Optional[float] = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock_only: bool = True
    tags: Optional[List[str]] = None
    sort_by: Optional[str] = Field(None, regex=r'^(price|rating|name|created_at)$')
    sort_order: Optional[str] = Field('asc', regex=r'^(asc|desc)$')
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class SearchResponse(BaseModel):
    total: int
    page: int
    size: int
    has_next: bool
    has_previous: bool
    products: List[ProductResponse]
    facets: Dict[str, Any] = {}
    query_time_ms: float

# Service layer
class ProductService:
    """Product service with comprehensive search functionality."""
    
    @staticmethod
    async def create_product(product_data: ProductCreate, user_id: str) -> ProductResponse:
        """Create a new product."""
        start_time = time.time()
        
        try:
            product = ProductDocument(
                name=product_data.name,
                description=product_data.description,
                price=product_data.price,
                sale_price=product_data.sale_price,
                category=product_data.category,
                brand=product_data.brand,
                tags=product_data.tags,
                in_stock=product_data.stock_quantity > 0,
                stock_quantity=product_data.stock_quantity,
                average_rating=0.0,
                review_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await elasticsearch_circuit_breaker.call(product.save)
            
            duration = time.time() - start_time
            StructuredLogger.log_elasticsearch_operation(
                operation="create_product",
                index=product._index._name,
                duration=duration,
                success=True,
                doc_count=1
            )
            
            return ProductResponse(
                id=product.meta.id,
                **product.to_dict()
            )
        
        except Exception as e:
            duration = time.time() - start_time
            StructuredLogger.log_elasticsearch_operation(
                operation="create_product",
                index="products_v1",
                duration=duration,
                success=False,
                error=str(e)
            )
            raise
    
    @staticmethod
    async def search_products(search_request: SearchRequest) -> SearchResponse:
        """Advanced product search with faceting."""
        start_time = time.time()
        
        try:
            # Build search query
            search = ProductDocument.search()
            
            # Text search
            if search_request.query:
                search = search.query(
                    "multi_match",
                    query=search_request.query,
                    fields=["name^2", "description", "tags"],
                    fuzziness="AUTO"
                )
            
            # Filters
            if search_request.category:
                search = search.filter("term", category=search_request.category)
            
            if search_request.brand:
                search = search.filter("term", brand=search_request.brand)
            
            if search_request.min_price is not None:
                search = search.filter("range", price={"gte": search_request.min_price})
            
            if search_request.max_price is not None:
                search = search.filter("range", price={"lte": search_request.max_price})
            
            if search_request.in_stock_only:
                search = search.filter("term", in_stock=True)
            
            if search_request.tags:
                search = search.filter("terms", tags=search_request.tags)
            
            # Sorting
            if search_request.sort_by:
                sort_field = search_request.sort_by
                if search_request.sort_order == "desc":
                    sort_field = f"-{sort_field}"
                search = search.sort(sort_field)
            
            # Pagination
            offset = (search_request.page - 1) * search_request.size
            search = search[offset:offset + search_request.size]
            
            # Add aggregations for faceting
            search.aggs.bucket('categories', 'terms', field='category')
            search.aggs.bucket('brands', 'terms', field='brand')
            search.aggs.bucket('price_ranges', 'range', field='price', ranges=[
                {"key": "0-50", "to": 50},
                {"key": "50-100", "from": 50, "to": 100},
                {"key": "100-200", "from": 100, "to": 200},
                {"key": "200+", "from": 200}
            ])
            
            # Execute search
            response = await elasticsearch_circuit_breaker.call(search.execute)
            
            # Build response
            products = [
                ProductResponse(
                    id=hit.meta.id,
                    score=hit.meta.score,
                    **hit.to_dict()
                )
                for hit in response.hits
            ]
            
            # Process facets
            facets = {}
            if hasattr(response.aggregations, 'categories'):
                facets['categories'] = [
                    {"value": bucket.key, "count": bucket.doc_count}
                    for bucket in response.aggregations.categories.buckets
                ]
            
            if hasattr(response.aggregations, 'brands'):
                facets['brands'] = [
                    {"value": bucket.key, "count": bucket.doc_count}
                    for bucket in response.aggregations.brands.buckets
                ]
            
            if hasattr(response.aggregations, 'price_ranges'):
                facets['price_ranges'] = [
                    {"range": bucket.key, "count": bucket.doc_count}
                    for bucket in response.aggregations.price_ranges.buckets
                ]
            
            duration = time.time() - start_time
            StructuredLogger.log_elasticsearch_operation(
                operation="search_products",
                index="products_v1",
                duration=duration,
                success=True,
                doc_count=len(products)
            )
            
            return SearchResponse(
                total=response.hits.total.value,
                page=search_request.page,
                size=search_request.size,
                has_next=offset + search_request.size < response.hits.total.value,
                has_previous=search_request.page > 1,
                products=products,
                facets=facets,
                query_time_ms=round(duration * 1000, 2)
            )
        
        except Exception as e:
            duration = time.time() - start_time
            StructuredLogger.log_elasticsearch_operation(
                operation="search_products",
                index="products_v1",
                duration=duration,
                success=False,
                error=str(e)
            )
            raise

# API endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize application."""
    try:
        # Configure Elasticsearch
        connections.configure(
            default={'hosts': ['localhost:9200'], 'timeout': 20}
        )
        
        # Initialize indices
        await ProductDocument.init()
        
        logging.info("✅ Application startup completed")
    except Exception as e:
        logging.error(f"❌ Application startup failed: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return await health_checker.perform_health_check()

@app.post("/products", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    current_user = Depends(require_role([UserRole.ADMIN, UserRole.USER]))
):
    """Create a new product."""
    return await ProductService.create_product(product_data, current_user.username)

@app.post("/products/search", response_model=SearchResponse)
async def search_products(search_request: SearchRequest):
    """Search products with advanced filtering and faceting."""
    return await ProductService.search_products(search_request)

@app.post("/products/bulk-index")
async def bulk_index_products(
    products: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    current_user = Depends(require_role([UserRole.ADMIN]))
):
    """Bulk index products in the background."""
    task = bulk_index_documents.delay(products)
    
    return {
        "message": f"Bulk indexing queued for {len(products)} products",
        "task_id": task.id
    }

if __name__ == "__main__":
    uvicorn.run(
        "complete_app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4,
        log_level="info"
    )
```

## Testing Integration Patterns

### Comprehensive Testing Setup
```python
# test_integration.py - Integration testing patterns
import pytest
import asyncio
from fastapi.testclient import TestClient
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import AsyncDocument
import redis
from unittest.mock import Mock, patch
import json
from datetime import datetime

# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def elasticsearch_test_client():
    """Setup test Elasticsearch client."""
    connections.configure(
        default={'hosts': ['localhost:9200'], 'timeout': 20}
    )
    
    # Create test index
    await ProductDocument.init(index='test_products')
    
    yield connections.get_connection()
    
    # Cleanup
    try:
        await connections.get_connection().indices.delete('test_products')
    except Exception:
        pass

@pytest.fixture
def redis_test_client():
    """Setup test Redis client."""
    client = redis.Redis(host='localhost', port=6379, db=15)  # Use test DB
    yield client
    client.flushdb()  # Cleanup

@pytest.fixture
def test_client():
    """FastAPI test client."""
    from complete_app import app
    return TestClient(app)

# Integration tests
class TestAuthenticationIntegration:
    """Test authentication integration."""
    
    async def test_user_registration_and_login(self, test_client):
        """Test complete user registration and login flow."""
        # Register user
        registration_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "roles": ["user"]
        }
        
        response = test_client.post("/auth/register", json=registration_data)
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"
        
        # Login
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        
        response = test_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # Test protected endpoint
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        response = test_client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"

class TestSearchIntegration:
    """Test search functionality integration."""
    
    async def test_product_creation_and_search(self, test_client, elasticsearch_test_client):
        """Test product creation and search integration."""
        # Create admin user and get token
        admin_token = await self._create_admin_user(test_client)
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create product
        product_data = {
            "name": "Test Product",
            "description": "This is a test product for integration testing",
            "price": 99.99,
            "category": "Electronics",
            "brand": "TestBrand",
            "tags": ["test", "integration"],
            "stock_quantity": 10
        }
        
        response = test_client.post("/products", json=product_data, headers=headers)
        assert response.status_code == 200
        
        created_product = response.json()
        assert created_product["name"] == "Test Product"
        assert created_product["in_stock"] == True
        
        # Wait for Elasticsearch to index
        await asyncio.sleep(1)
        
        # Search for product
        search_request = {
            "query": "Test Product",
            "page": 1,
            "size": 10
        }
        
        response = test_client.post("/products/search", json=search_request)
        assert response.status_code == 200
        
        search_results = response.json()
        assert search_results["total"] >= 1
        assert len(search_results["products"]) >= 1
        assert search_results["products"][0]["name"] == "Test Product"
    
    async def _create_admin_user(self, test_client):
        """Helper to create admin user and return token."""
        # Implementation would create admin user and return token
        pass

class TestBackgroundTaskIntegration:
    """Test background task integration."""
    
    @patch('background_tasks.bulk_index_documents.delay')
    async def test_bulk_indexing_task(self, mock_delay, test_client):
        """Test bulk indexing background task."""
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_delay.return_value = mock_task
        
        admin_token = await self._create_admin_user(test_client)
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        products = [
            {
                "name": f"Product {i}",
                "description": f"Description {i}",
                "price": 10.0 + i,
                "category": "Test",
                "brand": "TestBrand",
                "tags": ["bulk", "test"],
                "stock_quantity": 5
            }
            for i in range(100)
        ]
        
        response = test_client.post("/products/bulk-index", json=products, headers=headers)
        assert response.status_code == 200
        
        result = response.json()
        assert "task_id" in result
        assert result["task_id"] == "test-task-id"
        
        # Verify mock was called
        mock_delay.assert_called_once_with(products)

class TestErrorHandlingIntegration:
    """Test error handling integration."""
    
    async def test_elasticsearch_connection_error(self, test_client):
        """Test handling of Elasticsearch connection errors."""
        with patch('elasticsearch_dsl.connections.connections.get_connection') as mock_conn:
            mock_conn.side_effect = ConnectionError("Connection failed")
            
            search_request = {
                "query": "test query",
                "page": 1,
                "size": 10
            }
            
            response = test_client.post("/products/search", json=search_request)
            assert response.status_code == 503
            
            error_data = response.json()
            assert error_data["error"]["code"] == "ELASTICSEARCH_CONNECTION_ERROR"
    
    async def test_validation_error_handling(self, test_client):
        """Test request validation error handling."""
        # Invalid product data
        invalid_product = {
            "name": "",  # Empty name should fail validation
            "description": "short",  # Too short description
            "price": -10,  # Negative price
            "category": "",
            "brand": "",
            "stock_quantity": -1  # Negative stock
        }
        
        response = test_client.post("/products", json=invalid_product)
        assert response.status_code == 422
        
        error_data = response.json()
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        assert "validation_errors" in error_data["error"]["details"]

class TestHealthCheckIntegration:
    """Test health check integration."""
    
    async def test_health_check_with_services(self, test_client, elasticsearch_test_client, redis_test_client):
        """Test health check with all services running."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] in ["healthy", "warning"]
        assert "checks" in health_data
        assert "elasticsearch" in health_data["checks"]
        assert "redis" in health_data["checks"]
        assert "system" in health_data["checks"]
    
    async def test_readiness_probe(self, test_client):
        """Test Kubernetes readiness probe."""
        response = test_client.get("/health/ready")
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            assert response.json()["status"] == "ready"
    
    async def test_liveness_probe(self, test_client):
        """Test Kubernetes liveness probe."""
        response = test_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

# Load testing helpers
class TestPerformanceIntegration:
    """Test performance and load scenarios."""
    
    async def test_concurrent_searches(self, test_client):
        """Test concurrent search performance."""
        search_request = {
            "query": "test",
            "page": 1,
            "size": 10
        }
        
        async def perform_search():
            response = test_client.post("/products/search", json=search_request)
            return response.status_code
        
        # Perform 10 concurrent searches
        tasks = [perform_search() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All searches should succeed
        assert all(status == 200 for status in results)
    
    async def test_rate_limiting(self, test_client):
        """Test rate limiting behavior."""
        # This would test rate limiting if implemented
        pass

# Run tests
if __name__ == "__main__":
    pytest.main(["-v", "test_integration.py"])
```

## Next Steps

This comprehensive integration example demonstrates:

1. **Authentication Integration**: Complete JWT-based authentication with role-based access control
2. **Health Monitoring**: Production-ready health checks with Elasticsearch, Redis, and system monitoring
3. **Background Tasks**: Celery integration for bulk indexing and maintenance operations
4. **Error Handling**: Comprehensive error handling with structured logging and circuit breaker patterns
5. **Complete Application**: Production-ready FastAPI application with all integrations
6. **Testing Patterns**: Integration testing covering authentication, search, background tasks, and error scenarios

These patterns provide a solid foundation for building production-ready search applications with FastAPI and Elasticsearch-DSL.

**Continue your journey:**
- Explore [Testing and Deployment](../07-testing-deployment/01_testing-strategies.md) for comprehensive testing approaches
- Review [Production Patterns](../06-production-patterns/01_security-patterns.md) for additional security considerations
- Check out [Data Modeling](../05-data-modeling/01_document-design.md) for advanced document modeling techniques