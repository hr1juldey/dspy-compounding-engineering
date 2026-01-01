"""Protocol registration system."""

from typing import Type

from utils.policy.protocols.base import (
    PolicyProtocol,
    SemanticProtocol,
    StaticProtocol,
)

_STATIC_PROTOCOLS: list[Type[StaticProtocol]] = []
_SEMANTIC_PROTOCOLS: list[Type[SemanticProtocol]] = []


def register_static(protocol_cls: Type[StaticProtocol]):
    """Register a static protocol."""
    _STATIC_PROTOCOLS.append(protocol_cls)
    return protocol_cls


def register_semantic(protocol_cls: Type[SemanticProtocol]):
    """Register a semantic protocol."""
    _SEMANTIC_PROTOCOLS.append(protocol_cls)
    return protocol_cls


def get_all_protocols() -> list[Type[PolicyProtocol]]:
    """Get all registered protocols."""
    return _STATIC_PROTOCOLS + _SEMANTIC_PROTOCOLS


def get_static_protocols() -> list[Type[StaticProtocol]]:
    """Get static protocols only."""
    return _STATIC_PROTOCOLS.copy()


def get_semantic_protocols() -> list[Type[SemanticProtocol]]:
    """Get semantic protocols only."""
    return _SEMANTIC_PROTOCOLS.copy()
