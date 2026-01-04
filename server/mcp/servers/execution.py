"""
Execution subserver - code execution, review, and policy checking tools.

Contains tools for running work items, code reviews, and policy checks.
"""

import asyncio

from fastmcp import FastMCP

from server.application.services.check_service import CheckService
from utils.paths import CompoundingPaths
from workflows.review import run_review
from workflows.work import run_unified_work

execution_server = FastMCP("Execution")


@execution_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def execute_work(
    repo_root: str,
    pattern: str | None = None,
    dry_run: bool = False,
    parallel: bool = True,
    max_workers: int = 3,
) -> dict:
    """
    Execute work items (todos or plans) using ReAct agents.

    Args:
        repo_root: Root directory of repository
        pattern: Todo ID, plan file, or pattern
        dry_run: Dry run mode (no actual changes)
        parallel: Execute in parallel
        max_workers: Maximum number of parallel workers

    Returns:
        Work execution result dictionary
    """
    CompoundingPaths(repo_root)

    try:
        result = await asyncio.to_thread(
            run_unified_work,
            pattern=pattern,
            dry_run=dry_run,
            parallel=parallel,
            max_workers=max_workers,
            in_place=True,
        )

        return {"success": True, "result": result, "pattern": pattern}

    except Exception as e:
        return {"success": False, "error": str(e), "pattern": pattern}


@execution_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def review_code(
    repo_root: str,
    pr_url_or_id: str = "latest",
    project: bool = False,
) -> dict:
    """
    Perform exhaustive multi-agent code review.

    Args:
        repo_root: Root directory of repository
        pr_url_or_id: PR number, URL, branch, or 'latest'
        project: Review entire project vs just changes

    Returns:
        Review result dictionary
    """
    CompoundingPaths(repo_root)

    try:
        result = await asyncio.to_thread(run_review, pr_url_or_id=pr_url_or_id, project=project)

        return {"success": True, "result": result, "target": pr_url_or_id}

    except Exception as e:
        return {"success": False, "error": str(e), "target": pr_url_or_id}


@execution_server.tool()
def check_policies(
    repo_root: str,
    paths: list[str] | None = None,
    auto_fix: bool = False,
) -> dict:
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
