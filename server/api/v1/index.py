"""
FastAPI endpoints for codebase indexing operations.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.application.services.index_codebase_service import (
    IndexCodebaseService,
)

router = APIRouter(prefix="/index", tags=["index"])


class IndexRequest(BaseModel):
    """Request model for codebase indexing."""

    repo_root: str = Field(..., description="Root directory of repository")
    recreate: bool = Field(False, description="Force recreation of vector collection")
    with_graphrag: bool = Field(False, description="Enable GraphRAG entity extraction")


class IndexSubmitResponse(BaseModel):
    """Response model for task submission."""

    task_id: str = Field(..., description="Celery task ID")


class IndexStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    state: str
    ready: bool
    progress: dict | None = None
    result: dict | None = None


@router.post("", response_model=IndexSubmitResponse)
async def submit_index(request: IndexRequest) -> IndexSubmitResponse:
    """Submit codebase indexing task."""
    service = IndexCodebaseService()
    task_id = service.submit_indexing(
        repo_root=request.repo_root,
        recreate=request.recreate,
        with_graphrag=request.with_graphrag,
    )
    return IndexSubmitResponse(task_id=task_id)
