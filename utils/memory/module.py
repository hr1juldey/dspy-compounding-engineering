"""
Memory-Augmented DSPy Module using mem0.

Wraps DSPy modules with persistent agent memory injection.
Similar to KBPredict but uses mem0 for agent-specific memory.
"""

from typing import Any

import dspy

from utils.io.logger import logger
from utils.memory.agent_memory import AgentMemory


class MemoryPredict(dspy.Module):
    """
    DSPy Module with mem0 memory injection.

    Injects past agent interactions into context before prediction.
    """

    def __init__(self, signature: Any, agent_name: str, inject_memory: bool = True, **kwargs):
        super().__init__()
        self.agent_name = agent_name
        self.inject_memory = inject_memory
        self.memory = AgentMemory(agent_name)

        # Support signatures and modules
        if isinstance(signature, dspy.Module):
            self.predictor = signature
        elif (
            isinstance(signature, type)
            and issubclass(signature, dspy.Module)
            and not issubclass(signature, dspy.Signature)
        ):
            self.predictor = signature(**kwargs)
        else:
            self.predictor = dspy.Predict(signature, **kwargs)

    def forward(self, **kwargs):
        if not self.inject_memory:
            return self.predictor(**kwargs)

        logger.debug(f"MemoryPredict: Injecting memory for {self.agent_name}")
        augmented_kwargs = self._inject_memory_context(kwargs)

        # Call predictor
        result = self.predictor(**augmented_kwargs)

        # Store interaction
        query_parts = [str(v)[:500] for v in kwargs.values() if isinstance(v, str)]
        query = " ".join(query_parts)[:1000]
        self.memory.add_interaction(query, result.toDict())

        return result

    def _inject_memory_context(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        # Build query from inputs
        query_parts = [str(v)[:500] for v in kwargs.values() if isinstance(v, str)]
        query = " ".join(query_parts)[:1000]

        # Get memory context
        memory_context = self.memory.get_context(query, limit=5)

        if not memory_context:
            return kwargs

        # Inject into largest string field
        kwargs = kwargs.copy()
        target_key = max(
            (k for k, v in kwargs.items() if isinstance(v, str)),
            key=lambda k: len(kwargs[k]),
            default=None,
        )

        if target_key:
            kwargs[target_key] = f"{memory_context}\n\n---\n\n{kwargs[target_key]}"

        return kwargs
