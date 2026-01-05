"""Knowledge Base - orchestrates learning storage and retrieval."""

import os
from typing import Any, Dict, List, Optional

from filelock import BaseFileLock, FileLock
from qdrant_client import QdrantClient

from utils.io.logger import console, logger
from utils.knowledge.embeddings.collection_initializer import CollectionInitializer
from utils.knowledge.embeddings.provider import (
    DSPyEmbeddingProvider as EmbeddingProvider,
)
from utils.knowledge.graphrag.graph_store import GraphStore
from utils.knowledge.graphrag.indexer import GraphRAGIndexer
from utils.knowledge.indexing.indexer import CodebaseIndexer
from utils.knowledge.learning.docs import KnowledgeDocumentation
from utils.knowledge.learning.learning_formatter import LearningFormatter
from utils.knowledge.learning.learning_indexer import LearningIndexer
from utils.knowledge.learning.learning_persistence import LearningPersistence
from utils.knowledge.learning.learning_retrieval import LearningRetrieval
from utils.knowledge.utils.helpers import CollectionManagerMixin
from utils.security.scrubber import scrubber


class KnowledgeBase(CollectionManagerMixin):
    """Manages learnings via service layer delegation."""

    client: Optional[QdrantClient]  # type: ignore[override]

    def __init__(
        self, knowledge_dir: Optional[str] = None, qdrant_client: Optional[QdrantClient] = None
    ):
        from server.config import get_project_hash, registry
        from utils.paths import get_paths

        knowledge_dir = knowledge_dir or str(get_paths().knowledge_dir)
        self.knowledge_dir = os.path.abspath(knowledge_dir)
        os.makedirs(self.knowledge_dir, exist_ok=True)
        os.makedirs(os.path.join(self.knowledge_dir, "backups"), exist_ok=True)
        self.lock_path = os.path.join(self.knowledge_dir, "kb.lock")

        project_hash = get_project_hash()
        self.collection_name = f"learnings_{project_hash}"

        # Dependencies
        self.docs_service = KnowledgeDocumentation(self.knowledge_dir)
        self.client = qdrant_client or registry.get_qdrant_client()
        self.vector_db_available = self.client is not None
        self.embedding_provider = EmbeddingProvider()

        # Service layer initialization
        self.persistence = LearningPersistence(self.knowledge_dir)
        self.indexer = LearningIndexer(self.client, self.collection_name, self.embedding_provider)
        self.retrieval = LearningRetrieval(
            self.client, self.collection_name, self.embedding_provider, self.knowledge_dir
        )
        self.formatter = LearningFormatter()

        # Codebase indexing
        codebase_collection = f"codebase_{project_hash}"
        self.codebase_indexer = CodebaseIndexer(
            self.client, self.embedding_provider, collection_name=codebase_collection
        )

        # GraphRAG (lazy-loaded)
        self._graphrag_indexer = None
        self._entities_collection_name = f"entities_{project_hash}"

        # Ensure collections exist
        initializer = CollectionInitializer(
            self.client, self.embedding_provider, self._safe_ensure_collection
        )
        initializer.ensure_all_collections(project_hash, self.collection_name)

        # Sync if needed
        try:
            if (
                self.vector_db_available
                and self.client is not None
                and self.client.count(self.collection_name).count == 0
            ):
                console.print("[yellow]Syncing from disk...[/yellow]")
                self.indexer.sync_to_qdrant(self.knowledge_dir)
        except Exception as e:
            logger.debug(f"Collection check failed: {e}")

        logger.info("KnowledgeBase ready", to_cli=True)

    def save_learning(self, learning: Dict[str, Any], silent: bool = False) -> str:
        """Save learning: persist → index → update docs."""
        filepath = self.persistence.save_to_disk(learning)

        # Index in Qdrant
        self.indexer.index_learning(learning)

        if not silent:
            logger.success(f"Learning saved: {filepath}")

        # Update docs
        self.docs_service.update_ai_md(self.get_all_learnings(), silent=silent)
        self.docs_service.review_and_compress(silent=silent)

        return filepath

    def retrieve_relevant(
        self, query: str = "", tags: List[str] | None = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Delegate to retrieval service."""
        return self.retrieval.retrieve_relevant(query, tags, limit)

    def get_all_learnings(self) -> List[Dict[str, Any]]:
        """Get all learnings via retrieval service."""
        return self.retrieval._legacy_search(limit=1000)

    def get_context_string(self, query: str = "", tags: List[str] | None = None) -> str:
        """Format learnings for context injection."""
        learnings = self.retrieve_relevant(query, tags)
        return self.formatter.format_context_string(learnings)

    def get_compounding_ai_prompt(self, limit: int = 20) -> str:
        """Format learnings as system prompt."""
        learnings = self.get_all_learnings()
        return self.formatter.format_compounding_prompt(learnings, limit)

    def get_codify_lock_path(self) -> str:
        """Returns codify lock file path."""
        return os.path.join(self.knowledge_dir, "codify.lock")

    def get_lock(self, lock_type: str = "kb") -> BaseFileLock:
        """Get lock instance."""
        path = self.get_codify_lock_path() if lock_type == "codify" else self.lock_path
        return FileLock(path)

    def _ensure_knowledge_dir(self):
        """Ensure knowledge directory exists."""
        os.makedirs(self.knowledge_dir, exist_ok=True)

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text for embedding."""
        if not text:
            return ""
        text = scrubber.scrub(text)
        text = "".join(ch for ch in text if ch in "\n\r\t" or ch >= " ")
        return text[:30000]

    def index_codebase(
        self, root_dir: str, force_recreate: bool = False, with_graphrag: bool = False
    ):
        """Index codebase for semantic search."""
        stats = self.codebase_indexer.index_codebase(root_dir, force_recreate=force_recreate)
        if with_graphrag:
            self.graphrag_indexer.index_codebase(root_dir, force_recreate=force_recreate)
        return stats

    def search_codebase(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Search codebase using semantic/vector search.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of search results with path, content, score, etc.
        """
        return self.codebase_indexer.search_codebase(query, limit)

    def compress_ai_md(self, ratio: float = 0.3, dry_run: bool = False):
        """Compress AI knowledge base markdown."""
        return self.docs_service.compress_ai_md(ratio=ratio, dry_run=dry_run)

    @property
    def graphrag_indexer(self):
        """Lazy-load GraphRAG indexer."""
        if self._graphrag_indexer is None:
            graph_store = GraphStore(
                self.client, self.embedding_provider, self._entities_collection_name
            )
            self._graphrag_indexer = GraphRAGIndexer(graph_store)
        return self._graphrag_indexer
