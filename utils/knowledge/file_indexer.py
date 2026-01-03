"""Index single codebase files with batch embedding."""

import os
import uuid

from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct


class FileIndexer:
    """Index individual codebase files."""

    def __init__(self, client, collection_name, batch_embedder, semantic_chunker=None):
        self.client = client
        self.collection_name = collection_name
        self.batch_embedder = batch_embedder
        self.semantic_chunker = semantic_chunker

    def index_file(self, filepath: str, full_path: str, indexed_files: dict) -> bool:
        """Index single file if changed. Returns True if updated."""
        mtime = os.path.getmtime(full_path)

        # Skip if unchanged
        if filepath in indexed_files and indexed_files[filepath] >= mtime:
            return False

        # Read content
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            return False

        # Chunk content
        if self.semantic_chunker and filepath.lower().endswith((".py", ".md", ".json")):
            chunks = self.semantic_chunker.chunk(content, filepath)
        else:
            chunks = self._chunk_text(content)

        # Batch embed chunks
        results = self.batch_embedder.embed_texts_batch(chunks)

        # Build points
        points = []
        for idx, vector in results:
            pid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{filepath}::{idx}"))
            payload = {
                "path": filepath,
                "content": chunks[idx],
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "last_modified": mtime,
                "type": "code_file",
            }
            points.append(PointStruct(id=pid, vector=vector, payload=payload))

        if points:
            # Upsert points
            self.client.upsert(collection_name=self.collection_name, points=points)

            # Delete stale chunks if file shrunk
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(key="path", match=MatchValue(value=filepath)),
                        FieldCondition(key="chunk_index", range={"gte": len(chunks)}),
                    ]
                ),
            )
            return True

        return False

    @staticmethod
    def _chunk_text(text: str, size: int = 2000, overlap: int = 200) -> list:
        """Split text into overlapping chunks."""
        if not text:
            return []

        chunks = []
        pos = 0

        while pos < len(text):
            chunk = text[pos : pos + size]
            chunks.append(chunk)
            pos += size - overlap

        return chunks
