"""
Batch Embedder for efficient parallel embedding generation.

Wraps the DSPy embedding provider to provide batch processing with indexed results.
"""

from typing import List, Tuple

from utils.knowledge.embeddings.provider import DSPyEmbeddingProvider


class BatchEmbedder:
    """
    Efficient batch embedding generator.

    Wraps DSPyEmbeddingProvider to provide indexed batch results
    for tracking which chunks correspond to which embeddings.
    """

    def __init__(self, embedding_provider: DSPyEmbeddingProvider):
        """
        Initialize batch embedder.

        Args:
            embedding_provider: The DSPy embedding provider instance
        """
        self.provider = embedding_provider

    def embed_texts_batch(self, texts: List[str]) -> List[Tuple[int, List[float]]]:
        """
        Generate embeddings for a batch of texts with index tracking.

        Args:
            texts: List of text strings to embed

        Returns:
            List of (index, vector) tuples where index corresponds to the
            position in the input texts list
        """
        if not texts:
            return []

        # Get batch embeddings from provider
        vectors = self.provider.get_embeddings_batch(texts)

        # Return as (index, vector) tuples
        return [(i, vector) for i, vector in enumerate(vectors)]
