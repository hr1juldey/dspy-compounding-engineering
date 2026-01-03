"""
Redis connection pool for sync operations.

Provides thread-safe connection pooling for blocking Redis operations
in Celery tasks. Replaces creating a new connection for each operation.
"""

import redis

from server.config.settings import get_settings

settings = get_settings()

# Module-level connection pool (thread-safe, reusable)
_sync_pool = None


def get_sync_redis_pool() -> redis.ConnectionPool:
    """Get or create sync Redis connection pool."""
    global _sync_pool
    if _sync_pool is None:
        _sync_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=10,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _sync_pool


def get_sync_redis_client() -> redis.Redis:
    """Get Redis client from pool (reuses connections)."""
    return redis.Redis(connection_pool=get_sync_redis_pool())
