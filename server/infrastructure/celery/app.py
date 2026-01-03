"""
Celery application configuration with Redis broker.
"""

from celery import Celery

from server.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "compounding_engineering",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "server.infrastructure.celery.tasks.analyze",
        "server.infrastructure.celery.tasks.check",
        "server.infrastructure.celery.tasks.codify",
        "server.infrastructure.celery.tasks.compress_kb",
        "server.infrastructure.celery.tasks.garden",
        "server.infrastructure.celery.tasks.generate_command",
        "server.infrastructure.celery.tasks.index_codebase",
        "server.infrastructure.celery.tasks.plan",
        "server.infrastructure.celery.tasks.review",
        "server.infrastructure.celery.tasks.triage",
        "server.infrastructure.celery.tasks.work",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    broker_connection_retry_on_startup=True,
)


def check_celery_workers() -> bool:
    """
    Check if Celery workers are running.

    Returns:
        True if workers are active, False otherwise
    """
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        return active_workers is not None and len(active_workers) > 0
    except Exception:
        return False
