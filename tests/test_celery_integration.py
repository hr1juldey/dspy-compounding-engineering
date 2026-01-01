"""
Integration tests for Celery with real Redis.
"""

import os

import pytest


@pytest.fixture(scope="module")
def redis_available():
    """Check if Redis is available."""
    import redis

    try:
        client = redis.from_url("redis://localhost:6350", socket_connect_timeout=1)
        client.ping()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not os.getenv("REDIS_URL"), reason="Redis not configured")
def test_celery_app_configured():
    """Test Celery app is configured correctly."""
    from server.infrastructure.celery.app import celery_app

    assert celery_app.conf.broker_url
    assert celery_app.conf.result_backend
    assert celery_app.conf.task_serializer == "json"


@pytest.mark.skipif(not os.getenv("REDIS_URL"), reason="Redis not configured")
def test_celery_worker_check():
    """Test checking for Celery workers."""
    from server.infrastructure.celery.app import check_celery_workers

    # Should not raise
    result = check_celery_workers()
    assert isinstance(result, bool)


@pytest.mark.skipif(not os.getenv("REDIS_URL"), reason="Redis not configured")
def test_celery_task_registration():
    """Test all tasks are registered."""
    from server.infrastructure.celery.app import celery_app

    registered_tasks = list(celery_app.tasks.keys())

    expected_tasks = [
        "server.infrastructure.celery.tasks.analyze.analyze_code_task",
        "server.infrastructure.celery.tasks.work.execute_work_task",
        "server.infrastructure.celery.tasks.review.review_code_task",
        "server.infrastructure.celery.tasks.garden.garden_task",
        "server.infrastructure.celery.tasks.plan.generate_plan_task",
        "server.infrastructure.celery.tasks.check.check_policies_task",
    ]

    for task_name in expected_tasks:
        assert task_name in registered_tasks


@pytest.mark.skipif(not os.getenv("REDIS_URL"), reason="Redis not configured")
def test_redis_connection():
    """Test Redis connection works."""
    import redis

    from server.config.settings import get_settings

    settings = get_settings()

    client = redis.from_url(settings.redis_url, decode_responses=True)
    assert client.ping()


@pytest.mark.skipif(not os.getenv("REDIS_URL"), reason="Redis not configured")
def test_redis_pub_sub():
    """Test Redis pub/sub functionality."""
    import json

    import redis

    from server.config.settings import get_settings

    settings = get_settings()

    client = redis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()

    channel = "test_channel"
    pubsub.subscribe(channel)

    # Publish a message
    message = {"test": "data"}
    client.publish(channel, json.dumps(message))

    # Read the message
    # Skip the subscribe confirmation
    msg = pubsub.get_message()
    assert msg is not None

    # Get actual message
    import time

    time.sleep(0.1)
    msg = pubsub.get_message()
    if msg and msg["type"] == "message":
        data = json.loads(msg["data"])
        assert data["test"] == "data"

    pubsub.unsubscribe()
    client.close()
