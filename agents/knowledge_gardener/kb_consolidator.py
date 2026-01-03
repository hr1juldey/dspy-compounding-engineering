"""
KB Consolidator Signature.

Single Responsibility: Consolidate knowledge base learnings.
"""

import dspy


class KBConsolidatorSignature(dspy.Signature):
    """Consolidate and clean knowledge base entries by merging duplicates and removing noise.

    INPUTS:
    - current_knowledge_json: JSON string containing raw knowledge base entries.
      Format:
      [
        {
          "id": "kb_1",
          "content": "Learning or insight text",
          "source": "agent_name or commit_sha",
          "timestamp": "2024-01-03T10:30:00",
          "category": "optional category"
        },
        ...
      ]

    OUTPUT:
    You must return two fields:
    - consolidated_knowledge_json: JSON string containing cleaned and consolidated entries.
      Format:
      [
        {
          "id": "consolidated_1",
          "content": "Refined, consolidated content",
          "merged_from": ["kb_1", "kb_2", "kb_3"],
          "category": "Assigned category",
          "confidence": "high|medium|low",
          "actionable": true,
          "refinement_note": "Merged 3 duplicate entries about authentication"
        },
        ...
      ]
    - consolidation_summary: Summary of consolidation actions
      (e.g., "Processed 100 entries: merged 25 duplicates, removed 15 trivial items,
      categorized into 8 groups, kept 60 unique insights")

    TASK INSTRUCTIONS:
    - Merge duplicate or near-duplicate entries (similar content, same insight)
    - Remove noise: one-off observations, trivial items, non-actionable notes
    - Refine clarity: make entries concise, clear, and actionable
    - Categorize entries into logical groups (e.g., "authentication", "performance",
      "error handling", "architecture")
    - Track merged entry IDs for traceability
    - Assess confidence level based on source reliability and repetition
    - Mark entries as actionable (true) or informational (false)
    - Focus on preserving high-value insights and discarding low-value noise
    """

    current_knowledge_json: str = dspy.InputField(desc="Raw KB entries (JSON)")

    consolidated_knowledge_json: str = dspy.OutputField(desc="Cleaned KB entries")
    consolidation_summary: str = dspy.OutputField(desc="What was changed")
