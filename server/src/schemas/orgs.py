"""Organization schemas for AAX exchange."""

import secrets
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class RegisterOrgRequest(BaseModel):
    """Request to create an organization on the exchange."""

    name: str
    domain: str = ""
    budget_monthly_max: float = 50000.0
    budget_per_deal_max: float = 5000.0
    competitor_exclusions: list[str] = Field(default_factory=list)
    auto_approve_below: float = 1000.0


class OrgProfile(BaseModel):
    """Organization profile stored by the exchange."""

    org_id: str
    name: str
    domain: str = ""
    org_key: str  # aax_org_xxx — used by agents to register under this org
    budget_monthly_max: float = 50000.0
    budget_per_deal_max: float = 5000.0
    budget_monthly_spent: float = 0.0
    competitor_exclusions: list[str] = Field(default_factory=list)
    auto_approve_below: float = 1000.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True

    @staticmethod
    def generate_org_key() -> str:
        return f"aax_org_{secrets.token_urlsafe(24)}"


class OrgCredentials(BaseModel):
    """Returned on successful org creation."""

    org_id: str
    org_key: str
    protocol_url: str
    message: str = "Organization created. Give the org_key and protocol_url to your agent."
    next_actions: list[dict] = Field(default_factory=lambda: [
        {
            "action": "create_managed_agent",
            "endpoint": "POST /api/v1/agents/managed",
            "description": "Create a managed agent that the platform runs for you",
        },
        {
            "action": "give_to_external_agent",
            "description": (
                "Give your org_key and protocol_url to your own agent. "
                "It will read the protocol and self-register."
            ),
        },
    ])
