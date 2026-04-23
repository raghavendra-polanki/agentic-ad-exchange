"""Deal orchestrator — thin bridge between API routes and LangGraph engine.

The API routes call these functions instead of reimplementing deal logic inline.
Each function uses the real conflict engine and store, then publishes SSE events.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from src.api.stream import sse_bus
from src.conflict import conflict_checker
from src.engine.timeout import timeout_manager
from src.engine.webhook import deliver_webhook
from src.schemas.agents import DemandAgentProfile, SupplyAgentProfile
from src.schemas.deals import DealAgreement, DealState, DealSummary
from src.schemas.opportunities import OpportunitySignal
from src.schemas.proposals import (
    EvaluationDecision,
    Proposal,
    ProposalResponse,
    ProposalStatus,
)
from src.store import store

logger = logging.getLogger("aax.orchestrator")
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

# Default timeout for deals (seconds). 120s for demo pacing.
DEFAULT_DEAL_TIMEOUT = 300  # 5 minutes — allows time for Gemini reasoning


def _on_deal_expired(deal_id: str) -> None:
    """Sync callback fired by TimeoutManager when a deal expires."""
    import asyncio

    deal = store.deals.get(deal_id)
    if not deal or deal.state in (
        DealState.DEAL_AGREED,
        DealState.DEAL_REJECTED,
        DealState.DEAL_EXPIRED,
    ):
        return  # already terminal

    store.update_deal(deal_id, state=DealState.DEAL_EXPIRED)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(sse_bus.publish("deal_expired", {
            "deal_id": deal_id,
            "state": DealState.DEAL_EXPIRED,
            "timestamp": datetime.now(UTC).isoformat(),
        }))
    except RuntimeError:
        pass


async def _run_scene_analysis(
    opportunity_id: str, signal: OpportunitySignal, deal_id: str,
) -> None:
    """Background task: analyze opportunity image with Gemini Vision."""
    from src.gemini.scene_analyzer import scene_analyzer

    # Resolve image path
    image_path = None
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidate = _STATIC_DIR / "opportunities" / f"{signal.image_id}.{ext}"
        if candidate.exists():
            image_path = candidate
            break

    # Also check demo directory
    if not image_path:
        for ext in ("jpg", "jpeg", "png", "webp"):
            candidate = _STATIC_DIR / "demo" / f"{signal.image_id}.{ext}"
            if candidate.exists():
                image_path = candidate
                break

    if not image_path:
        logger.warning("Scene analysis: image not found for %s", signal.image_id)
        return

    image_bytes = image_path.read_bytes()
    mime = "image/png" if image_path.suffix == ".png" else "image/jpeg"

    # Stream platform thoughts to dashboard
    async def on_thought(text: str):
        await sse_bus.publish("agent_thinking", {
            "agent_id": "platform",
            "agent_name": "AAX Platform Agent",
            "deal_id": deal_id,
            "thought_chunk": text,
        })

    logger.info("Running scene analysis for opportunity %s", opportunity_id)
    try:
        analysis = await asyncio.wait_for(
            scene_analyzer.analyze(image_bytes, mime_type=mime, on_thought=on_thought),
            timeout=30,
        )
    except asyncio.TimeoutError:
        logger.warning("Scene analysis timed out for %s", opportunity_id)
        analysis = scene_analyzer._mock_analysis()

    # Store on opportunity record
    opp = store.opportunities.get(opportunity_id)
    if opp:
        opp.scene_analysis = analysis

    # Publish scene_analyzed SSE event
    await sse_bus.publish("scene_analyzed", {
        "deal_id": deal_id,
        "opportunity_id": opportunity_id,
        "scene_analysis": analysis,
        "image_url": signal.image_url,
    })

    # Record audit event
    store.add_deal_event(deal_id, {
        "type": "scene_analyzed",
        "actor": "AAX Platform",
        "actor_type": "platform",
        "description": f"Scene analyzed: {analysis.get('scene_type', 'unknown')} — "
                       f"{', '.join(analysis.get('categories', []))}",
        "scene_analysis": analysis,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    logger.info(
        "Scene analysis complete: %s, zones=%d, categories=%s",
        analysis.get("scene_type"),
        len(analysis.get("brand_zones", [])),
        analysis.get("categories"),
    )


async def _analyze_and_notify(opp, signal, deal_id, supply_org, matched_ids):
    """Background: run scene analysis, then deliver webhooks to matched agents.

    Runs as asyncio.create_task so the HTTP handler returns immediately.
    Scene analysis completes first, then agents are notified (with analysis data).
    """
    # Step 1: Scene analysis (if image provided)
    if signal.image_id:
        try:
            await asyncio.wait_for(
                _run_scene_analysis(opp.opportunity_id, signal, deal_id),
                timeout=30,
            )
        except asyncio.TimeoutError:
            logger.warning("Scene analysis timed out for %s, continuing", deal_id)
        except Exception as e:
            logger.error("Scene analysis failed for %s: %s", deal_id, e)

    # Step 2: Deliver webhooks to matched demand agents
    signal_data = signal.model_dump(mode="json")
    # Include scene analysis if available
    opp_record = store.opportunities.get(opp.opportunity_id)
    if opp_record and opp_record.scene_analysis:
        signal_data["scene_analysis"] = opp_record.scene_analysis

    for da_id in matched_ids:
        da = store.get_agent(da_id)
        org_id = store.agent_org.get(da_id)
        org = store.get_org(org_id) if org_id else None
        asyncio.create_task(deliver_webhook(da_id, "opportunity.matched", {
            "opportunity_id": opp.opportunity_id,
            "deal_id": deal_id,
            "signal": signal_data,
            "supply_org": supply_org,
            "next_actions": [
                {
                    "action": "propose",
                    "endpoint": f"POST /api/v1/opportunities/{opp.opportunity_id}/propose",
                    "description": "Submit a proposal for this opportunity",
                },
                {
                    "action": "pass",
                    "endpoint": f"POST /api/v1/opportunities/{opp.opportunity_id}/pass",
                    "description": "Decline this opportunity",
                },
            ],
            "constraints": {
                "response_timeout_seconds": DEFAULT_DEAL_TIMEOUT,
                "budget_per_deal": org.budget_per_deal_max if org else 5000,
                "budget_monthly_remaining": (
                    org.budget_monthly_max - org.budget_monthly_spent if org else 50000
                ),
            },
        }))


async def handle_signal_opportunity(
    agent: SupplyAgentProfile,
    signal: OpportunitySignal,
) -> dict:
    """Supply agent signals a new opportunity. Runs pre-screen, creates deal."""
    opp = store.create_opportunity(agent.agent_id, agent.organization, signal)

    demand_agents = store.get_demand_agents()
    matched = []
    prescreen_results = []

    for da in demand_agents:
        school = signal.subjects[0].school if signal.subjects else ""
        sport = signal.subjects[0].sport if signal.subjects else ""
        result = conflict_checker.pre_screen(school, sport, da.organization)
        prescreen_results.append({
            "agent_id": da.agent_id,
            "organization": da.organization,
            "status": result.status,
            "conflicts": [
                c.model_dump(mode="json") for c in result.conflicts
            ],
        })
        if result.status == "cleared":
            matched.append(da.agent_id)
            opp.matched_demand_agents.append(da.agent_id)

    deal_id = f"deal_{uuid.uuid4().hex[:8]}"
    deal = DealSummary(
        deal_id=deal_id,
        opportunity_id=opp.opportunity_id,
        supply_org=agent.organization,
        demand_org="",
        state=DealState.AWAITING_PROPOSALS,
        moment_description=signal.content_description,
    )
    store.create_deal(deal)

    # Register deal timeout
    try:
        timeout_manager.register(
            deal_id, DEFAULT_DEAL_TIMEOUT, _on_deal_expired,
        )
    except RuntimeError:
        pass  # no event loop (tests)

    await sse_bus.publish("deal_created", {
        "deal_id": deal_id,
        "opportunity_id": opp.opportunity_id,
        "state": DealState.AWAITING_PROPOSALS,
        "supply_org": agent.organization,
        "demand_org": "",
        "moment_description": signal.content_description,
        "matched_count": len(matched),
        "prescreen_results": prescreen_results,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Record deal event for audit trail
    store.add_deal_event(deal_id, {
        "type": "opportunity_listed",
        "actor": agent.organization,
        "actor_type": "supply",
        "description": signal.content_description,
        "matched_count": len(matched),
        "prescreen_results": prescreen_results,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Run scene analysis + webhook delivery in background (non-blocking)
    asyncio.create_task(
        _analyze_and_notify(opp, signal, deal_id, agent.organization, matched)
    )

    return {
        "opportunity_id": opp.opportunity_id,
        "deal_id": deal_id,
        "status": "listed",
        "matched_count": len(matched),
        "prescreen_results": prescreen_results,
        "next_actions": [
            {
                "action": "wait_for_proposals",
                "description": (
                    f"{len(matched)} demand agents notified."
                    " Proposals will arrive via webhook."
                ),
            }
        ],
    }


async def handle_pass_opportunity(
    agent: DemandAgentProfile,
    opportunity_id: str,
    reasoning: str = "",
) -> dict:
    """Demand agent declines an opportunity. Records reasoning to deal thread."""
    opp = store.opportunities.get(opportunity_id)
    if not opp:
        return None  # caller raises 404

    # Find the deal for this opportunity
    deal_id = None
    for d in store.deals.values():
        if d.opportunity_id == opportunity_id:
            deal_id = d.deal_id
            break

    reasoning = (reasoning or "").strip() or "No reasoning provided."
    ts = datetime.now(UTC).isoformat()

    if deal_id:
        store.add_deal_event(deal_id, {
            "type": "agent_passed",
            "actor": agent.organization,
            "actor_type": "demand",
            "agent_id": agent.agent_id,
            "reasoning": reasoning,
            "timestamp": ts,
        })

    await sse_bus.publish("agent_passed", {
        "deal_id": deal_id or "",
        "opportunity_id": opportunity_id,
        "agent_id": agent.agent_id,
        "actor": agent.organization,
        "actor_type": "demand",
        "reasoning": reasoning,
        "timestamp": ts,
    })

    return {
        "status": "passed",
        "opportunity_id": opportunity_id,
        "agent_id": agent.agent_id,
    }


async def handle_submit_proposal(
    agent: DemandAgentProfile,
    opportunity_id: str,
    proposal: Proposal,
) -> dict:
    """Demand agent submits a proposal. Runs final conflict check."""
    opp = store.opportunities.get(opportunity_id)
    if not opp:
        return None  # caller raises 404

    athlete_names = [s.athlete_name for s in opp.signal.subjects]
    school = opp.signal.subjects[0].school if opp.signal.subjects else ""
    sport = opp.signal.subjects[0].sport if opp.signal.subjects else ""

    conflict_result = conflict_checker.final_check(
        school, sport, agent.organization, athlete_names,
    )

    if conflict_result.status == "blocked":
        await sse_bus.publish("conflict_blocked", {
            "opportunity_id": opportunity_id,
            "demand_org": agent.organization,
            "conflicts": [
                c.model_dump(mode="json")
                for c in conflict_result.conflicts
            ],
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Record conflict event on any deal for this opportunity
        for d in store.deals.values():
            if d.opportunity_id == opportunity_id:
                store.add_deal_event(d.deal_id, {
                    "type": "conflict_blocked",
                    "actor": agent.organization,
                    "actor_type": "demand",
                    "conflicts": [
                        c.model_dump(mode="json")
                        for c in conflict_result.conflicts
                    ],
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                break

        return {
            "proposal_id": None,
            "status": "conflict_blocked",
            "conflict_result": conflict_result.model_dump(mode="json"),
        }

    prop = store.create_proposal({
        "opportunity_id": opportunity_id,
        "demand_agent_id": agent.agent_id,
        "demand_org": agent.organization,
        "deal_terms": proposal.deal_terms,
        "scores": proposal.scores,
        "reasoning": proposal.reasoning,
    })

    for deal in store.deals.values():
        if deal.opportunity_id == opportunity_id:
            new_ids = deal.all_proposal_ids + [prop.proposal_id]
            store.update_deal(
                deal.deal_id,
                state=DealState.AWAITING_SUPPLY_EVAL,
                demand_org=agent.organization,
                deal_terms=proposal.deal_terms,
                all_proposal_ids=new_ids,
            )

            await sse_bus.publish("deal_update", {
                "deal_id": deal.deal_id,
                "opportunity_id": opportunity_id,
                "state": DealState.AWAITING_SUPPLY_EVAL,
                "supply_org": deal.supply_org,
                "demand_org": agent.organization,
                "moment_description": deal.moment_description,
                "deal_terms": proposal.deal_terms.model_dump(mode="json"),
                "scores": (
                    proposal.scores.model_dump(mode="json")
                    if proposal.scores else None
                ),
                "reasoning": proposal.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

            # Record deal event
            store.add_deal_event(deal.deal_id, {
                "type": "proposal_submitted",
                "actor": agent.organization,
                "actor_type": "demand",
                "proposal_id": prop.proposal_id,
                "price": proposal.deal_terms.price.amount,
                "reasoning": proposal.reasoning,
                "scores": (
                    proposal.scores.model_dump(mode="json")
                    if proposal.scores else None
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            })

            # Deliver proposal.received webhook to supply agent
            asyncio.create_task(deliver_webhook(
                opp.supply_agent_id,
                "proposal.received",
                {
                    "deal_id": deal.deal_id,
                    "proposal_id": prop.proposal_id,
                    "opportunity_id": opportunity_id,
                    "demand_org": agent.organization,
                    "deal_terms": proposal.deal_terms.model_dump(
                        mode="json",
                    ),
                    "reasoning": proposal.reasoning,
                    "scores": (
                        proposal.scores.model_dump(mode="json")
                        if proposal.scores else None
                    ),
                    "next_actions": [
                        {
                            "action": "accept",
                            "endpoint": (
                                f"POST /api/v1/proposals"
                                f"/{prop.proposal_id}/respond"
                            ),
                        },
                        {
                            "action": "counter",
                            "endpoint": (
                                f"POST /api/v1/proposals"
                                f"/{prop.proposal_id}/respond"
                            ),
                        },
                        {
                            "action": "reject",
                            "endpoint": (
                                f"POST /api/v1/proposals"
                                f"/{prop.proposal_id}/respond"
                            ),
                        },
                    ],
                    "constraints": {
                        "round": prop.round,
                        "max_rounds": 3,
                    },
                },
            ))
            break

    return {
        "proposal_id": prop.proposal_id,
        "status": "submitted",
        "conflict_status": "cleared",
        "valid_actions": ["wait_for_supply_evaluation"],
        "constraints": {
            "max_counter_rounds": 3,
            "response_timeout_seconds": 600,
        },
    }


async def handle_respond_to_proposal(
    agent: SupplyAgentProfile | DemandAgentProfile,
    proposal_id: str,
    response: ProposalResponse,
) -> dict:
    """Supply agent responds to a proposal (accept/counter/reject)."""
    prop = store.proposals.get(proposal_id)
    if not prop:
        return None  # caller raises 404

    deal = None
    for d in store.deals.values():
        if d.opportunity_id == prop.opportunity_id:
            deal = d
            break

    if response.decision == EvaluationDecision.ACCEPT:
        prop_updated = prop.model_copy(
            update={"status": ProposalStatus.ACCEPTED},
        )
        store.proposals[proposal_id] = prop_updated

        if deal:
            store.update_deal(
                deal.deal_id,
                state=DealState.DEAL_AGREED,
                winning_proposal_id=proposal_id,
            )
            timeout_manager.cancel(deal.deal_id)

            agreement = DealAgreement(
                deal_id=deal.deal_id,
                opportunity_id=prop.opportunity_id,
                supply_agent_id=agent.agent_id,
                demand_agent_id=prop.demand_agent_id,
                final_terms=prop.deal_terms,
                supply_org=deal.supply_org,
                demand_org=prop.demand_org,
            )
            store.deal_results[deal.deal_id] = agreement.model_dump(
                mode="json",
            )

            await sse_bus.publish("deal_agreed", {
                "deal_id": deal.deal_id,
                "state": DealState.DEAL_AGREED,
                "supply_org": deal.supply_org,
                "demand_org": prop.demand_org,
                "moment_description": deal.moment_description,
                "deal_terms": prop.deal_terms.model_dump(mode="json"),
                "reasoning": response.reasoning,
                "scores": (
                    response.scores.model_dump(mode="json")
                    if response.scores else None
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            })

            store.add_deal_event(deal.deal_id, {
                "type": "proposal_accepted",
                "actor": agent.organization,
                "actor_type": (
                    "supply" if hasattr(agent, "capabilities") else "demand"
                ),
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

            # Deliver deal.agreed webhook to both agents
            agreed_payload = {
                "deal_id": deal.deal_id,
                "event": "deal.agreed",
                "final_terms": prop.deal_terms.model_dump(mode="json"),
                "supply_org": deal.supply_org,
                "demand_org": prop.demand_org,
            }
            opp = store.opportunities.get(prop.opportunity_id)
            if opp:
                asyncio.create_task(
                    deliver_webhook(
                        opp.supply_agent_id, "deal.agreed", agreed_payload,
                    ),
                )
            asyncio.create_task(
                deliver_webhook(
                    prop.demand_agent_id, "deal.agreed", agreed_payload,
                ),
            )

            # ── Trigger fulfillment: generate brief + deliver to supply ──
            asyncio.create_task(
                _trigger_fulfillment(deal, prop, opp),
            )

        return {
            "status": "accepted",
            "deal_id": deal.deal_id if deal else None,
            "next_actions": [{
                "action": "await_creative_brief",
                "description": "Brief will be sent to your webhook.",
            }],
        }

    elif response.decision == EvaluationDecision.REJECT:
        prop_updated = prop.model_copy(
            update={"status": ProposalStatus.REJECTED},
        )
        store.proposals[proposal_id] = prop_updated

        if deal:
            store.update_deal(deal.deal_id, state=DealState.DEAL_REJECTED)
            timeout_manager.cancel(deal.deal_id)
            await sse_bus.publish("deal_update", {
                "deal_id": deal.deal_id,
                "state": DealState.DEAL_REJECTED,
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

            store.add_deal_event(deal.deal_id, {
                "type": "proposal_rejected",
                "actor": agent.organization,
                "actor_type": (
                    "supply" if hasattr(agent, "capabilities") else "demand"
                ),
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

        return {"status": "rejected", "reasoning": response.reasoning}

    else:  # COUNTER
        # Enforce max negotiation rounds
        if deal and prop.round >= deal.max_rounds:
            return {
                "status": "error",
                "detail": (
                    f"Maximum negotiation rounds ({deal.max_rounds})"
                    " reached. Accept or reject."
                ),
            }

        prop_updated = prop.model_copy(
            update={"status": ProposalStatus.COUNTERED},
        )
        store.proposals[proposal_id] = prop_updated
        new_round = prop.round + 1

        if deal:
            store.update_deal(
                deal.deal_id,
                state=DealState.NEGOTIATING,
                negotiation_round=new_round,
                deal_terms=response.counter_terms,
            )
            await sse_bus.publish("deal_update", {
                "deal_id": deal.deal_id,
                "state": DealState.NEGOTIATING,
                "negotiation_round": new_round,
                "counter_terms": (
                    response.counter_terms.model_dump(mode="json")
                    if response.counter_terms else None
                ),
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

            store.add_deal_event(deal.deal_id, {
                "type": "counter_offer",
                "actor": agent.organization,
                "actor_type": (
                    "supply" if hasattr(agent, "capabilities") else "demand"
                ),
                "round": new_round,
                "counter_terms": (
                    response.counter_terms.model_dump(mode="json")
                    if response.counter_terms else None
                ),
                "reasoning": response.reasoning,
                "timestamp": datetime.now(UTC).isoformat(),
            })

            # Deliver counter.received webhook to the other party
            counter_recipient = prop.demand_agent_id
            asyncio.create_task(deliver_webhook(
                counter_recipient,
                "counter.received",
                {
                    "deal_id": deal.deal_id,
                    "proposal_id": proposal_id,
                    "counter_terms": (
                        response.counter_terms.model_dump(mode="json")
                        if response.counter_terms else None
                    ),
                    "reasoning": response.reasoning,
                    "constraints": {
                        "round": new_round,
                        "max_rounds": 3,
                    },
                    "next_actions": [
                        {"action": "accept"},
                        {"action": "counter"},
                        {"action": "reject"},
                    ],
                },
            ))

        counter = (
            response.counter_terms.model_dump(mode="json")
            if response.counter_terms else None
        )
        return {
            "status": "countered",
            "round": new_round,
            "counter_terms": counter,
        }


async def handle_select_winner(opportunity_id: str) -> dict | None:
    """Select the best non-blocked proposal for an opportunity."""
    opp = store.opportunities.get(opportunity_id)
    if not opp:
        return None

    # Gather all proposals for this opportunity
    proposals = [
        p for p in store.proposals.values()
        if p.opportunity_id == opportunity_id
        and p.status != ProposalStatus.CONFLICT_BLOCKED
    ]

    if not proposals:
        return {"status": "no_proposals", "opportunity_id": opportunity_id}

    # Sort by overall score (descending), then by price (descending)
    def sort_key(p):
        score = p.scores.overall if p.scores else 0
        price = p.deal_terms.price.amount if p.deal_terms else 0
        return (score, price)

    proposals.sort(key=sort_key, reverse=True)
    winner = proposals[0]

    # Update deal with winner
    for deal in store.deals.values():
        if deal.opportunity_id == opportunity_id:
            store.update_deal(
                deal.deal_id,
                state=DealState.AWAITING_SUPPLY_EVAL,
                demand_org=winner.demand_org,
                deal_terms=winner.deal_terms,
                winning_proposal_id=winner.proposal_id,
            )

            await sse_bus.publish("proposals_ranked", {
                "deal_id": deal.deal_id,
                "opportunity_id": opportunity_id,
                "state": DealState.AWAITING_SUPPLY_EVAL,
                "winning_proposal_id": winner.proposal_id,
                "all_proposals": [
                    {
                        "proposal_id": p.proposal_id,
                        "demand_org": p.demand_org,
                        "price": (
                            p.deal_terms.price.amount if p.deal_terms else 0
                        ),
                        "score": p.scores.overall if p.scores else 0,
                        "status": "won" if p == winner else "outbid",
                    }
                    for p in proposals
                ],
                "timestamp": datetime.now(UTC).isoformat(),
            })
            break

    return {
        "status": "winner_selected",
        "proposal_id": winner.proposal_id,
        "demand_org": winner.demand_org,
        "price": winner.deal_terms.price.amount if winner.deal_terms else 0,
    }


# ── Fulfillment ──────────────────────────────────────────────────────


async def _trigger_fulfillment(deal, prop, opp):
    """Generate creative brief and deliver to supply agent."""
    import asyncio as _asyncio
    await _asyncio.sleep(1)  # small delay for deal.agreed webhooks to land

    # Build brief from deal + opportunity data
    signal = opp.signal if opp else None
    subjects = signal.subjects if signal else []
    athlete = subjects[0].athlete_name if subjects else ""
    school = subjects[0].school if subjects else ""
    sport = subjects[0].sport if subjects else ""

    brief = {
        "deal_id": deal.deal_id,
        "deal_terms": prop.deal_terms.model_dump(mode="json"),
        "athlete_name": athlete,
        "school": school,
        "sport": sport,
        "moment_description": deal.moment_description,
        "brand_name": prop.demand_org,
    }

    # Store brief in deal results
    store.deal_results.setdefault(deal.deal_id, {})
    if isinstance(store.deal_results[deal.deal_id], dict):
        store.deal_results[deal.deal_id]["brief"] = brief

    # Update deal state
    store.update_deal(deal.deal_id, state=DealState.FULFILLMENT_BRIEF_SENT)

    # Record event
    store.add_deal_event(deal.deal_id, {
        "type": "brief_generated",
        "actor": "AAX Exchange",
        "actor_type": "platform",
        "brief": brief,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    await sse_bus.publish("fulfillment_update", {
        "deal_id": deal.deal_id,
        "state": "fulfillment_brief_sent",
        "stage": "brief_generated",
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Deliver brief to supply agent via webhook
    if opp:
        await deliver_webhook(
            opp.supply_agent_id,
            "brief.generated",
            {
                "deal_id": deal.deal_id,
                "brief": brief,
                "next_actions": [
                    {
                        "action": "submit_content",
                        "endpoint": f"POST /api/v1/content/{deal.deal_id}",
                        "description": (
                            "Generate content matching the brief and submit it."
                        ),
                    },
                ],
            },
        )

    # Generate branded content options if image was provided (v3)
    if opp and opp.signal.image_id:
        asyncio.create_task(
            _generate_branded_content(deal, prop, opp)
        )


async def _generate_branded_content(deal, prop, opp) -> None:
    """Background task: generate branded image options using Gemini."""
    from src.gemini.content_generator import content_generator

    signal = opp.signal
    scene = opp.scene_analysis or {}
    zones = scene.get("brand_zones", [])

    # Pick the best zone (highest tier or first available)
    default_zone = {"tier": 2, "zone_id": "general", "description": "brand placement"}
    best_zone = zones[0] if zones else default_zone

    # Resolve original image
    image_bytes = None
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidate = _STATIC_DIR / "opportunities" / f"{signal.image_id}.{ext}"
        if candidate.exists():
            image_bytes = candidate.read_bytes()
            break
    if not image_bytes:
        for ext in ("jpg", "jpeg", "png", "webp"):
            candidate = _STATIC_DIR / "demo" / f"{signal.image_id}.{ext}"
            if candidate.exists():
                image_bytes = candidate.read_bytes()
                break

    if not image_bytes:
        logger.warning("Content gen: image not found for %s", signal.image_id)
        return

    # Load brand logo
    brand_lower = prop.demand_org.lower().replace(" ", "_")
    logo_path = _STATIC_DIR / "brand_assets" / f"{brand_lower}_logo.png"
    logo_bytes = logo_path.read_bytes() if logo_path.exists() else None

    logger.info(
        "Generating branded content for deal %s: %s Tier %d",
        deal.deal_id, prop.demand_org, best_zone.get("tier", 2),
    )

    await sse_bus.publish("fulfillment_update", {
        "deal_id": deal.deal_id,
        "state": "content_generating",
        "stage": "generating_branded_options",
        "brand": prop.demand_org,
        "tier": best_zone.get("tier", 2),
        "timestamp": datetime.now(UTC).isoformat(),
    })

    options = await content_generator.generate_options(
        original_image_bytes=image_bytes,
        brand_logo_bytes=logo_bytes,
        brand_name=prop.demand_org,
        tier=best_zone.get("tier", 2),
        zone_description=best_zone.get("description", "brand placement"),
        creative_notes=scene.get("creative_notes", ""),
        num_options=1,
    )

    # Store options on deal
    store.deal_results.setdefault(deal.deal_id, {})
    store.deal_results[deal.deal_id]["content_options"] = options

    # Publish content_generated SSE event
    await sse_bus.publish("content_generated", {
        "deal_id": deal.deal_id,
        "options": options,
        "brand": prop.demand_org,
        "tier": best_zone.get("tier", 2),
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Record audit event
    store.add_deal_event(deal.deal_id, {
        "type": "content_generated",
        "actor": "AAX Platform",
        "actor_type": "platform",
        "description": f"Generated {len(options)} branded image options for {prop.demand_org}",
        "options": options,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    logger.info("Content generation complete for deal %s: %d options", deal.deal_id, len(options))

    # Validate each generated image (not a mock URL — the actual generated content)
    await _validate_generated_options(deal, options)


async def _validate_generated_options(deal, options: list[dict]) -> None:
    """Validate the platform-generated images using Gemini Vision.

    For each option that has a real image, run validation. If any option
    passes, mark the deal as completed. Otherwise log issues (future: trigger
    regeneration with corrections).
    """
    from src.validation.content import validate_content

    valid_options = [o for o in options if o.get("image_url") and not o.get("placeholder")]
    if not valid_options:
        logger.warning("No valid options to validate for deal %s", deal.deal_id)
        return

    validation_results = []
    for opt in valid_options:
        # validate_content checks /static/generated/ path automatically
        try:
            result = await validate_content(opt["image_url"], deal)
            result["option_id"] = opt["option_id"]
            result["style"] = opt["style"]
            validation_results.append(result)

            await sse_bus.publish("content_validated", {
                "deal_id": deal.deal_id,
                "option_id": opt["option_id"],
                "style": opt["style"],
                "passed": result.get("passed"),
                "score": result.get("score"),
                "checks": result.get("checks"),
                "issues": result.get("issues", []),
                "timestamp": datetime.now(UTC).isoformat(),
            })

            store.add_deal_event(deal.deal_id, {
                "type": "content_validated",
                "actor": "AAX Validator",
                "actor_type": "platform",
                "option_id": opt["option_id"],
                "style": opt["style"],
                "passed": result.get("passed"),
                "score": result.get("score"),
                "checks": result.get("checks"),
                "issues": result.get("issues", []),
                "timestamp": datetime.now(UTC).isoformat(),
            })
        except Exception as e:
            logger.error("Validation failed for option %s: %s", opt.get("option_id"), e)

    # Store validation results
    store.deal_results.setdefault(deal.deal_id, {})
    store.deal_results[deal.deal_id]["validation_results"] = validation_results

    # If any option passed, mark deal as completed
    any_passed = any(r.get("passed") for r in validation_results)
    if any_passed:
        store.update_deal(deal.deal_id, state=DealState.COMPLETED)
        await sse_bus.publish("deal_completed", {
            "deal_id": deal.deal_id,
            "timestamp": datetime.now(UTC).isoformat(),
        })
        store.add_deal_event(deal.deal_id, {
            "type": "deal_completed",
            "actor": "AAX Exchange",
            "actor_type": "platform",
            "description": f"Deal complete — {sum(1 for r in validation_results if r.get('passed'))} of {len(validation_results)} options passed validation",
            "timestamp": datetime.now(UTC).isoformat(),
        })
        logger.info("Deal %s completed — %d options passed validation", deal.deal_id, sum(1 for r in validation_results if r.get("passed")))
    else:
        logger.warning(
            "Deal %s — no options passed validation. Future: trigger regeneration with corrections.",
            deal.deal_id,
        )


async def handle_content_submission(
    deal_id: str,
    submission_data: dict,
    agent,
) -> dict:
    """Process content submitted by supply agent. Validate and complete.

    In v3, the platform generates branded content directly (via Gemini image gen)
    and validates those. Agent-submitted mock URLs should be ignored when the
    opportunity had an image — the platform is authoritative for content.
    """
    deal = store.deals.get(deal_id)
    if not deal:
        return None

    # v3: if opportunity had an image, platform owns content generation. Skip agent submission.
    opp = store.opportunities.get(deal.opportunity_id)
    if opp and opp.signal.image_id:
        logger.info(
            "Ignoring agent content submission for %s — platform handles image-based deals",
            deal_id,
        )
        return {"status": "ignored", "reason": "platform_owns_content"}

    content_url = submission_data.get("content_url", "")
    content_format = submission_data.get("format", "gameday_graphic")

    # Record submission event
    store.add_deal_event(deal_id, {
        "type": "content_submitted",
        "actor": agent.organization,
        "actor_type": "supply",
        "content_url": content_url,
        "format": content_format,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    store.update_deal(deal_id, state=DealState.FULFILLMENT_CONTENT_SUBMITTED)

    await sse_bus.publish("fulfillment_update", {
        "deal_id": deal_id,
        "state": "fulfillment_content_submitted",
        "stage": "content_submitted",
        "content_url": content_url,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Validate content (placeholder — will be replaced with Claude Vision)
    validation = await _validate_content(content_url, deal)

    # Record validation event
    store.add_deal_event(deal_id, {
        "type": "content_validated",
        "actor": "AAX Exchange",
        "actor_type": "platform",
        "passed": validation["passed"],
        "score": validation["score"],
        "checks": validation["checks"],
        "issues": validation.get("issues", []),
        "timestamp": datetime.now(UTC).isoformat(),
    })

    if validation["passed"]:
        store.update_deal(deal_id, state=DealState.COMPLETED)
        store.add_deal_event(deal_id, {
            "type": "deal_completed",
            "actor": "AAX Exchange",
            "actor_type": "platform",
            "timestamp": datetime.now(UTC).isoformat(),
        })

        await sse_bus.publish("deal_completed", {
            "deal_id": deal_id,
            "state": "completed",
            "supply_org": deal.supply_org,
            "demand_org": deal.demand_org,
            "content_url": content_url,
            "validation": validation,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Notify both agents
        opp = store.opportunities.get(deal.opportunity_id)
        if opp:
            completed_payload = {
                "deal_id": deal_id,
                "content_url": content_url,
                "validation": validation,
            }
            asyncio.create_task(
                deliver_webhook(
                    opp.supply_agent_id, "deal.completed", completed_payload,
                ),
            )
            # Find demand agent from proposals
            for p in store.proposals.values():
                if p.opportunity_id == deal.opportunity_id and p.status == "accepted":
                    asyncio.create_task(
                        deliver_webhook(
                            p.demand_agent_id, "deal.completed", completed_payload,
                        ),
                    )
                    break

        return {
            "status": "validated",
            "validation": validation,
            "deal_state": "completed",
        }
    else:
        # Content failed validation
        store.update_deal(deal_id, state=DealState.FULFILLMENT_REVISION_NEEDED)

        await sse_bus.publish("fulfillment_update", {
            "deal_id": deal_id,
            "state": "fulfillment_revision_needed",
            "stage": "revision_requested",
            "issues": validation.get("issues", []),
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Deliver revision request to supply agent
        opp = store.opportunities.get(deal.opportunity_id)
        if opp:
            asyncio.create_task(deliver_webhook(
                opp.supply_agent_id,
                "content.revision_requested",
                {
                    "deal_id": deal_id,
                    "validation": validation,
                    "next_actions": [{
                        "action": "resubmit_content",
                        "endpoint": f"POST /api/v1/content/{deal_id}",
                    }],
                },
            ))

        return {
            "status": "revision_needed",
            "validation": validation,
            "deal_state": "fulfillment_revision_needed",
        }


async def _validate_content(content_url: str, deal) -> dict:
    """Validate content using Gemini Vision (or fallback)."""
    from src.validation.content import validate_content
    return await validate_content(content_url, deal)
