"""
Server configuration using Pydantic Settings.
Loads from .env file in project root.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """Server configuration loaded from environment variables."""

    # Server settings
    host: str = "127.0.0.1"
    port: int = 12000
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 12001

    # LM Provider
    dspy_lm_provider: str = "ollama"
    dspy_lm_model: str = "qwen2.5vl:7b"
    ollama_base_url: str = "http://localhost:11434/v1"
    dspy_max_tokens: int = 16384

    # Embeddings
    embedding_provider: str = "ollama"
    embedding_model: str = "mxbai-embed-large:latest"
    embedding_base_url: str = "http://localhost:11434/api/embed/"

    # Vector Database
    qdrant_url: str = "http://localhost:6333"
    kb_max_retrieved: int = 25
    kb_similarity_threshold: float = 0.6

    # Redis (Celery broker)
    redis_url: str = "redis://localhost:6350"

    # Semantic Chunking
    use_semantic_chunking: bool = True
    semantic_chunk_size: int = 2000
    semantic_chunk_overlap: int = 200
    use_llm_chunking_validation: bool = True

    # Batch processing
    optimal_batch_size: int = 100

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


_settings: ServerSettings | None = None


def get_settings() -> ServerSettings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = ServerSettings()
    return _settings


# Create settings instance for easy access
settings = get_settings()

__all__ = ["ServerSettings", "get_settings", "settings"]
