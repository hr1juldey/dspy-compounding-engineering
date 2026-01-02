"""
Qdrant collection metadata management for dimension tracking.

Stores embedding dimension info in collection payload to detect
dimension changes and trigger reindexing when needed.
"""

from qdrant_client import QdrantClient

from utils.io.logger import logger


class CollectionMetadata:
    """
    Manages collection-level metadata in Qdrant.

    Stores dimension info in collection payload to enable:
    - Dimension change detection
    - Matryoshka dimension tracking
    - Auto-recreation on dimension mismatch
    """

    METADATA_KEY = "embedding_dimension"
    MODEL_KEY = "embedding_model"
    # Use fixed UUID for metadata point (deterministic)
    METADATA_ID = "00000000-0000-0000-0000-000000000000"

    def __init__(self, client: QdrantClient):
        """
        Initialize metadata manager.

        Args:
            client: Qdrant client instance
        """
        self.client = client

    def set_dimension(self, collection_name: str, dimension: int, model_name: str = None) -> None:
        """
        Store dimension metadata in collection.

        Uses collection payload to persist dimension info.

        Args:
            collection_name: Name of Qdrant collection
            dimension: Embedding dimension
            model_name: Optional embedding model name
        """
        try:
            # Qdrant doesn't support direct collection metadata
            # Store in a special metadata point instead
            metadata_payload = {
                self.METADATA_KEY: dimension,
                "_is_metadata": True,
            }

            if model_name:
                metadata_payload[self.MODEL_KEY] = model_name

            # Upsert metadata point with special UUID
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    {
                        "id": self.METADATA_ID,
                        "vector": [0.0] * dimension,
                        "payload": metadata_payload,
                    }
                ],
            )

            logger.debug(
                f"Stored dimension metadata for {collection_name}: "
                f"dim={dimension}, model={model_name}"
            )

        except Exception as e:
            logger.warning(f"Failed to store collection metadata: {e}")

    def get_dimension(self, collection_name: str) -> int | None:
        """
        Retrieve dimension metadata from collection.

        Args:
            collection_name: Name of Qdrant collection

        Returns:
            Stored dimension or None if not found
        """
        try:
            # Retrieve metadata point
            points = self.client.retrieve(collection_name=collection_name, ids=[self.METADATA_ID])

            if not points:
                logger.debug(f"No metadata found for {collection_name}")
                return None

            metadata = points[0].payload
            dimension = metadata.get(self.METADATA_KEY)

            if dimension:
                logger.debug(f"Retrieved dimension for {collection_name}: {dimension}")

            return dimension

        except Exception as e:
            logger.warning(f"Failed to retrieve collection metadata: {e}")
            return None

    def check_dimension_mismatch(self, collection_name: str, requested_dim: int) -> bool:
        """
        Check if requested dimension differs from stored dimension.

        Args:
            collection_name: Name of Qdrant collection
            requested_dim: Requested embedding dimension

        Returns:
            True if dimensions mismatch (requires reindexing)
        """
        stored_dim = self.get_dimension(collection_name)

        if stored_dim is None:
            logger.debug(f"No stored dimension for {collection_name} - assuming first indexing")
            return False

        mismatch = stored_dim != requested_dim

        if mismatch:
            logger.warning(
                f"Dimension mismatch for {collection_name}: "
                f"stored={stored_dim}, requested={requested_dim}"
            )

        return mismatch
