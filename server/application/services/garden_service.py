"""
Application service for knowledge base gardening operations.
"""

from celery.result import AsyncResult

from server.infrastructure.celery.tasks.garden import garden_task


class GardenService:
    """Service for managing knowledge base gardening tasks."""

    def submit_garden(
        self,
        repo_root: str,
        action: str = "consolidate",
        limit: int = 100,
    ) -> str:
        """
        Submit gardening task to Celery.

        Returns:
            Task ID for tracking
        """
        task = garden_task.delay(repo_root=repo_root, action=action, limit=limit)
        return task.id

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
