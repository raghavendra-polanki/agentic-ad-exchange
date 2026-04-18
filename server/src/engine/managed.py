"""ManagedAgentRunner — runs an agent in-process using Claude.

For Path A (managed agents): human creates an agent via dashboard,
the platform runs it internally using Claude with the configured
brand persona as system prompt. Uses the store's notification queue
instead of HTTP webhooks.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from src.schemas.agents import AgentType, RegisterAgentRequest
from src.store import store

logger = logging.getLogger("aax.managed")

# Load API key from env or server/.env
ANTHROPIC_API_KEY = (
    os.getenv("ANTHROPIC_API_KEY")
    or os.getenv("AAX_ANTHROPIC_API_KEY")
    or ""
)

_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    if not ANTHROPIC_API_KEY:
        ANTHROPIC_API_KEY = (
            os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("AAX_ANTHROPIC_API_KEY")
            or ""
        )

USE_LLM = bool(ANTHROPIC_API_KEY)
if USE_LLM:
    from anthropic import Anthropic

    _llm = Anthropic(api_key=ANTHROPIC_API_KEY)


def _call_claude(system_prompt: str, user_message: str) -> dict | None:
    """Synchronous Claude call. Returns parsed JSON or None."""
    if not USE_LLM:
        return None
    try:
        resp = _llm.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        text = resp.content[0].text
        if "{" in text:
            return json.loads(text[text.index("{"):text.rindex("}") + 1])
    except Exception as e:
        logger.warning("Claude call failed for managed agent: %s", e)
    return None


# Registry of running managed agents
_runners: dict[str, "ManagedAgentRunner"] = {}


def get_runner(agent_id: str) -> "ManagedAgentRunner | None":
    return _runners.get(agent_id)


def get_all_runners() -> dict[str, "ManagedAgentRunner"]:
    return _runners


class ManagedAgentRunner:
    """Runs an agent in-process. Processes notifications from the store queue."""

    def __init__(
        self,
        org_id: str,
        agent_config: dict,
    ):
        self.org_id = org_id
        self.agent_config = agent_config
        self.agent_id: str | None = None
        self.api_key: str | None = None
        self.running = False
        self._task: asyncio.Task | None = None

        # Build persona prompt from config
        self.system_prompt = self._build_persona(agent_config)

    def _build_persona(self, config: dict) -> str:
        """Build a Claude system prompt from agent configuration."""
        agent_type = config.get("agent_type", "demand")
        name = config.get("name", "Agent")
        org = config.get("organization", "Unknown")
        desc = config.get("description", "")

        if agent_type == "demand":
            bp = config.get("brand_profile", {})
            return (
                f"You are {name}, an AI advertising agent for {org}.\n"
                f"Role: Demand agent — you evaluate content sponsorship "
                f"opportunities and decide whether to bid.\n"
                f"Brand tone: {bp.get('tone', 'professional')}\n"
                f"Tagline: {bp.get('tagline', '')}\n"
                f"Budget: up to ${bp.get('budget_per_deal_max', 5000)} "
                f"per deal\n"
                f"Competitors to avoid: "
                f"{', '.join(bp.get('competitor_exclusions', []))}\n"
                f"Description: {desc}\n\n"
                f"When evaluating opportunities, respond with JSON:\n"
                f'{{"should_bid": true, "price": 2000, '
                f'"reasoning": "detailed reasoning", '
                f'"scores": {{"audience_fit": 80, "brand_alignment": 85, '
                f'"price_adequacy": 75, "projected_roi": 70, '
                f'"overall": 78}}}}'
            )
        else:
            return (
                f"You are {name}, an AI content agent for {org}.\n"
                f"Role: Supply agent — you evaluate proposals from brands "
                f"wanting to sponsor your athlete content.\n"
                f"Description: {desc}\n"
                f"Minimum price: $500\n\n"
                f"When evaluating proposals, respond with JSON:\n"
                f'{{"decision": "accept", "reasoning": "detailed reasoning",'
                f' "counter_price": null}}'
            )

    async def start(self):
        """Register with exchange and start processing loop."""
        req = RegisterAgentRequest(
            agent_type=AgentType(
                self.agent_config.get("agent_type", "demand"),
            ),
            name=self.agent_config.get("name", "Managed Agent"),
            organization=self.agent_config.get("organization", "Unknown"),
            description=self.agent_config.get("description", ""),
            # No callback_url — notifications go to polling queue
        )

        # Add brand profile if demand agent
        if req.agent_type == AgentType.DEMAND:
            from src.schemas.agents import BrandProfile

            bp = self.agent_config.get("brand_profile", {})
            req.brand_profile = BrandProfile(**bp) if bp else None

        creds = store.register_agent(req, org_id=self.org_id)
        self.agent_id = creds.agent_id
        self.api_key = creds.api_key
        self.running = True

        _runners[self.agent_id] = self

        logger.info(
            "Managed agent started: %s (%s) — LLM=%s",
            self.agent_config.get("name"),
            self.agent_id,
            "ON" if USE_LLM else "OFF",
        )

        # Start processing loop
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

                # Poll every 500ms
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Managed agent %s error: %s", self.agent_id, e,
                )
                await asyncio.sleep(1)

    async def _handle_notification(self, notif: dict):
        """Process a single notification."""
        event_type = notif.get("event", "")
        data = notif.get("data", notif)

        logger.info(
            "Managed agent %s processing: %s",
            self.agent_id, event_type,
        )

        if event_type == "opportunity.matched":
            await self._handle_opportunity(data)
        elif event_type == "proposal.received":
            await self._handle_proposal(data)
        elif event_type == "counter.received":
            await self._handle_counter(data)
        elif event_type == "brief.generated":
            await self._handle_brief(data)
        else:
            logger.info(
                "Managed agent %s: unhandled event %s",
                self.agent_id, event_type,
            )

    async def _handle_opportunity(self, data: dict):
        """Evaluate opportunity and submit proposal if interested."""
        import httpx

        opp_id = data.get("opportunity_id")
        signal = data.get("signal", {})

        subjects = signal.get("subjects", [])
        athlete = subjects[0].get("athlete_name", "Unknown") if subjects else "Unknown"
        school = subjects[0].get("school", "") if subjects else ""

        user_msg = (
            f"Evaluate this content opportunity:\n"
            f"- Athlete: {athlete} ({school})\n"
            f"- Sport: {signal.get('sport', 'unknown')}\n"
            f"- Moment: {signal.get('content_description', '')}\n"
            f"- Reach: {signal.get('audience', {}).get('projected_reach', 0):,}\n"
            f"- Trending: {signal.get('audience', {}).get('trending_score', 0)}\n"
            f"- Min price: ${signal.get('min_price', 0)}\n"
            f"\nShould you bid? At what price?"
        )

        result = _call_claude(self.system_prompt, user_msg)

        if result and result.get("should_bid"):
            price = min(
                self.agent_config.get("brand_profile", {}).get(
                    "budget_per_deal_max", 5000,
                ),
                result.get("price", 1000),
            )
            reasoning = result.get("reasoning", "Managed agent bid")
            scores = result.get("scores", {})
        else:
            # Fallback: simple bid logic
            price = 1000
            reasoning = (
                result.get("reasoning", "")
                if result else "Automated bid from managed agent"
            )
            scores = {"overall": 60}
            if result and not result.get("should_bid"):
                logger.info("Managed agent %s: passing on %s", self.agent_id, opp_id)
                return

        logger.info(
            "Managed agent %s: bidding $%s on %s",
            self.agent_id, price, opp_id,
        )

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
                    logger.error(
                        "Managed agent %s: proposal failed %s",
                        self.agent_id, resp.text,
                    )
        except Exception as e:
            logger.error("Managed agent %s: %s", self.agent_id, e)

    async def _handle_proposal(self, data: dict):
        """Evaluate a proposal (supply agent role)."""
        import httpx

        proposal_id = data.get("proposal_id")
        demand_org = data.get("demand_org", "Unknown")
        deal_terms = data.get("deal_terms", {})
        price = deal_terms.get("price", {}).get("amount", 0)

        user_msg = (
            f"Evaluate this proposal:\n"
            f"- Brand: {demand_org}\n"
            f"- Price: ${price}\n"
            f"- Format: {deal_terms.get('content_format', 'unknown')}\n"
            f"\nAccept, counter, or reject?"
        )

        result = _call_claude(self.system_prompt, user_msg)
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
                body: dict = {
                    "decision": decision,
                    "reasoning": reasoning,
                }
                if decision == "counter" and result:
                    cp = result.get("counter_price", price * 1.2)
                    body["counter_terms"] = {
                        "price": {"amount": cp, "currency": "USD"},
                        "content_format": deal_terms.get(
                            "content_format", "gameday_graphic",
                        ),
                    }

                await client.post(
                    f"http://localhost:8080/api/v1/proposals/{proposal_id}/respond",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
        except Exception as e:
            logger.error("Managed agent %s: %s", self.agent_id, e)

    async def _handle_counter(self, data: dict):
        """Handle counter-offer — accept if within budget."""
        import httpx

        proposal_id = data.get("proposal_id")
        counter_terms = data.get("counter_terms", {})
        counter_price = counter_terms.get("price", {}).get("amount", 0)
        budget = self.agent_config.get("brand_profile", {}).get(
            "budget_per_deal_max", 5000,
        )

        if counter_price <= budget:
            decision = "accept"
            reasoning = f"Counter of ${counter_price} within budget."
        else:
            decision = "reject"
            reasoning = f"Counter of ${counter_price} exceeds budget ${budget}."

        logger.info(
            "Managed agent %s: %s counter ($%s)",
            self.agent_id, decision, counter_price,
        )

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
        """Handle creative brief — submit mock content."""
        import time

        import httpx

        deal_id = data.get("deal_id")
        content_url = (
            f"https://managed-agent.aax.example/content/"
            f"{deal_id}_{int(time.time())}.png"
        )

        logger.info(
            "Managed agent %s: submitting content for %s",
            self.agent_id, deal_id,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"http://localhost:8080/api/v1/content/{deal_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "content_url": content_url,
                        "format": "gameday_graphic",
                    },
                )
        except Exception as e:
            logger.error("Managed agent %s: %s", self.agent_id, e)
