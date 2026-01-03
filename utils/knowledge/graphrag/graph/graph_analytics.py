"""Graph analytics using NetworkX (PageRank, clustering)."""

import networkx as nx

from utils.io.logger import logger
from utils.knowledge.graphrag.graph_store import GraphStore


class GraphAnalytics:
    """Provides graph analytics on code entity graph."""

    def __init__(self, graph: nx.DiGraph, graph_store: GraphStore):
        """
        Initialize graph analytics.

        Args:
            graph: NetworkX directed graph
            graph_store: GraphStore for entity retrieval
        """
        self.graph = graph
        self.graph_store = graph_store

    def get_top_entities_by_pagerank(self, top_k: int = 20) -> list[dict]:
        """
        Get most important entities by global PageRank.

        Useful for finding "hub" functions/classes in the codebase.

        Args:
            top_k: Number of top entities

        Returns:
            List of top entities with PageRank scores
        """
        if not self.graph.nodes():
            return []

        # Global PageRank
        try:
            pagerank_scores = nx.pagerank(self.graph, alpha=0.85, max_iter=100)
        except Exception as e:
            logger.error(f"PageRank failed: {e}")
            return []

        # Sort by PageRank
        sorted_entities = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)

        # Get entity details
        results = []
        for entity_id, pagerank in sorted_entities[:top_k]:
            entity = self.graph_store.get_entity(entity_id)
            if entity:
                results.append(
                    {
                        "entity_id": entity.id,
                        "name": entity.name,
                        "type": entity.type,
                        "file_path": entity.file_path,
                        "pagerank": pagerank,
                    }
                )

        return results

    def get_graph_clusters(self, num_clusters: int = 10) -> dict[int, list[str]]:  # noqa: ARG002
        """
        Detect graph clusters using community detection.

        Useful for identifying module boundaries and code groups.

        Args:
            num_clusters: Target number of clusters (not used, greedy algorithm determines count)

        Returns:
            Dict mapping cluster_id to list of entity_ids
        """
        if not self.graph.nodes():
            return {}

        # Use Louvain community detection (fast, good quality)
        try:
            import networkx.algorithms.community as nx_comm

            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()

            # Greedy modularity communities
            communities = nx_comm.greedy_modularity_communities(undirected, weight=None)

            # Convert to dict
            clusters = {}
            for idx, community in enumerate(communities):
                clusters[idx] = list(community)

            logger.info(
                f"Detected {len(clusters)} clusters (avg size: "
                f"{sum(len(c) for c in clusters.values()) / len(clusters):.1f})"
            )

            return clusters

        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return {}
