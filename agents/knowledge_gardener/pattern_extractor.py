"""
Pattern Extractor Signature.

Single Responsibility: Extract patterns from consolidated KB.
"""

import dspy


class PatternExtractorSignature(dspy.Signature):
    """
    Extract patterns from consolidated KB.

    Tasks:
    - Identify recurring themes
    - Find underlying patterns
    - Group related insights
    """

    consolidated_knowledge_json: str = dspy.InputField(desc="Cleaned KB from consolidator")

    identified_patterns: str = dspy.OutputField(desc="Patterns in JSON format")
    pattern_summary: str = dspy.OutputField(desc="High-level pattern description")
