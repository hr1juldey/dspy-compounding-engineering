"""
Graph store for code knowledge graph using Qdrant.

Stores entities as Qdrant points with:
- Dense vector embeddings (semantic search via HNSW)
- Relations embedded in payload (no separate collection)
- Graph clustering for scalability
"""

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    HnswConfigDiff,
    MatchValue,
    PointStruct,
    VectorParams,
)

from utils.io.logger import logger
from utils.knowledge.embeddings_dspy import DSPyEmbeddingProvider as EmbeddingProvider
from utils.knowledge.entities import Entity
from utils.knowledge.utils import CollectionManagerMixin


class GraphStore(CollectionManagerMixin):
    """
    Stores code entities as graph nodes in Qdrant.

    Architecture:
    - Entities stored as Qdrant points
    - Relations embedded in entity payload (not separate collection)
    - HNSW index for fast vector similarity
    - Graph clustering for scalability (future: NetworkX integration)
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_provider: EmbeddingProvider,
        collection_name: str,
    ):
        """
        Initialize graph store.

        Args:
            qdrant_client: Qdrant client instance
            embedding_provider: Provider for generating embeddings
            collection_name: Name of collection (must include hash suffix)
        """
        # Validate collection name has hash suffix
        if not any(c in collection_name for c in "_-"):
            raise ValueError(
                f"Collection name '{collection_name}' must include hash suffix "
                "(e.g., 'entities_abc123')"
            )

        self.client = qdrant_client
        self.embedding_provider = embedding_provider
        self.collection_name = collection_name
        self.vector_db_available = self.client is not None

        if self.vector_db_available:
            self._ensure_collection()

    def _ensure_collection(self, force_recreate: bool = False):
        """
        Ensure the Qdrant collection exists with optimized HNSW indexing.

        HNSW Configuration (first line of defense against bugs):
        - Distance: Cosine (best for embeddings)
        - m: 16 (connections per node, balance speed/accuracy)
        - ef_construct: 100 (build quality, higher = better but slower)
        - full_scan_threshold: 10000 (use HNSW for >10k points)
        """
        if not self.client:
            self.vector_db_available = False
            return

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if force_recreate and exists:
                logger.info(f"Deleting existing collection {self.collection_name}")
                self.client.delete_collection(self.collection_name)
                exists = False

            if not exists:
                logger.info(f"Creating collection {self.collection_name} with HNSW")

                # Create collection with optimized HNSW config
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_provider.vector_size,
                        distance=Distance.COSINE,  # Best for semantic embeddings
                        hnsw_config=HnswConfigDiff(
                            m=16,  # Connections per node (default: 16, range: 4-64)
                            ef_construct=100,  # Build quality (default: 100, range: 4-512)
                            full_scan_threshold=10000,  # Use HNSW when >10k points
                        ),
                    ),
                )

                logger.success(
                    f"Collection {self.collection_name} created with HNSW "
                    f"(m=16, ef_construct=100, distance=COSINE)"
                )

            self.vector_db_available = True

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            self.vector_db_available = False

    def store_entities(self, entities: list[Entity]) -> int:
        """
        Store entities in Qdrant with embeddings.

        Args:
            entities: List of Entity objects

        Returns:
            Number of entities stored
        """
        if not self.vector_db_available:
            logger.warning("Vector DB not available, cannot store entities")
            return 0

        if not entities:
            return 0

        # Generate embeddings for entities
        texts_to_embed = []
        for entity in entities:
            # Create text representation for embedding
            text = self._entity_to_text(entity)
            texts_to_embed.append(text)

        # Batch embed all entities
        from utils.knowledge.batch_embedder import BatchEmbedder

        batch_embedder = BatchEmbedder(self.embedding_provider)
        embedding_results = batch_embedder.embed_texts_batch(texts_to_embed)

        # Build Qdrant points
        points = []
        for idx, vector in embedding_results:
            entity = entities[idx]

            # Use entity ID directly (already deterministic hash)
            point_id = entity.id

            # Payload includes all entity data + relations
            payload = {
                "type": entity.type,
                "name": entity.name,
                "file_path": entity.file_path,
                "line_start": entity.line_start,
                "line_end": entity.line_end,
                "properties": entity.properties,
                "relations": entity.relations,  # Embedded relations (not separate collection)
            }

            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

        # Upsert entities
        self.client.upsert(collection_name=self.collection_name, points=points)

        logger.info(f"Stored {len(points)} entities in {self.collection_name}")
        return len(points)

    def get_entity(self, entity_id: str) -> Entity | None:
        """
        Retrieve entity by ID.

        Args:
            entity_id: Entity ID (hash)

        Returns:
            Entity object or None if not found
        """
        if not self.vector_db_available:
            return None

        try:
            result = self.client.retrieve(
                collection_name=self.collection_name, ids=[entity_id], with_vectors=False
            )

            if not result:
                return None

            point = result[0]
            return self._point_to_entity(point)

        except Exception as e:
            logger.error(f"Failed to retrieve entity {entity_id}: {e}")
            return None

    def query_entities(
        self, query: str, limit: int = 10, entity_type: str | None = None
    ) -> list[Entity]:
        """
        Search for entities by semantic similarity.

        Args:
            query: Search query text
            limit: Max results
            entity_type: Filter by entity type (Function, Class, etc.)

        Returns:
            List of Entity objects
        """
        if not self.vector_db_available:
            return []

        try:
            # Generate query embedding
            query_vector = self.embedding_provider.get_embedding(query)

            # Build filter
            search_filter = None
            if entity_type:
                search_filter = Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value=entity_type))]
                )

            # Search
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                query_filter=search_filter,
            ).points

            # Convert to entities
            entities = [self._point_to_entity(point) for point in results]
            return entities

        except Exception as e:
            logger.error(f"Entity query failed: {e}")
            return []

    def query_neighbors(
        self, entity_id: str, relation_type: str | None = None, limit: int = 50
    ) -> list[Entity]:
        """
        Find entities connected to this entity via relations.

        Args:
            entity_id: Source entity ID
            relation_type: Filter by relation type (calls, imports, inherits, etc.)
            limit: Max results

        Returns:
            List of connected Entity objects
        """
        # Get source entity
        source = self.get_entity(entity_id)
        if not source:
            return []

        # Extract related entity IDs from embedded relations
        related_ids = []

        if relation_type:
            # Filter by specific relation type
            if relation_type in source.relations:
                related_ids = source.relations[relation_type]
        else:
            # All relations
            for rel_ids in source.relations.values():
                related_ids.extend(rel_ids)

        # Limit results
        related_ids = related_ids[:limit]

        # Retrieve related entities
        if not related_ids:
            return []

        try:
            results = self.client.retrieve(
                collection_name=self.collection_name, ids=related_ids, with_vectors=False
            )

            return [self._point_to_entity(point) for point in results]

        except Exception as e:
            logger.error(f"Failed to retrieve neighbors: {e}")
            return []

    def get_all_entities(self, entity_type: str | None = None, limit: int = 10000) -> list[Entity]:
        """
        Get all entities from the collection.

        Args:
            entity_type: Optional filter by entity type
            limit: Max entities to retrieve

        Returns:
            List of Entity objects
        """
        if not self.vector_db_available:
            return []

        try:
            # Build filter
            scroll_filter = None
            if entity_type:
                scroll_filter = Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value=entity_type))]
                )

            # Scroll through all entities
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=limit,
                with_vectors=False,
            )[0]

            entities = [self._point_to_entity(point) for point in results]
            logger.debug(f"Retrieved {len(entities)} entities from {self.collection_name}")
            return entities

        except Exception as e:
            logger.error(f"Failed to get all entities: {e}")
            return []

    def query_entities_by_file(self, file_path: str) -> list[Entity]:
        """
        Get all entities from a specific file.

        Args:
            file_path: File path

        Returns:
            List of Entity objects
        """
        if not self.vector_db_available:
            return []

        try:
            # Scroll through entities for this file
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="file_path", match=MatchValue(value=file_path))]
                ),
                limit=1000,
                with_vectors=False,
            )[0]

            return [self._point_to_entity(point) for point in results]

        except Exception as e:
            logger.error(f"Failed to query entities by file: {e}")
            return []

    def delete_entities_by_file(self, file_path: str) -> int:
        """
        Delete all entities from a specific file.

        Args:
            file_path: File path

        Returns:
            Number of entities deleted
        """
        if not self.vector_db_available:
            return 0

        try:
            # Get current entities
            existing = self.query_entities_by_file(file_path)

            if not existing:
                return 0

            # Delete by IDs
            entity_ids = [e.id for e in existing]
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=entity_ids,
            )

            logger.info(f"Deleted {len(entity_ids)} entities from {file_path}")
            return len(entity_ids)

        except Exception as e:
            logger.error(f"Failed to delete entities: {e}")
            return 0

    def _entity_to_text(self, entity: Entity) -> str:
        """
        Convert entity to text for embedding.

        Strategy: Combine name, docstring, and source code for semantic richness.
        """
        parts = [f"{entity.type}: {entity.name}"]

        # Add docstring if available
        if "docstring" in entity.properties and entity.properties["docstring"]:
            parts.append(entity.properties["docstring"])

        # Add source code snippet (truncated for efficiency)
        if "source_code" in entity.properties and entity.properties["source_code"]:
            source = entity.properties["source_code"]
            # Truncate long source
            if len(source) > 2000:
                source = source[:2000] + "..."
            parts.append(source)

        return "\n".join(parts)

    def _point_to_entity(self, point: Any) -> Entity:
        """Convert Qdrant point to Entity object."""
        payload = point.payload

        return Entity(
            id=point.id,
            type=payload["type"],
            name=payload["name"],
            file_path=payload["file_path"],
            line_start=payload["line_start"],
            line_end=payload["line_end"],
            properties=payload.get("properties", {}),
            relations=payload.get("relations", {}),
            embedding=[],  # Don't load vectors unless needed
        )
