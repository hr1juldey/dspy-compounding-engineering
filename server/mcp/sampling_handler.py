"""
DSPy-based sampling handler using CE's LM configuration.

Provides a fallback sampling handler that uses the same LM configured
in .env (DSPY_LM_PROVIDER, DSPY_LM_MODEL) for clients without native sampling.
"""

from typing import cast

from server.config.settings import get_settings


def get_sampling_handler():
    """
    Get the appropriate sampling handler based on CE's LM configuration.

    Returns:
        Configured FastMCP sampling handler, or None if unavailable.
    """
    settings = get_settings()
    provider = settings.dspy_lm_provider.lower()
    model = settings.dspy_lm_model

    try:
        if provider == "ollama":
            # Ollama exposes OpenAI-compatible API at /v1
            from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
            from openai import AsyncOpenAI

            # Use Ollama's OpenAI-compatible endpoint
            base_url = settings.ollama_base_url.rstrip("/v1")  # Remove /v1 if present
            client = AsyncOpenAI(base_url=f"{base_url}/v1", api_key="ollama")
            return OpenAISamplingHandler(default_model=cast(str, model), client=client)  # type: ignore[arg-type]

        elif provider == "openai":
            from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler

            return OpenAISamplingHandler(default_model=cast(str, model))  # type: ignore[arg-type]

        elif provider == "anthropic":
            from fastmcp.client.sampling.handlers.anthropic import AnthropicSamplingHandler

            return AnthropicSamplingHandler(default_model=model)

        elif provider == "openrouter":
            import os

            from fastmcp.client.sampling.handlers.openai import OpenAISamplingHandler
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
            return OpenAISamplingHandler(default_model=cast(str, model), client=client)  # type: ignore[arg-type]

    except ImportError as e:
        # Handler not installed
        import sys

        print(f"Warning: Sampling handler for {provider} not available: {e}", file=sys.stderr)
        return None

    return None


# Create handler at module level for import
sampling_handler = get_sampling_handler()
