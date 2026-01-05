"""
Matryoshka embedding model configuration and validation.

Matryoshka embeddings support variable dimensions by truncating
the full-dimensional embedding vector to smaller sizes.
"""

from utils.io.logger import logger

# Registry of Matryoshka-capable models
MATRYOSHKA_MODELS = {
    "ollama/qwen3-embedding:8b": {
        "native_dimension": 4096,
        "supported_dimensions": [128, 256, 512, 1024, 2048, 4096],
    },
    "ollama/qwen3-embedding:4b": {
        "native_dimension": 2560,
        "supported_dimensions": [128, 256, 512, 1024, 2560],
    },
    "ollama/qwen3-embedding:0.6b": {
        "native_dimension": 1024,
        "supported_dimensions": [128, 256, 512, 768, 1024],
    },
    "ollama/nomic-embed-text": {
        "native_dimension": 768,
        "supported_dimensions": [128, 256, 384, 512, 768],
    },
}


def is_matryoshka_model(model_name: str) -> bool:
    """
    Check if a model supports Matryoshka embeddings.

    Args:
        model_name: Name of embedding model

    Returns:
        True if model supports dimension truncation
    """
    return model_name in MATRYOSHKA_MODELS


def get_native_dimension(model_name: str) -> int | None:
    """
    Get native (full) dimension for a model.

    Args:
        model_name: Name of embedding model

    Returns:
        Native dimension or None if not Matryoshka model
    """
    if not is_matryoshka_model(model_name):
        return None
    return MATRYOSHKA_MODELS[model_name]["native_dimension"]  # type: ignore[return-value]


def get_supported_dimensions(model_name: str) -> list[int]:
    """
    Get supported truncation dimensions for a model.

    Args:
        model_name: Name of embedding model

    Returns:
        List of supported dimensions (empty if not Matryoshka)
    """
    if not is_matryoshka_model(model_name):
        return []
    return MATRYOSHKA_MODELS[model_name]["supported_dimensions"]  # type: ignore[return-value]


def validate_dimension(model_name: str, requested_dim: int) -> bool:
    """
    Validate requested dimension against model capabilities.

    Args:
        model_name: Name of embedding model
        requested_dim: Requested embedding dimension

    Returns:
        True if dimension is supported
    """
    if not is_matryoshka_model(model_name):
        logger.warning(
            f"Model {model_name} is not a Matryoshka model - dimension selection ignored"
        )
        return False

    supported = get_supported_dimensions(model_name)
    is_valid = requested_dim in supported

    if not is_valid:
        logger.error(
            f"Dimension {requested_dim} not supported for {model_name}. Supported: {supported}"
        )

    return is_valid


def get_closest_dimension(model_name: str, requested_dim: int) -> int:
    """
    Get closest supported dimension to requested dimension.

    Useful for auto-correction when user requests unsupported dim.

    Args:
        model_name: Name of embedding model
        requested_dim: Requested embedding dimension

    Returns:
        Closest supported dimension (or requested if not Matryoshka)
    """
    if not is_matryoshka_model(model_name):
        return requested_dim

    supported = get_supported_dimensions(model_name)
    if not supported:
        return requested_dim

    # Find closest dimension
    closest = min(supported, key=lambda x: abs(x - requested_dim))
    return closest


def truncate_embedding(embedding: list[float], target_dimension: int) -> list[float]:
    """
    Truncate embedding to target dimension.

    Matryoshka embeddings are designed to be truncated from the front,
    preserving the most important features in earlier dimensions.

    Args:
        embedding: Full-dimensional embedding vector
        target_dimension: Target dimension (must be <= len(embedding))

    Returns:
        Truncated embedding vector
    """
    if target_dimension > len(embedding):
        logger.warning(
            f"Target dimension {target_dimension} > "
            f"embedding length {len(embedding)} - returning full embedding"
        )
        return embedding

    if target_dimension == len(embedding):
        return embedding

    # Matryoshka: truncate from front
    truncated = embedding[:target_dimension]

    logger.debug(f"Truncated embedding from {len(embedding)} to {target_dimension}")

    return truncated
