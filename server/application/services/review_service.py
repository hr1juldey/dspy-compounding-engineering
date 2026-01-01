"""
Application service for code review operations.
"""

from celery.result import AsyncResult

from server.infrastructure.celery.tasks.review import review_code_task


class ReviewService:
    """Service for managing code review tasks."""

    def submit_review(
        self,
        repo_root: str,
        pr_url_or_id: str = "latest",
        project: bool = False,
    ) -> str:
        """
        Submit code review task to Celery.

        Returns:
            Task ID for tracking
        """
        task = review_code_task.delay(
            repo_root=repo_root, pr_url_or_id=pr_url_or_id, project=project
        )
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
