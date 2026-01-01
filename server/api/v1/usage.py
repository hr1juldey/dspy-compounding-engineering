from fastapi import APIRouter

from server.models.response_schemas.usage_schema import UsageResponse

# Create a single router instance for usage endpoints
router = APIRouter(prefix="", tags=["usage"])


@router.get("/usage", response_model=UsageResponse)
async def get_usage():
    """
    token usage, task counts
    """
    # In a real implementation, this would fetch actual usage data
    # from a database or other persistence layer

    raise NotImplementedError("Usage endpoint not yet implemented")
