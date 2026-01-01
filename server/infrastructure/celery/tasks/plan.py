"""
Celery task for project plan generation.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.paths import CompoundingPaths
from workflows.plan import run_plan


@celery_app.task(bind=True)
def generate_plan_task(
    self,
    repo_root: str,
    feature_description: str,
):
    """
    Generate project plan from feature description.

    Args:
        repo_root: Root directory of target repository
        feature_description: Natural language feature description

    Returns:
        Plan generation result
    """
    task_id = self.request.id

    # Initialize paths (ensures .compounding exists)
    CompoundingPaths(repo_root)

    # Emit progress
    publish_progress(task_id, 0, "Generating project plan...")
    self.update_state(state="PROGRESS", meta={"percent": 0, "status": "Starting..."})

    try:
        publish_progress(task_id, 25, "Analyzing feature requirements...")
        self.update_state(
            state="PROGRESS", meta={"percent": 25, "status": "Analyzing requirements..."}
        )

        publish_progress(task_id, 50, "Generating implementation plan...")
        self.update_state(state="PROGRESS", meta={"percent": 50, "status": "Generating plan..."})

        # Execute plan workflow
        result = run_plan(feature_description=feature_description)

        publish_progress(task_id, 100, "Plan generation complete")
        self.update_state(state="PROGRESS", meta={"percent": 100, "status": "Complete"})

        return {"success": True, "result": result, "description": feature_description}

    except Exception as e:
        publish_progress(task_id, 100, f"Plan generation failed: {str(e)}")
        return {"success": False, "error": str(e), "description": feature_description}
