"""
FastAPI endpoints for code analysis operations.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.application.services.analyze_service import AnalyzeService

router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    """Request model for code analysis."""

    repo_root: str = Field(..., description="Root directory of repository")
    entity: str = Field(..., description="Entity to analyze")
    analysis_type: str = Field("navigate", description="Type of analysis")
    max_depth: int = Field(2, ge=1, le=3, description="Max depth")
    change_type: str = Field("Modify", description="Change type for impact")
    save: bool = Field(True, description="Save results to file")


class AnalyzeSubmitResponse(BaseModel):
    """Response model for task submission."""

    task_id: str = Field(..., description="Celery task ID")


class AnalyzeStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    state: str
    ready: bool
    progress: dict | None = None
    result: dict | None = None


@router.post("", response_model=AnalyzeSubmitResponse)
async def submit_analyze(request: AnalyzeRequest) -> AnalyzeSubmitResponse:
    """Submit code analysis task."""
    service = AnalyzeService()
    task_id = service.submit_analyze(
        repo_root=request.repo_root,
        entity=request.entity,
        analysis_type=request.analysis_type,
        max_depth=request.max_depth,
        change_type=request.change_type,
        save=request.save,
    )
    return AnalyzeSubmitResponse(task_id=task_id)


@router.get("/{task_id}", response_model=AnalyzeStatusResponse)
async def get_analyze_status(task_id: str) -> AnalyzeStatusResponse:
    """Get analysis task status and result."""
    service = AnalyzeService()
    status = service.get_status(task_id)
    return AnalyzeStatusResponse(**status)
