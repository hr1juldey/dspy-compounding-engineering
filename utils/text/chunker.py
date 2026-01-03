"""
Text chunking utility for style editing.

Extends SemanticChunker patterns for plain text and markdown documents.
"""

import os
import re

from agents.workflow.schema import ChunkWithContext


class TextChunker:
    """
    Intelligent text chunker with overlap for context preservation.

    Supports multiple chunking strategies:
    - Paragraph-based: Split on double newlines (\\n\\n)
    - Section-based: Split on markdown headers (# ## ###)
    - Sentence-based: Split on sentence boundaries (. ! ?)
    """

    def __init__(self):
        self.target_size = int(os.getenv("STYLE_EDIT_CHUNK_SIZE", "2000"))
        self.overlap = int(os.getenv("STYLE_EDIT_CHUNK_OVERLAP", "300"))

    def chunk_with_overlap(
        self, content: str, strategy: str = "paragraph"
    ) -> list[ChunkWithContext]:
        """
        Chunk content using specified strategy with overlap.

        Args:
            content: Full document text
            strategy: "paragraph", "section", or "sentence"

        Returns:
            List of ChunkWithContext objects with overlap
        """
        if strategy == "section":
            return self._chunk_by_sections(content)
        elif strategy == "sentence":
            return self._chunk_by_sentences(content)
        else:  # Default to paragraph
            return self._chunk_by_paragraphs(content)

    def _chunk_by_paragraphs(self, content: str) -> list[ChunkWithContext]:
        """
        Chunk by paragraphs (\\n\\n boundaries).

        Algorithm:
        1. Split on double newlines
        2. Build chunks up to target_size
        3. Add overlap from previous/next chunks
        4. Never split mid-paragraph
        """
        paragraphs = content.split("\n\n")
        raw_chunks = []
        current_chunk_paras = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            if current_size + para_size > self.target_size and current_chunk_paras:
                # Finalize current chunk
                raw_chunks.append("\n\n".join(current_chunk_paras))

                # Start new chunk with overlap (last 1-2 paragraphs)
                overlap_paras = self._get_overlap_paragraphs(current_chunk_paras)
                current_chunk_paras = overlap_paras + [para]
                current_size = (
                    sum(len(p) for p in current_chunk_paras) + (len(current_chunk_paras) - 1) * 2
                )
            else:
                current_chunk_paras.append(para)
                current_size += para_size + 2  # +2 for \n\n

        # Finalize last chunk
        if current_chunk_paras:
            raw_chunks.append("\n\n".join(current_chunk_paras))

        return self._build_chunk_objects(raw_chunks, content)

    def _chunk_by_sections(self, content: str) -> list[ChunkWithContext]:
        """
        Chunk by markdown sections (# headers).

        Splits on markdown headers while preserving section integrity.
        """
        # Find all header positions
        header_pattern = r"\n(#{1,6}\s+.+)"
        headers = list(re.finditer(header_pattern, content))

        if not headers:
            # No headers found, fall back to paragraph chunking
            return self._chunk_by_paragraphs(content)

        # Split into sections
        sections = []
        start_positions = [0] + [m.start() + 1 for m in headers]
        end_positions = [m.start() for m in headers] + [len(content)]

        for start, end in zip(start_positions, end_positions[1:], strict=False):
            section = content[start:end].strip()
            if section:
                sections.append(section)

        # Build chunks from sections
        raw_chunks = []
        current_chunk_sections = []
        current_size = 0

        for section in sections:
            section_size = len(section)

            if current_size + section_size > self.target_size and current_chunk_sections:
                raw_chunks.append("\n\n".join(current_chunk_sections))
                # Start new chunk with last section as overlap
                current_chunk_sections = [current_chunk_sections[-1], section]
                current_size = len(current_chunk_sections[-1]) + section_size + 2
            else:
                current_chunk_sections.append(section)
                current_size += section_size + 2

        # Finalize last chunk
        if current_chunk_sections:
            raw_chunks.append("\n\n".join(current_chunk_sections))

        return self._build_chunk_objects(raw_chunks, content)

    def _chunk_by_sentences(self, content: str) -> list[ChunkWithContext]:
        """
        Chunk by sentences (. ! ? boundaries).

        Fallback strategy for content without clear paragraph structure.
        """
        # Simple sentence splitting (can be improved with nltk if needed)
        sentence_pattern = r"([.!?]+\s+)"
        parts = re.split(sentence_pattern, content)

        # Reconstruct sentences
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            sentence = parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")
            if sentence.strip():
                sentences.append(sentence)

        # Build chunks from sentences
        raw_chunks = []
        current_chunk_sentences = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > self.target_size and current_chunk_sentences:
                raw_chunks.append("".join(current_chunk_sentences))
                # Overlap: last sentence
                current_chunk_sentences = [current_chunk_sentences[-1], sentence]
                current_size = len(current_chunk_sentences[-1]) + sentence_size
            else:
                current_chunk_sentences.append(sentence)
                current_size += sentence_size

        # Finalize last chunk
        if current_chunk_sentences:
            raw_chunks.append("".join(current_chunk_sentences))

        return self._build_chunk_objects(raw_chunks, content)

    def _get_overlap_paragraphs(self, paragraphs: list[str]) -> list[str]:
        """Get last N paragraphs that fit within overlap budget."""
        overlap_budget = self.overlap
        overlap_paras = []

        for para in reversed(paragraphs):
            test_join = "\n\n".join([para] + overlap_paras)
            if len(test_join) <= overlap_budget:
                overlap_paras.insert(0, para)
            else:
                break

        return overlap_paras

    def _build_chunk_objects(
        self, raw_chunks: list[str], original_content: str
    ) -> list[ChunkWithContext]:
        """Convert raw chunk strings to ChunkWithContext objects."""
        chunks = []
        total_chunks = len(raw_chunks)

        for i, chunk_text in enumerate(raw_chunks):
            # Find chunk position in original document
            start_char = original_content.find(chunk_text)
            end_char = start_char + len(chunk_text) if start_char >= 0 else len(chunk_text)

            # Determine position label
            if total_chunks == 1:
                position_label = "start"  # Single chunk document
            elif i == 0:
                position_label = "start"
            elif i == total_chunks - 1:
                position_label = "end"
            else:
                position_label = "middle"

            # Calculate overlap
            overlap_before = ""
            overlap_after = ""

            if i > 0:
                # Get overlap from previous chunk
                prev_chunk = raw_chunks[i - 1]
                overlap_before = (
                    prev_chunk[-self.overlap :] if len(prev_chunk) > self.overlap else prev_chunk
                )

            if i < total_chunks - 1:
                # Get overlap from next chunk
                next_chunk = raw_chunks[i + 1]
                overlap_after = next_chunk[: self.overlap]

            chunks.append(
                ChunkWithContext(
                    chunk_id=i,
                    content=chunk_text,
                    overlap_before=overlap_before,
                    overlap_after=overlap_after,
                    start_char=start_char if start_char >= 0 else 0,
                    end_char=end_char,
                    position_label=position_label,
                    total_chunks=total_chunks,
                )
            )

        return chunks
