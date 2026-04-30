"""Atomic JSON snapshot of editable store state.

Writes to server/data/state.json on every mutation; loads on startup.
Persists brand rules, content rules, and delegations across restarts.
Athletes are re-seeded from athletes_seed.json each boot, so they're not
included in this snapshot.

Single-writer model — the FastAPI process is the only writer. No locks,
no transactions. Atomicity comes from POSIX rename(): write to .tmp,
fsync, rename over the live file.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from src.schemas.delegations import AthleteProfile, DelegationGrant
from src.schemas.personas import BrandRules, ContentRules

logger = logging.getLogger("aax.persistence")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATE_FILE = DATA_DIR / "state.json"
ATHLETES_SEED_FILE = DATA_DIR / "athletes_seed.json"


class PersistedState(BaseModel):
    schema_version: int = 1
    snapshot_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    brand_rules: dict[str, BrandRules] = Field(default_factory=dict)
    content_rules: dict[str, ContentRules] = Field(default_factory=dict)
    delegations: dict[str, DelegationGrant] = Field(default_factory=dict)


def load_athletes_seed() -> dict[str, AthleteProfile]:
    """Read the seed athletes roster (3 entries for the demo)."""
    if not ATHLETES_SEED_FILE.exists():
        logger.warning("Athletes seed file missing: %s", ATHLETES_SEED_FILE)
        return {}
    raw = json.loads(ATHLETES_SEED_FILE.read_text())
    return {a["athlete_id"]: AthleteProfile(**a) for a in raw}


def save_state(store) -> None:
    """Write current editable state to disk atomically.

    Called after any mutation to brand_rules / content_rules / delegations.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = PersistedState(
        snapshot_at=datetime.now(UTC),
        brand_rules=store.brand_rules,
        content_rules=store.content_rules,
        delegations=store.delegations,
    )
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(state.model_dump_json(indent=2))
    tmp.replace(STATE_FILE)  # atomic on POSIX


def load_state(store) -> bool:
    """Load editable state from disk if state.json exists.

    Returns True if state was restored from snapshot, False if no
    snapshot existed (caller should then seed from personas/*.md).
    """
    if not STATE_FILE.exists():
        return False
    try:
        data = json.loads(STATE_FILE.read_text())
        state = PersistedState(**data)
    except Exception as e:
        logger.error("Failed to load state.json (%s) — starting fresh", e)
        return False

    store.brand_rules = dict(state.brand_rules)
    store.content_rules = dict(state.content_rules)
    store.delegations = dict(state.delegations)
    logger.info(
        "Restored from state.json: %d brand_rules, %d content_rules, %d delegations",
        len(store.brand_rules), len(store.content_rules), len(store.delegations),
    )
    return True
