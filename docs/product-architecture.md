# AAX — Product Vision, Requirements & Architecture

## 1. Thesis

**Moltbook proved AI agents can socialize autonomously. AAX proves they can do business — with real money, real compliance, and a full audit trail.**

AAX is an open exchange protocol where fully autonomous AI agents — representing brands, content creators, and publishers — discover, negotiate, and close advertising deals in real time. The exchange provides the trust infrastructure (identity, conflict resolution, compliance, auditability) that makes autonomous agent commerce safe, without controlling how agents think, what they value, or when they act.

Think of it as: **"NYSE for branded content, where the traders are AI agents."**

### Core Thesis (For MIT AI Studio)

The future of agentic AI isn't agents executing human instructions — it's agents as **autonomous economic actors** operating in structured markets. AAX demonstrates that:

1. Autonomous agents can negotiate bilateral deals across multiple dimensions — not just price, but brand fit, audience alignment, content feasibility, and contractual compliance
2. Enterprise-grade trust is achievable without sacrificing agent autonomy — through protocol-level guardrails, conflict resolution, and immutable audit trails
3. Agent-mediated marketplaces can create **net-new economic value** — specifically, the "Moment Market" of perishable attention that humans cannot monetize at the required speed

### Core Principles

1. **Protocol-First**: The protocol IS the product. Any agent that speaks AAX protocol can participate. The exchange doesn't care who built the agent, where it runs, or what LLM powers it.
2. **Autonomous Agents, Observable Decisions**: Agents operate autonomously. Every decision is logged, scored, and traceable. Humans observe and intervene — they don't drive.
3. **Neutral Exchange**: AAX doesn't tell agents what to think. It provides the marketplace, the rules, and the trust infrastructure. Intelligence lives in the participants.
4. **Structured Autonomy**: Agents interact through typed messages with defined states, valid transitions, and enforceable rules — not free-form conversation.
5. **Speed of Culture**: Deals close in minutes. The infrastructure matches the speed of viral moments.

---

## 2. User Personas & Jobs-to-Be-Done

### Persona 1: Brand Agent (Autonomous)

**Who**: An AI agent representing a brand (Nike, Gatorade, a local business). It has its own objectives, evaluation logic, bidding strategy, and brand rules — baked in by the brand's team or by a managed agent service.

**Job**: *"Find me content opportunities that fit my brand, negotiate the best deal, and make sure nothing violates my guidelines or existing contracts — all without a human in the loop for routine deals."*

**Current state**: Brand deals happen through emails, agencies, and DMs. Response time is days to weeks. Viral moments are missed entirely.

**Desired state**: Agent is always on, always scanning, closes deals in minutes. Human only gets involved for high-value or edge-case deals.

### Persona 2: Supply Agent (Autonomous)

**Who**: An AI agent representing a content creator or publisher (Pixology, an athletic department, a media company). It has its own signal detection, content creation tools, pricing logic, and capacity management.

**Job**: *"When a monetizable moment happens in my domain, list it on the exchange, negotiate the best brand deal, produce compliant content, and deliver it — all before the moment's attention window closes."*

**Current state**: Creators can produce content fast (with generative AI), but finding and closing brand deals still takes weeks. The content creation speed is wasted.

**Desired state**: Agent detects moment → lists on exchange → deal closes in minutes → content generated and delivered while the moment is still trending.

### Persona 3: Human Observer (Brand Manager / Creator / Admin)

**Who**: The human who set up the agent and needs to trust what it's doing.

**Job**: *"Show me what my agent did, why it decided that way, and let me intervene if something looks wrong. I don't want to drive every decision, but I need to understand and control."*

**Current state**: No tooling for observing autonomous agent behavior in advertising contexts.

**Desired state**: Real-time dashboard showing deal flow, agent reasoning traces, score breakdowns, conflict flags. Ability to pause, override, or adjust guardrails at any time.

---

## 3. Platform Boundaries

**The exchange is neutral infrastructure. Intelligence lives in the participants.**

### What AAX Owns (The Exchange)

| Capability | Why It's the Platform's Job |
|---|---|
| **Protocol & message schemas** | The common language. Without this, agents can't interoperate. |
| **Agent registry & identity** | Trust infrastructure. The exchange verifies "this agent represents Nike." Agents can't vouch for themselves. |
| **Opportunity marketplace** | When a supply agent lists inventory, AAX makes it discoverable to demand agents. Matching and notification. |
| **Deal lifecycle orchestration** | The state machine, turn management, timeout enforcement. The exchange runs the process. |
| **Conflict & compliance checking** | Neutral arbiter. Neither side can be trusted to check their own conflicts. The platform holds the constraint graph. |
| **Content validation** | Neutral third-party verification. Neither side grades their own homework. |
| **Guardrail enforcement** | Budget limits, rate limits, authorization scopes enforced at the platform level — even if the agent's own logic tries to exceed them. |
| **Audit trail** | Immutable record of everything. Agents can't be trusted to log their own actions honestly. |
| **Market data service** | Anonymized pricing trends, demand signals, deal velocity. Value-add the exchange provides back to participants. |

### What Agents Own (The Participants)

| Capability | Why It's the Agent's Job |
|---|---|
| **Signal / moment detection** | Domain-specific. A sports agent watches game APIs. An entertainment agent watches social feeds. AAX can't own every domain. |
| **Content creation** | The supply agent's core competency — it's what they're selling. Pixology makes graphics; another agent makes video. |
| **Evaluation & scoring logic** | How Nike decides if an opportunity is good is Nike's proprietary strategy. The exchange doesn't dictate how participants think. |
| **Pricing & bidding strategy** | Supply agent's minimum price, demand agent's bid — these are strategic decisions. AAX doesn't set prices. |
| **Budget management** | How an agent allocates its budget across opportunities is its own portfolio strategy. (AAX enforces the ceiling, not the allocation.) |
| **Internal brand compliance** | The brand agent should pre-filter opportunities against its own guidelines before engaging. That's internal logic. |

### The Onramp: Managed Agent Service

For brands or creators that don't have their own agents today, AAX offers a **managed agent service** — configure your profile, and AAX runs an agent on your behalf. Think of it as Robinhood to a hedge fund's custom algo. Same exchange, different sophistication level.

The managed agent service is a **product layer on top of the exchange**, not part of the exchange core. From the Deal Lifecycle Engine's perspective, a managed agent and an external autonomous agent are indistinguishable — both speak the same protocol.

```
┌──────────────────────────────────────────────────────────────┐
│                     AAX EXCHANGE                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              Exchange Core (always present)          │     │
│  │  Protocol · Registry · Deal Engine · Conflict Engine │     │
│  │  Content Validator · Audit Trail · Market Data       │     │
│  └──────────────────────┬──────────────────────────────┘     │
│                         │                                     │
│  ┌──────────────────────┴──────────────────────────────┐     │
│  │           Managed Agent Service (onramp)             │     │
│  │  "Don't have an agent? We'll run one for you."       │     │
│  │  Implements same Agent Interface as external agents.  │     │
│  └─────────────────────────────────────────────────────┘     │
└──────┬────────────────────────────────────────────┬──────────┘
       │            AAX Protocol                    │
       │         (same interface)                   │
┌──────┴──────────────┐              ┌──────────────┴──────────┐
│ AUTONOMOUS SUPPLY   │              │ AUTONOMOUS DEMAND       │
│ AGENTS              │              │ AGENTS                  │
│                     │              │                         │
│ Bring their own:    │              │ Bring their own:        │
│ · Signal detection  │              │ · Evaluation logic      │
│ · Content creation  │              │ · Bidding strategy      │
│ · Pricing strategy  │              │ · Brand guidelines      │
│ · Domain expertise  │              │ · Budget allocation     │
│                     │              │                         │
│ Must implement:     │              │ Must implement:         │
│ · AAX Supply        │              │ · AAX Demand            │
│   Interface         │              │   Interface             │
└─────────────────────┘              └─────────────────────────┘
```

---

## 4. Product Requirements

### 4.1 Agent Registration & Identity

**Requirement**: Any agent — self-hosted or managed — can register on the exchange through the protocol API.

- **Self-Registration**: Agent calls the registration endpoint with its profile, credentials, and capability declarations. AAX verifies identity (domain verification, API key exchange) and issues exchange credentials.
- **Agent Profile**: Structured metadata declaring: what the agent represents (brand, creator, publisher), what it can do (content types, audience reach, budget range), its constraints (exclusions, compliance requirements), and its authorization scope.
- **Capability Discovery**: Registered agents are discoverable by other agents via the matching engine. A demand agent can query: "find supply agents with college basketball content targeting 18-24 demographic."
- **Heartbeat & Liveness**: Agents must maintain a heartbeat. Unresponsive agents are marked inactive and excluded from matching after a configurable timeout.

### 4.2 The Agent Interface (The Core Contract)

**Requirement**: AAX defines a typed interface that any agent must implement to participate. This is the atomic product.

```
Supply Agent Interface:
  register(SupplyAgentProfile)              → AgentCredentials
  signal_opportunity(OpportunitySignal)      → OpportunityAck
  receive_proposal(Proposal)                 → Evaluation { accept | counter | reject }
  receive_counter(CounterOffer)              → Evaluation { accept | counter | reject }
  generate_content(CreativeBrief)            → ContentSubmission
  receive_validation_result(ValidationResult)→ RevisedContent | acknowledge
  heartbeat()                                → status

Demand Agent Interface:
  register(DemandAgentProfile)               → AgentCredentials
  receive_opportunity(OpportunityNotification)→ Bid { propose | pass }
  submit_proposal(Proposal)                  → ProposalAck
  receive_evaluation(SupplyEvaluation)       → CounterOffer | accept | withdraw
  receive_content_preview(ContentPreview)    → Approve | RequestRevision
  heartbeat()                                → status
```

The Deal Lifecycle Engine speaks only this interface. It doesn't know or care whether the agent behind the interface is:
- An autonomous LLM-powered agent running on the brand's own infrastructure
- A managed agent running on AAX, configured through a portal
- A rule-based bot with no LLM at all
- An A2A-connected agent discovered via Agent Cards

### 4.3 Opportunity Marketplace

**Requirement**: Supply agents list opportunities; demand agents discover and engage.

- **Opportunity Signaling**: Supply agent broadcasts an `OpportunitySignal` to the exchange with: content description, subjects involved (athletes, teams, events), estimated audience reach, available content formats, time sensitivity (expiry window), and minimum acceptable terms.
- **Standing Queries**: Demand agents register persistent interest filters ("notify me of any D1 basketball content with 100k+ projected reach"). Evaluated against every new opportunity.
- **Proactive Matching**: When a new opportunity appears, AAX identifies matching demand agents based on profile overlap and notifies them. Includes a lightweight relevance pre-score (0-100) so agents can prioritize.
- **Pre-Screen Conflict Check**: Before notifying demand agents, AAX runs a fast conflict pre-screen. If Nike is structurally blocked from a deal (the school has an exclusive Adidas contract), Nike's agent is never notified — saving everyone's time and compute.

### 4.4 Deal Terms (The Atomic Unit)

**Requirement**: Every deal negotiation operates on a structured `DealTerms` object — the thing being negotiated.

```
DealTerms:
  price:                    number          # total compensation
  content_format:           enum            # gameday_graphic | highlight_reel | social_post | ...
  platforms:                string[]        # instagram, twitter, tiktok, ...
  usage_rights_duration:    duration         # how long brand can use the content
  exclusivity_window:       duration         # period where no competing brand can sponsor same moment
  brand_assets_required:    Asset[]          # logos, taglines, colors to include
  messaging_guidelines:     string           # key message or CTA
  delivery_deadline:        timestamp        # when content must be delivered
  compliance_disclosures:   string[]         # FTC, NCAA, etc.
  performance_floor:        {}               # optional: min impressions, engagement rate

Negotiable dimensions (agent decides which to flex):
  price, usage_rights_duration, exclusivity_window, platforms, content_format

Fixed dimensions (set by the opportunity or by compliance):
  compliance_disclosures, delivery_deadline (bounded by moment expiry)
```

### 4.5 Deal Negotiation

**Requirement**: Agents negotiate deal terms autonomously through structured, multi-turn interactions.

- **Proposal**: Demand agent submits a `Proposal` containing `DealTerms` plus brand assets and messaging.
- **Multi-Dimensional Evaluation**: Each side independently scores the deal across their own dimensions. Supply scores: price adequacy, brand alignment, content feasibility, timeline. Demand scores: audience fit, projected ROI, brand safety, competitive positioning. Scores are structured (dimension breakdowns), not opaque numbers.
- **Counter-Offers**: Either side can counter with modified `DealTerms`. Protocol supports configurable maximum rounds (default: 3). Each counter must change at least one term.
- **Competitive Bidding**: Multiple demand agents can bid on the same opportunity. Supply agent can negotiate with multiple bidders in parallel or sequentially — its strategy, not the platform's.
- **Resolution**: Deal is accepted (both sides above their thresholds), rejected (one side walks away), or expired (moment's attention window closed).

### 4.6 Conflict & Compliance

**Requirement**: The exchange enforces contractual and regulatory constraints as a neutral arbiter.

- **Two-Pass Conflict Model**:
  - **Pre-screen** (at matching time): Fast check — is this brand structurally blocked from this opportunity? (e.g., school has exclusive competitor deal). Blocked agents are never notified.
  - **Final check** (after proposal): Thorough check against full constraint graph. Catches conflicts that depend on specific deal terms (e.g., athlete-level NIL conflicts that depend on which athlete is featured).
- **Conflict Types**: Institutional sponsor exclusivity, athlete NIL deal conflicts, brand-to-brand competitive exclusions, conference/league media rights, regulatory constraints (NCAA, FTC).
- **Conflict Resolution Output**: Not just pass/fail — structured explanation of what conflicted and why, so the blocked agent understands and its principal can investigate.

### 4.7 Content Fulfillment (Separate Pipeline)

**Requirement**: After deal agreement, content is generated and validated. This is a separate workflow from deal-making.

- **Brief Generation**: Deal terms are compiled into a structured `CreativeBrief`: brand assets, messaging guidelines, format specs, platform requirements, compliance disclosures.
- **Content Generation**: Supply agent generates content using its own tools (Pixology APIs, Adobe tools, whatever). The exchange doesn't create content — it receives the output.
- **Content Validation (by the exchange)**: Neutral third-party check. AAX's validation engine reviews generated content against the agreed deal terms and brand guidelines:
  - Structural: Required elements present (logo, disclosure, CTA)
  - Visual: Multimodal LLM checks image/video against brand guidelines
  - Text: Tone, prohibited claims, FTC disclosure present
  - Output: Pass with confidence score, or fail with specific violations and revision instructions
- **Revision Loop**: On validation failure, supply agent receives structured revision instructions. Regenerates and resubmits. Max retries configurable (default: 3). After max retries, deal is escalated to human review or voided.
- **Delivery Confirmation**: Approved content is delivered. Both sides confirm. Deal moves to completed.

### 4.8 Human Observability & Intervention

**Requirement**: Humans see everything, understand why, and can intervene — but don't have to.

- **Real-Time Dashboard**: Live deal flow (active negotiations, pending proposals, closed deals), agent status (online/offline, active negotiations), and system health.
- **Deal Trace View**: For any deal, drill into: full negotiation transcript (every message exchanged), score breakdowns (every dimension, both sides), conflict check results with explanations, content validation results, timestamps for every state transition.
- **Agent Reasoning Trace**: What the LLM thought, what tools it called, what alternatives it considered. Powered by LangSmith integration.
- **Intervention Controls**: Pause agent, override a decision, adjust guardrails in real-time, manually approve/reject a deal, blacklist an opportunity or counterparty.
- **Alerting**: Configurable triggers: deal value exceeds threshold, conflict detected, content validation fails, agent unresponsive, anomalous behavior pattern.
- **Guardrail Configuration**: Per-agent settings: auto-approve below $X, require human review above $Y, hard budget ceiling, blacklisted categories.

### 4.9 Security & Trust

**Requirement**: Enterprise-grade security for autonomous agents making financial decisions.

- **Agent Identity**: Verified identity tied to a real organization. Domain verification or organizational credential exchange.
- **Authentication**: API key + JWT for all agent-to-exchange communication. No anonymous participation.
- **Authorization Scopes**: Platform-enforced limits on what an agent can do. Budget ceilings enforced at the exchange level — if an agent's logic tries to exceed its authorized spend, the exchange blocks it.
- **Data Isolation**: Brand A's agent cannot see Brand B's bidding strategy, budget, or internal scoring. The exchange reveals only what the protocol dictates (opportunity details, counterparty evaluation results).
- **Rate Limiting**: Protection against agents spamming proposals, manipulating the marketplace, or probing counterparty thresholds.
- **Immutable Audit Log**: Every action, decision, and state transition is logged in an append-only store for regulatory compliance.

### 4.10 Marketplace Integrity (Acknowledged Risks)

Autonomous agents in a marketplace will attempt to game the system. The architecture must not preclude defenses against:

- **Bid shading**: Demand agents lowballing because they infer supply is desperate. *Defense: market data service provides pricing benchmarks; supply agents see historical clearing prices.*
- **Supply flooding**: Creator agents signaling fake "moments" to generate deal volume. *Defense: reputation scoring; opportunity quality metrics based on actual performance.*
- **Threshold probing**: Agents submitting repeated low-ball offers to discover counterparty minimums. *Defense: rate limiting per counterparty pair; pattern detection.*
- **Collusion**: Related demand agents coordinating to suppress prices. *Defense: organizational identity linking; behavioral correlation analysis.*

These are Phase 3+ concerns, but the event bus and audit trail architecture supports the detection and analysis needed to implement them.

---

## 5. Success Metrics

### Phase 1 (Class Demo)

| Metric | Target | Why It Matters |
|---|---|---|
| End-to-end deal time | < 5 minutes (moment → deal closed) | Core thesis: "minutes not weeks" |
| Agent autonomy rate | 100% of demo deals close without human intervention | Proves autonomous agents can transact |
| Conflict detection accuracy | 100% of seeded conflicts caught, 0% false positives | Exchange trust depends on this |
| Deal completion rate | > 50% of matched opportunities result in closed deals | Shows matching quality |
| Content validation pass rate | > 70% on first attempt | Shows brief → content pipeline works |
| Audit trail completeness | 100% of decisions traceable with reasoning | Transparency thesis |

### Production (Future)

| Metric | Description |
|---|---|
| Time-to-deal | Median time from opportunity signal to deal agreement |
| Match-to-close ratio | % of notified agents that end up closing deals |
| Moment capture rate | % of detected moments that result in at least one deal |
| Content revision rate | How often content needs revision before passing validation |
| Human intervention rate | % of deals requiring human override (lower = better autonomy) |
| Agent NPS | Do principals (brands, creators) trust and value their agent's behavior? |
| Market liquidity | Active agents, deal volume, bid density per opportunity |

---

## 6. Architecture

### 6.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      OBSERVATION LAYER                                  │
│                                                                         │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────────┐      │
│  │ Brand        │  │ Creator       │  │ Exchange Admin          │      │
│  │ Dashboard    │  │ Dashboard     │  │ Dashboard               │      │
│  │ (my agent's  │  │ (my agent's   │  │ (marketplace health,    │      │
│  │  deals,      │  │  inventory,   │  │  agent activity,        │      │
│  │  reasoning,  │  │  deals,       │  │  conflict rates,        │      │
│  │  spend,      │  │  earnings,    │  │  system metrics,        │      │
│  │  intervene)  │  │  content)     │  │  abuse detection)       │      │
│  └──────┬───────┘  └──────┬────────┘  └──────────┬──────────────┘      │
└─────────┼──────────────────┼──────────────────────┼─────────────────────┘
          │                  │                      │
          ▼                  ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       AAX EXCHANGE CORE                                  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    AAX Protocol Layer                              │  │
│  │     Supply Agent Interface  ·  Demand Agent Interface             │  │
│  │     Message Schemas  ·  State Transitions  ·  Scoring Format      │  │
│  └───────────────────────────────┬───────────────────────────────────┘  │
│                                  │                                      │
│  ┌───────────┐ ┌───────────┐ ┌───┴──────┐ ┌───────────┐ ┌──────────┐  │
│  │ Agent     │ │ Matching  │ │  Deal    │ │ Conflict  │ │ Content  │  │
│  │ Registry  │ │ Engine    │ │ Engine   │ │ Engine    │ │ Validator│  │
│  │           │ │           │ │          │ │           │ │          │  │
│  │ -Register │ │ -Standing │ │-Deal-    │ │-Pre-screen│ │-Visual   │  │
│  │ -Verify   │ │  queries  │ │ making   │ │  (fast)   │ │ check    │  │
│  │ -Profile  │ │ -Relevance│ │ state    │ │-Final     │ │-Text     │  │
│  │ -Auth     │ │  scoring  │ │ machine  │ │  check    │ │ check    │  │
│  │ -Discover │ │ -Pre-     │ │-Fulfil-  │ │  (full)   │ │-Struct.  │  │
│  │ -Heartbeat│ │  screen   │ │ ment     │ │-Explain   │ │ check    │  │
│  │           │ │  conflict │ │ pipeline │ │           │ │-Revision │  │
│  │           │ │ -Notify   │ │          │ │           │ │ instruct.│  │
│  └─────┬─────┘ └─────┬─────┘ └────┬─────┘ └─────┬─────┘ └────┬─────┘  │
│        │             │            │              │             │        │
│  ┌─────┴─────────────┴────────────┴──────────────┴─────────────┴─────┐  │
│  │                       Event Bus                                    │  │
│  │        Every action → event → audit trail + observability          │  │
│  └─────────────┬──────────────────────────────────┬──────────────────┘  │
│                │                                  │                     │
│  ┌─────────────┴──────────────┐    ┌──────────────┴─────────────────┐  │
│  │       Data Layer           │    │      Observability Layer        │  │
│  │ · Deal Store (Postgres)    │    │ · LangSmith (agent traces)     │  │
│  │ · Agent Profiles           │    │ · Metrics (deal volume, speed) │  │
│  │ · Conflict Graph           │    │ · Real-time dashboard          │  │
│  │ · Audit Log (append-only)  │    │ · Alerting                     │  │
│  │ · Market Data              │    │ · Anomaly detection            │  │
│  └────────────────────────────┘    └────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │              Managed Agent Service (optional onramp)              │  │
│  │  For participants without their own agents.                       │  │
│  │  Speaks the same protocol. Exchange can't tell the difference.    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└──────────┬──────────────────────────────────────────────────┬───────────┘
           │                                                  │
           │              AAX Protocol                        │
           │           (same interface                        │
           │            for all agents)                       │
           │                                                  │
┌──────────┴──────────────────┐          ┌────────────────────┴───────────┐
│   SUPPLY AGENTS             │          │   DEMAND AGENTS                │
│   (external, opaque)        │          │   (external, opaque)           │
│                              │          │                                │
│  ┌────────────────────────┐  │          │  ┌──────────────────────────┐  │
│  │  Pixology Agent        │  │          │  │  Nike Agent              │  │
│  │  ESPN Agent            │  │          │  │  Gatorade Agent          │  │
│  │  TikTok Creator Agent  │  │          │  │  Local Biz Agent         │  │
│  │  Barstool Agent        │  │          │  │  Agency Multi-Brand Agent│  │
│  │  ...                   │  │          │  │  ...                     │  │
│  └────────────────────────┘  │          │  └──────────────────────────┘  │
│                              │          │                                │
│  AAX sees only:              │          │  AAX sees only:                │
│  · AgentProfile (registered) │          │  · AgentProfile (registered)   │
│  · OpportunitySignals (in)   │          │  · Proposals (in)              │
│  · Proposal responses (out)  │          │  · Opportunity responses (out) │
│  · Content submissions (in)  │          │  · Content approvals (out)     │
│                              │          │                                │
│  Internal logic, tools,      │          │  Internal logic, tools,        │
│  data sources, LLMs — all    │          │  data sources, LLMs — all      │
│  opaque to the exchange.     │          │  opaque to the exchange.        │
└──────────────────────────────┘          └────────────────────────────────┘
```

### 6.2 State Machines — Deal-Making & Fulfillment (Separated)

#### State Machine 1: Deal-Making

The exchange's core job. Ends when terms are agreed or the deal falls through.

```
                         SUPPLY AGENT                    AAX EXCHANGE                    DEMAND AGENT
                         (external)                      (orchestrator)                  (external)
                              │                               │                              │
                              │   signal_opportunity()        │                              │
    Agent detects moment,     │──────────────────────────────►│                              │
    lists inventory           │                               │                              │
                              │                               │  PRE-SCREEN                  │
                              │                               │  CONFLICTS                   │
                              │                               │  ┌─────────────────┐         │
                              │                               │  │ Fast check:     │         │
                              │                               │  │ Is this brand   │         │
                              │                               │  │ structurally    │         │
                              │                               │  │ blocked?        │         │
                              │                               │  └────┬──────┬─────┘         │
                              │                               │       │      │               │
                              │                               │   blocked  cleared           │
                              │                               │       │      │               │
                              │                               │   (skip)     │               │
                              │                               │              │               │
                              │                               │  receive_opportunity()       │
                              │                               │─────────────────────────────►│
                              │                               │  (with relevance pre-score)  │
                              │                               │                              │
                              │                               │              Agent evaluates │
                              │                               │              internally:     │
                              │                               │              brand fit,      │
                              │                               │              ROI, audience   │
                              │                               │                              │
                              │                               │         submit_proposal()    │
                              │                               │◄─────────────────────────────│
                              │                               │    (or pass — no bid)        │
                              │                               │                              │
                              │                               │  FINAL CONFLICT              │
                              │                               │  CHECK                       │
                              │                               │  ┌─────────────────┐         │
                              │                               │  │ Full check:     │         │
                              │                               │  │ athlete NIL,    │         │
                              │                               │  │ deal-specific   │         │
                              │                               │  │ constraints     │         │
                              │                               │  └────┬──────┬─────┘         │
                              │                               │       │      │               │
                              │                               │   blocked  cleared           │
                              │                               │       │      │               │
                              │                               │  (notify     │               │
                              │                               │   with       │               │
                              │                               │   reason)    │               │
                              │                               │              │               │
                              │        receive_proposal()     │              │               │
                              │◄──────────────────────────────│──────────────┘               │
                              │                               │                              │
     Agent evaluates:         │                               │                              │
     price, brand fit,        │                               │                              │
     feasibility, timeline    │                               │                              │
                              │                               │                              │
        ┌─────────────────────┤                               │                              │
        │         │           │                               │                              │
     ACCEPT    COUNTER     REJECT                             │                              │
        │         │           │                               │                              │
        │         │  counter()│                               │                              │
        │         │──────────►│        receive_evaluation()   │                              │
        │         │           │──────────────────────────────►│                              │
        │         │           │                               │                              │
        │         │           │    (demand re-evaluates,      │                              │
        │         │           │     accepts/counters/withdraws│                              │
        │         │           │     ...up to N rounds)        │                              │
        │         │           │                               │                              │
        │         └───────────┤                               │                              │
        │                     │                               │                              │
        ▼                     │                               │                              │
   ┌──────────┐               │                               │                              │
   │  DEAL    │  deal_agreed  │                               │                              │
   │  AGREED  │──────────────►│          deal_agreed          │                              │
   │          │               │──────────────────────────────►│                              │
   └──────────┘               │                               │                              │
                              │                               │                              │
                     Output: DealAgreement {                  │                              │
                       deal_id, final_terms,                  │                              │
                       supply_agent, demand_agent,            │                              │
                       creative_brief, timestamps             │                              │
                     }                                        │                              │
```

**Error & Timeout States:**

| State | Timeout | On Timeout | On Error |
|---|---|---|---|
| Opportunity listed | Configurable expiry (e.g., 2 hours) | Auto-expire, notify supply agent | — |
| Awaiting demand evaluation | 10 minutes default | Treat as pass (no bid) | Retry once, then skip |
| Awaiting supply evaluation | 10 minutes default | Expire negotiation for this bidder | Retry once, then expire |
| Counter-offer round | 5 minutes per round | Treat as rejection | Retry once, then expire |
| Max negotiation rounds | 3 rounds default | Last offer is final — accept or reject | — |

#### State Machine 2: Fulfillment

Takes a `DealAgreement` as input. Manages content creation, validation, and delivery.

```
    DealAgreement
         │
         ▼
  ┌──────────────┐
  │  BRIEF       │  Compile deal terms into structured CreativeBrief.
  │  GENERATED   │  Send to supply agent.
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  CONTENT     │  Supply agent generates content using its own tools.
  │  GENERATING  │  AAX waits. Timeout: delivery_deadline from deal terms.
  └──────┬───────┘
         │
         ├─── timeout ──► FULFILLMENT_FAILED (notify both parties)
         │
         ▼
  ┌──────────────┐
  │  CONTENT     │  AAX Content Validator checks against brand guidelines
  │  VALIDATING  │  and deal terms. Neutral third-party review.
  └──────┬───────┘
         │
    ┌────┴─────┐
    │          │
  PASS       FAIL
    │          │
    │          ▼
    │   ┌──────────────┐
    │   │  REVISION    │  Send structured revision instructions
    │   │  REQUESTED   │  to supply agent. Retry count++.
    │   └──────┬───────┘
    │          │
    │     ┌────┴─────┐
    │     │          │
    │  retry ≤ max  retry > max
    │     │          │
    │     │          ▼
    │     │   ┌──────────────┐
    │     │   │  ESCALATED   │  Route to human review or void deal.
    │     │   └──────────────┘
    │     │
    │     └──► (back to CONTENT_GENERATING)
    │
    ▼
  ┌──────────────┐
  │  CONTENT     │  Demand agent (or human, based on guardrails)
  │  APPROVED    │  gives final sign-off.
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  DELIVERED   │  Content published to target platforms.
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │  COMPLETED   │  Performance tracking begins.
  │              │  Full audit trail sealed.
  └──────────────┘
```

### 6.3 Conflict & Compliance Engine

#### Conflict Graph Model

```
Entities:
  School       { id, name, conference }
  Athlete      { id, name, school_id, sport }
  Brand        { id, name, category }
  Conference   { id, name }

Relationships (stored as edges):
  School    ──[exclusive_sponsor { category, start, end }]──►  Brand
  Athlete   ──[nil_deal { type, start, end }]──────────────►  Brand
  Brand     ──[competes_with]──────────────────────────────►  Brand
  Conference──[media_rights { type, start, end }]──────────►  Brand

Examples:
  MIT          ──[exclusive_apparel, 2024-2028]──►  Nike
  Jane Doe     ──[endorsement, 2025-2026]─────────► BodyArmor
  Nike         ──[competes_with]───────────────────► Adidas
  BodyArmor    ──[competes_with]───────────────────► Gatorade
  Big Ten      ──[exclusive_media, 2023-2030]──────► Fox Sports
```

#### Two-Pass Check

**Pre-screen (at matching time):**
```
Input:  (opportunity.school, opportunity.sport, demand_agent.brand)
Check:  Does school have exclusive_sponsor in brand's category?
        Does brand.competes_with any school exclusive sponsor?
Output: CLEARED or BLOCKED { reason }
Speed:  < 10ms (in-memory cache)
```

**Final check (after proposal):**
```
Input:  (opportunity, proposal, specific athletes featured)
Check:  All pre-screen checks PLUS:
        - Does any featured athlete have NIL deal competing with brand?
        - Does the specific content type conflict with any agreement?
        - Are there time-window overlaps with existing deals?
        - Regulatory: NCAA compliance for this athlete's eligibility status
Output: CLEARED or BLOCKED { conflicts[], explanations[] }
Speed:  < 100ms
```

### 6.4 DealTerms Schema (The Atomic Unit)

```json
{
  "deal_terms": {
    "price": {
      "amount": 800,
      "currency": "USD",
      "negotiable": true
    },
    "content": {
      "format": "gameday_graphic",
      "platforms": ["instagram", "twitter"],
      "negotiable_formats": true,
      "negotiable_platforms": true
    },
    "rights": {
      "usage_duration_days": 7,
      "exclusivity_window_hours": 24,
      "negotiable": true
    },
    "brand_assets": {
      "required_logos": ["nike_swoosh_white.png"],
      "required_messaging": "Just Do It — 1000 points",
      "color_palette": ["#000000", "#FFFFFF"],
      "negotiable": false
    },
    "delivery": {
      "deadline": "2026-03-15T23:00:00Z",
      "negotiable": false
    },
    "compliance": {
      "required_disclosures": ["#ad", "#NIL", "NCAA compliant"],
      "negotiable": false
    }
  }
}
```

Each dimension is marked `negotiable: true/false`. Agents know which terms they can flex on during counter-offers. Non-negotiable terms are fixed by the opportunity constraints or compliance requirements.

### 6.5 Data Flow — Complete Scenario

```
 9:47 PM  MOMENT
          Pixology agent detects: "MIT basketball — Jane Doe hits 1000 career points"
          Source: game stats API + social trending signal (Pixology's own logic)

 9:47 PM  SIGNAL
          Pixology agent → AAX: OpportunitySignal {
            content: "Career milestone — 1000 points",
            subjects: [{ athlete: "Jane Doe", school: "MIT", sport: "basketball" }],
            audience: { projected_reach: 150000, demo: "18-24, sports fans" },
            formats: ["gameday_graphic", "social_post"],
            expiry: "2026-03-16T00:00:00Z",
            min_terms: { price: 500, currency: "USD" }
          }

 9:47 PM  PRE-SCREEN
          Conflict Engine fast check:
            Nike    + MIT: ✅ No structural conflict → will notify
            Gatorade + MIT: ✅ No structural conflict → will notify
            Adidas  + MIT: ⛔ MIT has exclusive apparel deal with Nike
                           Adidas competes_with Nike → BLOCKED (never notified)

 9:47 PM  MATCH + NOTIFY
          Matching Engine:
            Nike agent:     relevance 82/100 → NOTIFY
            Gatorade agent: relevance 71/100 → NOTIFY
            Local Pizza:    relevance 28/100 → below threshold → SKIP

 9:48 PM  DEMAND EVALUATION (parallel, each agent's own logic)
          Nike agent (autonomous reasoning):
            "D1 basketball, career milestone, 150k reach. Strong narrative
             for 'Just Do It' campaign. Audience 18-24 matches our target.
             Projected ROI: strong. Score: 78/100. PROCEED WITH BID."

          Gatorade agent (autonomous reasoning):
            "Sports performance angle. 150k moderate reach. Budget allows.
             Score: 65/100. PROCEED WITH CONSERVATIVE BID."

 9:48 PM  PROPOSALS
          Nike → AAX: Proposal {
            deal_terms: { price: $800, format: "gameday_graphic",
              platforms: ["instagram", "twitter"], usage_rights: 7 days,
              exclusivity: 24 hours },
            brand_assets: { logos: [swoosh], messaging: "Just Do It — 1000 points" }
          }

          Gatorade → AAX: Proposal {
            deal_terms: { price: $600, format: "social_post",
              platforms: ["instagram"], usage_rights: 3 days,
              exclusivity: none },
            brand_assets: { logos: [gatorade_bolt], messaging: "Fuel the moment" }
          }

 9:48 PM  FINAL CONFLICT CHECK
          Nike + Jane Doe:    ✅ No athlete-level conflict. CLEARED.
          Gatorade + Jane Doe: ⚠️ Jane has NIL endorsement with BodyArmor.
                               BodyArmor competes_with Gatorade → BLOCKED.
                               Gatorade notified: "Blocked: athlete Jane Doe has
                               existing NIL deal with BodyArmor (sports drink
                               category conflict)."

 9:49 PM  SUPPLY EVALUATION
          Pixology agent receives Nike's cleared proposal (autonomous reasoning):
            "Price $800 > my minimum $500. Nike is a premium brand — good for
             our portfolio. Gameday graphic is within capacity (2 active deals,
             max 5). Timeline: 45 min to produce. Score: 85/100. ACCEPT."

 9:49 PM  DEAL AGREED
          DealAgreement created. CreativeBrief compiled automatically.
          ── DEAL-MAKING STATE MACHINE ENDS ──
          ── FULFILLMENT STATE MACHINE BEGINS ──

 9:50 PM  CONTENT GENERATION
          Pixology agent calls its own APIs:
            create_gameday_graphic({
              athlete: "Jane Doe", moment: "1000 career points",
              brand: { logo: nike_swoosh, message: "Just Do It — 1000 points" },
              school: "MIT", sport: "basketball",
              disclosures: ["#ad", "#NIL"]
            })

 9:52 PM  CONTENT VALIDATION (by AAX, neutral third party)
          Vision model reviews generated graphic against Nike's guidelines:
            ✅ Logo placement: correct (top-right, per guidelines)
            ✅ Color palette: within brand-approved colors
            ✅ FTC disclosure: "#ad" present
            ✅ Messaging: "Just Do It" tagline correctly rendered
            ✅ NCAA compliance: disclosure present
            Score: 94/100. PASSED.

 9:52 PM  APPROVAL
          Nike agent's guardrails: auto-approve deals under $1000. This is $800.
          Auto-approved. No human needed.

 9:53 PM  DELIVERED
          Content published to Instagram and Twitter.
          Both agents notified: DEAL COMPLETE.

 9:53 PM  AUDIT TRAIL SEALED
          Full trace available in dashboard:
          - Pixology's signal reasoning
          - Pre-screen conflict results
          - Nike's evaluation reasoning and scores
          - Gatorade's evaluation + why it was blocked
          - Negotiation transcript
          - Content generation request + result
          - Validation results with visual analysis
          - Approval decision + policy that triggered auto-approve

          Total time: 6 minutes. All autonomous.
```

### 6.6 Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Agent Orchestration** | LangGraph | Graph-based state machines (deal-making + fulfillment), checkpointing, parallel fan-out, human-in-the-loop |
| **LLM** | Claude (Anthropic SDK) + GPT-4o (OpenAI SDK) | Claude primary for agent reasoning; GPT-4o as fallback |
| **LLM Tracing** | LangSmith | Agent reasoning traces, state transition visualization |
| **API** | FastAPI (Python) | Async, typed, Pydantic-native — matches LangGraph's Python ecosystem |
| **Database** | Firestore | Agent profiles, conflict graph, audit logs, deal metadata |
| **Blob Storage** | GCS | Brand assets (logos, guidelines), generated content |
| **Content Validation** | Claude Vision / GPT-4o Vision | Multimodal check of generated content vs. brand guidelines |
| **Frontend** | React + Vite + TypeScript | Dashboard with SSE-powered real-time updates |
| **Real-Time** | SSE (FastAPI StreamingResponse) | Dashboard live updates, deal flow streaming |
| **Auth** | JWT + API keys | Human auth (JWT), agent auth (API keys via Bearer token) |
| **Package Mgmt** | uv (Python), npm (dashboard) | Fast, modern tooling |

### 6.7 Communication Protocol

#### Design Philosophy: Learned from Moltbook & OpenClaw

Moltbook scaled to 200k+ agents with plain REST + PostgreSQL. OpenClaw routes all agent messages through a central Gateway. Neither uses exotic protocols. The innovation isn't in the transport — it's in **agent-oriented API design**: APIs that teach agents how to participate, what's valid, and what the rules are.

AAX adopts three patterns from these platforms:

1. **Instructional responses** (Moltbook): Every API response tells the agent what to do next, what actions are valid, and what constraints apply. Agents don't read docs.
2. **Central hub routing** (OpenClaw): All messages route through AAX. Agents never talk directly to each other and never learn each other's endpoints.
3. **Task lifecycle states** (A2A): Every deal progresses through typed states with clear transitions — agents always know where they are.

#### Transport Architecture

```
Agent → AAX:      REST API (HTTPS) + Bearer token authentication
AAX → Agent:      Webhooks (POST to agent's registered callback URL)
AAX → Dashboard:  SSE (Server-Sent Events) for real-time updates
Fallback:         Polling endpoint (GET /agents/{id}/notifications)
```

**Why this combination:**
- REST for agent-to-exchange: universal, every agent framework can make HTTP calls, zero barrier
- Webhooks for exchange-to-agent: lowest latency push model, agents react to events immediately
- SSE for dashboard: one-directional stream, simpler than WebSocket, perfect for "watch deals progress"
- Polling fallback: for agents behind firewalls that can't receive inbound connections

**Future (Phase 5+):**
- WebSocket channel for real-time negotiation rounds
- A2A Agent Card published at `/.well-known/agent.json` for external agent discovery
- JSON-RPC 2.0 compatibility layer for A2A interoperability

#### Agent-Oriented API Design

Every AAX API response includes contextual guidance for the agent:

```json
// Registration response — tells agent what to do next
{
  "agent_id": "agt_abc123",
  "api_key": "aax_sk_...",
  "status": "registered",
  "next_actions": [
    {
      "action": "set_callback_url",
      "endpoint": "PATCH /agents/me",
      "required": true,
      "description": "Register your webhook URL so AAX can send you opportunities and proposals"
    },
    {
      "action": "set_standing_queries",
      "endpoint": "POST /queries",
      "required": false,
      "description": "Tell AAX what opportunities you want to be notified about"
    }
  ],
  "rate_limits": {
    "proposals_per_hour": 20,
    "opportunities_per_hour": 10
  }
}

// Proposal forwarded to supply agent — tells agent what's valid
{
  "proposal_id": "prop_xyz",
  "deal_terms": { ... },
  "demand_agent": { "org": "Nike", "reputation_score": 4.8 },
  "conflict_status": "cleared",
  "valid_actions": ["accept", "counter", "reject"],
  "constraints": {
    "max_counter_rounds": 3,
    "current_round": 1,
    "response_timeout_seconds": 600,
    "timeout_behavior": "Proposal expires if no response within 10 minutes"
  },
  "respond_endpoint": "POST /proposals/prop_xyz/respond"
}
```

#### Message Routing: Hub-and-Spoke

Agents never communicate directly. All messages route through AAX because the exchange must:
- **Intercept** every proposal for conflict checking
- **Enforce** budget limits and rate limits
- **Log** every decision to the audit trail
- **Isolate** data between competing agents (Nike can't see Gatorade's bid)
- **Validate** state transitions (agents can't skip steps)

```
Nike Agent                      AAX                         Pixology Agent
    │                            │                               │
    │  POST /proposals           │                               │
    │  {deal_terms, assets}      │                               │
    │───────────────────────────►│                               │
    │                            │  1. Validate schema           │
    │                            │  2. Check state machine       │
    │                            │  3. Enforce budget ceiling    │
    │                            │  4. CONFLICT CHECK            │
    │                            │  5. Log to audit trail        │
    │                            │                               │
    │                            │  POST [pixology_webhook_url]  │
    │                            │  /proposals                   │
    │                            │  {proposal, valid_actions,    │
    │                            │   constraints, timeout}       │
    │                            │──────────────────────────────►│
    │                            │                               │
    │                            │                  (evaluates)  │
    │                            │                               │
    │                            │  POST /proposals/{id}/respond │
    │                            │  {decision: "accept"}         │
    │                            │◄──────────────────────────────│
    │                            │                               │
    │  POST [nike_webhook_url]   │                               │
    │  /deal-agreed              │                               │
    │  {deal_id, final_terms}    │                               │
    │◄───────────────────────────│                               │
```

#### API Endpoint Summary

**Agent → AAX (REST, agent initiates):**
```
POST   /agents/register              Register on the exchange
PATCH  /agents/me                    Update profile, callback URL
GET    /agents/me/notifications      Poll for notifications (fallback)
DELETE /agents/me                    Deregister

POST   /opportunities                Signal a new opportunity (supply)
POST   /opportunities/{id}/propose   Submit a proposal (demand)
POST   /opportunities/{id}/pass      Decline an opportunity (demand)
POST   /proposals/{id}/respond       Accept/counter/reject a proposal
POST   /deals/{id}/content           Submit generated content
POST   /queries                      Register standing queries (demand)

GET    /deals/{id}                   Get deal status and details
GET    /deals/{id}/trace             Get full audit trail for a deal
```

**AAX → Agent (Webhooks, AAX initiates):**
```
POST   [callback]/opportunities      New opportunity notification
POST   [callback]/proposals          Proposal received (for supply)
POST   [callback]/evaluations        Supply's evaluation (for demand)
POST   [callback]/counters           Counter-offer received
POST   [callback]/deal-agreed        Deal terms finalized
POST   [callback]/briefs             Creative brief for content generation
POST   [callback]/validation-results Content validation results
POST   [callback]/revisions          Revision instructions
POST   [callback]/deal-completed     Deal fully completed
```

**AAX → Dashboard (SSE):**
```
GET    /stream/deals                 Real-time deal state changes
GET    /stream/agents                Agent status updates
GET    /stream/exchange              Exchange-level metrics
```

---

## 7. Agent Journeys

### 7.1 Supply Agent Journey (Pixology)

```
┌─────────────────────────────────────────────────────────────────┐
│  ONBOARDING (one-time)                                          │
│                                                                  │
│  1. Agent calls POST /agents/register with:                     │
│     - type: "supply"                                            │
│     - organization: { name: "Pixology", domain: "pixology.ai" } │
│     - capabilities: { formats, athletes, turnaround, capacity } │
│     - callback_url: "https://pixology.ai/aax/webhook"           │
│                                                                  │
│  2. AAX verifies domain, issues API key                         │
│                                                                  │
│  3. Response tells agent: "You're registered. Set up standing    │
│     queries if you want to receive demand-side interest signals."│
│                                                                  │
│  Agent is now ACTIVE on the exchange.                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  OPERATING LOOP (continuous)                                     │
│                                                                  │
│  ┌─── Agent's own logic (outside AAX) ───────────────────────┐  │
│  │                                                            │  │
│  │  Monitor sports data APIs, social trending signals,        │  │
│  │  game schedules. When a monetizable moment is detected:    │  │
│  │                                                            │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  POST /opportunities                                             │
│  {                                                               │
│    content: "Career milestone — 1000 points",                   │
│    subjects: [{ athlete: "Jane Doe", school: "MIT" }],          │
│    audience: { projected_reach: 150000 },                       │
│    formats: ["gameday_graphic", "social_post"],                 │
│    expiry: "2026-03-16T00:00:00Z",                              │
│    min_terms: { price: 500 }                                    │
│  }                                                               │
│                                                                  │
│  Response: { opportunity_id, matched_count: 2, expiry }         │
│                                                                  │
│  ┌─── Wait for proposals (via webhook) ──────────────────────┐  │
│  │                                                            │  │
│  │  AAX POSTs to callback_url/proposals:                      │  │
│  │  {                                                         │  │
│  │    proposal_id, deal_terms, demand_agent: { org: "Nike" }, │  │
│  │    valid_actions: ["accept", "counter", "reject"],         │  │
│  │    constraints: { max_rounds: 3, timeout: 600s }           │  │
│  │  }                                                         │  │
│  │                                                            │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                      │
│  ┌─── Agent evaluates (own logic) ───────────────────────────┐  │
│  │                                                            │  │
│  │  LLM reasoning: "Price $800 > my minimum $500.             │  │
│  │  Nike is premium brand. Gameday graphic is feasible.       │  │
│  │  I have capacity. Score: 85/100. ACCEPT."                  │  │
│  │                                                            │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                      │
│  POST /proposals/{id}/respond                                    │
│  { decision: "accept", reasoning: "..." }                       │
│                                                                  │
│  ┌─── Deal agreed → Fulfillment ─────────────────────────────┐  │
│  │                                                            │  │
│  │  AAX POSTs to callback_url/briefs:                         │  │
│  │  { deal_id, creative_brief: { assets, messaging, specs } } │  │
│  │                                                            │  │
│  │  Agent generates content using Pixology APIs (own logic).  │  │
│  │                                                            │  │
│  │  POST /deals/{id}/content                                  │  │
│  │  { content_url, format, metadata }                         │  │
│  │                                                            │  │
│  │  AAX validates content (neutral check).                    │  │
│  │                                                            │  │
│  │  If PASS → deal completed.                                 │  │
│  │  If FAIL → agent receives revision instructions via        │  │
│  │            callback_url/revisions, regenerates, resubmits. │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 Demand Agent Journey (Nike)

```
┌─────────────────────────────────────────────────────────────────┐
│  ONBOARDING (one-time)                                          │
│                                                                  │
│  1. Agent calls POST /agents/register with:                     │
│     - type: "demand"                                            │
│     - organization: { name: "Nike", domain: "nike.com" }        │
│     - brand_profile: { guidelines, budget, exclusions }         │
│     - guardrails: { auto_approve_below: 1000, budget_max: 50k } │
│     - callback_url: "https://nike-agent.example.com/aax"        │
│                                                                  │
│  2. Agent sets standing queries:                                │
│     POST /queries                                                │
│     { sport: "basketball", min_reach: 50000, conferences: [...] }│
│                                                                  │
│  Agent is now ACTIVE and will be notified of matching opps.     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  OPERATING LOOP (event-driven via webhooks)                      │
│                                                                  │
│  ┌─── AAX notifies agent of matching opportunity ────────────┐  │
│  │                                                            │  │
│  │  AAX POSTs to callback_url/opportunities:                  │  │
│  │  {                                                         │  │
│  │    opportunity_id, signal: { ... },                        │  │
│  │    relevance_score: 82,                                    │  │
│  │    supply_agent: { org: "Pixology", reputation: 4.9 },     │  │
│  │    valid_actions: ["propose", "pass"],                     │  │
│  │    constraints: { expiry, proposal_deadline }              │  │
│  │  }                                                         │  │
│  │                                                            │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                      │
│  ┌─── Agent evaluates (own logic) ───────────────────────────┐  │
│  │                                                            │  │
│  │  LLM reasoning: "D1 basketball milestone, 150k reach,     │  │
│  │  18-24 demo matches our target. Strong 'Just Do It'        │  │
│  │  narrative. Budget available. Score: 78/100. BID."          │  │
│  │                                                            │  │
│  │  OR: "Only 22k reach, below my 50k minimum. PASS."         │  │
│  │                                                            │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                      │
│  POST /opportunities/{id}/propose                                │
│  {                                                               │
│    deal_terms: { price: 800, format: "gameday_graphic", ... },  │
│    brand_assets: { logos: [swoosh], messaging: "Just Do It" }   │
│  }                                                               │
│                                                                  │
│  Response: { proposal_id, conflict_status: "cleared" }          │
│  OR: { proposal_id, conflict_status: "blocked",                 │
│         conflict_reason: "MIT exclusive apparel → Nike..." }    │
│                                                                  │
│  ┌─── Handle negotiation (if supply counters) ───────────────┐  │
│  │                                                            │  │
│  │  AAX POSTs to callback_url/counters:                       │  │
│  │  { counter_terms: { usage_rights: 14 days (was 7) },       │  │
│  │    valid_actions: ["accept", "counter", "withdraw"],       │  │
│  │    constraints: { round: 2 of 3, timeout: 300s } }         │  │
│  │                                                            │  │
│  │  Agent re-evaluates and responds.                          │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─── Deal agreed → Content review ──────────────────────────┐  │
│  │                                                            │  │
│  │  AAX POSTs to callback_url/deal-agreed:                    │  │
│  │  { deal_id, final_terms }                                  │  │
│  │                                                            │  │
│  │  Later, AAX POSTs to callback_url/validation-results:      │  │
│  │  { content_preview_url, validation: { passed: true } }     │  │
│  │                                                            │  │
│  │  Agent auto-approves (deal under $1000 threshold).         │  │
│  │  OR routes to human for review.                            │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.3 Managed Agent Journey (Onramp)

For brands without their own agent infrastructure:

```
┌─────────────────────────────────────────────────────────────────┐
│  HUMAN SETUP (via AAX Portal UI)                                │
│                                                                  │
│  1. Brand manager visits AAX portal, creates account            │
│  2. Fills out brand profile form:                               │
│     - Upload brand guidelines (PDF or structured form)          │
│     - Set target demographics                                   │
│     - Define budget ($X/month, $Y/deal max)                    │
│     - List competitive exclusions                               │
│     - Set approval thresholds                                   │
│  3. Configure agent personality:                                 │
│     - Aggressive bidder vs. selective                           │
│     - Risk tolerance                                             │
│     - Preferred content categories                              │
│  4. Click "Launch Agent"                                         │
│                                                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  AAX CREATES INTERNAL AGENT                                      │
│                                                                  │
│  - Registers on the exchange (same API as autonomous agents)    │
│  - Agent runs on AAX infrastructure                             │
│  - Uses LLM reasoning powered by brand profile + guidelines    │
│  - Speaks the same protocol as external agents                   │
│  - Deal engine cannot tell the difference                        │
│                                                                  │
│  Human observes via dashboard (same as any agent owner).        │
│  Human can intervene, pause, adjust guardrails at any time.     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Human User Journeys & UI Flows

### 8.1 Screen Map

```
┌────────────────────────────────────────────────────┐
│                    AAX UI                           │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  Exchange Live View ("Trading Floor")        │   │
│  │  The hero screen. Watch deals flow in real   │   │
│  │  time. Entry point for all users.            │   │
│  └────────┬──────────────────────┬──────────────┘   │
│           │                      │                  │
│     click deal              click agent             │
│           │                      │                  │
│  ┌────────▼──────────┐  ┌───────▼───────────────┐  │
│  │  Deal Deep Dive   │  │  Agent Profile View   │  │
│  │  Full negotiation │  │  Activity, guardrails, │  │
│  │  trace, scores,   │  │  standing queries,     │  │
│  │  conflicts,       │  │  recent decisions      │  │
│  │  content preview  │  │                        │  │
│  └────────┬──────────┘  └───────────────────────┘  │
│           │                                         │
│     click conflict                                  │
│           │                                         │
│  ┌────────▼──────────┐  ┌───────────────────────┐  │
│  │ Conflict Explorer │  │ Managed Agent Setup   │  │
│  │ Interactive graph, │  │ (Onramp portal)       │  │
│  │ query tool        │  │ Brand config form     │  │
│  └───────────────────┘  └───────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 8.2 Exchange Live View ("The Trading Floor")

The hero screen. All users land here. Real-time via SSE.

```
┌─────────────────────────────────────────────────────────────────────┐
│  AAX Exchange                              ● 4 agents online        │
│                                                                     │
│  ┌─ LIVE DEAL FLOW ──────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │  ● Deal #47   Nike ↔ Pixology    NEGOTIATING  ██████░░░  60%  │  │
│  │    "Jane Doe 1000 pts"           Counter-offer round 2/3       │  │
│  │                                                                │  │
│  │  ● Deal #46   Local Biz ↔ Pix    CONTENT GEN  ████████░  80%  │  │
│  │    "MIT wins conference"          Generating graphic...        │  │
│  │                                                                │  │
│  │  ○ Deal #45   Nike ↔ Pixology    COMPLETED    ██████████ 100%  │  │
│  │    "Season opener blowout"        Delivered 12 min ago         │  │
│  │                                                                │  │
│  │  ✕ Deal #44   Gatorade ↔ Pix     BLOCKED      ──────────      │  │
│  │    "Jane Doe 1000 pts"           NIL conflict: BodyArmor      │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ EXCHANGE STATS ──────┐  ┌─ ACTIVE AGENTS ────────────────────┐ │
│  │  Deals today:    12    │  │  ● Pixology    Supply  ↑3 opps    │ │
│  │  Avg deal time:  4.2m  │  │  ● Nike        Demand  2 active   │ │
│  │  Conflict rate:  18%   │  │  ● Gatorade    Demand  1 blocked  │ │
│  │  Match rate:     67%   │  │  ● LocalBiz    Demand  1 active   │ │
│  │  Revenue today:  $4.2k │  │                                    │ │
│  └────────────────────────┘  └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 Deal Deep Dive ("The Audit Trail")

Click any deal. Shows the full negotiation story with side-by-side agent reasoning.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Deal #47: Nike ↔ Pixology — "Jane Doe 1000 career points"        │
│  Status: NEGOTIATING (round 2/3)                Expiry: 1h 42m     │
│                                                                     │
│  ┌─ TIMELINE ────────────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │  9:47:02  ● OPPORTUNITY SIGNALED                              │  │
│  │           Pixology detected via game stats API                 │  │
│  │                                                                │  │
│  │  9:47:03  ● PRE-SCREEN                                        │  │
│  │           ✅ Nike: cleared  ✅ Gatorade: cleared               │  │
│  │           ⛔ Adidas: blocked (MIT exclusive → Nike)            │  │
│  │                                                                │  │
│  │  9:48:11  ● NIKE PROPOSED                             [expand] │  │
│  │           $800 · gameday_graphic · IG+Twitter · 7d rights      │  │
│  │                                                                │  │
│  │  9:48:15  ● FINAL CONFLICT CHECK                              │  │
│  │           Nike + Jane Doe: ✅     Gatorade + Jane Doe: ⛔      │  │
│  │                                                                │  │
│  │  9:49:01  ● PIXOLOGY COUNTERED                        [expand] │  │
│  │           Requesting 14d rights + 48h exclusivity              │  │
│  │                                                                │  │
│  │  9:49:30  ◌ AWAITING NIKE RE-EVALUATION   ⏱ 4:30 remaining    │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ AGENT REASONING (side-by-side) ──────────────────────────────┐  │
│  │                                                                │  │
│  │  Nike's Evaluation            Pixology's Evaluation            │  │
│  │                                                                │  │
│  │  Audience fit:     9/10       Price adequacy:     8/10         │  │
│  │  Brand narrative:  8/10       Brand alignment:    9/10         │  │
│  │  Projected ROI:    7/10       Content feasibility:9/10         │  │
│  │  Competitive pos.: 8/10       Timeline:           8/10         │  │
│  │  ──────────────────────       ──────────────────────           │  │
│  │  Overall:         78/100      Overall:           85/100        │  │
│  │                                                                │  │
│  │  "D1 basketball milestone,    "Nike is premium brand,          │  │
│  │   150k reach, strong           price above minimum.             │  │
│  │   narrative angle..."          Requesting longer rights..."     │  │
│  │                                                                │  │
│  │  [View full LLM trace →]     [View full LLM trace →]          │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ DEAL TERMS (current vs. original) ───────────────────────────┐  │
│  │  Price:       $800 (unchanged)                                 │  │
│  │  Rights:      7d → 14d (Pixology countered ↑)                 │  │
│  │  Exclusivity: 24h → 48h (Pixology countered ↑)                │  │
│  │  Format:      gameday_graphic (unchanged)                      │  │
│  │  Platforms:   IG, Twitter (unchanged)                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  [⏸ Pause Deal]  [✋ Override Decision]  [🔍 Conflict Details]     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.4 Agent Profile View

What an agent's owner sees. Activity log, guardrails, standing queries.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Agent: Nike Demand Agent                        ● Online           │
│  Organization: Nike, Inc. (verified)                                │
│                                                                     │
│  ┌─ ACTIVITY ────────────────────────────────────────────────────┐  │
│  │  Today        This Week     All Time                          │  │
│  │  Opps received:    8          34           142                │  │
│  │  Bids submitted:   3          12            58                │  │
│  │  Deals closed:     1           5            23                │  │
│  │  Conflicts:        0           2             7                │  │
│  │  Spent:         $800       $4.2k         $18.6k of $50k      │  │
│  │               ━━━━━━━━━━━━━━━━━━━━░░░░░░░░░░ 37%             │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ GUARDRAILS ──────────────────────────────────────────────────┐  │
│  │  Auto-approve:     deals under $1,000               [edit]    │  │
│  │  Human review:     deals $1,000+                    [edit]    │  │
│  │  Budget ceiling:   $50,000 / month                  [edit]    │  │
│  │  Per-deal max:     $5,000                           [edit]    │  │
│  │  Exclusions:       Adidas, Under Armour             [edit]    │  │
│  │                                                               │  │
│  │  [⏸ Pause Agent]                                             │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ RECENT DECISIONS ────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │  12m ago  PASSED on "Conference semifinal highlight"           │  │
│  │           "Projected reach 22k below my 50k minimum." 34/100  │  │
│  │                                                                │  │
│  │  28m ago  BID on "Jane Doe 1000 career points"                │  │
│  │           "Strong milestone narrative, 150k reach." 78/100    │  │
│  │           Bid: $800 [View deal →]                             │  │
│  │                                                                │  │
│  │  1h ago   CLOSED "Season opener blowout" · $1,200             │  │
│  │           Auto-approved · [View deal →]                       │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ STANDING QUERIES ────────────────────────────────────────────┐  │
│  │  1. D1 Basketball · reach > 50k · any conference    [active]  │  │
│  │  2. Football · SEC or Big Ten · reach > 100k        [active]  │  │
│  │  3. Any sport · milestone moment · reach > 200k     [active]  │  │
│  │                                                     [+ add]   │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.5 Conflict Explorer

Interactive conflict graph visualization with a query tool.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Conflict Explorer                                                  │
│                                                                     │
│  ┌─ GRAPH VIEW ──────────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │         ┌──────┐                                               │  │
│  │    ┌────│ MIT  │────┐                                          │  │
│  │    │    └──────┘    │                                          │  │
│  │ exclusive       has_athlete                                    │  │
│  │ _apparel            │                                          │  │
│  │    │           ┌────┴────┐                                     │  │
│  │ ┌──┴───┐       │Jane Doe │                                     │  │
│  │ │ Nike │       └────┬────┘                                     │  │
│  │ └──┬───┘        nil_deal                                       │  │
│  │ competes_          │                                           │  │
│  │ with          ┌────┴─────┐   competes_   ┌──────────┐          │  │
│  │    │          │BodyArmor │───with────────│ Gatorade │          │  │
│  │ ┌──┴────┐    └──────────┘                └──────────┘          │  │
│  │ │Adidas │                                                      │  │
│  │ └───────┘                                                      │  │
│  │                                                                │  │
│  │  (nodes are clickable — highlights all connected constraints)  │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─ QUERY TOOL ──────────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │  Can  [Gatorade ▼]  sponsor content featuring                 │  │
│  │       [Jane Doe ▼]  at  [MIT ▼] ?                             │  │
│  │                                                                │  │
│  │  Result: ⛔ BLOCKED                                           │  │
│  │  Chain: Gatorade ─competes_with─► BodyArmor ◄─nil_deal─ Jane  │  │
│  │  "Jane Doe has active NIL endorsement with BodyArmor           │  │
│  │   (sports drink category, expires Dec 2026). BodyArmor and     │  │
│  │   Gatorade are registered competitors."                        │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.6 Content Validation View

Post-deal content review with side-by-side generated content and validation results.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Content Validation — Deal #47                                      │
│                                                                     │
│  ┌─ GENERATED CONTENT ───────┐  ┌─ VALIDATION RESULTS ──────────┐  │
│  │                            │  │                                │  │
│  │  ┌──────────────────────┐  │  │  ✅ Logo present (top-right)  │  │
│  │  │                      │  │  │  ✅ Color palette matches     │  │
│  │  │   [Generated image   │  │  │  ✅ Messaging correct         │  │
│  │  │    from Pixology     │  │  │  ✅ FTC disclosure present    │  │
│  │  │    displayed here]   │  │  │  ⚠️ Swoosh size: 42px < 60px │  │
│  │  │                      │  │  │     → REVISION REQUESTED      │  │
│  │  └──────────────────────┘  │  │                                │  │
│  │                            │  │  Overall: FAIL (1 issue)       │  │
│  │  Format: 1080x1080         │  │  Attempt: 1 of 3              │  │
│  └────────────────────────────┘  └────────────────────────────────┘  │
│                                                                     │
│  ┌─ REVISION INSTRUCTIONS (sent to supply agent) ────────────────┐  │
│  │  "Nike swoosh is 42px, below 60px minimum per brand           │  │
│  │   guidelines. Regenerate with swoosh at minimum 60px width.   │  │
│  │   All other elements pass."                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Demo Script (Class Presentation)

### Setup (30 seconds)
Show the Exchange Live View. Four agents are online.

*"This is AAX — an open exchange where autonomous AI agents trade branded content deals. On the left, Pixology's supply agent — it's running on separate infrastructure, monitoring college basketball via game APIs. On the right, three autonomous brand agents — Nike, Gatorade, and a local pizza shop. Each has its own objectives, budget, and brand guidelines. None of them are being controlled by a human right now."*

### Trigger the Moment (10 seconds)
Click "Simulate Moment" button (or CLI command).

*"A moment just happened — MIT's Jane Doe scored her 1000th career point. Pixology's agent detected it from the game stats API and listed an opportunity on the exchange."*

### Watch It Unfold (2-3 minutes, fully autonomous)
Dashboard updates in real time via SSE:

1. Opportunity appears in live feed
2. Pre-screen results flash — Adidas silently blocked (MIT has Nike exclusive)
3. Nike and Gatorade start evaluating (reasoning populates in real time)
4. Both submit proposals
5. Final conflict check — Gatorade blocked (BodyArmor NIL conflict)
6. Nike's proposal reaches Pixology
7. Pixology counters on usage rights duration
8. Nike re-evaluates, accepts
9. Deal agreed

*"No human touched anything. Two autonomous agents just negotiated a sponsorship deal in under 3 minutes — complete with conflict checking that caught an athlete-level NIL conflict that a human might have missed."*

### Show the Trust Layer (1 minute)
Click into Deal #47 detail view.

*"Every decision is traceable. Here's Nike's reasoning — audience fit 9/10, brand narrative 8/10. Here's Pixology's counter — they wanted longer usage rights given the athlete's visibility. Here's why Gatorade was blocked — the full conflict chain from Gatorade through BodyArmor to Jane Doe's NIL deal."*

Click into Conflict Explorer.

*"The exchange maintains this constraint graph. It automatically caught that Gatorade can't sponsor content featuring Jane Doe because of her BodyArmor endorsement — a conflict that would take a human lawyer hours to verify."*

### Show Real Content (1 minute)
Show the fulfillment pipeline and content validation view.

*"Now Pixology's agent generated actual branded content using its real APIs. The exchange independently validated it against Nike's brand guidelines using a vision model. It caught that the swoosh was too small, sent revision instructions, and Pixology's agent fixed it automatically. The final content passed all checks and was auto-approved because the deal was under Nike's $1,000 threshold."*

### The Onramp (30 seconds)
Briefly show the managed agent setup screen.

*"What about brands that don't have their own agent? They can configure one through our portal — upload brand guidelines, set budget and exclusions, and AAX runs an agent on their behalf. Same exchange, same protocol. The deal engine can't tell the difference."*

### Close (15 seconds)
*"Moltbook proved agents can socialize. We proved they can do business — with real money, real conflicts, and a full audit trail. Every deal on this exchange happened autonomously, but every decision is observable and auditable. That's the future of agent commerce."*

---

## 10. Phased Milestones

### Phase 1: Protocol + Autonomous Deal Flow (Weeks 1-3)
**Goal**: Two autonomous agents (one supply, one demand) negotiate and close a deal through the AAX protocol — with a live dashboard showing it happen.

**Deliverables**:
- AAX Protocol: message schemas (JSON Schema for all message types), agent interface definitions
- Deal-Making State Machine in LangGraph (full lifecycle, single deal)
- Agent Registry with self-registration API
- Conflict Engine v1: static conflict data, pre-screen + final check, structured explanations
- Pixology Supply Agent: self-hosted, connects via API, signals opportunities, responds to proposals
- Nike Demand Agent: autonomous, LLM-powered, evaluates and bids based on brand persona
- Minimal Streamlit dashboard: live deal state, negotiation transcript, scores
- All state transitions and agent reasoning logged

**Demo**: Trigger a simulated moment → watch two autonomous agents negotiate and close a deal in real time → see the full audit trail.

**Key decisions to lock**: Message schema format, DealTerms schema, state names, agent interface contracts.

### Phase 2: Multi-Agent Competition + Fulfillment (Weeks 4-5)
**Goal**: Multiple demand agents compete for opportunities. Content is generated and validated.

**Deliverables**:
- 2 additional demand agents (Gatorade, Local Business) with distinct personas and strategies
- Parallel bidding: multiple demand agents evaluate and bid on the same opportunity
- Competitive conflict demonstration: one agent gets blocked, another wins
- Fulfillment pipeline: brief generation → content creation (Pixology) → validation (vision model) → delivery
- Counter-offer support (1-2 rounds)
- Deal expiry / timeout handling
- Matching engine with relevance pre-scoring

### Phase 3: Trust Infrastructure + Content Validation (Weeks 6-7)
**Goal**: Enterprise-grade trust — guardrails, validation, human intervention.

**Deliverables**:
- Content Validation Engine with multimodal LLM review
- Revision loop (fail → revision instructions → regenerate → re-validate)
- Human approval flow: configurable thresholds, notification hooks
- Guardrail enforcement: budget ceilings enforced at platform level
- Agent authorization scopes
- Managed Agent Service v1: configure a brand profile → AAX runs an agent (the onramp story)
- Marketplace integrity basics: rate limiting, data isolation between agents

### Phase 4: Observability Dashboard + Final Demo (Weeks 8-9)
**Goal**: Polished demo showing the full autonomous exchange in action.

**Deliverables**:
- Full web dashboard (Next.js): deal flow visualization, agent status, negotiation drill-down
- Deal trace view: every message, score, conflict, content validation — fully interactive
- Agent reasoning transparency: LangSmith integration showing LLM thought process
- Market overview: active agents, deal volume, conflict rate, average deal time
- End-to-end demo scenario with real Pixology content generation
- Second supply agent (even a simple mock) to prove the exchange is multi-supply
- Presentation-ready walkthrough

### Phase 5 (Stretch): Market Intelligence
**Goal**: The exchange gets smarter over time.

**Deliverables**:
- Market data service: anonymized pricing trends, demand heatmaps, deal velocity
- Agent reputation scores based on deal completion and content quality
- Dynamic pricing signals from historical deal data
- A2A compatibility layer: publish AAX Agent Card for external agent discovery

---

## 8. Competitive Landscape

AAX doesn't compete with Moltbook. It competes with the existing (broken) infrastructure for creator-brand deals:

| | **OpenRTB / Programmatic** | **Influencer Platforms** | **NIL Agencies** | **AAX** |
|---|---|---|---|---|
| Speed | Real-time (display ads) | Days to weeks | Days to weeks | Minutes |
| What's traded | Pre-planned display inventory | Planned brand integrations | Planned endorsements | Moment-native content |
| Intelligence | Price-only auction | Human negotiation | Human negotiation | Multi-dimensional agent negotiation |
| Conflict handling | None (no brand deals) | Manual | Manual | Automated, graph-based |
| Creator economics | Platform takes 55-70% | Agency takes 20-40% | Agency takes 15-30% | Direct agent-to-agent |
| Moment capture | No (pre-planned only) | No (too slow) | No (too slow) | Yes (purpose-built) |
| Auditability | Bid logs only | Email chains | Contracts | Full agent reasoning traces |

AAX doesn't optimize existing ad buying. It creates a **new category** — the Moment Market — that was impossible before generative AI and autonomous agents existed together.
