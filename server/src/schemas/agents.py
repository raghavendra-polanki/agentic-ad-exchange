"""Agent registration and profile schemas."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from src.schemas.common import ContentFormat, Sport


class AgentType(StrEnum):
    SUPPLY = "supply"
    DEMAND = "demand"


class BrandProfile(BaseModel):
    """Brand-specific configuration for demand agents."""

    tone: str = ""
    tagline: str = ""
    target_demographics: dict[str, Any] = Field(default_factory=dict)
    budget_per_deal_max: float = 5000.0
    budget_per_month_max: float = 50000.0
    competitor_exclusions: list[str] = Field(default_factory=list)
    auto_approve_below: float = 1000.0


class SupplyCapabilities(BaseModel):
    """What a supply agent can produce."""

    content_formats: list[ContentFormat] = Field(default_factory=list)
    sports: list[Sport] = Field(default_factory=list)
    turnaround_minutes: int = 30
    max_concurrent_deals: int = 5


class StandingQuery(BaseModel):
    """Persistent interest filter for demand agents."""

    sport: Sport | None = None
    min_reach: int = 0
    conferences: list[str] = Field(default_factory=list)
    content_formats: list[ContentFormat] = Field(default_factory=list)
    max_price: float | None = None


class RegisterAgentRequest(BaseModel):
    """Request to register a new agent on the exchange."""

    agent_type: AgentType
    name: str
    organization: str
    description: str = ""
    callback_url: HttpUrl | None = None

    # Type-specific profiles
    brand_profile: BrandProfile | None = None
    supply_capabilities: SupplyCapabilities | None = None

    # Standing queries (demand agents)
    standing_queries: list[StandingQuery] = Field(default_factory=list)


class UpdateAgentRequest(BaseModel):
    """Update an agent's profile."""

    callback_url: HttpUrl | None = None
    brand_profile: BrandProfile | None = None
    supply_capabilities: SupplyCapabilities | None = None
    standing_queries: list[StandingQuery] | None = None


class AgentCredentials(BaseModel):
    """Returned on successful registration."""

    agent_id: str
    api_key: str
    webhook_secret: str = ""
    status: str = "registered"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SupplyAgentProfile(BaseModel):
    """Full supply agent profile stored by the exchange."""

    agent_id: str
    name: str
    organization: str
    agent_type: AgentType = AgentType.SUPPLY
    description: str = ""
    callback_url: str | None = None
    capabilities: SupplyCapabilities = Field(default_factory=SupplyCapabilities)
    is_active: bool = True
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reputation_score: float = 5.0


class DemandAgentProfile(BaseModel):
    """Full demand agent profile stored by the exchange."""

    agent_id: str
    name: str
    organization: str
    agent_type: AgentType = AgentType.DEMAND
    description: str = ""
    callback_url: str | None = None
    brand_profile: BrandProfile = Field(default_factory=BrandProfile)
    standing_queries: list[StandingQuery] = Field(default_factory=list)
    is_active: bool = True
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reputation_score: float = 5.0
    total_spend: float = 0.0
