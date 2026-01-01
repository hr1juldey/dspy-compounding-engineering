"""
Application service for policy enforcement checks.
"""

from celery.result import AsyncResult

from server.infrastructure.celery.tasks.check import check_policies_task


class CheckService:
    """Service for managing policy check tasks."""

    def submit_check(
        self,
        repo_root: str,
        paths: list[str] | None = None,
        auto_fix: bool = False,
        staged_only: bool = False,
    ) -> str:
        """
        Submit policy check task to Celery.

        Returns:
            Task ID for tracking
        """
        task = check_policies_task.delay(
            repo_root=repo_root, paths=paths, auto_fix=auto_fix, staged_only=staged_only
        )
        return task.id

    def check_sync(
        self,
        repo_root: str,
        paths: list[str] | None = None,
        auto_fix: bool = False,
        staged_only: bool = False,
    ) -> dict:
        """
        Run policy check synchronously (for fast operations).

        Returns:
            Check result immediately
        """
        result = check_policies_task.apply(
            args=(repo_root,),
            kwargs={"paths": paths, "auto_fix": auto_fix, "staged_only": staged_only},
        )
        return result.get()

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
        Get task status.

        Returns:
            Status dictionary
        """
        result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "state": result.state,
            "ready": result.ready(),
            "result": result.get() if result.ready() else None,
        }
