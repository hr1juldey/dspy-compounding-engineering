"""
Pattern Extractor Signature.

Single Responsibility: Extract patterns from consolidated KB.
"""

import dspy


class PatternExtractorSignature(dspy.Signature):
    """Extract recurring patterns and themes from consolidated knowledge base entries.

    INPUTS:
    - consolidated_knowledge_json: JSON string containing cleaned knowledge base entries
      from the KB consolidator. Format:
      [{"id": "...", "content": "...", "category": "...", "timestamp": "..."}, ...]

    OUTPUT:
    You must return two fields:
    - identified_patterns: JSON string containing extracted patterns. Format:
      {
        "patterns": [
          {
            "pattern_name": "Brief pattern name",
            "description": "Detailed description of the pattern",
            "frequency": "How often this appears (number or 'high/medium/low')",
            "related_entries": ["entry_id_1", "entry_id_2", ...],
            "examples": ["Example 1", "Example 2"]
          },
          ...
        ]
      }
    - pattern_summary: High-level summary describing the key patterns found
      (e.g., "Found 3 major patterns: authentication issues (12 entries),
      performance bottlenecks (8 entries), error handling gaps (5 entries)")

    TASK INSTRUCTIONS:
    - Analyze the consolidated knowledge entries to identify recurring themes
    - Group related insights under common pattern names
    - Count frequency/occurrences of each pattern
    - Link patterns back to specific KB entries using their IDs
    - Provide concrete examples for each pattern
    - Focus on actionable patterns (not trivial or one-off observations)
    - Rank patterns by importance/frequency
    """

    consolidated_knowledge_json: str = dspy.InputField(desc="Cleaned KB from consolidator")

    identified_patterns: str = dspy.OutputField(desc="Patterns in JSON format")
    pattern_summary: str = dspy.OutputField(desc="High-level pattern description")
