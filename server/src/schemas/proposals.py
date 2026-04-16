"""Proposal, negotiation, and evaluation schemas."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.schemas.deals import DealTerms


class ProposalStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTERED = "countered"
    EXPIRED = "expired"
    CONFLICT_BLOCKED = "conflict_blocked"


class EvaluationDecision(StrEnum):
    ACCEPT = "accept"
    COUNTER = "counter"
    REJECT = "reject"


class ScoreBreakdown(BaseModel):
    """Structured scoring across multiple dimensions."""

    audience_fit: float = 0.0
    brand_alignment: float = 0.0
    price_adequacy: float = 0.0
    content_feasibility: float = 0.0
    projected_roi: float = 0.0
    timeline_fit: float = 0.0
    overall: float = 0.0
    reasoning: str = ""


class Proposal(BaseModel):
    """Demand agent submits a proposal for an opportunity."""

    opportunity_id: str
    demand_agent_id: str = ""
    deal_terms: DealTerms
    reasoning: str = ""
    scores: ScoreBreakdown | None = None


class ProposalRecord(BaseModel):
    """Exchange's internal record of a proposal."""

    proposal_id: str
    opportunity_id: str
    demand_agent_id: str
    demand_org: str
    deal_terms: DealTerms
    status: ProposalStatus = ProposalStatus.PENDING
    scores: ScoreBreakdown | None = None
    reasoning: str = ""
    conflict_result: dict | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    round: int = 1


class ProposalResponse(BaseModel):
    """Supply or demand agent responds to a proposal/counter."""

    decision: EvaluationDecision
    counter_terms: DealTerms | None = None
    scores: ScoreBreakdown | None = None
    reasoning: str = ""


class CounterOffer(BaseModel):
    """Forwarded to the other party when someone counters."""

    proposal_id: str
    counter_terms: DealTerms
    from_agent_id: str = ""
    from_org: str = ""
    round: int = 1
    max_rounds: int = 3
    valid_actions: list[str] = Field(
        default_factory=lambda: ["accept", "counter", "reject"]
    )
    reasoning: str = ""
