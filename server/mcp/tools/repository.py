"""
MCP tools for repository management and status.
"""

from celery.result import AsyncResult

from server.application.services.repo_service import RepoService
from server.mcp.server import mcp


@mcp.tool()
def get_task_status(task_id: str) -> dict:
    """
    Get status of any task by ID.

    Args:
        task_id: Celery task ID

    Returns:
        Task status with progress and result if ready
    """
    result = AsyncResult(task_id)
    status = {"task_id": task_id, "state": result.state, "ready": result.ready()}

    if result.state == "PROGRESS":
        status["progress"] = result.info
    elif result.ready():
        status["result"] = result.get()

    return status


@mcp.tool()
def get_repo_status(repo_root: str) -> dict:
    """
    Get repository status and metadata.

    Args:
        repo_root: Root directory of repository

    Returns:
        Repository status information
    """
    service = RepoService()
    return service.get_repo_status(repo_root)


@mcp.tool()
def initialize_repo(repo_root: str) -> dict:
    """
    Initialize .compounding directory for a repository.

    Args:
        repo_root: Root directory of repository

    Returns:
        Initialization status
    """
    service = RepoService()
    return service.initialize_repo(repo_root)
