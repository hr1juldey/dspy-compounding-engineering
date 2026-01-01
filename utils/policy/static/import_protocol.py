"""Absolute import validator."""

import ast
from pathlib import Path

from utils.policy.protocols.base import StaticProtocol
from utils.policy.protocols.questions import PolicyQuestion
from utils.policy.violations import Severity, Violation


class ImportProtocol(StaticProtocol):
    """Validates no relative imports."""

    def get_rule_id(self) -> str:
        return "IMPORT001"

    def get_questions(self) -> list[PolicyQuestion]:
        return [
            PolicyQuestion(
                question="Should relative imports be allowed in your project?",
                header="Import Style",
                config_key="allow_relative_imports",
                options=[
                    {
                        "label": "Absolute only",
                        "description": "from project.utils import helper (recommended)",
                        "value": False,
                    },
                    {
                        "label": "Allow relative",
                        "description": "from ..utils import helper",
                        "value": True,
                    },
                ],
            )
        ]

    def check(self, file_path: Path) -> list[Violation]:
        """Check for relative imports."""
        config = self.context.config or {}
        if config.get("allow_relative_imports", False):
            return []

        violations = []
        try:
            source = file_path.read_text()
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level > 0:
                    violations.append(
                        Violation(
                            file_path=str(file_path),
                            line_number=node.lineno,
                            rule_id=self.get_rule_id(),
                            severity=Severity(config.get("relative_import_severity", "ERROR")),
                            message=f"Relative import detected: level={node.level}",
                            suggestion="Use absolute import rooted at project top-level",
                            auto_fixable=False,
                        )
                    )
        except SyntaxError:
            pass

        return violations
