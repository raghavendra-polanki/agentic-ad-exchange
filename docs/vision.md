# Agentic Ad Exchange (AAX)
## Vision Document

### The Problem

Think about how ads work on a YouTube video. The creator makes the video. YouTube slaps an ad on it. YouTube keeps most of the money. The creator — whose content attracted the audience in the first place — gets a small cut.

Why? Because the only other option for creators is **pre-planned brand deals**: spend weeks emailing sponsors, negotiating terms, signing contracts, and then baking the brand into the content during production. It works, but it's slow, manual, and only possible if you plan ahead.

Now think about what happens when something goes viral. A buzzer-beater in March Madness. A rookie's first triple-double. A controversial call that takes over social media. Millions of eyeballs, intensely focused, for a few hours.

**Nobody makes money from that moment.**

Not the creator, not the brand, nobody — because by the time a human could produce branded content, find the right sponsor, check for conflicts, and close a deal, the moment is gone. The attention has moved on.

This is the **Moment Market** — and it's completely broken. Not because brands don't want to pay (they do), and not because creators can't produce (with generative AI, they now can in minutes). It's broken because there is **no infrastructure to connect the right brand with the right creator at the speed a moment demands.**

That's what AAX solves.

---

### The Vision

**AAX is the stock exchange for attention moments — where AI agents trade advertising opportunities in real time.**

Just like a stock exchange matches buyers and sellers of shares in milliseconds using structured rules, AAX matches **creators who can produce content** with **brands who want to sponsor it** — autonomously, in minutes, with all the messy real-world checks (brand conflicts, athlete contracts, audience fit, compliance) handled by agents, not humans.

Two sides, each powered by AI agents:

- **Supply side**: A university athletic department's agent detects a trending moment (star player hits a milestone). It signals: *"I can produce branded content featuring this athlete, for this audience, within the next hour."*

- **Demand side**: A sports nutrition brand's agent is always listening. It sees the signal, checks: *Does this athlete's audience match mine? Any conflicts with my competitors? Does this fit my brand? Is the price right?* — and bids.

- **AAX in the middle**: The platform runs the deal through conflict checks (Does the university have an exclusive deal with a competing brand? Does the athlete have a personal NIL deal that blocks this?), ensures compliance, and either clears the deal or flags the issue. All in minutes. All auditable.

**A concrete example:**

> 9:47 PM — Buzzer-beater in March Madness. The clip goes viral.
> 9:48 PM — The university's supply agent signals available inventory.
> 9:49 PM — Three brand agents evaluate the opportunity.
> 9:50 PM — Deal closed, conflicts cleared, content generation begins.
> 9:55 PM — Branded content is live while the moment is still trending.

Today this takes weeks — if it happens at all. AAX makes it happen in minutes. It doesn't optimize existing advertising. It creates a **new category** of advertising that was impossible before generative AI and autonomous agents existed together.

---

### Market Context

**Why now? Three converging shifts.**

1. **Generative AI has collapsed content creation time.** What took a design team days — a branded gameday poster, a highlight reel with sponsor integration, a social-first reaction graphic — can now be produced in minutes. The production bottleneck that made moment marketing impossible is dissolving. But faster creation without faster deal-making just means faster content sitting unbrandished.

2. **Agent-to-Agent protocols are emerging.** Google's A2A, Anthropic's MCP, and advertising-specific protocols like AdCP are establishing standards for how AI agents communicate and transact. The primitives for autonomous agent commerce are being laid — but no one has built the domain-specific exchange infrastructure for advertising on top of them.

3. **NIL has created a massive, infrastructure-less market.** Since 2021, college athletes can monetize their name, image, and likeness — creating a $1.17B+ annual market with virtually no technology infrastructure. Deals happen via DMs, emails, and middlemen. Response times are measured in days. This is perhaps the single market most ready for agent-driven automation: high volume, high fragmentation, extreme time sensitivity, and zero incumbent technology.

**The Moment Market opportunity is enormous.**

Consider just college sports: ~500 Division I schools, ~30 sports each, ~30 games per sport per season. That's ~450,000 athletic events per year — each one generating dozens of potential viral moments. Today, essentially 0% of these moments are monetized in real-time through creator-native branded content. Even capturing a small fraction represents a multi-billion dollar market expansion — not taking share from existing ad spend, but creating **net new** advertising inventory that couldn't exist before.

And sports is just the starting vertical. The same infrastructure applies to entertainment (award shows, premieres, celebrity moments), gaming (esports highlights, streamer moments), news (breaking events with brand-safe angles), and any domain where attention spikes are sudden, concentrated, and fleeting.

**Why sports and university athletics as the starting vertical?**

- **Highest moment density**: Games produce predictable windows of unpredictable viral moments — the perfect environment for just-in-time advertising
- **Clear two-sided market**: Athletic departments and sports media (supply) and brands (demand) with established but painfully slow relationships
- **Rich conflict dimensions**: Institutional sponsors, athlete NIL deals, conference rules, NCAA compliance — these make the matching problem genuinely hard and valuable to solve
- **Perishable inventory**: A buzzer-beater highlight is worth 100x more for branding in the first hour than the next day — urgency forces the need for agent-speed deal-making
- **Underserved by technology**: Most NIL deals still happen through agencies, group chats, and spreadsheets — massive room for infrastructure improvement

---

### Platform Architecture (Conceptual)

```
┌─────────────────────────────────────────────────────────────┐
│                     AAX PLATFORM                            │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Agent       │    │   Deal       │    │  Conflict &  │  │
│  │   Registry &  │    │   Lifecycle  │    │  Compliance  │  │
│  │   Identity    │    │   Engine     │    │  Engine      │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                    │          │
│  ┌──────┴───────────────────┴────────────────────┴───────┐  │
│  │              AAX Protocol Layer                        │  │
│  │     (Discovery → Evaluation → Resolution → Audit)     │  │
│  └──────┬────────────────────────────────────────┬───────┘  │
│         │                                        │          │
│  ┌──────┴───────┐                        ┌───────┴──────┐  │
│  │  Supply-Side │                        │ Demand-Side  │  │
│  │  Agent SDK   │                        │ Agent SDK    │  │
│  └──────┬───────┘                        └───────┬──────┘  │
└─────────┼────────────────────────────────────────┼──────────┘
          │                                        │
   ┌──────┴───────┐                        ┌───────┴──────┐
   │  Supply      │                        │  Demand      │
   │  Agents      │                        │  Agents      │
   │              │                        │              │
   │ • Athletic   │                        │ • Nike       │
   │   Dept Agent │                        │   Brand Agent│
   │ • Influencer │                        │ • Gatorade   │
   │   Mgmt Agent │                        │   Brand Agent│
   │ • Media Co   │                        │ • Local Biz  │
   │   Agent      │                        │   Agent      │
   └──────────────┘                        └──────────────┘
```

### Core Platform Components

**1. Agent Registry & Identity**
Every agent on AAX has a verifiable identity — who it represents, what it's authorized to do, what inventory or budget it controls. Built on structured metadata (inspired by JSON-LD Agent Facts), the registry enables programmatic discovery: a brand agent can query "find me all supply agents with college basketball content targeting 18-24 demographic in the Southeast conference."

**2. Deal Lifecycle Engine**
The stateful orchestration core. Manages every deal through its lifecycle:
- **Discovery**: Demand agent queries supply inventory (or supply agent broadcasts availability)
- **Proposal**: One side initiates with structured terms
- **Evaluation**: Both sides independently score the deal across their dimensions
- **Conflict Check**: Platform surfaces institutional, contractual, and compliance conflicts
- **Counter / Adjust**: Agents modify terms to resolve scoring gaps
- **Resolution**: Deal is accepted, rejected, or expires
- **Audit Trail**: Every decision, score, and state transition is logged

**3. Conflict & Compliance Engine**
The unique infrastructure differentiator. Maintains a knowledge graph of:
- Institutional sponsor exclusivity agreements (e.g., university has Adidas deal → Nike bids are flagged)
- Athlete NIL deal registries (e.g., athlete has personal Beats deal → competing audio brand is blocked)
- Regulatory constraints (NCAA rules, FTC disclosure requirements)
- Brand-to-brand competitive conflicts (e.g., Coca-Cola and Pepsi cannot co-sponsor)

**4. AAX Protocol**
The standardized message format and state machine definition for agent-to-agent interactions on the exchange. Defines:
- Message schemas for proposals, evaluations, counters, and resolutions
- State transition rules (what moves are valid from each state)
- Timeout and expiry semantics (critical for time-sensitive inventory)
- Scoring report format (so both sides can see why a deal succeeded or failed)

**5. Supply-Side & Demand-Side Agent SDKs**
Libraries that make it easy to build agents that participate in the exchange. Provide:
- Protocol message handling
- Scoring function templates (plug in your own weights and logic)
- Conflict declaration interfaces
- Connection to the registry and lifecycle engine

---

### Phased Roadmap

#### Phase 1: The Protocol & Proof of Concept (Class Project Scope)

**Goal**: Build and demonstrate the core deal lifecycle — from discovery through resolution — with functional supply and demand agents operating on the AAX protocol.

**Deliverables**:
- AAX Protocol specification (message schemas, state machine, scoring format)
- Deal Lifecycle Engine with stateful multi-turn agent interactions
- Conflict detection engine (institutional sponsors, athlete NIL conflicts)
- 2-3 supply-side agents (university athletic department scenarios)
- 2-3 demand-side agents (brand agents with different objectives and constraints)
- Observability dashboard showing deal traces, agent reasoning, scoring breakdowns, and conflict flags
- End-to-end demo: a gameday content opportunity flows through discovery → evaluation → conflict check → resolution

**Out of scope**: Payment/settlement, real integrations, production deployment, real content generation.

**Success criteria**: Demonstrate that autonomous agents can discover, evaluate, and resolve a sponsorship deal across multiple dimensions — and that the platform correctly surfaces conflicts and produces an auditable decision trace.

---

#### Phase 2: Multi-Agent Dynamics & Market Intelligence

**Goal**: Move from 1:1 deal matching to a true marketplace with competing bids, portfolio optimization, and market-level insights.

**Deliverables**:
- Multi-bid scenarios: multiple demand agents competing for the same supply inventory
- Supply-side portfolio optimization: agents that strategically time and price their listings based on market conditions
- Demand-side budget allocation: agents that spread budget across opportunities to maximize total campaign ROI
- Market analytics layer: aggregate insights on deal velocity, average clearing scores, most contested inventory types
- Reputation system: agents build track records based on deal completion rates, content performance vs. projections
- Dynamic pricing signals: the platform provides market-rate guidance based on historical deal data

---

#### Phase 3: Protocol Standardization & Ecosystem

**Goal**: Make AAX an open protocol that any supply or demand platform can plug into.

**Deliverables**:
- Open protocol specification (versioned, with backward compatibility)
- Third-party agent certification program (agents must meet minimum standards for identity, compliance, and behavior)
- Federated registry: multiple identity providers can register agents (not just AAX-hosted)
- Cross-platform interoperability: agents built on different frameworks (LangGraph, AutoGen, CrewAI) can participate
- Integration adapters for existing ad-tech (connect to DSPs, SSPs, and CMS platforms)

---

#### Phase 4: Full Autonomous Marketplace

**Goal**: Production-grade exchange with financial settlement, legal contract generation, and real-time content marketplace.

**Deliverables**:
- Escrow and settlement infrastructure (automated payment on deal completion)
- Smart contract or programmatic agreement generation
- Real-time content marketplace (live inventory with sub-minute deal clearing)
- Regulatory compliance automation (auto-generate FTC disclosures, NCAA compliance filings)
- Enterprise features: team-based agent management, approval workflows, budget controls
- Expansion beyond sports: entertainment, gaming, lifestyle content verticals

---

### Why This Matters

The advertising industry isn't just being optimized by AI — it's being **structurally expanded**. Generative AI and autonomous agents together unlock a category of advertising that was physically impossible before: real-time, moment-native, creator-owned branded content at the speed of cultural relevance.

This isn't about making existing ad buying 10% more efficient. It's about the **market expansion** that happens when:

- Content that took days to create now takes minutes
- Deals that took weeks to close now take seconds
- Moments that expired before anyone could monetize them now become premium inventory
- Creators who were locked out of ad economics can now own their monetization

No existing infrastructure enables this. OpenRTB was built for pre-planned display auctions — it has no concept of moment-driven inventory or multi-dimensional creator-brand fit. Agent frameworks like LangGraph provide orchestration primitives but no advertising domain logic. Identity registries like List39 solve discovery but not deal evaluation or conflict resolution.

**AAX sits in the gap — purpose-built infrastructure for the Moment Market, where AI agents unlock advertising opportunities that humans simply couldn't capture at the required speed.**

The billions left on the table today aren't there because of a lack of demand or supply. They're there because the infrastructure to connect them at moment-speed doesn't exist yet.

AAX is that infrastructure.
