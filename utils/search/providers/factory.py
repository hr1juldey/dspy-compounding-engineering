"""Search provider factory."""

import os

from utils.io.logger import logger
from utils.search.providers.base import SearchProvider
from utils.search.providers.searxng import SearXNGProvider


class SearchProviderFactory:
    """Factory for creating search providers."""

    @staticmethod
    def create(provider_name: str | None = None) -> SearchProvider:
        """Create search provider from config."""
        provider_name = provider_name or os.getenv("SEARCH_PROVIDER", "searxng")

        if provider_name == "searxng":
            base_url = os.getenv("SEARXNG_URL", "http://localhost:8080")
            logger.info(f"Using SearXNG provider at {base_url}")
            return SearXNGProvider(base_url=base_url)

        raise ValueError(f"Unknown search provider: {provider_name}")
