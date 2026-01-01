"""
Pydantic schemas for GraphRAG agent outputs.

"Half-done answers" - structured findings for user confirmation.
"""

from pydantic import BaseModel, Field


# Dimension 3: Function I/O
class ParameterInfo(BaseModel):
    """Input/output parameter information."""

    name: str
    type_hint: str | None = None
    default_value: str | None = None
    is_variadic: bool = False
    position: int


class FunctionIO(BaseModel):
    """Function with inputs and outputs (Dimension 3)."""

    parameters: list[ParameterInfo] = []
    return_type: str | None = None
    processing_description: str | None = None
    key_operations: list[str] = []


# Dimension 4: Interaction
class InteractionFlow(BaseModel):
    """Data and control flow (Dimension 4)."""

    from_entity: str
    to_entity: str
    parameter_mapping: dict[str, str] = {}
    data_description: str = ""
    control_type: str = "sequential"
    condition: str | None = None


# Dimension 5: Temporal Change
class CodeChange(BaseModel):
    """Single code change event."""

    commit_sha: str
    author: str
    date: str
    message: str
    change_type: str
    lines_added: int
    lines_removed: int


class GitHistory(BaseModel):
    """Temporal evolution (Dimension 5)."""

    entity_name: str
    file_path: str
    first_seen: CodeChange
    last_modified: CodeChange
    total_commits: int
    recent_changes: list[CodeChange] = []
    change_frequency: str = "unknown"
    stability: str = "unknown"


class EntityDetails(BaseModel):
    """Entity with all 5 dimensions."""

    # Dimension 1: Location
    name: str
    type: str  # Function, Class, Method, Import, Module
    file_path: str
    line_start: int
    line_end: int | None = None
    module_path: str | None = None

    # Dimension 2: Relation (in relationships dict)

    # Dimension 3: Function (I/O)
    signature: str | None = None  # Backward compatible
    function_io: FunctionIO | None = None
    docstring: str | None = None

    # Dimension 4: Interaction (in relationships)

    # Dimension 5: Temporal Change
    git_history: GitHistory | None = None


class RelatedEntity(BaseModel):
    """Related entity (Dimensions 2 & 4)."""

    name: str
    type: str
    file_path: str
    # Dimension 2: Relation
    relation_type: str  # calls, called_by, imports, inherits
    # Dimension 4: Interaction
    interaction_flow: InteractionFlow | None = None
    context: str | None = None


class CodeNavigationReport(BaseModel):
    """Output from CodeNavigatorAgent."""

    summary: str = Field(description="e.g., 'Found 12 callers across 5 files'")
    entity_details: EntityDetails
    relationships: dict[str, list[RelatedEntity]]  # {calls: [...], called_by: [...]}
    impact_scope: str  # Local|Module|System-wide
    next_actions: list[str]  # User options


class EntityHub(BaseModel):
    """Hub entity with PageRank score."""

    entity_id: str
    name: str
    type: str
    pagerank: float
    file_path: str


class ClusterInfo(BaseModel):
    """Module cluster information."""

    cluster_id: int
    size: int  # Number of entities
    top_entities: list[str]  # Entity names
    files: list[str]  # Files in cluster


class ArchitectureReport(BaseModel):
    """Output from ArchitectureMapperAgent."""

    summary: str
    hubs: list[EntityHub]  # Top PageRank entities
    clusters: dict[int, ClusterInfo]  # Module boundaries
    layer_analysis: dict[str, list[str]]  # {Presentation: [...], Application: [...]}
    bottlenecks: list[str]  # High fanout entities


class ImpactReport(BaseModel):
    """Output from ImpactAnalyzerAgent."""

    summary: str  # e.g., "23 entities across 8 files affected"
    direct_dependents: list[EntityDetails]  # 1st degree
    indirect_dependents: list[EntityDetails]  # 2nd-3rd degree
    critical_paths: list[list[str]]  # Paths to critical entities
    blast_radius: dict[str, int]  # {files: 8, functions: 15, classes: 8}
    risk_assessment: str  # Low|Medium|High|Critical
    recommended_approach: str


class CycleInfo(BaseModel):
    """Circular dependency information."""

    cycle_path: list[str]  # A → B → C → A
    cycle_type: str  # Import|Call|Inheritance


class DependencyReport(BaseModel):
    """Output from DependencyTracerAgent."""

    summary: str  # e.g., "Found 2 paths, 1 circular dependency"
    shortest_path: list[EntityDetails] | None
    all_paths: list[list[EntityDetails]]
    circular_dependencies: list[CycleInfo]
    coupling_metrics: dict[str, int]  # {import_depth: 4, fanout: 12}
    recommendations: list[str]
