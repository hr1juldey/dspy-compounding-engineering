"""
Application service for code analysis operations.
"""

from celery.result import AsyncResult

from server.infrastructure.celery.tasks.analyze import analyze_code_task


class AnalyzeService:
    """Service for managing code analysis tasks."""

    def submit_analyze(
        self,
        repo_root: str,
        entity: str,
        analysis_type: str = "navigate",
        max_depth: int = 2,
        change_type: str = "Modify",
        save: bool = True,
    ) -> str:
        """
        Submit code analysis task to Celery.

        Returns:
            Task ID for tracking
        """
        task = analyze_code_task.delay(  # type: ignore[no-untyped-call]
            repo_root=repo_root,
            entity=entity,
            analysis_type=analysis_type,
            max_depth=max_depth,
            change_type=change_type,
            save=save,
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
