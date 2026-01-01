from typing import List, Optional

from pydantic import BaseModel


class TokenUsage(BaseModel):
    model: str
    tokens_used: int
    tokens_limit: Optional[int] = None


class TaskCount(BaseModel):
    task_type: str
    count: int


class UsageResponse(BaseModel):
    token_usage: List[TokenUsage]
    task_counts: List[TaskCount]
    total_tokens_used: int
    total_tasks_completed: int
