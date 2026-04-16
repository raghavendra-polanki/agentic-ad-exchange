"""Opportunity signaling and proposal submission API routes."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_current_agent
from src.engine.orchestrator import handle_signal_opportunity, handle_submit_proposal
from src.schemas.opportunities import OpportunitySignal
from src.schemas.proposals import Proposal

router = APIRouter()


@router.post("/")
async def signal_opportunity(
    signal: OpportunitySignal,
    agent=Depends(get_current_agent),
):
    """Supply agent signals a new opportunity on the exchange."""
    return await handle_signal_opportunity(agent, signal)


@router.post("/{opportunity_id}/propose")
async def submit_proposal(
    opportunity_id: str,
    proposal: Proposal,
    agent=Depends(get_current_agent),
):
    """Demand agent submits a proposal for an opportunity."""
    result = await handle_submit_proposal(agent, opportunity_id, proposal)
    if result is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return result


@router.post("/{opportunity_id}/pass")
async def pass_opportunity(
    opportunity_id: str,
    agent=Depends(get_current_agent),
):
    """Demand agent declines an opportunity."""
    return {"status": "passed", "opportunity_id": opportunity_id, "agent_id": agent.agent_id}
