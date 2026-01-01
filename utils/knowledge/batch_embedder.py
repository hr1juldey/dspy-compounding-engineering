"""
Batch embedding pipeline that saturates Ollama/embedding providers.

Provides 4-10x speedup by processing multiple chunks in parallel batches.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from utils.io.logger import logger


class BatchEmbedder:
    """
    Batch embedding pipeline that keeps embedding providers saturated.

    Strategy:
    1. Group texts into batches (size determined by machine benchmarks)
    2. Process multiple batches in parallel using ThreadPoolExecutor
    3. Each batch sends all texts to provider in ONE request
    4. Returns vectors maintaining input order
    """

    def __init__(
        self, embedding_provider: Any, batch_size: int | None = None, parallel_batches: int = 3
    ):
        """
        Initialize batch embedder.

        Args:
            embedding_provider: EmbeddingProvider instance
            batch_size: Chunks per batch (auto-detected if None)
            parallel_batches: Number of batches to process in parallel
        """
        self.embedding_provider = embedding_provider
        self.batch_size = batch_size or self._get_optimal_batch_size()
        self.parallel_batches = parallel_batches

    def _get_optimal_batch_size(self) -> int:
        """
        Get optimal batch size from environment or use defaults.

        Batch size is set by tests/test_batch_benchmark.py based on machine power.
        """
        # Check if benchmark has set optimal size
        env_batch_size = os.getenv("OPTIMAL_BATCH_SIZE")
        if env_batch_size:
            try:
                return int(env_batch_size)
            except ValueError:
                pass

        # Default fallback based on provider
        if self.embedding_provider.embedding_provider == "fastembed":
            return 100  # Local embedding is fast
        elif self.embedding_provider.embedding_provider == "ollama":
            return 50  # Balance between throughput and memory
        else:
            return 30  # OpenAI/OpenRouter rate limits

    def embed_texts_batch(self, texts: list[str]) -> list[tuple[int, list[float]]]:
        """
        Embed multiple texts using parallel batch processing.

        Args:
            texts: List of texts to embed

        Returns:
            List of (index, vector) tuples maintaining input order
        """
        if not texts:
            return []

        # Single text - no batching needed
        if len(texts) == 1:
            vector = self.embedding_provider.get_embedding(texts[0])
            return [(0, vector)]

        # Group into batches
        batches = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i : i + self.batch_size]
            batch_indices = list(range(i, i + len(batch_texts)))
            batches.append((batch_indices, batch_texts))

        logger.info(
            f"Embedding {len(texts)} texts in {len(batches)} batches "
            f"(size={self.batch_size}, parallel={self.parallel_batches})",
            to_cli=True,
        )

        # Process batches in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.parallel_batches) as executor:
            # Submit all batch jobs
            future_to_indices = {}
            for batch_indices, batch_texts in batches:
                future = executor.submit(self._embed_single_batch, batch_texts)
                future_to_indices[future] = batch_indices

            # Collect results as they complete
            for future in as_completed(future_to_indices):
                batch_indices = future_to_indices[future]
                try:
                    batch_vectors = future.result()
                    # Pair each vector with its original index
                    for idx, vector in zip(batch_indices, batch_vectors, strict=True):
                        results.append((idx, vector))
                except Exception as e:
                    logger.error(
                        f"Batch embedding failed for indices {batch_indices}", detail=str(e)
                    )
                    # Re-raise to fail fast
                    raise

        # Sort by original index to maintain order
        results.sort(key=lambda x: x[0])
        return results

    def _embed_single_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a single batch of texts.

        Args:
            texts: Batch of texts to embed

        Returns:
            List of embedding vectors
        """
        # Use batch API if available
        if hasattr(self.embedding_provider, "get_embeddings_batch"):
            return self.embedding_provider.get_embeddings_batch(texts)
        else:
            # Fallback: serial embedding (slower, but works)
            logger.warning("Batch API not available, falling back to serial embedding")
            return [self.embedding_provider.get_embedding(text) for text in texts]
