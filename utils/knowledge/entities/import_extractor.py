"""Import entity extraction from AST."""

import ast

from utils.knowledge.entities.entity_model import Entity, generate_entity_id


class ImportExtractor:
    """Extract import statements as entities."""

    @staticmethod
    def extract(tree: ast.AST, filepath: str) -> list[Entity]:
        """Extract all import entities from AST."""
        entities = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    entity_id = generate_entity_id(filepath, f"IMPORT_{alias.name}", node.lineno)
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
                    entity_id = generate_entity_id(
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
