"""
Redis pub/sub for progress broadcasting.
"""

import json
from datetime import datetime
from typing import AsyncIterator

import redis.asyncio as aioredis

from server.config.settings import get_settings

settings = get_settings()


def publish_progress(task_id: str, percent: int, message: str) -> None:
    """
    Publish progress update to Redis channel (synchronous).

    Args:
        task_id: Celery task ID
        percent: Progress percentage (0-100)
        message: Status message
    """
    try:
        import redis

        client = redis.from_url(settings.redis_url, decode_responses=True)
        channel = f"task_progress:{task_id}"

        payload = {
            "task_id": task_id,
            "percent": percent,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        client.publish(channel, json.dumps(payload))
        client.close()
    except Exception:
        # Silent failure - progress is optional
        pass


async def subscribe_to_task(task_id: str) -> AsyncIterator[dict]:
    """
    Subscribe to task progress updates (async generator).

    Args:
        task_id: Celery task ID

    Yields:
        Progress update dictionaries
    """
    client = await aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    channel = f"task_progress:{task_id}"

    try:
        await pubsub.subscribe(channel)

        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    yield data
                except json.JSONDecodeError:
                    continue

    finally:
        await pubsub.unsubscribe(channel)
        await client.close()
