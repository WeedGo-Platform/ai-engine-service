# AGI System Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the AGI system to production.

## Prerequisites

### System Requirements
- Python 3.8+
- PostgreSQL 13+
- 16GB+ RAM (32GB recommended)
- 100GB+ disk space for models
- GPU optional but recommended for better performance

### Required Services
- PostgreSQL database
- Redis (optional, for caching)
- Monitoring service (Prometheus/Grafana recommended)

## Pre-Deployment Checklist

### 1. Environment Configuration

Create a `.env.production` file:

```bash
# Environment
AGI_ENVIRONMENT=production

# Database
DATABASE_HOST=your-db-host
DATABASE_PORT=5432
DATABASE_NAME=agi_production
DATABASE_USER=agi_user
DATABASE_PASSWORD=secure-password
DATABASE_POOL_SIZE=20

# Security
JWT_SECRET_KEY=your-secure-jwt-secret-key-here
API_KEY_SECRET=your-api-key-secret

# API Configuration
API_PORT=5024
API_HOST=0.0.0.0
CORS_ORIGINS=["https://your-domain.com"]

# Model Configuration
MODEL_PATH=/opt/agi/models
DEFAULT_MODEL=llama_3_1_8b_instruct_q4_k_m
FALLBACK_MODEL=tinyllama_1_1b_chat_v1_0_q4_k_m

# Service Flags
ENABLE_RAG=true
ENABLE_MEMORY=true
ENABLE_TOOLS=true
ENABLE_ANALYTICS=true

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

### 2. Database Setup

Run database migrations:

```bash
cd /path/to/agi/backend
python3 agi/migrations/run_migrations.py
```

Verify tables:

```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'agi';
```

### 3. Model Installation

Download required models:

```bash
python3 agi/models/download_models.py --production
```

Verify models:

```bash
python3 -c "from agi.models.registry import get_model_registry; import asyncio; asyncio.run(get_model_registry().list_models())"
```

### 4. Security Configuration

#### Generate secure keys:

```bash
# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate API key secret
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### Set up SSL/TLS:

- Configure reverse proxy (nginx/Apache)
- Install SSL certificates
- Enable HTTPS only

### 5. Production Checks

Run the production readiness checker:

```bash
cd agi/deployment
python3 production_checklist.py
```

All checks should pass before deployment.

## Deployment Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt --no-cache-dir
```

### 2. Build and Optimize

```bash
# Compile Python files
python3 -m compileall agi/

# Optimize imports
python3 -m py_compile agi/**/*.py
```

### 3. Start Services

#### Using systemd (recommended):

Create `/etc/systemd/system/agi.service`:

```ini
[Unit]
Description=AGI API Server
After=network.target postgresql.service

[Service]
Type=simple
User=agi
Group=agi
WorkingDirectory=/opt/agi
Environment="PYTHONPATH=/opt/agi"
ExecStart=/usr/bin/python3 /opt/agi/agi/api/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable agi
sudo systemctl start agi
```

#### Using Docker:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agi/ ./agi/

ENV PYTHONPATH=/app
ENV AGI_ENVIRONMENT=production

EXPOSE 5024

CMD ["python3", "agi/api/server.py"]
```

Build and run:

```bash
docker build -t agi-system .
docker run -d --name agi -p 5024:5024 --env-file .env.production agi-system
```

### 4. Configure Reverse Proxy

#### Nginx configuration:

```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api/agi {
        proxy_pass http://localhost:5024;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 5. Set Up Monitoring

#### Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'agi'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

#### Health check endpoint:

```bash
curl https://api.your-domain.com/api/agi/health
```

### 6. Configure Backups

Create backup script:

```bash
#!/bin/bash
# /opt/agi/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/agi"

# Backup database
pg_dump -h localhost -U agi_user -d agi_production > "$BACKUP_DIR/db_$DATE.sql"

# Backup configurations
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/agi/config/

# Backup models (optional, large)
# tar -czf "$BACKUP_DIR/models_$DATE.tar.gz" /opt/agi/models/

# Keep only last 7 days
find "$BACKUP_DIR" -type f -mtime +7 -delete
```

Add to crontab:

```bash
0 2 * * * /opt/agi/backup.sh
```

## Post-Deployment

### 1. Verification Tests

Run smoke tests:

```bash
python3 agi/tests/run_tests.py
```

Test critical endpoints:

```bash
# Health check
curl https://api.your-domain.com/api/agi/health

# Chat endpoint
curl -X POST https://api.your-domain.com/api/agi/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test"}'

# Models list
curl https://api.your-domain.com/api/agi/models
```

### 2. Performance Tuning

#### Database optimization:

```sql
-- Analyze tables
ANALYZE agi.sessions;
ANALYZE agi.conversations;

-- Create indexes
CREATE INDEX idx_sessions_user_id ON agi.sessions(user_id);
CREATE INDEX idx_conversations_session_id ON agi.conversations(session_id);
```

#### Application tuning:

```python
# config/production.yaml
database:
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30

models:
  cache_size: 5
  preload_models: ["tinyllama_1_1b_chat_v1_0_q4_k_m"]
```

### 3. Monitoring Setup

Set up alerts for:

- API response time > 5s
- Error rate > 1%
- CPU usage > 80%
- Memory usage > 90%
- Disk usage > 85%
- Database connections > 80%

### 4. Security Hardening

- Enable rate limiting
- Configure WAF rules
- Set up DDoS protection
- Enable audit logging
- Regular security scans

## Troubleshooting

### Common Issues

#### 1. Model loading fails
- Check GPU/CPU memory
- Verify model file integrity
- Review model compatibility

#### 2. Database connection errors
- Verify connection string
- Check firewall rules
- Validate SSL certificates

#### 3. High memory usage
- Reduce model cache size
- Enable model unloading
- Increase swap space

#### 4. Slow response times
- Enable model preloading
- Optimize database queries
- Add caching layer

### Logs Location

- Application logs: `/var/log/agi/app.log`
- Error logs: `/var/log/agi/error.log`
- Access logs: `/var/log/nginx/access.log`

### Support

For issues, check:
1. Application logs
2. System metrics
3. Database performance
4. Network connectivity

## Rollback Procedure

If deployment fails:

1. Stop new service:
```bash
sudo systemctl stop agi
```

2. Restore database:
```bash
psql -h localhost -U agi_user -d agi_production < /backups/agi/db_last_known_good.sql
```

3. Restore previous version:
```bash
cd /opt/agi
git checkout <previous-version-tag>
```

4. Restart service:
```bash
sudo systemctl start agi
```

## Maintenance

### Regular Tasks

- **Daily**: Check logs, monitor metrics
- **Weekly**: Review performance, update models
- **Monthly**: Security patches, dependency updates
- **Quarterly**: Performance review, capacity planning

### Update Procedure

1. Test updates in staging
2. Schedule maintenance window
3. Backup current state
4. Apply updates
5. Run verification tests
6. Monitor for issues

## Conclusion

Following this guide ensures a robust, secure, and performant deployment of the AGI system. Regular monitoring and maintenance are essential for optimal operation.