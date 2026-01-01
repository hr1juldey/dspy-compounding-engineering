"""
AST-based Python code structure extractor.

Provides fast, deterministic extraction of functions, classes, and imports
for semantic chunking validation.
"""

import ast
from dataclasses import dataclass
from typing import Any


@dataclass
class CodeStructure:
    """AST-extracted code structure (ground truth)"""

    functions: list[dict[str, Any]]
    classes: list[dict[str, Any]]
    imports: list[dict[str, Any]]
    total_lines: int
    file_path: str


class PythonASTExtractor:
    """Extracts code structure using Python's ast module"""

    def extract(self, code: str, filepath: str = "") -> CodeStructure:
        """Parse Python code and extract structure"""
        try:
            tree = ast.parse(code)
            lines = code.split("\n")

            return CodeStructure(
                functions=self._extract_functions(tree),
                classes=self._extract_classes(tree),
                imports=self._extract_imports(tree),
                total_lines=len(lines),
                file_path=filepath,
            )
        except SyntaxError:
            # Return empty structure for invalid Python
            return CodeStructure([], [], [], len(code.split("\n")), filepath)

    def _extract_functions(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract all function definitions with line ranges"""
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(
                    {
                        "name": node.name,
                        "start": node.lineno,
                        "end": node.end_lineno or node.lineno,
                        "docstring": ast.get_docstring(node),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                    }
                )
        return functions

    def _extract_classes(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract all class definitions with methods"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    m.name
                    for m in node.body
                    if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                classes.append(
                    {
                        "name": node.name,
                        "start": node.lineno,
                        "end": node.end_lineno or node.lineno,
                        "docstring": ast.get_docstring(node),
                        "methods": methods,
                    }
                )
        return classes

    def _extract_imports(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extract import statements"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(
                    {
                        "line": node.lineno,
                        "module": getattr(node, "module", None),
                        "type": "from" if isinstance(node, ast.ImportFrom) else "import",
                    }
                )
        return imports

    def validate_chunk_boundaries(
        self, chunks: list[dict[str, Any]], structure: CodeStructure
    ) -> list[dict[str, Any]]:
        """
        Validate chunks against AST structure.
        Returns list of violations.
        """
        violations = []

        for func in structure.functions:
            containing = self._find_containing_chunks(func["start"], func["end"], chunks)
            if len(containing) > 1:
                violations.append(
                    {
                        "type": "function_split",
                        "name": func["name"],
                        "line_range": (func["start"], func["end"]),
                        "chunks": containing,
                    }
                )

        for cls in structure.classes:
            containing = self._find_containing_chunks(cls["start"], cls["end"], chunks)
            if len(containing) > 1:
                violations.append(
                    {
                        "type": "class_split",
                        "name": cls["name"],
                        "line_range": (cls["start"], cls["end"]),
                        "chunks": containing,
                    }
                )

        return violations

    def _find_containing_chunks(
        self, start: int, end: int, chunks: list[dict[str, Any]]
    ) -> list[int]:
        """Find which chunks contain the given line range"""
        containing = []
        for i, chunk in enumerate(chunks):
            chunk_start = chunk.get("start_line", 0)
            chunk_end = chunk.get("end_line", 0)
            # Check if chunk overlaps with [start, end]
            if not (chunk_end < start or chunk_start > end):
                containing.append(i)
        return containing
