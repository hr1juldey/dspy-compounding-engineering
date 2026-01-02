"""
NetworkX-based Graph RAG (mimicking fast-graphrag).

Uses PageRank + vector similarity for intelligent code navigation.
First line of defense: HNSW vector search
Second line: Graph traversal with PageRank
"""

import networkx as nx

from utils.io.logger import logger
from utils.knowledge.graph.graph_builder import GraphBuilder
from utils.knowledge.graph_store import GraphStore


class CodeGraphRAG:
    """
    Graph RAG for code using NetworkX + Qdrant.

    Architecture (mimicking fast-graphrag):
    1. HNSW vector search finds initial candidates (fast)
    2. Build local NetworkX graph from candidates + neighbors
    3. Run PageRank to rank by importance
    4. Return top-ranked entities with references
    """

    def __init__(self, graph_store: GraphStore):
        """
        Initialize CodeGraphRAG.

        Args:
            graph_store: GraphStore instance for entity storage/retrieval
        """
        self.graph_store = graph_store
        self.graph_builder = GraphBuilder(graph_store)

    @property
    def graph(self) -> nx.DiGraph:
        """Access underlying graph."""
        return self.graph_builder.graph

    def build_full_graph(self, entity_type: str | None = None) -> int:
        """Delegate to GraphBuilder."""
        return self.graph_builder.build_full_graph(entity_type)

    def query_with_pagerank(
        self,
        query: str,
        top_k: int = 10,
        vector_candidates: int = 50,
        include_neighbors: bool = True,
    ) -> list[dict]:
        """
        Query using HNSW + PageRank (fast-graphrag approach).

        Strategy:
        1. HNSW finds initial vector-similar entities (fast)
        2. Build local subgraph (candidates + neighbors)
        3. Run personalized PageRank
        4. Return top-k ranked by PageRank * vector_score

        Args:
            query: Search query text
            top_k: Number of results to return
            vector_candidates: Initial HNSW candidates
            include_neighbors: Include neighbor entities in subgraph

        Returns:
            List of dicts with entity info + scores
        """
        # Step 1: HNSW vector search (first line of defense)
        logger.debug(f"HNSW search for '{query}' (k={vector_candidates})")
        candidates = self.graph_store.query_entities(query, limit=vector_candidates)

        if not candidates:
            logger.warning(f"No candidates found for query: {query}")
            return []

        # Step 2: Build local subgraph
        subgraph_nodes = {e.id for e in candidates}

        if include_neighbors:
            # Add neighbors to subgraph for better PageRank context
            for entity in candidates:
                neighbors = self.graph_store.query_neighbors(entity.id, limit=20)
                subgraph_nodes.update(n.id for n in neighbors)

        # Extract subgraph from full graph
        if not self.graph.nodes():
            # Graph not built yet, build it now
            self.build_full_graph()

        subgraph = self.graph.subgraph(subgraph_nodes)

        if not subgraph.nodes():
            # Fallback: just use vector scores
            logger.warning("Empty subgraph, using vector scores only")
            return [
                {
                    "entity_id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "file_path": e.file_path,
                    "line_start": e.line_start,
                    "score": 1.0 / (i + 1),  # Simple rank score
                    "pagerank": 0.0,
                }
                for i, e in enumerate(candidates[:top_k])
            ]

        # Step 3: Personalized PageRank (second line of defense)
        # Personalize towards initial candidates (query-relevant entities)
        personalization = {
            node: 1.0 for node in subgraph.nodes() if node in [c.id for c in candidates]
        }

        try:
            pagerank_scores = nx.pagerank(
                subgraph, personalization=personalization, alpha=0.85, max_iter=100
            )
        except Exception as e:
            logger.error(f"PageRank failed: {e}")
            pagerank_scores = dict.fromkeys(subgraph.nodes(), 1.0)

        # Step 4: Combine PageRank + vector similarity
        results = []
        candidate_map = {c.id: c for c in candidates}

        for entity_id, pagerank in pagerank_scores.items():
            if entity_id in candidate_map:
                entity = candidate_map[entity_id]
                # Combine scores (you can tune weights)
                combined_score = pagerank * 100  # Scale PageRank

                results.append(
                    {
                        "entity_id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                        "file_path": entity.file_path,
                        "line_start": entity.line_start,
                        "score": combined_score,
                        "pagerank": pagerank,
                    }
                )

        # Sort by combined score
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k]

    def find_shortest_path(self, source_entity_id: str, target_entity_id: str) -> list[dict] | None:
        """
        Find shortest path between two entities.

        Args:
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID

        Returns:
            List of entities along path, or None if no path
        """
        if not self.graph.nodes():
            self.build_full_graph()

        try:
            path = nx.shortest_path(self.graph, source_entity_id, target_entity_id)

            # Get entity details for each node in path
            result = []
            for entity_id in path:
                entity = self.graph_store.get_entity(entity_id)
                if entity:
                    result.append(
                        {
                            "entity_id": entity.id,
                            "name": entity.name,
                            "type": entity.type,
                            "file_path": entity.file_path,
                        }
                    )

            return result

        except nx.NetworkXNoPath:
            logger.warning(f"No path found between {source_entity_id} and {target_entity_id}")
            return None
