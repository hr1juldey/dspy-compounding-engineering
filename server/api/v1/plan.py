"""
FastAPI endpoints for project plan generation operations.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.application.services.plan_service import PlanService

router = APIRouter(prefix="/plan", tags=["plan"])


class PlanRequest(BaseModel):
    """Request model for plan generation."""

    repo_root: str = Field(..., description="Root directory of repository")
    feature_description: str = Field(..., description="Feature description")


class PlanSubmitResponse(BaseModel):
    """Response model for task submission."""

    task_id: str = Field(..., description="Celery task ID")


class PlanStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    state: str
    ready: bool
    progress: dict | None = None
    result: dict | None = None


@router.post("", response_model=PlanSubmitResponse)
async def submit_plan(request: PlanRequest) -> PlanSubmitResponse:
    """Submit plan generation task."""
    service = PlanService()
    task_id = service.submit_plan(
        repo_root=request.repo_root, feature_description=request.feature_description
    )
    return PlanSubmitResponse(task_id=task_id)


@router.get("/{task_id}", response_model=PlanStatusResponse)
async def get_plan_status(task_id: str) -> PlanStatusResponse:
    """Get plan task status and result."""
    service = PlanService()
    status = service.get_status(task_id)
    return PlanStatusResponse(**status)
