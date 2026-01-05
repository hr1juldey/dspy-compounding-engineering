"""MCC-based search result reranking using embedding similarity."""

import os

import numpy as np

from utils.knowledge.embeddings.provider import DSPyEmbeddingProvider
from utils.search.providers.base import SearchResult
from utils.search.query_analyzer import QueryIntent


class SearchReranker:
    """Rerank results using MultiChainComparison with embedding-based judges."""

    def __init__(self, mode: str | None = None, num_chains: int | None = None):
        """
        Args:
            mode: always/disabled/adaptive (from SEARCH_RERANKING env var)
            num_chains: Number of MCC chains (3-5, from SEARCH_MCC_CHAINS env var)
        """
        self.mode = mode or os.getenv("SEARCH_RERANKING", "adaptive")

        # Parse num_chains from env (default: 3, min: 3, max: 5)
        chains_env = num_chains or int(os.getenv("SEARCH_MCC_CHAINS", "3"))
        self.num_chains = max(3, min(5, chains_env))

        self.embedder = DSPyEmbeddingProvider()

    def should_rerank(self, intent: QueryIntent) -> bool:
        """Determine if reranking should be applied."""
        if self.mode == "always":
            return True
        elif self.mode == "disabled":
            return False
        else:  # adaptive
            # Rerank for DOCS and CODE (high precision needs)
            return intent in [QueryIntent.DOCS, QueryIntent.CODE]

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def rerank(
        self,
        query: str,
        optimized_query: str,
        results: list[SearchResult],
        intent: QueryIntent,
    ) -> list[SearchResult]:
        """
        Rerank using MCC (M=3-5 chains) with embedding-based judges.

        Chain formulations:
        - Chain 1: Original query
        - Chain 2: Optimized query
        - Chain 3: Combined (original + optimized)
        - Chain 4: Title-focused (if num_chains >= 4)
        - Chain 5: Snippet-focused (if num_chains == 5)
        """
        if not self.should_rerank(intent):
            return results

        if len(results) <= 3:
            return results  # No need to rerank few results

        try:
            # Prepare query embeddings for all chains
            query_variants = [
                query,  # Chain 1: Original
                optimized_query,  # Chain 2: Optimized
                f"{query} {optimized_query}",  # Chain 3: Combined
                f"title: {optimized_query}",  # Chain 4: Title-focused
                f"description: {optimized_query}",  # Chain 5: Snippet-focused
            ]

            # Embed only the chains we'll use
            query_embeddings = [
                self.embedder.get_embedding(q) for q in query_variants[: self.num_chains]
            ]

            # Score each result with M chains for consensus
            scored_results = []
            for result in results:
                # Embed result content
                result_text = f"{result.title} {result.snippet}"
                result_emb = self.embedder.get_embedding(result_text)

                # Compute similarity for each chain
                scores = [self._cosine_similarity(q_emb, result_emb) for q_emb in query_embeddings]

                # Use median of M scores (robust to outliers)
                result.score = float(np.median(scores))
                scored_results.append(result)

            # Sort by score descending
            scored_results.sort(key=lambda r: r.score or 0, reverse=True)
            return scored_results

        except Exception:
            # Fallback: return original order
            return results
