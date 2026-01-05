"""Hybrid dense/sparse search with disk fallback."""

import glob
import json
import os
from typing import cast

from qdrant_client.models import (
    Condition,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    Prefetch,
)
from rich.console import Console

console = Console()


class LearningRetrieval:
    """Hybrid search with Qdrant fallback to disk."""

    def __init__(self, client, collection_name, embedding_provider, knowledge_dir):
        self.client = client
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider
        self.knowledge_dir = knowledge_dir

    def retrieve_relevant(self, query: str = "", tags: list | None = None, limit: int = 5):
        """Hybrid search with tag filtering, falls back to disk."""
        if not query and not tags:
            return self._legacy_search(limit=limit)
        try:
            query_filter = None
            if tags:
                tags_conds = [
                    FieldCondition(key="tags", match=MatchValue(value=tag)) for tag in tags
                ]
                cat_conds = [
                    FieldCondition(key="category", match=MatchValue(value=tag)) for tag in tags
                ]
                conds = tags_conds + cat_conds
                query_filter = Filter(should=cast(list[Condition], conds))

            dense = self.embedding_provider.get_embedding(query)
            sparse = self.embedding_provider.get_sparse_embedding(query)
            result = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    Prefetch(query=dense, using=None, limit=limit * 2, filter=query_filter),
                    Prefetch(
                        query=sparse, using="text-sparse", limit=limit * 2, filter=query_filter
                    ),
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=limit,
            ).points
            return [hit.payload for hit in result]

        except Exception as e:
            console.print(f"[red]Hybrid search failed: {e}. Falling back to disk.[/red]")
            return self._legacy_search(query, tags, limit)

    def _legacy_search(self, query: str = "", tags: list | None = None, limit: int = 5):
        """Disk-based search fallback."""
        results = []
        for filepath in sorted(glob.glob(os.path.join(self.knowledge_dir, "*.json")), reverse=True):
            try:
                with open(filepath) as f:
                    learning = json.load(f)

                if tags:
                    ltags = learning.get("tags", [])
                    ltags.append(learning.get("category", ""))
                    if not any(tag.lower() in [t.lower() for t in ltags] for tag in tags):
                        continue

                if query:
                    text = (
                        f"{learning.get('title', '')} "
                        f"{learning.get('description', '')} "
                        f"{learning.get('content', '')}"
                    ).lower()
                    if query.lower() not in text:
                        continue

                results.append(learning)
                if len(results) >= limit:
                    break

            except Exception:
                continue
        return results
