---
title: "Agentic Ad Exchange: Infrastructure for Real-Time, Agent-Mediated Advertising in the Moment Economy"
author: "Raghavendra Polanki"
affiliation: "Massachusetts Institute of Technology"
email: "rpolanki@mit.edu"
date: "April 2026"
---

# Agentic Ad Exchange: Infrastructure for Real-Time, Agent-Mediated Advertising in the Moment Economy

**Raghavendra Polanki** | Massachusetts Institute of Technology | rpolanki@mit.edu

## Abstract

The digital advertising ecosystem is architected around planned content and pre-negotiated brand deals --- a paradigm fundamentally misaligned with the real-time nature of cultural attention. Viral moments in sports, entertainment, and media generate concentrated audience attention with half-lives measured in hours, yet the infrastructure to monetize these moments through branded content does not exist. The convergence of generative AI (which collapses content production from days to minutes) and autonomous AI agents (which can evaluate and close deals in seconds) creates the preconditions for a new advertising category: **moment-native, creator-owned, agent-mediated brand placements**. This paper introduces the Agentic Ad Exchange (AAX), an infrastructure platform comprising a multi-dimensional deal evaluation protocol, a stateful deal lifecycle engine, and a conflict resolution system that enables supply-side agents (representing content creators and publishers) and demand-side agents (representing brands and sponsors) to autonomously discover, evaluate, and transact advertising opportunities in real time. We present AAX's architecture, define the deal lifecycle state machine, and describe a proof-of-concept implementation in the college sports and NIL (Name, Image, Likeness) market --- a domain characterized by high moment density, complex contractual conflicts, and perishable inventory. We argue that AAX represents not an optimization of existing programmatic advertising, but the enabling infrastructure for a net-new market category we term the **Moment Market**.

## 1. Introduction

Digital advertising today operates on two models, both structurally slow. In **platform-mediated overlay advertising** (e.g., YouTube pre-rolls, Instagram feed ads), platforms insert ads around creator content and capture the majority of revenue; creators receive a fraction despite generating the underlying attention. In **direct sponsorship**, creators negotiate brand deals manually --- a process involving weeks of outreach, contract negotiation, and production planning. Neither model can monetize a viral moment in real time.

Consider a concrete scenario: a buzzer-beater in the NCAA March Madness tournament generates millions of social impressions within minutes. A university athletic department could produce branded content featuring the athlete and the moment --- but by the time a brand deal is negotiated through traditional channels, the moment's attention window has closed. This pattern repeats across hundreds of thousands of athletic events annually, representing a significant untapped market.

Three concurrent technological shifts now make real-time moment monetization feasible:

1. **Generative AI** has reduced content production cycles from days to minutes, eliminating the creation bottleneck that historically prevented moment-speed branded content.
2. **Agent-to-agent communication protocols** (Google A2A, Anthropic MCP, AdCP) have established primitives for structured, autonomous inter-agent transactions.
3. **Market fragmentation in NIL** has created a \$1.17B+ annual market with high transaction volume, extreme time sensitivity, and virtually no technological infrastructure --- an ideal environment for agent-mediated automation.

What remains missing is the **domain-specific exchange infrastructure**: a protocol and engine purpose-built for autonomous agents to discover, evaluate, and clear advertising deals across multiple dimensions in real time. AAX addresses this gap.

## 2. System Architecture

AAX is structured as a two-sided exchange platform with four core infrastructure components operating over a unified protocol layer.

### 2.1 AAX Protocol

The AAX Protocol defines the message schemas, state transitions, and evaluation formats governing all agent interactions on the exchange. A deal progresses through a deterministic lifecycle:

**Discovery** $\rightarrow$ **Proposal** $\rightarrow$ **Evaluation** $\rightarrow$ **Conflict Check** $\rightarrow$ **Counter/Adjust** $\rightarrow$ **Resolution** $\rightarrow$ **Audit**

Each transition is governed by typed message schemas. The protocol enforces timeout and expiry semantics critical for perishable inventory --- a deal that is not resolved within the moment's attention window is automatically expired. All state transitions and agent decisions are logged to produce a complete audit trail.

### 2.2 Deal Lifecycle Engine

The Deal Lifecycle Engine provides stateful orchestration for multi-turn agent interactions. Unlike linear LLM chains, advertising deal evaluation requires cyclical reasoning: an agent may propose, receive a counter-offer, re-evaluate against updated constraints, and adjust --- potentially over multiple rounds. The engine maintains full conversational context across these cycles, ensuring agents do not lose state or hallucinate prior constraints.

The engine is implemented as a graph-based state machine where nodes represent deal states and edges represent valid transitions. This architecture draws on evaluation of frameworks such as LangGraph for cyclical state management, while extending them with advertising-domain-specific semantics (inventory expiry, conflict gates, multi-dimensional scoring).

### 2.3 Multi-Dimensional Evaluation

Unlike traditional programmatic advertising, which optimizes primarily on price (CPM-based auctions), AAX deal evaluation operates across multiple orthogonal dimensions. Supply-side agents evaluate: brand alignment with institutional values, contractual conflicts (existing sponsor exclusivity, athlete NIL agreements), content integrity (whether brand requirements degrade content quality), and minimum compensation thresholds. Demand-side agents evaluate: audience demographic fit, projected reach and viral probability, brand narrative relevance, portfolio diversification, and estimated ROI.

Each agent maintains a configurable scoring function over these dimensions with weighted priorities reflecting its principal's objectives. The platform does not impose a single ranking --- it facilitates multi-dimensional fit-finding where both sides must independently score above their acceptance thresholds.

### 2.4 Conflict and Compliance Engine

The Conflict and Compliance Engine is AAX's critical differentiator. It maintains a structured knowledge base of contractual and regulatory constraints:

- **Institutional sponsor exclusivity**: e.g., a university's exclusive apparel deal with Nike triggers an automatic conflict flag on any Adidas-sponsored bid.
- **Athlete NIL registries**: e.g., an athlete's personal endorsement deal with Beats blocks competing audio brand placements.
- **Regulatory constraints**: NCAA eligibility rules, FTC disclosure requirements for sponsored content.
- **Brand-to-brand competitive exclusions**: e.g., Coca-Cola and Pepsi cannot co-sponsor the same content asset.

The engine evaluates every proposed deal against this constraint graph before clearing, ensuring that autonomously closed deals do not violate existing agreements or regulations.

### 2.5 Agent Registry and Identity

Every participant agent on AAX maintains a verifiable identity record specifying its principal, authorization scope, supported content types, audience profile, and contractual declarations. The registry enables programmatic discovery --- a demand-side agent can query for supply agents matching specific audience demographics, content categories, or geographic regions. Identity design draws on decentralized registry standards (JSON-LD Agent Facts, List39) to ensure interoperability across heterogeneous agent frameworks.

## 3. The Moment Market: A New Advertising Category

We introduce the term **Moment Market** to describe the advertising category AAX enables. The Moment Market is defined by four properties that distinguish it from traditional programmatic advertising:

1. **Perishable inventory**: The advertising asset (a viral moment's attention) decays rapidly. Deals must clear in minutes, not days.
2. **Creator-native placement**: The brand is integrated *into* the content by the creator, not overlaid by a platform. The creator retains ownership and a proportionally larger share of revenue.
3. **Multi-dimensional matching**: Deal quality depends on brand-creator fit across many axes (values, audience, conflicts, timing), not just price.
4. **Agent-mediated execution**: The speed requirement necessitates autonomous AI agents making evaluation and transaction decisions without human-in-the-loop approval for each deal.

The scale of untapped opportunity is significant. In Division I college sports alone, approximately 500 institutions across 30 sports generate roughly 450,000 competitive events per season. Each event produces multiple potential viral moments. Today, near-zero percent of these moments are monetized through real-time branded content. Even modest capture rates represent substantial market creation --- not displacement of existing ad spend, but net-new inventory.

## 4. Proof of Concept: College Sports and NIL

We select the college sports and NIL market as our proof-of-concept domain for three reasons: (1) high moment density --- games produce predictable windows of unpredictable viral events; (2) rich conflict structure --- institutional sponsors, athlete NIL deals, conference agreements, and NCAA compliance create a genuinely complex constraint graph; and (3) infrastructure vacuum --- the current market operates through manual outreach with no technological matching layer.

The proof-of-concept implementation demonstrates the end-to-end deal lifecycle: a supply-side agent representing a university athletic department signals available inventory following a simulated viral moment; multiple demand-side agents (representing brands with distinct objectives and constraints) evaluate the opportunity across their scoring dimensions; the Conflict and Compliance Engine checks against declared institutional and athlete contracts; and the Deal Lifecycle Engine orchestrates the multi-turn interaction to resolution. An observability dashboard renders the full decision trace --- agent reasoning, scoring breakdowns, conflict flags, and state transitions --- providing transparency into autonomous agent behavior.

## 5. Related Work

Existing programmatic advertising infrastructure (OpenRTB, Google Ad Exchange) optimizes for price-based auction clearing of pre-planned display inventory and lacks support for multi-dimensional evaluation, real-time content creation, or agent-mediated deal-making. Multi-agent orchestration frameworks (LangGraph, Microsoft AutoGen, CrewAI) provide general-purpose state management and agent coordination primitives but no advertising domain logic. Decentralized identity registries (List39/Join39, NANDA Project) address agent discovery and verification but not deal evaluation or conflict resolution. AAX is positioned at the intersection of these capabilities --- applying agent orchestration and identity infrastructure to a domain-specific exchange protocol for real-time advertising.

## 6. Conclusion and Future Work

AAX demonstrates that the infrastructure for real-time, agent-mediated advertising is both technically feasible and architecturally distinct from existing ad-tech. The combination of generative AI and autonomous agents does not merely accelerate existing processes --- it enables a structurally new market category where perishable attention moments can be monetized through creator-native branded content at cultural speed.

Future phases of development include multi-agent competitive dynamics (multiple demand agents bidding on the same inventory), agent reputation systems based on historical deal performance, dynamic pricing signals derived from market activity, open protocol standardization for cross-platform interoperability, and financial settlement infrastructure. The long-term vision is an open exchange protocol where any supply or demand platform can plug in agents that autonomously participate in the Moment Market.
