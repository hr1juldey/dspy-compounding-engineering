"""SearXNG search provider with timeout protection."""

from typing import List

import httpx

from utils.io.logger import logger
from utils.search.providers.base import SearchProvider, SearchResult


class SearXNGProvider(SearchProvider):
    """SearXNG metasearch provider with robust error handling."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.timeout_config = httpx.Timeout(
            connect=5.0,  # DNS + TCP
            read=10.0,  # Response read
            write=5.0,
            pool=5.0,
        )

    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Execute SearXNG search with validation."""
        if not query or not query.strip():
            logger.warning("Empty search query")
            return []

        try:
            with httpx.Client(timeout=self.timeout_config) as client:
                response = client.post(
                    f"{self.base_url}/search",
                    data={"q": query, "format": "json", "safesearch": 0},
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for item in data.get("results", [])[:max_results]:
                    title = item.get("title", "").strip()
                    url = item.get("url", "").strip()
                    snippet = item.get("content", "").strip()

                    # Skip invalid results
                    if not title or not url:
                        continue

                    results.append(SearchResult(title=title, url=url, snippet=snippet))

                logger.info(f"SearXNG returned {len(results)} results for: {query}")
                return results

        except httpx.TimeoutException as e:
            logger.error(f"SearXNG timeout after 10s (provider sleeping?): {e}")
            raise TimeoutError(f"SearXNG timeout: {e}") from e
        except httpx.ConnectError as e:
            logger.error(f"SearXNG connection failed (not running?): {e}")
            raise ConnectionError(f"SearXNG unavailable: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"SearXNG HTTP error {e.response.status_code}: {e}")
            raise Exception(f"SearXNG HTTP error: {e}") from e
        except Exception as e:
            logger.error(f"SearXNG unexpected error: {type(e).__name__}: {e}")
            raise

    def health_check(self) -> bool:
        """Check SearXNG availability with quick timeout."""
        try:
            with httpx.Client(timeout=httpx.Timeout(3.0)) as client:
                response = client.get(f"{self.base_url}/", follow_redirects=True)
                is_healthy = response.status_code == 200
                if is_healthy:
                    logger.debug("SearXNG health check passed")
                else:
                    logger.warning(f"SearXNG returned status {response.status_code}")
                return is_healthy
        except httpx.TimeoutException:
            logger.warning("SearXNG health check timeout (provider sleeping)")
            return False
        except httpx.ConnectError:
            logger.warning("SearXNG not reachable (connection failed)")
            return False
        except Exception as e:
            logger.warning(f"SearXNG health check failed: {type(e).__name__}")
            return False
