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
    yield
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
