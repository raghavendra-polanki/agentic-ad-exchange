"""Proposal response API routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException

from src.api.stream import sse_bus
from src.schemas.deals import DealAgreement, DealState, FulfillmentState
from src.schemas.proposals import EvaluationDecision, ProposalResponse, ProposalStatus
from src.store import store

router = APIRouter()


def _get_agent_from_token(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization")
    api_key = authorization.replace("Bearer ", "")
    agent = store.get_agent_by_key(api_key)
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return agent


@router.post("/{proposal_id}/respond")
async def respond_to_proposal(
    proposal_id: str,
    response: ProposalResponse,
    authorization: str | None = Header(None),
):
    """Supply agent responds to a proposal (accept/counter/reject)."""
    agent = _get_agent_from_token(authorization)

    prop = store.proposals.get(proposal_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Find the associated deal
    deal = None
    for d in store.deals.values():
        if d.opportunity_id == prop.opportunity_id:
            deal = d
            break

    if response.decision == EvaluationDecision.ACCEPT:
        prop.status = ProposalStatus.ACCEPTED

        if deal:
            store.update_deal(deal.deal_id, state=DealState.DEAL_AGREED)

            agreement = DealAgreement(
                deal_id=deal.deal_id,
                opportunity_id=prop.opportunity_id,
                supply_agent_id=agent.agent_id,
                demand_agent_id=prop.demand_agent_id,
                final_terms=prop.deal_terms,
                supply_org=deal.supply_org,
                demand_org=prop.demand_org,
            )
            store.deal_results[deal.deal_id] = agreement.model_dump(mode="json")

            await sse_bus.publish("deal_agreed", {
                "deal_id": deal.deal_id,
                "state": DealState.DEAL_AGREED,
                "supply_org": deal.supply_org,
                "demand_org": prop.demand_org,
                "moment_description": deal.moment_description,
                "deal_terms": prop.deal_terms.model_dump(mode="json"),
                "reasoning": response.reasoning,
                "scores": response.scores.model_dump(mode="json") if response.scores else None,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        return {
            "status": "accepted",
            "deal_id": deal.deal_id if deal else None,
            "next_actions": [{"action": "await_creative_brief", "description": "Brief will be sent to your webhook."}],
        }

    elif response.decision == EvaluationDecision.REJECT:
        prop.status = ProposalStatus.REJECTED
        if deal:
            store.update_deal(deal.deal_id, state=DealState.DEAL_REJECTED)
            await sse_bus.publish("deal_update", {
                "deal_id": deal.deal_id,
                "state": DealState.DEAL_REJECTED,
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        return {"status": "rejected", "reasoning": response.reasoning}

    else:  # COUNTER
        prop.status = ProposalStatus.COUNTERED
        new_round = prop.round + 1
        if deal:
            store.update_deal(
                deal.deal_id,
                state=DealState.NEGOTIATING,
                negotiation_round=new_round,
                deal_terms=response.counter_terms,
            )
            await sse_bus.publish("deal_update", {
                "deal_id": deal.deal_id,
                "state": DealState.NEGOTIATING,
                "negotiation_round": new_round,
                "counter_terms": response.counter_terms.model_dump(mode="json") if response.counter_terms else None,
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        return {
            "status": "countered",
            "round": new_round,
            "counter_terms": response.counter_terms.model_dump(mode="json") if response.counter_terms else None,
        }
