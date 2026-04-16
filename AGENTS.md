# AGENTS.md

Cross-session learnings for Agent Teams working on AAX. Updated after each session.

## Module Ownership (Agent Teams)

When using Agent Teams for parallel development, each teammate owns a specific module.
**Do not modify files outside your assigned module without coordinating with the lead.**

| Agent Assignment | Owns (files) | Interface Dependencies |
|---|---|---|
| Protocol & API | `server/src/api/*`, `server/src/schemas/*` | Defines schemas all others consume |
| Deal Engine | `server/src/engine/*` | Consumes schemas, calls conflict checker |
| Conflict Engine | `server/src/conflict/*`, `data/seed/*` | Consumes schemas, called by deal engine |
| Agent SDK / Samples | `agents/*` | Consumes schemas, calls API endpoints |
| Dashboard | `dashboard/*`, `server/src/api/stream.py` | Consumes SSE stream + REST API |

## Development Conventions

### Python (server/)
- Python 3.12+, use type hints everywhere
- Pydantic v2 models for all schemas (in `server/src/schemas/`)
- FastAPI for API routes
- `uv` for dependency management (`uv sync` to install)
- Run server: `cd server && uv run uvicorn src.main:app --reload`
- Run tests: `cd server && uv run pytest`
- Lint: `cd server && uv run ruff check src/`
- Format: `cd server && uv run ruff format src/`

### React (dashboard/)
- Vite + React + TypeScript
- Run dev server: `cd dashboard && npm run dev`

### Schemas are the contract
The `server/src/schemas/` directory defines the AAX protocol. These Pydantic models are the source of truth for:
- API request/response shapes
- Deal state machine context
- Agent profile structure
- All message types between agents and exchange

**If you change a schema, coordinate with all agents that depend on it.**

## Gotchas & Learnings

(This section accumulates over time — add entries after each session)
