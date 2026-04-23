"""Content submission and validation API routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_current_agent
from src.api.stream import sse_bus
from src.engine.orchestrator import handle_content_submission
from src.store import store

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


@router.post("/{deal_id}/review")
async def review_content(
    deal_id: str,
    body: dict,
    agent=Depends(get_current_agent),
):
    """Agent reviews generated branded content options.

    Body: {option_id: int, decision: "approve"|"reject", reasoning: str}
    Both supply and demand agents must approve the same option to close.
    """
    deal = store.deals.get(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    option_id = body.get("option_id")
    decision = body.get("decision", "approve")
    reasoning = body.get("reasoning", "")

    # Store the review
    deal_results = store.deal_results.setdefault(deal_id, {})
    reviews = deal_results.setdefault("content_reviews", [])
    reviews.append({
        "agent_id": agent.agent_id,
        "organization": agent.organization,
        "option_id": option_id,
        "decision": decision,
        "reasoning": reasoning,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Publish SSE event
    await sse_bus.publish("content_review", {
        "deal_id": deal_id,
        "agent_id": agent.agent_id,
        "agent_name": getattr(agent, "name", agent.organization),
        "option_id": option_id,
        "decision": decision,
        "reasoning": reasoning,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Record audit event
    store.add_deal_event(deal_id, {
        "type": "content_reviewed",
        "actor": agent.organization,
        "actor_type": "supply" if hasattr(agent, "supply_capabilities") else "demand",
        "option_id": option_id,
        "decision": decision,
        "reasoning": reasoning,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Check if both parties approved the same option
    approvals = [r for r in reviews if r["decision"] == "approve"]
    approved_options = {}
    for r in approvals:
        oid = r["option_id"]
        approved_options.setdefault(oid, set()).add(r["organization"])

    # Need both supply_org and demand_org to approve same option
    for oid, orgs in approved_options.items():
        if deal.supply_org in orgs and deal.demand_org in orgs:
            # Both approved! Complete the deal
            store.update_deal(deal_id, state="completed")
            await sse_bus.publish("deal_completed", {
                "deal_id": deal_id,
                "approved_option": oid,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            store.add_deal_event(deal_id, {
                "type": "deal_completed",
                "actor": "AAX Exchange",
                "actor_type": "platform",
                "description": f"Both parties approved option {oid}. Deal complete.",
                "approved_option": oid,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            return {
                "status": "deal_completed",
                "approved_option": oid,
                "message": "Both parties approved. Deal is complete.",
            }

    return {
        "status": "review_recorded",
        "option_id": option_id,
        "decision": decision,
        "awaiting": "Both supply and demand must approve the same option.",
    }
