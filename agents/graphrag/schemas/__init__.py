"""
GraphRAG schemas package.

Exports all Pydantic models for agent inputs/outputs.
"""

from agents.graphrag.schemas.entity_schemas import (
    CodeChange,
    EntityDetails,
    FunctionIO,
    GitHistory,
    InteractionFlow,
    ParameterInfo,
)
from agents.graphrag.schemas.relationship_schemas import (
    ClusterInfo,
    CycleInfo,
    EntityHub,
    RelatedEntity,
)
from agents.graphrag.schemas.report_schemas import (
    ArchitectureReport,
    CodeNavigationReport,
    DependencyReport,
    ImpactReport,
)

__all__ = [
    # Entity schemas
    "ParameterInfo",
    "FunctionIO",
    "InteractionFlow",
    "CodeChange",
    "GitHistory",
    "EntityDetails",
    # Relationship schemas
    "RelatedEntity",
    "EntityHub",
    "ClusterInfo",
    "CycleInfo",
    # Report schemas
    "CodeNavigationReport",
    "ArchitectureReport",
    "ImpactReport",
    "DependencyReport",
]
