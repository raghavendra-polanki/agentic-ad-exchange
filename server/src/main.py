import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from src.api import agents, brands, content, deals, opportunities, orgs, proposals, stream
from src.conflict import init_conflict_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load conflict graph seed data
    init_conflict_engine()

    from src.engine.managed import ManagedAgentRunner
    from src.persistence import load_athletes_seed, load_state, save_state
    from src.personas import load_personas
    from src.schemas.orgs import RegisterOrgRequest
    from src.store import store

    # 1. Load persona files (BrandRules + ContentRules) into store
    brand_rules, content_rules, agent_seeds = load_personas()

    # 2. If a state.json snapshot exists, restore it (overrides personas).
    #    Otherwise seed store from personas and write the first snapshot.
    if not load_state(store):
        store.brand_rules = brand_rules
        store.content_rules = content_rules
        save_state(store)
        print(f"  Seeded brand_rules: {len(brand_rules)}, content_rules: {len(content_rules)} from personas/")
    else:
        print("  Restored brand_rules + delegations from state.json")

    # 3. Load athletes from seed file (always re-seeded — read-only roster)
    store.athletes = load_athletes_seed()
    print(f"  Seeded {len(store.athletes)} athletes")

    # 4. Seed orgs with fixed keys. One org per persona's organization.
    org_names = {seed["organization"] for seed in agent_seeds}
    org_ids: dict[str, str] = {}
    for org_name in sorted(org_names):
        creds = store.register_org(
            RegisterOrgRequest(name=org_name),
            protocol_base_url="http://localhost:8080",
        )
        org_ids[org_name] = creds.org_id
        print(f"  Seeded org: {org_name} → key={creds.org_key}")
    print(f"AAX Exchange started — conflict engine loaded, {len(org_ids)} orgs seeded")

    # 5. Start managed agents using stable agent_ids from persona filenames
    for seed in agent_seeds:
        try:
            org_id = org_ids.get(seed["organization"], "")
            agent_config = {
                "agent_type": seed["agent_type"],
                "name": seed["agent_name"],
                "organization": seed["organization"],
                "description": seed["description"],
            }
            # For demand agents, surface budget/exclusions to BrandProfile too
            if seed["agent_type"] == "demand" and seed["agent_id"] in store.brand_rules:
                rules = store.brand_rules[seed["agent_id"]]
                agent_config["brand_profile"] = {
                    "budget_per_deal_max": rules.budget_per_deal_max,
                    "budget_per_month_max": rules.budget_per_month_max,
                    "competitor_exclusions": rules.competitor_exclusions,
                    "target_demographics": rules.target_demographics.model_dump(),
                }
            runner = ManagedAgentRunner(
                org_id=org_id,
                agent_config=agent_config,
                agent_id=seed["agent_id"],
            )
            await runner.start()
            print(f"  Started managed agent: {seed['agent_name']} ({seed['agent_type']}) → {runner.agent_id}")
        except Exception as e:
            print(f"  Failed to start agent {seed['agent_name']}: {e}")
    print(f"{len(agent_seeds)} managed agents started")

    # Bridge engine EventBus → SSE bus so LangGraph events reach dashboard
    async def _bridge_events():
        from src.api.stream import sse_bus
        from src.engine.events import event_bus

        queue = event_bus.subscribe()
        try:
            while True:
                event = await queue.get()
                await sse_bus.publish(event["type"], event["data"])
        except asyncio.CancelledError:
            event_bus.unsubscribe(queue)

    bridge_task = asyncio.create_task(_bridge_events())

    yield

    bridge_task.cancel()
    print("AAX Exchange shutting down")


app = FastAPI(
    title="AAX Exchange",
    description="Agentic Ad Exchange — Protocol API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent-facing API (REST + webhooks)
app.include_router(orgs.router, prefix="/api/v1/orgs", tags=["orgs"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(proposals.router, prefix="/api/v1/proposals", tags=["proposals"])
app.include_router(deals.router, prefix="/api/v1/deals", tags=["deals"])
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])

# Brand rules editing
app.include_router(brands.router, prefix="/api/v1/brands", tags=["brands"])

# Dashboard-facing API (SSE)
app.include_router(stream.router, prefix="/api/v1/stream", tags=["stream"])


# ── Protocol files ────────────────────────────────────────────────────

_PROTOCOL_DIR = Path(__file__).parent.parent / "protocol"


@app.get("/protocol.md")
async def get_protocol():
    """Serve the main protocol specification."""
    path = _PROTOCOL_DIR / "protocol.md"
    if path.exists():
        return PlainTextResponse(path.read_text(), media_type="text/markdown")
    return PlainTextResponse("Protocol file not found", status_code=404)


@app.get("/protocol/{filename}")
async def get_protocol_file(filename: str):
    """Serve protocol documentation files."""
    path = _PROTOCOL_DIR / filename
    if path.exists() and path.suffix == ".md":
        return PlainTextResponse(path.read_text(), media_type="text/markdown")
    return PlainTextResponse("Protocol file not found", status_code=404)


# ── Static files (images: opportunities, generated content, brand assets) ────

_STATIC_DIR = Path(__file__).parent.parent / "static"
_STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/health")
async def health():
    from src.gemini.adaptor import gemini
    return {
        "status": "ok",
        "service": "aax-exchange",
        "gemini_available": gemini.available,
    }


# ── Dashboard SPA (must be defined LAST so API/static routes take precedence) ──

from fastapi.responses import FileResponse
from fastapi import HTTPException

_DASHBOARD_DIST = Path(__file__).parent.parent.parent / "dashboard" / "dist"
if _DASHBOARD_DIST.exists():
    _DASHBOARD_ASSETS = _DASHBOARD_DIST / "assets"
    if _DASHBOARD_ASSETS.exists():
        app.mount("/assets", StaticFiles(directory=str(_DASHBOARD_ASSETS)), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Don't catch API/protocol/static routes — those are served above.
        if full_path.startswith(("api/", "static/", "protocol", "health", "assets/")):
            raise HTTPException(status_code=404)
        index = _DASHBOARD_DIST / "index.html"
        if not index.exists():
            raise HTTPException(status_code=404, detail="Dashboard build missing")
        return FileResponse(index)
