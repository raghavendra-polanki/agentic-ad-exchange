"""Deal status and audit trail API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.engine.orchestrator import reject_paused_deal, resume_approved_deal
from src.store import store

router = APIRouter()


class RejectDealRequest(BaseModel):
    reason: str | None = None


@router.get("/stats")
async def get_stats():
    """Summary statistics for the dashboard."""
    deals = list(store.deals.values())
    terminal = {"deal_rejected", "deal_expired", "completed", "conflict_blocked"}
    active = [d for d in deals if d.state not in terminal]
    agreed = [d for d in deals if d.state in ("deal_agreed", "completed")]
    total = max(len(deals), 1)
    return {
        "total_deals": len(deals),
        "active_deals": len(active),
        "completed_deals": len(agreed),
        "conflict_rate": round(
            len([d for d in deals if d.state == "deal_rejected"]) / total * 100,
        ),
    }


@router.get("")
async def list_deals():
    """List all deals (for dashboard)."""
    return [d.model_dump(mode="json") for d in store.deals.values()]


@router.get("/{deal_id}")
async def get_deal(deal_id: str):
    """Get deal status and details."""
    deal = store.deals.get(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    result = deal.model_dump(mode="json")
    result["agreement"] = store.deal_results.get(deal_id)
    return result


@router.get("/{deal_id}/trace")
async def get_deal_trace(deal_id: str):
    """Get full audit trail for a deal."""
    deal = store.deals.get(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    events = store.deal_events.get(deal_id, [])
    proposals = [
        p.model_dump(mode="json")
        for p in store.proposals.values()
        if p.opportunity_id == deal.opportunity_id
    ]

    # Include opportunity image and scene analysis if available
    opp = store.opportunities.get(deal.opportunity_id)
    opportunity_data = None
    if opp:
        opportunity_data = {
            "image_url": opp.signal.image_url,
            "image_id": opp.signal.image_id,
            "scene_analysis": opp.scene_analysis,
        }

    return {
        "deal_id": deal_id,
        "deal": deal.model_dump(mode="json"),
        "events": events,
        "proposals": proposals,
        "agreement": store.deal_results.get(deal_id),
        "opportunity": opportunity_data,
    }


@router.post("/{deal_id}/approve")
async def approve_deal(deal_id: str):
    """Human approves a deal paused in AWAITING_HUMAN_APPROVAL.

    Resumes the deferred action (typically a proposal submission) and
    lets the deal continue through the normal flow.
    """
    if deal_id not in store.deals:
        raise HTTPException(status_code=404, detail="Deal not found")
    result = await resume_approved_deal(deal_id)
    if result is None:
        raise HTTPException(
            status_code=409,
            detail="Deal is not in AWAITING_HUMAN_APPROVAL state",
        )
    return result


@router.post("/{deal_id}/reject")
async def reject_deal(deal_id: str, req: RejectDealRequest | None = None):
    """Human rejects a paused deal — deal moves to DEAL_REJECTED."""
    if deal_id not in store.deals:
        raise HTTPException(status_code=404, detail="Deal not found")
    reason = req.reason if req else None
    result = await reject_paused_deal(deal_id, reason)
    if result is None:
        raise HTTPException(
            status_code=409,
            detail="Deal is not in AWAITING_HUMAN_APPROVAL state",
        )
    return result
