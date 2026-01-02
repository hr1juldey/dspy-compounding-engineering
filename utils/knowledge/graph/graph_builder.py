"""NetworkX graph construction from code entities."""

import networkx as nx

from utils.io.logger import logger
from utils.knowledge.entities import Entity
from utils.knowledge.graph_store import GraphStore


class GraphBuilder:
    """Builds NetworkX graph from Qdrant entities."""

    def __init__(self, graph_store: GraphStore):
        """
        Initialize graph builder.

        Args:
            graph_store: GraphStore instance for entity storage/retrieval
        """
        self.graph_store = graph_store
        self.graph = nx.DiGraph()  # Directed graph for code relationships

    def build_full_graph(self, entity_type: str | None = None) -> int:
        """
        Build complete NetworkX graph from all entities in Qdrant.

        Args:
            entity_type: Optional filter by entity type

        Returns:
            Number of nodes in graph
        """
        logger.info("Building NetworkX graph from entities...")

        # Clear existing graph
        self.graph.clear()

        # Get all entities with pagination for large repos (1000-entity batches)
        entities = self._get_all_entities(entity_type)

        # Add nodes
        for entity in entities:
            self.graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.type,
                file_path=entity.file_path,
                line_start=entity.line_start,
            )

        # Add edges from relations
        for entity in entities:
            for relation_type, target_ids in entity.relations.items():
                for target_id in target_ids:
                    # Add directed edge with relation type as attribute
                    self.graph.add_edge(entity.id, target_id, relation_type=relation_type)

        logger.success(
            f"Graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )
        return self.graph.number_of_nodes()

    def _get_all_entities(self, entity_type: str | None = None) -> list[Entity]:
        """
        Get all entities from graph store with pagination.

        Uses Qdrant scroll API with batching for large codebases.
        Handles repos with >10k entities efficiently.

        Args:
            entity_type: Optional filter by entity type

        Returns:
            List of all entities
        """
        entities = []
        batch_size = 1000
        offset = 0

        while True:
            batch = self.graph_store.get_all_entities(entity_type=entity_type, limit=batch_size)

            if not batch:
                break

            entities.extend(batch)
            offset += len(batch)

            # Progress logging for large repos
            if offset % 5000 == 0:
                logger.info(f"Loaded {offset} entities so far...")

            # If batch is smaller than batch_size, we've reached the end
            if len(batch) < batch_size:
                break

        logger.info(f"Loaded {len(entities)} total entities")
        return entities
