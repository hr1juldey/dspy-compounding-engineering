"""
Semantic chunker orchestrator using AST → BestOfN(CoT) → ReAct → Refine.

Coordinates intelligent code chunking that respects function/class boundaries.
"""

import os

import dspy

from utils.io.logger import logger
from utils.knowledge.chunking_metrics import create_reward_function
from utils.knowledge.chunking_strategies import ChunkingStrategyGenerator
from utils.knowledge.json_extractor import JSONExtractor
from utils.knowledge.markdown_extractor import MarkdownExtractor
from utils.knowledge.semantic_extractor import CodeStructure, PythonASTExtractor


class SemanticChunker:
    """
    Orchestrates semantic chunking using:
    1. AST Parser (fast, deterministic)
    2. BestOfN(ChainOfThought, N=3) (generate strategies)
    3. ReAct (evaluate and decide)
    4. Refine (conditional improvement)
    """

    def __init__(self, target_size: int | None = None, min_overlap: int | None = None):
        self.target_size = target_size or int(os.getenv("SEMANTIC_CHUNK_SIZE", "2000"))
        self.min_overlap = min_overlap or int(os.getenv("SEMANTIC_CHUNK_OVERLAP", "200"))

        # File type extractors
        self.ast_extractor = PythonASTExtractor()
        self.markdown_extractor = MarkdownExtractor()
        self.json_extractor = JSONExtractor()

        self.strategy_generator = ChunkingStrategyGenerator()

        # Decision thresholds
        self.EXCELLENT_THRESHOLD = 0.90
        self.ACCEPTABLE_THRESHOLD = 0.75
        self.REFINEMENT_THRESHOLD = 0.60

    def chunk(self, code: str, filepath: str = "") -> list[str]:
        """
        Main entry point: Chunk code semantically.

        Returns:
            List[str]: Chunked text segments
        """
        try:
            # Precondition: Skip empty or very small files
            if not code or len(code.strip()) < 100:
                logger.info(
                    f"Skipping semantic chunking for small file ({len(code)} chars)",
                    to_cli=True,
                )
                return self._fallback_chunking(code) if code else []

            # Precondition: Skip very large files (> 50KB) to avoid expensive LLM calls
            if len(code) > 50000:
                logger.warning(f"File too large ({len(code)} chars), using fallback chunking")
                return self._fallback_chunking(code)

            # Step 1: Determine file type and extract structure (case-insensitive)
            file_ext = filepath.lower().split(".")[-1] if "." in filepath else ""

            if file_ext == "md":
                # Markdown: Use deterministic section-based chunking
                logger.info(f"Using Markdown chunking for {filepath}", to_cli=True)
                md_structure = self.markdown_extractor.extract(code, filepath)
                return self.markdown_extractor.chunk_by_sections(
                    code, md_structure, self.target_size
                )

            if file_ext == "json":
                # JSON: Use structure-based chunking
                logger.info(f"Using JSON chunking for {filepath}", to_cli=True)
                json_structure = self.json_extractor.extract(code, filepath)
                return self.json_extractor.chunk_by_keys(code, json_structure, self.target_size)

            # Python: Use AST + LLM-based semantic chunking
            structure = self.ast_extractor.extract(code, filepath)

            # Step 2: Generate 3 strategies using BestOfN(CoT)
            best_strategy, best_score = self._generate_best_strategy(code, structure)

            # Step 3: ReAct evaluation and decision
            if best_score >= self.EXCELLENT_THRESHOLD:
                logger.info(f"Excellent chunking (score={best_score:.2f}), accepting", to_cli=True)
                return self._strategy_to_chunks(best_strategy)

            if best_score >= self.ACCEPTABLE_THRESHOLD:
                logger.info(f"Acceptable chunking (score={best_score:.2f}), accepting", to_cli=True)
                return self._strategy_to_chunks(best_strategy)

            if best_score >= self.REFINEMENT_THRESHOLD:
                logger.info(
                    f"Mediocre chunking (score={best_score:.2f}), attempting refinement",
                    to_cli=True,
                )
                # Step 4: Refine (conditional)
                refined_strategy = self._refine_strategy(best_strategy, structure, code)
                return self._strategy_to_chunks(refined_strategy)

            logger.warning(
                f"Semantic chunking failed (score={best_score:.2f}), using fallback",
                to_cli=True,
            )
            return self._fallback_chunking(code)

        except Exception as e:
            logger.error(f"Semantic chunking error: {e}", detail=str(e))
            return self._fallback_chunking(code)

    def _generate_best_strategy(self, code: str, structure: CodeStructure) -> tuple:
        """
        Generate 3 chunking strategies using BestOfN(ChainOfThought).

        Returns:
            (best_strategy, best_score)
        """
        lines = code.split("\n")
        reward_fn = create_reward_function(structure, lines)

        # Wrap generator in BestOfN
        best_of_n = dspy.BestOfN(
            module=self.strategy_generator,
            N=3,
            reward_fn=reward_fn,
            threshold=self.EXCELLENT_THRESHOLD,
        )

        # Generate and score strategies
        result = best_of_n(
            code=code,
            ast_structure=structure,
            target_chunk_size=self.target_size,
            min_overlap=self.min_overlap,
        )

        # Calculate final score
        score = reward_fn(args={"code": code, "ast_structure": structure}, pred=result)

        return result.chunking_strategy, score

    def _refine_strategy(self, strategy, structure: CodeStructure, code: str):
        """
        Use Refine module to improve strategy based on violations.

        Returns:
            Refined strategy
        """
        lines = code.split("\n")
        reward_fn = create_reward_function(structure, lines)

        # Create Refine module
        refine = dspy.Refine(
            module=self.strategy_generator,
            N=3,
            reward_fn=reward_fn,
            threshold=self.ACCEPTABLE_THRESHOLD,
        )

        result = refine(
            code=code,
            ast_structure=structure,
            target_chunk_size=self.target_size,
            min_overlap=self.min_overlap,
        )

        return result.chunking_strategy

    def _strategy_to_chunks(self, strategy) -> list[str]:
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
