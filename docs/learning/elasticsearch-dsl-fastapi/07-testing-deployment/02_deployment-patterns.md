# Deployment Patterns

Production deployment strategies for FastAPI + Elasticsearch-DSL applications with Docker, Kubernetes, and scalable deployment patterns.

## Table of Contents
- [Docker Deployment](#docker-deployment)
- [Kubernetes Patterns](#kubernetes-patterns)
- [Blue-Green Deployment](#blue-green-deployment)
- [Rolling Updates](#rolling-updates)
- [Environment Management](#environment-management)
- [Scaling Strategies](#scaling-strategies)
- [Load Balancing](#load-balancing)
- [Next Steps](#next-steps)

## Docker Deployment

### Production Dockerfile
```dockerfile
# Multi-stage build for optimized production image
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set ownership and permissions
RUN chown -R appuser:appuser /app
USER appuser

# Add .venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose for Production
```yaml
version: '3.8'

services:
  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: fastapi_app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ELASTICSEARCH_HOST=elasticsearch
      - ELASTICSEARCH_PORT=9200
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - LOG_LEVEL=info
      - WORKERS=4
    volumes:
      - ./logs:/app/logs
    depends_on:
      elasticsearch:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.example.com`)"
      - "traefik.http.services.api.loadbalancer.server.port=8000"

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    restart: unless-stopped
    environment:
      - cluster.name=search-cluster
      - node.name=search-node-1
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
      - ./config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis for caching
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    networks:
      - app-network

  # Monitoring with Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - app-network

volumes:
  elasticsearch_data:
  redis_data:
  prometheus_data:

networks:
  app-network:
    driver: bridge
```

### Nginx Configuration
```nginx
# config/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream fastapi_backend {
        least_conn;
        server api:8000 max_fails=3 fail_timeout=30s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    # Caching
    proxy_cache_path /var/cache/nginx/search 
                     levels=1:2 
                     keys_zone=search_cache:10m 
                     max_size=1g 
                     inactive=60m;

    server {
        listen 80;
        server_name api.example.com;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # API routes
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://fastapi_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Cache search results
        location /api/search {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_cache search_cache;
            proxy_cache_valid 200 5m;
            proxy_cache_key "$scheme$request_method$host$request_uri";
            
            proxy_pass http://fastapi_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            
            add_header X-Cache-Status $upstream_cache_status;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://fastapi_backend;
            access_log off;
        }

        # Static files (if any)
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## Kubernetes Patterns

### Kubernetes Manifests
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: search-api
  labels:
    name: search-api

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: search-api
data:
  ELASTICSEARCH_HOST: "elasticsearch-service"
  ELASTICSEARCH_PORT: "9200"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  LOG_LEVEL: "info"
  WORKERS: "4"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: search-api
type: Opaque
data:
  JWT_SECRET: "<base64-encoded-jwt-secret>"
  DATABASE_PASSWORD: "<base64-encoded-password>"

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-deployment
  namespace: search-api
  labels:
    app: fastapi
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: your-registry/search-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ELASTICSEARCH_HOST
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: ELASTICSEARCH_HOST
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: JWT_SECRET
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: api-logs-pvc

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  namespace: search-api
spec:
  selector:
    app: fastapi
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  namespace: search-api
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 80

---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
  namespace: search-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Elasticsearch StatefulSet
```yaml
# k8s/elasticsearch.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: search-api
spec:
  serviceName: elasticsearch-headless
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      initContainers:
      - name: increase-vm-max-map
        image: busybox
        command: ["sysctl", "-w", "vm.max_map_count=262144"]
        securityContext:
          privileged: true
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
        env:
        - name: cluster.name
          value: "search-cluster"
        - name: node.name
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: discovery.seed_hosts
          value: "elasticsearch-headless"
        - name: cluster.initial_master_nodes
          value: "elasticsearch-0,elasticsearch-1,elasticsearch-2"
        - name: ES_JAVA_OPTS
          value: "-Xms2g -Xmx2g"
        ports:
        - containerPort: 9200
          name: http
        - containerPort: 9300
          name: transport
        resources:
          requests:
            memory: "3Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        volumeMounts:
        - name: elasticsearch-data
          mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
  - metadata:
      name: elasticsearch-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
      storageClassName: fast-ssd

---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-service
  namespace: search-api
spec:
  selector:
    app: elasticsearch
  ports:
  - port: 9200
    name: http
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch-headless
  namespace: search-api
spec:
  clusterIP: None
  selector:
    app: elasticsearch
  ports:
  - port: 9200
    name: http
  - port: 9300
    name: transport
```

## Blue-Green Deployment

### Blue-Green Strategy Implementation
```python
# scripts/blue_green_deploy.py
import asyncio
import aiohttp
import time
from typing import Dict, List

class BlueGreenDeployer:
    """Manage blue-green deployments for zero-downtime updates."""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.kubectl_cmd = "kubectl"
        
    async def deploy(self, new_image: str, namespace: str = "search-api"):
        """Execute blue-green deployment."""
        
        print("Starting blue-green deployment...")
        
        # Step 1: Determine current environment
        current_env = await self._get_current_environment(namespace)
        target_env = "blue" if current_env == "green" else "green"
        
        print(f"Current environment: {current_env}")
        print(f"Target environment: {target_env}")
        
        try:
            # Step 2: Deploy to target environment
            await self._deploy_to_environment(target_env, new_image, namespace)
            
            # Step 3: Wait for deployment to be ready
            await self._wait_for_deployment_ready(target_env, namespace)
            
            # Step 4: Run health checks
            await self._run_health_checks(target_env, namespace)
            
            # Step 5: Switch traffic
            await self._switch_traffic(target_env, namespace)
            
            # Step 6: Verify traffic switch
            await self._verify_traffic_switch(target_env, namespace)
            
            # Step 7: Scale down old environment
            await self._scale_down_old_environment(current_env, namespace)
            
            print(f"Blue-green deployment completed successfully!")
            print(f"Traffic now routed to: {target_env}")
            
        except Exception as e:
            print(f"Deployment failed: {e}")
            await self._rollback(current_env, namespace)
            raise
    
    async def _get_current_environment(self, namespace: str) -> str:
        """Determine which environment is currently active."""
        cmd = f"{self.kubectl_cmd} get service fastapi-service -n {namespace} -o jsonpath='{{.spec.selector.environment}}'"
        result = await self._run_command(cmd)
        return result.strip() or "blue"
    
    async def _deploy_to_environment(self, env: str, image: str, namespace: str):
        """Deploy new version to target environment."""
        print(f"Deploying {image} to {env} environment...")
        
        # Update deployment with new image and environment label
        deployment_name = f"fastapi-{env}"
        
        # Apply deployment
        cmd = f"""
        {self.kubectl_cmd} set image deployment/{deployment_name} 
        fastapi={image} -n {namespace}
        """
        await self._run_command(cmd)
        
        # Update environment label
        cmd = f"""
        {self.kubectl_cmd} patch deployment {deployment_name} -n {namespace} 
        -p '{{"spec":{{"template":{{"metadata":{{"labels":{{"environment":"{env}"}}}}}}}}}}'
        """
        await self._run_command(cmd)
    
    async def _wait_for_deployment_ready(self, env: str, namespace: str, timeout: int = 300):
        """Wait for deployment to be ready."""
        print(f"Waiting for {env} deployment to be ready...")
        
        deployment_name = f"fastapi-{env}"
        cmd = f"{self.kubectl_cmd} rollout status deployment/{deployment_name} -n {namespace} --timeout={timeout}s"
        
        await self._run_command(cmd)
        print(f"{env} deployment is ready")
    
    async def _run_health_checks(self, env: str, namespace: str):
        """Run comprehensive health checks on new deployment."""
        print(f"Running health checks on {env} environment...")
        
        # Get pod IPs for direct health checks
        cmd = f"""
        {self.kubectl_cmd} get pods -n {namespace} 
        -l app=fastapi,environment={env} 
        -o jsonpath='{{.items[*].status.podIP}}'
        """
        pod_ips = await self._run_command(cmd)
        
        # Test each pod directly
        for pod_ip in pod_ips.split():
            await self._check_pod_health(pod_ip.strip())
        
        print(f"Health checks passed for {env} environment")
    
    async def _check_pod_health(self, pod_ip: str):
        """Check health of individual pod."""
        health_endpoints = [
            f"http://{pod_ip}:8000/health/live",
            f"http://{pod_ip}:8000/health/ready",
            f"http://{pod_ip}:8000/api/search?q=test"  # Functional test
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in health_endpoints:
                try:
                    async with session.get(endpoint, timeout=10) as response:
                        if response.status != 200:
                            raise Exception(f"Health check failed for {endpoint}: {response.status}")
                except Exception as e:
                    raise Exception(f"Health check failed for {pod_ip}: {e}")
    
    async def _switch_traffic(self, target_env: str, namespace: str):
        """Switch traffic to new environment."""
        print(f"Switching traffic to {target_env} environment...")
        
        # Update service selector to point to new environment
        cmd = f"""
        {self.kubectl_cmd} patch service fastapi-service -n {namespace} 
        -p '{{"spec":{{"selector":{{"environment":"{target_env}"}}}}}}'
        """
        await self._run_command(cmd)
        
        # Wait for service to update
        await asyncio.sleep(10)
    
    async def _verify_traffic_switch(self, target_env: str, namespace: str):
        """Verify traffic is routing to new environment."""
        print("Verifying traffic switch...")
        
        # Get service endpoint
        cmd = f"{self.kubectl_cmd} get service fastapi-service -n {namespace} -o jsonpath='{{.spec.clusterIP}}'"
        service_ip = await self._run_command(cmd)
        
        # Test traffic routing
        success_count = 0
        for i in range(10):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{service_ip}/health", timeout=5) as response:
                        if response.status == 200:
                            success_count += 1
                await asyncio.sleep(1)
            except Exception:
                pass
        
        if success_count < 8:  # Allow for some failures
            raise Exception("Traffic switch verification failed")
        
        print("Traffic switch verified successfully")
    
    async def _scale_down_old_environment(self, old_env: str, namespace: str):
        """Scale down the old environment."""
        print(f"Scaling down {old_env} environment...")
        
        deployment_name = f"fastapi-{old_env}"
        cmd = f"{self.kubectl_cmd} scale deployment {deployment_name} --replicas=0 -n {namespace}"
        await self._run_command(cmd)
    
    async def _rollback(self, safe_env: str, namespace: str):
        """Rollback to safe environment in case of failure."""
        print(f"Rolling back to {safe_env} environment...")
        
        # Switch traffic back
        cmd = f"""
        {self.kubectl_cmd} patch service fastapi-service -n {namespace} 
        -p '{{"spec":{{"selector":{{"environment":"{safe_env}"}}}}}}'
        """
        await self._run_command(cmd)
        
        print("Rollback completed")
    
    async def _run_command(self, cmd: str) -> str:
        """Execute shell command and return output."""
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Command failed: {stderr.decode()}")
        
        return stdout.decode()

# Usage
async def main():
    deployer = BlueGreenDeployer({})
    await deployer.deploy("your-registry/search-api:v2.0.0")

if __name__ == "__main__":
    asyncio.run(main())
```

## Rolling Updates

### Kubernetes Rolling Update Strategy
```yaml
# k8s/rolling-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-rolling
  namespace: search-api
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2          # Allow 2 extra pods during update
      maxUnavailable: 1    # Allow 1 pod to be unavailable
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: your-registry/search-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        # Graceful shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
        # Health checks for rolling updates
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
        # Graceful termination
        terminationGracePeriodSeconds: 30
```

### Rolling Update Script
```python
# scripts/rolling_update.py
import asyncio
import subprocess
from typing import Dict, List

class RollingUpdateManager:
    """Manage rolling updates with monitoring and rollback capabilities."""
    
    def __init__(self, namespace: str = "search-api"):
        self.namespace = namespace
        self.kubectl = "kubectl"
    
    async def update_deployment(self, deployment_name: str, new_image: str):
        """Perform rolling update with monitoring."""
        
        print(f"Starting rolling update for {deployment_name}")
        print(f"New image: {new_image}")
        
        try:
            # Step 1: Record deployment state before update
            await self._record_deployment_state(deployment_name)
            
            # Step 2: Update image
            await self._update_image(deployment_name, new_image)
            
            # Step 3: Monitor rollout
            await self._monitor_rollout(deployment_name)
            
            # Step 4: Verify deployment health
            await self._verify_deployment_health(deployment_name)
            
            print("Rolling update completed successfully")
            
        except Exception as e:
            print(f"Rolling update failed: {e}")
            await self._rollback_deployment(deployment_name)
            raise
    
    async def _record_deployment_state(self, deployment_name: str):
        """Record current deployment state for potential rollback."""
        cmd = f"""
        {self.kubectl} rollout history deployment/{deployment_name} 
        -n {self.namespace}
        """
        result = await self._run_command(cmd)
        print(f"Current deployment history:\n{result}")
    
    async def _update_image(self, deployment_name: str, new_image: str):
        """Update deployment image."""
        cmd = f"""
        {self.kubectl} set image deployment/{deployment_name} 
        fastapi={new_image} -n {self.namespace}
        """
        await self._run_command(cmd)
        print(f"Image updated to {new_image}")
    
    async def _monitor_rollout(self, deployment_name: str, timeout: int = 600):
        """Monitor rollout progress with detailed status."""
        print("Monitoring rollout progress...")
        
        # Start rollout status monitoring
        cmd = f"""
        {self.kubectl} rollout status deployment/{deployment_name} 
        -n {self.namespace} --timeout={timeout}s
        """
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Monitor progress
        while True:
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=10
                )
                
                if process.returncode == 0:
                    print("Rollout completed successfully")
                    break
                else:
                    raise Exception(f"Rollout failed: {stderr.decode()}")
                    
            except asyncio.TimeoutError:
                # Check current status
                await self._print_rollout_status(deployment_name)
                continue
    
    async def _print_rollout_status(self, deployment_name: str):
        """Print current rollout status."""
        cmd = f"""
        {self.kubectl} get deployment {deployment_name} -n {self.namespace} 
        -o wide
        """
        result = await self._run_command(cmd)
        print(f"Current status:\n{result}")
    
    async def _verify_deployment_health(self, deployment_name: str):
        """Verify all pods are healthy after update."""
        print("Verifying deployment health...")
        
        # Get pod status
        cmd = f"""
        {self.kubectl} get pods -n {self.namespace} 
        -l app=fastapi -o wide
        """
        result = await self._run_command(cmd)
        print(f"Pod status:\n{result}")
        
        # Check ready replicas
        cmd = f"""
        {self.kubectl} get deployment {deployment_name} -n {self.namespace} 
        -o jsonpath='{{.status.readyReplicas}}/{{.spec.replicas}}'
        """
        ready_status = await self._run_command(cmd)
        
        ready, total = map(int, ready_status.split('/'))
        if ready != total:
            raise Exception(f"Not all replicas are ready: {ready}/{total}")
        
        print(f"All replicas are ready: {ready}/{total}")
    
    async def _rollback_deployment(self, deployment_name: str):
        """Rollback deployment to previous version."""
        print("Rolling back deployment...")
        
        cmd = f"""
        {self.kubectl} rollout undo deployment/{deployment_name} 
        -n {self.namespace}
        """
        await self._run_command(cmd)
        
        # Wait for rollback to complete
        cmd = f"""
        {self.kubectl} rollout status deployment/{deployment_name} 
        -n {self.namespace} --timeout=300s
        """
        await self._run_command(cmd)
        
        print("Rollback completed")
    
    async def _run_command(self, cmd: str) -> str:
        """Execute shell command and return output."""
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Command failed: {stderr.decode()}")
        
        return stdout.decode()

# Usage
async def main():
    updater = RollingUpdateManager()
    await updater.update_deployment(
        "fastapi-deployment", 
        "your-registry/search-api:v1.2.0"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

## Environment Management

### Environment Configuration Strategy
```python
# config/environments.py
from enum import Enum
from typing import Dict, Any
from pydantic import BaseSettings

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class EnvironmentConfig(BaseSettings):
    """Base environment configuration."""
    
    # Environment identification
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    
    # Application settings
    app_name: str = "Search API"
    app_version: str = "1.0.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Elasticsearch settings
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_timeout: int = 30
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Security settings
    jwt_secret: str = "development-secret"
    jwt_expire_hours: int = 24
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"

class DevelopmentConfig(EnvironmentConfig):
    """Development environment configuration."""
    
    debug: bool = True
    log_level: str = "DEBUG"
    workers: int = 1
    
    # Development-specific settings
    auto_reload: bool = True
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]

class StagingConfig(EnvironmentConfig):
    """Staging environment configuration."""
    
    debug: bool = False
    log_level: str = "INFO"
    workers: int = 2
    
    # Staging-specific settings
    elasticsearch_host: str = "elasticsearch-staging"
    redis_host: str = "redis-staging"

class ProductionConfig(EnvironmentConfig):
    """Production environment configuration."""
    
    debug: bool = False
    log_level: str = "WARNING"
    workers: int = 4
    
    # Production-specific settings
    elasticsearch_host: str = "elasticsearch-cluster"
    redis_host: str = "redis-cluster"
    
    # Security hardening
    jwt_expire_hours: int = 8
    cors_origins: list = ["https://app.example.com"]

def get_config() -> EnvironmentConfig:
    """Get configuration based on environment."""
    import os
    
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "staging": StagingConfig,
        "production": ProductionConfig
    }
    
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()
```

### Environment-Specific Helm Charts
```yaml
# helm/values-production.yaml
replicaCount: 6

image:
  repository: your-registry/search-api
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: api.example.com
      paths: ["/"]
  tls:
    - secretName: api-tls
      hosts: ["api.example.com"]

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 6
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

env:
  ENVIRONMENT: "production"
  LOG_LEVEL: "WARNING"
  WORKERS: "4"
  ELASTICSEARCH_HOST: "elasticsearch-cluster"
  REDIS_HOST: "redis-cluster"

nodeSelector:
  node-type: "application"

tolerations:
  - key: "application"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app.kubernetes.io/name
            operator: In
            values: ["fastapi"]
        topologyKey: kubernetes.io/hostname
```

## Scaling Strategies

### Horizontal Pod Autoscaler
```yaml
# k8s/advanced-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-advanced-hpa
  namespace: search-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-deployment
  minReplicas: 3
  maxReplicas: 50
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  # Custom metrics (requests per second)
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "10"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Max
```

### Vertical Pod Autoscaler
```yaml
# k8s/vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: fastapi-vpa
  namespace: search-api
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-deployment
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: fastapi
      maxAllowed:
        cpu: 2
        memory: 4Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
      controlledResources: ["cpu", "memory"]
```

## Load Balancing

### Advanced Load Balancing with Istio
```yaml
# istio/virtual-service.yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: fastapi-vs
  namespace: search-api
spec:
  hosts:
  - api.example.com
  gateways:
  - fastapi-gateway
  http:
  # Canary deployment routing
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: fastapi-service
        subset: canary
      weight: 100
  # A/B testing routing
  - match:
    - headers:
        version:
          exact: "v2"
    route:
    - destination:
        host: fastapi-service
        subset: v2
  # Default routing with load balancing
  - route:
    - destination:
        host: fastapi-service
        subset: stable
      weight: 90
    - destination:
        host: fastapi-service
        subset: canary
      weight: 10
    fault:
      delay:
        percentage:
          value: 0.1
        fixedDelay: 5s
    retries:
      attempts: 3
      perTryTimeout: 30s

---
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: fastapi-dr
  namespace: search-api
spec:
  host: fastapi-service
  trafficPolicy:
    loadBalancer:
      consistentHash:
        httpHeaderName: "user-id"
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 10
    circuitBreaker:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
  - name: stable
    labels:
      version: stable
  - name: canary
    labels:
      version: canary
  - name: v2
    labels:
      version: v2
```

## Next Steps

1. **[CI/CD Integration](03_ci-cd-integration.md)** - Automated deployment pipelines
2. **[Operational Monitoring](04_operational-monitoring.md)** - Production monitoring and alerting
3. **[Performance Optimization](../06-production-patterns/03_performance-optimization.md)** - Scaling and efficiency

## Additional Resources

- **Kubernetes Documentation**: [kubernetes.io](https://kubernetes.io)
- **Docker Best Practices**: [docs.docker.com/develop/best-practices](https://docs.docker.com/develop/best-practices/)
- **Helm Charts**: [helm.sh](https://helm.sh)
- **Istio Service Mesh**: [istio.io](https://istio.io)