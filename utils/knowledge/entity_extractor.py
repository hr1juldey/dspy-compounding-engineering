"""
Fast AST-based entity extraction for code knowledge graph.

Extracts typed entities (functions, classes, imports) without expensive LLM calls.
LLM enrichment is optional and disabled by default.
"""

import ast
import hashlib
import os
from dataclasses import dataclass, field
from typing import Any

from utils.io.logger import logger


@dataclass
class Entity:
    """
    Graph node representing a code entity.

    Entities are stored in Qdrant with:
    - Dense vector embedding (semantic search)
    - Relations embedded in payload (no separate collection)
    """

    id: str  # Deterministic hash-based ID
    type: str  # Function, Class, Method, Import, Module
    name: str  # Entity name
    file_path: str  # Where defined
    line_start: int
    line_end: int

    # Core properties
    properties: dict[str, Any] = field(default_factory=dict)

    # Relations (embedded in entity, not separate collection)
    relations: dict[str, list[str]] = field(default_factory=dict)
    # Example: {"calls": ["func_id_1"], "imports": ["module_id"], "defines": ["method_id"]}

    # Embedding vector (populated later by embedding provider)
    embedding: list[float] = field(default_factory=list)


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
            # TODO: Load DSPy semantic enrichment module when needed
        else:
            logger.debug("LLM entity enrichment DISABLED (fast AST-only mode)")

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
        module_id = self._generate_id(filepath, "MODULE", 1)
        module_entity = Entity(
            id=module_id,
            type="Module",
            name=os.path.basename(filepath).replace(".py", ""),
            file_path=filepath,
            line_start=1,
            line_end=len(code.split("\n")),
            properties={
                "docstring": ast.get_docstring(tree),
                "size_lines": len(code.split("\n")),
            },
            relations={},
        )
        entities.append(module_entity)

        # Extract imports
        imports_entities = self._extract_imports(tree, filepath)
        entities.extend(imports_entities)

        # Extract functions
        functions_entities = self._extract_functions(tree, filepath, code)
        entities.extend(functions_entities)

        # Extract classes
        classes_entities = self._extract_classes(tree, filepath, code)
        entities.extend(classes_entities)

        # Extract relations between entities
        self._extract_relations(tree, entities, filepath)

        return entities

    def _extract_imports(self, tree: ast.AST, filepath: str) -> list[Entity]:
        """Extract import statements as entities."""
        entities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    entity_id = self._generate_id(filepath, f"IMPORT_{alias.name}", node.lineno)
                    entities.append(
                        Entity(
                            id=entity_id,
                            type="Import",
                            name=alias.name,
                            file_path=filepath,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            properties={"alias": alias.asname, "import_type": "absolute"},
                            relations={},
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    entity_id = self._generate_id(
                        filepath, f"IMPORT_{module}.{alias.name}", node.lineno
                    )
                    entities.append(
                        Entity(
                            id=entity_id,
                            type="Import",
                            name=f"{module}.{alias.name}" if module else alias.name,
                            file_path=filepath,
                            line_start=node.lineno,
                            line_end=node.lineno,
                            properties={
                                "from_module": module,
                                "alias": alias.asname,
                                "import_type": "from",
                                "level": node.level,
                            },
                            relations={},
                        )
                    )

        return entities

    def _extract_functions(self, tree: ast.AST, filepath: str, code: str) -> list[Entity]:
        """Extract top-level functions as entities."""
        entities = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entity_id = self._generate_id(filepath, f"FUNCTION_{node.name}", node.lineno)

                # Extract function signature
                try:
                    signature = ast.unparse(node.args)
                except Exception:
                    signature = ""

                entities.append(
                    Entity(
                        id=entity_id,
                        type="Function",
                        name=node.name,
                        file_path=filepath,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        properties={
                            "signature": signature,
                            "docstring": ast.get_docstring(node),
                            "decorators": [ast.unparse(d) for d in node.decorator_list],
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                            "returns": ast.unparse(node.returns) if node.returns else None,
                            "source_code": ast.get_source_segment(code, node),
                        },
                        relations={},
                    )
                )

        return entities

    def _extract_classes(self, tree: ast.AST, filepath: str, code: str) -> list[Entity]:
        """Extract classes and their methods as entities."""
        entities = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_id = self._generate_id(filepath, f"CLASS_{node.name}", node.lineno)

                # Extract base classes
                bases = [ast.unparse(base) for base in node.bases]

                # Extract method names
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)

                        # Create entity for each method
                        method_id = self._generate_id(
                            filepath, f"METHOD_{node.name}.{item.name}", item.lineno
                        )
                        try:
                            signature = ast.unparse(item.args)
                        except Exception:
                            signature = ""

                        entities.append(
                            Entity(
                                id=method_id,
                                type="Method",
                                name=f"{node.name}.{item.name}",
                                file_path=filepath,
                                line_start=item.lineno,
                                line_end=item.end_lineno or item.lineno,
                                properties={
                                    "class_name": node.name,
                                    "method_name": item.name,
                                    "signature": signature,
                                    "docstring": ast.get_docstring(item),
                                    "decorators": [ast.unparse(d) for d in item.decorator_list],
                                    "is_async": isinstance(item, ast.AsyncFunctionDef),
                                    "returns": ast.unparse(item.returns) if item.returns else None,
                                    "source_code": ast.get_source_segment(code, item),
                                },
                                relations={"defined_by": [class_id]},
                            )
                        )

                # Create class entity
                entities.append(
                    Entity(
                        id=class_id,
                        type="Class",
                        name=node.name,
                        file_path=filepath,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        properties={
                            "docstring": ast.get_docstring(node),
                            "bases": bases,
                            "methods": methods,
                            "decorators": [ast.unparse(d) for d in node.decorator_list],
                            "source_code": ast.get_source_segment(code, node),
                        },
                        relations={
                            "inherits": bases,
                            "defines": [f"{node.name}.{m}" for m in methods],
                        },
                    )
                )

        return entities

    def _extract_relations(self, tree: ast.AST, entities: list[Entity], filepath: str):
        """
        Extract call relationships between entities.

        Modifies entities in-place to add "calls" relations.
        """
        # Build name-to-entity mapping
        entity_map = {e.name: e for e in entities}

        # Walk AST to find function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Get caller context (which function is making this call)
                caller = self._find_enclosing_function(tree, node)
                if caller and caller in entity_map:
                    # Get callee name
                    callee = self._get_call_target(node)
                    if callee:
                        if "calls" not in entity_map[caller].relations:
                            entity_map[caller].relations["calls"] = []
                        entity_map[caller].relations["calls"].append(callee)

    def _find_enclosing_function(self, tree: ast.AST, node: ast.AST) -> str | None:  # noqa: ARG002
        """Find the name of the function/method containing this node."""
        # TODO: Implement proper scope tracking
        # For now, return None (simple version)
        return None

    def _get_call_target(self, call_node: ast.Call) -> str | None:
        """Extract the name of the function being called."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None

    def _generate_id(self, filepath: str, name: str, line: int) -> str:
        """
        Generate deterministic ID for entity.

        Format: hash(filepath:name:line)
        """
        unique_str = f"{filepath}::{name}::{line}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
