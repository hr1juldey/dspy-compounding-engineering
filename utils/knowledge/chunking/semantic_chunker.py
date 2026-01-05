"""
Semantic chunker: AST does heavy lifting, LLM validates.

Architecture:
1. AST generates deterministic chunking strategy (fast, free)
2. Optional LLM validation/improvement (env var controlled)
3. CoT + ReAct only when enabled (default: AST-only)
"""

import os
from typing import cast

import dspy

from utils.io.logger import logger
from utils.knowledge.chunking.json_extractor import JSONExtractor
from utils.knowledge.chunking.markdown_extractor import MarkdownExtractor
from utils.knowledge.chunking.metrics import create_reward_function
from utils.knowledge.chunking.semantic_extractor import CodeStructure, PythonASTExtractor
from utils.knowledge.chunking.strategies import ChunkBoundary, ChunkingStrategy


class SemanticChunker:
    """
    Fast semantic chunking with optional LLM validation:
    1. AST Parser (fast, deterministic) - PRIMARY
    2. Optional LLM validator (CoT + ReAct) - SECONDARY
    """

    def __init__(self, target_size: int | None = None, min_overlap: int | None = None):
        self.target_size = target_size or int(os.getenv("SEMANTIC_CHUNK_SIZE", "2000"))
        self.min_overlap = min_overlap or int(os.getenv("SEMANTIC_CHUNK_OVERLAP", "200"))

        # File type extractors
        self.ast_extractor = PythonASTExtractor()
        self.markdown_extractor = MarkdownExtractor()
        self.json_extractor = JSONExtractor()

        # LLM validation (disabled by default for speed)
        self.use_llm_validation = (
            os.getenv("USE_LLM_CHUNKING_VALIDATION", "false").lower() == "true"
        )

        # Only load LLM modules if needed
        if self.use_llm_validation:
            import dspy

            from utils.knowledge.chunking.strategies import ChunkingStrategyGenerator

            self.strategy_generator = ChunkingStrategyGenerator()
            self.dspy = dspy

    def chunk(self, code: str, filepath: str = "") -> list[str]:
        """
        Main entry point: Chunk code semantically.

        Returns:
            List[str]: Chunked text segments
        """
        try:
            # Validate input
            if not code:
                logger.debug(f"Empty file: {filepath}")
                return []

            # Configurable minimum file size (default 10 chars)
            min_size = int(os.getenv("SEMANTIC_MIN_FILE_SIZE", "10"))
            if len(code.strip()) < min_size:
                logger.info(
                    f"File too small ({len(code)} chars < {min_size}): {filepath}, using fallback"
                )
                return self._fallback_chunking(code)

            # Configurable maximum file size (default 500KB)
            max_size = int(os.getenv("SEMANTIC_MAX_FILE_SIZE", "500000"))
            if len(code) > max_size:
                logger.warning(
                    f"File too large ({len(code)} chars > {max_size}): {filepath}, using fallback"
                )
                return self._fallback_chunking(code)

            # Determine file type (case-insensitive)
            file_ext = filepath.lower().split(".")[-1] if "." in filepath else ""

            if file_ext == "md":
                # Markdown: Use deterministic section-based chunking
                md_structure = self.markdown_extractor.extract(code, filepath)
                return self.markdown_extractor.chunk_by_sections(
                    code, md_structure, self.target_size
                )

            if file_ext == "json":
                # JSON: Use structure-based chunking
                json_structure = self.json_extractor.extract(code, filepath)
                return self.json_extractor.chunk_by_keys(code, json_structure, self.target_size)

            # Python: AST-based with optional LLM validation
            structure = self.ast_extractor.extract(code, filepath)

            # Step 1: AST creates deterministic strategy (FAST, always runs)
            ast_strategy = self._ast_chunking_strategy(code, structure)

            # Step 2: Score AST strategy
            lines = code.split("\n")
            reward_fn = create_reward_function(structure, lines)
            ast_score = reward_fn(
                args={"code": code, "ast_structure": structure},
                pred=type("obj", (object,), {"chunking_strategy": ast_strategy})(),
            )

            # Step 3: If AST is good, accept it. If bad, LLM redoes it.
            accept_threshold = float(os.getenv("SEMANTIC_ACCEPT_THRESHOLD", "0.75"))

            if ast_score >= accept_threshold:
                # AST is good enough, use it
                logger.info(
                    f"AST accepted (score={ast_score:.2f} >= {accept_threshold}): {filepath}"
                )
                return self._strategy_to_chunks(ast_strategy)

            # AST below threshold - try LLM if enabled
            logger.info(
                f"AST below threshold (score={ast_score:.2f} < {accept_threshold}): {filepath}"
            )

            if self.use_llm_validation:
                try:
                    logger.info(f"Attempting LLM-based chunking: {filepath}")
                    llm_strategy = self._llm_redo_strategy(code, structure)
                    logger.success(f"LLM chunking succeeded: {filepath}")
                    return self._strategy_to_chunks(llm_strategy)
                except Exception as llm_error:
                    logger.warning(
                        f"LLM chunking failed, falling back to AST: {filepath} - {llm_error}"
                    )
                    # Fall through to AST fallback

            # Fall back to AST (either LLM disabled or LLM failed)
            logger.info(f"Using AST chunking (fallback from threshold/LLM failure): {filepath}")
            return self._strategy_to_chunks(ast_strategy)

        except Exception as e:
            logger.error(
                f"Fatal error in semantic chunking for {filepath}: {type(e).__name__}: {e}"
            )
            logger.debug(f"Stack trace: {e}", exc_info=True)
            return self._fallback_chunking(code)

    def _ast_chunking_strategy(self, code: str, structure: CodeStructure) -> ChunkingStrategy:  # noqa: C901
        """
        AST creates deterministic chunking strategy (NO LLM calls).

        Returns:
            ChunkingStrategy with ChunkBoundary objects
        """
        lines = code.split("\n")
        chunks = []

        # Build list of code units with boundaries
        units = []

        # Add imports
        import_lines = [imp["line"] for imp in structure.imports]
        if import_lines:
            units.append(
                {
                    "type": "imports",
                    "start": min(import_lines),
                    "end": max(import_lines) + 1,
                    "name": "imports",
                }
            )

        # Add functions
        for func in structure.functions:
            units.append(
                {
                    "type": "function",
                    "start": func["start"],
                    "end": func["end"],
                    "name": func["name"],
                }
            )

        # Add classes
        for cls in structure.classes:
            units.append(
                {"type": "class", "start": cls["start"], "end": cls["end"], "name": cls["name"]}
            )

        # Sort by start line
        units.sort(key=lambda u: u["start"])

        # Build chunks respecting unit boundaries
        current_chunk_lines = []
        current_start_line = 1

        for unit in units:
            # Add filler lines
            if current_start_line < unit["start"]:
                filler = lines[current_start_line - 1 : unit["start"] - 1]
                current_chunk_lines.extend(filler)

            # Add unit lines
            unit_lines = lines[unit["start"] - 1 : unit["end"]]
            unit_size = sum(len(line) for line in unit_lines)
            current_size = sum(len(line) for line in current_chunk_lines)

            if current_chunk_lines and current_size + unit_size > self.target_size:
                # Finalize chunk
                chunk_text = "\n".join(current_chunk_lines)
                if chunk_text.strip():
                    chunks.append(
                        ChunkBoundary(
                            start_line=current_start_line,
                            end_line=unit["start"] - 1,
                            content=chunk_text,
                            semantic_label=f"code_unit_{len(chunks)}",
                            rationale="AST-based boundary",
                        )
                    )

                # Start new chunk
                current_chunk_lines = unit_lines
                current_start_line = unit["start"]
            else:
                current_chunk_lines.extend(unit_lines)

            current_start_line = unit["end"] + 1

        # Add remaining lines
        if current_start_line <= len(lines):
            remaining = lines[current_start_line - 1 :]
            current_chunk_lines.extend(remaining)

        # Finalize last chunk
        if current_chunk_lines:
            chunk_text = "\n".join(current_chunk_lines)
            if chunk_text.strip():
                chunks.append(
                    ChunkBoundary(
                        start_line=current_start_line if chunks else 1,
                        end_line=len(lines),
                        content=chunk_text,
                        semantic_label=f"code_unit_{len(chunks)}",
                        rationale="AST-based boundary",
                    )
                )

        # Fallback if no chunks created
        if not chunks:
            chunks.append(
                ChunkBoundary(
                    start_line=1,
                    end_line=len(lines),
                    content=code,
                    semantic_label="full_file",
                    rationale="No AST units found",
                )
            )

        return ChunkingStrategy(
            reasoning="AST-based deterministic chunking at function/class boundaries",
            chunks=chunks,
            confidence=0.85,
        )

    def _llm_redo_strategy(self, code: str, structure: CodeStructure) -> ChunkingStrategy:
        """
        LLM redoes chunking when AST fails (SLOW, only when enabled).

        Uses CoT + ReAct to generate better chunking strategy.
        """
        # Use ChainOfThought to generate new strategy from scratch
        result = cast(
            dspy.Prediction,
            self.strategy_generator(
                code=code,
                ast_structure=structure,
                target_chunk_size=self.target_size,
                min_overlap=self.min_overlap,
            ),
        )

        return result.chunking_strategy

    def _strategy_to_chunks(self, strategy: ChunkingStrategy) -> list[str]:
        """Convert ChunkingStrategy to List[str]"""
        return [chunk.content for chunk in strategy.chunks]

    def _fallback_chunking(self, code: str) -> list[str]:
        """Simple character-based chunking fallback"""
        chunks = []
        text_len = len(code)
        start = 0

        while start < text_len:
            end = start + self.target_size
            chunk = code[start:end]
            chunks.append(chunk)
            start += self.target_size - self.min_overlap

        return chunks
