"""
Multi-hop search over code graph using DSPy + dspy-qdrant.

Combines HNSW vector search with NetworkX graph traversal.
"""

import dspy
from dspy_qdrant import QdrantRM
from pydantic import BaseModel

from server.config import get_project_hash, registry
from utils.knowledge.embeddings_dspy import DSPyEmbeddingProvider as EmbeddingProvider
from utils.knowledge.graph_rag import CodeGraphRAG
from utils.knowledge.graph_store import GraphStore
from utils.memory.module import MemoryPredict


class MultiHopResult(BaseModel):
    """Multi-hop search result."""

    found: bool
    hops: int
    path: list[dict]  # [{entity, type, file, line}]
    alternative_paths: list[list[dict]]
    reasoning: str  # How path was discovered


class MultiHopSearchSignature(dspy.Signature):
    """
    Multi-hop search over code graph.

    Strategy:
    1. HNSW vector search for initial candidates
    2. Graph traversal to find path
    3. PageRank re-ranking
    """

    start_query: str = dspy.InputField(desc="Starting point (entity or concept)")
    target_query: str = dspy.InputField(desc="Target to find")
    max_hops: int = dspy.InputField(default=3, desc="Maximum hops (1-5)")

    search_result: MultiHopResult = dspy.OutputField(desc="Multi-hop search results")


class MultiHopSearcher(dspy.Module):
    """
    Multi-hop searcher using dspy-qdrant + NetworkX.

    Combines vector search with graph structure.
    """

    def __init__(self):
        super().__init__()

        # dspy-qdrant retriever
        qdrant = registry.get_qdrant_client()
        project_hash = get_project_hash()

        self.retriever = QdrantRM(
            qdrant_client=qdrant,
            qdrant_collection_name=f"entities_{project_hash}",
            k=10,
        )

        # Graph RAG for traversal
        graph_store = GraphStore(qdrant, EmbeddingProvider(), f"entities_{project_hash}")
        self.graph_rag = CodeGraphRAG(graph_store)

        # Memory-augmented predictor
        self.searcher = MemoryPredict(MultiHopSearchSignature, agent_name="multi_hop_searcher")

    def forward(self, start_query: str, target_query: str, max_hops: int = 3):
        # Step 1: Find start entities via HNSW
        start_results = self.retriever(start_query)
        if not start_results:
            return MultiHopResult(
                found=False,
                hops=0,
                path=[],
                alternative_paths=[],
                reasoning="Start entity not found",
            )

        # Step 2: Find target entities via HNSW
        target_results = self.retriever(target_query)
        if not target_results:
            return MultiHopResult(
                found=False,
                hops=0,
                path=[],
                alternative_paths=[],
                reasoning="Target entity not found",
            )

        # Step 3: Find paths using NetworkX
        if not self.graph_rag.graph.nodes():
            self.graph_rag.build_full_graph()

        # Get entity IDs from results
        start_id = start_results[0]["id"]
        target_id = target_results[0]["id"]

        # Find path
        path = self.graph_rag.find_shortest_path(start_id, target_id)

        if not path:
            return MultiHopResult(
                found=False,
                hops=max_hops,
                path=[],
                alternative_paths=[],
                reasoning="No path found within max hops",
            )

        # Format path
        formatted_path = [
            {
                "entity": e["name"],
                "type": e["type"],
                "file": e["file_path"],
                "line": 0,
            }
            for e in path
        ]

        return MultiHopResult(
            found=True,
            hops=len(path) - 1,
            path=formatted_path,
            alternative_paths=[],
            reasoning=f"Found via {len(path)} hops using HNSW + NetworkX",
        )
