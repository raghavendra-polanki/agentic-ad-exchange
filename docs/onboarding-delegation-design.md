# Onboarding & Delegation — Design Doc

**Status:** Draft (2026-04-29) · **Author:** Raghav + Claude
**Goal:** Replace hardcoded `main.py` agent config with editable brand personas and add NIL provenance enforcement via delegation grants — without introducing auth, multi-tenancy, or a database.

---

## What this is, what it isn't

**Is:** Three small, additive features that turn the demo from "config-as-code" into "config-as-data" while introducing the seam OpenCLAW will plug into.

**Isn't:** Auth. Org/user management. Athlete-creation UI. Cryptographic delegation signing. Cloud storage. Production hardening.

### The three features

| Feature | What it does | Why now |
|---|---|---|
| **Editable brand personas** (`BRAND.md`) | Demand agents read their config from markdown files at runtime; dashboard form + raw editors save back | Today changing Nike's budget needs `main.py` edit + restart. Real exchanges have editable rules. |
| **Delegations** (athlete → supply agent) | Signal-time enforcement that the supply agent has rights to monetize the named athlete + scope | NIL provenance is the most academically embarrassing gap — supply agents currently sell anyone's image |
| **Auto-approve threshold** + `AWAITING_HUMAN_APPROVAL` state | Deals above a brand-configured threshold pause for a dashboard approve/reject | This is the seam OpenCLAW plugs into next. With it, chat layer becomes substantive. |

---

## Service-level architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Single FastAPI process                    │
│                                                              │
│   ┌─ store.py (in-memory) ──────────────────────────────┐    │
│   │  brand_rules  delegations  athletes  agents  deals  │    │
│   └─────────────────────┬───────────────────────────────┘    │
│                         │ write-on-mutation                  │
│                         ▼                                    │
│              server/data/state.json                          │
│                         ▲                                    │
│                         │ read on startup                    │
│   ┌─ personas/<agent_id>.md ────────────────────────────┐    │
│   │  YAML frontmatter (rules) + markdown body (voice)   │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                              │
│   server/static/                                             │
│     demo/         — bundled, immutable                       │
│     opportunities/— uploaded at runtime, local FS            │
│     generated/    — Gemini output, local FS                  │
└──────────────────────────────────────────────────────────────┘
```

- **Persistence:** single JSON file (`server/data/state.json`). Atomic write (`.tmp` + `rename`). Loaded on startup. No DB.
- **Image storage:** local FS, same as today. Restarts wipe `generated/` and `opportunities/` — fine for demo.
- **Hosting:** out of scope. Manual EC2 + HAProxy later.

---

## 1. Persona file format

### Filename & location

- `personas/<agent_id>.md` at repo root (alongside `agents/` for self-hosted samples).
- Demand agents: brand persona. Supply agents: content persona. Same parser, different fields.
- One file per managed agent; on startup, server scans the directory and seeds `brand_rules` / `content_rules` into `store`.

### Schema — demand (`personas/agt_nike_basketball.md`)

```markdown
---
agent_type: demand
brand: Nike Basketball
agent_name: Nike Basketball Agent
budget_per_deal_max: 5000
budget_per_month_max: 50000
auto_approve_threshold_usd: 1000
competitor_exclusions:
  - Adidas
  - Under Armour
  - New Balance
target_demographics:
  age_range: 18-35
  interests: [basketball, athletics]
---

# Nike Basketball — Voice

We rep the basketball line *exclusively*. Pass on football, hockey, soccer.

## What we love
- Rivalry games (Duke vs. UNC, Kentucky vs. Louisville)
- Dunks, last-second shots, championship moments
- Blue-blood programs

## What we never bid on
- Locker-room celebrations
- Anything below 50k reach

## Voice
Bold, empowering, aspirational — the "Just Do It" register.
```

### Schema — supply (`personas/agt_pixology_supply.md`)

```markdown
---
agent_type: supply
service: Pixology Content Agent
agent_name: Pixology Content Agent
min_price_per_deal: 100
max_concurrent_deals: 5
blocked_categories: []
---

# Pixology — Voice

Premium content creation for college athletics. Broadcast-grade, NCAA-compliant.

## How we negotiate
- Respect the listed `min_price` as the only hard floor
- For deals above floor, accept quickly — volume matters
- Counter up ~20% only if the bid is exactly at floor and there's room
```

### Parser

- Library: `python-frontmatter` (or 30 lines of regex + `yaml.safe_load`).
- Output: `(metadata: dict, body: str)`.
- Body becomes `voice_md` field on the rules entity, injected verbatim into the Gemini system prompt.

### Migration

One-shot script `scripts/migrate_personas.py`:
1. Read `seed_agents` from current `main.py`.
2. For each, write `personas/<agent_id>.md` with frontmatter from `brand_profile` + body lifted from `description` (which we recently sharpened — already useful voice content).
3. Replace the `seed_agents` block in `main.py` with a `load_personas()` call.

After migration, editing a brand = editing a markdown file (or saving via dashboard, which writes the same file).

---

## 2. Store entities (Pydantic)

```python
# server/src/schemas/personas.py (new file)

class BrandRules(BaseModel):
    agent_id: str
    brand: str
    agent_name: str

    # Hard constraints (enforced in code)
    budget_per_deal_max: int
    budget_per_month_max: int
    auto_approve_threshold_usd: int = 1000
    competitor_exclusions: list[str] = []
    target_age_range: str | None = None
    target_interests: list[str] = []

    # Soft guidance (injected into Gemini system prompt)
    voice_md: str

    # Audit
    updated_at: datetime
    version: int = 1


class ContentRules(BaseModel):
    agent_id: str
    service: str
    agent_name: str

    min_price_per_deal: int = 100
    max_concurrent_deals: int = 5
    blocked_categories: list[str] = []

    voice_md: str
    updated_at: datetime
    version: int = 1
```

```python
# server/src/schemas/delegations.py (new file)

class AthleteProfile(BaseModel):
    athlete_id: str           # "ath_cooper_reed"
    name: str
    school: str
    sport: str
    social_handles: dict[str, str] = {}
    profile_image_url: str | None = None


class DelegationGrant(BaseModel):
    grant_id: str             # uuid
    athlete_id: str
    grantee_agent_id: str

    # Scope
    sports: list[str]         # ["basketball"] or ["*"]
    moment_types: list[str]   # ["gameday", "milestone"] or ["*"]

    # Window
    valid_from: datetime
    valid_until: datetime
    max_deals_per_week: int | None = None

    # State
    revoked: bool = False
    revoked_at: datetime | None = None
    revoke_reason: str | None = None

    created_at: datetime

    def covers(self, signal) -> bool:
        """Returns True if this grant authorizes the given signal."""
        if self.revoked:
            return False
        now = datetime.now(UTC)
        if not (self.valid_from <= now <= self.valid_until):
            return False
        signal_sport = signal.subjects[0].sport if signal.subjects else ""
        if "*" not in self.sports and signal_sport not in self.sports:
            return False
        # moment_types check — derive from signal.content_description heuristically
        # or add a moment_type field to the signal schema (recommended)
        return True
```

### Athletes seed file

`server/data/athletes_seed.json` — 3 entries, loaded on startup:

```json
[
  {"athlete_id":"ath_cooper_reed","name":"Cooper Reed","school":"Duke","sport":"basketball","social_handles":{"instagram":"@coopreed"}},
  {"athlete_id":"ath_marcus_johnson","name":"Marcus Johnson","school":"Ohio State","sport":"football","social_handles":{"instagram":"@mj_buckeye"}},
  {"athlete_id":"ath_mit_engineers","name":"MIT Engineers","school":"MIT","sport":"hockey","social_handles":{"instagram":"@mitengineers"}}
]
```

The Signal Opportunity preset for each demo image now references `athlete_id` instead of typing free strings.

---

## 3. Persistence — `state.json`

```python
# server/src/store_persist.py (new file)

class PersistedState(BaseModel):
    schema_version: int = 1
    snapshot_at: datetime
    brand_rules: dict[str, BrandRules]
    content_rules: dict[str, ContentRules]
    delegations: dict[str, DelegationGrant]
    # athletes excluded — seeded from athletes_seed.json on every boot

STATE_FILE = Path("server/data/state.json")

def save_state():
    """Write-on-mutation. Atomic via tmp + rename."""
    state = PersistedState(
        snapshot_at=datetime.now(UTC),
        brand_rules=store.brand_rules,
        content_rules=store.content_rules,
        delegations=store.delegations,
    )
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(state.model_dump_json(indent=2))
    tmp.replace(STATE_FILE)  # atomic on POSIX

def load_state():
    if STATE_FILE.exists():
        # restore from snapshot
        data = json.loads(STATE_FILE.read_text())
        ...
    else:
        # first boot — seed from personas/*.md
        for path in Path("personas").glob("*.md"):
            seed_from_md(path)
        save_state()
```

- `save_state()` called after every mutation (PATCH brand rules, POST/DELETE delegation, etc.).
- No transactions, no migrations, no locks. Single-writer (the FastAPI process). Good enough for a demo.
- Reset state during demo prep: `rm server/data/state.json` and restart.

---

## 4. API endpoints (5 new)

```
# Brand rules
GET    /api/v1/brands                       List all brand rules
GET    /api/v1/brands/{agent_id}            Get one (structured + voice_md)
PATCH  /api/v1/brands/{agent_id}            Update (partial — structured fields, voice_md, or both)

# Athletes (read-only, seeded)
GET    /api/v1/athletes                     List all athletes
GET    /api/v1/athletes/{athlete_id}        Get one with active delegations

# Delegations
POST   /api/v1/athletes/{athlete_id}/delegations    Create grant
DELETE /api/v1/delegations/{grant_id}              Revoke (soft — sets revoked=true)

# Deal approval
POST   /api/v1/deals/{deal_id}/approve              Resume an AWAITING_HUMAN_APPROVAL deal
POST   /api/v1/deals/{deal_id}/reject               Reject an awaiting deal
```

All editable endpoints call `save_state()` after mutation.

---

## 5. Orchestrator hook points (2)

### Hook A — Delegation check at signal time

`server/src/engine/orchestrator.py::handle_signal_opportunity`, before creating the opportunity:

```python
for subject in signal.subjects:
    athlete = store.find_athlete(name=subject.athlete_name, school=subject.school)
    if athlete is None:
        # Unknown athlete in seed roster — for the demo we accept this with a warning
        # (real product would require athlete pre-registration)
        logger.warning("Signal references unknown athlete: %s", subject.athlete_name)
        continue
    grant = store.find_active_delegation(athlete.athlete_id, agent.agent_id)
    if not grant or not grant.covers(signal):
        return {
            "status": "rejected",
            "reason": "no_active_delegation",
            "athlete": athlete.name,
            "supply_agent": agent.organization,
        }
```

Also publish a `delegation_rejected` SSE event so the dashboard renders it cleanly.

### Hook B — Auto-approve gate at proposal-accept time

`server/src/engine/managed.py::_handle_proposal`, when supply agent decides "accept":

```python
if decision == "accept":
    rules = store.get_brand_rules(demand_agent_id)
    if rules and price > rules.auto_approve_threshold_usd:
        # Pause for human approval instead of finalizing
        await orchestrator.pause_deal_for_approval(
            deal_id=deal_id,
            proposal_id=proposal_id,
            price=price,
            threshold=rules.auto_approve_threshold_usd,
        )
        return  # do NOT POST /respond
```

`pause_deal_for_approval`:
1. Sets deal state to `DealState.AWAITING_HUMAN_APPROVAL`.
2. Writes deal event with reason + threshold.
3. Emits `human_approval_needed` SSE event with deal_id, brand, price, threshold.
4. Dashboard renders an "Approve / Reject" banner on the deal detail page.

When the human clicks Approve, `POST /deals/{id}/approve` finally fires the supply agent's "accept" decision (the deferred POST to `/proposals/{id}/respond`).

---

## 6. Dashboard pages (3)

### Page 1 — `/brands`

- **List view** (`/brands`): cards for each demand agent showing brand name, budget cap, auto-approve threshold, exclusion count, last-updated timestamp.
- **Edit view** (`/brands/{agent_id}`): two tabs.
  - **Form** tab: structured fields as inputs (number boxes, chip lists for exclusions/interests), markdown textarea for voice with side-by-side preview.
  - **Raw** tab: full BRAND.md as a code editor (`<textarea>` with monospace styling — Monaco is overkill for v1).
  - Save button writes both — server parses raw on save and reconciles structured fields.
  - Sidebar: version history (just a list of `updated_at` + version number for now).

### Page 2 — `/athletes`

- List of 3 athlete cards (read-only) with name, school, sport, social handles, profile photo placeholder.
- Click an athlete → `/athletes/{id}` panel:
  - **Active delegations** table: grantee agent, scope summary ("basketball, gameday/milestone"), expires-in, "Revoke" button.
  - **Grant new delegation** form: select supply agent (dropdown), select sports (chips), select moment types (chips), pick duration (7d / 30d / custom), submit.
  - **Past delegations** collapsed section (revoked + expired).

### Page 3 — DealDetail.tsx extension

Add a yellow approval banner above the thread when `deal.state === 'awaiting_human_approval'`:

> ⏸ **Approval needed** — Nike's auto-approve threshold is $1,000. This deal would close at $2,400.
> [Approve] [Reject with reason]

`Approve` → POST `/deals/{id}/approve` → orchestrator resumes the supply agent's "accept" → deal closes normally.
`Reject` → POST `/deals/{id}/reject` → deal moves to `DEAL_REJECTED` with `reason: "human_rejected"` + the human's text.

---

## 7. Build order (suggested)

1. **Persona files & loader** — write `personas/*.md`, parser, `BrandRules` / `ContentRules` Pydantic models, store fields, `load_personas()` call. Replace `seed_agents` in `main.py`. *No UI yet.*
2. **JSON snapshot** — `save_state()` / `load_state()` wired to all mutations.
3. **Brand rules API + Form view** — `GET/PATCH /brands`, form-only dashboard page (skip raw view). Demand agent reasoning re-reads brand_rules from store at every Gemini call.
4. **Athletes seed + read-only `/athletes` page**.
5. **Delegations API + Grant/Revoke UI**, signal-time enforcement.
6. **Auto-approve threshold + `AWAITING_HUMAN_APPROVAL` state + dashboard approval banner**.
7. **Raw editor tab** for BRAND.md (nice-to-have, can defer).

Each step is independently demoable. If we hit time pressure, we can ship after step 5 (delegations) — that's the most academically interesting feature on its own.

---

## 8. Open questions

- **Moment-type taxonomy.** Delegations scope by `moment_type` (gameday / milestone / celebration / training). Today the signal schema doesn't have this field — should we add it, or derive from `content_description` with Gemini? Lean: add the field, default to "gameday".
- **Athlete matching from signal.** Today `signal.subjects[].athlete_name` is a free string. Should we change it to require `athlete_id`? Lean: yes, but only after (1) is done so the form has a dropdown of seeded athletes.
- **Concurrent deal counter.** `max_concurrent_deals` on supply, `max_deals_per_week` on delegation — both require querying recent deal history. Define in code, defer enforcement to a follow-up.
- **What does "approve" mean exactly?** When the human approves a held deal, we resume the supply agent's accept. But what if the supply agent has *already* committed to other proposals during the wait? Lean: deal_id is locked in `AWAITING_HUMAN_APPROVAL`; supply agent can still negotiate other deals concurrently — they're independent.

---

## 9. Out of scope (will not do in this milestone)

- Auth, login, user accounts
- Multi-org tenancy
- Athlete creation UI (seed-only roster of 3)
- Brand creation UI (seed-only — edit existing brands)
- Cryptographic signing of delegations
- Real revocation propagation to in-flight deals (revocation only blocks future signals)
- Cloud storage / GCS / Firestore
- Deployment automation
- OpenCLAW chat layer (the next milestone — this design intentionally exposes the seam)
