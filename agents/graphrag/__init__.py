"""
GraphRAG agents for deep code analysis.

Agents:
- CodeNavigatorAgent: Entity relationship navigation
- ArchitectureMapperAgent: PageRank + clustering analysis
- ImpactAnalyzerAgent: Blast radius calculation
- DependencyTracerAgent: Multi-hop dependency tracing
"""

from agents.graphrag.architecture_mapper import (
    ArchitectureMapperModule,
    ArchitectureMapperSignature,
)
from agents.graphrag.code_navigator import (
    CodeNavigatorModule,
    CodeNavigatorSignature,
)
from agents.graphrag.dependency_tracer import (
    DependencyTracerModule,
    DependencyTracerSignature,
)
from agents.graphrag.impact_analyzer import (
    ImpactAnalyzerModule,
    ImpactAnalyzerSignature,
)

__all__ = [
    "CodeNavigatorSignature",
    "CodeNavigatorModule",
    "ArchitectureMapperSignature",
    "ArchitectureMapperModule",
    "ImpactAnalyzerSignature",
    "ImpactAnalyzerModule",
    "DependencyTracerSignature",
    "DependencyTracerModule",
]
