"""
Memory Compressor Signature.

Single Responsibility: Compress agent memories.
"""

import dspy


class MemoryCompressorSignature(dspy.Signature):
    """Compress and deduplicate agent memories from mem0 storage.

    INPUTS:
    - agent_memories_json: JSON string containing raw agent memories from mem0.
      Format: [{"id": "...", "content": "...", "metadata": {...}, "timestamp": "..."}, ...]

    OUTPUT:
    You must return two fields:
    - compressed_memories_json: JSON string containing deduplicated and compressed memories.
      Format:
      [
        {
          "id": "compressed_id",
          "content": "Compressed content merging similar entries",
          "original_ids": ["mem1_id", "mem2_id", ...],
          "metadata": {...},
          "compression_note": "Merged 3 similar conversation entries"
        },
        ...
      ]
    - compression_stats: Dictionary with compression metrics:
      {
        "total_input": 150,
        "removed_duplicates": 30,
        "merged_similar": 20,
        "kept_unique": 100,
        "compression_ratio": "33% reduction"
      }

    TASK INSTRUCTIONS:
    - Deduplicate identical or near-identical conversation entries
    - Compress reasoning chains by extracting key conclusions
    - Merge similar patterns into consolidated entries
    - Preserve important metadata (timestamps, agent names, context)
    - Track compression metrics (removed, merged, kept)
    - Link compressed entries back to original IDs for traceability
    - Maintain semantic meaning while reducing redundancy
    - Focus on preserving unique insights and discarding noise
    """

    agent_memories_json: str = dspy.InputField(desc="Raw agent mem0 memories")

    compressed_memories_json: str = dspy.OutputField(desc="Deduplicated memories")
    compression_stats: dict = dspy.OutputField(desc="Metrics: removed, merged, kept")
