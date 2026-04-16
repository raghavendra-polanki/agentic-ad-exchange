"""Shared FastAPI dependencies for API routes."""

from fastapi import Header, HTTPException

from src.schemas.agents import DemandAgentProfile, SupplyAgentProfile
from src.store import store


def get_current_agent(
    authorization: str | None = Header(None),
) -> SupplyAgentProfile | DemandAgentProfile:
    """Extract and validate the agent from the Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    api_key = authorization.replace("Bearer ", "")
    agent = store.get_agent_by_key(api_key)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return agent
