# Installation & Setup

**Get Elasticsearch running in your development environment**

*Estimated reading time: 20 minutes*

## Overview

This guide will help you set up Elasticsearch for development and learning. We'll cover multiple installation methods, from Docker (recommended for beginners) to local installation for advanced users.

## 🐳 Docker Setup (Recommended)

**Easiest way to get started with Elasticsearch**

### Prerequisites
- Docker installed on your system
- Docker Compose (usually included with Docker)
- At least 4GB of RAM available

### Quick Start with This Project

This project includes a complete Docker setup with Elasticsearch 9.0.2 LTS:

```bash
# Clone this repository (if you haven't already)
git clone <repository-url>
cd python-elasticsearch

# Start all services
docker compose up -d

# Verify Elasticsearch is running
curl http://localhost:9200
```

### Services Included
- **Elasticsearch 9.0.2**: `http://localhost:9200`
- **Kibana 9.0.2**: `http://localhost:5601`
- **FastAPI**: `http://localhost:8000`

### Manual Docker Setup

If you want to set up Elasticsearch Docker manually:

```yaml
# docker-compose.yml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:9.0.2
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - elastic

  kibana:
    image: kibana:9.0.2
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
    driver: local

networks:
  elastic:
    driver: bridge
```

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs elasticsearch
```

## 🖥️ Local Installation

**For advanced users who prefer local installation**

### macOS Installation

**Using Homebrew:**
```bash
# Install Elasticsearch
brew install elasticsearch

# Start Elasticsearch
brew services start elasticsearch

# Stop Elasticsearch
brew services stop elasticsearch
```

**Manual Installation:**
```bash
# Download Elasticsearch
curl -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-9.0.2-darwin-x86_64.tar.gz

# Extract
tar -xzf elasticsearch-9.0.2-darwin-x86_64.tar.gz

# Navigate to directory
cd elasticsearch-9.0.2

# Start Elasticsearch
./bin/elasticsearch
```

### Linux Installation

**Using APT (Debian/Ubuntu):**
```bash
# Import GPG key
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -

# Add repository
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-8.x.list

# Update and install
sudo apt-get update
sudo apt-get install elasticsearch

# Start service
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

**Manual Installation:**
```bash
# Download
curl -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-9.0.2-linux-x86_64.tar.gz

# Extract
tar -xzf elasticsearch-9.0.2-linux-x86_64.tar.gz

# Start
cd elasticsearch-9.0.2
./bin/elasticsearch
```

### Windows Installation

**Using ZIP:**
```powershell
# Download from https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-9.0.2-windows-x86_64.zip

# Extract to C:\elasticsearch

# Start Elasticsearch
C:\elasticsearch\bin\elasticsearch.bat
```

## ⚙️ Configuration

### Basic Configuration

**For Docker:** Configuration is handled through environment variables in docker-compose.yml

**For Local Installation:** Edit `config/elasticsearch.yml`:

```yaml
# config/elasticsearch.yml

# Cluster name
cluster.name: my-cluster

# Node name
node.name: node-1

# Network settings
network.host: localhost
http.port: 9200

# Discovery settings (for single node)
discovery.type: single-node

# Security settings (for development)
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false

# Memory settings
path.data: /usr/share/elasticsearch/data
path.logs: /usr/share/elasticsearch/logs
```

### Memory Configuration

**Docker:**
```yaml
environment:
  - ES_JAVA_OPTS=-Xms1g -Xmx1g  # 1GB heap
```

**Local:**
```bash
# Edit config/jvm.options
-Xms1g  # Initial heap size
-Xmx1g  # Maximum heap size
```

### Production vs Development Settings

**Development Settings:**
```yaml
# Quick startup, no security
discovery.type: single-node
xpack.security.enabled: false
xpack.ml.enabled: false
```

**Production Settings:**
```yaml
# Cluster mode, security enabled
discovery.seed_hosts: ["host1", "host2"]
cluster.initial_master_nodes: ["node-1", "node-2"]
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
```

## 🔧 Verification

### Check Installation

```bash
# Test Elasticsearch is running
curl http://localhost:9200

# Expected response:
{
  "name" : "node-1",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "uuid-here",
  "version" : {
    "number" : "9.0.2",
    "build_flavor" : "default",
    "build_type" : "docker",
    "build_hash" : "hash-here",
    "build_date" : "2025-05-28T10:06:37.834829258Z",
    "build_snapshot" : false,
    "lucene_version" : "10.1.0",
    "minimum_wire_compatibility_version" : "8.18.0",
    "minimum_index_compatibility_version" : "8.0.0"
  },
  "tagline" : "You Know, for Search"
}
```

### Check Cluster Health

```bash
# Check cluster health
curl http://localhost:9200/_cluster/health?pretty

# Expected response:
{
  "cluster_name" : "elasticsearch",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 1,
  "number_of_data_nodes" : 1,
  "active_primary_shards" : 0,
  "active_shards" : 0,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0,
  "task_max_waiting_in_queue_millis" : 0,
  "active_shards_percent_as_number" : 100.0
}
```

### Check Node Information

```bash
# Check node info
curl http://localhost:9200/_nodes?pretty

# Check indices
curl http://localhost:9200/_cat/indices?v

# Check shards
curl http://localhost:9200/_cat/shards?v
```

## 🛠️ Development Tools

### Command Line Tools

**HTTPie (recommended for API testing):**
```bash
# Install HTTPie
pip install httpie

# Or using brew
brew install httpie

# Test with HTTPie
http GET localhost:9200
```

**curl (built-in):**
```bash
# Basic curl examples
curl -X GET "localhost:9200/"
curl -X GET "localhost:9200/_cluster/health"
curl -X GET "localhost:9200/_cat/indices?v"
```

### Browser Tools

**Kibana Dev Tools:**
1. Open Kibana at `http://localhost:5601`
2. Navigate to **Management > Dev Tools**
3. Use the console for interactive queries

**Postman:**
- Import Elasticsearch collection
- Set base URL to `http://localhost:9200`
- Create requests for common operations

### Code Editors

**VS Code Extensions:**
- Elasticsearch for VS Code
- REST Client
- JSON Tools

## 🐍 Client Libraries

### Python Client

```bash
# Install official Python client
pip install elasticsearch

# Or using this project's environment
uv add elasticsearch
```

```python
from elasticsearch import Elasticsearch

# Connect to Elasticsearch
es = Elasticsearch(
    hosts=['http://localhost:9200'],
    verify_certs=False,
    ssl_show_warn=False
)

# Test connection
info = es.info()
print(f"Connected to Elasticsearch {info['version']['number']}")
```

### JavaScript Client

```bash
# Install Node.js client
npm install @elastic/elasticsearch
```

```javascript
const { Client } = require('@elastic/elasticsearch');

const client = new Client({
  node: 'http://localhost:9200'
});

// Test connection
client.info().then(response => {
  console.log(`Connected to Elasticsearch ${response.body.version.number}`);
});
```

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using port 9200
lsof -i :9200

# Kill process if needed
sudo kill -9 <PID>
```

**Memory Issues:**
```bash
# Check available memory
free -h

# Reduce heap size in docker-compose.yml
ES_JAVA_OPTS=-Xms512m -Xmx512m
```

**Permission Errors (Linux):**
```bash
# Fix data directory permissions
sudo chown -R 1000:1000 /usr/share/elasticsearch/data
```

**Connection Refused:**
```bash
# Check if Elasticsearch is running
docker ps
# or
ps aux | grep elasticsearch

# Check logs
docker logs elasticsearch
```

### Docker-specific Issues

**Container Won't Start:**
```bash
# Check logs
docker logs elasticsearch

# Common solutions:
# 1. Increase Docker memory allocation (4GB minimum)
# 2. Check disk space
# 3. Remove old containers: docker system prune
```

**Data Persistence:**
```bash
# Backup data
docker cp elasticsearch:/usr/share/elasticsearch/data ./backup

# Restore data
docker cp ./backup elasticsearch:/usr/share/elasticsearch/data
```

## 📊 Monitoring Setup

### Basic Monitoring

```bash
# Monitor cluster stats
watch -n 5 'curl -s http://localhost:9200/_cluster/stats?pretty'

# Monitor node stats
curl http://localhost:9200/_nodes/stats?pretty

# Monitor index stats
curl http://localhost:9200/_stats?pretty
```

### Kibana Monitoring

1. Open Kibana at `http://localhost:5601`
2. Navigate to **Stack Monitoring**
3. Enable monitoring for cluster health

## 🔒 Security Considerations

### Development Security

**Current setup (development only):**
```yaml
# Security disabled for easy development
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false
```

**⚠️ Warning:** Never use these settings in production!

### Production Security

For production deployments:
```yaml
# Enable security
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true

# Set passwords
xpack.security.authc.realms.native.native1.order: 0
```

## 🎯 Performance Tuning

### Development Optimization

```yaml
# Faster startup for development
bootstrap.memory_lock: false
discovery.type: single-node
action.destructive_requires_name: false

# Reduced resource usage
ES_JAVA_OPTS: -Xms512m -Xmx512m
```

### Resource Requirements

**Minimum (Development):**
- RAM: 2GB
- CPU: 2 cores
- Disk: 10GB

**Recommended (Development):**
- RAM: 4GB
- CPU: 4 cores
- Disk: 50GB SSD

## 🔗 Next Steps

Now that you have Elasticsearch running, let's start interacting with it:

1. **[Basic API Interactions](basic-api-interactions.md)** - Your first Elasticsearch commands
2. **[Document Operations](../02-data-management/document-operations.md)** - Learn CRUD operations
3. **[Search Fundamentals](../03-search-fundamentals/query-dsl-basics.md)** - Start searching data

## 📚 Key Takeaways

- ✅ **Docker is recommended** for development and learning
- ✅ **This project includes** a complete Docker setup
- ✅ **Verify installation** with simple curl commands
- ✅ **Use appropriate settings** for development vs production
- ✅ **Install client libraries** for your preferred language
- ✅ **Monitor your cluster** from the beginning
- ✅ **Security is disabled** in development setup (enable for production)

Ready to start using Elasticsearch? Continue with [Basic API Interactions](basic-api-interactions.md) to learn your first commands!