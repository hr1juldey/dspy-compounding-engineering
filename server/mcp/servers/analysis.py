"""
Analysis subserver - GraphRAG code analysis and planning tools.

Contains tools that use DSPy agents for code understanding.
"""

import asyncio

from fastmcp import FastMCP

from utils.paths import get_paths, reset_paths
from workflows.analyze import run_analyze
from workflows.plan import run_plan

analysis_server = FastMCP("Analysis")


@analysis_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def analyze_code(
    repo_root: str,
    entity: str,
    analysis_type: str = "navigate",
    max_depth: int = 2,
    change_type: str = "Modify",
    save: bool = True,
) -> dict:
    """
    Analyze code using GraphRAG agents.

    **Prerequisites:**
        - Repository must be initialized via `initialize_repo()` tool first
        - Use `get_repo_status()` to check initialization state

    Args:
        repo_root: Root directory of repository
        entity: Entity to analyze (function, class, module)
        analysis_type: Type of analysis (navigate|impact|deps|arch|search)
        max_depth: Maximum relationship depth (1-3)
        change_type: Change type for impact analysis
        save: Whether to save results to file

    Returns:
        Analysis result dictionary

    Note:
        When working with multiple repositories, each requires separate initialization.
        Collections are isolated per repository using stable path-based hashing.
    """
    # Initialize paths singleton for target repo
    reset_paths()
    get_paths(repo_root)

    try:
        # Run sync workflow in thread pool
        result = await asyncio.to_thread(
            run_analyze,
            entity=entity,
            analysis_type=analysis_type,
            max_depth=max_depth,
            change_type=change_type,
            save=save,
        )

        return {"success": True, "result": result, "entity": entity, "type": analysis_type}

    except Exception as e:
        return {"success": False, "error": str(e), "entity": entity, "type": analysis_type}


@analysis_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def generate_plan(
    repo_root: str,
    feature_description: str,
) -> dict:
    """
    Generate project implementation plan from feature description.

    **Prerequisites:**
        - Repository must be initialized via `initialize_repo()` tool first
        - Use `get_repo_status()` to check initialization state

    Args:
        repo_root: Root directory of repository
        feature_description: Natural language feature description

    Returns:
        Plan result with implementation steps

    Note:
        When working with multiple repositories, each requires separate initialization.
        Collections are isolated per repository using stable path-based hashing.
    """
    # Initialize paths singleton for target repo
    reset_paths()
    get_paths(repo_root)

    try:
        result = await asyncio.to_thread(
            run_plan,
            feature_description=feature_description,
        )

        return {"success": True, "plan": result, "feature": feature_description}

    except Exception as e:
        return {"success": False, "error": str(e), "feature": feature_description}
