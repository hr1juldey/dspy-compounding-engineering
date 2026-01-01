"""PolicyQuestion schema for interactive init wizard."""

from pydantic import BaseModel


class PolicyQuestion(BaseModel):
    """Interactive question for policy initialization."""

    question: str
    header: str
    config_key: str
    options: list[dict]
    default_index: int = 0
    multiselect: bool = False
    depends_on: str | None = None
