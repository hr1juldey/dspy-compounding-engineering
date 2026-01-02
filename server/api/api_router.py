"""
Main API router that combines all v1 endpoints.
"""

from fastapi import APIRouter

from server.api.v1.analyze import router as analyze_router
from server.api.v1.check import router as check_router
from server.api.v1.config import router as config_router
from server.api.v1.garden import router as garden_router
from server.api.v1.index import router as index_router
from server.api.v1.plan import router as plan_router
from server.api.v1.review import router as review_router
from server.api.v1.websockets import router as websocket_router
from server.api.v1.work import router as work_router

# Create main API router
api_router = APIRouter()

# Include all v1 routers under /v1 prefix
api_router.include_router(analyze_router, prefix="/v1")
api_router.include_router(work_router, prefix="/v1")
api_router.include_router(review_router, prefix="/v1")
api_router.include_router(garden_router, prefix="/v1")
api_router.include_router(plan_router, prefix="/v1")
api_router.include_router(check_router, prefix="/v1")
api_router.include_router(config_router, prefix="/v1")
api_router.include_router(index_router, prefix="/v1")

# WebSocket routes (no /v1 prefix)
api_router.include_router(websocket_router)
