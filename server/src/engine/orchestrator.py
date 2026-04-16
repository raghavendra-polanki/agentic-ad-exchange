"""Deal orchestrator — thin bridge between API routes and LangGraph engine.

The API routes call these functions instead of reimplementing deal logic inline.
Each function uses the real conflict engine and store, then publishes SSE events.
"""

import uuid
from datetime import UTC, datetime

from src.api.stream import sse_bus
from src.conflict import conflict_checker
from src.schemas.agents import DemandAgentProfile, SupplyAgentProfile
from src.schemas.deals import DealAgreement, DealState, DealSummary
from src.schemas.opportunities import OpportunitySignal
from src.schemas.proposals import (
    EvaluationDecision,
    Proposal,
    ProposalResponse,
    ProposalStatus,
)
from src.store import store


async def handle_signal_opportunity(
    agent: SupplyAgentProfile,
    signal: OpportunitySignal,
) -> dict:
    """Supply agent signals a new opportunity. Runs pre-screen and creates deal."""
    opp = store.create_opportunity(agent.agent_id, agent.organization, signal)

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
                "description": (
                    f"{len(matched)} demand agents notified."
                    " Proposals will arrive via webhook."
                ),
            }
        ],
    }


async def handle_submit_proposal(
    agent: DemandAgentProfile,
    opportunity_id: str,
    proposal: Proposal,
) -> dict:
    """Demand agent submits a proposal. Runs final conflict check."""
    opp = store.opportunities.get(opportunity_id)
    if not opp:
        return None  # caller raises 404

    athlete_names = [s.athlete_name for s in opp.signal.subjects]
    school = opp.signal.subjects[0].school if opp.signal.subjects else ""
    sport = opp.signal.subjects[0].sport if opp.signal.subjects else ""

    conflict_result = conflict_checker.final_check(school, sport, agent.organization, athlete_names)

    if conflict_result.status == "blocked":
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

    prop = store.create_proposal({
        "opportunity_id": opportunity_id,
        "demand_agent_id": agent.agent_id,
        "demand_org": agent.organization,
        "deal_terms": proposal.deal_terms,
        "scores": proposal.scores,
        "reasoning": proposal.reasoning,
    })

    for deal in store.deals.values():
        if deal.opportunity_id == opportunity_id:
            store.update_deal(deal.deal_id,
                state=DealState.AWAITING_SUPPLY_EVAL,
                demand_org=agent.organization,
                deal_terms=proposal.deal_terms)

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


async def handle_respond_to_proposal(
    agent: SupplyAgentProfile | DemandAgentProfile,
    proposal_id: str,
    response: ProposalResponse,
) -> dict:
    """Supply agent responds to a proposal (accept/counter/reject)."""
    prop = store.proposals.get(proposal_id)
    if not prop:
        return None  # caller raises 404

    deal = None
    for d in store.deals.values():
        if d.opportunity_id == prop.opportunity_id:
            deal = d
            break

    if response.decision == EvaluationDecision.ACCEPT:
        prop_updated = prop.model_copy(update={"status": ProposalStatus.ACCEPTED})
        store.proposals[proposal_id] = prop_updated

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
            "next_actions": [{
                "action": "await_creative_brief",
                "description": "Brief will be sent to your webhook.",
            }],
        }

    elif response.decision == EvaluationDecision.REJECT:
        prop_updated = prop.model_copy(update={"status": ProposalStatus.REJECTED})
        store.proposals[proposal_id] = prop_updated

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
        prop_updated = prop.model_copy(update={"status": ProposalStatus.COUNTERED})
        store.proposals[proposal_id] = prop_updated
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
                "counter_terms": (
                    response.counter_terms.model_dump(mode="json")
                    if response.counter_terms else None
                ),
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        counter = (
            response.counter_terms.model_dump(mode="json")
            if response.counter_terms else None
        )
        return {
            "status": "countered",
            "round": new_round,
            "counter_terms": counter,
        }
