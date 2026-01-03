"""
DependencyTracerAgent: Multi-hop dependency tracing.

Capabilities:
- Find shortest path between entities
- Detect circular dependencies
- Trace import chains
- Identify tight coupling
"""

import dspy
import networkx as nx

from agents.graphrag.schema import CycleInfo, DependencyReport, EntityDetails
from server.config import get_project_hash, registry
from utils.knowledge.embeddings.provider import DSPyEmbeddingProvider as EmbeddingProvider
from utils.knowledge.graphrag.graph import CodeGraphRAG
from utils.knowledge.graphrag.graph_store import GraphStore
from utils.memory.module import MemoryPredict


class DependencyTracerSignature(dspy.Signature):
    """Trace multi-hop dependencies between entities and detect circular dependencies.

    INPUTS:
    - source_entity: Name of the starting entity (function, class, or module name)
    - target_entity: Name of the target entity to find path to, OR the special value
      "detect_cycles" to search for circular dependencies starting from source_entity.
      Leave empty to analyze all paths from source.

    OUTPUT:
    You must return a DependencyReport object containing:
    - summary: One-line summary of dependency analysis
      (e.g., "Found 2 paths, 1 circular dependency" or "Found path with 3 hops")
    - shortest_path: List of EntityDetails representing the shortest dependency path from
      source to target (None if no path exists or if detecting cycles). Path ordered from
      source to target. Each EntityDetails contains:
      * name: Entity name
      * type: Entity type (Function, Class, Method, Import, Module)
      * file_path: File location
      * line_start: Starting line number
    - all_paths: List of all dependency paths found (each path is a list of EntityDetails).
      Include multiple paths if they exist. Empty list if no paths found.
    - circular_dependencies: List of CycleInfo objects for circular dependencies detected.
      Each CycleInfo contains:
      * cycle_path: List of entity names forming the cycle (e.g., ["A", "B", "C", "A"])
      * cycle_type: Type of cycle ("Import", "Call", "Inheritance", or "Dependency")
    - coupling_metrics: Dictionary with coupling measurements:
      * "path_length": Number of hops in the dependency chain
      * "import_depth": Number of import levels
      * "fanout": Number of dependencies from source
      (Include metrics that are relevant to the analysis)
    - recommendations: List of actionable recommendations based on the dependency analysis
      (e.g., "Break cycle at EntityA", "Consider reducing import depth",
      "Path found - entities are connected")

    TASK INSTRUCTIONS:
    - Use graph traversal to find dependency paths between entities
    - When target_entity is "detect_cycles", focus on finding circular dependencies
    - Report the shortest path first, then include alternative paths
    - Identify cycle types (import cycles, call cycles, inheritance cycles)
    - Calculate coupling metrics to assess dependency health
    - Provide specific recommendations for reducing coupling or breaking cycles
    """

    source_entity: str = dspy.InputField(desc="Start entity")
    target_entity: str = dspy.InputField(desc="Target entity (or 'detect_cycles')", default="")

    dependency_trace: DependencyReport = dspy.OutputField(
        desc="Dependency paths and cycle analysis"
    )


class DependencyTracerModule(dspy.Module):
    """
    DependencyTracer module with NetworkX path finding.

    Uses CodeGraphRAG for multi-hop traversal.
    """

    def __init__(self):
        super().__init__()

        # Initialize graph store + GraphRAG
        qdrant = registry.get_qdrant_client()
        project_hash = get_project_hash()
        graph_store = GraphStore(qdrant, EmbeddingProvider(), f"entities_{project_hash}")
        self.graph_rag = CodeGraphRAG(graph_store)

        # Memory-augmented predictor
        self.tracer = MemoryPredict(DependencyTracerSignature, agent_name="dependency_tracer")

    def forward(self, source_entity: str, target_entity: str = ""):
        # Build graph if needed
        if not self.graph_rag.graph.nodes():
            self.graph_rag.build_full_graph()

        # Find source entity
        source_entities = self.graph_rag.graph_store.query_entities(source_entity, limit=1)

        if not source_entities:
            return DependencyReport(
                summary=f"Source entity '{source_entity}' not found",
                shortest_path=None,
                all_paths=[],
                circular_dependencies=[],
                coupling_metrics={},
                recommendations=["Verify entity name"],
            )

        source = source_entities[0]

        # Detect cycles if requested
        if target_entity == "detect_cycles":
            cycles = self._detect_cycles(source)
            return DependencyReport(
                summary=f"Found {len(cycles)} circular dependencies",
                shortest_path=None,
                all_paths=[],
                circular_dependencies=cycles,
                coupling_metrics={},
                recommendations=[f"Break cycle at {c.cycle_path[0]}" for c in cycles],
            )

        # Find target entity
        target_entities = self.graph_rag.graph_store.query_entities(target_entity, limit=1)

        if not target_entities:
            return DependencyReport(
                summary=f"Target entity '{target_entity}' not found",
                shortest_path=None,
                all_paths=[],
                circular_dependencies=[],
                coupling_metrics={},
                recommendations=["Verify target name"],
            )

        target = target_entities[0]

        # Find paths
        path_result = self.graph_rag.find_shortest_path(source.id, target.id)

        if not path_result:
            return DependencyReport(
                summary="No path found",
                shortest_path=None,
                all_paths=[],
                circular_dependencies=[],
                coupling_metrics={},
                recommendations=["Entities are not connected"],
            )

        # Convert to EntityDetails
        shortest_path = [
            EntityDetails(
                name=e["name"],
                type=e["type"],
                file_path=e["file_path"],
                line_start=0,
            )
            for e in path_result
        ]

        return DependencyReport(
            summary=f"Found path with {len(shortest_path) - 1} hops",
            shortest_path=shortest_path,
            all_paths=[shortest_path],
            circular_dependencies=[],
            coupling_metrics={"path_length": len(shortest_path) - 1},
            recommendations=["Path found"],
        )

    def _detect_cycles(self, source) -> list[CycleInfo]:
        """Detect circular dependencies."""
        cycles = []

        try:
            # Find simple cycles starting from source
            for cycle in nx.simple_cycles(self.graph_rag.graph, length_bound=10):
                if source.id in cycle:
                    cycle_names = [self.graph_rag.graph_store.get_entity(eid).name for eid in cycle]
                    cycles.append(CycleInfo(cycle_path=cycle_names, cycle_type="Dependency"))

                    if len(cycles) >= 5:  # Limit to 5 cycles
                        break
        except Exception:
            pass  # No cycles found

        return cycles
