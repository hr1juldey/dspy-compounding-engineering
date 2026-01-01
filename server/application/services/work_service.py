"""
Application service for work execution operations.
"""

from celery.result import AsyncResult

from server.infrastructure.celery.tasks.work import execute_work_task


class WorkService:
    """Service for managing work execution tasks."""

    def submit_work(
        self,
        repo_root: str,
        pattern: str | None = None,
        dry_run: bool = False,
        parallel: bool = True,
        max_workers: int = 3,
        in_place: bool = True,
    ) -> str:
        """
        Submit work execution task to Celery.

        Returns:
            Task ID for tracking
        """
        task = execute_work_task.delay(
            repo_root=repo_root,
            pattern=pattern,
            dry_run=dry_run,
            parallel=parallel,
            max_workers=max_workers,
            in_place=in_place,
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
