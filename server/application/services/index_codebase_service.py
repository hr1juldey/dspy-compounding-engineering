"""
Codebase indexing service for semantic search.

Wraps index_codebase_task Celery task for MCP/API access.
"""

from celery.result import AsyncResult

from server.infrastructure.celery.tasks.index_codebase import (
    index_codebase_task,
)


class IndexCodebaseService:
    """Service for indexing codebase into vector database."""

    def submit_indexing(
        self,
        repo_root: str,
        recreate: bool = False,
        with_graphrag: bool = False,
    ) -> str:
        """
        Submit codebase indexing task to Celery.

        Args:
            repo_root: Root directory of repository
            recreate: Force recreation of vector collection
            with_graphrag: Enable GraphRAG entity extraction

        Returns:
            Task ID for async tracking
        """
        result = index_codebase_task.delay(
            repo_root=repo_root, recreate=recreate, with_graphrag=with_graphrag
        )
        return result.id

    def get_result(self, task_id: str) -> dict | None:
        """
        Get task result if ready.

        Returns:
            Result dictionary or None if not ready
        """
        result = AsyncResult(task_id)
        if result.ready():
            return result.get()
        return None

    def get_status(self, task_id: str) -> dict:
        """
        Get task status and progress.

        Returns:
            Status dictionary with state, progress, and result
        """
        result = AsyncResult(task_id)

        status = {
            "task_id": task_id,
            "state": result.state,
            "ready": result.ready(),
        }

        if result.state == "PROGRESS":
            status["progress"] = result.info
        elif result.ready():
            status["result"] = result.get()

        return status
