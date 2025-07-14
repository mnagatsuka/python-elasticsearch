# Installation & Setup

**Get Kibana 9.0 running in local and Docker environments**

*Estimated reading time: 25 minutes*

## Overview

This guide covers multiple approaches to installing and configuring Kibana 9.0, from quick Docker setups for development to production-ready configurations. We'll focus on getting you up and running quickly while understanding the key configuration options.

## 🐳 Docker Setup (Recommended for Learning)

### Quick Start with Docker Compose

**Prerequisites:**
- Docker Desktop installed and running
- At least 4GB RAM available for containers
- Available ports: 9200 (Elasticsearch), 5601 (Kibana)

**Step 1: Create Docker Compose Configuration**

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:9.0.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - elastic

  kibana:
    image: docker.elastic.co/kibana/kibana:9.0.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - SERVER_PUBLICBASEURL=http://localhost:5601
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

**Step 2: Start the Stack**

```bash
# Start all services
docker compose up -d

# View logs to ensure everything is starting correctly
docker compose logs -f

# Check service status
docker compose ps
```

**Step 3: Verify Installation**

```bash
# Test Elasticsearch
curl http://localhost:9200
# Expected output: JSON with cluster information

# Test Kibana (may take 30-60 seconds to start)
curl http://localhost:5601/api/status
# Expected output: JSON with overall status "green"
```

### Access Kibana

Open your browser and navigate to: `http://localhost:5601`

You should see the Kibana home screen with options to:
- Add integrations
- Upload data
- Explore sample data

## 💻 Local Installation

### System Requirements

**Minimum Requirements:**
- 2GB RAM available for Kibana
- 1GB disk space
- Java 11 or higher (for Elasticsearch)
- Modern web browser (Chrome, Firefox, Safari, Edge)

**Recommended for Development:**
- 4GB+ RAM
- 10GB+ disk space
- SSD for better performance

### Install on macOS

**Using Homebrew:**

```bash
# Install Elasticsearch first
brew tap elastic/tap
brew install elastic/tap/elasticsearch-full

# Install Kibana
brew install elastic/tap/kibana-full

# Start Elasticsearch
brew services start elastic/tap/elasticsearch-full

# Start Kibana
brew services start elastic/tap/kibana-full
```

**Manual Installation:**

```bash
# Download and extract Kibana
curl -O https://artifacts.elastic.co/downloads/kibana/kibana-9.0.0-darwin-x86_64.tar.gz
tar -xzf kibana-9.0.0-darwin-x86_64.tar.gz
cd kibana-9.0.0

# Start Kibana (Elasticsearch must be running first)
./bin/kibana
```

### Install on Linux

**Using Package Manager (Ubuntu/Debian):**

```bash
# Add Elastic repository
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/9.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-9.x.list

# Update package list
sudo apt update

# Install Kibana
sudo apt install kibana

# Enable and start service
sudo systemctl enable kibana
sudo systemctl start kibana
```

**Using Package Manager (CentOS/RHEL):**

```bash
# Add Elastic repository
sudo rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

# Create repository file
sudo tee /etc/yum.repos.d/elastic.repo << 'EOF'
[elastic-9.x]
name=Elastic repository for 9.x packages
baseurl=https://artifacts.elastic.co/packages/9.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF

# Install Kibana
sudo yum install kibana

# Enable and start service
sudo systemctl enable kibana
sudo systemctl start kibana
```

### Install on Windows

**Using ZIP Archive:**

```powershell
# Download Kibana (PowerShell)
Invoke-WebRequest -Uri "https://artifacts.elastic.co/downloads/kibana/kibana-9.0.0-windows-x86_64.zip" -OutFile "kibana-9.0.0.zip"

# Extract archive
Expand-Archive -Path "kibana-9.0.0.zip" -DestinationPath "C:\elastic\"

# Navigate to Kibana directory
cd "C:\elastic\kibana-9.0.0"

# Start Kibana (ensure Elasticsearch is running first)
.\bin\kibana.bat
```

## ⚙️ Configuration

### Basic Configuration File

The main configuration file is `kibana.yml`. Here are essential settings:

```yaml
# kibana.yml - Basic configuration

# Server configuration
server.port: 5601
server.host: "localhost"
server.publicBaseUrl: "http://localhost:5601"

# Elasticsearch connection
elasticsearch.hosts: ["http://localhost:9200"]

# Logging
logging.appenders.default:
  type: console
  layout:
    type: pattern
    pattern: "[%date][%level][%logger] %message"

logging.root:
  level: info
  appenders: [default]

# Kibana specific settings
kibana.index: ".kibana"
path.data: data

# Development settings
server.rewriteBasePath: false
xpack.encryptedSavedObjects.encryptionKey: "a-32-character-long-passphrase"
```

### Environment-Specific Configurations

**Development Environment:**

```yaml
# kibana-dev.yml
server.host: "0.0.0.0"  # Allow external connections
elasticsearch.hosts: ["http://localhost:9200"]
logging.root.level: debug
server.keepAliveTimeout: 60000
server.socketTimeout: 120000

# Enable all features for testing
xpack.canvas.enabled: true
xpack.lens.enabled: true
xpack.maps.enabled: true
xpack.ml.enabled: false  # Disable ML to reduce resource usage
```

**Production Environment:**

```yaml
# kibana-prod.yml
server.host: "0.0.0.0"
server.publicBaseUrl: "https://your-kibana-domain.com"
elasticsearch.hosts: ["https://es-node1:9200", "https://es-node2:9200"]

# Security settings
xpack.security.enabled: true
elasticsearch.username: "kibana_system"
elasticsearch.password: "${KIBANA_PASSWORD}"

# SSL configuration
server.ssl.enabled: true
server.ssl.certificate: "/path/to/kibana.crt"
server.ssl.key: "/path/to/kibana.key"

# Performance settings
server.maxPayload: 1048576
elasticsearch.requestTimeout: 30000
elasticsearch.shardTimeout: 30000

# Monitoring
xpack.monitoring.enabled: true
```

### Security Configuration

**Enable Basic Security:**

```yaml
# In kibana.yml
xpack.security.enabled: true
elasticsearch.username: "kibana_system"
elasticsearch.password: "your-secure-password"

# Optional: Configure session settings
xpack.security.session.idleTimeout: "1h"
xpack.security.session.lifespan: "7d"
```

**Set up Elasticsearch Security:**

```bash
# In Elasticsearch directory, set passwords
bin/elasticsearch-setup-passwords interactive

# Or use the auto setup
bin/elasticsearch-setup-passwords auto
```

## 🔧 Environment Variables

### Docker Environment Variables

```bash
# Essential Kibana environment variables
ELASTICSEARCH_HOSTS=http://elasticsearch:9200
SERVER_PUBLICBASEURL=http://localhost:5601
KIBANA_SYSTEM_PASSWORD=your-password

# Advanced settings
SERVER_MAXPAYLOAD=1048576
ELASTICSEARCH_REQUESTTIMEOUT=30000
LOGGING_ROOT_LEVEL=info

# Security settings
XPACK_SECURITY_ENABLED=true
XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY=your-32-char-key
```

### System Environment Variables

```bash
# For local installations
export KIBANA_HOME=/usr/share/kibana
export KIBANA_PATH_CONF=/etc/kibana
export KIBANA_PATH_DATA=/var/lib/kibana
export KIBANA_PATH_LOGS=/var/log/kibana

# Node.js settings for Kibana
export NODE_OPTIONS="--max-old-space-size=4096"
```

## 📊 Verification and Testing

### Health Checks

**Check Kibana Status:**

```bash
# Basic connectivity
curl http://localhost:5601/api/status

# Detailed status
curl http://localhost:5601/api/status?v7format=true | jq .

# Check specific components
curl http://localhost:5601/api/status | jq '.status.overall.state'
```

**Expected Response:**
```json
{
  "name": "kibana",
  "uuid": "...",
  "version": {
    "number": "9.0.0",
    "build_hash": "...",
    "build_number": 12345,
    "build_snapshot": false
  },
  "status": {
    "overall": {
      "state": "green",
      "title": "Green",
      "nickname": "Looking good",
      "icon": "success"
    }
  }
}
```

### Troubleshooting Common Issues

**Issue: Kibana won't start**

```bash
# Check logs
docker compose logs kibana

# Or for local installation
tail -f /var/log/kibana/kibana.log

# Common causes:
# 1. Elasticsearch not running or not accessible
# 2. Port 5601 already in use
# 3. Insufficient memory
# 4. Configuration errors
```

**Issue: Cannot connect to Elasticsearch**

```bash
# Test Elasticsearch connectivity from Kibana container
docker exec -it kibana curl http://elasticsearch:9200

# Check network connectivity
docker network ls
docker network inspect <network_name>

# Verify Elasticsearch is healthy
curl http://localhost:9200/_cluster/health
```

**Issue: Permission denied errors**

```bash
# Fix file permissions (Linux/macOS)
sudo chown -R kibana:kibana /var/lib/kibana
sudo chown -R kibana:kibana /var/log/kibana

# For Docker volumes
docker compose down
docker volume rm <volume_name>
docker compose up -d
```

## 🚀 Sample Data Setup

### Load Sample Data

Once Kibana is running, you can load sample datasets:

1. **Navigate to Kibana Home** (`http://localhost:5601`)
2. **Click "Try sample data"**
3. **Choose from available datasets:**
   - **Sample eCommerce orders** - Retail analytics
   - **Sample flight data** - Travel and logistics
   - **Sample web logs** - Web analytics

```bash
# Or load sample data via API
curl -X POST "localhost:5601/api/sample_data/ecommerce"
curl -X POST "localhost:5601/api/sample_data/flights"
curl -X POST "localhost:5601/api/sample_data/logs"
```

### Verify Sample Data

```bash
# Check loaded indices
curl http://localhost:9200/_cat/indices?v

# Expected output should include:
# kibana_sample_data_ecommerce
# kibana_sample_data_flights  
# kibana_sample_data_logs
```

## 🔧 Performance Tuning

### Optimize for Development

```yaml
# kibana.yml settings for better development experience
server.maxPayload: 1048576
elasticsearch.requestTimeout: 30000
elasticsearch.pingTimeout: 3000

# Reduce resource usage
xpack.monitoring.enabled: false
xpack.ml.enabled: false
xpack.reporting.enabled: false
```

### Memory Configuration

```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"

# For Docker
services:
  kibana:
    environment:
      - NODE_OPTIONS=--max-old-space-size=4096
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

## 🔗 Next Steps

Now that Kibana is installed and running:

1. **Explore the Interface** → [Interface Navigation](interface-navigation.md)
2. **Connect Your Data** → [Data Views & Index Patterns](../02-data-views-discovery/data-views-index-patterns.md)
3. **Create First Visualization** → [Kibana Lens Basics](../03-visualization-fundamentals/kibana-lens-basics.md)

## 📚 Quick Reference

### Essential Commands

```bash
# Docker management
docker compose up -d          # Start services
docker compose down           # Stop services
docker compose logs kibana    # View Kibana logs
docker compose restart kibana # Restart Kibana

# Service management (Linux)
sudo systemctl start kibana    # Start Kibana
sudo systemctl stop kibana     # Stop Kibana
sudo systemctl status kibana   # Check status
sudo systemctl restart kibana  # Restart Kibana

# Configuration files
/etc/kibana/kibana.yml         # Main config (Linux)
./config/kibana.yml            # Main config (manual install)
```

### Important URLs

- **Kibana Home**: `http://localhost:5601`
- **Dev Tools**: `http://localhost:5601/app/dev_tools`
- **Status API**: `http://localhost:5601/api/status`
- **Sample Data**: `http://localhost:5601/app/home#/tutorial_directory/sampleData`

With Kibana successfully installed, you're ready to begin exploring data visualization and analytics!