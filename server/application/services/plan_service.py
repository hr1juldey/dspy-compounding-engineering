"""
Application service for project plan generation operations.
"""

from celery.result import AsyncResult

from server.infrastructure.celery.tasks.plan import generate_plan_task


class PlanService:
    """Service for managing plan generation tasks."""

    def submit_plan(
        self,
        repo_root: str,
        feature_description: str,
    ) -> str:
        """
        Submit plan generation task to Celery.

        Returns:
            Task ID for tracking
        """
        task = generate_plan_task.delay(
            repo_root=repo_root, feature_description=feature_description
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
