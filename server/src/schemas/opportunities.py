"""Opportunity signaling and marketplace schemas."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.schemas.common import ContentFormat, Sport


class OpportunityStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"


class SubjectInfo(BaseModel):
    """An athlete or entity featured in the opportunity."""

    athlete_name: str
    school: str
    sport: Sport
    athlete_id: str | None = None


class AudienceInfo(BaseModel):
    """Projected audience for the opportunity."""

    projected_reach: int = 0
    demographics: str = ""
    trending_score: float = 0.0


class OpportunitySignal(BaseModel):
    """Supply agent signals a new monetizable moment to the exchange."""

    content_description: str
    subjects: list[SubjectInfo]
    audience: AudienceInfo = Field(default_factory=AudienceInfo)
    available_formats: list[ContentFormat] = Field(default_factory=list)
    expiry: datetime | None = None
    min_price: float = 0.0
    sport: Sport = Sport.BASKETBALL


class OpportunityRecord(BaseModel):
    """Internal exchange record for a listed opportunity."""

    opportunity_id: str
    supply_agent_id: str
    supply_org: str
    signal: OpportunitySignal
    status: OpportunityStatus = OpportunityStatus.ACTIVE
    matched_demand_agents: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OpportunityNotification(BaseModel):
    """Sent to demand agents when a matching opportunity is found."""

    opportunity_id: str
    signal: OpportunitySignal
    supply_agent: dict[str, str] = Field(default_factory=dict)
    relevance_score: float = 0.0
    valid_actions: list[str] = Field(default_factory=lambda: ["propose", "pass"])
    constraints: dict[str, str] = Field(default_factory=dict)
