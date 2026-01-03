"""
Pydantic models for multi-step style editing.

Models used by EveryStyleEditorModule for chunking, processing, and aggregation.
"""

from pydantic import BaseModel, Field


class ChunkWithContext(BaseModel):
    """Represents a text chunk with overlap context for continuity."""

    chunk_id: int = Field(description="0-indexed chunk identifier")
    content: str = Field(description="The chunk text content")
    overlap_before: str = Field(default="", description="Trailing context from previous chunk")
    overlap_after: str = Field(default="", description="Leading context from next chunk")
    start_char: int = Field(description="Starting character position in original document")
    end_char: int = Field(description="Ending character position in original document")
    position_label: str = Field(description="Position in document: 'start', 'middle', or 'end'")
    total_chunks: int = Field(description="Total number of chunks in document")


class ContentAnalysisResult(BaseModel):
    """Result from ContentAnalyzer signature."""

    needs_chunking: bool = Field(description="Whether document requires chunking")
    chunk_strategy: str = Field(
        description="Chunking strategy: 'paragraph', 'section', 'sentence', or 'none'"
    )
    estimated_chunks: int = Field(description="Estimated number of chunks needed")
    reasoning: str = Field(description="Explanation for chunking decision")


class StyleEdit(BaseModel):
    """Single style edit suggestion."""

    original_quote: str = Field(description="Original text that needs editing")
    corrected_version: str = Field(description="Corrected text")
    rule: str = Field(description="Every style guide rule being applied")
    position_in_doc: int = Field(description="Character offset in original document", default=0)


class ChunkEditResult(BaseModel):
    """Result from ChunkStyleEditor signature."""

    chunk_id: int = Field(description="Chunk identifier")
    style_edits: list[StyleEdit] = Field(
        default_factory=list, description="List of edits for this chunk"
    )
    consistency_notes: str = Field(
        default="",
        description="Style decisions to maintain consistency in subsequent chunks",
    )


class AggregatedEditResult(BaseModel):
    """Final aggregated and deduplicated result."""

    final_edits: str = Field(
        description="Formatted string of all edits (backward compatible format)"
    )
    stats: dict[str, int] = Field(
        default_factory=dict,
        description="Statistics: total_chunks, total_edits, duplicates_removed",
    )
    coverage: str = Field(
        default="", description="Description of which document portions were edited"
    )
