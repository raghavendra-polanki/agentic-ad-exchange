"""Deal status and audit trail API routes."""

from fastapi import APIRouter, HTTPException

from src.store import store

router = APIRouter()


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

    return {
        "deal_id": deal_id,
        "deal": deal.model_dump(mode="json"),
        "events": events,
        "proposals": proposals,
        "agreement": store.deal_results.get(deal_id),
    }
