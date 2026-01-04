"""
Compatibility module - re-exports from new location.

CodebaseIndexer moved to utils.knowledge.indexing.indexer
This module provides backward compatibility for existing imports.
"""

from utils.knowledge.indexing.indexer import CodebaseIndexer

__all__ = ["CodebaseIndexer"]
