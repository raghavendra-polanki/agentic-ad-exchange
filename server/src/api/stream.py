from fastapi import APIRouter

router = APIRouter()


@router.get("/deals")
async def stream_deals():
    """SSE stream of real-time deal state changes for the dashboard."""
    pass


@router.get("/agents")
async def stream_agents():
    """SSE stream of agent status updates for the dashboard."""
    pass
