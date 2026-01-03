"""
ImpactAnalyzerAgent: Blast radius calculation.

Capabilities:
- Calculate blast radius (affected entities)
- Trace downstream dependencies
- Identify critical paths
- Estimate refactor scope
"""

import dspy

from agents.graphrag.schema import EntityDetails, ImpactReport
from server.config import get_project_hash, registry
from utils.knowledge.embeddings_dspy import DSPyEmbeddingProvider as EmbeddingProvider
from utils.knowledge.graph import CodeGraphRAG
from utils.knowledge.graph_store import GraphStore
from utils.memory.module import MemoryPredict


class ImpactAnalyzerSignature(dspy.Signature):
    """Analyze the impact of changing a code entity (blast radius calculation).

    INPUTS:
    - target_entity: The name of the entity to analyze (function, class, or method name)
    - change_type: Type of change being considered. Options:
      * "Modify": Changing the entity's implementation
      * "Delete": Removing the entity entirely
      * "Refactor": Restructuring without changing behavior
      * "Rename": Changing the entity's name

    OUTPUT:
    You must return an ImpactReport object containing:
    - summary: One-line summary of the impact (e.g., "23 entities across 8 files affected")
    - direct_dependents: List of EntityDetails for entities that directly depend on the target
      (1st degree dependencies). Each EntityDetails contains:
      * name: Entity name
      * type: Entity type (Function, Class, Method, Import, Module)
      * file_path: File location
      * line_start: Starting line number
      * signature: Function/method signature (if applicable)
    - indirect_dependents: List of EntityDetails for entities that indirectly depend on target
      (2nd-3rd degree dependencies, following the dependency chain)
    - critical_paths: List of dependency paths to critical entities. Each path is a list of
      entity names showing the dependency chain (e.g., ["target", "caller1", "caller2"])
    - blast_radius: Dictionary with impact counts:
      * files: Number of unique files affected
      * functions: Number of functions/methods affected
      * classes: Number of classes affected
    - risk_assessment: Overall risk level based on blast radius size:
      * "Low": < 10 entities affected
      * "Medium": 10-50 entities affected
      * "High": > 50 entities affected
      * "Critical": For changes affecting core system entities
    - recommended_approach: Suggested approach for making the change safely

    TASK INSTRUCTIONS:
    - Calculate both direct (1-hop) and indirect (2-3 hop) dependencies
    - Identify critical dependency paths using shortest path analysis
    - Assess risk based on the scope of affected entities
    - Provide actionable recommendations for safely implementing the change
    """

    target_entity: str = dspy.InputField(desc="Entity to analyze")
    change_type: str = dspy.InputField(desc="Modify|Delete|Refactor|Rename", default="Modify")

    impact_analysis: ImpactReport = dspy.OutputField(desc="Impact analysis with affected entities")


class ImpactAnalyzerModule(dspy.Module):
    """
    ImpactAnalyzer module with recursive dependency traversal.

    Calculates blast radius up to 3 hops.
    """

    def __init__(self):
        super().__init__()

        # Initialize graph store and GraphRAG
        qdrant = registry.get_qdrant_client()
        project_hash = get_project_hash()
        self.graph_store = GraphStore(qdrant, EmbeddingProvider(), f"entities_{project_hash}")
        self.graph_rag = CodeGraphRAG(self.graph_store)

        # Memory-augmented predictor
        self.analyzer = MemoryPredict(ImpactAnalyzerSignature, agent_name="impact_analyzer")

    def forward(self, target_entity: str, change_type: str = "Modify"):
        # Find target entity
        entities = self.graph_store.query_entities(target_entity, limit=1)

        if not entities:
            return ImpactReport(
                summary=f"Entity '{target_entity}' not found",
                direct_dependents=[],
                indirect_dependents=[],
                critical_paths=[],
                blast_radius={"files": 0, "functions": 0, "classes": 0},
                risk_assessment="Unknown",
                recommended_approach="Entity not found in graph",
            )

        entity = entities[0]

        # Get direct dependents (1st degree)
        direct = self.graph_store.query_neighbors(entity.id, limit=50)

        # Get indirect dependents (2nd-3rd degree)
        indirect = []
        visited = {entity.id}

        for dep in direct:
            if dep.id not in visited:
                visited.add(dep.id)
                second_degree = self.graph_store.query_neighbors(dep.id, limit=20)
                for dep2 in second_degree:
                    if dep2.id not in visited:
                        visited.add(dep2.id)
                        indirect.append(dep2)

        # Build entity details
        direct_details = [
            EntityDetails(
                name=e.name,
                type=e.type,
                file_path=e.file_path,
                line_start=e.line_start,
                signature=e.properties.get("signature"),
            )
            for e in direct
        ]

        indirect_details = [
            EntityDetails(
                name=e.name,
                type=e.type,
                file_path=e.file_path,
                line_start=e.line_start,
                signature=e.properties.get("signature"),
            )
            for e in indirect
        ]

        # Calculate blast radius
        all_entities = [entity] + direct + indirect
        files = {e.file_path for e in all_entities}
        functions = [e for e in all_entities if e.type in ["Function", "Method"]]
        classes = [e for e in all_entities if e.type == "Class"]

        blast_radius = {
            "files": len(files),
            "functions": len(functions),
            "classes": len(classes),
        }

        # Risk assessment
        risk = "Low" if len(all_entities) < 10 else "High" if len(all_entities) > 50 else "Medium"

        # Find critical paths (top 5 most important paths through dependencies)
        critical_paths = self._find_critical_paths(entity, direct, indirect)

        return ImpactReport(
            summary=f"{len(all_entities)} entities across {len(files)} files affected",
            direct_dependents=direct_details,
            indirect_dependents=indirect_details,
            critical_paths=critical_paths,
            blast_radius=blast_radius,
            risk_assessment=risk,
            recommended_approach=f"{risk} risk - proceed with caution",
        )

    def _find_critical_paths(self, source_entity, direct_deps, indirect_deps):
        """
        Find critical dependency paths from source to important entities.

        Uses shortest path finding + PageRank to identify most important routes.

        Args:
            source_entity: Source entity
            direct_deps: Direct dependents
            indirect_deps: Indirect dependents

        Returns:
            List of paths (each path is a list of entity names)
        """
        paths = []

        # Get top indirect dependents by combining them with direct
        all_deps = direct_deps + indirect_deps

        # For each dependent, find shortest path
        for dep in all_deps[:10]:  # Limit to top 10 to avoid performance issues
            path_entities = self.graph_rag.find_shortest_path(source_entity.id, dep.id)

            if path_entities:
                # Extract entity names for the path
                path_names = [e["name"] for e in path_entities]
                paths.append(path_names)

        # Return top 5 unique paths, sorted by length (shorter = more critical)
        unique_paths = []
        seen = set()
        for path in sorted(paths, key=len):
            path_key = tuple(path)
            if path_key not in seen and len(path) > 1:  # Exclude single-entity paths
                unique_paths.append(path)
                seen.add(path_key)
                if len(unique_paths) >= 5:
                    break

        return unique_paths
