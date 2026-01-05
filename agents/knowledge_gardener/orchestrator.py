"""
Knowledge Gardener Orchestrator.

Multi-step ReAct orchestrator following workflow/plan.py pattern.
Chains 4 signatures together with KBPredict for context injection.
"""

from typing import cast

import dspy

from agents.knowledge_gardener.commit_indexer import CommitIndexerSignature
from agents.knowledge_gardener.kb_consolidator import KBConsolidatorSignature
from agents.knowledge_gardener.memory_compressor import MemoryCompressorSignature
from agents.knowledge_gardener.pattern_extractor import PatternExtractorSignature
from agents.knowledge_gardener.schema import KnowledgeGardenerResult
from utils.knowledge.module import KBPredict


class KnowledgeGardenerOrchestrator(dspy.Module):
    """
    Multi-step ReAct orchestrator.

    Chains 4 signatures together following workflow/plan.py pattern.
    Each signature wrapped with KBPredict for context injection.
    """

    def __init__(self):
        super().__init__()

        # Wrap each signature with KBPredict for knowledge injection
        self.consolidator = KBPredict(
            KBConsolidatorSignature, kb_tags=["knowledge-gardening", "consolidation"]
        )

        self.pattern_extractor = KBPredict(
            PatternExtractorSignature, kb_tags=["knowledge-gardening", "patterns"]
        )

        self.memory_compressor = KBPredict(
            MemoryCompressorSignature, kb_tags=["memory-compression"]
        )

        self.commit_indexer = KBPredict(CommitIndexerSignature, kb_tags=["git-indexing"])

    def forward(
        self,
        current_knowledge_json: str,
        agent_memories_json: str = "{}",
        recent_commits_json: str = "[]",
    ) -> KnowledgeGardenerResult:
        """
        Multi-step orchestration (following workflow/plan.py pattern).

        Step 1: Consolidate KB
        Step 2: Extract patterns from consolidated KB
        Step 3: Compress agent memories (parallel to Step 2)
        Step 4: Index git commits (parallel to Step 2)
        Step 5: Combine all results
        """

        # Step 1: Consolidate KB learnings
        kb_result = cast(
            dspy.Prediction, self.consolidator(current_knowledge_json=current_knowledge_json)
        )

        # Step 2: Extract patterns from consolidated KB
        pattern_result = cast(
            dspy.Prediction,
            self.pattern_extractor(
                consolidated_knowledge_json=kb_result.consolidated_knowledge_json
            ),
        )

        # Step 3: Compress memories (independent of KB consolidation)
        memory_result = cast(
            dspy.Prediction, self.memory_compressor(agent_memories_json=agent_memories_json)
        )

        # Step 4: Index commits (independent of KB consolidation)
        commit_result = cast(
            dspy.Prediction, self.commit_indexer(recent_commits_json=recent_commits_json)
        )

        # Step 5: Combine all results
        return KnowledgeGardenerResult(
            compressed_knowledge_json=kb_result.consolidated_knowledge_json,
            identified_patterns=pattern_result.identified_patterns,
            pattern_summary=pattern_result.pattern_summary,
            compressed_memories_json=memory_result.compressed_memories_json,
            compression_stats=memory_result.compression_stats,
            shared_commit_memory_json=commit_result.shared_commit_memory_json,
            indexing_summary=commit_result.indexing_summary,
        )
