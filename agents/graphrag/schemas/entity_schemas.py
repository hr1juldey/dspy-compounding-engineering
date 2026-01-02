"""Pydantic schemas for GraphRAG entities and function I/O."""

from pydantic import BaseModel


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
