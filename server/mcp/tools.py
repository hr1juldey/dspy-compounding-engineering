"""
MCP tool definitions.
Each tool delegates to application services.
"""

from celery.result import AsyncResult

from server.application.services.analyze_service import AnalyzeService
from server.application.services.check_service import CheckService
from server.application.services.garden_service import GardenService
from server.application.services.plan_service import PlanService
from server.application.services.repo_service import RepoService
from server.application.services.review_service import ReviewService
from server.application.services.work_service import WorkService
from server.mcp.server import mcp


@mcp.tool()
def analyze_code(
    repo_root: str,
    entity: str,
    analysis_type: str = "navigate",
    max_depth: int = 2,
    change_type: str = "Modify",
) -> dict:
    """
    Analyze code using GraphRAG agents (async - returns task_id).

    Args:
        repo_root: Root directory of repository
        entity: Entity to analyze (function, class, module)
        analysis_type: Type of analysis (navigate|impact|deps|arch|search)
        max_depth: Maximum relationship depth (1-3)
        change_type: Change type for impact analysis

    Returns:
        Task submission info with task_id
    """
    service = AnalyzeService()
    task_id = service.submit_analyze(
        repo_root=repo_root,
        entity=entity,
        analysis_type=analysis_type,
        max_depth=max_depth,
        change_type=change_type,
    )
    return {"task_id": task_id, "status": "submitted"}


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
def garden_knowledge(repo_root: str, action: str = "consolidate", limit: int = 100) -> dict:
    """
    Maintain knowledge base (async - returns task_id).

    Args:
        repo_root: Root directory of repository
        action: Action (consolidate|compress-memory|index-commits|all)
        limit: Max commits to index

    Returns:
        Task submission info with task_id
    """
    service = GardenService()
    task_id = service.submit_garden(repo_root=repo_root, action=action, limit=limit)
    return {"task_id": task_id, "status": "submitted"}


@mcp.tool()
def generate_plan(repo_root: str, feature_description: str) -> dict:
    """
    Generate project plan (async - returns task_id).

    Args:
        repo_root: Root directory of repository
        feature_description: Natural language feature description

    Returns:
        Task submission info with task_id
    """
    service = PlanService()
    task_id = service.submit_plan(repo_root=repo_root, feature_description=feature_description)
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
