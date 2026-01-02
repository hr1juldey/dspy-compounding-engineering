"""
Entity enrichment using DSPy for semantic enhancement.

Multi-step pipeline following SOLID principles:
1. Analyze purpose (simple, quick)
2. Enhance docstring (using purpose)
3. Infer types (focused task)

Each signature has single responsibility for easier LLM processing.
"""

import dspy


# Step 1: Purpose Analysis (simple, quick)
class PurposeAnalysisSignature(dspy.Signature):
    """Analyze entity purpose - SINGLE RESPONSIBILITY."""

    entity_type: str = dspy.InputField(desc="Function|Class|Method")
    entity_name: str = dspy.InputField(desc="Entity name")
    source_code: str = dspy.InputField(desc="Source code snippet")

    purpose_summary: str = dspy.OutputField(desc="One-sentence: What does this do?")
    complexity_score: int = dspy.OutputField(desc="Complexity rating 1-10")


# Step 2: Docstring Enhancement (uses purpose from step 1)
class DocstringEnhancementSignature(dspy.Signature):
    """Enhance docstring - SINGLE RESPONSIBILITY."""

    entity_type: str = dspy.InputField(desc="Function|Class|Method")
    entity_name: str = dspy.InputField(desc="Entity name")
    purpose_summary: str = dspy.InputField(desc="What it does (from step 1)")
    source_code: str = dspy.InputField(desc="Source code")
    existing_docstring: str = dspy.InputField(desc="Current docstring or 'None'")

    enhanced_docstring: str = dspy.OutputField(
        desc="Improved docstring with purpose, params, returns, examples"
    )


# Step 3: Type Inference (focused, independent)
class TypeInferenceSignature(dspy.Signature):
    """Infer parameter types - SINGLE RESPONSIBILITY."""

    entity_type: str = dspy.InputField(desc="Function|Method")
    entity_name: str = dspy.InputField(desc="Entity name")
    source_code: str = dspy.InputField(desc="Function/method source")

    inferred_types: str = dspy.OutputField(desc='JSON dict of param types: {"param_name": "type"}')


class EntityEnrichmentModule(dspy.Module):
    """
    Multi-step entity enrichment following SOLID principles.

    Pipeline:
    1. PurposeAnalysis (CoT) - Understand entity
    2. DocstringEnhancement (CoT) - Generate docs using purpose
    3. TypeInference (CoT) - Infer types independently

    Each step is simple, focused, easier for smaller LLMs.
    """

    def __init__(self):
        """Initialize multi-step enrichment pipeline."""
        super().__init__()

        # Step 1: Analyze purpose (simple task)
        self.purpose_analyzer = dspy.ChainOfThought(PurposeAnalysisSignature)

        # Step 2: Enhance docstring (uses step 1 output)
        self.docstring_enhancer = dspy.ChainOfThought(DocstringEnhancementSignature)

        # Step 3: Infer types (focused, independent)
        self.type_inferrer = dspy.ChainOfThought(TypeInferenceSignature)

    def forward(
        self,
        entity_type: str,
        entity_name: str,
        source_code: str,
        existing_docstring: str = "",
    ):
        """
        Enrich entity through multi-step pipeline.

        Args:
            entity_type: Type of entity (Function, Class, etc.)
            entity_name: Name of entity
            source_code: Source code
            existing_docstring: Existing docstring if any

        Returns:
            Object with: purpose_summary, complexity_score, enhanced_docstring, inferred_types
        """
        # Truncate source to avoid token limits
        source_truncated = source_code[:1500]

        # Step 1: Analyze purpose & complexity (quick, simple)
        purpose_result = self.purpose_analyzer(
            entity_type=entity_type,
            entity_name=entity_name,
            source_code=source_truncated,
        )

        # Step 2: Enhance docstring (uses purpose from step 1)
        docstring_result = self.docstring_enhancer(
            entity_type=entity_type,
            entity_name=entity_name,
            purpose_summary=purpose_result.purpose_summary,
            source_code=source_truncated,
            existing_docstring=existing_docstring or "None",
        )

        # Step 3: Infer types (only for functions/methods)
        inferred_types = {}
        if entity_type in ["Function", "Method"]:
            try:
                type_result = self.type_inferrer(
                    entity_type=entity_type,
                    entity_name=entity_name,
                    source_code=source_truncated,
                )
                # Parse JSON string to dict
                import json

                inferred_types = json.loads(type_result.inferred_types)
            except Exception:
                inferred_types = {}  # Fallback to empty if parsing fails

        # Combine results
        class EnrichmentResult:
            def __init__(self, purpose, complexity, docstring, types):
                self.purpose_summary = purpose
                self.complexity_score = complexity
                self.enhanced_docstring = docstring
                self.inferred_types = types

        return EnrichmentResult(
            purpose=purpose_result.purpose_summary,
            complexity=purpose_result.complexity_score,
            docstring=docstring_result.enhanced_docstring,
            types=inferred_types,
        )
