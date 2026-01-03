"""ChunkStyleEditor signature for reviewing text chunks."""

import dspy

from agents.workflow.schema import ChunkEditResult


class ChunkStyleEditor(dspy.Signature):
    """Review a CHUNK of text according to Every's house style guide.

    INPUTS:
    - chunk_content: The text chunk to review (not the full document)
    - chunk_position: Position in document - "start", "middle", or "end"
    - previous_edits_summary: Summary of style decisions from previous chunks
      (for consistency)

    OUTPUT:
    - chunk_result: ChunkEditResult object containing:
      * chunk_id: int - Chunk identifier (will be set by caller)
      * style_edits: list[StyleEdit] - List of edits for THIS CHUNK ONLY
      * consistency_notes: str - Style decisions to maintain in next chunk

    TASK INSTRUCTIONS:
    Review this chunk according to Every's house style guide:

    **Capitalization & Case:**
    - Headlines: Title case
    - Everything else: Sentence case
    - Job titles: Lowercase
    - Buttons: Sentence case

    **Grammar & Voice:**
    - Companies: Singular ("it")
    - Teams/people: Plural
    - Active voice over passive
    - Oxford commas: Yes
    - Commas between independent clauses only
    - Colons: Capitalize after only if independent clause follows

    **Word Choice:**
    - Remove: "actually", "very", "just"
    - Cut adverbs where possible
    - Direction: "earlier/later/previously" (not "above/below")
    - Quantity: "more/less/fewer" (not "over/under")
    - Avoid "We have"/"We get"
    - Avoid clichés and jargon
    - No "This" at sentence start without clear antecedent

    **Numbers & Quantities:**
    - Spell out 1-9 (except when starting with a year)
    - Numerals for 10+
    - Percentages: "7 percent" (spell out)
    - Large numbers: Use commas (1,000)
    - Money: "£1 billion"
    - "Two times faster" (not "2x", except "10x")

    **Formatting & Punctuation:**
    - Emphasis: Italics only (no bold/underline)
    - Ellipsis: No space after...
    - Em dashes: —like this— (no spaces, max 2 per paragraph)
    - Compound adjectives: Hyphenate (except -ly adverbs)
    - Titles (books/movies): Italicize
    - No slashes (use hyphens instead)
    - Punctuation: Outside parentheses (unless full sentence), inside quotes
    - Quotes: Single for quotes within quotes, comma before if introduced

    **Links & References:**
    - Hyperlinks: 2-4 descriptive words
    - Image credits: "Source: X/Name" or "Source: Website name"
    - Names: Full name on first mention, last name thereafter
    - People: Identify by company/title

    **Chunk-Specific Guidelines:**
    1. Focus ONLY on this chunk - don't suggest edits for text not in this chunk
    2. Review previous_edits_summary to maintain consistency with earlier chunks
    3. In consistency_notes, document any style decisions made (e.g., "Using
       'Jane Doe' on first mention, 'Doe' thereafter")
    4. If chunk_position is "start", this is the beginning of the document
    5. If chunk_position is "end", this is the final chunk
    6. For each violation, create a StyleEdit object with:
       - original_quote: The exact text needing correction
       - corrected_version: The fixed version
       - rule: The specific style guide rule being applied
       - position_in_doc: Character offset (approximate, relative to chunk start)
    """

    chunk_content: str = dspy.InputField(desc="Text chunk to review")
    chunk_position: str = dspy.InputField(desc="Position in document: 'start', 'middle', or 'end'")
    previous_edits_summary: str = dspy.InputField(
        desc="Style decisions from previous chunks (for consistency)", default=""
    )

    chunk_result: ChunkEditResult = dspy.OutputField(
        desc="Edit results for this chunk with consistency notes"
    )
