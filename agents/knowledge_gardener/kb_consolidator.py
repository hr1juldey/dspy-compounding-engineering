"""
KB Consolidator Signature.

Single Responsibility: Consolidate knowledge base learnings.
"""

import dspy


class KBConsolidatorSignature(dspy.Signature):
    """
    Consolidate KB learnings.

    Tasks:
    - Merge duplicate entries
    - Remove noise (one-off, trivial items)
    - Refine clarity (concise, actionable)
    - Categorize entries
    """

    current_knowledge_json: str = dspy.InputField(desc="Raw KB entries (JSON)")

    consolidated_knowledge_json: str = dspy.OutputField(desc="Cleaned KB entries")
    consolidation_summary: str = dspy.OutputField(desc="What was changed")
