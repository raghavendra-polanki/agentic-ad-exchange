"""Opportunity signaling and proposal submission API routes."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Header, HTTPException

from src.api.stream import sse_bus
from src.conflict import conflict_checker
from src.schemas.agents import DemandAgentProfile
from src.schemas.deals import DealState, DealSummary, DealTerms, Price
from src.schemas.opportunities import OpportunitySignal
from src.schemas.proposals import Proposal, ProposalRecord, ProposalStatus, ScoreBreakdown
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


@router.post("/")
async def signal_opportunity(
    signal: OpportunitySignal,
    authorization: str | None = Header(None),
):
    """Supply agent signals a new opportunity on the exchange."""
    agent = _get_agent_from_token(authorization)

    # Create opportunity record
    opp = store.create_opportunity(agent.agent_id, agent.organization, signal)

    # Pre-screen: check each demand agent for conflicts
    demand_agents = store.get_demand_agents()
    matched = []
    prescreen_results = []

    for da in demand_agents:
        school = signal.subjects[0].school if signal.subjects else ""
        sport = signal.subjects[0].sport if signal.subjects else ""
        result = conflict_checker.pre_screen(school, sport, da.organization)
        prescreen_results.append({
            "agent_id": da.agent_id,
            "organization": da.organization,
            "status": result.status,
            "conflicts": [c.model_dump(mode="json") for c in result.conflicts],
        })
        if result.status == "cleared":
            matched.append(da.agent_id)
            opp.matched_demand_agents.append(da.agent_id)

    # Create deal tracker
    deal_id = f"deal_{uuid.uuid4().hex[:8]}"
    deal = DealSummary(
        deal_id=deal_id,
        opportunity_id=opp.opportunity_id,
        supply_org=agent.organization,
        demand_org="",
        state=DealState.AWAITING_PROPOSALS,
        moment_description=signal.content_description,
    )
    store.create_deal(deal)

    # Publish events to dashboard
    await sse_bus.publish("deal_created", {
        "deal_id": deal_id,
        "opportunity_id": opp.opportunity_id,
        "state": DealState.AWAITING_PROPOSALS,
        "supply_org": agent.organization,
        "demand_org": "",
        "moment_description": signal.content_description,
        "matched_count": len(matched),
        "prescreen_results": prescreen_results,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    return {
        "opportunity_id": opp.opportunity_id,
        "deal_id": deal_id,
        "status": "listed",
        "matched_count": len(matched),
        "prescreen_results": prescreen_results,
        "next_actions": [
            {
                "action": "wait_for_proposals",
                "description": f"{len(matched)} demand agents notified. Proposals will arrive via webhook.",
            }
        ],
    }


@router.post("/{opportunity_id}/propose")
async def submit_proposal(
    opportunity_id: str,
    proposal: Proposal,
    authorization: str | None = Header(None),
):
    """Demand agent submits a proposal for an opportunity."""
    agent = _get_agent_from_token(authorization)

    opp = store.opportunities.get(opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Final conflict check (athlete-level)
    athlete_names = [s.athlete_name for s in opp.signal.subjects]
    school = opp.signal.subjects[0].school if opp.signal.subjects else ""
    sport = opp.signal.subjects[0].sport if opp.signal.subjects else ""

    conflict_result = conflict_checker.final_check(school, sport, agent.organization, athlete_names)

    if conflict_result.status == "blocked":
        # Publish conflict event
        await sse_bus.publish("conflict_blocked", {
            "opportunity_id": opportunity_id,
            "demand_org": agent.organization,
            "conflicts": [c.model_dump(mode="json") for c in conflict_result.conflicts],
            "timestamp": datetime.now(UTC).isoformat(),
        })

        return {
            "proposal_id": None,
            "status": "conflict_blocked",
            "conflict_result": conflict_result.model_dump(mode="json"),
        }

    # Create proposal record
    prop = store.create_proposal({
        "opportunity_id": opportunity_id,
        "demand_agent_id": agent.agent_id,
        "demand_org": agent.organization,
        "deal_terms": proposal.deal_terms,
        "scores": proposal.scores,
        "reasoning": proposal.reasoning,
    })

    # Find the deal for this opportunity and update it
    for deal in store.deals.values():
        if deal.opportunity_id == opportunity_id:
            store.update_deal(deal.deal_id,
                state=DealState.AWAITING_SUPPLY_EVAL,
                demand_org=agent.organization,
                deal_terms=proposal.deal_terms)

            # Publish to dashboard
            await sse_bus.publish("deal_update", {
                "deal_id": deal.deal_id,
                "opportunity_id": opportunity_id,
                "state": DealState.AWAITING_SUPPLY_EVAL,
                "supply_org": deal.supply_org,
                "demand_org": agent.organization,
                "moment_description": deal.moment_description,
                "deal_terms": proposal.deal_terms.model_dump(mode="json"),
                "scores": proposal.scores.model_dump(mode="json") if proposal.scores else None,
                "reasoning": proposal.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            break

    return {
        "proposal_id": prop.proposal_id,
        "status": "submitted",
        "conflict_status": "cleared",
        "valid_actions": ["wait_for_supply_evaluation"],
        "constraints": {"max_counter_rounds": 3, "response_timeout_seconds": 600},
    }


@router.post("/{opportunity_id}/pass")
async def pass_opportunity(
    opportunity_id: str,
    authorization: str | None = Header(None),
):
    """Demand agent declines an opportunity."""
    agent = _get_agent_from_token(authorization)
    return {"status": "passed", "opportunity_id": opportunity_id, "agent_id": agent.agent_id}
