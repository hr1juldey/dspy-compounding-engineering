"""
Multi-hop search over code graph using DSPy + dspy-qdrant.

Combines HNSW vector search with NetworkX graph traversal.
"""

import dspy
from dspy_qdrant import QdrantRM
from pydantic import BaseModel

from server.config import get_project_hash, registry
from utils.knowledge.embeddings_dspy import DSPyEmbeddingProvider as EmbeddingProvider
from utils.knowledge.graph import CodeGraphRAG
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
    """Search for dependency paths between code entities using multi-hop graph traversal.

    INPUTS:
    - start_query: Natural language query or entity name for the starting point
      (e.g., "process_data function", "authentication module", "User class")
    - target_query: Natural language query or entity name for the target to find
      (e.g., "database connection", "logging handler", "error handling")
    - max_hops: Maximum number of relationship hops to traverse (1-5):
      * 1: Direct dependencies only
      * 2: Two-hop dependencies (A → B → C)
      * 3: Three-hop dependencies (typical default)
      * 4-5: Extended search for distant relationships

    OUTPUT:
    You must return a MultiHopResult object containing:
    - found: Boolean indicating whether a path was found (true/false)
    - hops: Number of hops in the discovered path (0 if not found)
    - path: List of dictionaries representing the dependency path from start to target.
      Each dictionary contains:
      * "entity": Entity name
      * "type": Entity type (Function, Class, Method, Import, Module)
      * "file": File path where entity is defined
      * "line": Line number (use 0 if not available)
      Path should be ordered from start to target.
    - alternative_paths: List of alternative paths (each path is a list of entity dicts).
      Include multiple paths if they exist, ranked by relevance or length.
    - reasoning: Explanation of how the path was discovered and why this path is relevant
      (e.g., "Found via 3 hops: AuthService → UserManager → Database → Logger")

    TASK INSTRUCTIONS:
    - Search for entities matching the start_query and target_query using semantic search
    - Find the shortest dependency path between start and target entities
    - Limit path length to max_hops
    - Include alternative paths if multiple routes exist
    - Explain the reasoning behind the discovered path
    - If no path exists within max_hops, return found=false with explanatory reasoning
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
