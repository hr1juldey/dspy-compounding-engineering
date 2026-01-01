"""
Pydantic schemas for GraphRAG agent outputs.

"Half-done answers" - structured findings for user confirmation.
"""

from pydantic import BaseModel, Field


class EntityDetails(BaseModel):
    """Entity information."""

    name: str
    type: str  # Function, Class, Method, Import, Module
    file_path: str
    line_start: int
    signature: str | None = None


class RelatedEntity(BaseModel):
    """Related entity reference."""

    name: str
    type: str
    file_path: str
    relation_type: str  # calls, called_by, imports, inherits


class CodeNavigationReport(BaseModel):
    """Output from CodeNavigatorAgent."""

    summary: str = Field(description="e.g., 'Found 12 callers across 5 files'")
    entity_details: EntityDetails
    relationships: dict[str, list[RelatedEntity]]  # {calls: [...], called_by: [...]}
    impact_scope: str  # Local|Module|System-wide
    next_actions: list[str]  # User options


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


class ArchitectureReport(BaseModel):
    """Output from ArchitectureMapperAgent."""

    summary: str
    hubs: list[EntityHub]  # Top PageRank entities
    clusters: dict[int, ClusterInfo]  # Module boundaries
    layer_analysis: dict[str, list[str]]  # {Presentation: [...], Application: [...]}
    bottlenecks: list[str]  # High fanout entities


class ImpactReport(BaseModel):
    """Output from ImpactAnalyzerAgent."""

    summary: str  # e.g., "23 entities across 8 files affected"
    direct_dependents: list[EntityDetails]  # 1st degree
    indirect_dependents: list[EntityDetails]  # 2nd-3rd degree
    critical_paths: list[list[str]]  # Paths to critical entities
    blast_radius: dict[str, int]  # {files: 8, functions: 15, classes: 8}
    risk_assessment: str  # Low|Medium|High|Critical
    recommended_approach: str


class CycleInfo(BaseModel):
    """Circular dependency information."""

    cycle_path: list[str]  # A → B → C → A
    cycle_type: str  # Import|Call|Inheritance


class DependencyReport(BaseModel):
    """Output from DependencyTracerAgent."""

    summary: str  # e.g., "Found 2 paths, 1 circular dependency"
    shortest_path: list[EntityDetails] | None
    all_paths: list[list[EntityDetails]]
    circular_dependencies: list[CycleInfo]
    coupling_metrics: dict[str, int]  # {import_depth: 4, fanout: 12}
    recommendations: list[str]
