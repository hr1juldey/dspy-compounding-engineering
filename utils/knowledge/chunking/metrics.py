"""
Reward metrics for semantic chunking quality evaluation.

Provides quantifiable scoring for BestOfN and Refine modules.
"""

from typing import Any, Callable

from utils.knowledge.chunking.semantic_extractor import CodeStructure
from utils.knowledge.chunking.strategies import ChunkBoundary


def ast_integrity_score(chunks: list[ChunkBoundary], structure: CodeStructure) -> float:
    """
    Metric 1: Structural integrity (50% weight).
    Functions/classes must NOT be split across chunks.
    """
    total = len(structure.functions) + len(structure.classes)
    if total == 0:
        return 1.0

    violations = 0
    for func in structure.functions:
        if _is_split(func["start"], func["end"], chunks):
            violations += 1

    for cls in structure.classes:
        if _is_split(cls["start"], cls["end"], chunks):
            violations += 1

    return max(0.0, 1.0 - (violations / total))


def size_distribution_score(chunks: list[ChunkBoundary]) -> float:
    """
    Metric 2: Size balance (20% weight).
    Ideal: 1500-3000 chars, Acceptable: 1000-4000 chars.
    """
    IDEAL_MIN, IDEAL_MAX = 1500, 3000
    ACCEPTABLE_MIN, ACCEPTABLE_MAX = 1000, 4000

    scores = []
    for chunk in chunks:
        size = len(chunk.content)

        if IDEAL_MIN <= size <= IDEAL_MAX:
            scores.append(1.0)
        elif ACCEPTABLE_MIN <= size <= ACCEPTABLE_MAX:
            if size < IDEAL_MIN:
                scores.append((size - ACCEPTABLE_MIN) / (IDEAL_MIN - ACCEPTABLE_MIN))
            else:
                scores.append(1.0 - ((size - IDEAL_MAX) / (ACCEPTABLE_MAX - IDEAL_MAX)))
        else:
            scores.append(0.0)

    return sum(scores) / len(scores) if scores else 0.0


def boundary_quality_score(chunks: list[ChunkBoundary], original_lines: list[str]) -> float:
    """
    Metric 3: Boundary quality (20% weight).
    Chunks should start at logical boundaries (indentation 0, after blank line).
    """
    if len(chunks) <= 1:
        return 1.0

    good_boundaries = 1  # First chunk always valid

    for chunk in chunks[1:]:
        start_line = chunk.start_line - 1  # Convert to 0-indexed
        if start_line >= len(original_lines):
            continue

        line = original_lines[start_line]
        indent = len(line) - len(line.lstrip())
        prev_blank = start_line > 0 and original_lines[start_line - 1].strip() == ""

        if indent == 0 or prev_blank:
            good_boundaries += 1

    return good_boundaries / len(chunks)


def overlap_adequacy_score(chunks: list[ChunkBoundary]) -> float:
    """
    Metric 4: Overlap adequacy (10% weight).
    Target: 200-400 char overlap between consecutive chunks.
    """
    if len(chunks) <= 1:
        return 1.0

    MIN, IDEAL_MIN, IDEAL_MAX = 100, 200, 400

    scores = []
    for i in range(len(chunks) - 1):
        overlap_lines = chunks[i].end_line - chunks[i + 1].start_line + 1

        if overlap_lines < 0:
            scores.append(0.0)
        elif overlap_lines < MIN:
            scores.append(overlap_lines / MIN)
        elif IDEAL_MIN <= overlap_lines <= IDEAL_MAX:
            scores.append(1.0)
        else:
            scores.append(0.5)

    return sum(scores) / len(scores) if scores else 0.0


def create_reward_function(structure: CodeStructure, original_lines: list[str]) -> Callable:
    """
    Factory: Creates reward function for BestOfN and Refine.

    Returns:
        Callable[[args, pred], float]: Reward function (0.0 to 1.0)
    """

    def reward_fn(args: Any, pred: Any) -> float:
        # Access chunking_strategy from the Prediction object
        strategy = getattr(pred, "chunking_strategy", None)
        if not strategy or not hasattr(strategy, "chunks"):
            return 0.0  # Failed prediction

        chunks = strategy.chunks

        integrity = ast_integrity_score(chunks, structure)
        size = size_distribution_score(chunks)
        boundary = boundary_quality_score(chunks, original_lines)
        overlap = overlap_adequacy_score(chunks)

        # Weighted combination
        final = 0.50 * integrity + 0.20 * size + 0.20 * boundary + 0.10 * overlap

        return final

    return reward_fn


def _is_split(start: int, end: int, chunks: list[ChunkBoundary]) -> bool:
    """Check if line range [start, end] is split across multiple chunks"""
    containing = [c for c in chunks if not (c.end_line < start or c.start_line > end)]
    return len(containing) > 1
