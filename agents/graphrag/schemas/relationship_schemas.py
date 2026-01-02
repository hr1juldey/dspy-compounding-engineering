"""Pydantic schemas for entity relationships and clusters."""

from pydantic import BaseModel

from agents.graphrag.schemas.entity_schemas import InteractionFlow


class RelatedEntity(BaseModel):
    """Related entity (Dimensions 2 & 4)."""

    name: str
    type: str
    file_path: str
    # Dimension 2: Relation
    relation_type: str  # calls, called_by, imports, inherits
    # Dimension 4: Interaction
    interaction_flow: InteractionFlow | None = None
    context: str | None = None


class EntityHub(BaseModel):
    """Hub entity with PageRank score."""

    entity_id: str
    name: str
    type: str
    pagerank: float
    file_path: str


class ClusterInfo(BaseModel):
    """Module cluster information."""

    cluster_id: int
    size: int  # Number of entities
    top_entities: list[str]  # Entity names
    files: list[str]  # Files in cluster


class CycleInfo(BaseModel):
    """Circular dependency information."""

    cycle_path: list[str]  # A → B → C → A
    cycle_type: str  # Import|Call|Inheritance
