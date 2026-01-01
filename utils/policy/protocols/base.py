"""Base protocol classes for extensible policy validation."""

from abc import abstractmethod
from pathlib import Path
from typing import Protocol

from utils.policy.protocols.questions import PolicyQuestion
from utils.policy.violations import Violation


class PolicyProtocol(Protocol):
    """Base protocol that all policy validators must implement."""

    @abstractmethod
    def check(self, file_path: Path) -> list[Violation]:
        """Check file against policy."""
        ...

    @abstractmethod
    def get_rule_id(self) -> str:
        """Return unique rule identifier."""
        ...

    @abstractmethod
    def get_questions(self) -> list[PolicyQuestion]:
        """Convert policy into interactive questions for init wizard."""
        ...


class StaticProtocol(PolicyProtocol):
    """Protocol for fast AST-based validators."""

    def __init__(self, context):
        self.context = context


class SemanticProtocol(PolicyProtocol):
    """Protocol for DSPy-based intelligent validators."""

    def __init__(self, context):
        self.context = context

    @abstractmethod
    def get_signature_class(self) -> type:
        """Return DSPy signature class for this validator."""
        ...
