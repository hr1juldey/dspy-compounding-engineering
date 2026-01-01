"""
Unit tests for Redis pub/sub.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


@patch("redis.from_url")
def test_publish_progress_success(mock_redis_from_url):
    """Test publishing progress successfully."""
    from server.infrastructure.redis.pubsub import publish_progress

    mock_client = MagicMock()
    mock_redis_from_url.return_value = mock_client

    publish_progress("task-123", 50, "Working...")

    mock_client.publish.assert_called_once()
    call_args = mock_client.publish.call_args
    channel = call_args[0][0]
    payload = json.loads(call_args[0][1])

    assert channel == "task_progress:task-123"
    assert payload["percent"] == 50
    assert payload["message"] == "Working..."
    mock_client.close.assert_called_once()


@patch("redis.from_url")
def test_publish_progress_failure(mock_redis_from_url):
    """Test publish_progress handles errors gracefully."""
    from server.infrastructure.redis.pubsub import publish_progress

    mock_redis_from_url.side_effect = Exception("Redis connection failed")

    # Should not raise, just fail silently
    publish_progress("task-123", 50, "Working...")


@pytest.mark.asyncio
async def test_subscribe_to_task():
    """Test subscribing to task progress with proper async mocking."""
    from server.infrastructure.redis.pubsub import subscribe_to_task

    # Mock the aioredis module
    with patch("redis.asyncio.from_url") as mock_from_url:
        # Create proper async mock
        mock_client = MagicMock()
        mock_pubsub = MagicMock()

        # Make from_url return an awaitable
        async def async_from_url(*args, **kwargs):
            return mock_client

        mock_from_url.side_effect = async_from_url
        mock_client.pubsub.return_value = mock_pubsub

        # Mock async message iteration
        async def mock_listen():
            yield {"type": "subscribe"}
            yield {
                "type": "message",
                "data": json.dumps(
                    {
                        "task_id": "task-123",
                        "percent": 50,
                        "message": "Working...",
                    }
                ),
            }

        mock_pubsub.listen.return_value = mock_listen()

        # Mock async methods
        async def mock_subscribe(*args):
            pass

        async def mock_unsubscribe(*args):
            pass

        async def mock_close():
            pass

        mock_pubsub.subscribe = mock_subscribe
        mock_pubsub.unsubscribe = mock_unsubscribe
        mock_client.close = mock_close

        # Collect messages
        messages = []
        async for update in subscribe_to_task("task-123"):
            messages.append(update)
            break  # Only get first message

        assert len(messages) == 1
        assert messages[0]["percent"] == 50
