"""Tests for the Deal Engine — deal-making and fulfillment state machines."""

from src.engine import (
    create_deal_making_graph,
    create_fulfillment_graph,
    run_deal_making,
    run_fulfillment,
)
from src.schemas.deals import DealAgreement, DealState, DealTerms, FulfillmentState, Price
from src.schemas.opportunities import AudienceInfo, OpportunitySignal, SubjectInfo


def test_deal_making_graph_compiles():
    """The deal-making state machine should compile without errors."""
    graph = create_deal_making_graph()
    assert graph is not None


def test_fulfillment_graph_compiles():
    """The fulfillment state machine should compile without errors."""
    graph = create_fulfillment_graph()
    assert graph is not None


def test_deal_making_happy_path():
    """Run a full deal through the happy path: opportunity -> proposal -> accept -> deal_agreed."""
    signal = OpportunitySignal(
        content_description="Star quarterback throws 5 TDs in rivalry game",
        subjects=[
            SubjectInfo(athlete_name="Marcus Johnson", school="MIT", sport="football")
        ],
        audience=AudienceInfo(projected_reach=50000, trending_score=0.9),
        available_formats=["gameday_graphic"],
        min_price=1000.0,
        sport="football",
    )

    result = run_deal_making(
        opportunity_signal=signal,
        supply_agent_id="pixology-001",
        supply_org="Pixology",
    )

    # Should end in DEAL_AGREED (the default placeholder accepts)
    assert result["state"] == DealState.DEAL_AGREED
    assert result["deal_id"].startswith("deal-")
    assert len(result["events"]) > 0
    assert len(result["proposals"]) > 0
    assert len(result["matched_agents"]) > 0


def test_deal_making_has_audit_events():
    """Every state transition should produce an audit event."""
    signal = OpportunitySignal(
        content_description="Big basketball win",
        subjects=[
            SubjectInfo(athlete_name="Jane Doe", school="Stanford", sport="basketball")
        ],
        sport="basketball",
    )

    result = run_deal_making(signal, "supply-001", "TestOrg")

    events = result["events"]
    actions = [e["action"] for e in events]

    # Should include key lifecycle steps
    assert "list_opportunity" in actions
    assert "pre_screen" in actions
    assert "notify_demand" in actions
    assert "receive_proposal" in actions
    assert "deal_agreed" in actions


def test_fulfillment_happy_path():
    """Run fulfillment: brief -> content -> validate -> approve -> deliver."""
    agreement = DealAgreement(
        deal_id="deal-test-001",
        opportunity_id="opp-test-001",
        supply_agent_id="pixology-001",
        demand_agent_id="nike-001",
        final_terms=DealTerms(
            price=Price(amount=2500.0),
            content_format="gameday_graphic",
            platforms=["instagram"],
        ),
        supply_org="Pixology",
        demand_org="Nike",
    )

    result = run_fulfillment(agreement)

    assert result["state"] == FulfillmentState.COMPLETED
    assert result["deal_id"] == "deal-test-001"
    assert result["creative_brief"] is not None
    assert result["content_submission"] is not None
    assert result["validation_result"] is not None

    events = result["events"]
    actions = [e["action"] for e in events]
    assert "generate_brief" in actions
    assert "await_content" in actions
    assert "validate_content" in actions
    assert "approve_content" in actions
    assert "deliver" in actions
    assert "complete" in actions


def test_fulfillment_revision_count():
    """Verify revision_count stays at 0 when validation passes on first try."""
    agreement = DealAgreement(
        deal_id="deal-test-002",
        opportunity_id="opp-test-002",
        supply_agent_id="pixology-001",
        demand_agent_id="nike-001",
        final_terms=DealTerms(
            price=Price(amount=1000.0),
            content_format="social_post",
            platforms=["twitter"],
        ),
    )

    result = run_fulfillment(agreement)

    # Placeholder validator always passes, so no revisions
    assert result["revision_count"] == 0
    assert result["state"] == FulfillmentState.COMPLETED
