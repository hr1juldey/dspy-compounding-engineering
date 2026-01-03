"""Module entity extraction from AST."""

import ast
import os

from utils.knowledge.graphrag.entities.entity_model import Entity, generate_entity_id


class ModuleExtractor:
    """Extract module-level entity."""

    @staticmethod
    def extract(tree: ast.AST, filepath: str, code: str) -> Entity:
        """Extract module entity from AST."""
        module_id = generate_entity_id(filepath, "MODULE", 1)
        return Entity(
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
