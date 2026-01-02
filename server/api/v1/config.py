"""
FastAPI endpoints for .env configuration management.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter(prefix="/config", tags=["config"])

templates = Jinja2Templates(directory="server/ui/templates")


class ConfigUpdate(BaseModel):
    """Model for configuration updates."""

    DSPY_LM_PROVIDER: str | None = None
    DSPY_LM_MODEL: str | None = None
    OLLAMA_BASE_URL: str | None = None
    EMBEDDING_PROVIDER: str | None = None
    EMBEDDING_MODEL: str | None = None
    QDRANT_URL: str | None = None
    REDIS_URL: str | None = None
    HOST: str | None = None
    PORT: int | None = None


def load_env_config() -> dict:
    """Load current .env configuration."""
    env_path = Path(".env")
    config = {}

    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key] = value

    return config


def update_env_file(updates: dict) -> None:
    """Update .env file with new values."""
    env_path = Path(".env")
    config = load_env_config()

    # Update with new values (filter None)
    for key, value in updates.items():
        if value is not None:
            config[key] = str(value)

    # Write back to file
    with open(env_path, "w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")


@router.get("", response_class=HTMLResponse)
async def config_ui(request: Request):
    """Serve configuration UI."""
    current_config = load_env_config()
    return templates.TemplateResponse("config.html", {"request": request, "config": current_config})


@router.get("/current")
async def get_current_config() -> dict:
    """Get current configuration (API)."""
    return load_env_config()


@router.post("")
async def update_config(config: ConfigUpdate) -> dict:
    """Update .env configuration."""
    update_env_file(config.model_dump(exclude_none=True))
    return {"status": "updated", "message": "Configuration saved successfully"}


@router.get("/llm/providers")
async def get_llm_providers() -> dict:
    """Get list of supported LLM providers."""
    return {
        "providers": [
            {"name": "ollama", "description": "Local Ollama models"},
            {"name": "openai", "description": "OpenAI API (GPT-4, etc.)"},
            {"name": "anthropic", "description": "Anthropic API (Claude)"},
        ]
    }


@router.get("/llm/models")
async def get_llm_models(provider: str) -> dict:
    """Get list of available models for a provider."""
    models_map = {
        "ollama": [
            "qwen2.5:7b",
            "qwen2.5:14b",
            "llama3.3:70b",
            "deepseek-r1:70b",
            "gemma2:27b",
        ],
        "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"],
    }

    if provider not in models_map:
        return {"error": f"Unknown provider: {provider}", "models": []}

    return {"provider": provider, "models": models_map[provider]}


@router.get("/embeddings/providers")
async def get_embedding_providers() -> dict:
    """Get list of supported embedding providers."""
    return {
        "providers": [
            {"name": "ollama", "description": "Local Ollama embeddings"},
            {"name": "openai", "description": "OpenAI embeddings"},
            {"name": "huggingface", "description": "HuggingFace transformers"},
        ]
    }


@router.get("/embeddings/models")
async def get_embedding_models(provider: str) -> dict:
    """Get list of available embedding models for a provider."""
    models_map = {
        "ollama": ["nomic-embed-text", "mxbai-embed-large", "all-minilm"],
        "openai": ["text-embedding-3-large", "text-embedding-3-small"],
        "huggingface": ["BAAI/bge-large-en-v1.5", "sentence-transformers/all-MiniLM-L6-v2"],
    }

    if provider not in models_map:
        return {"error": f"Unknown provider: {provider}", "models": []}

    return {"provider": provider, "models": models_map[provider]}
