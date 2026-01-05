"""
Async Qdrant client wrapper with sync compatibility.

Provides async operations for high-throughput scenarios while maintaining
backward compatibility with existing sync code.
"""

from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.async_qdrant_client import AsyncQdrantClient


class QdrantAsyncWrapper:
    """
    Dual-mode Qdrant client with sync and async interfaces.

    Maintains backward compatibility by defaulting to sync operations,
    while providing async methods for new high-performance code.

    Usage:
        # Sync mode (backward compatible, default)
        wrapper = QdrantAsyncWrapper(url, prefer_async=False)
        wrapper.upsert(...)  # Blocks

        # Async mode (new code)
        wrapper = QdrantAsyncWrapper(url, prefer_async=True)
        await wrapper.async_upsert(...)  # Non-blocking
    """

    def __init__(self, url: str, prefer_async: bool = False, timeout: int = 90):
        """
        Initialize dual-mode client.

        Args:
            url: Qdrant server URL
            prefer_async: Whether to use async client by default
            timeout: Request timeout in seconds
        """
        self.url = url
        self.timeout = timeout
        self.prefer_async = prefer_async

        # Always create sync client (backward compatibility)
        self.sync_client = QdrantClient(url=url, timeout=timeout)

        # Lazy-create async client (only if needed)
        self._async_client: Optional[AsyncQdrantClient] = None

    @property
    def async_client(self) -> AsyncQdrantClient:
        """Lazy-load async client on first use."""
        if self._async_client is None:
            self._async_client = AsyncQdrantClient(url=self.url, timeout=self.timeout)
        return self._async_client

    # Sync methods (backward compatible)
    def upsert(self, *args, **kwargs):
        """Sync upsert (backward compatible)."""
        return self.sync_client.upsert(*args, **kwargs)

    def query_points(self, *args, **kwargs):
        """Sync query (backward compatible)."""
        return self.sync_client.query_points(*args, **kwargs)

    def count(self, *args, **kwargs):
        """Sync count (backward compatible)."""
        return self.sync_client.count(*args, **kwargs)

    def scroll(self, *args, **kwargs):
        """Sync scroll (backward compatible)."""
        return self.sync_client.scroll(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Sync delete (backward compatible)."""
        return self.sync_client.delete(*args, **kwargs)

    def get_collections(self, *args, **kwargs):
        """Sync get collections (backward compatible)."""
        return self.sync_client.get_collections(*args, **kwargs)

    def create_collection(self, *args, **kwargs):
        """Sync create collection (backward compatible)."""
        return self.sync_client.create_collection(*args, **kwargs)

    def retrieve(self, *args, **kwargs):
        """Sync retrieve (backward compatible)."""
        return self.sync_client.retrieve(*args, **kwargs)

    def delete_collection(self, *args, **kwargs):
        """Sync delete collection (backward compatible)."""
        return self.sync_client.delete_collection(*args, **kwargs)

    # Async methods (new, high-performance)
    async def async_upsert(self, *args, **kwargs):
        """Async upsert (non-blocking)."""
        return await self.async_client.upsert(*args, **kwargs)

    async def async_query_points(self, *args, **kwargs):
        """Async query (non-blocking)."""
        return await self.async_client.query_points(*args, **kwargs)

    async def async_count(self, *args, **kwargs):
        """Async count (non-blocking)."""
        return await self.async_client.count(*args, **kwargs)

    async def async_scroll(self, *args, **kwargs):
        """Async scroll (non-blocking)."""
        return await self.async_client.scroll(*args, **kwargs)

    async def async_delete(self, *args, **kwargs):
        """Async delete (non-blocking)."""
        return await self.async_client.delete(*args, **kwargs)

    async def async_retrieve(self, *args, **kwargs):
        """Async retrieve (non-blocking)."""
        return await self.async_client.retrieve(*args, **kwargs)

    async def close_async(self):
        """Close async client."""
        if self._async_client:
            await self._async_client.close()

    def close(self):
        """Close sync client."""
        self.sync_client.close()
