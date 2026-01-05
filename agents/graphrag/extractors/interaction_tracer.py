"""
Interaction Tracer (Dimension 4).

Traces data flow between caller and callee using AST + DSPy.
"""

import ast
from typing import cast

import dspy

from agents.graphrag.schema import InteractionFlow


class DataFlowTracerSignature(dspy.Signature):
    """
    Trace parameter flow between two entities.

    Analyzes call site to determine parameter mapping.
    """

    caller_name: str = dspy.InputField(desc="Calling entity")
    callee_name: str = dspy.InputField(desc="Called entity")
    call_site_code: str = dspy.InputField(desc="Code snippet of function call")
    caller_params: str = dspy.InputField(desc="Caller's parameters (JSON)")
    callee_params: str = dspy.InputField(desc="Callee's parameters (JSON)")

    parameter_mapping: dict[str, str] = dspy.OutputField(
        desc="Mapping from caller variables to callee parameters"
    )
    data_description: str = dspy.OutputField(desc="Human-readable description of what data flows")


class DataFlowTracer(dspy.Module):
    """
    Traces data flow using AST + DSPy.

    Workflow:
    1. AST parse to find call site
    2. Extract argument mapping
    3. Use DSPy to semantically describe the flow
    """

    def __init__(self):
        super().__init__()
        self.tracer = dspy.Predict(DataFlowTracerSignature)

    def trace_flow(
        self, caller_name: str, callee_name: str, caller_code: str, callee_params_json: str
    ) -> InteractionFlow | None:
        """
        Trace parameter flow from caller to callee.

        Returns:
            InteractionFlow or None if no call site found
        """
        call_site = self._find_call_site(caller_code, callee_name)

        if not call_site:
            return None

        result = cast(
            dspy.Prediction,
            self.tracer(
                caller_name=caller_name,
                callee_name=callee_name,
                call_site_code=call_site,
                caller_params="",
                callee_params=callee_params_json,
            ),
        )

        return InteractionFlow(
            from_entity=caller_name,
            to_entity=callee_name,
            parameter_mapping=result.parameter_mapping,
            data_description=result.data_description,
        )

    def _find_call_site(self, source_code: str, callee_name: str) -> str | None:
        """Find the line where callee is called."""
        try:
            tree = ast.parse(source_code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == callee_name:
                        return ast.unparse(node)
                    elif isinstance(node.func, ast.Attribute) and node.func.attr == callee_name:
                        return ast.unparse(node)

            return None
        except Exception:
            return None
