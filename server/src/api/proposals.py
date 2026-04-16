"""Proposal response API routes."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_current_agent
from src.engine.orchestrator import handle_respond_to_proposal
from src.schemas.proposals import ProposalResponse

router = APIRouter()


@router.post("/{proposal_id}/respond")
async def respond_to_proposal(
    proposal_id: str,
    response: ProposalResponse,
    agent=Depends(get_current_agent),
):
    """Supply agent responds to a proposal (accept/counter/reject)."""
    result = await handle_respond_to_proposal(agent, proposal_id, response)
    if result is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return result
