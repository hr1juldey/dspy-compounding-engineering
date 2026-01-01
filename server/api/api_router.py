from fastapi import APIRouter

from server.api.v1 import health_router, history_router, policy_router, usage_router

# Create a main API router that includes all v1 endpoints
api_router = APIRouter()

# Include all v1 routers under the /v1 prefix
api_router.include_router(health_router, prefix="/v1", tags=["health"])
api_router.include_router(usage_router, prefix="/v1", tags=["usage"])
api_router.include_router(history_router, prefix="/v1", tags=["history"])
api_router.include_router(policy_router, prefix="/v1", tags=["policy"])
