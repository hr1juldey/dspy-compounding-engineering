"""Warmup utility using DSPy signatures with centrally configured LM/embedder."""

import math
import time
from datetime import datetime
from typing import Tuple

import dspy
from pydantic import BaseModel, Field

from server.config.service_registry import registry
from utils.io.logger import logger


class TimeFormatOutput(BaseModel):
    """Output format for time conversion."""

    formatted_time: str = Field(description="Time in AM/PM format (e.g. 3:45 PM)")


class TimeFormatter(dspy.Signature):
    """Convert 24-hour time to 12-hour AM/PM format."""

    current_time: str = dspy.InputField(description="Current time in 24-hour format (HH:MM)")
    time_output: TimeFormatOutput = dspy.OutputField(description="Time formatted as 12-hour AM/PM")


class SentencePairOutput(BaseModel):
    """Output format for sentence pair generation."""

    present_tense: str = Field(description="Sentence about the time in present tense")
    future_tense: str = Field(description="Sentence about the time in future tense")


class SentencePairGenerator(dspy.Signature):
    """Generate two sentences about the current time - one present, one future tense."""

    current_time: str = dspy.InputField(description="Current time in AM/PM format")
    sentences: SentencePairOutput = dspy.OutputField(description="Two sentences about the time")


class WarmupTest:
    """Test LLM and embedder using DSPy signatures (centrally configured instances)."""

    def warmup_llm(self) -> Tuple[bool, str]:
        """Test LLM using DSPy ChainOfThought signature."""
        try:
            logger.info("Warming up LLM with DSPy ChainOfThought...")
            logger.info("Note: First call may take 60-120s to load model...")
            start_time = time.time()

            # Check DSPy LM is configured
            if not hasattr(dspy.settings, "lm") or dspy.settings.lm is None:
                raise RuntimeError("DSPy LM not configured. Call configure_dspy() first")

            # Use ChainOfThought with time formatting task
            time_formatter = dspy.ChainOfThought(TimeFormatter)

            # Get current time in 24-hour format
            now = datetime.now()
            current_time_24h = now.strftime("%H:%M")

            # Ask LLM to convert to AM/PM format
            result = time_formatter(current_time=current_time_24h)

            elapsed = time.time() - start_time

            # Validate response
            if not result or not hasattr(result, "time_output"):
                raise ValueError("LLM returned invalid response structure")

            formatted_time = result.time_output.formatted_time
            if not formatted_time or len(formatted_time.strip()) == 0:
                raise ValueError("LLM returned empty formatted_time")

            # Check for AM/PM
            if "AM" not in formatted_time.upper() and "PM" not in formatted_time.upper():
                logger.warning(f"LLM response missing AM/PM: '{formatted_time}'")

            msg = f"✓ LLM ready: Responded in {elapsed:.2f}s with '{formatted_time}'"
            logger.success(msg)
            return True, msg

        except Exception as e:
            error_msg = f"✗ LLM failed: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise

    def warmup_embedder(self) -> Tuple[bool, str]:
        """Test embedder using LLM-generated dynamic sentences."""
        try:
            logger.info("Warming up embedder with LLM-generated sentences...")
            start_time = time.time()

            # Get centrally configured KB with embedder
            kb = registry.get_kb()
            if not kb or not hasattr(kb, "embedding_provider"):
                raise RuntimeError("KnowledgeBase not initialized")

            embedding_provider = kb.embedding_provider

            # Generate dynamic sentences using LLM (ensures no caching)
            now = datetime.now()
            current_time_ampm = now.strftime("%I:%M %p")

            sentence_gen = dspy.ChainOfThought(SentencePairGenerator)
            result = sentence_gen(current_time=current_time_ampm)

            if not result or not hasattr(result, "sentences"):
                raise ValueError("LLM failed to generate sentence pair")

            present_sentence = result.sentences.present_tense
            future_sentence = result.sentences.future_tense

            if not present_sentence or not future_sentence:
                raise ValueError("LLM returned empty sentences")

            logger.info(f"Present: {present_sentence}")
            logger.info(f"Future: {future_sentence}")

            # Embed both sentences (dynamic content ensures no embedding cache)
            emb_present = embedding_provider.get_embedding(present_sentence)
            emb_future = embedding_provider.get_embedding(future_sentence)

            # Validate embeddings are non-empty and have valid values
            for name, emb in [("present", emb_present), ("future", emb_future)]:
                if not emb or len(emb) == 0:
                    raise ValueError(f"Empty embedding for {name} tense sentence")
                if any(not math.isfinite(v) for v in emb):
                    raise ValueError(f"Invalid values (NaN/inf) in {name} tense embedding")
                # Verify non-zero values
                non_zero = sum(1 for v in emb if v != 0.0)
                if non_zero == 0:
                    raise ValueError(f"All-zero embedding for {name} tense sentence")

            embedding_dim = len(emb_present)
            elapsed = time.time() - start_time

            msg = (
                f"✓ Embedder ready: {embedding_dim}D, "
                f"embedded 2 LLM-generated sentences in {elapsed:.2f}s"
            )
            logger.success(msg)
            return True, msg

        except Exception as e:
            error_msg = f"✗ Embedder failed: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise

    def run_all(self) -> bool:
        """Run all warmup tests using DSPy signatures."""
        logger.info("=" * 60)
        logger.info("Starting LLM & Embedder Warmup (DSPy Signatures)")
        logger.info("=" * 60)

        try:
            # Test 1: LLM with ChainOfThought
            logger.info("\n[1/2] Testing LLM...")
            self.warmup_llm()

            # Test 2: Embedder
            logger.info("\n[2/2] Testing Embedder...")
            self.warmup_embedder()

            logger.info("\n" + "=" * 60)
            logger.success("✓ All warmup tests passed!")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"\n✗ Warmup failed: {e}")
            logger.error("=" * 60)
            raise
