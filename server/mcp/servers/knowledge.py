"""
Knowledge subserver - knowledge base management tools.

Contains tools for indexing, gardening, codifying, and compressing knowledge.
"""

import asyncio

from fastmcp import FastMCP

from utils.knowledge import KnowledgeBase
from utils.paths import CompoundingPaths
from workflows.codify import run_codify
from workflows.garden import run_garden

knowledge_server = FastMCP("Knowledge")


@knowledge_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def index_codebase(
    repo_root: str,
    recreate: bool = False,
    with_graphrag: bool = False,
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
    CompoundingPaths(repo_root)

    try:
        kb = KnowledgeBase()

        # Run indexing in thread pool (sync operation)
        result = await asyncio.to_thread(
            kb.index_codebase,
            root_dir=repo_root,
            force_recreate=recreate,
            with_graphrag=with_graphrag,
        )

        return {"success": True, "result": result, "repo_root": repo_root}

    except Exception as e:
        return {"success": False, "error": str(e), "repo_root": repo_root}


@knowledge_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def garden_knowledge(
    repo_root: str,
    action: str = "consolidate",
    limit: int = 100,
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
    CompoundingPaths(repo_root)

    try:
        result = await asyncio.to_thread(run_garden, action=action, limit=limit)

        return {"success": True, "result": result, "action": action}

    except Exception as e:
        return {"success": False, "error": str(e), "action": action}


@knowledge_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def codify_feedback(
    repo_root: str,
    feedback: str,
    source: str = "manual_input",
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
    CompoundingPaths(repo_root)

    try:
        result = await asyncio.to_thread(run_codify, feedback=feedback, source=source)

        return {"success": True, "result": result, "feedback": feedback, "source": source}

    except Exception as e:
        return {"success": False, "error": str(e), "feedback": feedback}


@knowledge_server.tool(task=True)  # SLOW: background if client supports (optional mode)
async def compress_knowledge_base(
    repo_root: str,
    ratio: float = 0.5,
    dry_run: bool = False,
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
        return {"success": False, "error": "Ratio must be between 0.0 and 1.0"}

    CompoundingPaths(repo_root)

    try:
        kb = KnowledgeBase()

        result = await asyncio.to_thread(kb.compress_ai_md, ratio=ratio, dry_run=dry_run)

        return {"success": True, "result": result, "ratio": ratio, "dry_run": dry_run}

    except Exception as e:
        return {"success": False, "error": str(e), "ratio": ratio}
