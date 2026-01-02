"""
Entity extraction orchestrator (facade pattern).

Coordinates AST extractors and relation builders.
"""

import ast
import os

from utils.io.logger import logger
from utils.knowledge.entities.class_extractor import ClassMethodExtractor
from utils.knowledge.entities.entity_model import Entity
from utils.knowledge.entities.function_extractor import FunctionExtractor
from utils.knowledge.entities.import_extractor import ImportExtractor
from utils.knowledge.entities.module_extractor import ModuleExtractor
from utils.knowledge.entities.relation_builder import RelationBuilder


class EntityExtractor:
    """
    Fast AST-based entity extraction (NO expensive LLM calls).

    Architecture:
    1. AST extracts all code entities deterministically
    2. Generates deterministic IDs (hash-based)
    3. Extracts relations (imports, calls, inheritance)
    4. Optional LLM semantic enrichment (disabled by default)
    """

    def __init__(self, use_llm_enrichment: bool | None = None):
        """
        Initialize entity extractor.

        Args:
            use_llm_enrichment: Whether to use LLM for semantic enrichment (default: env var)
        """
        if use_llm_enrichment is None:
            use_llm_enrichment = os.getenv("USE_LLM_ENTITY_ENRICHMENT", "false").lower() == "true"

        self.use_llm_enrichment = use_llm_enrichment

        # Only load LLM modules if needed
        if self.use_llm_enrichment:
            logger.info("LLM entity enrichment ENABLED (will be slow)")
            try:
                from utils.knowledge.entities.entity_enrichment import EntityEnrichmentModule

                self.enrichment_module = EntityEnrichmentModule()
                logger.success("Entity enrichment module loaded")
            except Exception as e:
                logger.error(f"Failed to load enrichment module: {e}")
                self.use_llm_enrichment = False
                self.enrichment_module = None
        else:
            logger.debug("LLM entity enrichment DISABLED (fast AST-only mode)")
            self.enrichment_module = None

    def extract_from_python(self, code: str, filepath: str) -> list[Entity]:
        """
        Extract all entities from Python code using AST.

        Fast, deterministic, no LLM calls (unless enrichment enabled).

        Args:
            code: Python source code
            filepath: File path (for entity IDs)

        Returns:
            List of Entity objects
        """
        entities = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {filepath}: {e}")
            return []

        # Extract module-level entity
        module_entity = ModuleExtractor.extract(tree, filepath, code)
        entities.append(module_entity)

        # Extract imports
        imports_entities = ImportExtractor.extract(tree, filepath)
        entities.extend(imports_entities)

        # Extract functions
        functions_entities = FunctionExtractor.extract(tree, filepath, code)
        entities.extend(functions_entities)

        # Extract classes and methods
        classes_entities = ClassMethodExtractor.extract(tree, filepath, code)
        entities.extend(classes_entities)

        # Extract relations between entities
        RelationBuilder.build_relations(tree, entities)

        # Optionally enrich entities with LLM
        if self.use_llm_enrichment and self.enrichment_module:
            entities = self._enrich_entities(entities)

        return entities

    def _enrich_entities(self, entities):
        """
        Enrich entities with LLM-generated metadata.

        Args:
            entities: List of entities to enrich

        Returns:
            List of enriched entities
        """
        enriched = []

        for entity in entities:
            # Only enrich Functions, Methods, and Classes
            if entity.type not in ["Function", "Method", "Class"]:
                enriched.append(entity)
                continue

            try:
                # Get enrichment from LLM
                result = self.enrichment_module.forward(
                    entity_type=entity.type,
                    entity_name=entity.name,
                    source_code=entity.properties.get("source_code", ""),
                    existing_docstring=entity.properties.get("docstring", ""),
                )

                # Update entity with enriched metadata
                entity.properties["enriched_docstring"] = result.enhanced_docstring
                entity.properties["inferred_types"] = result.inferred_types
                entity.properties["purpose_summary"] = result.purpose_summary
                entity.properties["complexity_score"] = result.complexity_score

                enriched.append(entity)

            except Exception as e:
                logger.warning(f"Failed to enrich {entity.name}: {e}")
                enriched.append(entity)  # Keep original

        return enriched
