"""
MCP tools for repository management and status.

These are fast, synchronous tools that don't require background tasks.
"""

from celery.result import AsyncResult
from fastmcp import FastMCP

from server.application.services.repo_service import RepoService
from server.infrastructure.execution import RepoExecutor

# Sync tools need separate server without tasks enabled
repository_server = FastMCP("Repository")


@repository_server.tool()
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


@repository_server.tool()
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


@repository_server.tool()
def initialize_repo(repo_root: str, dir_name: str | None = None) -> dict:
    """
    Initialize compounding directory for a repository (REQUIRED FIRST STEP).

    **This must be called before using any other repo_root-accepting tools.**

    Creates the compounding directory structure (.ce, .claude, etc.) and detects
    the repository's environment (Python/Node/Rust/Go/C).

    Args:
        repo_root: Root directory of repository to initialize
        dir_name: Name of the directory to create (e.g., '.claude', '.ce', '.qwen').
                  If None, uses COMPOUNDING_DIR_NAME env var or defaults to '.ce'.

    Returns:
        Initialization status with detected environment and created paths

    Example:
        # Initialize a repository before using any tools
        >>> result = initialize_repo(repo_root="/path/to/my-project")
        >>> print(result)
        {
            "status": "initialized",
            "repo_root": "/path/to/my-project",
            "base_dir": "/path/to/my-project/.ce",
            "environment_detected": "Python 3.12 (Poetry)"
        }

        # Now you can use other tools on this repo
        >>> analyze_code(repo_root="/path/to/my-project", entity="MyClass")

    Multi-Repo Usage:
        When using the MCP server on multiple repositories, the correct pattern is:

        ```python
        from utils.paths import get_paths

        # Set target repository path BEFORE creating KnowledgeBase
        get_paths(target_repo_path)
        kb = KnowledgeBase()
        ```

        This ensures collections use the target repository's hash, not the
        CE server's repository hash, preventing data collision between projects.
    """
    service = RepoService()
    result = service.initialize_repo(repo_root, dir_name=dir_name)

    # Detect environment on init
    try:
        executor = RepoExecutor(repo_root)
        environment = executor.environment
        result["environment_detected"] = environment.description
    except Exception as e:
        result["environment_detected"] = f"Error detecting environment: {e}"

    return result
