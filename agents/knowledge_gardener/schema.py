"""
Knowledge Gardener Pydantic schemas.

Structured outputs for KnowledgeGardener components.
"""

from pydantic import BaseModel


class KnowledgeGardenerResult(BaseModel):
    """Structured output from KnowledgeGardenerOrchestrator."""

    # KB results
    compressed_knowledge_json: str
    identified_patterns: str
    pattern_summary: str

    # Memory results
    compressed_memories_json: str
    compression_stats: dict

    # Commit results
    shared_commit_memory_json: str
    indexing_summary: str
