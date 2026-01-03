"""Function entity extraction from AST."""

import ast

from utils.knowledge.graphrag.entities.entity_model import Entity, generate_entity_id


class FunctionExtractor:
    """Extract top-level functions as entities."""

    @staticmethod
    def extract(tree: ast.AST, filepath: str, code: str) -> list[Entity]:
        """Extract all top-level function entities from AST."""
        entities = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entity_id = generate_entity_id(filepath, f"FUNCTION_{node.name}", node.lineno)

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
