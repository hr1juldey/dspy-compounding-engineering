"""
Analysis subserver - GraphRAG code analysis and planning tools.

Contains tools that use DSPy agents for code understanding.
"""

import asyncio

from fastmcp import FastMCP
from infrastructure.events.decorators import track_tool_execution

from utils.paths import get_paths, reset_paths
from workflows.analyze import run_analyze
from workflows.plan import run_plan

analysis_server = FastMCP("Analysis")


@analysis_server.tool(task=True)
@track_tool_execution(total_stages=3)
async def analyze_code(
    repo_root: str,
    entity: str,
    analysis_type: str = "navigate",
    max_depth: int = 2,
    change_type: str = "Modify",
    save: bool = True,
    ctx=None,
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
    reset_paths()
    get_paths(repo_root)

    try:
        if ctx:
            await ctx.report_progress(progress=2, total=3, message="Analyzing code...")

        # Run sync workflow in thread pool with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(
                run_analyze,
                entity=entity,
                analysis_type=analysis_type,
                max_depth=max_depth,
                change_type=change_type,
                save=save,
            ),
            timeout=600,  # 10 minutes
        )

        return {"success": True, "result": result, "entity": entity, "type": analysis_type}

    except asyncio.TimeoutError:
        if ctx:
            ctx.logger.error("Code analysis timed out after 10 minutes")
        raise
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Code analysis failed: {e}")
        raise


@analysis_server.tool(task=True)
@track_tool_execution(total_stages=4)
async def generate_plan(
    repo_root: str,
    feature_description: str,
    ctx=None,
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
    reset_paths()
    get_paths(repo_root)

    try:
        if ctx:
            await ctx.report_progress(progress=2, total=4, message="Researching...")

        if ctx:
            await ctx.report_progress(progress=3, total=4, message="Generating plan...")

        result = await asyncio.wait_for(
            asyncio.to_thread(
                run_plan,
                feature_description=feature_description,
            ),
            timeout=600,  # 10 minutes
        )

        return {"success": True, "plan": result, "feature": feature_description}

    except asyncio.TimeoutError:
        if ctx:
            ctx.logger.error("Plan generation timed out after 10 minutes")
        raise
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Plan generation failed: {e}")
        raise
