"""
mem0 configuration factory with Qdrant backend.

Provides mem0 config for agent-specific memory collections.
"""

import os

from config import get_project_hash, registry


def get_mem0_config(agent_name: str) -> dict:
    """
    Get mem0 configuration for agent-specific memory.

    Args:
        agent_name: Agent identifier (e.g., 'code_navigator')

    Returns:
        dict: mem0 configuration with Qdrant backend
    """
    qdrant_client = registry.get_qdrant_client()
    project_hash = get_project_hash()

    # Use OpenAI for mem0 LLM (required for fact extraction)
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY required for mem0")

    return {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "client": qdrant_client,
                "collection_name": f"mem_{agent_name}_{project_hash}",
                "embedding_model_dims": 1536,  # text-embedding-3-small
            },
        },
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
                "temperature": 0.1,
                "max_tokens": 2000,
            },
        },
        "version": "v1.1",
    }
