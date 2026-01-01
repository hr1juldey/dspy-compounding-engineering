"""
Celery task for knowledge base gardening.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.paths import CompoundingPaths
from workflows.garden import run_garden


@celery_app.task(bind=True)
def garden_task(
    self,
    repo_root: str,
    action: str = "consolidate",
    limit: int = 100,
):
    """
    Maintain and optimize the knowledge base.

    Args:
        repo_root: Root directory of target repository
        action: Action to perform (consolidate|compress-memory|index-commits|all)
        limit: Max commits to index

    Returns:
        Garden result
    """
    task_id = self.request.id

    # Initialize paths (ensures .compounding exists)
    CompoundingPaths(repo_root)

    # Emit progress
    publish_progress(task_id, 0, f"Starting {action} gardening...")
    self.update_state(state="PROGRESS", meta={"percent": 0, "status": "Starting..."})

    try:
        publish_progress(task_id, 20, f"Running {action}...")
        self.update_state(state="PROGRESS", meta={"percent": 20, "status": f"Running {action}..."})

        # Execute garden workflow
        result = run_garden(action=action, limit=limit)

        publish_progress(task_id, 100, "Gardening complete")
        self.update_state(state="PROGRESS", meta={"percent": 100, "status": "Complete"})

        return {"success": True, "result": result, "action": action}

    except Exception as e:
        publish_progress(task_id, 100, f"Gardening failed: {str(e)}")
        return {"success": False, "error": str(e), "action": action}
