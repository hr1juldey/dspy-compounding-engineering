"""
Celery task for knowledge base compression.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.knowledge import KnowledgeBase
from utils.paths import CompoundingPaths


@celery_app.task(bind=True)
def compress_kb_task(
    self,
    repo_root: str,
    ratio: float = 0.5,
    dry_run: bool = False,
):
    """
    Compress AI.md knowledge base (async task).

    Args:
        repo_root: Root directory of target repository
        ratio: Target compression ratio (0.0 to 1.0)
        dry_run: Preview mode without modifying file

    Returns:
        Task result dictionary
    """
    # Initialize paths
    CompoundingPaths(repo_root)

    # Publish progress
    publish_progress(self.request.id, 0, "Starting KB compression...")

    try:
        # Validate ratio
        if not (0.0 <= ratio <= 1.0):
            raise ValueError("Ratio must be between 0.0 and 1.0")

        # Execute KB compression
        kb = KnowledgeBase()
        result = kb.compress_ai_md(ratio=ratio, dry_run=dry_run)

        publish_progress(self.request.id, 100, "KB compression complete")

        return {
            "success": True,
            "result": result,
            "ratio": ratio,
            "dry_run": dry_run,
        }

    except Exception as e:
        publish_progress(self.request.id, 100, f"Compression failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "ratio": ratio,
        }
