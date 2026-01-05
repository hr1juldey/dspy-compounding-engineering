"""Rule-based query intent classification."""

from enum import Enum


class QueryIntent(Enum):
    """Search intent categories."""

    CODE = "code"  # Code examples, APIs
    NEWS = "news"  # Recent events, releases
    DOCS = "documentation"  # How-to, tutorials
    ACADEMIC = "academic"  # Research papers
    GENERAL = "general"  # Everything else


class QueryAnalyzer:
    """Classify query intent using keyword matching."""

    # Intent keyword patterns
    PATTERNS = {
        QueryIntent.CODE: [
            "example",
            "sample",
            "snippet",
            "implementation",
            "github",
            "source code",
            "api",
            "function",
            "class",
        ],
        QueryIntent.NEWS: [
            "latest",
            "recent",
            "new",
            "release",
            "announcement",
            "2024",
            "2025",
            "2026",
            "update",
            "version",
        ],
        QueryIntent.DOCS: [
            "how to",
            "tutorial",
            "guide",
            "documentation",
            "learn",
            "setup",
            "install",
            "configure",
            "use",
        ],
        QueryIntent.ACADEMIC: [
            "paper",
            "research",
            "arxiv",
            "study",
            "algorithm",
            "theory",
            "analysis",
            "survey",
        ],
    }

    @classmethod
    def classify(cls, query: str) -> QueryIntent:
        """Classify query intent."""
        query_lower = query.lower()

        # Count keyword matches per intent
        scores = dict.fromkeys(QueryIntent, 0)

        for intent, keywords in cls.PATTERNS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[intent] += 1

        # Return intent with highest score, default to GENERAL
        max_score = max(scores.values())
        if max_score == 0:
            return QueryIntent.GENERAL

        return max(scores, key=scores.get)  # type: ignore[no-overload-found]
