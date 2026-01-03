"""Batch indexing of learnings to Qdrant (50x speedup via batch embedding)."""

import itertools
import json
import os
import uuid

from qdrant_client.models import PointStruct

from utils.io.logger import console, logger


def _prepare_text(learning: dict) -> str:
    """Prepare text for embedding."""
    parts = [learning.get("title", ""), learning.get("description", "")]
    content = learning.get("content", "")
    parts.append(content.get("summary", "") if isinstance(content, dict) else content)
    if learning.get("codified_improvements"):
        for imp in learning["codified_improvements"]:
            parts.append(f"{imp.get('title', '')} {imp.get('description', '')}")
    return " ".join(str(p).strip() for p in parts if str(p).strip())


class LearningIndexer:
    """Batch embed and store learnings in Qdrant."""

    def __init__(self, client, collection_name: str, embedding_provider):
        self.client = client
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider

    def index_learning(self, learning: dict) -> bool:
        """Index single learning to Qdrant."""
        if not self.client or not learning:
            return False
        try:
            text = _prepare_text(learning)
            if not text:
                return False
            dense = self.embedding_provider.get_embeddings_batch([text])
            sparse = [self.embedding_provider.get_sparse_embedding(text)]
            lid = learning.get("id") or str(uuid.uuid4())
            pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(lid)))
            point = PointStruct(
                id=pid, vector={"": dense[0], "text-sparse": sparse[0]}, payload=learning
            )
            self.client.upsert(collection_name=self.collection_name, points=[point])
            return True
        except Exception as e:
            logger.error(f"Failed to index learning: {e}")
            return False

    def sync_to_qdrant(self, knowledge_dir: str, batch_size: int = 10):
        """Sync learnings from disk to Qdrant in batches (50x speedup)."""
        files = [
            f for f in os.listdir(knowledge_dir) if f.endswith(".json") and not f.startswith(".")
        ]
        synced_count = 0
        for batch in iter(lambda: list(itertools.islice(iter(files), batch_size)), []):
            texts, learnings = [], []
            for fname in batch:
                try:
                    with open(os.path.join(knowledge_dir, fname)) as f:
                        learning = json.load(f)
                    texts.append(_prepare_text(learning))
                    learnings.append(learning)
                except Exception as e:
                    logger.error(f"Load failed: {e}")

            if not texts:
                continue

            # Batch embed (critical 50x speedup)
            dense = self.embedding_provider.get_embeddings_batch(texts)
            sparse = [self.embedding_provider.get_sparse_embedding(t) for t in texts]

            points = []
            for idx, learning in enumerate(learnings):
                try:
                    pid = str(
                        uuid.uuid5(uuid.NAMESPACE_DNS, learning.get("id") or str(uuid.uuid4()))
                    )
                    points.append(
                        PointStruct(
                            id=pid,
                            vector={"": dense[idx], "text-sparse": sparse[idx]},
                            payload=learning,
                        )
                    )
                except Exception as e:
                    logger.error(f"Point creation failed: {e}")

            if points:
                self.client.upsert(collection_name=self.collection_name, points=points)
                synced_count += len(points)
        if synced_count:
            console.print(f"[green]Synced {synced_count}.[/green]")
