"""EditAggregator signature for combining and deduplicating style edits."""

import dspy

from agents.workflow.schema import AggregatedEditResult


class EditAggregator(dspy.Signature):
    """Aggregate and deduplicate style edits from multiple text chunks.

    INPUTS:
    - chunk_edits: JSON string containing list of ChunkEditResult objects from all chunks
    - original_document: Preview of original document (first ~1000 chars for context)

    OUTPUT:
    - aggregated_result: AggregatedEditResult object containing:
      * final_edits: str - Formatted string of all edits (numbered list, ready to display)
      * stats: dict - Statistics with keys: total_chunks, total_edits, duplicates_removed
      * coverage: str - Description of which document portions were edited

    TASK INSTRUCTIONS:
    Combine edits from all chunks into a single, deduplicated list:

    1. **Parse chunk_edits JSON**:
       - Each chunk has: chunk_id, style_edits list, consistency_notes
       - Each style_edit has: original_quote, corrected_version, rule, position_in_doc

    2. **Deduplicate Edits**:
       - Remove duplicates where original_quote is identical
       - If multiple edits for same quote, keep the first occurrence
       - Handle chunk boundary overlaps:
         * If edit appears in both chunk N and N+1 (overlap zone), keep only once
         * Compare by original_quote and rule applied

    3. **Renumber Sequentially**:
       - Assign sequential numbers starting from 1
       - Format each edit as:
         N. "original quote" -> "corrected version" (Rule: explanation)

    4. **Format final_edits String**:
       - Create numbered list matching EveryStyleEditor output format
       - Example:
         1. "The company are launching" -> "The company is launching"
            (Rule: Companies are singular)
         2. "Click here for more" -> "Learn more about the API"
            (Rule: Hyperlinks should be 2-4 descriptive words)

    5. **Calculate Statistics**:
       - total_chunks: Count of chunks processed
       - total_edits: Count of unique edits after deduplication
       - duplicates_removed: Count of duplicate edits removed

    6. **Describe Coverage**:
       - Brief description of document portions edited
       - Example: "Edits span entire document (chunks 1-5)"
       - Or: "Primarily first and last sections (chunks 1-2, 8-10)"

    **Quality Guidelines**:
    - Preserve original rule explanations
    - Maintain author's voice in corrected versions
    - Don't create new edits - only aggregate existing ones
    - If zero edits across all chunks, return empty final_edits with explanation
    """

    chunk_edits: str = dspy.InputField(desc="JSON array of ChunkEditResult objects from all chunks")
    original_document: str = dspy.InputField(
        desc="Document preview for context (first 1000 chars)", default=""
    )

    aggregated_result: AggregatedEditResult = dspy.OutputField(
        desc="Final aggregated and deduplicated edit results"
    )
