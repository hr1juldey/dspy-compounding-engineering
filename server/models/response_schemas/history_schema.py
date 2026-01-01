from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TaskHistory(BaseModel):
    task_id: str
    task_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    description: str
    repo: str


class SweepHistory(BaseModel):
    sweep_id: str
    repo: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    findings_count: int


class HistoryResponse(BaseModel):
    recent_tasks: List[TaskHistory]
    recent_sweeps: List[SweepHistory]
