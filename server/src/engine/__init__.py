"""AAX Deal Engine — LangGraph state machines for deal-making and fulfillment."""

from src.engine.deal_making import create_deal_making_graph, run_deal_making
from src.engine.events import EventBus, event_bus
from src.engine.fulfillment import create_fulfillment_graph, run_fulfillment
from src.engine.orchestrator import (
    handle_respond_to_proposal,
    handle_signal_opportunity,
    handle_submit_proposal,
)
from src.engine.state import DealMakingState, FulfillmentState

__all__ = [
    "EventBus",
    "DealMakingState",
    "FulfillmentState",
    "create_deal_making_graph",
    "create_fulfillment_graph",
    "event_bus",
    "handle_respond_to_proposal",
    "handle_signal_opportunity",
    "handle_submit_proposal",
    "run_deal_making",
    "run_fulfillment",
]
