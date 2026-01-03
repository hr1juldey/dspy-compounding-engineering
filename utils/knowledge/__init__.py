"""Knowledge Base module - learning storage, retrieval, and indexing."""

from utils.knowledge.codebase_search import CodebaseSearch
from utils.knowledge.compression import LLMKBCompressor
from utils.knowledge.core import KnowledgeBase
from utils.knowledge.docs import KnowledgeDocumentation
from utils.knowledge.embeddings_dspy import EmbeddingProvider
from utils.knowledge.extractor import (
    codify_batch_triage_session,
    codify_learning,
    codify_review_findings,
    codify_triage_decision,
    codify_work_outcome,
)
from utils.knowledge.file_indexer import FileIndexer
from utils.knowledge.indexer import CodebaseIndexer
from utils.knowledge.indexer_metadata import IndexerMetadata
from utils.knowledge.learning_formatter import LearningFormatter
from utils.knowledge.learning_indexer import LearningIndexer
from utils.knowledge.learning_persistence import LearningPersistence
from utils.knowledge.learning_retrieval import LearningRetrieval
from utils.knowledge.module import KBPredict

__all__ = [
    "LLMKBCompressor",
    "KnowledgeBase",
    "KnowledgeDocumentation",
    "EmbeddingProvider",
    "codify_batch_triage_session",
    "codify_learning",
    "codify_review_findings",
    "codify_triage_decision",
    "codify_work_outcome",
    "CodebaseIndexer",
    "KBPredict",
    # New service modules (internal APIs)
    "CodebaseSearch",
    "FileIndexer",
    "IndexerMetadata",
    "LearningFormatter",
    "LearningIndexer",
    "LearningPersistence",
    "LearningRetrieval",
]
