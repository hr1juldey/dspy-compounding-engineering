"""Class and method entity extraction from AST."""

import ast

from utils.knowledge.entities.entity_model import Entity, generate_entity_id


class ClassMethodExtractor:
    """Extract classes and their methods as entities."""

    @staticmethod
    def extract(tree: ast.AST, filepath: str, code: str) -> list[Entity]:
        """Extract all class and method entities from AST."""
        entities = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_id = generate_entity_id(filepath, f"CLASS_{node.name}", node.lineno)

                # Extract base classes
                bases = [ast.unparse(base) for base in node.bases]

                # Extract method names
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)

                        # Create entity for each method
                        method_id = generate_entity_id(
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
