import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import agents, content, deals, opportunities, proposals, stream
from src.conflict import init_conflict_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load conflict graph seed data
    init_conflict_engine()
    print("AAX Exchange started — conflict engine loaded")

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
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(opportunities.router, prefix="/api/v1/opportunities", tags=["opportunities"])
app.include_router(proposals.router, prefix="/api/v1/proposals", tags=["proposals"])
app.include_router(deals.router, prefix="/api/v1/deals", tags=["deals"])
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])

# Dashboard-facing API (SSE)
app.include_router(stream.router, prefix="/api/v1/stream", tags=["stream"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "aax-exchange"}
