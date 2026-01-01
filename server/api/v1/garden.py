"""
FastAPI endpoints for knowledge base gardening operations.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.application.services.garden_service import GardenService

router = APIRouter(prefix="/garden", tags=["garden"])


class GardenRequest(BaseModel):
    """Request model for gardening."""

    repo_root: str = Field(..., description="Root directory of repository")
    action: str = Field("consolidate", description="Action to perform")
    limit: int = Field(100, ge=1, description="Max commits to index")


class GardenSubmitResponse(BaseModel):
    """Response model for task submission."""

    task_id: str = Field(..., description="Celery task ID")


class GardenStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    state: str
    ready: bool
    progress: dict | None = None
    result: dict | None = None


@router.post("", response_model=GardenSubmitResponse)
async def submit_garden(request: GardenRequest) -> GardenSubmitResponse:
    """Submit gardening task."""
    service = GardenService()
    task_id = service.submit_garden(
        repo_root=request.repo_root, action=request.action, limit=request.limit
    )
    return GardenSubmitResponse(task_id=task_id)


@router.get("/{task_id}", response_model=GardenStatusResponse)
async def get_garden_status(task_id: str) -> GardenStatusResponse:
    """Get gardening task status and result."""
    service = GardenService()
    status = service.get_status(task_id)
    return GardenStatusResponse(**status)
