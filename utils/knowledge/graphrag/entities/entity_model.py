"""
Entity data model and ID generation for code knowledge graph.

Entities represent code elements (functions, classes, methods, imports).
"""

import hashlib
from typing import Any

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """
    Graph node representing a code entity.

    Entities are stored in Qdrant with:
    - Dense vector embedding (semantic search)
    - Relations embedded in payload (no separate collection)
    """

    id: str  # Deterministic hash-based ID
    type: str  # Function, Class, Method, Import, Module
    name: str  # Entity name
    file_path: str  # Where defined
    line_start: int
    line_end: int

    # Core properties
    properties: dict[str, Any] = Field(default_factory=dict)

    # Relations (embedded in entity, not separate collection)
    relations: dict[str, list[str]] = Field(default_factory=dict)
    # Example: {"calls": ["func_id_1"], "imports": ["module_id"], "defines": ["method_id"]}

    # Embedding vector (populated later by embedding provider)
    embedding: list[float] = Field(default_factory=list)


def generate_entity_id(filepath: str, name: str, line: int) -> str:
    """
    Generate deterministic ID for entity.

    Format: hash(filepath:name:line)

    Args:
        filepath: File path where entity is defined
        name: Entity name
        line: Line number where entity starts

    Returns:
        16-character hex hash
    """
    unique_str = f"{filepath}::{name}::{line}"
    return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
