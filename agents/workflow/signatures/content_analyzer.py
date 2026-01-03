"""ContentAnalyzer signature for determining chunking strategy."""

import dspy

from agents.workflow.schema import ContentAnalysisResult


class ContentAnalyzer(dspy.Signature):
    """Analyze document structure to determine if chunking is needed.

    INPUTS:
    - content: Preview of document text (first ~500 chars for structure detection)
    - token_count: Approximate token count of full document (as string)

    OUTPUT:
    - analysis: ContentAnalysisResult object containing:
      * needs_chunking: bool - True if document exceeds safe token limit
      * chunk_strategy: str - "paragraph", "section", "sentence", or "none"
      * estimated_chunks: int - Predicted number of chunks needed
      * reasoning: str - Explanation for the chosen strategy

    TASK INSTRUCTIONS:
    Analyze the document preview to determine optimal chunking approach:

    1. **Check Token Count**:
       - Safe limit is typically 60% of max_tokens (~9800 tokens for 16384 limit)
       - If token_count < safe limit: needs_chunking = False, strategy = "none"
       - If token_count >= safe limit: needs_chunking = True, choose strategy

    2. **Detect Content Structure** (from preview):
       - Markdown headers ("\\n## " or "\\n# "): Use "section" strategy
       - Multiple paragraphs ("\\n\\n" appears 3+ times): Use "paragraph" strategy
       - Dense text (few paragraph breaks): Use "sentence" strategy

    3. **Estimate Chunks**:
       - Calculate: total_chars / target_chunk_size
       - Target chunk size is typically 2000 characters
       - Round up to nearest integer

    4. **Provide Clear Reasoning**:
       - Explain token count decision
       - Justify chosen strategy based on document structure
       - Note estimated number of chunks

    Example outputs:
    - Small doc: needs_chunking=False, strategy="none", reasoning="Document is
      only 1500 tokens, well within safe limit"
    - Large markdown: needs_chunking=True, strategy="section",
      reasoning="10,500 tokens exceeds limit, markdown headers detected"
    """

    content: str = dspy.InputField(
        desc="Document preview (first 500 chars) for structure detection"
    )
    token_count: str = dspy.InputField(desc="Total token count of full document")

    analysis: ContentAnalysisResult = dspy.OutputField(
        desc="Analysis result with chunking decision and strategy"
    )
