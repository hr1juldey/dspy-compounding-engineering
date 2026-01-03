"""
Entity extraction package for GraphRAG.

Exports main components for entity extraction and relation building.
"""

from utils.knowledge.graphrag.entities.entity_model import Entity, generate_entity_id
from utils.knowledge.graphrag.entities.extractor import EntityExtractor

__all__ = ["Entity", "EntityExtractor", "generate_entity_id"]
