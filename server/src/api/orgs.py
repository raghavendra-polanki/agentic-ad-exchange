"""Organization registration and management routes."""

from fastapi import APIRouter, Depends, Request

from src.api.deps import get_current_org
from src.api.stream import sse_bus
from src.schemas.orgs import OrgCredentials, OrgProfile, RegisterOrgRequest
from src.store import store

router = APIRouter()


@router.post("/register", response_model=OrgCredentials)
async def register_org(req: RegisterOrgRequest, request: Request) -> OrgCredentials:
    """Register a new organization on the exchange."""
    protocol_base_url = str(request.base_url).rstrip("/")
    creds = store.register_org(req, protocol_base_url)

    await sse_bus.publish("org_registered", {
        "org_id": creds.org_id,
        "name": req.name,
    })

    return creds


@router.get("/me", response_model=OrgProfile)
async def get_org_me(org: OrgProfile = Depends(get_current_org)) -> OrgProfile:
    """Get the authenticated organization's profile."""
    return org


@router.get("/")
async def list_orgs():
    """List all registered organizations (for dashboard, no auth)."""
    return store.get_all_orgs_summary()
