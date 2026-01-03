"""
CodeNavigatorAgent: Entity relationship navigation.

Capabilities:
- Find all callers/callees of a function
- Trace import dependencies
- Map class hierarchies
- List methods by class
"""

import dspy

from agents.graphrag.schema import (
    CodeNavigationReport,
    EntityDetails,
    RelatedEntity,
)
from server.config import get_project_hash, registry
from utils.knowledge.embeddings_dspy import DSPyEmbeddingProvider as EmbeddingProvider
from utils.knowledge.graph_store import GraphStore
from utils.memory.module import MemoryPredict


class CodeNavigatorSignature(dspy.Signature):
    """Navigate codebase structure by exploring entity relationships and dependencies.

    INPUTS:
    - query: Name of the entity to explore (function, class, method name) or a navigation
      query (e.g., "find callers of process_data")
    - entity_type: Optional filter to narrow search to specific entity type. Options:
      * "Function": Standalone functions
      * "Class": Class definitions
      * "Method": Class methods
      * "Import": Import statements
      * "Module": Python modules
      * "" (empty): Search all entity types
    - max_depth: How many relationship hops to explore (1-3):
      * 1: Direct relationships only (immediate callers/callees)
      * 2: Two-hop relationships (callers of callers)
      * 3: Three-hop relationships (full dependency chain)

    OUTPUT:
    You must return a CodeNavigationReport object containing:
    - summary: One-line summary of navigation results
      (e.g., "Found 12 callers across 5 files")
    - entity_details: EntityDetails object for the target entity with:
      * name: Entity name
      * type: Entity type (Function, Class, Method, Import, Module)
      * file_path: File location
      * line_start: Starting line number
      * signature: Function/method signature (if applicable)
    - relationships: Dictionary mapping relationship types to lists of RelatedEntity objects.
      Common relationship types:
      * "calls": Entities called by this entity
      * "called_by": Entities that call this entity
      * "imports": Modules imported by this entity
      * "imported_by": Modules that import this entity
      * "inherits": Classes this class inherits from
      * "inherited_by": Classes that inherit from this class
      Each RelatedEntity contains: name, type, file_path, relation_type
    - impact_scope: Scope of the entity's influence:
      * "Local (1 file)": Entity only used within its own file
      * "Module (2-3 files)": Entity used across a few related files
      * "System-wide (N files)": Entity used broadly across the system
    - next_actions: List of suggested follow-up exploration actions
      (e.g., "Explore calls", "Explore called_by", "View source code")

    TASK INSTRUCTIONS:
    - Find the target entity using the query string
    - Retrieve relationships up to max_depth hops
    - Group relationships by type (calls, called_by, imports, etc.)
    - Assess impact scope based on file spread
    - Return pre-analyzed structure (relationships, not raw code)
    - Suggest logical next navigation steps
    """

    query: str = dspy.InputField(desc="Entity name or navigation query")
    entity_type: str = dspy.InputField(desc="Function|Class|Method|Import|Module", default="")
    max_depth: int = dspy.InputField(default=2, desc="Relationship depth (1-3)")

    navigation_result: CodeNavigationReport = dspy.OutputField(
        desc="Structured navigation results with options"
    )


class CodeNavigatorModule(dspy.Module):
    """
    CodeNavigator module with graph store + memory.

    Pattern: Signature + Module + MemoryPredict
    """

    def __init__(self):
        super().__init__()

        # Initialize graph store
        qdrant = registry.get_qdrant_client()
        project_hash = get_project_hash()
        self.graph_store = GraphStore(qdrant, EmbeddingProvider(), f"entities_{project_hash}")

        # Memory-augmented predictor
        self.navigator = MemoryPredict(CodeNavigatorSignature, agent_name="code_navigator")

    def forward(self, query: str, entity_type: str = "", max_depth: int = 2):
        # Search for entity
        entities = self.graph_store.query_entities(query, limit=5, entity_type=entity_type)

        if not entities:
            return CodeNavigationReport(
                summary=f"No entities found for '{query}'",
                entity_details=EntityDetails(
                    name=query, type="Unknown", file_path="", line_start=0
                ),
                relationships={},
                impact_scope="None",
                next_actions=["Try different search term"],
            )

        # Use first match
        entity = entities[0]

        # Get relationships
        neighbors = self.graph_store.query_neighbors(entity.id, limit=50)

        # Group by relation type
        relationships: dict[str, list[RelatedEntity]] = {}
        for neighbor in neighbors:
            # Determine relation type from entity.relations
            relation_types = [
                rel_type
                for rel_type, target_ids in entity.relations.items()
                if neighbor.id in target_ids
            ]

            for rel_type in relation_types or ["related_to"]:
                if rel_type not in relationships:
                    relationships[rel_type] = []

                relationships[rel_type].append(
                    RelatedEntity(
                        name=neighbor.name,
                        type=neighbor.type,
                        file_path=neighbor.file_path,
                        relation_type=rel_type,
                    )
                )

        # Determine impact scope
        unique_files = {neighbor.file_path for neighbor in neighbors}
        if len(unique_files) <= 1:
            scope = "Local (1 file)"
        elif len(unique_files) <= 3:
            scope = "Module (2-3 files)"
        else:
            scope = f"System-wide ({len(unique_files)} files)"

        return CodeNavigationReport(
            summary=f"Found {len(neighbors)} related entities across {len(unique_files)} files",
            entity_details=EntityDetails(
                name=entity.name,
                type=entity.type,
                file_path=entity.file_path,
                line_start=entity.line_start,
                signature=entity.properties.get("signature"),
            ),
            relationships=relationships,
            impact_scope=scope,
            next_actions=[f"Explore {rel_type}" for rel_type in relationships.keys()],
        )
