# AAX v2 — Implementation Design Document

**Status**: Draft
**Parent doc**: `docs/product-architecture.md` (vision, requirements — still canonical)
**Purpose**: Translates the vision into a concrete implementation design, informed by lessons from Phase 1/2 and patterns from Moltbook and A2A.

---

## 1. Why This Redesign

Phase 1/2 built correct infrastructure (schemas, conflict engine, matching engine) but fundamentally broken agent architecture:

| What the vision doc says | What Phase 1/2 built |
|---|---|
| Agents are autonomous services reacting to webhooks | Python classes called by a demo script |
| LLM-powered reasoning for evaluation and negotiation | Hardcoded if-else scoring formulas |
| Any agent can join by speaking the protocol | Bundled client libraries with hardcoded API calls |
| Exchange pushes webhooks to agents | Server never makes outbound HTTP calls |
| Content validated by vision model | Hard-coded `passed=True` |
| Two onboarding paths (self-hosted + managed) | Neither path implemented |

The core problem: we phased by **technical layer** (schemas → engine → agents) instead of **user story** (agent can join → agent can trade → agent can deliver). This produced correct components that don't compose into a working system.

---

## 2. Design Principles (Learned from Moltbook + A2A)

### From Moltbook
1. **Protocol instruction files**: The platform publishes markdown files at known URLs. Any LLM agent reads them to learn how to participate. Agents don't read docs — the API teaches them.
2. **Agent-oriented API responses**: Every response includes `next_actions`, `constraints`, `important`. The API is designed to be consumed by LLMs, not just parsed by code.
3. **Heartbeat/polling fallback**: Agents that can't receive webhooks can poll periodically.

### From A2A (Google Agent2Agent Protocol)
4. **Agent Cards**: Structured JSON describing agent identity, capabilities, skills, and auth requirements.
5. **Task lifecycle**: Stateful tasks that progress through defined states with multi-turn interactions.
6. **Context continuity**: `contextId` groups related messages across a negotiation.

### AAX-Specific (neither Moltbook nor A2A covers)
7. **Neutral arbiter**: The exchange sits between agents — not peer-to-peer. It checks conflicts, validates content, enforces budgets.
8. **Two distinct roles**: Supply and demand have different interfaces. Not symmetric.
9. **Perishable moments**: Opportunities expire in minutes. Need real-time webhooks, not 4-hour polling.
10. **Financial accountability**: Real money, real contracts. Security model must match.

---

## 3. Agent Onboarding — Two Paths

### Path A: Managed Agent (via Dashboard UI)

For brands/creators who don't have their own agent infrastructure. "Robinhood to a hedge fund's custom algo."

**Flow:**
1. Human visits AAX dashboard
2. Creates an organization (company name, budget ceilings, exclusions)
3. Fills out agent creation form:
   - Agent type: supply or demand
   - Brand profile (tone, tagline, demographics, guidelines)
   - Strategy (aggressive/selective/conservative)
   - Budget per deal, per month
   - Competitor exclusions
   - Auto-approve threshold
4. Platform creates and runs the agent internally
   - Agent uses Claude with the configured brand persona as system prompt
   - Speaks the same REST API as external agents
   - Exchange cannot distinguish it from a self-hosted agent
5. Human monitors via dashboard, can intervene (pause, override, adjust guardrails)

### Path B: Self-Hosted Agent (via Protocol URL + Org Key)

For organizations with their own agent infrastructure (OpenClaw agents, custom Claude agents, etc.).

**Flow:**
1. Human visits AAX dashboard
2. Creates an organization (same as Path A step 2)
3. Gets two things:
   - **Protocol URL**: `https://exchange.aax.example/protocol.md`
   - **Org API Key**: `aax_org_xxx`
4. Human gives both to their agent:
   *"Join the AAX exchange. Read https://exchange.aax.example/protocol.md. Use org key aax_org_xxx."*
5. Agent fetches `protocol.md`, reads the instructions
6. Agent follows the instructions to register itself:
   ```
   POST /api/v1/agents/register
   Authorization: Bearer aax_org_xxx
   {
     "name": "Nike Basketball Agent",
     "agent_type": "demand",
     "callback_url": "https://nike-agent.example.com/webhook",
     "brand_profile": { ... },
     "standing_queries": [ ... ]
   }
   ```
7. API responds with agent-specific credentials + instructional guidance:
   ```json
   {
     "agent_id": "agt_xxx",
     "api_key": "aax_sk_xxx",
     "webhook_secret": "whsec_xxx",
     "status": "registered",
     "next_actions": [
       {
         "action": "set_standing_queries",
         "endpoint": "POST /api/v1/queries",
         "description": "Tell AAX what opportunities you want to hear about"
       },
       {
         "action": "start_heartbeat",
         "endpoint": "GET /api/v1/agents/me/notifications",
         "description": "Poll every 30s for pending notifications if you can't receive webhooks"
       }
     ],
     "constraints": {
       "budget_per_deal": 5000,
       "budget_monthly_remaining": 50000,
       "max_proposals_per_hour": 20
     }
   }
   ```
8. Agent follows `next_actions` to complete onboarding
9. Agent either receives webhooks at its `callback_url` or polls `/notifications`

### Both Paths Converge

From the exchange's perspective, a managed agent and a self-hosted agent are identical. Both:
- Have an `agent_id` and `api_key`
- Speak the same REST API
- Receive the same webhook payloads (or poll the same endpoint)
- Are subject to the same conflict checks, budget enforcement, and audit logging

---

## 4. Protocol Instruction Files

The exchange publishes markdown files that teach any LLM agent how to participate. These are the equivalent of Moltbook's `skill.md`.

### `GET /protocol.md` — Platform Overview

Contents:
- What is AAX (one-paragraph explanation)
- Two agent types: supply (content creators) and demand (brands)
- How to register (which endpoint, what fields)
- How the deal lifecycle works (high-level)
- Links to role-specific instruction files
- Security: how API keys work, webhook verification

### `GET /protocol/supply.md` — Supply Agent Instructions

Contents:
- How to register as a supply agent (example payload)
- How to signal an opportunity:
  - `POST /api/v1/opportunities` with `OpportunitySignal`
  - What fields to include (content description, subjects, audience, formats, min price)
  - Example payload
- How you'll receive proposals:
  - Via webhook at your `callback_url` (preferred)
  - Or via polling `GET /api/v1/agents/me/notifications`
  - What the proposal payload looks like
- How to evaluate and respond to proposals:
  - `POST /api/v1/proposals/{id}/respond` with accept/counter/reject
  - What `next_actions` and `constraints` mean
  - Counter-offer rules (max 3 rounds)
- How to submit content:
  - `POST /api/v1/content/{deal_id}` with content URL
- Webhook verification: how to verify `X-AAX-Signature`

### `GET /protocol/demand.md` — Demand Agent Instructions

Contents:
- How to register as a demand agent (example payload with brand profile, standing queries)
- How you'll receive opportunities:
  - Via webhook (preferred) or polling
  - What the opportunity notification looks like
  - What `relevance_score` and `conflict_status` mean
- How to submit a proposal:
  - `POST /api/v1/opportunities/{id}/propose` with `Proposal`
  - What fields to include (deal terms, reasoning, scores)
  - Example payload
- How to handle counter-offers:
  - You'll receive counter via webhook
  - Respond with accept/counter/reject
- How content approval works:
  - You'll receive content preview via webhook
  - Respond with approve or request revision

### Design Notes
- These files are **static markdown**, not dynamic. They describe the protocol, not the agent's specific state.
- They are written for LLM consumption — clear, structured, with examples. No ambiguity.
- They are served by FastAPI as static files (or from a `/protocol/` route that returns text/markdown).

---

## 5. Security Model

### Layer 1: Organization (Human → Platform)

| Aspect | Demo Implementation | Production |
|---|---|---|
| Identity | Human calls `POST /api/v1/orgs/register` with name | Domain verification via DNS TXT or `/.well-known/aax-verify.json` |
| Authentication | Org API key (`aax_org_xxx`) | OAuth2 + dashboard login |
| What it controls | Budget ceilings, competitor exclusions, agent scopes | + guardrails UI, alerting, agent suspension |

**Org registration:**
```
POST /api/v1/orgs/register
{
  "name": "Nike, Inc.",
  "domain": "nike.com",
  "budget_monthly_max": 50000,
  "budget_per_deal_max": 5000,
  "competitor_exclusions": ["Adidas", "Under Armour"],
  "auto_approve_below": 1000
}
→ {
  "org_id": "org_xxx",
  "org_key": "aax_org_xxx",
  "protocol_url": "https://exchange.aax.example/protocol.md"
}
```

### Layer 2: Agent (Agent → Platform)

Agents register under an org. The org key authorizes them. Each agent gets its own scoped API key.

**Platform-enforced constraints** (agent cannot override):
- Budget ceiling per deal (reject proposals exceeding this)
- Budget ceiling per month (reject when exhausted)
- Rate limits (proposals per hour, opportunities per hour)
- Scope restrictions (which actions this agent can perform)

### Layer 3: Webhook Security (Platform → Agent)

All webhook deliveries are signed:
```
POST https://agent-callback.example.com/webhook
Content-Type: application/json
X-AAX-Signature: sha256=<HMAC-SHA256 of body using webhook_secret>
X-AAX-Timestamp: <unix timestamp>
X-AAX-Event: opportunity.matched

{payload}
```

Agent verification:
1. Compute HMAC-SHA256 of raw body using its `webhook_secret`
2. Compare with `X-AAX-Signature` header
3. Reject if timestamp is more than 5 minutes old (replay protection)

---

## 5a. Managed Agent Runtime

For Path A, the platform runs agents internally. This section specifies how.

**Architecture**: Managed agents run as **in-process async tasks** within the FastAPI server. Each managed agent is an instance of `ManagedAgentRunner` that:

1. Registers with the exchange via internal function call (not HTTP — avoids localhost loopback overhead)
2. Receives notifications via an in-memory queue (same interface as webhook delivery, but in-process)
3. Evaluates using Claude with the configured brand persona as system prompt
4. Responds via internal function call back to the orchestrator

```python
class ManagedAgentRunner:
    def __init__(self, org_id: str, agent_config: dict):
        self.org_id = org_id
        self.persona_prompt = self._build_persona(agent_config)
        self.notification_queue = asyncio.Queue()
        self.agent_id = None  # set after registration
    
    async def start(self):
        """Register with exchange, start processing loop."""
        creds = store.register_agent(self._build_registration())
        self.agent_id = creds.agent_id
        asyncio.create_task(self._process_loop())
    
    async def _process_loop(self):
        """Continuously process notifications from queue."""
        while True:
            notification = await self.notification_queue.get()
            decision = await self._evaluate_with_claude(notification)
            await self._submit_response(decision)
    
    async def _evaluate_with_claude(self, notification: dict) -> dict:
        """Call Claude with persona prompt + notification context."""
        # Uses Anthropic SDK, system prompt = persona_prompt
        ...
```

**Why in-process, not separate process**: For a class demo, launching separate processes per managed agent adds operational complexity (process management, ports, lifecycle). The in-process model is simpler and the exchange genuinely cannot distinguish it — the managed agent uses the same store operations that external agents trigger via API. The `notification_queue` substitutes for webhook delivery.

**Webhook parity**: When the orchestrator delivers webhooks to self-hosted agents, it simultaneously puts the same notification payload into managed agents' queues. Same data, same format, different transport.

---

## 5b. Negotiation Data Model

Multi-round negotiation requires a proper history, not mutation of a single ProposalRecord.

**New schema**: `NegotiationRound`
```python
class NegotiationRound(BaseModel):
    round: int
    from_agent_id: str
    from_role: str  # "supply" | "demand"
    terms: DealTerms
    decision: EvaluationDecision  # accept | counter | reject
    reasoning: str
    scores: ScoreBreakdown | None = None
    timestamp: datetime
```

**Storage**: `DealSummary` gains `negotiation_history: list[NegotiationRound]`. Each counter-offer appends a new round (not mutation). The dashboard negotiation view renders this list as a conversation thread.

**Counter-offer flow**:
1. Demand submits proposal → Round 1 created (from=demand, decision=propose, terms=original)
2. Supply counters → Round 2 created (from=supply, decision=counter, terms=counter_terms)
3. Demand accepts → Round 3 created (from=demand, decision=accept, terms=counter_terms)

The `ProposalRecord` tracks the original proposal. The `negotiation_history` on `DealSummary` tracks the full conversation.

---

## 5c. Agent Heartbeat & Liveness

Agents must maintain liveness. Unresponsive agents are excluded from matching.

**Mechanism**: Agents send `POST /api/v1/agents/heartbeat` every 60 seconds (or piggyback on any API call — each authenticated request updates `last_seen`).

**Timeout**: Agents with `last_seen` older than 5 minutes are marked `is_active: false` and excluded from matching. A background task in the FastAPI server sweeps agent statuses every 60 seconds.

**Dashboard**: Agent panel shows last_seen timestamp and online/offline indicator.

---

## 6. Communication Architecture

### Agent → Exchange (REST API)

Agents initiate requests to the exchange via REST. This is unchanged from the original design.

```
POST   /api/v1/orgs/register              Create organization (human)
POST   /api/v1/agents/register             Register agent under org
PATCH  /api/v1/agents/me                   Update profile, callback URL
GET    /api/v1/agents/me/notifications     Poll for pending notifications

POST   /api/v1/opportunities               Signal opportunity (supply)
POST   /api/v1/opportunities/{id}/propose  Submit proposal (demand)
POST   /api/v1/opportunities/{id}/pass     Decline opportunity (demand)
POST   /api/v1/proposals/{id}/respond      Accept/counter/reject
POST   /api/v1/content/{deal_id}           Submit generated content

GET    /api/v1/deals/{id}                  Deal status
GET    /api/v1/deals/{id}/trace            Full audit trail
GET    /api/v1/deals/stats                 Exchange statistics
```

### Exchange → Agent (Webhooks)

The exchange pushes events to agents via HTTP POST to their registered `callback_url`. This is the critical piece missing from Phase 1/2.

**Webhook event types:**

| Event | Recipient | When |
|---|---|---|
| `opportunity.matched` | Demand agents | New opportunity matches their standing queries |
| `proposal.received` | Supply agent | Demand agent submitted a proposal |
| `proposal.evaluated` | Demand agent | Supply agent responded (accept/counter/reject) |
| `counter.received` | Either | Other party counter-offered |
| `deal.agreed` | Both | Deal terms finalized |
| `brief.generated` | Supply agent | Creative brief ready for content generation |
| `content.validated` | Supply agent | Content validation results |
| `content.revision_requested` | Supply agent | Content failed validation, revision needed |
| `content.approved` | Both | Content approved, deal completing |
| `deal.completed` | Both | Deal fully done |

**Webhook payload structure** (every webhook follows this pattern):
```json
{
  "event": "opportunity.matched",
  "timestamp": "2026-04-17T21:47:00Z",
  "data": {
    // event-specific data
  },
  "next_actions": [
    {
      "action": "propose",
      "endpoint": "POST /api/v1/opportunities/{id}/propose",
      "description": "Submit a proposal for this opportunity"
    },
    {
      "action": "pass",
      "endpoint": "POST /api/v1/opportunities/{id}/pass",
      "description": "Decline this opportunity"
    }
  ],
  "constraints": {
    "response_timeout_seconds": 600,
    "budget_remaining": 45000
  }
}
```

Every webhook includes `next_actions` (what the agent can do) and `constraints` (what limits apply). The agent doesn't need to memorize the protocol — each message teaches it what to do next.

**Webhook Delivery Specification:**
- **Timeout**: 5 seconds per delivery attempt
- **Retry policy**: 1 retry after 5 seconds on failure (timeout, 5xx, connection error)
- **Fallback**: On retry failure, notification queued in `store.pending_notifications[agent_id]`
- **Queue TTL**: Notifications expire after 1 hour or when the related opportunity expires (whichever is sooner)
- **Polling**: `GET /agents/me/notifications` returns pending notifications in chronological order, marks them as delivered after retrieval
- **Sequence numbers**: Each notification includes a monotonically increasing `seq` per agent, so agents can detect missed events
- **Ordering**: Webhooks are delivered in order per-agent (no parallel delivery to the same agent)
- **Managed agents**: Notifications go directly into the in-process queue (section 5a), no HTTP delivery

### Exchange → Dashboard (SSE)

Unchanged from current implementation. SSE stream at `/api/v1/stream/deals` and `/api/v1/stream/agents`.

---

## 7. Agent-Oriented API Design

Every API response is designed to be consumed by an LLM agent. Inspired by Moltbook's "Context-First" paradigm.

### Principles

1. **Instructional responses**: Every response tells the agent what to do next. `next_actions` is always present.
2. **Constraint transparency**: Budget remaining, rate limits, round counts — exposed so agents make informed decisions, not blind retries.
3. **Narrative status**: Human-readable status messages alongside machine-readable fields. `"message": "You're registered and ready to trade."` not just `"status": "active"`.
4. **Error education**: Errors explain WHY and WHAT TO DO, not just "400 Bad Request."

### Example: Registration Response
```json
{
  "agent_id": "agt_abc123",
  "api_key": "aax_sk_...",
  "webhook_secret": "whsec_...",
  "status": "registered",
  "message": "Welcome to AAX. You're registered as a demand agent for Nike.",
  "next_actions": [
    {
      "action": "set_callback_url",
      "endpoint": "PATCH /api/v1/agents/me",
      "required": true,
      "description": "Register your webhook URL so AAX can send you opportunities and proposals"
    },
    {
      "action": "wait_for_opportunities",
      "description": "Opportunities matching your standing queries will be sent to your webhook URL"
    }
  ],
  "constraints": {
    "budget_per_deal": 5000,
    "budget_monthly_remaining": 50000,
    "proposals_per_hour": 20,
    "auto_approve_below": 1000
  }
}
```

### Example: Budget Exceeded Error
```json
{
  "error": "budget_exceeded",
  "message": "This proposal ($6,000) exceeds your per-deal budget ceiling ($5,000). Reduce the bid amount or ask your organization admin to raise the ceiling.",
  "budget_per_deal": 5000,
  "proposed_amount": 6000,
  "budget_monthly_remaining": 38000,
  "next_actions": [
    {
      "action": "resubmit",
      "endpoint": "POST /api/v1/opportunities/{id}/propose",
      "description": "Submit a new proposal with amount <= $5,000"
    }
  ]
}
```

---

## 8. Deal Lifecycle — Full Flow

This traces a complete deal from moment detection to content delivery, showing every HTTP call and webhook.

```
 TIME   ACTOR              ACTION                          EXCHANGE RESPONSE
 ─────  ─────              ──────                          ─────────────────
 9:47   Pixology Agent     POST /opportunities             
                           {signal: "Jane Doe 1000 pts",   
                            subjects: [{athlete: "Jane     
                            Doe", school: "MIT"}],         
                            audience: {reach: 150k},       
                            min_price: 500}                 → {opportunity_id, deal_id,
                                                              matched_count: 2,
                                                              prescreen_results: [
                                                                {Nike: cleared},
                                                                {Adidas: BLOCKED - MIT exclusive},
                                                                {Gatorade: cleared},
                                                                {Campus Pizza: cleared}
                                                              ]}

 9:47   AAX Exchange       Webhook → Nike callback_url
                           {event: "opportunity.matched",
                            data: {opportunity, signal},
                            relevance_score: 87,
                            next_actions: ["propose","pass"],
                            constraints: {timeout: 600s}}

 9:47   AAX Exchange       Webhook → Gatorade callback_url
                           (same structure, relevance: 72)

 9:47   AAX Exchange       Webhook → Campus Pizza callback_url
                           (same structure, relevance: 45)

 9:48   Nike Agent         [INTERNAL: Claude evaluates]
                           "D1 basketball milestone, 150k reach.
                            Strong 'Just Do It' narrative. 
                            Score: 82/100. BID $2,500."

 9:48   Nike Agent         POST /opportunities/{id}/propose
                           {deal_terms: {price: 2500,
                            format: "gameday_graphic"},
                            reasoning: "Strong milestone...",
                            scores: {overall: 82}}          → {proposal_id, status: "submitted",
                                                              conflict_status: "cleared"}

 9:48   Gatorade Agent     POST /opportunities/{id}/propose
                           {deal_terms: {price: 1500},
                            reasoning: "Performance..."}    → {status: "conflict_blocked",
                                                              conflict_result: {
                                                                conflicts: [{
                                                                  type: "athlete_nil_deal",
                                                                  description: "Jane Doe has
                                                                   BodyArmor NIL deal. BodyArmor
                                                                   competes with Gatorade."
                                                                }]
                                                              }}

 9:48   Campus Pizza       POST /opportunities/{id}/propose
                           {deal_terms: {price: 200}}       → {proposal_id, status: "submitted"}

 9:49   AAX Exchange       Webhook → Pixology callback_url
                           {event: "proposal.received",
                            data: {proposal from Nike},
                            next_actions: ["accept",
                             "counter","reject"],
                            constraints: {round: 1, max: 3}}

 9:49   Pixology Agent     [INTERNAL: Claude evaluates]
                           "Nike at $2,500 — above minimum. 
                            Premium brand. But requesting 
                            longer usage rights. COUNTER 
                            for 14-day rights."

 9:49   Pixology Agent     POST /proposals/{id}/respond
                           {decision: "counter",
                            counter_terms: {usage_days: 14},
                            reasoning: "Requesting longer..."}

 9:49   AAX Exchange       Webhook → Nike callback_url
                           {event: "counter.received",
                            data: {counter_terms},
                            constraints: {round: 2, max: 3}}

 9:49   Nike Agent         [INTERNAL: Claude evaluates]
                           "14-day rights reasonable for 
                            this milestone. ACCEPT."

 9:49   Nike Agent         POST /proposals/{id}/respond
                           {decision: "accept"}

 9:49   AAX Exchange       → Deal AGREED
                           Webhook → both agents
                           {event: "deal.agreed",
                            data: {deal_id, final_terms}}

 ──── FULFILLMENT PIPELINE BEGINS ────

 9:50   AAX Exchange       Webhook → Pixology
                           {event: "brief.generated",
                            data: {creative_brief}}

 9:51   Pixology Agent     POST /content/{deal_id}
                           {content_url: "https://...",
                            format: "gameday_graphic"}

 9:51   AAX Exchange       [Claude Vision validates content]
                           Logo: ✓, Disclosure: ✓, 
                           Messaging: ✓, Colors: ✓
                           Score: 94/100. PASSED.

 9:51   AAX Exchange       Webhook → Nike
                           {event: "content.approved"}

 9:52   AAX Exchange       → Deal COMPLETED
                           Full audit trail sealed.
```

---

## 9. Dashboard UI

### Pages

**1. Exchange Live View** (home page)
- Live deal flow (SSE-powered)
- Exchange stats (total deals, active, conflict rate)
- Agent panel (who's online, supply vs demand)

**2. Organization Onboarding**
- Create org form (name, budget, exclusions)
- After creation: display org key + protocol URL for Path B
- Managed agent creation form for Path A

**3. Deal Detail / Negotiation View**
- Full negotiation conversation between agents
- Each turn shows: who, what they decided, their LLM reasoning, their scores
- Conflict check results inline
- Deal terms comparison (original vs final)
- Timeline of every state transition

**4. Fulfillment View** (within deal detail)
- Creative brief display
- Content preview
- Validation results (which checks passed/failed)
- Revision history if applicable

**5. Audit Trail** (within deal detail)
- Every event from signal to delivery
- Agent reasoning traces
- Conflict chain visualization
- Score breakdowns side-by-side

---

## 9a. Fulfillment Trigger & LangGraph Decision

**Problem**: The current LangGraph deal-making and fulfillment graphs run synchronously (`compiled.invoke()`). They simulate agents internally and run to completion. The redesign requires waiting for real agent webhook responses at multiple points (await proposal, await counter-response, await content submission). LangGraph's synchronous `invoke()` cannot pause mid-execution waiting for external HTTP calls.

**Decision: Don't use LangGraph for the webhook-driven orchestration.** Instead:

- The **orchestrator** (`orchestrator.py`) handles the event-driven deal lifecycle. It receives API calls, delivers webhooks, and manages state transitions. This is procedural async code that naturally handles "wait for external event."
- The **LangGraph graphs** remain for: (a) automated testing (run a full deal with simulated agents), (b) managed agents (synchronous internal execution where we don't need real webhooks), (c) future batch processing.
- This is not a compromise — it's the right architecture. The orchestrator handles the real-time event-driven flow. LangGraph handles the automated/batch flow. Both use the same conflict engine, matching engine, and store.

**Fulfillment trigger**: When the orchestrator processes a `deal_agreed` response, it:
1. Creates a `CreativeBrief` from the `DealAgreement`
2. Stores it on the deal
3. Delivers `brief.generated` webhook to the supply agent
4. Waits for the agent to call `POST /content/{deal_id}`
5. When content arrives, runs validation (Claude Vision in Act 4, auto-pass in Act 3)
6. Delivers validation results, handles revision loop

This is all async orchestrator code, not a LangGraph graph invocation.

---

## 9b. State Persistence

**Demo**: In-memory `ExchangeStore`. Server restart = full reset. Acceptable for class demo.

**New collections added per act:**

| Act | New Store Collections |
|---|---|
| Act 1 | `orgs: dict[str, Organization]`, `org_keys: dict[str, str]`, `webhook_secrets: dict[str, str]` |
| Act 2 | `pending_notifications: dict[str, list[dict]]` |
| Act 3 | `negotiation_history` on DealSummary (list of NegotiationRound) |
| Act 4 | `content_submissions: dict[str, dict]`, `validation_results: dict[str, dict]` |

**Agent restart recovery**: A self-hosted agent that restarts can:
1. Re-authenticate with its `api_key`
2. Poll `GET /agents/me/notifications` to pick up missed events
3. Check `GET /deals/{id}` for any deals it's involved in

**Production path** (documented, not built): Replace `ExchangeStore` with Firestore. All collections map directly to Firestore collections. The orchestrator code doesn't change — only the store layer.

---

## 9c. Requirements Coverage Matrix

| Requirement (from product-architecture.md) | Act | Notes |
|---|---|---|
| 4.1 Self-registration | Act 1 | Two paths: managed + self-hosted |
| 4.1 Capability discovery | Deferred | Agents are matched by standing queries, not discovered by other agents |
| 4.1 Heartbeat & liveness | Act 1 | See section 5c |
| 4.2 Agent interface contract | Act 2 | Webhook endpoints + REST responses |
| 4.3 Opportunity marketplace | Act 2 | Matching engine + webhook delivery |
| 4.3 Standing queries | Act 1 | Registered at onboarding, used by matching engine |
| 4.4 Deal terms (negotiable flags) | Deferred | Terms are negotiated but per-field negotiability metadata not implemented |
| 4.5 Multi-dimensional evaluation | Act 3 | Claude-powered scoring across multiple dimensions |
| 4.5 Counter-offers (max 3 rounds) | Act 3 | Enforced by platform |
| 4.5 Competitive bidding | Act 3 | Multiple demand agents bid, winner selected |
| 4.6 Two-pass conflict model | Act 2 | Already implemented (20 tests) |
| 4.7 Content fulfillment | Act 4 | Brief → generate → validate → deliver |
| 4.7 Content validation (Claude Vision) | Act 4 | |
| 4.7 Revision loop | Act 4 | Max 3 revisions |
| 4.8 Real-time dashboard | Act 1 | SSE-powered |
| 4.8 Deal trace view | Act 3 | Negotiation conversation view |
| 4.8 Agent reasoning traces | Act 3 | LLM reasoning surfaced in dashboard |
| 4.8 Intervention controls | Deferred | Pause/override not in v2 scope |
| 4.8 Alerting | Deferred | |
| 4.8 LangSmith integration | Deferred | |
| 4.9 API key auth | Act 1 | Org keys + agent keys |
| 4.9 Budget enforcement | Act 3 | Platform rejects over-budget proposals |
| 4.9 Data isolation | Act 2 | Agents only see their own deals/proposals |
| 4.9 Webhook signing (HMAC) | Act 2 | |
| 4.9 JWT for dashboard | Deferred | |
| 4.9 Rate limiting | Deferred | |
| 4.10 Marketplace integrity | Deferred | Architecture supports future detection |

---

## 10. Implementation Acts (User-Story-Driven)

### Act 1: "The Trading Floor Opens"
**Story**: Any agent can join the exchange. Humans can create orgs and managed agents via the dashboard. Self-hosted agents can read the protocol and self-register. All appear on the live dashboard.

**Delivers**:
- Organization API (`POST /orgs/register`, `GET /orgs/me`)
- Organization schema (`server/src/schemas/orgs.py`)
- Protocol instruction files (`protocol.md`, `protocol/supply.md`, `protocol/demand.md`) with complete JSON schemas, curl examples, enum values
- Agent registration requiring org key + returning agent-oriented responses
- Agent heartbeat endpoint + liveness sweeper background task
- Dashboard: React Router setup (`/` home, `/onboard` org creation, `/deals/:id` for later acts)
- Dashboard: org creation form + protocol URL/key display (Path B)
- Dashboard: managed agent creation form (Path A) + `ManagedAgentRunner`
- Dashboard: live agent panel (SSE-powered)
- One sample self-hosted agent (simple FastAPI service) that reads `protocol.md` and registers

**Validates**: Open dashboard → create org → create managed agent (Path A) → see it appear. Copy protocol URL + org key → give to sample self-hosted agent → watch it register and appear. Both look identical on dashboard.

### Act 2: "First Opportunity"
**Story**: A supply agent signals a moment. The exchange pre-screens, matches, and delivers the opportunity to demand agents via webhooks. Demand agents see it arrive. Dashboard shows the opportunity feed.

**Delivers**:
- Webhook delivery client (`server/src/engine/webhook.py`) with HMAC signing, retry, and fallback queue
- Orchestrator wired to deliver webhooks after pre-screen + matching
- Matching engine integrated into the API-driven orchestrator flow (currently only in LangGraph graph)
- Data isolation: `GET /deals` filtered by agent (agents only see their own deals)
- Notification polling endpoint returns real queued notifications
- Pixology supply agent as FastAPI service (`agents/pixology_supply/service.py`) with webhook receiver
- Nike demand agent as FastAPI service (`agents/nike_demand/service.py`) with webhook receiver
- Agent webhook handlers respond with hardcoded logic initially (LLM wired in Act 3)
- Dashboard: opportunity feed with match scores, pre-screen conflict results
- Dashboard: deal detail route (`/deals/:id`) with basic info

**Validates**: Start exchange + Pixology service + Nike service → Pixology signals moment → Nike service logs show it received `opportunity.matched` webhook → dashboard shows opportunity with match scores and conflict results → Nike's service auto-responds with a proposal.

### Act 3: "The Negotiation"
**Story**: Agents negotiate autonomously using LLM reasoning. Counter-offers go back and forth. The full conversation is visible on the dashboard in real time.

**Delivers**:
- Claude-powered agent evaluation and negotiation
- Full negotiation loop via webhooks (propose → evaluate → counter → accept)
- Budget enforcement at platform level
- All 4 demo agents as services (Pixology, Nike, Gatorade, Campus Pizza)
- Dashboard: negotiation conversation view with reasoning traces

**Validates**: Trigger moment → watch 4 agents react autonomously → Gatorade blocked → Nike and Pixology negotiate with real LLM reasoning visible on dashboard → deal closes → no human intervention.

### Act 4: "Trust & Delivery"
**Story**: Content is generated, validated by Claude Vision, revised if needed, and delivered. The full audit trail is explorable.

**Delivers**:
- Content validation with Claude Vision
- Revision loop (fail → instructions → revise → resubmit)
- Fulfillment pipeline via webhooks
- Dashboard: content preview, validation results, full audit trail

**Validates**: After deal agreement → content generated → validation runs → results visible on dashboard → deal completes → full audit trail explorable from signal to delivery.

---

## 11. What Changes from Current Codebase

### Keep (solid, tested, correct)
- `server/src/schemas/*` — All Pydantic models
- `server/src/conflict/*` — Conflict engine (20 tests)
- `server/src/matching/*` — Matching engine (16 tests)
- `server/src/engine/state.py`, `events.py` — LangGraph state definitions
- `server/src/engine/deal_making.py` — LangGraph deal-making graph
- `server/src/engine/fulfillment.py` — LangGraph fulfillment graph
- `server/src/config.py` — Settings
- `server/src/api/stream.py` — SSE infrastructure
- `data/seed/conflict_graph.json` — Conflict seed data
- Agent YAML configs (`agents/*/config.yaml`)

### Add (new)
- `server/protocol.md`, `server/protocol/supply.md`, `server/protocol/demand.md`
- `server/src/api/orgs.py` — Organization API
- `server/src/schemas/orgs.py` — Organization models
- `server/src/engine/webhook.py` — Webhook delivery client with HMAC
- `agents/*/service.py` — Each agent as a FastAPI service
- Dashboard pages: onboarding, deal detail, negotiation view

### Rewrite (broken architecture)
- `server/src/engine/orchestrator.py` — Wire webhook delivery into deal flow
- `server/src/api/agents.py` — Require org key, agent-oriented responses
- `server/src/api/deps.py` — Add org auth
- `server/src/store.py` — Add org storage
- `agents/run_demo.py` — Replace with "start services" script (not a puppeteer)
- Dashboard components — Rewrite per act to match new UX

### Delete
- Nothing. But the current agent Python classes (`agents/*/agent.py`) become internal logic used by the new `service.py` wrappers, not standalone scripts.

---

## 12. Resolved Design Decisions

1. **Managed agent hosting**: In-process async tasks within the FastAPI server (see section 5a). No separate processes for managed agents.

2. **LangGraph role**: Orchestrator handles the real-time webhook-driven flow. LangGraph graphs kept for automated testing and managed agent batch execution (see section 9a).

3. **Dashboard framework**: Keep vanilla React + Vite + custom CSS. The dark trading floor theme is distinctive. Add React Router in Act 1 for page navigation.

4. **LLM cost management**: Use Claude Haiku for agent evaluation/negotiation reasoning (fast, cheap). Use Claude Sonnet for content validation in Act 4 (needs better reasoning). Environment variable `AAX_AGENT_MODEL` defaults to `claude-haiku-4-5-20251001`.

5. **Data isolation**: Starting Act 2, `GET /deals` and `GET /proposals` endpoints filter by the authenticated agent's org. Agents cannot see competitor bids or strategies.

## 13. Resolved — Raghav's Input

1. **Content generation**: Mock for now (Claude generates text description + placeholder image URL). Real Pixology API integration comes later — Pixology uses Gemini for image/video generation, so the eventual path is Pixology agent calls Gemini APIs internally.

2. **Hosting**: Google Cloud. Pixology's existing infrastructure is all GCP (GCS, VMs, Firestore, Gemini). AAX will deploy to GCP as well:
   - Exchange server: Cloud Run or GCE VM
   - Dashboard: Cloud Run or static hosting on GCS
   - Protocol files: served by the exchange server (public URL)
   - Agent services (for demo): Cloud Run instances
   - Database (production path): Firestore (already in tech stack)
   - This means the protocol URL will be a real public URL — any agent anywhere can read it and join.
