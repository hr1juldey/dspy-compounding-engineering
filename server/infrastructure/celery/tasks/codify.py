"""
Celery task for feedback codification into knowledge base.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.paths import CompoundingPaths
from workflows.codify import run_codify


@celery_app.task(bind=True)
def codify_task(
    self,
    repo_root: str,
    feedback: str,
    source: str = "manual_input",
):
    """
    Codify feedback into knowledge base (async task).

    Args:
        repo_root: Root directory of target repository
        feedback: Feedback, instruction, or learning to codify
        source: Source of feedback (e.g., 'review', 'retro')

    Returns:
        Task result dictionary
    """
    # Initialize paths
    CompoundingPaths(repo_root)

    # Publish progress
    publish_progress(self.request.id, 0, "Starting feedback codification...")

    try:
        # Execute codify workflow
        result = run_codify(feedback=feedback, source=source)

        publish_progress(self.request.id, 100, "Feedback codified successfully")

        return {
            "success": True,
            "result": result,
            "feedback": feedback,
            "source": source,
        }

    except Exception as e:
        publish_progress(self.request.id, 100, f"Codification failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "feedback": feedback,
        }
