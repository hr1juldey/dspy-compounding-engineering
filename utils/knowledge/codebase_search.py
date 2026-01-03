"""
Vector-based codebase search.

Queries indexed code chunks via embedding similarity.
"""

from typing import Any, Dict, List

from utils.io.logger import logger


class CodebaseSearch:
    """
    Search indexed codebase using vector embeddings.

    Single Responsibility: Execute semantic searches on indexed code.
    """

    def __init__(self, client, collection_name: str, embedding_provider):
        """
        Initialize search handler.

        Args:
            client: Qdrant client
            collection_name: Collection to search
            embedding_provider: Provider for query embeddings
        """
        self.client = client
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search codebase for relevant code snippets.

        Args:
            query: Search query text
            limit: Maximum results to return (default: 5)

        Returns:
            List of matching code chunks with scores
        """
        try:
            # Get embedding for query
            query_vector = self.embedding_provider.get_embedding(query)

            # Query Qdrant collection
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
            ).points

            # Format results with scores
            results = []
            for hit in search_result:
                payload = hit.payload
                payload["score"] = hit.score
                results.append(payload)

            return results

        except Exception as e:
            logger.error(f"Codebase search failed: {e}")
            return []
