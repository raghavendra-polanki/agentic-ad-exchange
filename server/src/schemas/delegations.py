"""Athlete profiles + delegation grants — NIL provenance enforcement.

Athletes are seeded from server/data/athletes_seed.json (read-only roster
of 3 for the demo). Delegations are mutable, granted/revoked from the
dashboard; signal-time orchestrator enforcement ensures supply agents
can only sell content for athletes that have authorized them.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class AthleteProfile(BaseModel):
    athlete_id: str
    name: str
    school: str
    sport: str
    social_handles: dict[str, str] = Field(default_factory=dict)
    profile_image_url: str | None = None


class DelegationGrant(BaseModel):
    """An athlete (or rights-holder) authorizing a supply agent to monetize.

    Scope-checked at signal time. If a supply agent signals an opportunity
    naming an athlete without an active grant covering the signal's sport
    + window, the orchestrator rejects the signal at the platform.
    """

    grant_id: str
    athlete_id: str
    grantee_agent_id: str

    # Scope
    sports: list[str] = Field(default_factory=lambda: ["*"])
    moment_types: list[str] = Field(default_factory=lambda: ["*"])

    # Window
    valid_from: datetime
    valid_until: datetime
    max_deals_per_week: int | None = None

    # State
    revoked: bool = False
    revoked_at: datetime | None = None
    revoke_reason: str | None = None

    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def covers(self, sport: str | None = None, moment_type: str | None = None) -> bool:
        """Returns True if this grant authorizes the given signal context.

        Caller passes the sport from the signal (and optionally a moment_type
        if/when that field is added). Wildcard "*" in sports or moment_types
        means "any". Revoked or out-of-window grants always return False.
        """
        if self.revoked:
            return False
        now = datetime.now(UTC)
        if not (self.valid_from <= now <= self.valid_until):
            return False
        if sport is not None and "*" not in self.sports:
            if sport not in self.sports:
                return False
        if moment_type is not None and "*" not in self.moment_types:
            if moment_type not in self.moment_types:
                return False
        return True
