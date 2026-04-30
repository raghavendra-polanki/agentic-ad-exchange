"""Athletes (read-only roster) + delegation grants API.

Athletes are seeded once from server/data/athletes_seed.json — no creation
endpoint for the demo. Delegations are mutable: granted by an athlete (or
their rights-holder) to a supply agent for a scoped window. Enforced at
signal time by orchestrator.handle_signal_opportunity.
"""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.persistence import save_state
from src.schemas.delegations import AthleteProfile, DelegationGrant
from src.store import store

router = APIRouter()


class AthleteWithDelegations(BaseModel):
    profile: AthleteProfile
    active_delegations: list[DelegationGrant] = Field(default_factory=list)
    past_delegations: list[DelegationGrant] = Field(default_factory=list)


class GrantDelegationRequest(BaseModel):
    grantee_agent_id: str
    sports: list[str] = Field(default_factory=lambda: ["*"])
    moment_types: list[str] = Field(default_factory=lambda: ["*"])
    duration_days: int = 30
    max_deals_per_week: int | None = None


class RevokeDelegationRequest(BaseModel):
    reason: str | None = None


@router.get("")
@router.get("/")
async def list_athletes() -> list[AthleteProfile]:
    return store.list_athletes()


@router.get("/{athlete_id}")
async def get_athlete(athlete_id: str) -> AthleteWithDelegations:
    profile = store.get_athlete(athlete_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Athlete not found")

    grants = store.list_delegations_for_athlete(athlete_id)
    active = [g for g in grants if g.covers()]
    past = [g for g in grants if not g.covers()]
    return AthleteWithDelegations(
        profile=profile, active_delegations=active, past_delegations=past,
    )


@router.post("/{athlete_id}/delegations")
async def grant_delegation(
    athlete_id: str, req: GrantDelegationRequest,
) -> DelegationGrant:
    if not store.get_athlete(athlete_id):
        raise HTTPException(status_code=404, detail="Athlete not found")
    if not store.get_agent(req.grantee_agent_id):
        raise HTTPException(status_code=404, detail="Grantee agent not found")

    now = datetime.now(UTC)
    grant = DelegationGrant(
        grant_id=f"del_{uuid.uuid4().hex[:10]}",
        athlete_id=athlete_id,
        grantee_agent_id=req.grantee_agent_id,
        sports=req.sports or ["*"],
        moment_types=req.moment_types or ["*"],
        valid_from=now,
        valid_until=now + timedelta(days=req.duration_days),
        max_deals_per_week=req.max_deals_per_week,
    )
    store.delegations[grant.grant_id] = grant
    save_state(store)
    return grant


router_delegations = APIRouter()


@router_delegations.delete("/{grant_id}")
async def revoke_delegation(grant_id: str, req: RevokeDelegationRequest | None = None) -> DelegationGrant:
    grant = store.delegations.get(grant_id)
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")
    if grant.revoked:
        return grant  # idempotent
    grant.revoked = True
    grant.revoked_at = datetime.now(UTC)
    if req:
        grant.revoke_reason = req.reason
    store.delegations[grant_id] = grant
    save_state(store)
    return grant
