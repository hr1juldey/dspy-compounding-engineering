"""
Knowledge subserver - knowledge base management tools.

Contains tools for indexing, gardening, codifying, and compressing knowledge.
"""

import asyncio

from fastmcp import FastMCP

from server.infrastructure.events.decorators import track_tool_execution
from utils.knowledge import KnowledgeBase
from utils.paths import get_paths, reset_paths
from workflows.codify import run_codify
from workflows.garden import run_garden

knowledge_server = FastMCP("Knowledge")


@knowledge_server.tool(task=True)  # SLOW: background if client supports (optional mode)
@track_tool_execution(total_stages=2)
async def index_codebase(
    repo_root: str,
    recreate: bool = False,
    with_graphrag: bool = False,
    ctx=None,
) -> dict:
    """
    Index codebase for semantic search.

    Args:
        repo_root: Root directory of repository
        recreate: Force recreation of vector collection
        with_graphrag: Enable GraphRAG entity extraction (slower but richer)

    Returns:
        Indexing result dictionary
    """
    reset_paths()
    get_paths(repo_root)

    try:
        loop = asyncio.get_event_loop()

        def progress_callback(filepath: str, processed: int, total: int):
            """Stream indexing progress via MCP (thread-safe)."""
            if ctx:
                # Use run_coroutine_threadsafe to call async from worker thread
                asyncio.run_coroutine_threadsafe(
                    ctx.report_progress(
                        progress=processed,
                        total=total,
                        message=f"Indexed {processed}/{total}: {filepath}",
                    ),
                    loop,
                )

        kb = KnowledgeBase()

        # Run indexing in thread pool with live progress streaming
        result = await asyncio.wait_for(
            asyncio.to_thread(
                kb.index_codebase,
                root_dir=repo_root,
                force_recreate=recreate,
                with_graphrag=with_graphrag,
                progress_callback=progress_callback,
            ),
            timeout=600,  # 10 minutes
        )

        return {"success": True, "result": result, "repo_root": repo_root}

    except asyncio.TimeoutError:
        if ctx:
            ctx.logger.error("Codebase indexing timed out after 10 minutes")
        raise
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Codebase indexing failed: {e}")
        raise


@knowledge_server.tool(task=True)  # SLOW: background if client supports (optional mode)
@track_tool_execution(total_stages=3)
async def garden_knowledge(
    repo_root: str,
    action: str = "consolidate",
    limit: int = 100,
    ctx=None,
) -> dict:
    """
    Maintain knowledge base.

    Args:
        repo_root: Root directory of repository
        action: Action (consolidate|compress-memory|index-commits|all)
        limit: Max commits to index

    Returns:
        Garden result dictionary
    """
    reset_paths()
    get_paths(repo_root)

    try:
        if ctx:
            await ctx.report_progress(
                progress=0, total=1, message="Starting knowledge gardening..."
            )

        # Run gardening (stage progress happens inside)
        result = await asyncio.wait_for(
            asyncio.to_thread(run_garden, action=action, limit=limit),
            timeout=600,  # 10 minutes
        )

        if ctx:
            await ctx.report_progress(progress=1, total=1, message=f"Gardening complete: {action}")

        return {"success": True, "result": result, "action": action}

    except asyncio.TimeoutError:
        if ctx:
            ctx.logger.error("Knowledge base gardening timed out after 10 minutes")
        raise
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Knowledge base gardening failed: {e}")
        raise


@knowledge_server.tool(task=True)  # SLOW: background if client supports (optional mode)
@track_tool_execution(total_stages=3)
async def codify_feedback(
    repo_root: str,
    feedback: str,
    source: str = "manual_input",
    ctx=None,
) -> dict:
    """
    Codify feedback into knowledge base.

    Args:
        repo_root: Root directory of repository
        feedback: Feedback, instruction, or learning to codify
        source: Source of feedback (e.g., 'review', 'retro', 'manual_input')

    Returns:
        Codification result dictionary
    """
    reset_paths()
    get_paths(repo_root)

    try:
        if ctx:
            await ctx.report_progress(progress=0, total=1, message="Starting codification...")

        result = await asyncio.wait_for(
            asyncio.to_thread(run_codify, feedback=feedback, source=source),
            timeout=600,  # 10 minutes
        )

        if ctx:
            await ctx.report_progress(progress=1, total=1, message="Codification complete")

        return {"success": True, "result": result, "feedback": feedback, "source": source}

    except asyncio.TimeoutError:
        if ctx:
            ctx.logger.error("Feedback codification timed out after 10 minutes")
        raise
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Feedback codification failed: {e}")
        raise


@knowledge_server.tool(task=True)  # SLOW: background if client supports (optional mode)
@track_tool_execution(total_stages=3)
async def compress_knowledge_base(
    repo_root: str,
    ratio: float = 0.5,
    dry_run: bool = False,
    ctx=None,
) -> dict:
    """
    Compress AI.md knowledge base semantically.

    Args:
        repo_root: Root directory of repository
        ratio: Target compression ratio (0.0 to 1.0)
        dry_run: Preview mode without modifying file

    Returns:
        Compression result dictionary
    """
    if not (0.0 <= ratio <= 1.0):
        if ctx:
            ctx.logger.error("Ratio must be between 0.0 and 1.0")
        raise ValueError("Ratio must be between 0.0 and 1.0")

    reset_paths()
    get_paths(repo_root)

    try:
        if ctx:
            await ctx.report_progress(progress=0, total=1, message="Starting compression...")

        kb = KnowledgeBase()

        result = await asyncio.wait_for(
            asyncio.to_thread(kb.compress_ai_md, ratio=ratio, dry_run=dry_run),
            timeout=600,  # 10 minutes
        )

        if ctx:
            await ctx.report_progress(progress=1, total=1, message="Compression complete")

        return {"success": True, "result": result, "ratio": ratio, "dry_run": dry_run}

    except asyncio.TimeoutError:
        if ctx:
            ctx.logger.error("Knowledge base compression timed out after 10 minutes")
        raise
    except Exception as e:
        if ctx:
            ctx.logger.error(f"Knowledge base compression failed: {e}")
        raise
