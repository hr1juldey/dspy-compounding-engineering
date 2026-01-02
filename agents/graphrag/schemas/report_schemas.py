"""Pydantic schemas for GraphRAG agent reports."""

from pydantic import BaseModel, Field

from agents.graphrag.schemas.entity_schemas import EntityDetails
from agents.graphrag.schemas.relationship_schemas import (
    ClusterInfo,
    CycleInfo,
    EntityHub,
    RelatedEntity,
)


class CodeNavigationReport(BaseModel):
    """Output from CodeNavigatorAgent."""

    summary: str = Field(description="e.g., 'Found 12 callers across 5 files'")
    entity_details: EntityDetails
    relationships: dict[str, list[RelatedEntity]]  # {calls: [...], called_by: [...]}
    impact_scope: str  # Local|Module|System-wide
    next_actions: list[str]  # User options


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


class DependencyReport(BaseModel):
    """Output from DependencyTracerAgent."""

    summary: str  # e.g., "Found 2 paths, 1 circular dependency"
    shortest_path: list[EntityDetails] | None
    all_paths: list[list[EntityDetails]]
    circular_dependencies: list[CycleInfo]
    coupling_metrics: dict[str, int]  # {import_depth: 4, fanout: 12}
    recommendations: list[str]
