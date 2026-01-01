"""
FastAPI endpoints for work execution operations.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.application.services.work_service import WorkService

router = APIRouter(prefix="/work", tags=["work"])


class WorkRequest(BaseModel):
    """Request model for work execution."""

    repo_root: str = Field(..., description="Root directory of repository")
    pattern: str | None = Field(None, description="Todo ID, plan file, or pattern")
    dry_run: bool = Field(False, description="Dry run mode")
    parallel: bool = Field(True, description="Execute in parallel")
    max_workers: int = Field(3, ge=1, le=10, description="Max parallel workers")
    in_place: bool = Field(True, description="Apply changes in-place")


class WorkSubmitResponse(BaseModel):
    """Response model for task submission."""

    task_id: str = Field(..., description="Celery task ID")


class WorkStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    state: str
    ready: bool
    progress: dict | None = None
    result: dict | None = None


@router.post("", response_model=WorkSubmitResponse)
async def submit_work(request: WorkRequest) -> WorkSubmitResponse:
    """Submit work execution task."""
    service = WorkService()
    task_id = service.submit_work(
        repo_root=request.repo_root,
        pattern=request.pattern,
        dry_run=request.dry_run,
        parallel=request.parallel,
        max_workers=request.max_workers,
        in_place=request.in_place,
    )
    return WorkSubmitResponse(task_id=task_id)


@router.get("/{task_id}", response_model=WorkStatusResponse)
async def get_work_status(task_id: str) -> WorkStatusResponse:
    """Get work task status and result."""
    service = WorkService()
    status = service.get_status(task_id)
    return WorkStatusResponse(**status)
