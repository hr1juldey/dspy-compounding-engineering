"""Server configuration package - central config for Compounding Engineering."""

from server.config.env_loader import load_configuration
from server.config.lm_provider import (
    configure_dspy,
    get_model_max_tokens,
    resolve_embedding_config,
)
from server.config.project import (
    CONTEXT_OUTPUT_RESERVE,
    CONTEXT_WINDOW_LIMIT,
    DEFAULT_MAX_TOKENS,
    DENSE_FALLBACK_MODEL_NAME,
    SPARSE_MODEL_NAME,
    TIER_1_FILES,
    get_project_hash,
    get_project_root,
)
from server.config.service_registry import ServiceRegistry, registry

__all__ = [
    "configure_dspy",
    "get_project_root",
    "get_project_hash",
    "ServiceRegistry",
    "registry",
    "load_configuration",
    "get_model_max_tokens",
    "resolve_embedding_config",
    "CONTEXT_WINDOW_LIMIT",
    "CONTEXT_OUTPUT_RESERVE",
    "DEFAULT_MAX_TOKENS",
    "TIER_1_FILES",
    "SPARSE_MODEL_NAME",
    "DENSE_FALLBACK_MODEL_NAME",
]
