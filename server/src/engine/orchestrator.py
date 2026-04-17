"""Deal orchestrator — thin bridge between API routes and LangGraph engine.

The API routes call these functions instead of reimplementing deal logic inline.
Each function uses the real conflict engine and store, then publishes SSE events.
"""

import asyncio
import uuid
from datetime import UTC, datetime

from src.api.stream import sse_bus
from src.conflict import conflict_checker
from src.engine.timeout import timeout_manager
from src.engine.webhook import deliver_webhook
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

# Default timeout for deals (seconds). 120s for demo pacing.
DEFAULT_DEAL_TIMEOUT = 120


def _on_deal_expired(deal_id: str) -> None:
    """Sync callback fired by TimeoutManager when a deal expires."""
    import asyncio

    deal = store.deals.get(deal_id)
    if not deal or deal.state in (
        DealState.DEAL_AGREED,
        DealState.DEAL_REJECTED,
        DealState.DEAL_EXPIRED,
    ):
        return  # already terminal

    store.update_deal(deal_id, state=DealState.DEAL_EXPIRED)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(sse_bus.publish("deal_expired", {
            "deal_id": deal_id,
            "state": DealState.DEAL_EXPIRED,
            "timestamp": datetime.now(UTC).isoformat(),
        }))
    except RuntimeError:
        pass


async def handle_signal_opportunity(
    agent: SupplyAgentProfile,
    signal: OpportunitySignal,
) -> dict:
    """Supply agent signals a new opportunity. Runs pre-screen, creates deal."""
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
            "conflicts": [
                c.model_dump(mode="json") for c in result.conflicts
            ],
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

    # Register deal timeout
    try:
        timeout_manager.register(
            deal_id, DEFAULT_DEAL_TIMEOUT, _on_deal_expired,
        )
    except RuntimeError:
        pass  # no event loop (tests)

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

    # Deliver opportunity.matched webhooks to matched demand agents
    for da_id in matched:
        da = store.get_agent(da_id)
        org_id = store.agent_org.get(da_id)
        org = store.get_org(org_id) if org_id else None
        asyncio.create_task(deliver_webhook(da_id, "opportunity.matched", {
            "opportunity_id": opp.opportunity_id,
            "deal_id": deal_id,
            "signal": signal.model_dump(mode="json"),
            "supply_org": agent.organization,
            "next_actions": [
                {
                    "action": "propose",
                    "endpoint": (
                        f"POST /api/v1/opportunities"
                        f"/{opp.opportunity_id}/propose"
                    ),
                    "description": "Submit a proposal for this opportunity",
                },
                {
                    "action": "pass",
                    "endpoint": (
                        f"POST /api/v1/opportunities"
                        f"/{opp.opportunity_id}/pass"
                    ),
                    "description": "Decline this opportunity",
                },
            ],
            "constraints": {
                "response_timeout_seconds": DEFAULT_DEAL_TIMEOUT,
                "budget_per_deal": (
                    org.budget_per_deal_max if org else 5000
                ),
                "budget_monthly_remaining": (
                    org.budget_monthly_max - org.budget_monthly_spent
                    if org else 50000
                ),
            },
        }))

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

    conflict_result = conflict_checker.final_check(
        school, sport, agent.organization, athlete_names,
    )

    if conflict_result.status == "blocked":
        await sse_bus.publish("conflict_blocked", {
            "opportunity_id": opportunity_id,
            "demand_org": agent.organization,
            "conflicts": [
                c.model_dump(mode="json")
                for c in conflict_result.conflicts
            ],
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
            new_ids = deal.all_proposal_ids + [prop.proposal_id]
            store.update_deal(
                deal.deal_id,
                state=DealState.AWAITING_SUPPLY_EVAL,
                demand_org=agent.organization,
                deal_terms=proposal.deal_terms,
                all_proposal_ids=new_ids,
            )

            await sse_bus.publish("deal_update", {
                "deal_id": deal.deal_id,
                "opportunity_id": opportunity_id,
                "state": DealState.AWAITING_SUPPLY_EVAL,
                "supply_org": deal.supply_org,
                "demand_org": agent.organization,
                "moment_description": deal.moment_description,
                "deal_terms": proposal.deal_terms.model_dump(mode="json"),
                "scores": (
                    proposal.scores.model_dump(mode="json")
                    if proposal.scores else None
                ),
                "reasoning": proposal.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

            # Deliver proposal.received webhook to supply agent
            asyncio.create_task(deliver_webhook(
                opp.supply_agent_id,
                "proposal.received",
                {
                    "deal_id": deal.deal_id,
                    "proposal_id": prop.proposal_id,
                    "opportunity_id": opportunity_id,
                    "demand_org": agent.organization,
                    "deal_terms": proposal.deal_terms.model_dump(
                        mode="json",
                    ),
                    "reasoning": proposal.reasoning,
                    "scores": (
                        proposal.scores.model_dump(mode="json")
                        if proposal.scores else None
                    ),
                    "next_actions": [
                        {
                            "action": "accept",
                            "endpoint": (
                                f"POST /api/v1/proposals"
                                f"/{prop.proposal_id}/respond"
                            ),
                        },
                        {
                            "action": "counter",
                            "endpoint": (
                                f"POST /api/v1/proposals"
                                f"/{prop.proposal_id}/respond"
                            ),
                        },
                        {
                            "action": "reject",
                            "endpoint": (
                                f"POST /api/v1/proposals"
                                f"/{prop.proposal_id}/respond"
                            ),
                        },
                    ],
                    "constraints": {
                        "round": prop.round,
                        "max_rounds": 3,
                    },
                },
            ))
            break

    return {
        "proposal_id": prop.proposal_id,
        "status": "submitted",
        "conflict_status": "cleared",
        "valid_actions": ["wait_for_supply_evaluation"],
        "constraints": {
            "max_counter_rounds": 3,
            "response_timeout_seconds": 600,
        },
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
        prop_updated = prop.model_copy(
            update={"status": ProposalStatus.ACCEPTED},
        )
        store.proposals[proposal_id] = prop_updated

        if deal:
            store.update_deal(
                deal.deal_id,
                state=DealState.DEAL_AGREED,
                winning_proposal_id=proposal_id,
            )
            timeout_manager.cancel(deal.deal_id)

            agreement = DealAgreement(
                deal_id=deal.deal_id,
                opportunity_id=prop.opportunity_id,
                supply_agent_id=agent.agent_id,
                demand_agent_id=prop.demand_agent_id,
                final_terms=prop.deal_terms,
                supply_org=deal.supply_org,
                demand_org=prop.demand_org,
            )
            store.deal_results[deal.deal_id] = agreement.model_dump(
                mode="json",
            )

            await sse_bus.publish("deal_agreed", {
                "deal_id": deal.deal_id,
                "state": DealState.DEAL_AGREED,
                "supply_org": deal.supply_org,
                "demand_org": prop.demand_org,
                "moment_description": deal.moment_description,
                "deal_terms": prop.deal_terms.model_dump(mode="json"),
                "reasoning": response.reasoning,
                "scores": (
                    response.scores.model_dump(mode="json")
                    if response.scores else None
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            })

            # Deliver deal.agreed webhook to both agents
            agreed_payload = {
                "deal_id": deal.deal_id,
                "event": "deal.agreed",
                "final_terms": prop.deal_terms.model_dump(mode="json"),
                "supply_org": deal.supply_org,
                "demand_org": prop.demand_org,
            }
            opp = store.opportunities.get(prop.opportunity_id)
            if opp:
                asyncio.create_task(
                    deliver_webhook(
                        opp.supply_agent_id, "deal.agreed", agreed_payload,
                    ),
                )
            asyncio.create_task(
                deliver_webhook(
                    prop.demand_agent_id, "deal.agreed", agreed_payload,
                ),
            )

        return {
            "status": "accepted",
            "deal_id": deal.deal_id if deal else None,
            "next_actions": [{
                "action": "await_creative_brief",
                "description": "Brief will be sent to your webhook.",
            }],
        }

    elif response.decision == EvaluationDecision.REJECT:
        prop_updated = prop.model_copy(
            update={"status": ProposalStatus.REJECTED},
        )
        store.proposals[proposal_id] = prop_updated

        if deal:
            store.update_deal(deal.deal_id, state=DealState.DEAL_REJECTED)
            timeout_manager.cancel(deal.deal_id)
            await sse_bus.publish("deal_update", {
                "deal_id": deal.deal_id,
                "state": DealState.DEAL_REJECTED,
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        return {"status": "rejected", "reasoning": response.reasoning}

    else:  # COUNTER
        # Enforce max negotiation rounds
        if deal and prop.round >= deal.max_rounds:
            return {
                "status": "error",
                "detail": (
                    f"Maximum negotiation rounds ({deal.max_rounds})"
                    " reached. Accept or reject."
                ),
            }

        prop_updated = prop.model_copy(
            update={"status": ProposalStatus.COUNTERED},
        )
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

            # Deliver counter.received webhook to the other party
            counter_recipient = prop.demand_agent_id
            asyncio.create_task(deliver_webhook(
                counter_recipient,
                "counter.received",
                {
                    "deal_id": deal.deal_id,
                    "proposal_id": proposal_id,
                    "counter_terms": (
                        response.counter_terms.model_dump(mode="json")
                        if response.counter_terms else None
                    ),
                    "reasoning": response.reasoning,
                    "constraints": {
                        "round": new_round,
                        "max_rounds": 3,
                    },
                    "next_actions": [
                        {"action": "accept"},
                        {"action": "counter"},
                        {"action": "reject"},
                    ],
                },
            ))

        counter = (
            response.counter_terms.model_dump(mode="json")
            if response.counter_terms else None
        )
        return {
            "status": "countered",
            "round": new_round,
            "counter_terms": counter,
        }


async def handle_select_winner(opportunity_id: str) -> dict | None:
    """Select the best non-blocked proposal for an opportunity."""
    opp = store.opportunities.get(opportunity_id)
    if not opp:
        return None

    # Gather all proposals for this opportunity
    proposals = [
        p for p in store.proposals.values()
        if p.opportunity_id == opportunity_id
        and p.status != ProposalStatus.CONFLICT_BLOCKED
    ]

    if not proposals:
        return {"status": "no_proposals", "opportunity_id": opportunity_id}

    # Sort by overall score (descending), then by price (descending)
    def sort_key(p):
        score = p.scores.overall if p.scores else 0
        price = p.deal_terms.price.amount if p.deal_terms else 0
        return (score, price)

    proposals.sort(key=sort_key, reverse=True)
    winner = proposals[0]

    # Update deal with winner
    for deal in store.deals.values():
        if deal.opportunity_id == opportunity_id:
            store.update_deal(
                deal.deal_id,
                state=DealState.AWAITING_SUPPLY_EVAL,
                demand_org=winner.demand_org,
                deal_terms=winner.deal_terms,
                winning_proposal_id=winner.proposal_id,
            )

            await sse_bus.publish("proposals_ranked", {
                "deal_id": deal.deal_id,
                "opportunity_id": opportunity_id,
                "state": DealState.AWAITING_SUPPLY_EVAL,
                "winning_proposal_id": winner.proposal_id,
                "all_proposals": [
                    {
                        "proposal_id": p.proposal_id,
                        "demand_org": p.demand_org,
                        "price": (
                            p.deal_terms.price.amount if p.deal_terms else 0
                        ),
                        "score": p.scores.overall if p.scores else 0,
                        "status": "won" if p == winner else "outbid",
                    }
                    for p in proposals
                ],
                "timestamp": datetime.now(UTC).isoformat(),
            })
            break

    return {
        "status": "winner_selected",
        "proposal_id": winner.proposal_id,
        "demand_org": winner.demand_org,
        "price": winner.deal_terms.price.amount if winner.deal_terms else 0,
    }
