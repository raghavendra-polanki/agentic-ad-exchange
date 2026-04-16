from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register_agent():
    """Register a new supply or demand agent on the exchange."""
    pass


@router.get("/me")
async def get_agent_profile():
    """Get the authenticated agent's profile."""
    pass


@router.patch("/me")
async def update_agent_profile():
    """Update agent profile (callback URL, standing queries, etc.)."""
    pass


@router.get("/{agent_id}/notifications")
async def poll_notifications(agent_id: str):
    """Polling fallback for agents that can't receive webhooks."""
    pass
