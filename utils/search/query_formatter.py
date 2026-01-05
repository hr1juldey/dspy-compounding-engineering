"""DSPy-powered query optimization."""

from typing import cast

import dspy

from utils.search.query_analyzer import QueryIntent


class QueryFormatterSignature(dspy.Signature):
    """Optimize search query for better results."""

    intent: str = dspy.InputField(desc="Search intent: code/news/docs/academic/general")
    original_query: str = dspy.InputField(desc="Original user query")
    optimized_query: str = dspy.OutputField(
        desc="Optimized search query: concise, keyword-focused, removes filler "
        "words, adds context keywords"
    )


class QueryFormatter:
    """Format queries using DSPy."""

    def __init__(self):
        self.formatter = dspy.ChainOfThought(QueryFormatterSignature)

    def format(self, query: str, intent: QueryIntent) -> str:
        """Format query with DSPy."""
        try:
            result = cast(
                dspy.Prediction, self.formatter(intent=intent.value, original_query=query)
            )
            return result.optimized_query
        except Exception:
            # Fallback: return original query
            return query
