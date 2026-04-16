"""LangGraph state definitions for deal-making and fulfillment state machines."""

from typing import Annotated, TypedDict


def _append(existing: list, new: list) -> list:
    """Reducer that appends new items to the existing list."""
    return existing + new


class DealMakingState(TypedDict, total=False):
    """State for the deal-making LangGraph state machine."""

    deal_id: str
    opportunity: dict  # serialized OpportunityRecord
    state: str  # DealState value
    proposals: Annotated[list[dict], _append]  # serialized ProposalRecords
    active_proposal: dict | None
    conflict_results: Annotated[list[dict], _append]  # pre-screen results
    negotiation_round: int
    max_rounds: int  # default 3
    matched_agents: list[str]  # demand agent IDs that passed pre-screen
    events: Annotated[list[dict], _append]  # audit trail
    error: str | None


class FulfillmentState(TypedDict, total=False):
    """State for the fulfillment LangGraph state machine."""

    deal_id: str
    agreement: dict  # serialized DealAgreement
    state: str  # FulfillmentState value
    creative_brief: dict | None
    content_submission: dict | None
    validation_result: dict | None
    revision_count: int
    max_revisions: int  # default 3
    events: Annotated[list[dict], _append]
    error: str | None
