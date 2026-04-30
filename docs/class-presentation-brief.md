# AAX — Class Presentation Brief

A spec document to feed to Claude (or any LLM) for generating a 6–10 slide deck about the Agentic Ad Exchange (AAX) project.

**Audience:** MIT AI Studio class (Spring 2026) — peers, faculty, possibly industry guests.
**Length target:** 10–15 minute talk. 6–10 slides.
**Talk arc:** problem → solution → what makes it real → live demo → what we learned → what's next.

> **Use this doc as input** when prompting Claude: *"Using the brief at @docs/class-presentation-brief.md, generate a 9-slide deck. Each slide should have a title, 3-5 bullet points, and a visual cue. Match the tone — confident, specific, no jargon for jargon's sake."*

---

## 1. Pitch in two sentences

Agentic Ad Exchange (AAX) is an open protocol where fully autonomous AI agents — representing brands and content creators — discover, negotiate, and close advertising deals in real time. Unlike a generic agent demo, AAX is built around the things that make a real exchange trustworthy: conflict checking, content validation, human approval thresholds, and a full audit trail of every AI decision.

**One-line hook (use this verbatim):**
> *"Moltbook proved agents can socialize. AAX proves they can do business — with real compliance, real conflicts, and a full audit trail."*

---

## 2. The problem we're solving

College NIL (Name, Image, Likeness) and creator marketing are exploding markets, but every deal still takes weeks: email threads, rate-card guessing, conflict checking, brand-safety review, legal sign-off.

**The bottleneck isn't the creative work — it's the coordination.**

AI agents can already do the hard parts (draft, price, evaluate). What they can't yet do is **transact with each other across organizations, safely, with rules.**

AAX is the substrate that lets them.

---

## 3. What AAX is (the neutral protocol thesis)

- **Not an app.** Not a marketplace UI. Not a matchmaker.
- **It's a protocol** — REST + webhooks + SSE — plus the neutral infrastructure that enforces it (deal engine, conflict graph, content validator, audit log).
- **Brands and creators run their own agents.** Anyone can build one in any language. The exchange never sees inside.
- **The exchange's only job** is to route messages, orchestrate deal lifecycles, check conflicts, validate content, and write the audit trail.

This is the philosophical core of AAX. Worth a slide of its own.

---

## 4. Architecture at a glance

```
┌──────────────┐    REST + Webhooks     ┌───────────────────────────┐
│ Supply Agent │ ─────────────────────▶ │            AAX            │
│ (Pixology)   │ ◀──── SSE stream ───── │  ┌─────────────────────┐  │
└──────────────┘                        │  │   Deal Engine       │  │
                                        │  │   (LangGraph)       │  │
┌──────────────┐                        │  └─────────────────────┘  │
│ Demand Agent │ ─────────────────────▶ │  ┌─────────────────────┐  │
│ (Nike)       │ ◀────────────────────  │  │  Conflict Engine    │  │
└──────────────┘                        │  │  (two-pass graph)   │  │
                                        │  └─────────────────────┘  │
┌──────────────┐                        │  ┌─────────────────────┐  │
│ Demand Agent │ ─────────────────────▶ │  │  Gemini Layer       │  │
│ (Gatorade)   │ ◀────────────────────  │  │  reasoning · vision │  │
└──────────────┘                        │  │  · Nano Banana gen  │  │
                                        │  └─────────────────────┘  │
┌──────────────┐                        │  ┌─────────────────────┐  │
│ Demand Agent │ ─────────────────────▶ │  │  Content Validator  │  │
│ (CampusPizza)│ ◀────────────────────  │  │  (Gemini Vision)    │  │
└──────────────┘                        │  └─────────────────────┘  │
                                        └───────────────────────────┘
                                                    │
                                                    ▼
                                         ┌──────────────────┐
                                         │   Dashboard      │
                                         │ (React + Vite)   │
                                         └──────────────────┘
```

**Slide-friendly summary table:**

| Layer | What it does |
|---|---|
| Protocol | REST + HMAC webhooks + SSE, agent-oriented responses |
| Deal Engine | Two LangGraph state machines: deal-making + fulfillment |
| Conflict Engine | Graph-based, neutral, two-pass (pre-screen + final check) |
| Gemini Layer | Reasoning (streamed thoughts), Vision (scene + validation), Nano Banana (image gen) |
| Content Validator | Separate Vision pass scores generated content before deal closes |
| Real-time | Server-Sent Events from exchange to dashboard |
| Frontend | React dashboard: thinking animations, live thread, generated content gallery |

---

## 5. What makes it real (not a mock) — the credibility punch

This is the slide that earns trust. **Every bullet is provable on screen during the live demo.**

- **Multi-step reasoning, streamed live.** Every agent thinks out loud using Gemini's thinking mode. Thought chunks render in the dashboard as they arrive — visible rationales for every bid, pass, counter, and accept.
- **Platform as creative director.** Gemini Vision analyzes the source image, proposes brand zones (overlay, scene enhancement, immersive 3D) and placement tiers, and hands structured creative direction to the next stage.
- **Real content generation.** Gemini Nano Banana generates branded variants using the athlete photo + brand reference assets — *not placeholder URLs.*
- **Real content validation.** A separate Gemini Vision pass scores generated content against the brief before the deal is allowed to close.
- **Two-pass conflict engine.** Pre-screen blocks competitors at matching; final-check validates after the proposal. NIL athlete exclusions are graph-traversed, not hardcoded.
- **Every decision auditable.** Passes, bids, counters, validations, and platform actions land on a replayable deal timeline.

---

## 6. The live demo (centerpiece)

This is the moment that lands the project. **Same dashboard, same code, three signals — three different winners.** Deterministic-by-design so it always works on stage.

### Signal 1 — Basketball dunk (Duke vs UNC)
- Premium basketball moment, Nike ball visible in frame
- Min price $1,500, reach 450k
- **Winner: Nike** ($2-4k bid)
- **Losers (visible in thread with reasoning):**
  - Gatorade passes — *"basketball-only dunk, that's Nike's lane, no performance narrative"*
  - Campus Pizza passes — *"non-MIT, way over our $200 budget"*

### Signal 2 — Football catch (Ohio State rain dive)
- Sweat-soaked, clutch, 4th down, rain-soaked turf
- Min price $1,200, reach 850k
- **Winner: Gatorade** ($2-3k bid)
- **Losers visible:**
  - Nike Basketball passes — *"hard filter: non-basketball is handled by other Nike divisions"*
  - Campus Pizza passes — *"not MIT, over budget"*

### Signal 3 — MIT hockey upset celebration
- Locker-room joy, dorm-life energy, Mass Ave celebration
- Min price $100, reach 12k (small but engaged)
- **Winner: Campus Pizza** (~$150-200 bid)
- **Losers visible:**
  - Nike — *"non-basketball, low reach"*
  - Gatorade — *"locker-room celebration, no performance narrative"*

**The teaching moment:** the matching logic is *not a black box.* Every passed bid shows *why* — a future regulator, brand manager, or athlete can read the agent's actual reasoning, not just the final outcome.

After the third deal closes, walk through the generated content: branded image with Campus Pizza logo integrated naturally into the scene, then the Gemini Vision validator scoring it against the brief.

---

## 7. Why this is interesting research (not just a project)

Save this for a thoughtful slide near the end.

- **NIL provenance is a real, unsolved problem.** Who can authorize a creator's content for monetization? AAX's two-pass conflict + delegation model is one answer.
- **Multi-agent emergent behavior on a common protocol.** AAX shows that diverse agents (different LLMs, different strategies, different objectives) can transact stably without a central orchestrator deciding outcomes.
- **The audit trail is the product.** Every AI decision — including reasoning, evaluations, conflict checks, and validations — is captured as a replayable timeline. Regulators, athletes, and brands can audit *why* a deal closed.
- **Neutral substrate beats vertical SaaS.** The same protocol could route programmatic creative buys, influencer deals, or any market where two autonomous agents need to close under real rules.

---

## 8. What we learned along the way (good for a "lessons" slide)

Pick the 3 most relevant for the audience:

- **Reasoning visibility is the trust unlock.** When agents stream their thoughts, users instantly trust the system more than any "AI did the right thing" claim.
- **Hard rules + soft voice** is the right config split. Budget caps and exclusions belong in code (typed, enforced); brand voice belongs in markdown (expressive, LLM-injected).
- **The "creative director" pattern works.** Letting the platform analyze content first, then handing structured guidance to brand agents, produces better creative outcomes than letting each brand re-analyze independently.
- **Pass decisions are first-class.** "X passed because Y" is as important as "X bid $5k." Showing both makes the system explainable.
- **Async > sync everywhere.** Wrapping every Gemini call in `asyncio.to_thread` was the difference between a responsive demo and a hung server.

---

## 9. What's next (roadmap slide)

Build credibility by showing you know what's *not* yet done.

**Near-term (in flight):**
- Editable brand personas via dashboard (markdown files with frontmatter)
- NIL delegation grants (athletes authorize who can sell their moments, scoped + revocable)
- Auto-approve thresholds + human-in-the-loop approval for high-value deals

**Next milestone:**
- **OpenCLAW integration** — humans interact with their AAX agents from WhatsApp / Telegram / Signal via the popular open-source personal-agent runtime. Approval prompts, deal queries, override commands.

**Stretch:**
- Concurrent signal stress test (20 overlapping signals through the conflict engine)
- Cryptographic delegation signing
- Multiple verticals (influencer, programmatic creative)
- Third-party SDK + "build your first AAX agent in 10 minutes" tutorial

---

## 10. Try it

- **Live demo:** https://aax.pixology.ai
- **GitHub:** https://github.com/raghavendra-polanki/agentic-ad-exchange
- **Tech stack:** Python · FastAPI · LangGraph · Gemini 3 Flash + Nano Banana · React + Vite · SSE

---

## Suggested slide-by-slide structure

> Pick 6, 8, or 10 of these depending on time. **Bold ones are non-negotiable.**

| # | Slide | Purpose | Key visual |
|---|---|---|---|
| 1 | **Title + Moltbook hook** | Set the frame in 5 seconds | Black slide, big "AAX", quote in serif italic |
| 2 | **The problem** | Make them care | "Weeks of email" → "Hours of agent-to-agent" comparison |
| 3 | **What AAX is** | Define the thesis (neutral protocol) | The architecture diagram |
| 4 | What makes it real | Establish technical depth | 6 bullets, each with a tiny icon |
| 5 | **Live demo intro + Signal 1** | Hand things over to the running app | Screenshot of dashboard at the moment Nike wins |
| 6 | Signal 2 + 3 (or one combined "three winners") | Show the differentiation | Side-by-side of three outcomes |
| 7 | Generated content + validation | Show that "real" means real | Screenshot of branded image + validator score |
| 8 | Why this is research-grade | Close the academic loop | NIL provenance + audit trail framing |
| 9 | What's next | Roadmap, with OpenCLAW callout | Timeline graphic |
| 10 | Try it / Q&A | Live URL + repo + thank-yous | QR code to https://aax.pixology.ai |

---

## Tone & style notes for whoever generates the deck

- **Be specific.** Numbers, names, real dollar amounts. Don't say "various brands" — say "Nike, Gatorade, Campus Pizza."
- **Quote the agents.** The deck should include actual reasoning text from agents (e.g., a real "passed because basketball-only" snippet from a demo run).
- **No jargon for jargon's sake.** "Multi-agent system" is fine; "agentic AI workforce orchestration framework" is not.
- **Two visual themes:**
  - Dark background, vivid orange (#F97316) primary, electric purple (#8B5CF6) accent — matches the dashboard
  - Clean editorial typography, lots of whitespace, no clipart
- **One memorable line per slide.** Land one quotable phrase, not five.
- **End on a question, not a thank-you.** Suggested closer: *"If agents can transact, what economy emerges?"*

---

## Things to bring to class on demo day

- Laptop with the dashboard loaded (`https://aax.pixology.ai`)
- Backup: a video screen-record of a successful end-to-end run (in case Wi-Fi is bad or Gemini API has a hiccup)
- Phone / second screen for the OpenCLAW preview if it's ready
- A printed handout or QR code for the GitHub repo

---

## Acknowledgements (for the credits slide)

- **Pixology** — supply-side content creation infrastructure (Raghav's startup)
- **MIT AI Studio** — Spring 2026 cohort
- **Google DeepMind** — Gemini 3 Flash and Nano Banana
- **OpenCLAW** community — design influence on the agent runtime split
- **Anthropic Claude Code + Agent Teams** — entire codebase developed via parallel AI agents
