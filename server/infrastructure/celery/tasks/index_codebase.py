"""
Celery task for codebase indexing into vector database.
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.knowledge import KnowledgeBase
from utils.paths import CompoundingPaths


@celery_app.task(bind=True)
def index_codebase_task(
    self,
    repo_root: str,
    recreate: bool = False,
):
    """
    Index codebase for semantic search (async task).

    Args:
        repo_root: Root directory of target repository
        recreate: Force recreation of vector collection

    Returns:
        Task result dictionary
    """
    # Initialize paths
    CompoundingPaths(repo_root)

    # Publish progress
    publish_progress(self.request.id, 0, "Starting codebase indexing...")

    try:
        # Execute codebase indexing
        kb = KnowledgeBase()
        result = kb.index_codebase(root_dir=repo_root, force_recreate=recreate)

        publish_progress(self.request.id, 100, "Codebase indexing complete")

        return {
            "success": True,
            "result": result,
            "repo_root": repo_root,
            "recreate": recreate,
        }

    except Exception as e:
        publish_progress(self.request.id, 100, f"Indexing failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "repo_root": repo_root,
        }
