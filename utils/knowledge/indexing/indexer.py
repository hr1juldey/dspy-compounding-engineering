"""Codebase Indexer - orchestrates file indexing via service layer."""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from rich.console import Console

from utils.io.logger import logger
from utils.knowledge.chunking.semantic_chunker import SemanticChunker
from utils.knowledge.embeddings.batch_embedder import BatchEmbedder
from utils.knowledge.embeddings.provider import (
    DSPyEmbeddingProvider as EmbeddingProvider,
)
from utils.knowledge.indexing.codebase_search import CodebaseSearch
from utils.knowledge.indexing.file_indexer import FileIndexer
from utils.knowledge.indexing.indexer_metadata import IndexerMetadata
from utils.knowledge.utils.helpers import CollectionManagerMixin

console = Console()


class CodebaseIndexer(CollectionManagerMixin):
    """Orchestrates codebase indexing via service layer."""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_provider: EmbeddingProvider,
        collection_name: str,
    ):
        if not any(c in collection_name for c in "_-"):
            raise ValueError(f"Collection '{collection_name}' needs hash suffix")

        self.client = qdrant_client
        self.embedding_provider = embedding_provider
        self.collection_name = collection_name
        self.vector_db_available = self.client is not None

        # Service layer initialization
        self.batch_embedder = BatchEmbedder(embedding_provider)
        self.metadata = IndexerMetadata(qdrant_client, collection_name)
        # Always use AST chunking (fast, deterministic)
        # LLM validation is controlled separately via USE_LLM_CHUNKING_VALIDATION
        semantic_chunker = SemanticChunker()
        self.file_indexer = FileIndexer(
            qdrant_client, collection_name, self.batch_embedder, semantic_chunker
        )
        self.search = CodebaseSearch(qdrant_client, collection_name, embedding_provider)

        if self.vector_db_available:
            self._ensure_collection()

    def _ensure_collection(self, force_recreate: bool = False):
        """Ensure the Qdrant collection exists."""
        self.vector_db_available = self._safe_ensure_collection(
            collection_name=self.collection_name,
            vector_size=self.embedding_provider.vector_size,
            force_recreate=force_recreate,
            enable_sparse=False,
            registry_flag="codebase_ensured",
        )

    def index_codebase(
        self,
        root_dir: str,
        force_recreate: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> dict:
        """Index codebase - delegates to async or sequential mode."""
        import time

        start_time = time.time()
        root_path = Path(root_dir)
        all_files = list(root_path.rglob("*.py"))

        if not all_files:
            logger.warning(f"No Python files in {root_dir}")
            return {"files": 0, "entities": 0, "time_sec": 0.0}

        if force_recreate:
            logger.info("Force recreating collection")
            self._ensure_collection(force_recreate=True)

        # Filter files using .gitignore patterns
        from utils.knowledge.utils.gitignore_parser import GitignoreParser

        gitignore = GitignoreParser(root_dir)
        python_files = gitignore.filter_files(all_files)

        # Get indexed files metadata
        indexed_files = self.metadata.get_indexed_files_metadata()

        # Prepare file paths for processing (filepath, full_path tuples)
        files_to_process = [(str(f.relative_to(root_path)), str(f)) for f in python_files]

        logger.info(f"Indexing {len(files_to_process)} files")

        # Process files (async or sequential)
        use_async = os.getenv("USE_ASYNC_INDEXING", "true").lower() == "true"

        if use_async:
            from utils.knowledge.indexing.async_indexer import AsyncFileIndexer

            async_indexer = AsyncFileIndexer(self, max_concurrency=20)
            stats = asyncio.run(
                async_indexer.index_files_parallel(
                    files_to_process, indexed_files, progress_callback
                )
            )
        else:
            updated = skipped = 0
            for filepath, full_path in files_to_process:
                try:
                    if self.file_indexer.index_file(filepath, full_path, indexed_files):
                        updated += 1
                    else:
                        skipped += 1
                    if progress_callback:
                        progress_callback(filepath, updated + skipped, len(files_to_process))
                except Exception as e:
                    logger.error(f"Failed to index {filepath}: {e}")

            stats = {"updated": updated, "skipped": skipped}

        elapsed_time = time.time() - start_time
        stats["time_sec"] = elapsed_time

        logger.success(
            f"Indexing complete: {stats['updated']} updated, "
            f"{stats['skipped']} skipped in {elapsed_time:.1f}s"
        )
        return stats

    def search_codebase(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search codebase via CodebaseSearch service."""
        return self.search.search(query, limit)
