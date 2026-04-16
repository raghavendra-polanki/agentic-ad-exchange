"""Conflict graph and compliance checking schemas."""

from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ConflictStatus(StrEnum):
    CLEARED = "cleared"
    BLOCKED = "blocked"


class ConflictType(StrEnum):
    SCHOOL_EXCLUSIVE_SPONSOR = "school_exclusive_sponsor"
    ATHLETE_NIL_DEAL = "athlete_nil_deal"
    BRAND_COMPETITOR = "brand_competitor"
    CONFERENCE_MEDIA_RIGHTS = "conference_media_rights"


class ConflictExplanation(BaseModel):
    """Structured explanation of why a conflict was detected."""

    conflict_type: ConflictType
    description: str
    entities_involved: list[str] = Field(default_factory=list)
    chain: str = ""


class ConflictCheckResult(BaseModel):
    """Result of a pre-screen or final conflict check."""

    status: ConflictStatus
    brand: str = ""
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    conflicts: list[ConflictExplanation] = Field(default_factory=list)
    check_type: str = "pre_screen"


# --- Conflict Graph Entities (used by the conflict engine) ---


class School(BaseModel):
    school_id: str
    name: str
    conference: str = ""


class Athlete(BaseModel):
    athlete_id: str
    name: str
    school_id: str
    sport: str = ""


class Brand(BaseModel):
    brand_id: str
    name: str
    category: str = ""


class Conference(BaseModel):
    conference_id: str
    name: str


class SponsorshipEdge(BaseModel):
    """School ──[exclusive_sponsor]──► Brand."""

    school_id: str
    brand_id: str
    category: str
    start_date: date
    end_date: date


class NilDealEdge(BaseModel):
    """Athlete ──[nil_deal]──► Brand."""

    athlete_id: str
    brand_id: str
    deal_type: str = "endorsement"
    start_date: date
    end_date: date


class CompetesWithEdge(BaseModel):
    """Brand ──[competes_with]──► Brand (bidirectional)."""

    brand_a_id: str
    brand_b_id: str
    category: str = ""


class ConflictGraph(BaseModel):
    """The full conflict graph — loaded from seed data."""

    schools: list[School] = Field(default_factory=list)
    athletes: list[Athlete] = Field(default_factory=list)
    brands: list[Brand] = Field(default_factory=list)
    conferences: list[Conference] = Field(default_factory=list)
    sponsorships: list[SponsorshipEdge] = Field(default_factory=list)
    nil_deals: list[NilDealEdge] = Field(default_factory=list)
    competitors: list[CompetesWithEdge] = Field(default_factory=list)
