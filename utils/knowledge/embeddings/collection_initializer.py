"""
Collection initialization for KnowledgeBase.

Single Responsibility: Proactively create all required Qdrant collections
to prevent 400 errors and wasteful LLM calls.
"""

from typing import Optional

from qdrant_client import QdrantClient

from utils.io.logger import logger


class CollectionInitializer:
    """
    Manages proactive creation of all KnowledgeBase collections.

    Prevents wasteful LLM calls by ensuring infrastructure exists BEFORE
    any indexing/search operations.
    """

    def __init__(self, client: Optional[QdrantClient], embedding_provider, ensure_method):
        """
        Initialize collection manager.

        Args:
            client: Qdrant client instance
            embedding_provider: Embedding provider for vector dimensions
            ensure_method: Method to ensure single collection exists
        """
        self.client = client
        self.embedding_provider = embedding_provider
        self._safe_ensure_collection = ensure_method

    def ensure_all_collections(self, project_hash: str, collection_name: str):
        """
        Proactively create ALL collections for this codebase.

        Prevents 400 errors and wasteful LLM calls by ensuring
        infrastructure is ready BEFORE any operations.

        Collections created:
        - learnings_{hash}: Knowledge base learnings
        - codebase_{hash}: Semantic code search
        - entities_{hash}: GraphRAG entity graph

        Args:
            project_hash: Stable hash identifying this codebase
            collection_name: Main learnings collection name
        """
        if self.client is None:
            logger.warning("Qdrant not available - collections will not be created")
            return

        logger.debug(f"Ensuring all collections for project {project_hash}")

        # 1. Learnings collection (with sparse vectors)
        self._ensure_learnings_collection(collection_name)

        # 2. Codebase collection (semantic code search)
        self._ensure_codebase_collection(project_hash)

        # 3. Entities collection (GraphRAG)
        self._ensure_entities_collection(project_hash)

        logger.debug("All collections ensured successfully")

    def _ensure_learnings_collection(self, collection_name: str):
        """Ensure learnings collection exists."""
        self._safe_ensure_collection(
            collection_name=collection_name,
            vector_size=self.embedding_provider.vector_size,
            force_recreate=False,
            enable_sparse=True,
            registry_flag="learnings_ensured",
        )

    def _ensure_codebase_collection(self, project_hash: str):
        """Ensure codebase collection exists."""
        codebase_collection = f"codebase_{project_hash}"
        self._safe_ensure_collection(
            collection_name=codebase_collection,
            vector_size=self.embedding_provider.vector_size,
            force_recreate=False,
            enable_sparse=True,
            registry_flag="codebase_ensured",
        )

    def _ensure_entities_collection(self, project_hash: str):
        """Ensure entities collection exists (for GraphRAG)."""
        if not self.client:
            logger.debug("Qdrant client unavailable, skipping entities collection")
            return

        entities_collection = f"entities_{project_hash}"
        try:
            if not self.client.collection_exists(entities_collection):
                logger.debug(f"Creating empty entities collection: {entities_collection}")
                self._safe_ensure_collection(
                    collection_name=entities_collection,
                    vector_size=self.embedding_provider.vector_size,
                    force_recreate=False,
                    enable_sparse=False,
                    registry_flag="entities_ensured",
                )
        except Exception as e:
            logger.warning(f"Failed to create entities collection: {e}")
