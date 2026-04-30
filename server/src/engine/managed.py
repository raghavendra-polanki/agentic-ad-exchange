"""ManagedAgentRunner — runs an agent in-process using Gemini.

For Path A (managed agents): human creates an agent via dashboard,
the platform runs it internally using Gemini with the configured
brand persona as system prompt. Uses the store's notification queue
instead of HTTP webhooks. Streams reasoning thoughts to SSE.
"""

import asyncio
import json
import logging

from src.api.stream import sse_bus
from src.gemini.adaptor import gemini
from src.schemas.agents import AgentType, RegisterAgentRequest
from src.store import store

logger = logging.getLogger("aax.managed")

# Registry of running managed agents
_runners: dict[str, "ManagedAgentRunner"] = {}


def get_runner(agent_id: str) -> "ManagedAgentRunner | None":
    return _runners.get(agent_id)


def get_all_runners() -> dict[str, "ManagedAgentRunner"]:
    return _runners


def _parse_json_response(text: str) -> dict | None:
    """Extract JSON from LLM response text."""
    text = text.strip()
    # Handle markdown code blocks
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if "```" in text:
            text = text[:text.rindex("```")]
        text = text.strip()
    if "{" in text:
        try:
            return json.loads(text[text.index("{"):text.rindex("}") + 1])
        except (json.JSONDecodeError, ValueError):
            pass
    return None


class ManagedAgentRunner:
    """Runs an agent in-process. Processes notifications from the store queue."""

    def __init__(
        self,
        org_id: str,
        agent_config: dict,
        agent_id: str | None = None,
    ):
        self.org_id = org_id
        self.agent_config = agent_config
        self.agent_id: str | None = agent_id  # stable id (from persona filename) or None to generate
        self.api_key: str | None = None
        self.running = False
        self._task: asyncio.Task | None = None
        # system_prompt is built in start() after register, when we know
        # the final agent_id and have BrandRules/ContentRules in the store.
        self.system_prompt: str = ""

    def _build_demand_prompt(self) -> str:
        """Build a Gemini system prompt for a demand agent from BrandRules.

        Re-reading from the store on every call is the Phase B move; for now
        this is invoked once at start. Falls back to agent_config when no
        BrandRules row exists (e.g. agents created via API without a persona).
        """
        rules = store.get_brand_rules(self.agent_id) if self.agent_id else None
        if rules:
            name = rules.agent_name
            org = rules.brand
            budget = rules.budget_per_deal_max
            competitors = ", ".join(rules.competitor_exclusions) or "(none listed)"
            voice = rules.voice_md
        else:
            cfg = self.agent_config
            bp = cfg.get("brand_profile", {})
            name = cfg.get("name", "Agent")
            org = cfg.get("organization", "Unknown")
            budget = bp.get("budget_per_deal_max", 5000)
            competitors = ", ".join(bp.get("competitor_exclusions", [])) or "(none listed)"
            voice = cfg.get("description", "")

        return f"""You are {name}, an autonomous AI sponsorship agent for {org}.

## Your Identity
- Brand: {org}
- Budget: up to ${budget} per deal
- Competitors to NEVER sponsor alongside: {competitors}

## Voice & Brand Guidance
{voice}

## Your Evaluation Framework
When evaluating a content opportunity, think through each step:
1. BRAND FIT: Does this athlete/moment align with {org}'s brand narrative?
2. AUDIENCE: Is the reach worth the spend? What's the CPM?
3. TIER VALUE: Which placement tier (1=background, 2=integration, 3=product interaction) maximizes impact?
4. PRICE STRATEGY: What's fair market value? Bid strong but leave room for negotiation.
5. TIMING: Is this moment still fresh?

## Your Negotiation Style
- Open strong but leave 20% room for counter
- Accept counters within 25% of your bid
- Never chase — if rejected, move on
- Prefer exclusivity on the content

## Response Format
Respond with ONLY a JSON object:
{{"should_bid": true, "price": 2000, "reasoning": "detailed multi-sentence reasoning explaining your decision process", "scores": {{"audience_fit": 80, "brand_alignment": 85, "price_adequacy": 75, "projected_roi": 70, "overall": 78}}}}

If passing: {{"should_bid": false, "reasoning": "why this doesn't fit"}}"""

    def _build_supply_prompt(self) -> str:
        """Build a Gemini system prompt for a supply agent from ContentRules."""
        rules = store.get_content_rules(self.agent_id) if self.agent_id else None
        if rules:
            name = rules.agent_name
            org = self.agent_config.get("organization", "Pixology")
            min_price = rules.min_price_per_deal
            voice = rules.voice_md
        else:
            cfg = self.agent_config
            name = cfg.get("name", "Content Agent")
            org = cfg.get("organization", "Pixology")
            min_price = 100
            voice = cfg.get("description", "")

        return f"""You are {name}, an autonomous AI content creation agent for {org}.

## Your Identity
- Service: Premium content creation for college athletes
- Quality: Broadcast-grade, NCAA-compliant
- Default minimum price floor: ${min_price} (the listed opportunity min_price overrides)

## Voice & Service Guidance
{voice}

## Your Evaluation Framework
When evaluating a brand proposal, think through:
1. PRICE: Does it meet or exceed the opportunity's listed min_price? That's the only hard floor — respect what we priced it at.
2. BRAND SAFETY: Will this brand help or hurt the athlete's image?
3. CREATIVE FEASIBILITY: Can you produce natural-looking content at the requested tier?
4. USAGE RIGHTS: Shorter is better for you. Push for 14 days max.
5. PARTNER VALUE: Premium brands get slight preference, but local relevance also counts.

## Your Negotiation Style
- Accept any offer that meets or exceeds the listed min_price
- Counter up ~20% only if the bid is exactly at floor AND you sense more room
- Reject ONLY if the bid is below the listed min_price
- For local/small-budget deals (min_price < $300), accept quickly — volume matters

## Response Format
Respond with ONLY a JSON object:
{{"decision": "accept", "reasoning": "detailed reasoning", "counter_price": null}}
For counter: {{"decision": "counter", "reasoning": "why countering", "counter_price": 750}}
For reject: {{"decision": "reject", "reasoning": "why rejecting", "counter_price": null}}"""

    async def start(self):
        """Register with exchange and start processing loop."""
        req = RegisterAgentRequest(
            agent_type=AgentType(self.agent_config.get("agent_type", "demand")),
            name=self.agent_config.get("name", "Managed Agent"),
            organization=self.agent_config.get("organization", "Unknown"),
            description=self.agent_config.get("description", ""),
        )

        if req.agent_type == AgentType.DEMAND:
            from src.schemas.agents import BrandProfile
            bp = self.agent_config.get("brand_profile", {})
            req.brand_profile = BrandProfile(**bp) if bp else None

        creds = store.register_agent(req, org_id=self.org_id, agent_id=self.agent_id)
        self.agent_id = creds.agent_id
        self.api_key = creds.api_key

        # Build system_prompt now that agent_id is stable and store may have rules
        if req.agent_type == AgentType.DEMAND:
            self.system_prompt = self._build_demand_prompt()
        else:
            self.system_prompt = self._build_supply_prompt()
        self.running = True
        _runners[self.agent_id] = self

        logger.info(
            "Managed agent started: %s (%s) — Gemini=%s",
            self.agent_config.get("name"), self.agent_id,
            "ON" if gemini.available else "OFF",
        )
        self._task = asyncio.create_task(self._process_loop())

    async def stop(self):
        """Stop the processing loop."""
        self.running = False
        if self._task:
            self._task.cancel()
        if self.agent_id:
            _runners.pop(self.agent_id, None)
        logger.info("Managed agent stopped: %s", self.agent_id)

    async def _process_loop(self):
        """Continuously poll for notifications and process them."""
        while self.running:
            try:
                notifications = store.drain_notifications(self.agent_id)
                for notif in notifications:
                    await self._handle_notification(notif)
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Managed agent %s error: %s", self.agent_id, e)
                await asyncio.sleep(1)

    async def _call_gemini(self, user_message: str, deal_id: str = "") -> dict | None:
        """Call Gemini with streaming thoughts published to SSE.

        Rebuilds system_prompt from current store state on every call so
        brand-rules edits made via the dashboard take effect immediately,
        without a server restart.
        """
        if not gemini.available:
            return None

        # Re-read persona from store (BrandRules / ContentRules may have been edited)
        agent_type = self.agent_config.get("agent_type", "demand")
        if agent_type == "demand":
            self.system_prompt = self._build_demand_prompt()
        else:
            self.system_prompt = self._build_supply_prompt()

        full_prompt = f"{self.system_prompt}\n\n---\n\n{user_message}"

        async def on_thought(text: str):
            await sse_bus.publish("agent_thinking", {
                "agent_id": self.agent_id,
                "agent_name": self.agent_config.get("name", "Managed Agent"),
                "deal_id": deal_id,
                "thought_chunk": text,
            })

        try:
            result = await asyncio.wait_for(
                gemini.reason(
                    prompt=full_prompt,
                    on_thought=on_thought,
                    thinking_budget=4096,
                ),
                timeout=60,  # 60s max for Gemini reasoning
            )
            return _parse_json_response(result["text"])
        except asyncio.TimeoutError:
            logger.warning("Gemini timed out for managed agent %s", self.agent_id)
            return None
        except Exception as e:
            logger.warning("Gemini call failed for managed agent %s: %s", self.agent_id, e)
            return None

    async def _handle_notification(self, notif: dict):
        """Process a single notification."""
        event_type = notif.get("event", "")
        data = notif.get("data", notif)

        logger.info(
            "Managed agent %s received: event=%r, keys=%s, data_keys=%s",
            self.agent_id,
            event_type,
            list(notif.keys()),
            list(data.keys()) if isinstance(data, dict) else type(data).__name__,
        )

        if event_type == "opportunity.matched":
            await self._handle_opportunity(data)
        elif event_type == "proposal.received":
            await self._handle_proposal(data)
        elif event_type == "counter.received":
            await self._handle_counter(data)
        elif event_type == "brief.generated":
            await self._handle_brief(data)
        elif event_type:
            logger.info("Managed agent %s: unhandled event %r", self.agent_id, event_type)
        else:
            logger.warning(
                "Managed agent %s: notification missing 'event' key. Full notif: %s",
                self.agent_id, str(notif)[:300],
            )

    async def _handle_opportunity(self, data: dict):
        """Evaluate opportunity and submit proposal if interested."""
        import httpx

        opp_id = data.get("opportunity_id")
        deal_id = data.get("deal_id", "")
        signal = data.get("signal", {})

        subjects = signal.get("subjects", [])
        athlete = subjects[0].get("athlete_name", "Unknown") if subjects else "Unknown"
        school = subjects[0].get("school", "") if subjects else ""
        scene = data.get("scene_analysis", {})

        # Build rich evaluation prompt
        scene_context = ""
        if scene:
            zones = scene.get("brand_zones", [])
            zone_text = "\n".join(
                f"  - {z['zone_id']} (Tier {z['tier']}): {z['description']}"
                for z in zones
            )
            scene_context = (
                f"\n\nScene Analysis (from platform):\n"
                f"  Type: {scene.get('scene_type')}, Mood: {scene.get('mood')}\n"
                f"  Brand zones:\n{zone_text}\n"
                f"  Categories: {scene.get('categories')}\n"
                f"  Pricing guidance: {scene.get('pricing_guidance')}"
            )

        user_msg = (
            f"Evaluate this content sponsorship opportunity:\n"
            f"- Athlete: {athlete} ({school})\n"
            f"- Sport: {signal.get('sport', 'unknown')}\n"
            f"- Moment: {signal.get('content_description', '')}\n"
            f"- Audience reach: {signal.get('audience', {}).get('projected_reach', 0):,}\n"
            f"- Trending score: {signal.get('audience', {}).get('trending_score', 0)}\n"
            f"- Min price: ${signal.get('min_price', 0)}\n"
            f"- Available formats: {signal.get('available_formats', [])}"
            f"{scene_context}\n\n"
            f"Should you bid? If yes, at what price and for which tier/zone?"
        )

        result = await self._call_gemini(user_msg, deal_id)

        if result and result.get("should_bid"):
            budget = self.agent_config.get("brand_profile", {}).get(
                "budget_per_deal_max", 5000,
            )
            price = min(budget, result.get("price", 1000))
            reasoning = result.get("reasoning", "Managed agent bid")
            scores = result.get("scores", {"overall": 70})
        else:
            if result and not result.get("should_bid"):
                pass_reason = result.get("reasoning", "Opportunity did not fit brand criteria.")
                logger.info(
                    "Managed agent %s: passing on %s — %s",
                    self.agent_id, opp_id, pass_reason[:120],
                )
                agent = store.get_agent(self.agent_id)
                if agent:
                    from src.engine.orchestrator import handle_pass_opportunity
                    await handle_pass_opportunity(agent, opp_id, pass_reason)
                return
            # Fallback if Gemini unavailable
            price = 1000
            reasoning = "Automated bid from managed agent"
            scores = {"overall": 60}

        logger.info("Managed agent %s: bidding $%s on %s", self.agent_id, price, opp_id)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"http://localhost:8080/api/v1/opportunities/{opp_id}/propose",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "deal_terms": {
                            "price": {"amount": price, "currency": "USD"},
                            "content_format": "gameday_graphic",
                            "platforms": ["instagram", "twitter"],
                            "usage_rights_duration_days": 30,
                        },
                        "reasoning": reasoning,
                        "scores": scores,
                    },
                )
                if resp.status_code == 200:
                    logger.info("Managed agent %s: proposal submitted", self.agent_id)
                else:
                    logger.error("Managed agent %s: proposal failed %s", self.agent_id, resp.text)
        except Exception as e:
            logger.error("Managed agent %s: %s", self.agent_id, e)

    async def _handle_proposal(self, data: dict):
        """Evaluate a proposal (supply agent role)."""
        import httpx

        proposal_id = data.get("proposal_id")
        deal_id = data.get("deal_id", "")
        demand_org = data.get("demand_org", "Unknown")
        deal_terms = data.get("deal_terms", {})
        price = deal_terms.get("price", {}).get("amount", 0)

        # Look up the opportunity's listed min_price so the supply agent can
        # respect the floor it originally set.
        opportunity_id = data.get("opportunity_id", "")
        min_price = 0
        moment = ""
        if opportunity_id:
            opp = store.opportunities.get(opportunity_id)
            if opp:
                min_price = opp.signal.min_price or 0
                moment = opp.signal.content_description or ""

        user_msg = (
            f"Evaluate this sponsorship proposal:\n"
            f"- Brand: {demand_org}\n"
            f"- Moment: {moment[:200]}\n"
            f"- Price offered: ${price}\n"
            f"- Our listed min_price (the floor we set): ${min_price}\n"
            f"- Content format: {deal_terms.get('content_format', 'unknown')}\n"
            f"- Platforms: {deal_terms.get('platforms', [])}\n"
            f"- Usage rights: {deal_terms.get('usage_rights_duration_days', 'N/A')} days\n"
            f"\nShould you accept, counter, or reject? "
            f"Remember: the listed min_price is the only hard floor."
        )

        result = await self._call_gemini(user_msg, deal_id)
        decision = result.get("decision", "accept") if result else "accept"
        reasoning = (
            result.get("reasoning", "")
            if result else f"Auto-accepted ${price} from {demand_org}"
        )

        logger.info(
            "Managed agent %s: %s proposal from %s ($%s)",
            self.agent_id, decision, demand_org, price,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                body: dict = {"decision": decision, "reasoning": reasoning}
                if decision == "counter" and result:
                    cp = result.get("counter_price", price * 1.2)
                    body["counter_terms"] = {
                        "price": {"amount": cp, "currency": "USD"},
                        "content_format": deal_terms.get("content_format", "gameday_graphic"),
                    }
                await client.post(
                    f"http://localhost:8080/api/v1/proposals/{proposal_id}/respond",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
        except Exception as e:
            logger.error("Managed agent %s: %s", self.agent_id, e)

    async def _handle_counter(self, data: dict):
        """Handle counter-offer — use Gemini to evaluate or fallback to budget check."""
        import httpx

        proposal_id = data.get("proposal_id")
        deal_id = data.get("deal_id", "")
        counter_terms = data.get("counter_terms", {})
        counter_price = counter_terms.get("price", {}).get("amount", 0)
        budget = self.agent_config.get("brand_profile", {}).get(
            "budget_per_deal_max", 5000,
        )

        # Try Gemini for nuanced evaluation
        user_msg = (
            f"The other party has counter-offered:\n"
            f"- Counter price: ${counter_price}\n"
            f"- Your budget limit: ${budget}\n"
            f"- Original terms: {counter_terms}\n\n"
            f"Accept or reject this counter-offer?"
        )
        result = await self._call_gemini(user_msg, deal_id)

        if result:
            decision = result.get("decision", "accept" if counter_price <= budget else "reject")
            reasoning = result.get("reasoning", "")
        else:
            # Fallback: simple budget check
            if counter_price <= budget:
                decision = "accept"
                reasoning = f"Counter of ${counter_price} within budget."
            else:
                decision = "reject"
                reasoning = f"Counter of ${counter_price} exceeds budget ${budget}."

        logger.info("Managed agent %s: %s counter ($%s)", self.agent_id, decision, counter_price)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"http://localhost:8080/api/v1/proposals/{proposal_id}/respond",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"decision": decision, "reasoning": reasoning},
                )
        except Exception as e:
            logger.error("Managed agent %s: %s", self.agent_id, e)

    async def _handle_brief(self, data: dict):
        """Handle creative brief — platform owns content generation in v3.

        The managed agent acknowledges receipt of the brief; the platform
        generates and validates the actual branded images.
        """
        deal_id = data.get("deal_id")
        logger.info(
            "Managed agent %s: received brief for %s — platform handles content generation",
            self.agent_id, deal_id,
        )
