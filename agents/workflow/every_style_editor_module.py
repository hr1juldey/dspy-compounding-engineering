"""
EveryStyleEditorModule: Robust multi-step style editor with chunking.

Handles documents of any size by breaking them into manageable chunks and
processing sequentially to prevent Ollama overload.
"""

import json
import os

import dspy

from agents.workflow.every_style_editor import EveryStyleEditor
from agents.workflow.schema import ChunkEditResult
from agents.workflow.signatures import ChunkStyleEditor, ContentAnalyzer, EditAggregator
from utils.io.logger import logger
from utils.knowledge.module import KBPredict
from utils.text.chunker import TextChunker
from utils.token.counter import TokenCounter


class EveryStyleEditorModule(dspy.Module):
    """
    Robust style editor handling documents of any size via intelligent chunking.

    Architecture:
    1. Analyze content (determine if chunking needed based on token count)
    2. Chunk if needed (paragraph/section/sentence-based with overlap)
    3. Process chunks SEQUENTIALLY with consistency tracking
    4. Aggregate and deduplicate results

    Prevents Ollama overload by:
    - Keeping chunks < 60% of max_tokens (~9800 tokens default)
    - Sequential processing (no concurrent load)
    - Defensive error handling per chunk
    - Fallback to single-pass if all chunks fail

    Usage:
        editor = EveryStyleEditorModule()
        result = editor(content_to_review="Your long document here...")
        print(result.style_edits)
    """

    def __init__(self):
        super().__init__()

        # Stage 1: Analyzer (deterministic, no KB needed)
        self.analyzer = dspy.Predict(ContentAnalyzer)

        # Stage 2: Chunker (utility, no LLM)
        self.chunker = TextChunker()

        # Stage 3: Chunk processor (KB-wrapped for context)
        self.chunk_editor = KBPredict(
            ChunkStyleEditor, kb_tags=["style-editing", "every-style-guide"]
        )

        # Stage 4: Aggregator (KB-wrapped for deduplication patterns)
        self.aggregator = KBPredict(EditAggregator, kb_tags=["style-editing", "aggregation"])

        # Token counter for analysis
        self.token_counter = TokenCounter()

        # Get configuration
        self.chunk_threshold = float(os.getenv("STYLE_EDIT_CHUNK_THRESHOLD", "0.6"))
        self.max_tokens = int(os.getenv("DSPY_MAX_TOKENS", "16384"))

    def forward(self, content_to_review: str) -> dspy.Prediction:
        """
        Main entry point - maintains EveryStyleEditor interface.

        Args:
            content_to_review: Full document text to review

        Returns:
            dspy.Prediction with:
            - style_edits: str (formatted numbered list of edits)
        """
        # STAGE 1: Analyze content
        token_count = self.token_counter.count_tokens(content_to_review)
        safe_limit = int(self.max_tokens * self.chunk_threshold)

        logger.info(
            f"EveryStyleEditorModule: Analyzing document "
            f"({token_count} tokens, safe limit: {safe_limit})"
        )

        # Get preview for structure detection
        content_preview = content_to_review[:500]

        analysis = self.analyzer(content=content_preview, token_count=str(token_count))

        # Small document? Use single-pass (no chunking)
        if not analysis.analysis.needs_chunking:
            logger.info("EveryStyleEditorModule: Document fits in single pass, no chunking needed")
            return self._single_pass(content_to_review)

        logger.info(
            f"EveryStyleEditorModule: Using chunking strategy '{analysis.analysis.chunk_strategy}' "
            f"(estimated {analysis.analysis.estimated_chunks} chunks)"
        )

        # STAGE 2: Chunk the content
        chunks = self.chunker.chunk_with_overlap(
            content_to_review, strategy=analysis.analysis.chunk_strategy
        )

        logger.info(f"EveryStyleEditorModule: Created {len(chunks)} chunks")

        # STAGE 3: Process chunks SEQUENTIALLY
        chunk_results = []
        consistency_notes = ""
        failed_chunks = []

        for chunk in chunks:
            try:
                logger.debug(
                    f"EveryStyleEditorModule: Processing chunk {chunk.chunk_id + 1}/{len(chunks)}"
                )

                result = self.chunk_editor(
                    chunk_content=chunk.content,
                    chunk_position=chunk.position_label,
                    previous_edits_summary=consistency_notes,
                )

                # Add chunk_id to result
                chunk_edit_result = result.chunk_result
                chunk_edit_result.chunk_id = chunk.chunk_id

                chunk_results.append(chunk_edit_result)
                consistency_notes = chunk_edit_result.consistency_notes

            except Exception as e:
                logger.warning(f"EveryStyleEditorModule: Chunk {chunk.chunk_id} failed: {e}")
                failed_chunks.append(chunk.chunk_id)
                # Continue with next chunk (defensive programming)

        # All chunks failed? Fallback to single-pass
        if not chunk_results:
            logger.error(
                "EveryStyleEditorModule: All chunks failed, attempting single-pass fallback"
            )
            return self._single_pass(content_to_review)

        if failed_chunks:
            logger.warning(
                f"EveryStyleEditorModule: {len(failed_chunks)} chunks failed, "
                f"proceeding with {len(chunk_results)} successful chunks"
            )

        # STAGE 4: Aggregate results
        logger.info("EveryStyleEditorModule: Aggregating results from all chunks")

        try:
            # Serialize chunk results to JSON
            chunk_edits_json = json.dumps([r.dict() for r in chunk_results])

            # Get document preview for context
            doc_preview = content_to_review[:1000]

            aggregated = self.aggregator(
                chunk_edits=chunk_edits_json, original_document=doc_preview
            )

            logger.success(
                f"EveryStyleEditorModule: Complete. Stats: {aggregated.aggregated_result.stats}"
            )

            # Return in original EveryStyleEditor format
            return dspy.Prediction(style_edits=aggregated.aggregated_result.final_edits)

        except Exception as e:
            logger.error(f"EveryStyleEditorModule: Aggregation failed: {e}")
            # Fallback: Return raw chunk results
            return self._fallback_raw_results(chunk_results)

    def _single_pass(self, content: str) -> dspy.Prediction:
        """
        Fallback: Use original EveryStyleEditor for small documents.

        Args:
            content: Document text

        Returns:
            dspy.Prediction with style_edits
        """
        logger.info("EveryStyleEditorModule: Using single-pass EveryStyleEditor")
        editor = dspy.Predict(EveryStyleEditor)
        return editor(content_to_review=content)

    def _fallback_raw_results(self, chunk_results: list[ChunkEditResult]) -> dspy.Prediction:
        """
        Fallback: Format raw chunk results without aggregation.

        Args:
            chunk_results: List of ChunkEditResult objects

        Returns:
            dspy.Prediction with formatted edits
        """
        logger.warning("EveryStyleEditorModule: Using fallback raw results formatting")

        edits = []
        edit_number = 1

        for chunk_result in chunk_results:
            for edit in chunk_result.style_edits:
                edits.append(
                    f'{edit_number}. "{edit.original_quote}" -> "{edit.corrected_version}" '
                    f"(Rule: {edit.rule})"
                )
                edit_number += 1

        if not edits:
            formatted_edits = "No style edits found."
        else:
            formatted_edits = "\n".join(edits)

        return dspy.Prediction(style_edits=formatted_edits)
