"""Agent registration and profile API routes."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_current_agent
from src.api.stream import sse_bus
from src.schemas.agents import AgentCredentials, RegisterAgentRequest, UpdateAgentRequest
from src.store import store

router = APIRouter()


@router.post("/register")
async def register_agent(req: RegisterAgentRequest) -> AgentCredentials:
    """Register a new supply or demand agent on the exchange."""
    creds = store.register_agent(req)

    await sse_bus.publish("agent_status", {
        "agent_id": creds.agent_id,
        "name": req.name,
        "organization": req.organization,
        "agent_type": req.agent_type,
        "status": "online",
        "is_active": True,
    })

    return creds


@router.get("/me")
async def get_agent_profile(agent=Depends(get_current_agent)):
    return agent.model_dump(mode="json")


@router.patch("/me")
async def update_agent_profile(
    req: UpdateAgentRequest,
    agent=Depends(get_current_agent),
):

    updates = {}
    if req.callback_url is not None:
        updates["callback_url"] = str(req.callback_url)
    if updates:
        updated = agent.model_copy(update=updates)
        store.agents[agent.agent_id] = updated

    return {"status": "updated", "agent_id": agent.agent_id}


@router.get("")
async def list_agents():
    """List all registered agents (for dashboard)."""
    return store.get_all_agents_summary()


@router.get("/{agent_id}/notifications")
async def poll_notifications(agent_id: str):
    """Polling fallback for agents that can't receive webhooks."""
    agent = store.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"notifications": [], "agent_id": agent_id}
