import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from src.api import agents, content, deals, opportunities, orgs, proposals, stream
from src.conflict import init_conflict_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load conflict graph seed data + seed orgs
    init_conflict_engine()

    # Seed default orgs with fixed keys for easy testing
    from src.schemas.orgs import RegisterOrgRequest
    from src.store import store
    org_ids: dict[str, str] = {}
    for org_name in ["Pixology", "Nike", "Gatorade", "Campus Pizza"]:
        creds = store.register_org(
            RegisterOrgRequest(name=org_name),
            protocol_base_url="http://localhost:8080",
        )
        org_ids[org_name] = creds.org_id
        print(f"  Seeded org: {org_name} → key={creds.org_key}")
    print("AAX Exchange started — conflict engine loaded, 4 orgs seeded")

    # Seed default managed agents (1 supply + 3 demand)
    from src.engine.managed import ManagedAgentRunner
    seed_agents = [
        {
            "org_name": "Pixology",
            "config": {
                "agent_type": "supply",
                "name": "Pixology Content Agent",
                "organization": "Pixology",
                "description": "Premium content creation for college athletics — gameday graphics, social posts, highlight reels.",
            },
        },
        {
            "org_name": "Nike",
            "config": {
                "agent_type": "demand",
                "name": "Nike Basketball Agent",
                "organization": "Nike",
                "description": (
                    "NIKE BASKETBALL DIVISION ONLY — this agent reps the basketball line "
                    "exclusively. Bids aggressively on high-profile basketball moments: "
                    "rivalry games, dunks, championship plays at blue-blood programs "
                    "(Duke, UNC, Kentucky, UConn). Prefers moments where Nike footwear, "
                    "apparel, or the Nike basketball is already visible. "
                    "HARD FILTER: must_pass on any non-basketball moment (football, "
                    "hockey, soccer, etc.) — those are handled by other Nike divisions, "
                    "not this agent. Also passes on locker-room/casual moments and "
                    "anything with <50k reach."
                ),
                "brand_profile": {
                    "tone": "Bold, empowering, aspirational",
                    "tagline": "Just Do It",
                    "target_demographics": {"age_range": "18-35", "interests": ["basketball", "athletics"]},
                    "budget_per_deal_max": 5000,
                    "budget_per_month_max": 50000,
                    "competitor_exclusions": ["Adidas", "Under Armour", "New Balance"],
                },
            },
        },
        {
            "org_name": "Gatorade",
            "config": {
                "agent_type": "demand",
                "name": "Gatorade Sports Agent",
                "organization": "Gatorade",
                "description": (
                    "PERFORMANCE & CLUTCH MOMENTS. Gatorade bids on sweat-soaked, "
                    "high-effort athletic moments — game-winning plays, endurance, "
                    "overtime grit, rain/mud/weather, last-second drives. Football, "
                    "soccer, track, and football-adjacent sports are sweet spots. "
                    "Values hydration narrative over brand-logo visibility. "
                    "Passes on basketball-only dunk moments (Nike territory) and "
                    "locker-room celebrations (no performance narrative)."
                ),
                "brand_profile": {
                    "tone": "Energetic, performance-focused, authentic",
                    "tagline": "Is It In You?",
                    "target_demographics": {"age_range": "18-30", "interests": ["football", "endurance_sports", "fitness"]},
                    "budget_per_deal_max": 3000,
                    "budget_per_month_max": 25000,
                    "competitor_exclusions": ["BodyArmor", "Powerade", "Prime Hydration"],
                },
            },
        },
        {
            "org_name": "Campus Pizza",
            "config": {
                "agent_type": "demand",
                "name": "Campus Pizza Agent",
                "organization": "Campus Pizza",
                "description": (
                    "HYPER-LOCAL MIT CELEBRATIONS ONLY. Campus Pizza is a tiny shop on "
                    "Mass Ave — bids exclusively on MIT-campus moments under $200. "
                    "LOVES locker-room celebrations, intramural wins, dorm-life energy, "
                    "and casual hangout scenes. IGNORES anything over $300 min-price "
                    "(out of budget) and anything non-MIT. Small reach (<30k) is FINE — "
                    "campus audience converts well for a local shop."
                ),
                "brand_profile": {
                    "tone": "Casual, fun, community-driven",
                    "tagline": "Fuel Your Game Day",
                    "target_demographics": {"age_range": "18-24", "interests": ["college_life", "food", "MIT"]},
                    "budget_per_deal_max": 200,
                    "budget_per_month_max": 1000,
                    "competitor_exclusions": [],
                },
            },
        },
    ]
    for seed in seed_agents:
        try:
            org_id = org_ids.get(seed["org_name"], "")
            runner = ManagedAgentRunner(org_id=org_id, agent_config=seed["config"])
            await runner.start()
            print(f"  Seeded agent: {seed['config']['name']} ({seed['config']['agent_type']}) → {runner.agent_id}")
        except Exception as e:
            print(f"  Failed to seed agent {seed['config']['name']}: {e}")
    print("4 managed agents started (1 supply + 3 demand)")

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
