"""
Function I/O Extractor (Dimension 3).

Uses Python AST to parse function signatures into ParameterInfo.
NOT a DSPy module - pure Python parsing.
"""

import ast

from agents.graphrag.schema import ParameterInfo


class ParameterExtractor:
    """Extracts structured parameter information using AST."""

    def extract_from_code(
        self, source_code: str, entity_name: str
    ) -> tuple[list[ParameterInfo], str | None]:
        """
        Parse function signature from source code.

        Returns:
            (parameters, return_type)
        """
        try:
            tree = ast.parse(source_code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == entity_name:
                    parameters = self._parse_parameters(node.args)
                    return_type = self._parse_return_type(node)
                    return parameters, return_type

            return [], None
        except Exception:
            return [], None

    def _parse_parameters(self, args: ast.arguments) -> list[ParameterInfo]:
        """Parse function arguments into ParameterInfo."""
        params = []

        # Positional arguments
        for i, arg in enumerate(args.args):
            params.append(
                ParameterInfo(
                    name=arg.arg,
                    type_hint=ast.unparse(arg.annotation) if arg.annotation else None,
                    position=i,
                )
            )

        # *args
        if args.vararg:
            params.append(
                ParameterInfo(
                    name=args.vararg.arg,
                    type_hint=ast.unparse(args.vararg.annotation)
                    if args.vararg.annotation
                    else None,
                    is_variadic=True,
                    position=len(params),
                )
            )

        # **kwargs
        if args.kwarg:
            params.append(
                ParameterInfo(
                    name=args.kwarg.arg,
                    type_hint=ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None,
                    is_variadic=True,
                    position=len(params),
                )
            )

        return params

    def _parse_return_type(self, node: ast.FunctionDef) -> str | None:
        """Extract return type annotation."""
        if node.returns:
            return ast.unparse(node.returns)
        return None
