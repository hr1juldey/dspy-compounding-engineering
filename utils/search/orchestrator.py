"""Main web search orchestration with resilient fallbacks."""

import time
from typing import List

from infrastructure.events.collector import event_collector
from infrastructure.events.event import EventStatus

from utils.io.logger import logger
from utils.search.providers.base import SearchResult
from utils.search.providers.factory import SearchProviderFactory
from utils.search.query_analyzer import QueryAnalyzer
from utils.search.query_formatter import QueryFormatter
from utils.search.reranker import SearchReranker


class WebSearchOrchestrator:
    """Orchestrate full search pipeline with fallback resilience."""

    def __init__(self):
        self.provider = SearchProviderFactory.create()
        self.analyzer = QueryAnalyzer()
        self.formatter = QueryFormatter()
        self.reranker = SearchReranker()
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds

    def _simplify_query(self, query: str) -> str:
        """Simplify query by removing modifiers (how, what, why, etc)."""
        keywords = ["how to", "what is", "why does", "can you", "please"]
        simplified = query.lower()
        for keyword in keywords:
            simplified = simplified.replace(keyword, "").strip()
        return simplified or query

    def _broaden_query(self, query: str) -> str:
        """Broaden query by removing specific terms."""
        words = query.split()
        return " ".join(words[:3]) if len(words) > 3 else query

    def _handle_empty_results(
        self, query: str, results: List[SearchResult], max_results: int
    ) -> List[SearchResult]:
        """Try fallback queries if no results found."""
        # Fallback 1: Try simplified original query
        if not results:
            simplified = self._simplify_query(query)
            if simplified != query.lower():
                logger.info(f"No results, trying simplified query: {simplified}")
                results = self._search_with_retry(simplified, max_results=max_results)

        # Fallback 2: Try broadened query
        if not results:
            broadened = self._broaden_query(query)
            if broadened != query:
                logger.info(f"No results, trying broadened query: {broadened}")
                results = self._search_with_retry(broadened, max_results=max_results)

        # Fallback 3: Try original unoptimized query
        if not results:
            logger.info(f"No results, trying original unoptimized query: {query}")
            results = self._search_with_retry(query, max_results=max_results)

        return results

    def _emit_search_event(
        self,
        query: str,
        status: str,
        duration_ms: int,
        attempt: int,
        error: str = None,
        results_count: int = 0,
    ) -> None:
        """Emit search operation event."""
        event_collector.emit(
            operation="web_search",
            subject=query,
            status=status,
            details={
                "results": results_count,
                "provider": "searxng",
                "attempt": attempt,
            },
            duration_ms=duration_ms,
            error=error,
        )

    def _search_with_retry(
        self, query: str, max_results: int = 10, retry_count: int = 0
    ) -> List[SearchResult]:
        """Execute search with retry logic for timeouts/unavailability."""
        start = time.time()
        try:
            logger.debug(f"Search attempt {retry_count + 1}/{self.max_retries} for: {query}")
            results = self.provider.search(query, max_results=max_results)
            duration = int((time.time() - start) * 1000)
            self._emit_search_event(
                query,
                EventStatus.SUCCESS,
                duration,
                retry_count + 1,
                results_count=len(results),
            )
            return results
        except (TimeoutError, ConnectionError) as e:
            duration = int((time.time() - start) * 1000)
            if retry_count < self.max_retries - 1:
                wait_time = self.retry_delay * (2**retry_count)
                logger.warning(
                    f"Search timeout/connection error (attempt {retry_count + 1}), "
                    f"retrying in {wait_time}s: {type(e).__name__}"
                )
                time.sleep(wait_time)
                return self._search_with_retry(query, max_results, retry_count + 1)
            else:
                logger.error(f"Search failed after {self.max_retries} retries: {type(e).__name__}")
                self._emit_search_event(
                    query, EventStatus.FAILED, duration, retry_count + 1, error=str(e)
                )
                return []
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error(f"Unexpected search error: {type(e).__name__}: {e}")
            error_msg = f"{type(e).__name__}: {e}"
            self._emit_search_event(
                query, EventStatus.FAILED, duration, retry_count + 1, error=error_msg
            )
            return []

    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Execute full search pipeline with intelligent fallbacks."""
        logger.info(f"Web search: {query}")

        # Step 1: Classify intent
        intent = self.analyzer.classify(query)
        logger.debug(f"Query intent: {intent.value}")

        # Step 2: Format query (DSPy)
        optimized_query = self.formatter.format(query, intent)
        logger.debug(f"Optimized query: {optimized_query}")

        # Step 3: Execute search with fallback logic
        results = self._search_with_retry(optimized_query, max_results=max_results)
        results = self._handle_empty_results(query, results, max_results)

        if not results:
            logger.warning(f"No search results found for: {query}")
            return []

        # Step 4: Rerank results
        reranked = self.reranker.rerank(query, optimized_query, results, intent)

        logger.info(f"Returned {len(reranked)} results after {len(results)} found")
        return reranked[:5]
