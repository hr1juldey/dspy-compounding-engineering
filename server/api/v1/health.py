import time

from fastapi import APIRouter

from server.models.response_schemas.health_schema import HealthStatus

# Create a single router instance for health endpoints
router = APIRouter(prefix="", tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    GET /health
    Check the health status of the server
    """
    start_time = time.time()

    return HealthStatus(
        status="healthy",
        timestamp=start_time,
        uptime=start_time,  # In a real app, this would track actual uptime
    )
