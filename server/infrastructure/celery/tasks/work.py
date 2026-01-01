"""
Celery tasks for work execution (todos and plans).
"""

from server.infrastructure.celery.app import celery_app
from server.infrastructure.redis.pubsub import publish_progress
from utils.paths import CompoundingPaths
from workflows.work import run_unified_work


@celery_app.task(bind=True)
def execute_work_task(
    self,
    repo_root: str,
    pattern: str | None = None,
    dry_run: bool = False,
    parallel: bool = True,
    max_workers: int = 3,
    in_place: bool = True,
):
    """
    Execute work items (todos or plans) using ReAct agents.

    Args:
        repo_root: Root directory of target repository
        pattern: Todo ID, plan file, or pattern
        dry_run: Dry run mode (no actual changes)
        parallel: Execute in parallel
        max_workers: Maximum number of parallel workers
        in_place: Apply changes in-place vs worktree

    Returns:
        Work execution result
    """
    task_id = self.request.id

    # Initialize paths (ensures .compounding exists)
    CompoundingPaths(repo_root)

    # Emit progress
    publish_progress(task_id, 0, "Starting work execution...")
    self.update_state(state="PROGRESS", meta={"percent": 0, "status": "Starting..."})

    try:
        publish_progress(task_id, 20, "Loading work items...")
        self.update_state(state="PROGRESS", meta={"percent": 20, "status": "Loading..."})

        # Execute workflow
        result = run_unified_work(
            pattern=pattern,
            dry_run=dry_run,
            parallel=parallel,
            max_workers=max_workers,
            in_place=in_place,
        )

        publish_progress(task_id, 100, "Work execution complete")
        self.update_state(state="PROGRESS", meta={"percent": 100, "status": "Complete"})

        return {"success": True, "result": result, "pattern": pattern}

    except Exception as e:
        publish_progress(task_id, 100, f"Execution failed: {str(e)}")
        return {"success": False, "error": str(e), "pattern": pattern}
