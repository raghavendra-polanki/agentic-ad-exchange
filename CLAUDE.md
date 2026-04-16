# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Agentic Ad Exchange (AAX)** — MIT AI Studio class project (Spring 2026). An open exchange protocol where fully autonomous AI agents representing brands and content creators discover, negotiate, and close advertising deals in real time.

**Core thesis**: "Moltbook proved agents can socialize. AAX proves they can do business — with real compliance, real conflicts, and a full audit trail."

**Proof-of-concept domain**: College sports / NIL (Name, Image, Likeness). Pixology (Raghav's startup) provides real content creation APIs for the supply side.

## Development Workflow: Agent Teams

**All development on AAX uses Claude Code Agent Teams for parallel development.**

### How We Develop

1. **Human (Raghav)** defines the task and priorities
2. **Lead Agent** (main Claude Code session) breaks down work, creates plan, spawns teammates
3. **Teammate Agents** work in parallel on isolated git worktrees, each owning a specific module
4. **Lead Agent** integrates, runs tests, resolves conflicts
5. **Human** reviews, gives feedback, captures learnings in AGENTS.md

### Module Ownership (for Agent Teams)

| Agent Assignment | Owns | Key Files |
|---|---|---|
| **Protocol & API** | API endpoints, Pydantic schemas | `server/src/api/*`, `server/src/schemas/*` |
| **Deal Engine** | LangGraph state machines (deal-making + fulfillment) | `server/src/engine/*` |
| **Conflict Engine** | Conflict graph, pre-screen + final check | `server/src/conflict/*`, `data/seed/*` |
| **Agent SDK / Samples** | Sample autonomous agents (Pixology, Nike, etc.) | `agents/*` |
| **Dashboard** | React UI, SSE streaming | `dashboard/*`, `server/src/api/stream.py` |

### Rules for Teammates
- **Only modify files in your assigned module.** Coordinate with lead before touching shared files.
- **Schemas are the contract.** `server/src/schemas/` defines the protocol. If you need a schema change, tell the lead — don't modify schemas directly.
- **Read AGENTS.md** for cross-session learnings and gotchas.
- **Write tests** for your module. Run `cd server && uv run pytest` before marking a task complete.

## Build & Run Commands

```bash
# Server (Python/FastAPI)
cd server
uv sync                                    # Install dependencies
uv run uvicorn src.main:app --reload        # Run dev server (port 8080)
uv run pytest                               # Run tests
uv run ruff check src/                      # Lint
uv run ruff format src/                     # Format

# Dashboard (React/Vite)
cd dashboard
npm install                                 # Install dependencies
npm run dev                                 # Run dev server (port 5173)

# Sample Agents (run as separate processes)
cd agents/nike_demand
uv run python agent.py                      # Run Nike agent
```

## Architecture

AAX is **protocol-first** — the agent interface is the product. The exchange is neutral infrastructure; intelligence lives in the participants. Agents are opaque to the exchange — AAX only sees protocol messages, not agent internals.

### Platform Boundary
- **AAX owns**: Protocol, agent registry, deal lifecycle orchestration (LangGraph), conflict checking (neutral arbiter), content validation (neutral third party), guardrail enforcement, audit trail, market data
- **Agents own**: Signal/moment detection, content creation, evaluation logic, pricing/bidding strategy, budget allocation, internal brand compliance
- **Managed Agent Service**: Optional onramp for participants without their own agents. Speaks the same protocol — exchange can't tell the difference.

### Communication Protocol
- **Agent → AAX**: REST API (HTTPS) + Bearer token auth
- **AAX → Agent**: Webhooks (POST to agent's registered callback URL)
- **AAX → Dashboard**: SSE (Server-Sent Events)
- **Routing**: Hub-and-spoke — all messages route through AAX, agents never talk directly
- **API design**: Agent-oriented (Moltbook-style) — responses include `next_actions`, `valid_actions`, `constraints`

### Tech Stack
| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph (deal-making + fulfillment state machines) |
| LLM | Claude (primary) via Anthropic SDK, GPT-4o (fallback) via OpenAI SDK |
| LLM Tracing | LangSmith |
| API | FastAPI (Python) |
| Database | Firestore (agent profiles, conflict graph, audit logs, deal state) |
| Blob Storage | GCS (brand assets, generated content) |
| Real-Time | SSE via FastAPI StreamingResponse |
| Frontend | React + Vite + TypeScript |
| Auth | JWT (human) + API keys (agents) |
| Package Manager | uv (Python), npm (dashboard) |

### Core Components
1. **Schemas** (`server/src/schemas/`) — Pydantic models defining the AAX protocol. Source of truth for all message types.
2. **API Layer** (`server/src/api/`) — FastAPI routes. Agent-facing REST + dashboard SSE.
3. **Deal Engine** (`server/src/engine/`) — Two LangGraph state machines: Deal-Making and Fulfillment.
4. **Conflict Engine** (`server/src/conflict/`) — Two-pass conflict model (pre-screen at matching + final check after proposal). Graph traversal over Firestore data.
5. **Matching Engine** (`server/src/matching/`) — Standing queries, relevance pre-scoring, webhook notifications.
6. **Content Validator** (`server/src/validation/`) — Multimodal LLM review of content against brand guidelines.
7. **Audit Trail** (`server/src/audit/`) — Event capture, reasoning traces, immutable logging.

### Agent Types for Demo
- **Pixology Supply Agent** (`agents/pixology_supply/`) — Self-hosted, real Pixology API integration
- **Nike Demand Agent** (`agents/nike_demand/`) — LLM-powered, aggressive premium brand
- **Gatorade Demand Agent** (`agents/gatorade_demand/`) — Gets blocked by athlete NIL conflicts
- **Campus Pizza Demand Agent** (`agents/local_biz_demand/`) — Small budget, local, conservative

## Key Documents

- `docs/product-architecture.md` — **Definitive doc**: vision, requirements, architecture, protocol, agent journeys, UI flows, demo script, phased milestones
- `docs/vision.md` — Original vision with market context
- `docs/aax-technical-abstract.md` — Academic paper
- `AGENTS.md` — Cross-session learnings for Agent Teams
