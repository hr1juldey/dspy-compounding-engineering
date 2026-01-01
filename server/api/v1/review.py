"""
FastAPI endpoints for code review operations.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.application.services.review_service import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


class ReviewRequest(BaseModel):
    """Request model for code review."""

    repo_root: str = Field(..., description="Root directory of repository")
    pr_url_or_id: str = Field("latest", description="PR number, URL, or 'latest'")
    project: bool = Field(False, description="Review entire project")


class ReviewSubmitResponse(BaseModel):
    """Response model for task submission."""

    task_id: str = Field(..., description="Celery task ID")


class ReviewStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    state: str
    ready: bool
    progress: dict | None = None
    result: dict | None = None


@router.post("", response_model=ReviewSubmitResponse)
async def submit_review(request: ReviewRequest) -> ReviewSubmitResponse:
    """Submit code review task."""
    service = ReviewService()
    task_id = service.submit_review(
        repo_root=request.repo_root,
        pr_url_or_id=request.pr_url_or_id,
        project=request.project,
    )
    return ReviewSubmitResponse(task_id=task_id)


@router.get("/{task_id}", response_model=ReviewStatusResponse)
async def get_review_status(task_id: str) -> ReviewStatusResponse:
    """Get review task status and result."""
    service = ReviewService()
    status = service.get_status(task_id)
    return ReviewStatusResponse(**status)
