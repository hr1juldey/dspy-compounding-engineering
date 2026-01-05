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
    with_graphrag: bool = False,
):
    """
    Index codebase for semantic search (async task).

    Args:
        repo_root: Root directory of target repository
        recreate: Force recreation of vector collection
        with_graphrag: Enable GraphRAG entity extraction

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

        # Create progress callback for GraphRAG
        def progress_callback(current: int, total: int, message: str):
            """Report GraphRAG indexing progress."""
            if total > 0:
                percent = min(90, int((current / total) * 90))
                publish_progress(self.request.id, percent, message)

        # Run indexing with progress reporting
        if with_graphrag:
            publish_progress(
                self.request.id,
                5,
                "Starting GraphRAG entity extraction...",
            )

        result = kb.index_codebase(
            root_dir=repo_root,
            force_recreate=recreate,
            with_graphrag=with_graphrag,
            progress_callback=progress_callback if with_graphrag else None,  # type: ignore[unexpected-keyword]
        )

        publish_progress(self.request.id, 100, "Codebase indexing complete")

        return {
            "success": True,
            "result": result,
            "repo_root": repo_root,
            "recreate": recreate,
            "with_graphrag": with_graphrag,
        }

    except Exception as e:
        publish_progress(self.request.id, 100, f"Indexing failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "repo_root": repo_root,
        }
