"""
Celery task for issue triage and categorization.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.paths import CompoundingPaths
from workflows.triage import run_triage


@celery_app.task(bind=True)
def triage_task(
    self,
    repo_root: str,
    pattern: str | None = None,
    dry_run: bool = False,
):
    """
    Run issue triage and categorization (async task).

    Args:
        repo_root: Root directory of target repository
        pattern: Optional pattern to filter issues
        dry_run: Preview mode without creating todos

    Returns:
        Task result dictionary
    """
    # Initialize paths
    CompoundingPaths(repo_root)

    # Publish progress
    publish_progress(self.request.id, 0, "Starting triage...")

    try:
        # Execute triage workflow
        result = run_triage(pattern=pattern, dry_run=dry_run)  # type: ignore[unexpected-keyword]

        publish_progress(self.request.id, 100, "Triage complete")

        return {
            "success": True,
            "result": result,
            "pattern": pattern,
            "dry_run": dry_run,
        }

    except Exception as e:
        publish_progress(self.request.id, 100, f"Triage failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "pattern": pattern,
        }
