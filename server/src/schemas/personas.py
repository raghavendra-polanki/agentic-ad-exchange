"""Persona configs — editable rules for managed brand and content agents.

Each managed agent has a persona file (personas/<agent_id>.md) with YAML
frontmatter for hard, programmatically-enforced rules and a markdown body
for soft, LLM-injected voice guidance. On startup the server seeds these
into the in-memory store; subsequent edits flow through state.json.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class TargetDemographics(BaseModel):
    age_range: str | None = None
    interests: list[str] = Field(default_factory=list)


class BrandRules(BaseModel):
    """Editable config for a demand (brand) agent."""

    agent_id: str
    brand: str
    agent_name: str

    # Hard constraints (enforced in code, not by the LLM)
    budget_per_deal_max: int
    budget_per_month_max: int
    auto_approve_threshold_usd: int = 1000
    competitor_exclusions: list[str] = Field(default_factory=list)
    target_demographics: TargetDemographics = Field(default_factory=TargetDemographics)

    # Soft guidance — markdown body, injected into Gemini system prompt
    voice_md: str = ""

    # Audit
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: int = 1


class ContentRules(BaseModel):
    """Editable config for a supply (content) agent."""

    agent_id: str
    service: str
    agent_name: str

    min_price_per_deal: int = 100
    max_concurrent_deals: int = 5
    blocked_categories: list[str] = Field(default_factory=list)

    voice_md: str = ""

    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: int = 1
