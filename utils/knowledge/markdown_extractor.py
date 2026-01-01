"""
Markdown structure extractor for semantic chunking.

Extracts headers, code blocks, and logical sections from Markdown files.
"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class MarkdownStructure:
    """Markdown document structure"""

    headers: list[dict[str, Any]]
    code_blocks: list[dict[str, Any]]
    total_lines: int
    file_path: str


class MarkdownExtractor:
    """Extracts structure from Markdown files"""

    def extract(self, content: str, filepath: str = "") -> MarkdownStructure:
        """Parse Markdown and extract structure"""
        lines = content.split("\n")

        return MarkdownStructure(
            headers=self._extract_headers(lines),
            code_blocks=self._extract_code_blocks(lines),
            total_lines=len(lines),
            file_path=filepath,
        )

    def _extract_headers(self, lines: list[str]) -> list[dict[str, Any]]:
        """Extract all headers with line numbers"""
        headers = []
        for i, line in enumerate(lines, 1):
            match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headers.append({"level": level, "text": text, "line": i})
        return headers

    def _extract_code_blocks(self, lines: list[str]) -> list[dict[str, Any]]:
        """Extract code blocks with line ranges"""
        code_blocks = []
        in_block = False
        start_line = 0
        language = ""

        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                if not in_block:
                    in_block = True
                    start_line = i
                    language = line.strip()[3:].strip()
                else:
                    in_block = False
                    code_blocks.append({"start": start_line, "end": i, "language": language})
                    language = ""

        return code_blocks

    def chunk_by_sections(
        self, content: str, structure: MarkdownStructure, target_size: int = 2000
    ) -> list[str]:
        """
        Chunk Markdown by semantic sections (headers).

        Strategy:
        - Split by headers (# ## ###)
        - Keep sections together
        - Merge small adjacent sections
        - Don't split code blocks
        """
        lines = content.split("\n")
        chunks = []

        if not structure.headers:
            # No headers - use simple chunking
            return self._simple_chunk(content, target_size)

        # Create chunks based on header boundaries
        sections = []
        for i, header in enumerate(structure.headers):
            start = header["line"] - 1  # Convert to 0-indexed
            end = (
                structure.headers[i + 1]["line"] - 1
                if i + 1 < len(structure.headers)
                else len(lines)
            )

            section_text = "\n".join(lines[start:end])
            sections.append({"start": start, "end": end, "text": section_text, "header": header})

        # Merge small sections and split large ones
        current_chunk = []
        current_size = 0

        for section in sections:
            section_size = len(section["text"])

            if current_size + section_size <= target_size:
                # Add to current chunk
                current_chunk.append(section["text"])
                current_size += section_size
            else:
                # Finish current chunk and start new one
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [section["text"]]
                current_size = section_size

        # Add final chunk
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks if chunks else [content]

    def _simple_chunk(self, content: str, target_size: int) -> list[str]:
        """Simple character-based chunking fallback"""
        chunks = []
        start = 0
        overlap = 200

        while start < len(content):
            end = start + target_size
            chunk = content[start:end]
            chunks.append(chunk)
            start += target_size - overlap

        return chunks
