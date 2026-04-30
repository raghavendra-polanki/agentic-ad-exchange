"""Brand rules editing API.

GET    /api/v1/brands              List all brand rules
GET    /api/v1/brands/{agent_id}   Read one
PATCH  /api/v1/brands/{agent_id}   Update fields (partial)

Edits write through to state.json via persistence.save_state().
The managed agent's reasoning loop re-reads from store on every Gemini
call, so changes take effect on the next bid without a restart.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.persistence import save_state
from src.schemas.personas import BrandRules, TargetDemographics
from src.store import store

router = APIRouter()


class BrandRulesPatch(BaseModel):
    """Partial-update payload — every field is optional."""

    brand: str | None = None
    agent_name: str | None = None
    budget_per_deal_max: int | None = None
    budget_per_month_max: int | None = None
    auto_approve_threshold_usd: int | None = None
    competitor_exclusions: list[str] | None = None
    target_demographics: TargetDemographics | None = None
    voice_md: str | None = None


@router.get("/")
async def list_brand_rules() -> list[BrandRules]:
    return store.list_brand_rules()


@router.get("/{agent_id}")
async def get_brand_rules(agent_id: str) -> BrandRules:
    rules = store.get_brand_rules(agent_id)
    if not rules:
        raise HTTPException(status_code=404, detail="Brand rules not found")
    return rules


@router.patch("/{agent_id}")
async def update_brand_rules(agent_id: str, patch: BrandRulesPatch) -> BrandRules:
    rules = store.get_brand_rules(agent_id)
    if not rules:
        raise HTTPException(status_code=404, detail="Brand rules not found")

    updates = patch.model_dump(exclude_unset=True)
    if not updates:
        return rules  # nothing to do

    new_data = rules.model_dump()
    new_data.update(updates)
    new_data["updated_at"] = datetime.now(UTC)
    new_data["version"] = rules.version + 1

    new_rules = BrandRules(**new_data)
    store.brand_rules[agent_id] = new_rules
    save_state(store)
    return new_rules
