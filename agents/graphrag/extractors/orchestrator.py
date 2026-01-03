"""
Five-Dimension Extraction Orchestrator.

Combines all extractors to build complete EntityDetails.
"""

import ast

from agents.graphrag.extractors.function_io_extractor import ParameterExtractor
from agents.graphrag.extractors.interaction_tracer import DataFlowTracer
from agents.graphrag.extractors.temporal_extractor import TemporalExtractor
from agents.graphrag.schema import EntityDetails, FunctionIO, ParameterInfo
from utils.knowledge.graphrag.graph_store import GraphStore


class FiveDimensionExtractor:
    """
    Extracts all 5 dimensions of code for an entity.

    Workflow:
    1. Extract parameter schema (AST) - Dimension 3
    2. Extract docstring (AST) - Dimension 3
    3. Extract git history (GitService) - Dimension 5
    4. (Data flow traced separately for relationships) - Dimension 4
    """

    def __init__(self, graph_store: GraphStore):
        self.graph_store = graph_store
        self.param_extractor = ParameterExtractor()
        self.temporal_extractor = TemporalExtractor()
        self.dataflow_tracer = DataFlowTracer()

    def extract_full_entity(
        self,
        entity_name: str,
        entity_type: str,
        source_code: str,
        file_path: str,
        line_start: int,
    ) -> EntityDetails:
        """
        Extract all 5 dimensions for an entity.

        Returns enhanced EntityDetails.
        """
        # Dimension 3: Parameter Schema (AST extraction)
        parameters, return_type = self.param_extractor.extract_from_code(source_code, entity_name)

        # Dimension 3: Docstring (AST extraction)
        docstring = self._extract_docstring(source_code, entity_name)

        # Dimension 3: Build FunctionIO
        function_io = None
        if parameters or return_type:
            function_io = FunctionIO(
                parameters=parameters,
                return_type=return_type,
                processing_description=None,
                key_operations=[],
            )

        # Dimension 5: Git history (temporal)
        git_history = self.temporal_extractor.extract_history(entity_name, file_path)

        return EntityDetails(
            # Dimension 1: Location
            name=entity_name,
            type=entity_type,
            file_path=file_path,
            line_start=line_start,
            # Dimension 3: Function (I/O)
            signature=self._build_signature_string(entity_name, parameters, return_type),
            function_io=function_io,
            docstring=docstring,
            # Dimension 5: Temporal Change
            git_history=git_history,
        )

    def _extract_docstring(self, source_code: str, entity_name: str) -> str | None:
        """Extract docstring from source code."""
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == entity_name:
                    return ast.get_docstring(node)
            return None
        except Exception:
            return None

    def _build_signature_string(
        self, name: str, params: list[ParameterInfo], return_type: str | None
    ) -> str:
        """Build signature string from structured parameters."""
        param_strs = []
        for p in params:
            if p.type_hint:
                param_strs.append(f"{p.name}: {p.type_hint}")
            else:
                param_strs.append(p.name)

        sig = f"{name}({', '.join(param_strs)})"
        if return_type:
            sig += f" -> {return_type}"

        return sig
