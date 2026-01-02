"""
MCP tools for code execution, review, and policy checking.
"""

from server.application.services.check_service import CheckService
from server.application.services.review_service import ReviewService
from server.application.services.work_service import WorkService
from server.mcp.server import mcp


@mcp.tool()
def execute_work(
    repo_root: str,
    pattern: str | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Execute work items (async - returns task_id).

    Args:
        repo_root: Root directory of repository
        pattern: Todo ID, plan file, or pattern
        dry_run: Dry run mode

    Returns:
        Task submission info with task_id
    """
    service = WorkService()
    task_id = service.submit_work(repo_root=repo_root, pattern=pattern, dry_run=dry_run)
    return {"task_id": task_id, "status": "submitted"}


@mcp.tool()
def review_code(repo_root: str, pr_url_or_id: str = "latest", project: bool = False) -> dict:
    """
    Review code (async - returns task_id).

    Args:
        repo_root: Root directory of repository
        pr_url_or_id: PR number, URL, or 'latest'
        project: Review entire project

    Returns:
        Task submission info with task_id
    """
    service = ReviewService()
    task_id = service.submit_review(repo_root=repo_root, pr_url_or_id=pr_url_or_id, project=project)
    return {"task_id": task_id, "status": "submitted"}


@mcp.tool()
def check_policies(repo_root: str, paths: list[str] | None = None, auto_fix: bool = False) -> dict:
    """
    Check policy compliance (synchronous - fast operation).

    Args:
        repo_root: Root directory of repository
        paths: Files or directories to check (None = all)
        auto_fix: Auto-fix violations using ruff

    Returns:
        Check results immediately
    """
    service = CheckService()
    return service.check_sync(repo_root=repo_root, paths=paths, auto_fix=auto_fix)
