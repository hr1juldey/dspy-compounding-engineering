"""
FastAPI endpoints for policy enforcement checks.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.application.services.check_service import CheckService

router = APIRouter(prefix="/check", tags=["check"])


class CheckRequest(BaseModel):
    """Request model for policy checks."""

    repo_root: str = Field(..., description="Root directory of repository")
    paths: list[str] | None = Field(None, description="Files or directories to check")
    auto_fix: bool = Field(False, description="Auto-fix violations")
    staged_only: bool = Field(False, description="Check only staged files")


class CheckResponse(BaseModel):
    """Response model for synchronous check."""

    success: bool
    exit_code: int
    paths: str | list[str]
    auto_fix: bool


@router.post("", response_model=CheckResponse)
async def run_check(request: CheckRequest) -> CheckResponse:
    """Run policy checks synchronously (fast operation)."""
    service = CheckService()
    result = service.check_sync(
        repo_root=request.repo_root,
        paths=request.paths,
        auto_fix=request.auto_fix,
        staged_only=request.staged_only,
    )
    return CheckResponse(**result)
