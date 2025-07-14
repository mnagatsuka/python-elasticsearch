# Security & Authentication

Comprehensive security and authentication patterns for production FastAPI + Elasticsearch-DSL applications with enterprise-grade protection.

## Table of Contents
- [JWT Token Management](#jwt-token-management)
- [Role-Based Access Control](#role-based-access-control)
- [API Authentication Strategies](#api-authentication-strategies)
- [Rate Limiting](#rate-limiting)
- [Elasticsearch Security Integration](#elasticsearch-security-integration)
- [Data Privacy Patterns](#data-privacy-patterns)
- [Security Middleware](#security-middleware)
- [Next Steps](#next-steps)

## JWT Token Management

### JWT Service Implementation
```python
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import secrets
import hashlib

class TokenData(BaseModel):
    username: str
    user_id: str
    roles: List[str]
    permissions: List[str]
    exp: datetime
    iat: datetime

class RefreshTokenData(BaseModel):
    user_id: str
    token_id: str
    exp: datetime

class JWTManager:
    """Comprehensive JWT token management with refresh tokens."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.active_refresh_tokens = {}  # In production, use Redis
        
    def create_access_token(
        self,
        user_id: str,
        username: str,
        roles: List[str],
        permissions: List[str]
    ) -> str:
        """Create a new access token."""
        
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "permissions": permissions,
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a new refresh token."""
        
        token_id = secrets.token_urlsafe(32)
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "token_id": token_id,
            "exp": expire.timestamp(),
            "type": "refresh"
        }
        
        # Store in active tokens (use Redis in production)
        self.active_refresh_tokens[token_id] = {
            "user_id": user_id,
            "exp": expire,
            "created_at": datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def verify_access_token(self, token: str) -> TokenData:
        """Verify and decode access token."""
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return TokenData(
                username=payload.get("username"),
                user_id=payload.get("sub"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat"))
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    async def verify_refresh_token(self, token: str) -> RefreshTokenData:
        """Verify refresh token and check if it's active."""
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            token_id = payload.get("token_id")
            if token_id not in self.active_refresh_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked"
                )
            
            return RefreshTokenData(
                user_id=payload.get("sub"),
                token_id=token_id,
                exp=datetime.fromtimestamp(payload.get("exp"))
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def revoke_refresh_token(self, token_id: str):
        """Revoke a refresh token."""
        if token_id in self.active_refresh_tokens:
            del self.active_refresh_tokens[token_id]
    
    async def revoke_all_user_tokens(self, user_id: str):
        """Revoke all refresh tokens for a user."""
        tokens_to_remove = [
            token_id for token_id, data in self.active_refresh_tokens.items()
            if data["user_id"] == user_id
        ]
        
        for token_id in tokens_to_remove:
            del self.active_refresh_tokens[token_id]

jwt_manager = JWTManager(secret_key="your-secret-key-here")  # Use env var
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Dependency to get current authenticated user."""
    return await jwt_manager.verify_access_token(credentials.credentials)
```

### Password Security
```python
class PasswordManager:
    """Secure password handling with advanced security features."""
    
    def __init__(self):
        self.min_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        self.require_special = True
        self.max_password_age_days = 90
        self.password_history_count = 5
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password meets security requirements."""
        
        errors = []
        score = 0
        
        # Length check
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")
        else:
            score += 1
        
        # Character requirements
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letters")
        else:
            score += 1
            
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letters")
        else:
            score += 1
            
        if self.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain numbers")
        else:
            score += 1
            
        if self.require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain special characters")
        else:
            score += 1
        
        # Additional strength checks
        if len(set(password)) < len(password) * 0.7:
            errors.append("Password has too many repeated characters")
        else:
            score += 1
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength_score": score,
            "strength_level": self._get_strength_level(score)
        }
    
    def _get_strength_level(self, score: int) -> str:
        """Get password strength level."""
        if score >= 5:
            return "strong"
        elif score >= 3:
            return "medium"
        else:
            return "weak"

password_manager = PasswordManager()
```

## Role-Based Access Control

### RBAC Implementation
```python
from enum import Enum
from typing import Set

class Permission(str, Enum):
    # User permissions
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    
    # Search permissions
    SEARCH_BASIC = "search:basic"
    SEARCH_ADVANCED = "search:advanced"
    SEARCH_ADMIN = "search:admin"
    
    # Index permissions
    INDEX_READ = "index:read"
    INDEX_WRITE = "index:write"
    INDEX_DELETE = "index:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"

class Role(str, Enum):
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class RBACManager:
    """Role-Based Access Control manager."""
    
    def __init__(self):
        self.role_permissions = {
            Role.GUEST: {
                Permission.SEARCH_BASIC
            },
            Role.USER: {
                Permission.SEARCH_BASIC,
                Permission.SEARCH_ADVANCED,
                Permission.USER_READ
            },
            Role.MODERATOR: {
                Permission.SEARCH_BASIC,
                Permission.SEARCH_ADVANCED,
                Permission.USER_READ,
                Permission.USER_WRITE,
                Permission.INDEX_READ
            },
            Role.ADMIN: {
                Permission.SEARCH_BASIC,
                Permission.SEARCH_ADVANCED,
                Permission.SEARCH_ADMIN,
                Permission.USER_READ,
                Permission.USER_WRITE,
                Permission.USER_DELETE,
                Permission.INDEX_READ,
                Permission.INDEX_WRITE,
                Permission.SYSTEM_MONITOR
            },
            Role.SUPER_ADMIN: set(Permission)  # All permissions
        }
    
    def get_user_permissions(self, roles: List[str]) -> Set[Permission]:
        """Get all permissions for user roles."""
        permissions = set()
        
        for role in roles:
            if role in self.role_permissions:
                permissions.update(self.role_permissions[role])
        
        return permissions
    
    def has_permission(self, user_permissions: List[str], required_permission: Permission) -> bool:
        """Check if user has required permission."""
        return required_permission.value in user_permissions
    
    def has_any_permission(self, user_permissions: List[str], required_permissions: List[Permission]) -> bool:
        """Check if user has any of the required permissions."""
        return any(perm.value in user_permissions for perm in required_permissions)
    
    def has_all_permissions(self, user_permissions: List[str], required_permissions: List[Permission]) -> bool:
        """Check if user has all required permissions."""
        return all(perm.value in user_permissions for perm in required_permissions)

rbac_manager = RBACManager()

def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs or dependency
            current_user = kwargs.get('current_user') or args[-1]
            
            if not isinstance(current_user, TokenData):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not rbac_manager.has_permission(current_user.permissions, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission {permission.value} required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_any_permission(*permissions: Permission):
    """Decorator to require any of the specified permissions."""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user') or args[-1]
            
            if not isinstance(current_user, TokenData):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not rbac_manager.has_any_permission(current_user.permissions, list(permissions)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {[p.value for p in permissions]}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

## API Authentication Strategies

### Multi-Strategy Authentication
```python
from abc import ABC, abstractmethod
from fastapi import Request

class AuthenticationStrategy(ABC):
    """Abstract base class for authentication strategies."""
    
    @abstractmethod
    async def authenticate(self, request: Request) -> Optional[TokenData]:
        """Authenticate the request."""
        pass

class JWTAuthStrategy(AuthenticationStrategy):
    """JWT token authentication strategy."""
    
    async def authenticate(self, request: Request) -> Optional[TokenData]:
        """Authenticate using JWT token."""
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        try:
            return await jwt_manager.verify_access_token(token)
        except HTTPException:
            return None

class APIKeyAuthStrategy(AuthenticationStrategy):
    """API key authentication strategy."""
    
    def __init__(self):
        # In production, store API keys in database
        self.api_keys = {
            "api_key_123": {
                "user_id": "service_user_1",
                "username": "service_account",
                "roles": ["service"],
                "permissions": ["search:basic", "search:advanced"],
                "rate_limit": 1000  # requests per hour
            }
        }
    
    async def authenticate(self, request: Request) -> Optional[TokenData]:
        """Authenticate using API key."""
        
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        
        return TokenData(
            username=key_data["username"],
            user_id=key_data["user_id"],
            roles=key_data["roles"],
            permissions=key_data["permissions"],
            exp=datetime.utcnow() + timedelta(hours=1),  # API keys don't expire
            iat=datetime.utcnow()
        )

class SessionAuthStrategy(AuthenticationStrategy):
    """Session-based authentication strategy."""
    
    def __init__(self):
        self.sessions = {}  # In production, use Redis
    
    async def authenticate(self, request: Request) -> Optional[TokenData]:
        """Authenticate using session."""
        
        session_id = request.cookies.get("session_id")
        if not session_id or session_id not in self.sessions:
            return None
        
        session_data = self.sessions[session_id]
        
        # Check if session is expired
        if session_data["expires"] < datetime.utcnow():
            del self.sessions[session_id]
            return None
        
        return TokenData(
            username=session_data["username"],
            user_id=session_data["user_id"],
            roles=session_data["roles"],
            permissions=session_data["permissions"],
            exp=session_data["expires"],
            iat=session_data["created"]
        )

class MultiAuthManager:
    """Manager for multiple authentication strategies."""
    
    def __init__(self):
        self.strategies = [
            JWTAuthStrategy(),
            APIKeyAuthStrategy(),
            SessionAuthStrategy()
        ]
    
    async def authenticate(self, request: Request) -> Optional[TokenData]:
        """Try all authentication strategies."""
        
        for strategy in self.strategies:
            try:
                result = await strategy.authenticate(request)
                if result:
                    return result
            except Exception:
                continue  # Try next strategy
        
        return None

multi_auth = MultiAuthManager()

async def get_current_user_multi(request: Request) -> TokenData:
    """Dependency that supports multiple authentication methods."""
    
    user = await multi_auth.authenticate(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user
```

## Rate Limiting

### Advanced Rate Limiting
```python
import time
from collections import defaultdict
from typing import Dict, Tuple
import asyncio
import redis.asyncio as redis

class RateLimiter:
    """Advanced rate limiting with multiple strategies."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.local_cache = defaultdict(list)  # Fallback for development
        
        # Rate limit configurations
        self.limits = {
            "default": {"requests": 100, "window": 3600},  # 100 req/hour
            "premium": {"requests": 1000, "window": 3600},  # 1000 req/hour
            "api_key": {"requests": 5000, "window": 3600},  # 5000 req/hour
            "admin": {"requests": 10000, "window": 3600}   # 10000 req/hour
        }
    
    async def is_allowed(
        self,
        identifier: str,
        rate_limit_type: str = "default"
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit."""
        
        if rate_limit_type not in self.limits:
            rate_limit_type = "default"
        
        config = self.limits[rate_limit_type]
        current_time = int(time.time())
        window_start = current_time - config["window"]
        
        if self.redis:
            return await self._check_redis_rate_limit(
                identifier, config, current_time, window_start
            )
        else:
            return await self._check_local_rate_limit(
                identifier, config, current_time, window_start
            )
    
    async def _check_redis_rate_limit(
        self,
        identifier: str,
        config: Dict[str, int],
        current_time: int,
        window_start: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis."""
        
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(f"rate_limit:{identifier}", 0, window_start)
        
        # Count current requests
        pipe.zcard(f"rate_limit:{identifier}")
        
        # Add current request
        pipe.zadd(f"rate_limit:{identifier}", {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(f"rate_limit:{identifier}", config["window"])
        
        results = await pipe.execute()
        current_requests = results[1]
        
        allowed = current_requests < config["requests"]
        
        return allowed, {
            "requests_made": current_requests + 1,
            "requests_limit": config["requests"],
            "window_seconds": config["window"],
            "reset_time": current_time + config["window"]
        }
    
    async def _check_local_rate_limit(
        self,
        identifier: str,
        config: Dict[str, int],
        current_time: int,
        window_start: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limit using local memory (development only)."""
        
        # Clean old entries
        self.local_cache[identifier] = [
            req_time for req_time in self.local_cache[identifier]
            if req_time > window_start
        ]
        
        current_requests = len(self.local_cache[identifier])
        allowed = current_requests < config["requests"]
        
        if allowed:
            self.local_cache[identifier].append(current_time)
        
        return allowed, {
            "requests_made": current_requests + (1 if allowed else 0),
            "requests_limit": config["requests"],
            "window_seconds": config["window"],
            "reset_time": current_time + config["window"]
        }

# Rate limiting middleware
class RateLimitMiddleware:
    """Middleware for request rate limiting."""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        # Determine rate limit type based on user
        rate_limit_type = "default"
        identifier = request.client.host  # Default to IP
        
        # Try to get authenticated user for better rate limiting
        try:
            user = await multi_auth.authenticate(request)
            if user:
                identifier = user.user_id
                
                # Determine rate limit based on user roles
                if "admin" in user.roles:
                    rate_limit_type = "admin"
                elif "premium" in user.roles:
                    rate_limit_type = "premium"
                elif "service" in user.roles:
                    rate_limit_type = "api_key"
        except:
            pass  # Use default settings
        
        # Check rate limit
        allowed, info = await self.rate_limiter.is_allowed(identifier, rate_limit_type)
        
        if not allowed:
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "details": info
                }),
                status_code=429,
                headers={
                    "X-RateLimit-Limit": str(info["requests_limit"]),
                    "X-RateLimit-Remaining": str(max(0, info["requests_limit"] - info["requests_made"])),
                    "X-RateLimit-Reset": str(info["reset_time"]),
                    "Retry-After": str(info["window_seconds"])
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["requests_limit"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, info["requests_limit"] - info["requests_made"]))
        response.headers["X-RateLimit-Reset"] = str(info["reset_time"])
        
        return response

# Initialize rate limiter
rate_limiter = RateLimiter()
```

## Elasticsearch Security Integration

### Secure Elasticsearch Access
```python
from elasticsearch_dsl import connections
from elasticsearch import Elasticsearch
import ssl

class SecureElasticsearchManager:
    """Secure Elasticsearch connection and access management."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self._setup_secure_connection()
    
    def _setup_secure_connection(self):
        """Setup secure Elasticsearch connection."""
        
        # SSL/TLS configuration
        ssl_context = ssl.create_default_context()
        if self.config.get("verify_certs", True):
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        # Custom CA certificate
        if self.config.get("ca_certs"):
            ssl_context.load_verify_locations(self.config["ca_certs"])
        
        # Client certificates
        if self.config.get("client_cert") and self.config.get("client_key"):
            ssl_context.load_cert_chain(
                self.config["client_cert"],
                self.config["client_key"]
            )
        
        # Create secure client
        self.client = Elasticsearch(
            hosts=self.config["hosts"],
            http_auth=(self.config["username"], self.config["password"]),
            use_ssl=True,
            ssl_context=ssl_context,
            verify_certs=self.config.get("verify_certs", True),
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        # Register with elasticsearch-dsl
        connections.add_connection("secure", self.client)
    
    async def get_user_filtered_client(self, user: TokenData) -> Elasticsearch:
        """Get Elasticsearch client with user-specific filtering."""
        
        # Create client with user context
        client_config = self.config.copy()
        
        # Add user-specific headers for audit logging
        client_config["headers"] = {
            "X-User-ID": user.user_id,
            "X-Username": user.username,
            "X-User-Roles": ",".join(user.roles)
        }
        
        return Elasticsearch(**client_config)
    
    def get_index_patterns_for_user(self, user: TokenData) -> List[str]:
        """Get allowed index patterns for user."""
        
        patterns = []
        
        # Basic users can only access public indices
        if "user" in user.roles:
            patterns.extend(["public-*", "shared-*"])
        
        # Moderators can access moderation indices
        if "moderator" in user.roles:
            patterns.extend(["moderation-*", "reports-*"])
        
        # Admins can access all indices
        if "admin" in user.roles or "super_admin" in user.roles:
            patterns.append("*")
        
        return patterns
    
    async def validate_index_access(self, user: TokenData, index_name: str) -> bool:
        """Validate if user can access specific index."""
        
        allowed_patterns = self.get_index_patterns_for_user(user)
        
        for pattern in allowed_patterns:
            if pattern == "*" or index_name.startswith(pattern.replace("*", "")):
                return True
        
        return False

# Dependency for secure Elasticsearch access
async def get_secure_es_client(
    current_user: TokenData = Depends(get_current_user)
) -> Elasticsearch:
    """Get Elasticsearch client with user security context."""
    return await es_manager.get_user_filtered_client(current_user)

# Usage in endpoints
@app.get("/search/{index_name}")
@require_permission(Permission.SEARCH_BASIC)
async def search_index(
    index_name: str,
    query: str,
    current_user: TokenData = Depends(get_current_user),
    es_client: Elasticsearch = Depends(get_secure_es_client)
):
    """Search with security validation."""
    
    # Validate index access
    if not await es_manager.validate_index_access(current_user, index_name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to index: {index_name}"
        )
    
    # Perform search with audit logging
    try:
        result = await es_client.search(
            index=index_name,
            body={"query": {"match": {"content": query}}}
        )
        
        # Log access
        await audit_logger.log_search_access(
            user_id=current_user.user_id,
            index_name=index_name,
            query=query,
            result_count=result["hits"]["total"]["value"]
        )
        
        return result
        
    except Exception as e:
        await audit_logger.log_search_error(
            user_id=current_user.user_id,
            index_name=index_name,
            error=str(e)
        )
        raise
```

## Data Privacy Patterns

### Data Anonymization and PII Protection
```python
import re
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

class PIIDetector:
    """Detect and handle Personally Identifiable Information."""
    
    def __init__(self):
        # PII patterns
        self.patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
        }
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII in text."""
        
        found_pii = {}
        
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                found_pii[pii_type] = matches
        
        return found_pii
    
    def anonymize_text(self, text: str, hash_salt: str = "") -> str:
        """Anonymize PII in text."""
        
        anonymized = text
        
        for pii_type, pattern in self.patterns.items():
            def replace_match(match):
                # Create consistent hash for same PII
                original = match.group()
                hash_obj = hashlib.sha256((original + hash_salt).encode())
                return f"[{pii_type.upper()}_{hash_obj.hexdigest()[:8]}]"
            
            anonymized = pattern.sub(replace_match, anonymized)
        
        return anonymized

class DataRetentionManager:
    """Manage data retention and automatic deletion."""
    
    def __init__(self):
        # Retention policies by data type
        self.retention_policies = {
            "search_logs": timedelta(days=30),
            "user_activity": timedelta(days=90),
            "audit_logs": timedelta(days=365),
            "personal_data": timedelta(days=730),  # 2 years
            "system_logs": timedelta(days=7)
        }
    
    async def should_delete_record(
        self,
        record_type: str,
        created_date: datetime
    ) -> bool:
        """Check if record should be deleted based on retention policy."""
        
        if record_type not in self.retention_policies:
            return False
        
        retention_period = self.retention_policies[record_type]
        expiration_date = created_date + retention_period
        
        return datetime.utcnow() > expiration_date
    
    async def anonymize_expired_records(self, es_client: Elasticsearch):
        """Anonymize records that are past retention but not deleted."""
        
        # Find records eligible for anonymization
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"created_date": {"lt": "now-90d"}}},
                        {"term": {"contains_pii": True}},
                        {"term": {"anonymized": False}}
                    ]
                }
            }
        }
        
        result = await es_client.search(index="user_activity", body=query)
        
        pii_detector = PIIDetector()
        
        for hit in result["hits"]["hits"]:
            doc_id = hit["_id"]
            doc = hit["_source"]
            
            # Anonymize PII fields
            if "content" in doc:
                doc["content"] = pii_detector.anonymize_text(doc["content"])
            
            if "user_input" in doc:
                doc["user_input"] = pii_detector.anonymize_text(doc["user_input"])
            
            # Mark as anonymized
            doc["anonymized"] = True
            doc["anonymized_date"] = datetime.utcnow().isoformat()
            
            # Update document
            await es_client.update(
                index="user_activity",
                id=doc_id,
                body={"doc": doc}
            )

class ConsentManager:
    """Manage user consent for data processing."""
    
    def __init__(self):
        self.consent_types = {
            "analytics": "Analytics and performance monitoring",
            "marketing": "Marketing communications",
            "personalization": "Personalized search results",
            "data_sharing": "Data sharing with partners"
        }
    
    async def get_user_consent(
        self,
        user_id: str,
        es_client: Elasticsearch
    ) -> Dict[str, bool]:
        """Get current user consent status."""
        
        try:
            result = await es_client.get(
                index="user_consent",
                id=user_id
            )
            return result["_source"]["consents"]
        except:
            # Default to no consent
            return {consent_type: False for consent_type in self.consent_types}
    
    async def update_user_consent(
        self,
        user_id: str,
        consents: Dict[str, bool],
        es_client: Elasticsearch
    ):
        """Update user consent preferences."""
        
        consent_doc = {
            "user_id": user_id,
            "consents": consents,
            "updated_date": datetime.utcnow().isoformat(),
            "ip_address": "[ANONYMIZED]",  # Don't store actual IP
            "user_agent": "[ANONYMIZED]"   # Don't store actual user agent
        }
        
        await es_client.index(
            index="user_consent",
            id=user_id,
            body=consent_doc
        )
    
    async def can_process_data(
        self,
        user_id: str,
        purpose: str,
        es_client: Elasticsearch
    ) -> bool:
        """Check if user has consented to data processing for specific purpose."""
        
        consents = await self.get_user_consent(user_id, es_client)
        return consents.get(purpose, False)

# GDPR compliance helpers
class GDPRCompliance:
    """GDPR compliance utilities."""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.retention_manager = DataRetentionManager()
        self.consent_manager = ConsentManager()
    
    async def handle_data_subject_request(
        self,
        user_id: str,
        request_type: str,
        es_client: Elasticsearch
    ) -> Dict[str, Any]:
        """Handle GDPR data subject requests."""
        
        if request_type == "access":
            return await self._handle_access_request(user_id, es_client)
        elif request_type == "deletion":
            return await self._handle_deletion_request(user_id, es_client)
        elif request_type == "portability":
            return await self._handle_portability_request(user_id, es_client)
        else:
            raise ValueError(f"Unknown request type: {request_type}")
    
    async def _handle_access_request(
        self,
        user_id: str,
        es_client: Elasticsearch
    ) -> Dict[str, Any]:
        """Handle data access request (Article 15)."""
        
        # Search for all user data across indices
        query = {
            "query": {"term": {"user_id": user_id}},
            "size": 10000
        }
        
        user_data = {}
        
        # Search across all user data indices
        for index in ["user_activity", "search_history", "user_preferences"]:
            try:
                result = await es_client.search(index=index, body=query)
                user_data[index] = [hit["_source"] for hit in result["hits"]["hits"]]
            except:
                user_data[index] = []
        
        return {
            "user_id": user_id,
            "request_type": "access",
            "data": user_data,
            "export_date": datetime.utcnow().isoformat()
        }
    
    async def _handle_deletion_request(
        self,
        user_id: str,
        es_client: Elasticsearch
    ) -> Dict[str, Any]:
        """Handle data deletion request (Article 17)."""
        
        deleted_records = {}
        
        # Delete from all user data indices
        for index in ["user_activity", "search_history", "user_preferences", "user_consent"]:
            try:
                # Delete by query
                result = await es_client.delete_by_query(
                    index=index,
                    body={"query": {"term": {"user_id": user_id}}}
                )
                deleted_records[index] = result["deleted"]
            except Exception as e:
                deleted_records[index] = f"Error: {str(e)}"
        
        return {
            "user_id": user_id,
            "request_type": "deletion",
            "deleted_records": deleted_records,
            "deletion_date": datetime.utcnow().isoformat()
        }
```

## Security Middleware

### Comprehensive Security Middleware
```python
class SecurityMiddleware:
    """Comprehensive security middleware stack."""
    
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    async def __call__(self, request: Request, call_next):
        # Pre-request security checks
        await self._validate_request_security(request)
        
        # Process request
        response = await call_next(request)
        
        # Post-request security measures
        await self._apply_security_headers(response)
        await self._scan_response_for_pii(response)
        
        return response
    
    async def _validate_request_security(self, request: Request):
        """Validate request for security issues."""
        
        # Check for suspicious patterns
        user_agent = request.headers.get("user-agent", "")
        if self._is_suspicious_user_agent(user_agent):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Suspicious request detected"
            )
        
        # Validate content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agent patterns."""
        
        suspicious_patterns = [
            "sqlmap", "nikto", "nmap", "masscan",
            "gobuster", "dirb", "wfuzz", "burpsuite"
        ]
        
        return any(pattern in user_agent.lower() for pattern in suspicious_patterns)
    
    async def _apply_security_headers(self, response: Response):
        """Apply security headers to response."""
        
        for header, value in self.security_headers.items():
            response.headers[header] = value
    
    async def _scan_response_for_pii(self, response: Response):
        """Scan response for accidental PII exposure."""
        
        if hasattr(response, 'body') and response.body:
            body_text = response.body.decode('utf-8')
            pii_found = self.pii_detector.detect_pii(body_text)
            
            if pii_found:
                # Log PII exposure incident
                logger.warning(
                    "PII detected in response",
                    pii_types=list(pii_found.keys()),
                    endpoint=response.url if hasattr(response, 'url') else 'unknown'
                )

# Apply security middleware
app.add_middleware(SecurityMiddleware)
```

## Next Steps

1. **[Performance Optimization](03_performance-optimization.md)** - Scaling and efficiency patterns
2. **[Error Handling](04_error-handling.md)** - Resilience and recovery patterns
3. **[Testing Strategies](../07-testing-deployment/01_testing-strategies.md)** - Security testing

## Additional Resources

- **OWASP Security Guidelines**: [owasp.org](https://owasp.org)
- **JWT Best Practices**: [auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp](https://auth0.com/blog/a-look-at-the-latest-draft-for-jwt-bcp/)
- **FastAPI Security**: [fastapi.tiangolo.com/tutorial/security](https://fastapi.tiangolo.com/tutorial/security/)
- **Elasticsearch Security**: [elastic.co/guide/en/elasticsearch/reference/current/security-settings.html](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-settings.html)