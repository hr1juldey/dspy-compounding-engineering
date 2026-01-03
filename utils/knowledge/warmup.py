"""Warmup utility for LLM and embedder initialization with error propagation."""

import time
from typing import Tuple

import dspy

from utils.io.logger import logger
from utils.knowledge.embeddings_dspy import DSPyEmbeddingProvider as EmbeddingProvider


class WarmupTest:
    """Test LLM and embedder initialization with actual API calls."""

    def __init__(self):
        self.embedding_provider = None
        self.llm_config = None

    def warmup_embedder(self, test_text: str = "warmup test") -> Tuple[bool, str]:
        """
        Test embedder by generating a test embedding.

        Args:
            test_text: Text to embed for testing

        Returns:
            Tuple[success, message]

        Raises:
            Exception: If embedder fails to initialize or generate embedding
        """
        try:
            logger.info("Warming up embedder...")
            start_time = time.time()

            self.embedding_provider = EmbeddingProvider()
            embedding = self.embedding_provider.get_embedding(test_text)

            elapsed = time.time() - start_time
            embedding_dim = len(embedding) if embedding else 0

            if not embedding or embedding_dim == 0:
                raise ValueError("Embedder returned empty embedding")

            msg = f"✓ Embedder ready: {embedding_dim}D embedding generated in {elapsed:.2f}s"
            logger.success(msg)
            return True, msg

        except Exception as e:
            error_msg = f"✗ Embedder failed: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise

    def warmup_llm(self, test_prompt: str = "Say 'ready'") -> Tuple[bool, str]:
        """
        Test LLM by generating a test response.

        Args:
            test_prompt: Prompt to send to LLM for testing

        Returns:
            Tuple[success, message]

        Raises:
            Exception: If LLM fails to initialize or generate response
        """
        try:
            logger.info("Warming up LLM...")
            start_time = time.time()

            # Get current LM from DSPy settings
            if not hasattr(dspy.settings, "lm") or dspy.settings.lm is None:
                raise RuntimeError(
                    "DSPy LM not configured. Call configure_dspy() before warmup_llm()"
                )

            lm = dspy.settings.lm

            # Make a test call to the LLM
            response = lm(test_prompt, max_tokens=10)

            elapsed = time.time() - start_time
            response_text = response[0] if isinstance(response, (list, tuple)) else str(response)

            if not response_text or len(response_text.strip()) == 0:
                raise ValueError("LLM returned empty response")

            msg = f"✓ LLM ready: Got response in {elapsed:.2f}s: {response_text[:50]}"
            logger.success(msg)
            return True, msg

        except Exception as e:
            error_msg = f"✗ LLM failed: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise

    def warmup_dspy_module(self) -> Tuple[bool, str]:
        """
        Test DSPy module initialization (ChainOfThought).

        Returns:
            Tuple[success, message]

        Raises:
            Exception: If DSPy module fails
        """
        try:
            logger.info("Warming up DSPy ChainOfThought...")
            start_time = time.time()

            from utils.knowledge.chunking_strategies import ChunkingStrategyGenerator

            generator = ChunkingStrategyGenerator()

            # Verify the generator has the ChainOfThought module
            if not hasattr(generator, "cot"):
                raise RuntimeError("ChunkingStrategyGenerator missing ChainOfThought")

            elapsed = time.time() - start_time
            msg = f"✓ DSPy module ready in {elapsed:.2f}s"
            logger.success(msg)
            return True, msg

        except Exception as e:
            error_msg = f"✗ DSPy module failed: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise

    def run_all(self) -> bool:
        """
        Run all warmup tests in sequence.

        Returns:
            True if all pass

        Raises:
            Exception: On first failure (with proper error message)
        """
        logger.info("=" * 60)
        logger.info("Starting LLM & Embedder Warmup Tests")
        logger.info("=" * 60)

        try:
            # Test 1: Embedder
            logger.info("\n[1/3] Testing Embedder...")
            self.warmup_embedder()

            # Test 2: LLM
            logger.info("\n[2/3] Testing LLM...")
            self.warmup_llm()

            # Test 3: DSPy Module
            logger.info("\n[3/3] Testing DSPy Module...")
            self.warmup_dspy_module()

            logger.info("\n" + "=" * 60)
            logger.success("✓ All warmup tests passed!")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"\n✗ Warmup failed: {e}")
            logger.error("=" * 60)
            raise
