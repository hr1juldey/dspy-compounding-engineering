"""
GraphRAG-specific tools for DSPy agents.

Triggers deep graph analysis when semantic search isn't enough.
"""

import json
from typing import cast

import dspy

from agents.graphrag.architecture_mapper import ArchitectureMapperModule
from agents.graphrag.code_navigator import CodeNavigatorModule
from agents.graphrag.dependency_tracer import DependencyTracerModule
from agents.graphrag.impact_analyzer import ImpactAnalyzerModule


def get_graphrag_tools() -> list[dspy.Tool]:
    """
    Get GraphRAG analysis tools.

    Heavyweight tools - use after lightweight semantic search.
    """
    return [
        get_entity_search_tool(),
        get_impact_analysis_tool(),
        get_architecture_map_tool(),
        get_dependency_trace_tool(),
    ]


def get_entity_search_tool() -> dspy.Tool:
    """Find entities by name and relationships."""

    def search_entity(entity_name: str, max_depth: int = 2) -> str:
        """
        Search for entity and its relationships.

        Args:
            entity_name: Name of function/class/method
            max_depth: Relationship depth (1-3)

        Returns:
            JSON string with entity details + relationships
        """
        navigator = CodeNavigatorModule()
        result = cast(dspy.Prediction, navigator(query=entity_name, max_depth=max_depth))

        return json.dumps(result.model_dump(), indent=2)

    return dspy.Tool(search_entity)


def get_impact_analysis_tool() -> dspy.Tool:
    """Analyze blast radius of changing an entity."""

    def analyze_impact(entity_name: str, change_type: str = "Modify") -> str:
        """
        Calculate impact of changing an entity.

        Args:
            entity_name: Entity to analyze
            change_type: Modify|Delete|Refactor|Rename

        Returns:
            JSON with affected entities, blast radius
        """
        analyzer = ImpactAnalyzerModule()
        result = cast(dspy.Prediction, analyzer(target_entity=entity_name, change_type=change_type))

        return json.dumps(result.model_dump(), indent=2)

    return dspy.Tool(analyze_impact)


def get_architecture_map_tool() -> dspy.Tool:
    """Map system architecture using PageRank."""

    def map_architecture(scope: str = "Global") -> str:
        """
        Generate architecture map with hubs and clusters.

        Args:
            scope: Global|Module|Subsystem

        Returns:
            JSON with PageRank hubs, clusters, layers
        """
        mapper = ArchitectureMapperModule()
        result = cast(dspy.Prediction, mapper(analysis_scope=scope))

        return json.dumps(result.model_dump(), indent=2)

    return dspy.Tool(map_architecture)


def get_dependency_trace_tool() -> dspy.Tool:
    """Trace dependency paths between entities."""

    def trace_dependency(source: str, target: str = "") -> str:
        """
        Find shortest path from source to target entity.

        Args:
            source: Source entity name
            target: Target entity (or 'detect_cycles')

        Returns:
            JSON with path, circular deps
        """
        tracer = DependencyTracerModule()
        result = cast(dspy.Prediction, tracer(source_entity=source, target_entity=target))

        return json.dumps(result.model_dump(), indent=2)

    return dspy.Tool(trace_dependency)
