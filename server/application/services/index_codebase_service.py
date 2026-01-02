"""
Codebase indexing service for semantic search.

Wraps index_codebase_task Celery task for MCP/API access.
"""

from server.infrastructure.celery.tasks.index_codebase import index_codebase_task


class IndexCodebaseService:
    """Service for indexing codebase into vector database."""

    def submit_indexing(
        self,
        repo_root: str,
        recreate: bool = False,
    ) -> str:
        """
        Submit codebase indexing task to Celery.

        Args:
            repo_root: Root directory of repository
            recreate: Force recreation of vector collection

        Returns:
            Task ID for async tracking
        """
        result = index_codebase_task.delay(repo_root=repo_root, recreate=recreate)
        return result.id
