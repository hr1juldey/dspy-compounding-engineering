from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class PolicyRequest(BaseModel):
    task: str
    repo: str
    context: Optional[Dict[str, Any]] = None


class PolicyResponse(BaseModel):
    should_run: bool
    reason: str
    confidence: float
    timestamp: datetime
