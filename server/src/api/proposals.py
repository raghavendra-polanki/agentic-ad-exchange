from fastapi import APIRouter

router = APIRouter()


@router.post("/{proposal_id}/respond")
async def respond_to_proposal(proposal_id: str):
    """Supply agent responds to a proposal (accept/counter/reject)."""
    pass
