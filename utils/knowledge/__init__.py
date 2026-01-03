"""Knowledge Base module - learning storage, retrieval, and indexing."""

# Core components (at root level)
# Re-export from subdirectories (backward compatible)
from utils.knowledge.chunking.semantic_chunker import SemanticChunker
from utils.knowledge.core import KnowledgeBase
from utils.knowledge.embeddings.provider import EmbeddingProvider
from utils.knowledge.indexing.codebase_search import CodebaseSearch
from utils.knowledge.indexing.file_indexer import FileIndexer
from utils.knowledge.indexing.indexer import CodebaseIndexer
from utils.knowledge.indexing.indexer_metadata import IndexerMetadata
from utils.knowledge.learning.compression import LLMKBCompressor
from utils.knowledge.learning.docs import KnowledgeDocumentation
from utils.knowledge.learning.extractor import (
    codify_batch_triage_session,
    codify_learning,
    codify_review_findings,
    codify_triage_decision,
    codify_work_outcome,
)
from utils.knowledge.learning.learning_formatter import LearningFormatter
from utils.knowledge.learning.learning_indexer import LearningIndexer
from utils.knowledge.learning.learning_persistence import LearningPersistence
from utils.knowledge.learning.learning_retrieval import LearningRetrieval
from utils.knowledge.module import KBPredict

__all__ = [
    # Core
    "KnowledgeBase",
    "KBPredict",
    # Public API (backward compatible)
    "CodebaseIndexer",
    "CodebaseSearch",
    "EmbeddingProvider",
    "FileIndexer",
    "IndexerMetadata",
    "KnowledgeDocumentation",
    "LLMKBCompressor",
    "LearningFormatter",
    "LearningIndexer",
    "LearningPersistence",
    "LearningRetrieval",
    "SemanticChunker",
    "codify_batch_triage_session",
    "codify_learning",
    "codify_review_findings",
    "codify_triage_decision",
    "codify_work_outcome",
]
