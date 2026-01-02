"""Language model provider configuration and token detection."""

import os

import dspy

from server.config.project import DEFAULT_MAX_TOKENS
from utils.io.logger import console, logger


def resolve_embedding_config() -> tuple[str, str, str | None]:
    """Determine embedding provider, model, and base URL from environment."""
    lm_provider = os.getenv("DSPY_LM_PROVIDER", "openai")
    raw_provider = os.getenv("EMBEDDING_PROVIDER")
    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    base_url = os.getenv("EMBEDDING_BASE_URL", None)
    if raw_provider:
        return raw_provider, model_name, base_url
    if lm_provider == "openrouter" and os.getenv("OPENROUTER_API_KEY"):
        return "openrouter", model_name, base_url
    return "openai", model_name, base_url


def _get_openrouter_max_tokens(model_name: str) -> int | None:
    """Query OpenRouter API for model's context length."""
    try:
        import httpx

        api_key = os.getenv("OPENROUTER_API_KEY")
        clean_name = model_name.replace(":free", "")
        resp = httpx.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            timeout=5.0,
        )
        if resp.status_code != 200:
            return None
        for m in resp.json().get("data", []):
            model_id = m.get("id", "")
            if model_id == model_name or model_id == clean_name or clean_name in model_id:
                ctx = m.get("context_length", 128000)
                max_out = min(ctx // 4, 32768)
                console.print(f"[dim]Model {model_name}: context={ctx}, max_tokens={max_out}[/dim]")
                return max_out
        return None
    except Exception:
        return None


def get_model_max_tokens(model_name: str, provider: str = "openai") -> int:
    """Auto-detect max output tokens for a model."""
    try:
        import litellm

        lookup_map = {
            "openrouter": f"openrouter/{model_name}",
            "anthropic": f"anthropic/{model_name}",
            "ollama": f"ollama/{model_name}",
        }
        lookup_name = lookup_map.get(provider, model_name)
        model_info = litellm.get_model_info(lookup_name)
        max_output = model_info.get("max_output_tokens") or model_info.get(
            "max_tokens", DEFAULT_MAX_TOKENS
        )
        result = min(max_output, 32768)
        console.print(f"[dim]Model {lookup_name}: max_tokens={max_output}, using {result}[/dim]")
        return result
    except Exception:
        pass
    if provider == "openrouter":
        or_result = _get_openrouter_max_tokens(model_name)
        if or_result:
            return or_result
    console.print(f"[dim]Model {model_name}: using default max_tokens={DEFAULT_MAX_TOKENS}[/dim]")
    return DEFAULT_MAX_TOKENS


def configure_dspy(env_file: str | None = None):
    """Configure DSPy with the appropriate LM provider and settings."""
    from server.config.env_loader import load_configuration
    from server.config.service_registry import registry

    load_configuration(env_file)
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        if os.getenv("LANGFUSE_HOST") and not os.getenv("LANGFUSE_BASE_URL"):
            os.environ["LANGFUSE_BASE_URL"] = os.environ["LANGFUSE_HOST"]
        try:
            if not os.getenv("COMPOUNDING_QUIET"):
                console.print("[dim]Langfuse observability enabled.[/dim]")
        except ImportError:
            logger.warning("openinference-instrumentation-dspy not found.")
        except Exception as e:
            logger.error("Failed to initialize Langfuse tracing", detail=str(e))
    registry.check_qdrant()
    registry.check_api_keys()
    provider = os.getenv("DSPY_LM_PROVIDER", "openai")
    model_name = os.getenv("DSPY_LM_MODEL", "gpt-4.1")
    max_tokens = get_model_max_tokens(model_name, provider)
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set.")
        lm = dspy.LM(model=model_name, api_key=api_key, max_tokens=max_tokens)
    elif provider == "anthropic":
        lm = dspy.LM(
            model=f"anthropic/{model_name}",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=max_tokens,
        )
    elif provider == "ollama":
        lm = dspy.LM(model=f"ollama/{model_name}", max_tokens=max_tokens)
    elif provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set.")
        lm = dspy.LM(
            model=f"openai/{model_name}",
            api_key=api_key,
            api_base="https://openrouter.ai/api/v1",
            max_tokens=max_tokens,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    dspy.settings.configure(lm=lm)
