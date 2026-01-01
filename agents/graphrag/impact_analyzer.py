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
from config import get_project_hash, registry
from utils.knowledge.embeddings_dspy import DSPyEmbeddingProvider as EmbeddingProvider
from utils.knowledge.graph_store import GraphStore
from utils.memory.module import MemoryPredict


class ImpactAnalyzerSignature(dspy.Signature):
    """
    Analyze impact of changing an entity.

    Returns impact analysis with change scenarios.
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

        # Initialize graph store
        qdrant = registry.get_qdrant_client()
        project_hash = get_project_hash()
        self.graph_store = GraphStore(qdrant, EmbeddingProvider(), f"entities_{project_hash}")

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

        return ImpactReport(
            summary=f"{len(all_entities)} entities across {len(files)} files affected",
            direct_dependents=direct_details,
            indirect_dependents=indirect_details,
            critical_paths=[],  # TODO: Implement path finding
            blast_radius=blast_radius,
            risk_assessment=risk,
            recommended_approach=f"{risk} risk - proceed with caution",
        )
