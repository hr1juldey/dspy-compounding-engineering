"""
MCP tools for code analysis and planning.
"""

from server.application.services.analyze_service import AnalyzeService
from server.application.services.plan_service import PlanService
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
