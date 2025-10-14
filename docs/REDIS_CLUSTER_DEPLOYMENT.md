# Redis Cluster Deployment Guide

**WeedGo AI Engine - Production Redis Configuration**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Local Development Setup](#local-development-setup)
5. [Production Deployment](#production-deployment)
6. [Configuration](#configuration)
7. [High Availability](#high-availability)
8. [Monitoring](#monitoring)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deploying Redis for the WeedGo AI Engine in both development and production environments. Redis is used for:

- **Verification Code Storage**: Distributed verification codes
- **Rate Limiting**: Cross-server rate limit counters
- **Password Tokens**: Secure password reset/setup tokens
- **Session Storage**: User session data (future)
- **Cache**: Temporary data cache (future)

### Why Redis Cluster?

| Feature | Benefit |
|---------|---------|
| **Horizontal Scalability** | Handle more connections/data |
| **High Availability** | Automatic failover on node failure |
| **Data Partitioning** | Data distributed across nodes |
| **Replication** | Data redundancy across replicas |

---

## Architecture

### Development Architecture

```
┌─────────────────┐
│  AI Engine API  │
│  (Port 5024)    │
└────────┬────────┘
         │
         │ Redis Protocol
         │
    ┌────▼────┐
    │  Redis  │
    │  Single │
    │  Node   │
    └─────────┘
```

### Production Architecture (3-Node Cluster)

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
      ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
      │ API #1  │       │ API #2  │      │ API #3  │
      └────┬────┘       └────┬────┘      └────┬────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │   Redis Cluster   │
                   │   (6 Nodes Total) │
                   └───────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
      ┌────▼────┐       ┌────▼────┐      ┌────▼────┐
      │ Master1 │◄─────►│ Master2 │◄─────►│ Master3 │
      │ :7000   │       │ :7001   │       │ :7002   │
      └────┬────┘       └────┬────┘       └────┬────┘
           │                 │                  │
      ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
      │ Slave1  │       │ Slave2  │       │ Slave3  │
      │ :7003   │       │ :7004   │       │ :7005   │
      └─────────┘       └─────────┘       └─────────┘
```

**Nodes:**
- 3 Master nodes (data storage, write operations)
- 3 Slave nodes (read replicas, failover targets)
- Data automatically sharded across masters
- Each master has 1 slave for redundancy

---

## Prerequisites

### System Requirements

**Minimum (Development)**:
- 1 CPU core
- 512MB RAM
- 1GB disk space
- Redis 6.2+

**Recommended (Production)**:
- 4 CPU cores per node
- 8GB RAM per node
- 50GB SSD per node
- Redis 7.0+
- Linux (Ubuntu 20.04+ or CentOS 8+)

### Software Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server redis-tools

# CentOS/RHEL
sudo yum install redis redis-tools

# macOS (Homebrew)
brew install redis
```

### Network Requirements

- TCP ports 6379-6384 (Redis instances)
- TCP ports 16379-16384 (Cluster bus)
- Firewall rules allowing inter-node communication

---

## Local Development Setup

### Single Node Setup (Simplest)

1. **Install Redis**

```bash
# macOS
brew install redis

# Ubuntu/Debian
sudo apt-get install redis-server
```

2. **Start Redis**

```bash
# macOS (Homebrew)
redis-server

# Ubuntu/Debian (systemd)
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

3. **Verify Installation**

```bash
redis-cli ping
# Expected output: PONG
```

4. **Configure AI Engine**

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty for development
```

### Docker Compose Setup (Recommended for Development)

1. **Create docker-compose.yml**

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: weedgo-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  redis-data:
    driver: local
```

2. **Start Redis**

```bash
docker-compose up -d redis
```

3. **Verify**

```bash
docker exec -it weedgo-redis redis-cli ping
# Expected: PONG
```

---

## Production Deployment

### Option 1: AWS ElastiCache (Managed Redis)

**Recommended for production - fully managed by AWS**

1. **Create ElastiCache Cluster**

```bash
# AWS CLI
aws elasticache create-cache-cluster \
    --cache-cluster-id weedgo-redis-prod \
    --cache-node-type cache.r6g.large \
    --engine redis \
    --engine-version 7.0 \
    --num-cache-nodes 1 \
    --preferred-availability-zone us-east-1a \
    --security-group-ids sg-xxxxxxxx

# For cluster mode (multiple shards)
aws elasticache create-replication-group \
    --replication-group-id weedgo-redis-cluster \
    --replication-group-description "WeedGo Production Redis" \
    --engine redis \
    --cache-node-type cache.r6g.large \
    --num-node-groups 3 \
    --replicas-per-node-group 1 \
    --automatic-failover-enabled \
    --multi-az-enabled \
    --at-rest-encryption-enabled \
    --transit-encryption-enabled
```

2. **Configuration**

```bash
# .env file
REDIS_HOST=weedgo-redis-cluster.abc123.cache.amazonaws.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your-secure-password
REDIS_SSL=true
```

**Benefits:**
- ✅ Automatic backups
- ✅ Automatic failover
- ✅ Auto-scaling
- ✅ Encryption at rest/transit
- ✅ VPC isolation
- ✅ CloudWatch monitoring

### Option 2: Self-Managed Cluster (On-Premises/VPS)

1. **Install Redis on All Nodes**

```bash
# On each server (redis1, redis2, redis3)
sudo apt-get update
sudo apt-get install redis-server
```

2. **Configure Each Node**

```bash
# /etc/redis/redis-7000.conf (Master 1)
port 7000
cluster-enabled yes
cluster-config-file nodes-7000.conf
cluster-node-timeout 5000
appendonly yes
bind 0.0.0.0
protected-mode no
requirepass your-secure-password
masterauth your-secure-password

# /etc/redis/redis-7001.conf (Master 2)
port 7001
# ... same config with port 7001

# /etc/redis/redis-7002.conf (Master 3)
port 7002
# ... same config with port 7002

# Repeat for slaves (ports 7003-7005)
```

3. **Start All Nodes**

```bash
# Start each instance
redis-server /etc/redis/redis-7000.conf &
redis-server /etc/redis/redis-7001.conf &
redis-server /etc/redis/redis-7002.conf &
redis-server /etc/redis/redis-7003.conf &
redis-server /etc/redis/redis-7004.conf &
redis-server /etc/redis/redis-7005.conf &
```

4. **Create Cluster**

```bash
redis-cli --cluster create \
    192.168.1.10:7000 \
    192.168.1.11:7001 \
    192.168.1.12:7002 \
    192.168.1.10:7003 \
    192.168.1.11:7004 \
    192.168.1.12:7005 \
    --cluster-replicas 1 \
    -a your-secure-password
```

5. **Verify Cluster**

```bash
redis-cli -c -p 7000 -a your-secure-password cluster nodes
redis-cli -c -p 7000 -a your-secure-password cluster info
```

---

## Configuration

### Redis Configuration File

**Recommended production settings:**

```conf
# /etc/redis/redis.conf

# Network
bind 0.0.0.0  # Listen on all interfaces (VPC only!)
port 6379
protected-mode yes
tcp-backlog 511
timeout 300
tcp-keepalive 300

# General
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16

# Security
requirepass your-very-secure-password-here
rename-command CONFIG ""  # Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# AOF (Append Only File)
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Memory Management
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used keys
maxmemory-samples 5

# Cluster (if using cluster mode)
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 15000
cluster-require-full-coverage yes

# Slow Log
slowlog-log-slower-than 10000  # 10ms
slowlog-max-len 128

# Client Output Buffer Limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
```

### AI Engine Configuration

```python
# services/redis_verification_store.py

# Connection pool settings
ConnectionPool(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True,
    max_connections=50,  # Adjust based on load
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    socket_keepalive=True,
    socket_keepalive_options={
        socket.TCP_KEEPIDLE: 1,
        socket.TCP_KEEPINTVL: 1,
        socket.TCP_KEEPCNT: 5
    }
)
```

---

## High Availability

### Automatic Failover

Redis Cluster automatically handles failover:

1. **Failure Detection**: Nodes ping each other (cluster-node-timeout)
2. **Voting**: Slaves vote to promote new master
3. **Promotion**: Slave becomes master
4. **Client Redirect**: Clients automatically redirect to new master

### Manual Failover (Maintenance)

```bash
# Initiate manual failover
redis-cli -c -h master-node -p 7000 -a password CLUSTER FAILOVER

# Force failover (if master unresponsive)
redis-cli -c -h slave-node -p 7003 -a password CLUSTER FAILOVER FORCE
```

### Health Checks

```bash
# Check cluster health
redis-cli -c -h any-node -p 7000 -a password CLUSTER INFO

# Check individual node
redis-cli -h node -p 7000 -a password INFO replication

# Monitor in real-time
redis-cli -h node -p 7000 -a password --stat
```

---

## Monitoring

### Prometheus Metrics

The AI Engine exposes Redis metrics at `/metrics`:

```
# Redis operation metrics
redis_operations_total{operation="get",success="true"} 1523
redis_operations_total{operation="set",success="true"} 892
redis_connection_errors_total 2
redis_operation_duration_seconds{operation="get",quantile="0.95"} 0.003
```

### Redis INFO Command

```bash
redis-cli -h host -p 6379 -a password INFO

# Key metrics to monitor:
# - used_memory_human: Current memory usage
# - connected_clients: Active connections
# - instantaneous_ops_per_sec: Operations/second
# - keyspace_hits: Cache hit rate
# - keyspace_misses: Cache miss rate
# - evicted_keys: Keys evicted due to maxmemory
# - expired_keys: Keys expired naturally
```

### CloudWatch Monitoring (AWS ElastiCache)

Key metrics to monitor:

- CPUUtilization < 70%
- EngineCPUUtilization < 80%
- DatabaseMemoryUsagePercentage < 90%
- CacheHits / (CacheHits + CacheMisses) > 0.8
- Evictions < 1000/hour
- ReplicationLag < 1 second

### Alerting

```yaml
# prometheus/alerts.yml
groups:
  - name: redis
    rules:
      - alert: RedisDown
        expr: redis_up == 0
        for: 5m
        annotations:
          summary: "Redis instance down"

      - alert: RedisHighMemory
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 10m
        annotations:
          summary: "Redis memory usage > 90%"

      - alert: RedisHighConnections
        expr: redis_connected_clients > 1000
        for: 5m
        annotations:
          summary: "Redis has > 1000 connections"

      - alert: RedisHighLatency
        expr: redis_operation_duration_seconds{quantile="0.95"} > 0.1
        for: 5m
        annotations:
          summary: "Redis P95 latency > 100ms"
```

---

## Backup & Recovery

### Automated Backups (ElastiCache)

AWS ElastiCache provides automatic backups:

```bash
# Create manual snapshot
aws elasticache create-snapshot \
    --replication-group-id weedgo-redis-cluster \
    --snapshot-name weedgo-backup-$(date +%Y%m%d)

# List snapshots
aws elasticache describe-snapshots \
    --replication-group-id weedgo-redis-cluster

# Restore from snapshot
aws elasticache create-replication-group \
    --replication-group-id weedgo-redis-restored \
    --snapshot-name weedgo-backup-20250115
```

### Manual Backups (Self-Managed)

```bash
# Trigger RDB snapshot
redis-cli -h host -p 6379 -a password BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backup/redis-backup-$(date +%Y%m%d).rdb

# Copy AOF file
cp /var/lib/redis/appendonly.aof /backup/redis-aof-$(date +%Y%m%d).aof
```

### Recovery

```bash
# Stop Redis
sudo systemctl stop redis-server

# Restore RDB
sudo cp /backup/redis-backup-20250115.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb

# Start Redis
sudo systemctl start redis-server

# Verify
redis-cli -a password INFO keyspace
```

---

## Troubleshooting

### Connection Issues

**Problem**: `ConnectionError: Error connecting to Redis`

**Solutions**:
```bash
# Check Redis is running
redis-cli ping

# Check firewall
sudo ufw status
sudo ufw allow 6379/tcp

# Check Redis listening
sudo netstat -tlnp | grep 6379

# Test connection
redis-cli -h host -p 6379 -a password ping
```

### Memory Issues

**Problem**: `OOM command not allowed when used memory > 'maxmemory'`

**Solutions**:
```bash
# Check current memory
redis-cli -a password INFO memory

# Increase maxmemory
redis-cli -a password CONFIG SET maxmemory 4gb

# Change eviction policy
redis-cli -a password CONFIG SET maxmemory-policy allkeys-lru

# Clear database (CAUTION!)
redis-cli -a password FLUSHDB
```

### Cluster Issues

**Problem**: `CLUSTERDOWN The cluster is down`

**Solutions**:
```bash
# Check cluster status
redis-cli -c -a password CLUSTER INFO

# Check node health
redis-cli -c -a password CLUSTER NODES

# Fix broken cluster
redis-cli --cluster fix host:port -a password

# Reshard if needed
redis-cli --cluster reshard host:port -a password
```

### Performance Issues

**Problem**: Slow Redis operations

**Solutions**:
```bash
# Check slow log
redis-cli -a password SLOWLOG GET 10

# Monitor operations in real-time
redis-cli -a password MONITOR

# Check latency
redis-cli -a password --latency

# Check CPU and memory
redis-cli -a password INFO cpu
redis-cli -a password INFO memory
```

---

## Best Practices

### Security

1. ✅ **Always use passwords** in production
2. ✅ **Enable encryption** at rest and in transit (TLS/SSL)
3. ✅ **Use VPC/private networks** - never expose to internet
4. ✅ **Disable dangerous commands** (FLUSHALL, CONFIG, etc.)
5. ✅ **Use separate databases** for different environments
6. ✅ **Regular security audits**

### Performance

1. ✅ **Use connection pooling** (we do: max 50 connections)
2. ✅ **Enable pipelining** for bulk operations
3. ✅ **Set appropriate TTLs** (we use 5-minute code expiry)
4. ✅ **Monitor memory usage** and adjust maxmemory
5. ✅ **Use Redis 7+** for better performance
6. ✅ **SSD storage** for persistence files

### Operations

1. ✅ **Automated backups** daily at minimum
2. ✅ **Test recovery procedures** quarterly
3. ✅ **Monitor metrics** with alerts
4. ✅ **Regular updates** for security patches
5. ✅ **Document procedures** for team
6. ✅ **Capacity planning** before growth

---

## References

- [Redis Official Documentation](https://redis.io/documentation)
- [Redis Cluster Tutorial](https://redis.io/docs/manual/scaling/)
- [AWS ElastiCache Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)
- [Redis Persistence](https://redis.io/docs/manual/persistence/)

---

**Last Updated**: January 2025
**Version**: 1.0.0
**Document Owner**: WeedGo DevOps Team
