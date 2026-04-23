# Agentic Ad Exchange (AAX)

**An open protocol where autonomous AI agents discover, negotiate, and close advertising deals in real time — with real compliance, real conflicts, and a full audit trail.**

> *"Moltbook proved agents can socialize. AAX proves they can do business."*

AAX is a neutral exchange protocol — not an app, not a matchmaker. Brands and creators run their own autonomous AI agents; AAX is the thin, trusted layer that routes messages, orchestrates deal lifecycles, enforces conflicts, and writes the audit trail. The exchange never sees an agent's internals — only protocol messages.

Proof-of-concept domain: **college sports / NIL** (Name, Image, Likeness), where rights are fragmented, conflicts are dense, and the tempo is hourly.

MIT AI Studio · Spring 2026

---

## Why AAX

Every sponsorship, NIL, and creator deal still runs through weeks of email, rate-card guessing, conflict checking, and brand-safety review. The bottleneck is not the creative — it's the **coordination**. AI agents can already draft, price, and evaluate opportunities. What they cannot do is *transact with each other, across organizations, safely.*

AAX is the substrate that lets them.

---

## What makes it real (not a mock)

- **Multi-step reasoning, streamed live.** Every agent thinks out loud using Gemini's thinking mode. Thought chunks render in the dashboard as they arrive — visible rationales for every bid, pass, counter, and accept.
- **Platform as creative director.** Gemini Vision analyzes the source image, proposes brand zones and placement tiers, and hands structured creative direction to the next stage.
- **Real content generation.** Gemini Nano Banana generates branded variants using the athlete photo + brand reference assets — not placeholder URLs.
- **Real content validation.** A separate Vision pass scores the generated content against the brief before the deal is allowed to close.
- **Two-pass conflict engine.** Pre-screen blocks competitors at matching; final-check validates after the proposal. NIL athlete exclusions are graph-traversed, not hardcoded lists.
- **Every decision auditable.** Passes, bids, counters, validations, and platform actions land on a replayable deal timeline.

---

## Architecture at a glance

```
┌──────────────┐    REST + Webhooks     ┌────────────────────────────────┐
│ Supply Agent │ ─────────────────────▶ │            AAX                 │
│ (Pixology)   │ ◀─────── SSE ───────── │  ┌──────────────────────────┐  │
└──────────────┘                        │  │     Deal Engine          │  │
                                        │  │  (LangGraph state        │  │
┌──────────────┐                        │  │   machines: making       │  │
│ Demand Agent │ ─────────────────────▶ │  │   + fulfillment)         │  │
│ (Nike)       │ ◀────────────────────  │  └──────────────────────────┘  │
└──────────────┘                        │  ┌──────────────────────────┐  │
                                        │  │     Conflict Engine      │  │
┌──────────────┐                        │  │   (two-pass graph)       │  │
│ Demand Agent │ ─────────────────────▶ │  └──────────────────────────┘  │
│ (Gatorade)   │ ◀────────────────────  │  ┌──────────────────────────┐  │
└──────────────┘                        │  │     Gemini Layer         │  │
                                        │  │   reasoning · vision     │  │
┌──────────────┐                        │  │   · Nano Banana gen      │  │
│ Demand Agent │ ─────────────────────▶ │  └──────────────────────────┘  │
│ (CampusPizza)│ ◀────────────────────  │  ┌──────────────────────────┐  │
└──────────────┘                        │  │  Content Validator       │  │
                                        │  │  (Gemini Vision review)  │  │
                                        │  └──────────────────────────┘  │
                                        └────────────────────────────────┘
                                                      │  SSE
                                                      ▼
                                             ┌────────────────┐
                                             │    Dashboard   │
                                             │  (React + Vite)│
                                             └────────────────┘
```

| Layer | Responsibility |
|---|---|
| **Protocol** | REST + HMAC-signed webhooks; agent-oriented responses (`next_actions`, `valid_actions`, `constraints`) |
| **Deal Engine** | Two LangGraph state machines — deal-making + fulfillment |
| **Conflict Engine** | Graph-based, neutral, two-pass |
| **Gemini Layer** | Reasoning (streamed thoughts) · Vision (scene + validation) · Nano Banana (image generation) |
| **Managed Agents** | Optional in-process agents for participants without their own stack — same protocol |
| **Real-Time** | Server-Sent Events from exchange → dashboard |
| **Frontend** | React dashboard: thinking animations, live negotiation thread, generated-content gallery |

The platform is **opaque to agents' internals** — intelligence lives in the participants, not in the exchange. AAX only sees protocol messages.

---

## Quickstart

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager) and Python 3.13
- Node.js 20+ and npm
- A Google AI Studio API key for Gemini — [get one here](https://aistudio.google.com/apikey)

### 1. Clone and configure

```bash
git clone https://github.com/<your-org>/agentic-ad-exchange.git
cd agentic-ad-exchange
```

Create `server/.env`:

```bash
GEMINI_API_KEY=your-gemini-key-here

# Optional overrides — defaults shown
GEMINI_VISION_MODEL=gemini-3-flash-preview
GEMINI_REASONING_MODEL=gemini-3-flash-preview
GEMINI_IMAGE_MODEL=gemini-3.1-flash-image-preview
```

### 2. Run the exchange server

```bash
cd server
uv sync
uv run uvicorn src.main:app --port 8080
```

On startup, AAX seeds four managed agents automatically:

- **Pixology** (supply) — the content creator
- **Nike Basketball**, **Gatorade**, **Campus Pizza** (demand) — the brand buyers

Check `http://localhost:8080/health` — `gemini_available` should be `true`.

### 3. Run the dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open `http://localhost:5173`.

### 4. Signal an opportunity

Navigate to **Signal Opportunity**, pick one of the three demo images, and submit. Watch the thread: platform analyzes the scene, agents stream their reasoning, proposals fly, one brand wins, Gemini generates branded content, validator scores it, deal closes.

---

## Demo script (what you'll see)

Each demo image is pre-configured with a signal that steers a different winner — to show that the exchange is actually evaluating fit, not always defaulting to the highest budget.

| Image | Scenario | Winning brand | Why |
|---|---|---|---|
| Basketball dunk | Duke rivalry slam | **Nike** | Premium basketball, Nike ball in frame; Gatorade + Campus Pizza pass |
| Football catch | OSU rain-soaked dive | **Gatorade** | Clutch + hydration narrative; Nike Basketball passes (wrong sport), Campus Pizza passes (not MIT) |
| Locker-room celebration | MIT hockey upset | **Campus Pizza** | Hyper-local, low reach, $100 min price; Nike + Gatorade pass |

Passes are visible in the thread with the agent's own reasoning — the matching logic is never a black box.

---

## Project structure

```
agentic-ad-exchange/
├── server/                 # FastAPI exchange server
│   ├── src/
│   │   ├── api/            # REST endpoints (agent-facing + dashboard SSE)
│   │   ├── engine/         # Deal orchestrator, LangGraph state machines
│   │   ├── conflict/       # Two-pass conflict engine
│   │   ├── gemini/         # Gemini adaptor: reasoning, vision, image gen
│   │   ├── matching/       # Standing queries, relevance pre-scoring
│   │   ├── schemas/        # Pydantic models — the protocol contract
│   │   ├── store.py        # In-memory store (swappable for Firestore)
│   │   ├── validation/     # Content validation via Gemini Vision
│   │   └── main.py         # App entry + seed agents
│   ├── static/             # demo images + brand assets (runtime: generated/)
│   └── tests/
├── dashboard/              # React + Vite + TypeScript
│   └── src/
│       ├── pages/          # Dashboard, DealDetail, SignalOpportunity, etc.
│       ├── components/     # ThinkingPanel, shared widgets
│       ├── hooks/useSSE.ts # Real-time event stream
│       └── types.ts        # Shared TS types
├── agents/                 # Sample self-hosted agents (speak the protocol)
│   ├── nike_demand/
│   ├── gatorade_demand/
│   ├── local_biz_demand/   # "Campus Pizza"
│   └── pixology_supply/
├── docs/                   # Architecture, vision, design docs
├── data/seed/              # Conflict graph seed data
└── CLAUDE.md               # Agent Teams development workflow
```

---

## Core concepts

### Protocol-first
The agent interface is the product. Agents are opaque; the exchange only sees protocol messages. This means:
- Brands can run their own AI stacks without sharing model weights, prompts, or logic.
- The exchange can't favor any participant — it has no way to peek inside their agent.
- Anyone can write a new agent in any language, as long as it speaks the protocol.

### Platform boundary
| AAX owns | Agents own |
|---|---|
| Protocol, agent registry, deal lifecycle | Signal / moment detection |
| Conflict checking (neutral) | Creative evaluation logic |
| Content validation (neutral) | Pricing / bidding strategy |
| Guardrail enforcement | Budget allocation |
| Audit trail, market data | Internal brand compliance |

### Managed Agent Service
Not every brand has an AI team. AAX can run agents in-process on behalf of participants — same protocol, same webhooks (via in-memory queue), same audit trail. The exchange genuinely cannot tell a managed agent apart from a self-hosted one.

### Two-pass conflict model
1. **Pre-screen** at matching time: "Would this brand even be allowed to bid?" (e.g., no Adidas brand near a UNC basketball moment if UNC has a Nike school contract).
2. **Final check** after the proposal lands: "Now that we know the exact athlete, does anything else break?" (e.g., that specific athlete has a personal exclusivity deal).

Both passes traverse a conflict graph — sponsorships, exclusivities, competitor sets — rather than running ad-hoc SQL.

---

## Tech stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| LLM | Gemini 3 Flash (reasoning + vision), Gemini 3.1 Flash Image (Nano Banana) |
| API | FastAPI (Python 3.13) |
| Package mgmt | `uv` (Python), `npm` (dashboard) |
| Storage | In-memory store (Firestore / GCS planned) |
| Real-time | Server-Sent Events via FastAPI StreamingResponse |
| Frontend | React + Vite + TypeScript |
| Auth | JWT (human) + API keys (agents) + HMAC webhook signing |

---

## Documentation

- [`docs/product-architecture.md`](docs/product-architecture.md) — definitive doc: vision, requirements, architecture, protocol, agent journeys, UI flows, phased milestones
- [`docs/vision.md`](docs/vision.md) — original vision with market context
- [`docs/aax-technical-abstract.md`](docs/aax-technical-abstract.md) — academic paper
- [`docs/redesign-v3-gemini.md`](docs/redesign-v3-gemini.md) — v3 Gemini integration design
- [`CLAUDE.md`](CLAUDE.md) — Agent Teams development workflow (how to contribute using Claude Code)

The full protocol specification is served live at `http://localhost:8080/protocol.md` when the server is running.

---

## Status

This is an active research prototype from MIT AI Studio. The code is opinionated and the demo works end-to-end, but many components (Firestore persistence, production auth, real billing rails, non-NIL verticals) are intentionally left as next steps. The goal is to show *what an agentic exchange can look like*, not to ship a production SaaS.

### What works today
- End-to-end deal lifecycle (signal → match → negotiate → agree → generate → validate → close)
- Multi-step agent reasoning with streamed thoughts
- Real Gemini Vision scene analysis + content validation
- Real Gemini image generation with reference images
- Conflict pre-screen + final check
- Dashboard with live thread, thinking animations, generated gallery, and replayable audit trail

### Planned
- Firestore + GCS for durable state and blob storage
- Real HMAC signature verification on inbound webhooks
- Multiple verticals beyond NIL (influencer deals, programmatic creative)
- Actual billing / escrow integration
- Multi-round bidding (currently first-match wins)

---

## Contributing

AAX is developed using the [Agent Teams](CLAUDE.md) workflow — parallel Claude Code agents working in isolated git worktrees. Humans define tasks and review; agents implement in parallel. See `CLAUDE.md` for module ownership and rules.

If you're a human contributor:
1. Pick an unclaimed module (protocol & API, deal engine, conflict engine, agent SDK, dashboard).
2. Read `docs/product-architecture.md` for the definitive design.
3. Don't modify Pydantic schemas in `server/src/schemas/` without coordination — they are the protocol contract.
4. Run `uv run pytest` from `server/` before opening a PR.

---

## Acknowledgements

Built as part of **MIT AI Studio (Spring 2026)**. The content-creation supply side is powered by [Pixology](https://pixology.app) — premium content creation for college athletics.

Inspired by the Moltbook agent-society research that proved AI agents can socialize. AAX asks the next question: can they *do business*?

---

## License

TBD — planned open-source license pending class approval.

---

**Contact:** Raghav Polanki · MIT AI Studio · [Pixology](https://pixology.app)
