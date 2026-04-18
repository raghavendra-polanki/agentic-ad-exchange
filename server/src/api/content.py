"""Content submission and validation API routes."""

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_current_agent
from src.engine.orchestrator import handle_content_submission

router = APIRouter()


@router.post("/{deal_id}")
async def submit_content(
    deal_id: str,
    submission: dict,
    agent=Depends(get_current_agent),
):
    """Supply agent submits generated content for validation."""
    result = await handle_content_submission(deal_id, submission, agent)
    if result is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return result
