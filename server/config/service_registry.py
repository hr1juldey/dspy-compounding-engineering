"""Service registry singleton for runtime status tracking."""

import os
import threading
from typing import Any


class ServiceRegistry:
    """Registry for runtime service status. Singleton pattern."""

    _instance = None
    _lock = threading.RLock()

    # Declare instance attributes for type checker
    _status: dict[str, Any]
    lock: threading.RLock

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._status = {
                        "qdrant_available": None,
                        "openai_key_available": None,
                        "embeddings_ready": None,
                        "learnings_ensured": False,
                        "codebase_ensured": False,
                        "kb_cache": None,
                    }
                    instance.lock = threading.RLock()
                    cls._instance = instance
                    # Configure logging on init
                    from server.config.logging import configure_logging

                    configure_logging()
        return cls._instance

    @property
    def status(self):
        with self.lock:
            return self._status.copy()

    def check_qdrant(self, force: bool = False) -> bool:
        """Check if Qdrant is available."""
        with self.lock:
            if self._status["qdrant_available"] is not None and not force:
                return self._status["qdrant_available"]
            try:
                from qdrant_client import QdrantClient

                url = os.getenv("QDRANT_URL", "http://localhost:6333")
                client = QdrantClient(url=url, timeout=90)
                client.get_collections()
                self._status["qdrant_available"] = True
            except Exception:
                from utils.io.logger import logger

                self._status["qdrant_available"] = False
                if not os.getenv("COMPOUNDING_QUIET"):
                    logger.warning("Qdrant unavailable. Falling back to keyword search.")
            return self._status["qdrant_available"]

    def get_qdrant_client(self):
        """Returns Qdrant client if available, else None."""
        with self.lock:
            if not self.check_qdrant():
                return None
            from qdrant_client import QdrantClient

            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            return QdrantClient(url=qdrant_url, timeout=90)

    def get_qdrant_client_required(self):
        """Returns Qdrant client or raises RuntimeError if unavailable."""
        client = self.get_qdrant_client()
        if client is None:
            raise RuntimeError("Qdrant client not initialized - ensure Qdrant is running")
        return client

    def check_api_keys(self, force: bool = False) -> bool:
        """Check if required API keys are available."""
        with self.lock:
            if self._status["openai_key_available"] is not None and not force:
                return self._status["openai_key_available"]
        from server.config.lm_provider import resolve_embedding_config
        from utils.io.logger import logger

        lm_p = os.getenv("DSPY_LM_PROVIDER", "openai")
        lm_ok = self._check_provider_key(lm_p)
        emb_p, _, _ = resolve_embedding_config()
        emb_ok = self._check_provider_key(emb_p) or emb_p == "fastembed"
        if not lm_ok:
            logger.warning(f"No API key for LM provider '{lm_p}'.")
        if not emb_ok:
            logger.warning(f"No API key for embedding provider '{emb_p}'.")
        with self.lock:
            self._status["openai_key_available"] = lm_ok and emb_ok
        return self._status["openai_key_available"]

    def _check_provider_key(self, provider: str) -> bool:
        """Check if key exists for given provider."""
        key_map = {
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "ollama": "True",
        }
        env_var = key_map.get(provider)
        if env_var is None:
            return False  # Unknown provider, no key available
        return bool(os.getenv(env_var)) if env_var != "True" else True

    def get_kb(self, force: bool = False):
        """Get or initialize KnowledgeBase instance."""
        with self.lock:
            if self._status["kb_cache"] is None or force:
                from utils.knowledge import KnowledgeBase

                self._status["kb_cache"] = KnowledgeBase()
            return self._status["kb_cache"]

    def get_mem0_memory(self, agent_name: str):
        """Get mem0 Memory instance for agent."""
        from mem0 import Memory

        from utils.memory.config import get_mem0_config

        return Memory.from_config(get_mem0_config(agent_name))


registry = ServiceRegistry()
