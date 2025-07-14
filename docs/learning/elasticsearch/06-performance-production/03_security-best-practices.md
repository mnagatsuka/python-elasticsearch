# Security Best Practices

**Protect your Elasticsearch deployment with comprehensive security measures**

*Estimated reading time: 25 minutes*

## Overview

Security is paramount for production Elasticsearch deployments. This guide covers authentication, authorization, encryption, network security, and compliance best practices for securing your Elasticsearch cluster and data.

## 📋 Table of Contents

1. [Security Fundamentals](#security-fundamentals)
2. [Authentication & Authorization](#authentication--authorization)
3. [Encryption](#encryption)
4. [Network Security](#network-security)
5. [Data Protection](#data-protection)
6. [Compliance & Auditing](#compliance--auditing)
7. [Security Monitoring](#security-monitoring)

## 🔐 Security Fundamentals

### Security Architecture

```
External Network → Firewall → Load Balancer → Elasticsearch Cluster
                                    ↓
                          Authentication & Authorization
                                    ↓
                            Encrypted Communication
                                    ↓
                              Secure Storage
```

### Security Layers

1. **Network Security** - Firewalls, VPNs, network segmentation
2. **Transport Security** - TLS/SSL encryption in transit
3. **Authentication** - User identity verification
4. **Authorization** - Role-based access control
5. **Data Security** - Encryption at rest and field-level security
6. **Audit Logging** - Security event monitoring

## 🔑 Authentication & Authorization

### Enable X-Pack Security

**Basic Security Configuration:**
```yaml
# elasticsearch.yml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true

# Generate certificates
bin/elasticsearch-certutil ca
bin/elasticsearch-certutil cert --ca elastic-stack-ca.p12
```

### User Management

**Create Admin User:**
```bash
# Set built-in user passwords
bin/elasticsearch-setup-passwords interactive

# Create custom user
curl -X POST "localhost:9200/_security/user/admin" -H 'Content-Type: application/json' -d'
{
  "password": "strong_password_123!",
  "roles": ["superuser"],
  "full_name": "Administrator",
  "email": "admin@company.com"
}
'
```

**Built-in Users:**
- `elastic` - Superuser with all privileges
- `kibana_system` - Kibana server user
- `logstash_system` - Logstash service user
- `beats_system` - Beats service user
- `apm_system` - APM server user
- `remote_monitoring_user` - Monitoring user

### Role-Based Access Control (RBAC)

**Create Custom Roles:**
```bash
# Read-only role for analysts
curl -X POST "localhost:9200/_security/role/analyst" -H 'Content-Type: application/json' -d'
{
  "cluster": ["monitor"],
  "indices": [
    {
      "names": ["logs-*", "metrics-*"],
      "privileges": ["read", "view_index_metadata"]
    }
  ]
}
'

# Write role for applications
curl -X POST "localhost:9200/_security/role/app_writer" -H 'Content-Type: application/json' -d'
{
  "cluster": ["monitor"],
  "indices": [
    {
      "names": ["app-*"],
      "privileges": ["create", "index", "read", "view_index_metadata"]
    }
  ]
}
'

# Admin role for DevOps
curl -X POST "localhost:9200/_security/role/devops_admin" -H 'Content-Type: application/json' -d'
{
  "cluster": ["all"],
  "indices": [
    {
      "names": ["*"],
      "privileges": ["all"]
    }
  ],
  "applications": [
    {
      "application": "kibana-.kibana",
      "privileges": ["all"],
      "resources": ["*"]
    }
  ]
}
'
```

**Index-level Security:**
```bash
# Restrict access to sensitive indices
curl -X POST "localhost:9200/_security/role/hr_access" -H 'Content-Type: application/json' -d'
{
  "cluster": [],
  "indices": [
    {
      "names": ["hr-*"],
      "privileges": ["read"],
      "query": {
        "term": {
          "department": "human_resources"
        }
      }
    }
  ]
}
'
```

### API Key Authentication

**Create API Keys:**
```bash
# Create API key for application
curl -X POST "localhost:9200/_security/api_key" -H 'Content-Type: application/json' -d'
{
  "name": "my-api-key",
  "role_descriptors": {
    "app_role": {
      "cluster": ["monitor"],
      "indices": [
        {
          "names": ["app-*"],
          "privileges": ["create", "index", "read"]
        }
      ]
    }
  },
  "expiration": "1d"
}
'

# Use API key in requests
curl -H "Authorization: ApiKey <base64(id:api_key)>" "localhost:9200/_cluster/health"
```

## 🔒 Encryption

### Transport Layer Security (TLS)

**Configure TLS for HTTP:**
```yaml
# elasticsearch.yml
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.keystore.path: certs/elastic-certificates.p12
xpack.security.http.ssl.truststore.path: certs/elastic-certificates.p12
```

**Configure TLS for Transport:**
```yaml
# elasticsearch.yml
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.keystore.path: certs/elastic-certificates.p12
xpack.security.transport.ssl.truststore.path: certs/elastic-certificates.p12
```

### Encryption at Rest

**Enable Encryption at Rest:**
```yaml
# elasticsearch.yml
xpack.security.encryptionKey.type: keystore
path.data: /encrypted/elasticsearch/data

# File system encryption
# Use LUKS (Linux) or FileVault (macOS) or BitLocker (Windows)
```

**Field-level Security:**
```bash
# Create role with field-level security
curl -X POST "localhost:9200/_security/role/limited_access" -H 'Content-Type: application/json' -d'
{
  "indices": [
    {
      "names": ["users"],
      "privileges": ["read"],
      "field_security": {
        "grant": ["name", "email", "department"],
        "except": ["ssn", "salary", "personal_data"]
      }
    }
  ]
}
'
```

### Document-level Security

**Implement Document-level Security:**
```bash
# Restrict documents based on user attributes
curl -X POST "localhost:9200/_security/role/regional_access" -H 'Content-Type: application/json' -d'
{
  "indices": [
    {
      "names": ["sales-*"],
      "privileges": ["read"],
      "query": {
        "term": {
          "region": "{{_user.metadata.region}}"
        }
      }
    }
  ]
}
'

# Create user with metadata
curl -X POST "localhost:9200/_security/user/regional_user" -H 'Content-Type: application/json' -d'
{
  "password": "secure_password",
  "roles": ["regional_access"],
  "metadata": {
    "region": "north_america"
  }
}
'
```

## 🌐 Network Security

### Firewall Configuration

**Elasticsearch Ports:**
```bash
# Required ports
9200  # HTTP API
9300  # Transport layer

# Firewall rules (iptables example)
iptables -A INPUT -p tcp --dport 9200 -s <trusted_network> -j ACCEPT
iptables -A INPUT -p tcp --dport 9300 -s <cluster_network> -j ACCEPT
iptables -A INPUT -p tcp --dport 9200 -j DROP
iptables -A INPUT -p tcp --dport 9300 -j DROP
```

### Network Segmentation

**Production Network Layout:**
```
Internet → WAF → Load Balancer (DMZ) → Elasticsearch Cluster (Private Network)
            ↓
       Kibana (DMZ) ← → Elasticsearch (Private)
            ↓
    Application Servers ← → Elasticsearch (Private)
```

### IP Filtering

**Configure IP Filtering:**
```yaml
# elasticsearch.yml
xpack.security.transport.filter.allow: "192.168.1.0/24"
xpack.security.transport.filter.deny: "_all"
xpack.security.http.filter.allow: "10.0.0.0/8"
xpack.security.http.filter.deny: "_all"
```

### Reverse Proxy Configuration

**Nginx Configuration:**
```nginx
server {
    listen 443 ssl;
    server_name elasticsearch.company.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=es_limit:10m rate=10r/s;
    limit_req zone=es_limit burst=20 nodelay;
    
    # Basic auth at proxy level
    auth_basic "Elasticsearch Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    location / {
        proxy_pass http://elasticsearch-backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

upstream elasticsearch-backend {
    server 10.0.1.10:9200;
    server 10.0.1.11:9200;
    server 10.0.1.12:9200;
}
```

## 🛡️ Data Protection

### Sensitive Data Handling

**Data Classification:**
```bash
# Index template with data classification
curl -X PUT "localhost:9200/_index_template/sensitive_data" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["sensitive-*"],
  "template": {
    "settings": {
      "index.number_of_replicas": 2,
      "index.auto_expand_replicas": false
    },
    "mappings": {
      "properties": {
        "data_classification": {
          "type": "keyword",
          "value": "sensitive"
        },
        "retention_period": {
          "type": "keyword"
        }
      }
    }
  }
}
'
```

### Data Masking

**Implement Data Masking:**
```bash
# Ingest pipeline for data masking
curl -X PUT "localhost:9200/_ingest/pipeline/data_masking" -H 'Content-Type: application/json' -d'
{
  "description": "Mask sensitive data",
  "processors": [
    {
      "script": {
        "source": """
          if (ctx.email != null) {
            String email = ctx.email;
            int atIndex = email.indexOf('@');
            if (atIndex > 0) {
              String username = email.substring(0, atIndex);
              String domain = email.substring(atIndex);
              String maskedUsername = username.substring(0, Math.min(2, username.length())) + "***";
              ctx.email_masked = maskedUsername + domain;
            }
          }
          
          if (ctx.phone != null) {
            String phone = ctx.phone.replaceAll("\\D", "");
            if (phone.length() >= 10) {
              ctx.phone_masked = phone.substring(0, 3) + "-***-" + phone.substring(phone.length() - 4);
            }
          }
        """
      }
    }
  ]
}
'
```

### Backup Security

**Secure Snapshots:**
```bash
# Create secure repository
curl -X PUT "localhost:9200/_snapshot/secure_backup" -H 'Content-Type: application/json' -d'
{
  "type": "s3",
  "settings": {
    "bucket": "elasticsearch-backups",
    "region": "us-east-1",
    "server_side_encryption": true,
    "storage_class": "standard_ia",
    "access_key": "AKIA...",
    "secret_key": "...",
    "compress": true
  }
}
'

# Create encrypted snapshot
curl -X PUT "localhost:9200/_snapshot/secure_backup/encrypted_snapshot" -H 'Content-Type: application/json' -d'
{
  "indices": "sensitive-*",
  "include_global_state": false,
  "metadata": {
    "encryption": "enabled",
    "retention": "7_years"
  }
}
'
```

## 📊 Compliance & Auditing

### Audit Logging

**Enable Audit Logging:**
```yaml
# elasticsearch.yml
xpack.security.audit.enabled: true
xpack.security.audit.outputs: [index, logfile]
xpack.security.audit.logfile.events.emit_request_body: true

# Audit events to log
xpack.security.audit.logfile.events.include:
  - access_granted
  - access_denied
  - anonymous_access_denied
  - authentication_failed
  - connection_granted
  - connection_denied
  - tampered_request
  - run_as_granted
  - run_as_denied
```

**Custom Audit Filtering:**
```yaml
# elasticsearch.yml
xpack.security.audit.logfile.events.ignore_filters:
  - users: ["kibana", "logstash_system"]
    actions: ["indices:data/read/*"]
  - indices: ["system-*"]
    actions: ["indices:data/write/*"]
```

### GDPR Compliance

**Data Subject Rights Implementation:**
```bash
# Data deletion (Right to be forgotten)
curl -X POST "localhost:9200/users/_delete_by_query" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "user_id": "gdpr_deletion_request_123"
    }
  }
}
'

# Data export (Right to data portability)
curl -X POST "localhost:9200/users/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "user_id": "data_export_request_456"
    }
  },
  "_source": {
    "excludes": ["internal_*", "system_*"]
  }
}
'
```

### Data Retention Policies

**Automated Data Retention:**
```bash
# Create retention policy
curl -X PUT "localhost:9200/_ilm/policy/gdpr_retention" -H 'Content-Type: application/json' -d'
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_age": "30d",
            "max_size": "50gb"
          }
        }
      },
      "warm": {
        "min_age": "30d",
        "actions": {
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "cold": {
        "min_age": "90d",
        "actions": {
          "allocate": {
            "include": {
              "_tier_preference": "data_cold"
            }
          }
        }
      },
      "delete": {
        "min_age": "2555d"  // 7 years for compliance
      }
    }
  }
}
'
```

## 📈 Security Monitoring

### Security Analytics

**Monitor Security Events:**
```bash
# Search for failed authentications
curl -X POST "localhost:9200/.security-audit-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event_type": "authentication_failed"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "aggs": {
    "failed_by_user": {
      "terms": {"field": "user.name"}
    },
    "failed_by_ip": {
      "terms": {"field": "origin.address"}
    }
  }
}
'

# Monitor privilege escalation attempts
curl -X POST "localhost:9200/.security-audit-*/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "bool": {
      "must": [
        {"term": {"event_type": "access_denied"}},
        {"term": {"request.action": "cluster:admin/*"}}
      ]
    }
  }
}
'
```

### Security Alerting

**Watcher Security Alerts:**
```bash
# Brute force detection
curl -X PUT "localhost:9200/_watcher/watch/brute_force_detection" -H 'Content-Type: application/json' -d'
{
  "trigger": {
    "schedule": {"interval": "1m"}
  },
  "input": {
    "search": {
      "request": {
        "indices": [".security-audit-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {"term": {"event_type": "authentication_failed"}},
                {"range": {"@timestamp": {"gte": "now-5m"}}}
              ]
            }
          },
          "aggs": {
            "by_ip": {
              "terms": {"field": "origin.address", "min_doc_count": 5}
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.aggregations.by_ip.buckets.0.doc_count": {"gt": 10}
    }
  },
  "actions": {
    "send_email": {
      "email": {
        "to": ["security@company.com"],
        "subject": "Brute Force Attack Detected",
        "body": "Multiple failed login attempts detected from IP: {{ctx.payload.aggregations.by_ip.buckets.0.key}}"
      }
    }
  }
}
'

# Privilege escalation alert
curl -X PUT "localhost:9200/_watcher/watch/privilege_escalation" -H 'Content-Type: application/json' -d'
{
  "trigger": {
    "schedule": {"interval": "30s"}
  },
  "input": {
    "search": {
      "request": {
        "indices": [".security-audit-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {"term": {"event_type": "access_denied"}},
                {"wildcard": {"request.action": "cluster:admin/*"}},
                {"range": {"@timestamp": {"gte": "now-1m"}}}
              ]
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": {"ctx.payload.hits.total": {"gt": 0}}
  },
  "actions": {
    "notify_security_team": {
      "email": {
        "to": ["security@company.com"],
        "subject": "Privilege Escalation Attempt",
        "body": "Unauthorized admin access attempt detected"
      }
    }
  }
}
'
```

### Security Dashboards

**Kibana Security Dashboard:**
```json
{
  "title": "Security Monitoring Dashboard",
  "visualizations": [
    {
      "name": "Authentication Events",
      "type": "histogram",
      "query": "event_type:(authentication_success OR authentication_failed)"
    },
    {
      "name": "Failed Login Attempts by IP",
      "type": "pie_chart",
      "query": "event_type:authentication_failed",
      "aggregation": "terms",
      "field": "origin.address"
    },
    {
      "name": "Privilege Escalation Attempts",
      "type": "data_table",
      "query": "event_type:access_denied AND request.action:cluster\\:admin*"
    }
  ]
}
```

## 🔧 Security Hardening Checklist

### Production Security Checklist

- [ ] **Enable X-Pack Security** with strong passwords
- [ ] **Configure TLS/SSL** for all communications
- [ ] **Implement RBAC** with least privilege principle
- [ ] **Enable audit logging** for all security events
- [ ] **Configure firewall rules** and network segmentation
- [ ] **Set up API key authentication** for applications
- [ ] **Implement field-level security** for sensitive data
- [ ] **Configure secure snapshots** with encryption
- [ ] **Set up security monitoring** and alerting
- [ ] **Regular security updates** and patches
- [ ] **Backup encryption keys** securely
- [ ] **Document security procedures** and incident response
- [ ] **Regular security assessments** and penetration testing
- [ ] **User access reviews** and privilege audits

### Configuration Validation

**Security Health Check Script:**
```bash
#!/bin/bash

ES_HOST="localhost:9200"

echo "=== Elasticsearch Security Health Check ==="

# Check if security is enabled
SECURITY_ENABLED=$(curl -s "$ES_HOST" | jq -r '.tagline' | grep -c "security")
echo "Security enabled: $SECURITY_ENABLED"

# Check TLS configuration
TLS_ENABLED=$(curl -k -s "https://$ES_HOST" | jq -r '.cluster_name' >/dev/null 2>&1 && echo "1" || echo "0")
echo "TLS enabled: $TLS_ENABLED"

# Check for default passwords
DEFAULT_PASSWORDS=$(curl -s -u elastic:changeme "$ES_HOST/_cluster/health" >/dev/null 2>&1 && echo "1" || echo "0")
echo "Default passwords detected: $DEFAULT_PASSWORDS"

# Check audit logging
AUDIT_ENABLED=$(curl -s "$ES_HOST/_cat/indices/.security-audit*" | wc -l)
echo "Audit indices: $AUDIT_ENABLED"

echo "=== Security Health Check Complete ==="
```

## 🔗 Next Steps

You've now learned comprehensive security practices for Elasticsearch. To continue your learning:

1. **[Monitoring & Operations](02_monitoring-operations.md)** - Monitor security events and alerts
2. **[Index Management](index-management.md)** - Secure index lifecycle policies
3. **[Troubleshooting](troubleshooting.md)** - Debug security-related issues

## 📚 Key Takeaways

- ✅ **Enable X-Pack Security** in all production environments
- ✅ **Use strong authentication** with API keys and RBAC
- ✅ **Encrypt all communications** with TLS/SSL
- ✅ **Implement network security** with firewalls and segmentation
- ✅ **Protect sensitive data** with field-level security and masking
- ✅ **Enable comprehensive auditing** for compliance and monitoring
- ✅ **Monitor security events** with real-time alerting
- ✅ **Follow security hardening** best practices and checklists
- ✅ **Regular security reviews** and updates
- ✅ **Document all procedures** for incident response

Security is an ongoing process - stay updated with the latest Elasticsearch security features and best practices!