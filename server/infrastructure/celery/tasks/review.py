"""
Celery task for multi-agent code reviews.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.paths import CompoundingPaths
from workflows.review import run_review


@celery_app.task(bind=True)
def review_code_task(
    self,
    repo_root: str,
    pr_url_or_id: str = "latest",
    project: bool = False,
):
    """
    Perform exhaustive multi-agent code review.

    Args:
        repo_root: Root directory of target repository
        pr_url_or_id: PR number, URL, branch, or 'latest'
        project: Review entire project vs just changes

    Returns:
        Review result
    """
    task_id = self.request.id

    # Initialize paths (ensures .compounding exists)
    CompoundingPaths(repo_root)

    # Emit progress
    publish_progress(task_id, 0, "Initializing code review...")
    self.update_state(state="PROGRESS", meta={"percent": 0, "status": "Initializing..."})

    try:
        publish_progress(task_id, 15, "Loading changes...")
        self.update_state(state="PROGRESS", meta={"percent": 15, "status": "Loading changes..."})

        publish_progress(task_id, 30, "Running review agents...")
        self.update_state(state="PROGRESS", meta={"percent": 30, "status": "Reviewing..."})

        # Execute review workflow
        result = run_review(pr_url_or_id=pr_url_or_id, project=project)

        publish_progress(task_id, 100, "Review complete")
        self.update_state(state="PROGRESS", meta={"percent": 100, "status": "Complete"})

        return {"success": True, "result": result, "target": pr_url_or_id}

    except Exception as e:
        publish_progress(task_id, 100, f"Review failed: {str(e)}")
        return {"success": False, "error": str(e), "target": pr_url_or_id}
