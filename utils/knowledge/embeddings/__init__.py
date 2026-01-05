"""Embeddings subsystem - embedding generation and management."""

from utils.knowledge.embeddings.batch_embedder import BatchEmbedder
from utils.knowledge.embeddings.collection_initializer import CollectionInitializer
from utils.knowledge.embeddings.collection_metadata import CollectionMetadata
from utils.knowledge.embeddings.matryoshka_config import (
    is_matryoshka_model,
    truncate_embedding,
    validate_dimension,
)
from utils.knowledge.embeddings.provider import DSPyEmbeddingProvider, resolve_dspy_embedder_config

__all__ = [
    "BatchEmbedder",
    "CollectionInitializer",
    "CollectionMetadata",
    "DSPyEmbeddingProvider",
    "is_matryoshka_model",
    "resolve_dspy_embedder_config",
    "truncate_embedding",
    "validate_dimension",
]
