"""
MCP tools for knowledge base management.
"""

from server.application.services.codify_service import CodifyService
from server.application.services.compress_kb_service import CompressKBService
from server.application.services.garden_service import GardenService
from server.application.services.index_codebase_service import IndexCodebaseService
from server.mcp.server import mcp


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
def codify_feedback(repo_root: str, feedback: str, source: str = "manual_input") -> dict:
    """
    Codify feedback into knowledge base (async - returns task_id).

    Transforms raw feedback into structured improvements.

    Args:
        repo_root: Root directory of repository
        feedback: Feedback, instruction, or learning to codify
        source: Source of feedback (e.g., 'review', 'retro', 'manual_input')

    Returns:
        Task submission info with task_id
    """
    service = CodifyService()
    task_id = service.submit_codify(repo_root=repo_root, feedback=feedback, source=source)
    return {"task_id": task_id, "status": "submitted"}


@mcp.tool()
def compress_knowledge_base(repo_root: str, ratio: float = 0.5, dry_run: bool = False) -> dict:
    """
    Compress AI.md knowledge base (async - returns task_id).

    Semantically compresses KB to reduce token usage while preserving learnings.

    Args:
        repo_root: Root directory of repository
        ratio: Target compression ratio (0.0 to 1.0)
        dry_run: Preview mode without modifying file

    Returns:
        Task submission info with task_id
    """
    if not (0.0 <= ratio <= 1.0):
        raise ValueError("Ratio must be between 0.0 and 1.0")

    service = CompressKBService()
    task_id = service.submit_compression(repo_root=repo_root, ratio=ratio, dry_run=dry_run)
    return {"task_id": task_id, "status": "submitted"}


@mcp.tool()
def index_codebase(repo_root: str, recreate: bool = False, with_graphrag: bool = False) -> dict:
    """
    Index codebase for semantic search (async - returns task_id).

    Indexes code into Qdrant vector database for GraphRAG and agents.
    Performs smart incremental indexing (skips unchanged files).

    GraphRAG Mode (with_graphrag=True):
    - Extracts code entities (functions, classes, methods)
    - Builds knowledge graph with relationships
    - Enables advanced code navigation and impact analysis
    - WARNING: Significantly slower than standard indexing

    Args:
        repo_root: Root directory of repository
        recreate: Force recreation of vector collection
        with_graphrag: Enable GraphRAG entity extraction

    Returns:
        Task submission info with task_id
    """
    service = IndexCodebaseService()
    task_id = service.submit_indexing(
        repo_root=repo_root, recreate=recreate, with_graphrag=with_graphrag
    )
    return {"task_id": task_id, "status": "submitted"}
