"""
Celery task for policy enforcement checks.
"""

from server.infrastructure.celery.app import celery_app
from utils.paths import CompoundingPaths
from workflows.check import run_check


@celery_app.task(bind=True)
def check_policies_task(
    self,
    repo_root: str,
    paths: list[str] | None = None,
    auto_fix: bool = False,
    staged_only: bool = False,
):
    """
    Run policy enforcement checks (synchronous - fast operation).

    Args:
        repo_root: Root directory of target repository
        paths: Files or directories to check
        auto_fix: Auto-fix violations using ruff
        staged_only: Check only staged files

    Returns:
        Check result with exit code
    """
    # Initialize paths (ensures .compounding exists)
    CompoundingPaths(repo_root)

    try:
        # Execute check workflow (synchronous)
        exit_code = run_check(
            repo_root=repo_root, paths=paths, auto_fix=auto_fix, staged_only=staged_only
        )

        return {
            "success": exit_code == 0,
            "exit_code": exit_code,
            "paths": paths or "all",
            "auto_fix": auto_fix,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "exit_code": 1,
            "paths": paths or "all",
            "auto_fix": auto_fix,
        }
