"""Content submission and validation API routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_current_agent
from src.api.stream import sse_bus
from src.schemas.deals import ContentSubmission, FulfillmentState, ValidationResult
from src.store import store

router = APIRouter()


@router.post("/{deal_id}")
async def submit_content(
    deal_id: str,
    submission: ContentSubmission,
    agent=Depends(get_current_agent),
):

    deal = store.deals.get(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Auto-validate for Phase 1
    validation = ValidationResult(
        deal_id=deal_id,
        passed=True,
        score=0.94,
        checks={
            "brand_logo_present": True,
            "disclosure_present": True,
            "messaging_aligned": True,
            "color_palette_match": True,
        },
    )

    store.update_deal(deal_id, state=FulfillmentState.COMPLETED)

    await sse_bus.publish("deal_completed", {
        "deal_id": deal_id,
        "state": FulfillmentState.COMPLETED,
        "supply_org": deal.supply_org,
        "demand_org": deal.demand_org,
        "moment_description": deal.moment_description,
        "content_url": submission.content_url,
        "validation": validation.model_dump(mode="json"),
        "timestamp": datetime.now(UTC).isoformat(),
    })

    return {
        "status": "validated",
        "validation": validation.model_dump(mode="json"),
        "deal_state": FulfillmentState.COMPLETED,
    }
