"""Agent registration and profile API routes."""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from src.api.deps import get_current_agent
from src.api.stream import sse_bus
from src.schemas.agents import RegisterAgentRequest, UpdateAgentRequest
from src.store import store

router = APIRouter()


@router.post("/register")
async def register_agent(
    req: RegisterAgentRequest,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """Register a new agent on the exchange. Requires org key."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail=(
                "Missing Authorization header. "
                "Register your organization first at POST /api/v1/orgs/register, "
                "then use the org_key as Bearer token to register agents."
            ),
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not token.startswith("aax_org_"):
        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid org key format. "
                "Agent registration requires an org key (starts with 'aax_org_'). "
                "Register your organization first at POST /api/v1/orgs/register."
            ),
        )

    org = store.get_org_by_key(token)
    if org is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid org key. Organization not found.",
        )

    creds = store.register_agent(req, org_id=org.org_id)

    await sse_bus.publish("agent_status", {
        "agent_id": creds.agent_id,
        "name": req.name,
        "organization": req.organization,
        "agent_type": req.agent_type,
        "status": "online",
        "is_active": True,
        "org_id": org.org_id,
    })

    # Build agent-oriented next_actions (Moltbook-style)
    if not req.callback_url:
        next_action = {
            "action": "set_callback_url",
            "endpoint": "PATCH /api/v1/agents/me",
            "description": (
                "Register your webhook URL so AAX can push opportunities "
                "and deal updates to your agent in real time."
            ),
        }
    else:
        next_action = {
            "action": "wait_for_opportunities",
            "endpoint": None,
            "description": (
                "Opportunities matching your queries will be sent "
                "to your webhook URL."
            ),
        }

    return {
        "agent_id": creds.agent_id,
        "api_key": creds.api_key,
        "webhook_secret": creds.webhook_secret,
        "status": "registered",
        "message": (
            f"Welcome to AAX. You're registered as a {req.agent_type} agent "
            f"for {req.organization}."
        ),
        "next_actions": [next_action],
        "constraints": {
            "budget_per_deal": org.budget_per_deal_max,
            "budget_monthly_remaining": (
                org.budget_monthly_max - org.budget_monthly_spent
            ),
            "max_proposals_per_hour": 20,
        },
    }


@router.get("/me")
async def get_agent_profile(agent=Depends(get_current_agent)):
    """Get the authenticated agent's profile."""
    return agent.model_dump(mode="json")


@router.patch("/me")
async def update_agent_profile(
    req: UpdateAgentRequest,
    agent=Depends(get_current_agent),
):
    """Update agent profile (callback URL, standing queries, etc.)."""
    updates = {}
    if req.callback_url is not None:
        updates["callback_url"] = str(req.callback_url)
    if updates:
        updated = agent.model_copy(update=updates)
        store.agents[agent.agent_id] = updated

    return {"status": "updated", "agent_id": agent.agent_id}


@router.post("/managed")
async def create_managed_agent(
    config: dict,
    authorization: str | None = Header(None),
) -> dict[str, Any]:
    """Create a managed agent that runs in-process using Claude."""
    from src.engine.managed import ManagedAgentRunner

    # Resolve org
    org = None
    if authorization:
        token = authorization.removeprefix("Bearer ").strip()
        if token.startswith("aax_org_"):
            org = store.get_org_by_key(token)

    org_id = org.org_id if org else None

    # Start the managed runner
    runner = ManagedAgentRunner(org_id=org_id or "", agent_config=config)
    await runner.start()

    await sse_bus.publish("agent_status", {
        "agent_id": runner.agent_id,
        "name": config.get("name", "Managed Agent"),
        "organization": config.get("organization", "Unknown"),
        "agent_type": config.get("agent_type", "demand"),
        "status": "online",
        "is_active": True,
        "managed": True,
    })

    return {
        "agent_id": runner.agent_id,
        "status": "running",
        "managed": True,
        "message": (
            f"Managed agent '{config.get('name')}' is now running "
            f"and will autonomously participate on the exchange."
        ),
    }


@router.post("/thinking")
async def post_thinking(body: dict, agent=Depends(get_current_agent)):
    """Self-hosted agents stream their reasoning thoughts to the exchange.

    Body: {thought_chunk: str, deal_id: str}
    The exchange publishes these as SSE events for dashboard visibility.
    """
    thought = body.get("thought_chunk", "")
    deal_id = body.get("deal_id", "")

    if thought:
        await sse_bus.publish("agent_thinking", {
            "agent_id": agent.agent_id,
            "agent_name": getattr(agent, "name", "Agent"),
            "deal_id": deal_id,
            "thought_chunk": thought,
        })

    return {"status": "received"}


@router.get("")
async def list_agents():
    """List all registered agents (for dashboard)."""
    return store.get_all_agents_summary()


@router.post("/heartbeat")
async def heartbeat(agent=Depends(get_current_agent)):
    """Agent heartbeat — lets AAX know the agent is alive."""
    store.touch_agent(agent.agent_id)
    return {"status": "ok", "agent_id": agent.agent_id}


@router.get("/me/notifications")
async def poll_notifications(agent=Depends(get_current_agent)):
    """Polling fallback for agents that can't receive webhooks."""
    notifications = store.drain_notifications(agent.agent_id)
    return {"notifications": notifications, "agent_id": agent.agent_id}
