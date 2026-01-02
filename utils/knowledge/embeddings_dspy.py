"""
DSPy-based embedding provider (replaces custom EmbeddingProvider).

Uses dspy.Embedder for unified embedding across all providers.
"""

import os

import dspy
import numpy as np

from utils.io.logger import logger


def resolve_dspy_embedder_config() -> str:
    """
    Resolve embedding configuration to dspy.Embedder model name.

    Requires .env variables:
    - EMBEDDING_PROVIDER: openai, ollama, anthropic, fastembed
    - EMBEDDING_MODEL: model name (provider-specific)

    Returns:
        Model name in dspy.Embedder format (e.g., "openai/text-embedding-3-small")
    """
    provider = os.getenv("EMBEDDING_PROVIDER") or os.getenv("DSPY_LM_PROVIDER")
    model = os.getenv("EMBEDDING_MODEL")

    if not provider:
        raise ValueError("EMBEDDING_PROVIDER or DSPY_LM_PROVIDER must be set in .env")
    if not model:
        raise ValueError("EMBEDDING_MODEL must be set in .env")

    # Map to dspy.Embedder format
    if provider == "openai":
        return f"openai/{model}"
    elif provider == "ollama":
        return f"ollama/{model}"
    elif provider == "anthropic":
        return f"anthropic/{model}"
    elif provider == "fastembed":
        return "fastembed"
    else:
        raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider}")


def create_fastembed_embedder():
    """Create custom FastEmbed callable for dspy.Embedder."""
    from fastembed import TextEmbedding

    model_name = os.getenv("EMBEDDING_MODEL")
    if not model_name:
        raise ValueError("EMBEDDING_MODEL must be set in .env for fastembed")

    model = TextEmbedding(model_name=model_name)

    def fastembed_callable(texts: list[str]) -> np.ndarray:
        """Custom callable for dspy.Embedder."""
        results = list(model.embed(texts))
        return np.array(results)

    return fastembed_callable


class DSPyEmbeddingProvider:
    """
    Thin wrapper around dspy.Embedder for backward compatibility.

    Replaces custom EmbeddingProvider (292 lines → 95 lines).
    """

    def __init__(self):
        embedder_model = resolve_dspy_embedder_config()

        # Create dspy.Embedder
        if embedder_model == "fastembed":
            # Custom callable for FastEmbed
            embedder_func = create_fastembed_embedder()
            self.embedder = dspy.Embedder(embedder_func, batch_size=100)
        else:
            # Hosted model via litellm (openai, ollama, anthropic, etc.)
            self.embedder = dspy.Embedder(embedder_model, batch_size=200, caching=True)

        # Infer vector size from model name
        self.vector_size = self._infer_vector_size(embedder_model)

        logger.info(f"Initialized DSPy embedder: {embedder_model} (dim={self.vector_size})")

    def get_embedding(self, text: str) -> list[float]:
        """Get embedding for single text (backward compatible API)."""
        text_clean = text.replace("\n", " ")
        result = self.embedder(text_clean)

        if isinstance(result, np.ndarray):
            return result.tolist()
        return result

    def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for batch of texts (backward compatible API)."""
        texts_clean = [t.replace("\n", " ") for t in texts]
        result = self.embedder(texts_clean)

        if isinstance(result, np.ndarray):
            return result.tolist()
        return result

    def get_sparse_embedding(self, text: str) -> dict:
        """Get sparse embedding for BM25 hybrid search (Qdrant format)."""
        from collections import Counter

        text_lower = text.lower()
        # Simple tokenization: split on whitespace and punctuation
        tokens = text_lower.replace(",", " ").replace(".", " ").split()
        # Count token frequencies
        counts = Counter(tokens)
        # Create sparse vector with token index as key and frequency as value
        return {str(i): float(freq) for i, (token, freq) in enumerate(counts.items())}

    def _infer_vector_size(self, model_name: str) -> int:
        """
        Infer vector size from model name using comprehensive dimension map.

        Handles ollama's :latest suffix automatically.
        """
        dimension_map = {
            # OpenAI models
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
            # Ollama models
            "mxbai-embed-large": 1024,
            "nomic-embed-text": 768,
            "all-minilm": 384,
            "bge-small-en-v1.5": 384,
            "bge-base-en-v1.5": 768,
            "bge-large-en-v1.5": 1024,
            "snowflake-arctic-embed:22m": 384,
            "snowflake-arctic-embed:33m": 384,
            "snowflake-arctic-embed:110m": 768,
            "snowflake-arctic-embed:s": 384,
            "snowflake-arctic-embed:m": 768,
            "snowflake-arctic-embed2": 1024,
        }

        # Extract model base name (remove provider prefix)
        model_base = model_name.split("/")[-1]

        # Ollama adds :latest suffix - strip it before lookup
        if model_base.endswith(":latest"):
            model_base = model_base[:-7]

        return dimension_map.get(model_base, 1024)


# Alias for backward compatibility
EmbeddingProvider = DSPyEmbeddingProvider
