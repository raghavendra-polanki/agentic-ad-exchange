"""Deal terms, state machines, and fulfillment schemas."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.schemas.common import ContentFormat, Platform


class DealState(StrEnum):
    """Deal-making state machine states."""

    OPPORTUNITY_LISTED = "opportunity_listed"
    PRE_SCREENING = "pre_screening"
    MATCHING = "matching"
    AWAITING_PROPOSALS = "awaiting_proposals"
    PROPOSAL_RECEIVED = "proposal_received"
    FINAL_CONFLICT_CHECK = "final_conflict_check"
    AWAITING_SUPPLY_EVAL = "awaiting_supply_evaluation"
    NEGOTIATING = "negotiating"
    AWAITING_HUMAN_APPROVAL = "awaiting_human_approval"
    DEAL_AGREED = "deal_agreed"
    DEAL_REJECTED = "deal_rejected"
    DEAL_EXPIRED = "deal_expired"
    # Fulfillment states (deal continues through these after agreement)
    FULFILLMENT_BRIEF_SENT = "fulfillment_brief_sent"
    FULFILLMENT_CONTENT_SUBMITTED = "fulfillment_content_submitted"
    FULFILLMENT_REVISION_NEEDED = "fulfillment_revision_needed"
    CONTENT_GENERATING = "content_generating"
    COMPLETED = "completed"


class FulfillmentState(StrEnum):
    """Fulfillment pipeline states."""

    BRIEF_GENERATED = "brief_generated"
    CONTENT_GENERATING = "content_generating"
    CONTENT_VALIDATING = "content_validating"
    REVISION_REQUESTED = "revision_requested"
    CONTENT_APPROVED = "content_approved"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    FULFILLMENT_FAILED = "fulfillment_failed"
    ESCALATED = "escalated"


class Price(BaseModel):
    amount: float
    currency: str = "USD"


class BrandAssets(BaseModel):
    """Brand assets to include in content."""

    required_logos: list[str] = Field(default_factory=list)
    required_messaging: str = ""
    color_palette: list[str] = Field(default_factory=list)


class DealTerms(BaseModel):
    """The atomic unit of negotiation — what's being traded."""

    price: Price
    content_format: ContentFormat
    platforms: list[Platform] = Field(default_factory=list)
    usage_rights_duration_days: int = 7
    exclusivity_window_hours: int = 24
    brand_assets: BrandAssets = Field(default_factory=BrandAssets)
    messaging_guidelines: str = ""
    delivery_deadline: datetime | None = None
    compliance_disclosures: list[str] = Field(
        default_factory=lambda: ["#ad", "#NIL"]
    )


class CreativeBrief(BaseModel):
    """Compiled from deal terms — sent to supply agent for content generation."""

    deal_id: str
    deal_terms: DealTerms
    athlete_name: str = ""
    school: str = ""
    sport: str = ""
    moment_description: str = ""
    brand_name: str = ""


class ContentSubmission(BaseModel):
    """Supply agent submits generated content."""

    deal_id: str
    content_url: str
    format: ContentFormat
    metadata: dict[str, str] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationResult(BaseModel):
    """Content validation result from AAX's neutral check."""

    deal_id: str
    passed: bool
    score: float = 0.0
    checks: dict[str, bool] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    revision_instructions: str = ""


class DealAgreement(BaseModel):
    """Created when both sides agree — output of deal-making state machine."""

    deal_id: str
    opportunity_id: str
    supply_agent_id: str
    demand_agent_id: str
    final_terms: DealTerms
    supply_org: str = ""
    demand_org: str = ""
    agreed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DealSummary(BaseModel):
    """Lightweight deal representation for lists and dashboard."""

    deal_id: str
    opportunity_id: str
    supply_org: str
    demand_org: str
    state: DealState | FulfillmentState
    deal_terms: DealTerms | None = None
    moment_description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    negotiation_round: int = 0
    max_rounds: int = 3
    winning_proposal_id: str | None = None
    all_proposal_ids: list[str] = Field(default_factory=list)
