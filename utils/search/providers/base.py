"""Base classes for search providers."""

from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel


class SearchResult(BaseModel):
    """Single search result."""

    title: str
    url: str
    snippet: str
    score: Optional[float] = None  # For reranking


class SearchProvider(ABC):
    """Abstract base for search providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Execute search and return results."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is available."""
        pass
