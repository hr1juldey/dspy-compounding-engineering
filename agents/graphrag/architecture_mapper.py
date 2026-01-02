"""
ArchitectureMapperAgent: System architecture analysis.

Capabilities:
- Identify hub entities (PageRank)
- Detect module boundaries (clustering)
- Find architectural layers
- Spot bottlenecks
"""

import dspy

from agents.graphrag.schema import (
    ArchitectureReport,
    ClusterInfo,
    EntityHub,
)
from server.config import get_project_hash, registry
from utils.knowledge.embeddings_dspy import DSPyEmbeddingProvider as EmbeddingProvider
from utils.knowledge.graph import CodeGraphRAG
from utils.knowledge.graph_store import GraphStore
from utils.memory.module import MemoryPredict


class ArchitectureMapperSignature(dspy.Signature):
    """
    Map system architecture using graph analysis.

    Returns architecture summary, not recommendations.
    """

    analysis_scope: str = dspy.InputField(desc="Global|Module|Subsystem", default="Global")
    focus_area: str = dspy.InputField(default="", desc="Optional: specific module")

    architecture_map: ArchitectureReport = dspy.OutputField(
        desc="Architectural analysis with visual representation"
    )


class ArchitectureMapperModule(dspy.Module):
    """
    ArchitectureMapper module with GraphRAG + memory.

    Uses PageRank and clustering for architecture insights.
    """

    def __init__(self):
        super().__init__()

        # Initialize graph store + GraphRAG
        qdrant = registry.get_qdrant_client()
        project_hash = get_project_hash()
        graph_store = GraphStore(qdrant, EmbeddingProvider(), f"entities_{project_hash}")
        self.graph_rag = CodeGraphRAG(graph_store)

        # Memory-augmented predictor
        self.mapper = MemoryPredict(ArchitectureMapperSignature, agent_name="architecture_mapper")

    def forward(self, analysis_scope: str = "Global", focus_area: str = ""):
        # Build graph if not already built
        if not self.graph_rag.graph.nodes():
            self.graph_rag.build_full_graph()

        # Get hubs via PageRank
        top_entities = self.graph_rag.get_top_entities_by_pagerank(top_k=20)

        hubs = [
            EntityHub(
                entity_id=e["entity_id"],
                name=e["name"],
                type=e["type"],
                pagerank=e["pagerank"],
                file_path=e["file_path"],
            )
            for e in top_entities
        ]

        # Get clusters
        raw_clusters = self.graph_rag.get_graph_clusters(num_clusters=10)

        clusters = {}
        for cluster_id, entity_ids in raw_clusters.items():
            # Get entity details for cluster
            cluster_entities = [
                self.graph_rag.graph_store.get_entity(eid) for eid in entity_ids[:10]
            ]
            cluster_entities = [e for e in cluster_entities if e]

            clusters[cluster_id] = ClusterInfo(
                cluster_id=cluster_id,
                size=len(entity_ids),
                top_entities=[e.name for e in cluster_entities[:5]],
                files=list({e.file_path for e in cluster_entities}),
            )

        # Simple layer analysis (heuristic)
        layer_analysis = self._analyze_layers(hubs)

        # Identify bottlenecks (high PageRank + high fanout)
        bottlenecks = [h.name for h in hubs[:5] if h.pagerank > 0.01]

        return ArchitectureReport(
            summary=f"System has {len(clusters)} clusters, {len(hubs)} hub entities",
            hubs=hubs,
            clusters=clusters,
            layer_analysis=layer_analysis,
            bottlenecks=bottlenecks,
        )

    def _analyze_layers(self, hubs: list[EntityHub]) -> dict[str, list[str]]:
        """Simple heuristic layer analysis."""
        layers: dict[str, list[str]] = {
            "Presentation": [],
            "Application": [],
            "Domain": [],
        }

        for hub in hubs:
            if "agents/" in hub.file_path:
                layers["Presentation"].append(hub.name)
            elif "utils/" in hub.file_path:
                layers["Application"].append(hub.name)
            else:
                layers["Domain"].append(hub.name)

        return layers
