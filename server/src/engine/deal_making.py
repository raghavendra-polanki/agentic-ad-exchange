"""Deal-making LangGraph state machine.

Orchestrates: opportunity listing -> pre-screen -> matching -> proposals ->
conflict check -> negotiation -> deal agreed/rejected/expired.
"""

import asyncio
import uuid
from datetime import UTC, datetime

from langgraph.graph import END, StateGraph

from src.engine.events import event_bus
from src.engine.state import DealMakingState
from src.schemas.conflicts import ConflictCheckResult, ConflictStatus
from src.schemas.deals import DealAgreement, DealState, DealTerms, Price
from src.schemas.opportunities import OpportunityRecord, OpportunitySignal
from src.schemas.proposals import (
    EvaluationDecision,
    Proposal,
    ProposalRecord,
    ProposalResponse,
    ProposalStatus,
)

# ruff: noqa: I001


# ---------------------------------------------------------------------------
# Placeholder functions — will be wired to real engines / agent callbacks
# ---------------------------------------------------------------------------


def call_conflict_prescreen(school: str, sport: str, brand: str) -> ConflictCheckResult:
    """Placeholder -- will be wired to ConflictEngine."""
    return ConflictCheckResult(status=ConflictStatus.CLEARED, brand=brand)


def call_conflict_final_check(
    school: str, sport: str, brand: str, athlete_name: str
) -> ConflictCheckResult:
    """Placeholder -- will be wired to ConflictEngine for athlete-level check."""
    return ConflictCheckResult(
        status=ConflictStatus.CLEARED,
        brand=brand,
        check_type="final",
    )


def get_registered_demand_agents() -> list[dict]:
    """Placeholder -- returns fake demand agents for Phase 1."""
    return [
        {"agent_id": "nike-agent-001", "organization": "Nike", "brand": "Nike"},
        {"agent_id": "gatorade-agent-001", "organization": "Gatorade", "brand": "Gatorade"},
    ]


def notify_agent_webhook(agent_id: str, payload: dict) -> bool:
    """Placeholder -- will POST to agent callback URL."""
    return True


def simulate_demand_proposal(opportunity: dict, agent_id: str) -> Proposal:
    """Placeholder -- simulates a demand agent submitting a proposal."""
    return Proposal(
        opportunity_id=opportunity.get("opportunity_id", ""),
        demand_agent_id=agent_id,
        deal_terms=DealTerms(
            price=Price(amount=2500.0),
            content_format="gameday_graphic",
            platforms=["instagram"],
        ),
        reasoning="Auto-generated proposal for Phase 1 demo.",
    )


def simulate_supply_response(proposal: dict) -> ProposalResponse:
    """Placeholder -- simulates supply agent accepting the proposal."""
    return ProposalResponse(
        decision=EvaluationDecision.ACCEPT,
        reasoning="Auto-accepted for Phase 1 demo.",
    )


# ---------------------------------------------------------------------------
# Helper: create an audit event dict
# ---------------------------------------------------------------------------


def _event(deal_id: str, action: str, state: str, detail: str = "") -> dict:
    return {
        "deal_id": deal_id,
        "action": action,
        "state": state,
        "detail": detail,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------


def list_opportunity(state: DealMakingState) -> dict:
    """Entry node: record the opportunity and set initial state."""
    deal_id = state["deal_id"]
    evt = _event(deal_id, "list_opportunity", DealState.OPPORTUNITY_LISTED)

    # Publish event (fire-and-forget in sync context)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            payload = {**evt, "new_state": DealState.OPPORTUNITY_LISTED}
            loop.create_task(
                event_bus.publish("deal.state_change", payload)
            )
        else:
            payload = {**evt, "new_state": DealState.OPPORTUNITY_LISTED}
            loop.run_until_complete(
                event_bus.publish("deal.state_change", payload)
            )
    except RuntimeError:
        pass  # No event loop available (e.g. in tests)

    return {
        "state": DealState.OPPORTUNITY_LISTED,
        "events": [evt],
    }


def pre_screen(state: DealMakingState) -> dict:
    """Run conflict pre-screen for each registered demand agent."""
    deal_id = state["deal_id"]
    opportunity = state["opportunity"]
    signal = opportunity.get("signal", {})
    subjects = signal.get("subjects", [])
    school = subjects[0]["school"] if subjects else ""
    sport = signal.get("sport", "")

    demand_agents = get_registered_demand_agents()
    matched: list[str] = []
    conflict_results: list[dict] = []

    for agent in demand_agents:
        result = call_conflict_prescreen(school, sport, agent["brand"])
        result_dict = result.model_dump()
        result_dict["agent_id"] = agent["agent_id"]
        conflict_results.append(result_dict)
        if result.status == ConflictStatus.CLEARED:
            matched.append(agent["agent_id"])

    evt = _event(
        deal_id,
        "pre_screen",
        DealState.PRE_SCREENING,
        f"Screened {len(demand_agents)} agents, {len(matched)} cleared.",
    )

    return {
        "state": DealState.PRE_SCREENING,
        "matched_agents": matched,
        "conflict_results": conflict_results,
        "events": [evt],
    }


def notify_demand(state: DealMakingState) -> dict:
    """Send opportunity to matched demand agents (placeholder logs notification)."""
    deal_id = state["deal_id"]
    matched = state.get("matched_agents", [])
    opportunity = state["opportunity"]

    for agent_id in matched:
        notify_agent_webhook(agent_id, {"opportunity": opportunity})

    evt = _event(
        deal_id,
        "notify_demand",
        DealState.AWAITING_PROPOSALS,
        f"Notified {len(matched)} demand agents.",
    )

    return {
        "state": DealState.AWAITING_PROPOSALS,
        "events": [evt],
    }


def receive_proposal(state: DealMakingState) -> dict:
    """Process incoming proposal from a demand agent."""
    deal_id = state["deal_id"]
    opportunity = state["opportunity"]
    matched = state.get("matched_agents", [])

    # For Phase 1, simulate a proposal from the first matched agent
    if not matched:
        return {
            "state": DealState.DEAL_EXPIRED,
            "error": "No matched agents to receive proposals from.",
            "events": [_event(deal_id, "receive_proposal", DealState.DEAL_EXPIRED, "No agents.")],
        }

    agent_id = matched[0]
    proposal = simulate_demand_proposal(opportunity, agent_id)
    proposal_record = ProposalRecord(
        proposal_id=f"prop-{uuid.uuid4().hex[:8]}",
        opportunity_id=proposal.opportunity_id,
        demand_agent_id=proposal.demand_agent_id,
        demand_org=agent_id,  # simplified for Phase 1
        deal_terms=proposal.deal_terms,
        scores=proposal.scores,
        reasoning=proposal.reasoning,
        round=state.get("negotiation_round", 1),
    )

    evt = _event(
        deal_id,
        "receive_proposal",
        DealState.PROPOSAL_RECEIVED,
        f"Proposal from {agent_id}, round {proposal_record.round}.",
    )

    return {
        "state": DealState.PROPOSAL_RECEIVED,
        "proposals": [proposal_record.model_dump()],
        "active_proposal": proposal_record.model_dump(),
        "events": [evt],
    }


def final_conflict_check(state: DealMakingState) -> dict:
    """Run full conflict check on the active proposal (athlete-level)."""
    deal_id = state["deal_id"]
    active = state.get("active_proposal", {})
    opportunity = state["opportunity"]
    signal = opportunity.get("signal", {})
    subjects = signal.get("subjects", [])
    school = subjects[0]["school"] if subjects else ""
    sport = signal.get("sport", "")
    athlete = subjects[0]["athlete_name"] if subjects else ""
    brand = active.get("demand_org", "")

    result = call_conflict_final_check(school, sport, brand, athlete)

    if result.status == ConflictStatus.BLOCKED:
        evt = _event(
            deal_id,
            "final_conflict_check",
            DealState.DEAL_REJECTED,
            f"Conflict blocked: {brand}",
        )
        # Update active proposal status
        active_updated = {**active, "status": ProposalStatus.CONFLICT_BLOCKED}
        return {
            "state": DealState.DEAL_REJECTED,
            "active_proposal": active_updated,
            "conflict_results": [result.model_dump()],
            "events": [evt],
        }

    evt = _event(
        deal_id,
        "final_conflict_check",
        DealState.FINAL_CONFLICT_CHECK,
        f"Cleared: {brand}",
    )
    return {
        "state": DealState.FINAL_CONFLICT_CHECK,
        "conflict_results": [result.model_dump()],
        "events": [evt],
    }


def forward_to_supply(state: DealMakingState) -> dict:
    """Send cleared proposal to supply agent for evaluation."""
    deal_id = state["deal_id"]

    evt = _event(
        deal_id,
        "forward_to_supply",
        DealState.AWAITING_SUPPLY_EVAL,
        "Forwarded proposal to supply agent.",
    )

    return {
        "state": DealState.AWAITING_SUPPLY_EVAL,
        "events": [evt],
    }


def process_response(state: DealMakingState) -> dict:
    """Handle supply agent's response: accept / reject / counter."""
    deal_id = state["deal_id"]
    active = state.get("active_proposal", {})

    response = simulate_supply_response(active)

    if response.decision == EvaluationDecision.ACCEPT:
        evt = _event(deal_id, "process_response", DealState.NEGOTIATING, "Supply accepted.")
        return {
            "state": DealState.DEAL_AGREED,
            "events": [evt],
        }
    elif response.decision == EvaluationDecision.REJECT:
        evt = _event(deal_id, "process_response", DealState.NEGOTIATING, "Supply rejected.")
        return {
            "state": DealState.DEAL_REJECTED,
            "events": [evt],
        }
    else:
        # Counter
        round_num = state.get("negotiation_round", 1)
        max_rounds = state.get("max_rounds", 3)
        if round_num >= max_rounds:
            evt = _event(
                deal_id, "process_response", DealState.NEGOTIATING, "Max rounds reached."
            )
            return {
                "state": DealState.DEAL_REJECTED,
                "events": [evt],
            }
        evt = _event(
            deal_id,
            "process_response",
            DealState.NEGOTIATING,
            f"Counter from supply, round {round_num + 1}.",
        )
        return {
            "state": DealState.NEGOTIATING,
            "negotiation_round": round_num + 1,
            "events": [evt],
        }


def deal_agreed(state: DealMakingState) -> dict:
    """Terminal: create DealAgreement and log completion."""
    deal_id = state["deal_id"]
    opportunity = state["opportunity"]
    active = state.get("active_proposal", {})

    agreement = DealAgreement(
        deal_id=deal_id,
        opportunity_id=opportunity.get("opportunity_id", ""),
        supply_agent_id=opportunity.get("supply_agent_id", ""),
        demand_agent_id=active.get("demand_agent_id", ""),
        final_terms=DealTerms(**active["deal_terms"]) if active.get("deal_terms") else DealTerms(
            price=Price(amount=0), content_format="gameday_graphic"
        ),
        supply_org=opportunity.get("supply_org", ""),
        demand_org=active.get("demand_org", ""),
    )

    evt = _event(deal_id, "deal_agreed", DealState.DEAL_AGREED, "Deal finalized.")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            payload = {
                "deal_id": deal_id,
                "agreement": agreement.model_dump(mode="json"),
            }
            loop.create_task(event_bus.publish("deal.agreed", payload))
    except RuntimeError:
        pass

    return {
        "state": DealState.DEAL_AGREED,
        "events": [evt],
    }


def deal_rejected(state: DealMakingState) -> dict:
    """Terminal: deal rejected."""
    deal_id = state["deal_id"]
    evt = _event(deal_id, "deal_rejected", DealState.DEAL_REJECTED, "Deal rejected.")
    return {
        "state": DealState.DEAL_REJECTED,
        "events": [evt],
    }


def deal_expired(state: DealMakingState) -> dict:
    """Terminal: deal expired (no matches or timeout)."""
    deal_id = state["deal_id"]
    evt = _event(deal_id, "deal_expired", DealState.DEAL_EXPIRED, "Deal expired.")
    return {
        "state": DealState.DEAL_EXPIRED,
        "events": [evt],
    }


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------


def after_pre_screen(state: DealMakingState) -> str:
    """Route after pre-screen: notify_demand if matches, else deal_expired."""
    if state.get("matched_agents"):
        return "notify_demand"
    return "deal_expired"


def after_final_conflict(state: DealMakingState) -> str:
    """Route after final conflict check: forward if cleared, reject if blocked."""
    if state.get("state") == DealState.DEAL_REJECTED:
        return "deal_rejected"
    return "forward_to_supply"


def after_process_response(state: DealMakingState) -> str:
    """Route after supply response: agreed, rejected, or another round."""
    current = state.get("state", "")
    if current == DealState.DEAL_AGREED:
        return "deal_agreed"
    elif current == DealState.DEAL_REJECTED:
        return "deal_rejected"
    else:
        # Counter — go back to receive_proposal for next round
        return "receive_proposal"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def create_deal_making_graph() -> StateGraph:
    """Build and compile the deal-making LangGraph state machine."""
    graph = StateGraph(DealMakingState)

    # Add nodes
    graph.add_node("list_opportunity", list_opportunity)
    graph.add_node("pre_screen", pre_screen)
    graph.add_node("notify_demand", notify_demand)
    graph.add_node("receive_proposal", receive_proposal)
    graph.add_node("final_conflict_check", final_conflict_check)
    graph.add_node("forward_to_supply", forward_to_supply)
    graph.add_node("process_response", process_response)
    graph.add_node("deal_agreed", deal_agreed)
    graph.add_node("deal_rejected", deal_rejected)
    graph.add_node("deal_expired", deal_expired)

    # Set entry
    graph.set_entry_point("list_opportunity")

    # Linear edges
    graph.add_edge("list_opportunity", "pre_screen")
    graph.add_edge("notify_demand", "receive_proposal")
    graph.add_edge("receive_proposal", "final_conflict_check")
    graph.add_edge("forward_to_supply", "process_response")

    # Conditional edges
    graph.add_conditional_edges("pre_screen", after_pre_screen, {
        "notify_demand": "notify_demand",
        "deal_expired": "deal_expired",
    })
    graph.add_conditional_edges("final_conflict_check", after_final_conflict, {
        "forward_to_supply": "forward_to_supply",
        "deal_rejected": "deal_rejected",
    })
    graph.add_conditional_edges("process_response", after_process_response, {
        "deal_agreed": "deal_agreed",
        "deal_rejected": "deal_rejected",
        "receive_proposal": "receive_proposal",
    })

    # Terminal edges
    graph.add_edge("deal_agreed", END)
    graph.add_edge("deal_rejected", END)
    graph.add_edge("deal_expired", END)

    return graph.compile()


def run_deal_making(
    opportunity_signal: OpportunitySignal,
    supply_agent_id: str,
    supply_org: str,
) -> dict:
    """Convenience function: create initial state, invoke the deal-making graph, return result."""
    deal_id = f"deal-{uuid.uuid4().hex[:12]}"
    opportunity = OpportunityRecord(
        opportunity_id=f"opp-{uuid.uuid4().hex[:8]}",
        supply_agent_id=supply_agent_id,
        supply_org=supply_org,
        signal=opportunity_signal,
    )

    initial_state: DealMakingState = {
        "deal_id": deal_id,
        "opportunity": opportunity.model_dump(mode="json"),
        "state": "",
        "proposals": [],
        "active_proposal": None,
        "conflict_results": [],
        "negotiation_round": 1,
        "max_rounds": 3,
        "matched_agents": [],
        "events": [],
        "error": None,
    }

    compiled = create_deal_making_graph()
    result = compiled.invoke(initial_state)
    return result
