from fastapi import APIRouter

from server.models.response_schemas.policy_schema import PolicyRequest, PolicyResponse

# Create a single router instance for policy endpoints
router = APIRouter(prefix="", tags=["policy"])


@router.post("/policy", response_model=PolicyResponse)
async def should_we_run(request: PolicyRequest):
    """
    SHOULD_WE_RUN(task, repo) decision endpoint
    """
    # In a real implementation, this would contain logic to determine
    # if a task should run based on various factors like:
    # - repository state
    # - task type
    # - current system load
    # - previous task outcomes
    # - knowledge base insights

    raise NotImplementedError("Policy endpoint not yet implemented")
