# Redis Configuration for Celery

## Status: ✓ Running and Stable

Redis is configured and running on **port 6350** (avoiding conflict with port 6379).

## Configuration Details

### Docker Compose Setup

- **Container Name**: `dspy-ce-redis`
- **Image**: `redis:7-alpine`
- **Port**: 6350 (host network mode)
- **Restart Policy**: `unless-stopped` (auto-restart on failure)

### Persistence Configuration

Redis is configured with dual persistence for maximum reliability:

1. **AOF (Append Only File)**:
   - Enabled with `appendonly yes`
   - Sync mode: `everysec` (good balance between performance and safety)

2. **RDB Snapshots**:
   - Every 15 minutes if at least 1 key changed
   - Every 5 minutes if at least 10 keys changed
   - Every 1 minute if at least 10,000 keys changed

3. **Memory Management**:
   - Max memory: 256MB
   - Eviction policy: `allkeys-lru` (Least Recently Used)

### Data Storage

- **Volume**: Named Docker volume `redis_data`
- **Location**: Managed by Docker (persistent across container restarts)

## Connection Details

### From Python/Celery

```python
# .env configuration
REDIS_URL=redis://localhost:6350

# Python usage
import redis
r = redis.from_url('redis://localhost:6350')

# Celery configuration
CELERY_BROKER_URL = 'redis://localhost:6350/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6350/0'
```

### From CLI

```bash
# Inside container
docker compose exec redis redis-cli -p 6350

# Test connection
docker compose exec redis redis-cli -p 6350 ping
# Expected: PONG
```

## Management Commands

### Start Redis
```bash
docker compose up -d redis
```

### Stop Redis
```bash
docker compose stop redis
```

### View Logs
```bash
docker compose logs -f redis
```

### Check Health
```bash
docker compose ps redis
# Should show: Up X seconds (healthy)
```

### Backup Data
```bash
# Trigger RDB snapshot
docker compose exec redis redis-cli -p 6350 BGSAVE

# Copy backup
docker compose exec redis cat /data/dump.rdb > redis_backup_$(date +%Y%m%d).rdb
```

### Monitor Performance
```bash
# Real-time stats
docker compose exec redis redis-cli -p 6350 --stat

# Memory usage
docker compose exec redis redis-cli -p 6350 INFO memory

# All connected clients
docker compose exec redis redis-cli -p 6350 CLIENT LIST
```

## Health Check

Redis includes an automatic health check that runs every 5 seconds:
- Command: `redis-cli -p 6350 ping`
- Timeout: 3 seconds
- Retries: 10 before marking unhealthy
- Start period: 5 seconds (grace period during startup)

## Celery Integration (Future)

When setting up Celery, use this configuration:

```python
# config/celery.py
from celery import Celery
import os

app = Celery('dspy_ce')

app.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6350/0'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6350/0'),
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 6350
ss -tlnp | grep 6350

# If another process is using it, change the port in docker-compose.yml
# Update both the --port flag and healthcheck
```

### Connection Refused
```bash
# Check if Redis is running
docker compose ps redis

# Check logs for errors
docker compose logs redis

# Restart Redis
docker compose restart redis
```

### Data Loss Prevention

Redis is configured with:
- Automatic persistence (AOF + RDB)
- Named volume (survives container deletion)
- `restart: unless-stopped` (auto-recovery)

Data will persist across:
- Container restarts
- Host reboots
- Docker daemon restarts

## Notes

- Port 6350 is used instead of default 6379 to avoid conflicts
- Network mode is `host` for direct access (no NAT overhead)
- Suitable for development and production use
- Ready for Celery task queue integration
