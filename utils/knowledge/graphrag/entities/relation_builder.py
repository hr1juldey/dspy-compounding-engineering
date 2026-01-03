"""
Relation extraction between code entities.

Builds call graphs and dependency relationships from AST.
"""

import ast

from utils.knowledge.graphrag.entities.entity_model import Entity


class RelationBuilder:
    """
    Extract relationships between entities.

    Implements scope tracking to determine caller-callee relationships.
    """

    @staticmethod
    def build_relations(tree: ast.AST, entities: list[Entity]) -> None:
        """
        Extract call relationships between entities.

        Modifies entities in-place to add "calls" relations.

        Args:
            tree: AST tree of the source code
            entities: List of entities to build relations for
        """
        # Build name-to-entity mapping
        entity_map = {e.name: e for e in entities}

        # Walk AST to find function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Get caller context (which function is making this call)
                caller = RelationBuilder._find_enclosing_function(tree, node)
                if caller and caller in entity_map:
                    # Get callee name
                    callee = RelationBuilder._get_call_target(node)
                    if callee:
                        if "calls" not in entity_map[caller].relations:
                            entity_map[caller].relations["calls"] = []
                        entity_map[caller].relations["calls"].append(callee)

    @staticmethod
    def _find_enclosing_function(tree: ast.AST, target_node: ast.AST) -> str | None:
        """
        Find the name of the function/method containing this node.

        Uses parent mapping to traverse up the AST tree.

        Args:
            tree: AST tree root
            target_node: Node to find enclosing function for

        Returns:
            Function/method name or None if not inside a function
        """

        class ParentMapper(ast.NodeVisitor):
            """Build parent mapping for AST nodes."""

            def __init__(self):
                self.parent_map = {}

            def visit(self, node):
                for child in ast.iter_child_nodes(node):
                    self.parent_map[child] = node
                self.generic_visit(node)

        # Build parent map
        mapper = ParentMapper()
        mapper.visit(tree)

        # Traverse up from target node
        current = target_node
        while current in mapper.parent_map:
            current = mapper.parent_map[current]
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current.name
            if isinstance(current, ast.ClassDef):
                # Check if inside a method
                for item in current.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Need to check if target_node is inside this method
                        if RelationBuilder._is_node_inside(target_node, item, mapper.parent_map):
                            return f"{current.name}.{item.name}"

        return None

    @staticmethod
    def _is_node_inside(target: ast.AST, container: ast.AST, parent_map: dict) -> bool:
        """Check if target node is inside container node."""
        current = target
        while current in parent_map:
            if current == container:
                return True
            current = parent_map[current]
        return False

    @staticmethod
    def _get_call_target(call_node: ast.Call) -> str | None:
        """Extract the name of the function being called."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None
