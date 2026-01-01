from fastapi import APIRouter

from server.models.response_schemas.history_schema import HistoryResponse

# Create a single router instance for history endpoints
router = APIRouter(prefix="", tags=["history"])


@router.get("/history", response_model=HistoryResponse)
async def get_history():
    """
    completed tasks, past sweeps
    """
    raise NotImplementedError("History endpoint not yet implemented")
