"""
Entity enrichment using DSPy for semantic enhancement.

Multi-step pipeline following SOLID principles:
1. Analyze purpose (simple, quick)
2. Enhance docstring (using purpose)
3. Infer types (focused task)

Each signature has single responsibility for easier LLM processing.
"""

from typing import cast

import dspy


# Step 1: Purpose Analysis (simple, quick)
class PurposeAnalysisSignature(dspy.Signature):
    """Analyze the purpose and complexity of a code entity (Step 1 of enrichment pipeline).

    INPUTS:
    - entity_type: Type of the entity being analyzed. Options:
      * "Function": Standalone function
      * "Class": Class definition
      * "Method": Class method
    - entity_name: Name of the entity (e.g., "process_data", "UserManager", "save")
    - source_code: Source code snippet of the entity (truncated to ~1500 chars)

    OUTPUT:
    - purpose_summary: Single-sentence summary describing what this entity does.
      Should be clear, concise, and focus on the "what" not the "how".
      Examples:
      * "Processes user data and validates input fields"
      * "Manages user authentication and session handling"
      * "Saves entity to database with error handling"
    - complexity_score: Integer rating from 1-10 indicating code complexity:
      * 1-3: Simple (few lines, straightforward logic)
      * 4-6: Moderate (multiple steps, some conditionals)
      * 7-9: Complex (nested logic, multiple responsibilities)
      * 10: Very complex (should be refactored)

    TASK INSTRUCTIONS:
    - Read the source code to understand what the entity does
    - Write a clear, single-sentence purpose summary
    - Assess complexity based on: lines of code, nesting depth, number of responsibilities
    - Keep the purpose statement high-level and user-focused
    """

    entity_type: str = dspy.InputField(desc="Function|Class|Method")
    entity_name: str = dspy.InputField(desc="Entity name")
    source_code: str = dspy.InputField(desc="Source code snippet")

    purpose_summary: str = dspy.OutputField(desc="One-sentence: What does this do?")
    complexity_score: int = dspy.OutputField(desc="Complexity rating 1-10")


# Step 2: Docstring Enhancement (uses purpose from step 1)
class DocstringEnhancementSignature(dspy.Signature):
    """Generate enhanced docstring for code entity (Step 2 of enrichment pipeline).

    INPUTS:
    - entity_type: Type of entity. Options:
      * "Function": Standalone function
      * "Class": Class definition
      * "Method": Class method
    - entity_name: Name of the entity
    - purpose_summary: One-sentence purpose from Step 1 (PurposeAnalysisSignature output)
    - source_code: Source code of the entity (truncated to ~1500 chars)
    - existing_docstring: Current docstring if one exists, or the string "None" if missing

    OUTPUT:
    - enhanced_docstring: Improved docstring following Python best practices. Should include:
      * Summary line: Brief description based on purpose_summary
      * Args section: Document all parameters with types and descriptions (for functions/methods)
      * Returns section: Document return value with type and description (for functions/methods)
      * Raises section: Document exceptions raised (if applicable)
      * Examples section: Brief usage example (optional but recommended)
      Format as Google-style or NumPy-style docstring.

    TASK INSTRUCTIONS:
    - Use the purpose_summary as the foundation for the summary line
    - Analyze the source code to identify parameters, return types, and exceptions
    - If existing_docstring is not "None", preserve good content and improve the rest
    - For classes: Document the class purpose, attributes, and key methods
    - For functions/methods: Document all parameters and return values
    - Keep docstrings concise but complete
    - Use proper formatting (indentation, sections, type hints)
    """

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
    """Infer parameter and return types for functions/methods (Step 3 of enrichment pipeline).

    INPUTS:
    - entity_type: Type of entity. Options:
      * "Function": Standalone function
      * "Method": Class method
      (Only functions and methods have parameters to type-infer)
    - entity_name: Name of the function or method
    - source_code: Source code of the function/method (truncated to ~1500 chars)

    OUTPUT:
    - inferred_types: JSON string representing inferred types as a dictionary.
      Format: {"param_name": "type", "return": "return_type"}

      Examples:
      * {"user_id": "int", "name": "str", "return": "bool"}
      * {"data": "dict", "validate": "bool", "return": "Optional[User]"}
      * {"items": "list[str]", "return": "None"}

      Type inference guidelines:
      * Use Python type hints syntax (str, int, bool, list, dict, etc.)
      * Use Optional[T] for potentially None values
      * Use Union[A, B] for multiple possible types
      * Use list[T], dict[K, V] for generic collections
      * Include "return" key for the return type
      * If a type cannot be inferred, use "Any"

    TASK INSTRUCTIONS:
    - Analyze the source code to understand parameter usage
    - Infer types based on:
      * Variable names (e.g., "count" suggests int, "name" suggests str)
      * Operations (e.g., x + 1 suggests int, x.upper() suggests str)
      * Comparisons and conditionals
      * Return statements
    - Return a valid JSON dictionary as a string
    - Include all parameters and the return type
    - Be conservative: use "Any" if type is truly ambiguous
    """

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
        purpose_result = cast(
            dspy.Prediction,
            self.purpose_analyzer(
                entity_type=entity_type,
                entity_name=entity_name,
                source_code=source_truncated,
            ),
        )

        # Step 2: Enhance docstring (uses purpose from step 1)
        docstring_result = cast(
            dspy.Prediction,
            self.docstring_enhancer(
                entity_type=entity_type,
                entity_name=entity_name,
                purpose_summary=purpose_result.purpose_summary,
                source_code=source_truncated,
                existing_docstring=existing_docstring or "None",
            ),
        )

        # Step 3: Infer types (only for functions/methods)
        inferred_types = {}
        if entity_type in ["Function", "Method"]:
            try:
                type_result = cast(
                    dspy.Prediction,
                    self.type_inferrer(
                        entity_type=entity_type,
                        entity_name=entity_name,
                        source_code=source_truncated,
                    ),
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
