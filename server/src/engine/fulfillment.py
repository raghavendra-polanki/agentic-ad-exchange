"""Fulfillment LangGraph state machine.

Orchestrates: brief generation -> content creation -> validation ->
approval -> delivery -> completion.
"""

import asyncio
import uuid
from datetime import UTC, datetime

from langgraph.graph import END, StateGraph

from src.engine.events import event_bus
from src.engine.state import FulfillmentState
from src.schemas.deals import (
    ContentSubmission,
    CreativeBrief,
    DealAgreement,
    DealTerms,
    ValidationResult,
)
from src.schemas.deals import (
    FulfillmentState as FulfillmentStateEnum,
)

# ---------------------------------------------------------------------------
# Placeholder functions — will be wired to real services
# ---------------------------------------------------------------------------


def simulate_content_generation(brief: dict) -> ContentSubmission:
    """Placeholder -- simulates supply agent generating content."""
    return ContentSubmission(
        deal_id=brief.get("deal_id", ""),
        content_url=f"https://storage.aax.example/content/{uuid.uuid4().hex[:8]}.png",
        format=brief.get("deal_terms", {}).get("content_format", "gameday_graphic"),
    )


def simulate_content_validation(submission: dict, brief: dict) -> ValidationResult:
    """Placeholder -- auto-passes validation for Phase 1."""
    return ValidationResult(
        deal_id=submission.get("deal_id", ""),
        passed=True,
        score=0.95,
        checks={
            "brand_logo_present": True,
            "disclosure_present": True,
            "messaging_aligned": True,
        },
    )


def simulate_demand_approval(deal_id: str) -> bool:
    """Placeholder -- auto-approve for Phase 1."""
    return True


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _fire_and_forget(coro) -> None:
    """Schedule an async coroutine from sync code if an event loop is running."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        pass  # No running loop (e.g. in tests) — skip event publishing


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


def generate_brief(state: FulfillmentState) -> dict:
    """Compile DealAgreement into a CreativeBrief."""
    deal_id = state["deal_id"]
    agreement = state["agreement"]

    brief = CreativeBrief(
        deal_id=deal_id,
        deal_terms=DealTerms(**agreement["final_terms"]),
        brand_name=agreement.get("demand_org", ""),
        athlete_name="",  # would come from opportunity in full implementation
        school="",
        sport="",
        moment_description="",
    )

    evt = _event(deal_id, "generate_brief", FulfillmentStateEnum.BRIEF_GENERATED, "Brief compiled.")

    _fire_and_forget(
        event_bus.publish(
            "fulfillment.state_change",
            {**evt, "new_state": FulfillmentStateEnum.BRIEF_GENERATED},
        )
    )

    return {
        "state": FulfillmentStateEnum.BRIEF_GENERATED,
        "creative_brief": brief.model_dump(mode="json"),
        "events": [evt],
    }


def await_content(state: FulfillmentState) -> dict:
    """Wait for / simulate supply agent submitting content."""
    deal_id = state["deal_id"]
    brief = state.get("creative_brief", {})

    submission = simulate_content_generation(brief)

    evt = _event(
        deal_id,
        "await_content",
        FulfillmentStateEnum.CONTENT_GENERATING,
        "Content received from supply agent.",
    )

    return {
        "state": FulfillmentStateEnum.CONTENT_GENERATING,
        "content_submission": submission.model_dump(mode="json"),
        "events": [evt],
    }


def validate_content(state: FulfillmentState) -> dict:
    """Run content validation (placeholder for Phase 1)."""
    deal_id = state["deal_id"]
    submission = state.get("content_submission", {})
    brief = state.get("creative_brief", {})

    result = simulate_content_validation(submission, brief)

    new_state = (
        FulfillmentStateEnum.CONTENT_VALIDATING
        if result.passed
        else FulfillmentStateEnum.REVISION_REQUESTED
    )

    evt = _event(
        deal_id,
        "validate_content",
        new_state,
        f"Validation {'passed' if result.passed else 'failed'} (score: {result.score}).",
    )

    return {
        "state": new_state,
        "validation_result": result.model_dump(mode="json"),
        "events": [evt],
    }


def request_revision(state: FulfillmentState) -> dict:
    """Send revision instructions back to supply agent."""
    deal_id = state["deal_id"]
    revision_count = state.get("revision_count", 0) + 1
    validation = state.get("validation_result", {})

    evt = _event(
        deal_id,
        "request_revision",
        FulfillmentStateEnum.REVISION_REQUESTED,
        f"Revision #{revision_count} requested: {validation.get('revision_instructions', '')}",
    )

    return {
        "state": FulfillmentStateEnum.REVISION_REQUESTED,
        "revision_count": revision_count,
        "events": [evt],
    }


def approve_content(state: FulfillmentState) -> dict:
    """Demand agent approves content (auto-approve for Phase 1)."""
    deal_id = state["deal_id"]

    simulate_demand_approval(deal_id)

    evt = _event(
        deal_id,
        "approve_content",
        FulfillmentStateEnum.CONTENT_APPROVED,
        "Content approved by demand agent.",
    )

    return {
        "state": FulfillmentStateEnum.CONTENT_APPROVED,
        "events": [evt],
    }


def deliver(state: FulfillmentState) -> dict:
    """Mark content as delivered."""
    deal_id = state["deal_id"]

    evt = _event(deal_id, "deliver", FulfillmentStateEnum.DELIVERED, "Content delivered.")

    return {
        "state": FulfillmentStateEnum.DELIVERED,
        "events": [evt],
    }


def complete(state: FulfillmentState) -> dict:
    """Terminal: fulfillment complete."""
    deal_id = state["deal_id"]

    evt = _event(deal_id, "complete", FulfillmentStateEnum.COMPLETED, "Fulfillment complete.")

    _fire_and_forget(
        event_bus.publish("fulfillment.completed", {"deal_id": deal_id})
    )

    return {
        "state": FulfillmentStateEnum.COMPLETED,
        "events": [evt],
    }


def escalated(state: FulfillmentState) -> dict:
    """Terminal: too many revisions, escalate to humans."""
    deal_id = state["deal_id"]

    evt = _event(deal_id, "escalated", FulfillmentStateEnum.ESCALATED, "Escalated to humans.")

    return {
        "state": FulfillmentStateEnum.ESCALATED,
        "events": [evt],
    }


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------


def after_validation(state: FulfillmentState) -> str:
    """Route after validation: approve if passed, request revision if failed."""
    if state.get("state") == FulfillmentStateEnum.CONTENT_VALIDATING:
        return "approve_content"
    return "request_revision"


def after_revision(state: FulfillmentState) -> str:
    """Route after revision: retry if within limit, escalate if over."""
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 3)
    if revision_count >= max_revisions:
        return "escalated"
    return "await_content"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def create_fulfillment_graph() -> StateGraph:
    """Build and compile the fulfillment LangGraph state machine."""
    graph = StateGraph(FulfillmentState)

    # Add nodes
    graph.add_node("generate_brief", generate_brief)
    graph.add_node("await_content", await_content)
    graph.add_node("validate_content", validate_content)
    graph.add_node("request_revision", request_revision)
    graph.add_node("approve_content", approve_content)
    graph.add_node("deliver", deliver)
    graph.add_node("complete", complete)
    graph.add_node("escalated", escalated)

    # Set entry
    graph.set_entry_point("generate_brief")

    # Linear edges
    graph.add_edge("generate_brief", "await_content")
    graph.add_edge("await_content", "validate_content")
    graph.add_edge("approve_content", "deliver")
    graph.add_edge("deliver", "complete")

    # Conditional edges
    graph.add_conditional_edges("validate_content", after_validation, {
        "approve_content": "approve_content",
        "request_revision": "request_revision",
    })
    graph.add_conditional_edges("request_revision", after_revision, {
        "await_content": "await_content",
        "escalated": "escalated",
    })

    # Terminal edges
    graph.add_edge("complete", END)
    graph.add_edge("escalated", END)

    return graph.compile()


def run_fulfillment(deal_agreement: DealAgreement) -> dict:
    """Convenience function: create initial state, invoke the fulfillment graph, return result."""
    initial_state: FulfillmentState = {
        "deal_id": deal_agreement.deal_id,
        "agreement": deal_agreement.model_dump(mode="json"),
        "state": "",
        "creative_brief": None,
        "content_submission": None,
        "validation_result": None,
        "revision_count": 0,
        "max_revisions": 3,
        "events": [],
        "error": None,
    }

    compiled = create_fulfillment_graph()
    result = compiled.invoke(initial_state)
    return result
