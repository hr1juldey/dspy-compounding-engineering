"""
DSPy-based chunking strategy generator using ChainOfThought.

Generates semantic chunking strategies with reasoning, wrapped in BestOfN for quality.
"""

import dspy
from pydantic import BaseModel, Field

from utils.knowledge.semantic_extractor import CodeStructure


class ChunkBoundary(BaseModel):
    """Single chunk with metadata"""

    start_line: int = Field(description="1-indexed line number where chunk starts")
    end_line: int = Field(description="1-indexed line number where chunk ends")
    content: str = Field(description="Actual text content of chunk")
    semantic_label: str = Field(
        description="What this chunk contains (e.g., 'function process_data', 'imports')"
    )
    rationale: str = Field(description="Why this boundary was chosen")


class ChunkingStrategy(BaseModel):
    """Complete chunking strategy with reasoning"""

    reasoning: str = Field(
        default="Semantic chunking applied",
        description="Overall strategy and approach to chunking",
    )
    chunks: list[ChunkBoundary] = Field(description="List of chunk boundaries")
    confidence: float = Field(default=0.5, description="Self-assessed confidence (0.0 to 1.0)")


class ChunkingSignature(dspy.Signature):
    """Generate a semantic chunking strategy for Python source code.

    INPUTS:
    - code: The complete Python source code to be chunked
    - ast_structure: AST-extracted structure showing functions, classes, and their line ranges
    - target_chunk_size: Desired chunk size in characters (aim for this, but prioritize
      semantic boundaries)
    - min_overlap: Minimum character overlap between consecutive chunks for context
      preservation

    OUTPUT:
    You must return a ChunkingStrategy object containing:
    - reasoning: Explain your chunking decisions (why you split where you did)
    - chunks: List of ChunkBoundary objects, each with:
      * start_line: 1-indexed line number where chunk starts
      * end_line: 1-indexed line number where chunk ends (inclusive)
      * content: The actual text content of the chunk
      * semantic_label: Description of what this chunk contains
        (e.g., "function process_data", "class Config", "imports")
      * rationale: Why this specific boundary was chosen
    - confidence: Your self-assessed confidence in this chunking strategy (0.0 to 1.0)

    STRATEGY:
    - Maintain semantic boundaries (don't split functions/classes mid-definition)
    - Group related code together (imports together, helper functions near their usage)
    - Ensure chunks have context via minimum overlap
    - Prefer natural boundaries (function/class definitions, blank lines, comments)
    """

    code: str = dspy.InputField(description="Python source code to chunk")
    ast_structure: str = dspy.InputField(
        description="AST-extracted structure (functions, classes, line ranges)"
    )
    target_chunk_size: int = dspy.InputField(
        default=2000, description="Target chunk size in characters"
    )
    min_overlap: int = dspy.InputField(default=200, description="Minimum overlap between chunks")

    chunking_strategy: ChunkingStrategy = dspy.OutputField(
        description="Generated chunking strategy with reasoning, chunks list, and confidence"
    )


class ChunkingStrategyGenerator(dspy.Module):
    """
    Generates semantic chunking strategies using ChainOfThought.
    Wrapped in BestOfN(N=3) for quality.
    """

    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought(ChunkingSignature)

    def forward(
        self,
        code: str,
        ast_structure: CodeStructure,
        target_chunk_size: int = 2000,
        min_overlap: int = 200,
    ):
        """Generate chunking strategy with reasoning"""
        ast_str = self._format_ast_structure(ast_structure)

        result = self.cot(
            code=code,
            ast_structure=ast_str,
            target_chunk_size=target_chunk_size,
            min_overlap=min_overlap,
        )

        return result

    def _format_ast_structure(self, structure: CodeStructure) -> str:
        """Format CodeStructure for LLM consumption"""
        lines = [f"Total lines: {structure.total_lines}"]

        if structure.imports:
            first_import = structure.imports[0]["line"]
            last_import = structure.imports[-1]["line"]
            lines.append(f"\nImports: Lines {first_import}-{last_import}")

        if structure.functions:
            lines.append("\nFunctions:")
            for func in structure.functions:
                lines.append(f"  - {func['name']}: Lines {func['start']}-{func['end']}")

        if structure.classes:
            lines.append("\nClasses:")
            for cls in structure.classes:
                lines.append(f"  - {cls['name']}: Lines {cls['start']}-{cls['end']}")
                for method in cls["methods"]:
                    lines.append(f"    - method: {method}")

        return "\n".join(lines)
