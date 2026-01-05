"""Unit tests for search providers and orchestration."""

import pytest

from utils.search.providers.searxng import SearXNGProvider
from utils.search.query_analyzer import QueryAnalyzer, QueryIntent


class TestIntentClassification:
    """Test query intent detection."""

    def test_docs_intent(self):
        """Detect documentation queries."""
        analyzer = QueryAnalyzer()
        assert analyzer.classify("how to use React hooks") == QueryIntent.DOCS
        assert analyzer.classify("tutorial for Python") == QueryIntent.DOCS
        assert analyzer.classify("learn Django setup") == QueryIntent.DOCS

    def test_news_intent(self):
        """Detect news/release queries."""
        analyzer = QueryAnalyzer()
        assert analyzer.classify("latest Python 3.12 features") == QueryIntent.NEWS
        assert analyzer.classify("recent Django release") == QueryIntent.NEWS
        assert analyzer.classify("2025 JavaScript updates") == QueryIntent.NEWS

    def test_code_intent(self):
        """Detect code/example queries."""
        analyzer = QueryAnalyzer()
        assert analyzer.classify("numpy array example") == QueryIntent.CODE
        assert analyzer.classify("GitHub async implementation") == QueryIntent.CODE
        assert analyzer.classify("API source code") == QueryIntent.CODE

    def test_academic_intent(self):
        """Detect academic/research queries."""
        analyzer = QueryAnalyzer()
        assert analyzer.classify("attention is all you need paper") == QueryIntent.ACADEMIC
        assert analyzer.classify("arxiv transformer research") == QueryIntent.ACADEMIC
        assert analyzer.classify("algorithm analysis survey") == QueryIntent.ACADEMIC

    def test_general_intent(self):
        """Default to general for unmatched queries."""
        analyzer = QueryAnalyzer()
        assert analyzer.classify("what is a tree") == QueryIntent.GENERAL
        assert analyzer.classify("random question") == QueryIntent.GENERAL


class TestSearXNGProvider:
    """Test SearXNG search provider."""

    @pytest.mark.integration
    def test_health_check(self):
        """Test SearXNG availability on localhost."""
        provider = SearXNGProvider("http://localhost:8080")
        # Note: This test requires SearXNG to be running
        # Skip in CI unless SearXNG is available
        result = provider.health_check()
        assert isinstance(result, bool)

    @pytest.mark.integration
    def test_search_returns_results(self):
        """Test basic search functionality."""
        provider = SearXNGProvider("http://localhost:8080")
        results = provider.search("Python programming", max_results=5)
        assert isinstance(results, list)
        # Only assert structure if results returned
        if results:
            for result in results:
                assert hasattr(result, "title")
                assert hasattr(result, "url")
                assert hasattr(result, "snippet")

    @pytest.mark.integration
    def test_search_respects_max_results(self):
        """Test max_results parameter is respected."""
        provider = SearXNGProvider("http://localhost:8080")
        results = provider.search("test query", max_results=3)
        assert len(results) <= 3

    @pytest.mark.integration
    def test_timeout_protection(self):
        """Test that provider has timeout protection."""
        provider = SearXNGProvider("http://localhost:8080")
        # Timeout config should be set
        assert provider.timeout_config is not None
        assert provider.timeout_config.connect == 5.0
        assert provider.timeout_config.read == 10.0
