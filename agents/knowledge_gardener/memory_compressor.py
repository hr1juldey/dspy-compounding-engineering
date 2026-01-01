"""
Memory Compressor Signature.

Single Responsibility: Compress agent memories.
"""

import dspy


class MemoryCompressorSignature(dspy.Signature):
    """
    Compress agent memories.

    Tasks:
    - Deduplicate conversation entries
    - Compress reasoning chains
    - Merge similar patterns
    """

    agent_memories_json: str = dspy.InputField(desc="Raw agent mem0 memories")

    compressed_memories_json: str = dspy.OutputField(desc="Deduplicated memories")
    compression_stats: dict = dspy.OutputField(desc="Metrics: removed, merged, kept")
