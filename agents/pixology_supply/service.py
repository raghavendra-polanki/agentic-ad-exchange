"""Pixology Supply Agent — content creation service for college athletics."""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, Request

logger = logging.getLogger("pixology-agent")
logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

EXCHANGE_URL = os.getenv("AAX_EXCHANGE_URL", "http://localhost:8080")
ORG_KEY = os.getenv("AAX_ORG_KEY", "aax_org_pixology_12345")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8081"))

# ── Load .env from project root ──
from pathlib import Path
_env_file = Path(__file__).resolve().parent.parent.parent / "server" / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ── LLM Setup (Gemini) ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or ""
USE_LLM = bool(GEMINI_API_KEY)
if USE_LLM:
    from google import genai
    from google.genai import types
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

PIXOLOGY_SYSTEM_PROMPT = """You are Pixology's autonomous content creation agent — premium graphics for college athletes.

## Your Identity
- Service: Gameday graphics, social posts, highlight reels
- Quality: Broadcast-grade, NCAA-compliant
- Turnaround: 45 minutes standard, 2 hours premium composite
- Min price: $500 (below this, not worth production effort)
- Athletes: You protect their image and reputation above all

## Your Strategy
- Tier 3 commands premium — compositing work is expensive
- Prefer repeat brand partners (Nike, premium brands)
- Reject brands that could harm athlete's NIL value
- Counter aggressively on Tier 3 — brands need YOU more

## Your Evaluation Framework
When evaluating a proposal, think through:
1. PRICE: Is it fair for the tier and production effort?
2. BRAND SAFETY: Will this brand help or hurt the athlete?
3. CREATIVE FEASIBILITY: Can you produce natural content at this tier?
4. USAGE RIGHTS: Shorter is better. Push for 14 days max.
5. TIMELINE: Can you deliver before the moment goes stale?

## Your Negotiation Style
- Never accept first offer on Tier 3 (always counter up)
- Accept first offer on Tier 1 if price >= $500
- Counter with specific reasoning
- Reject anything below $400 outright

Respond with ONLY a JSON object:
{"decision": "accept"|"counter"|"reject", "reasoning": "detailed reasoning", "counter_price": null}
For counter: {"decision": "counter", "reasoning": "why", "counter_price": 750}"""

COUNTER_EVAL_PROMPT = """You are Pixology's autonomous content creation agent evaluating a counter-offer.

The demand agent has counter-offered after your previous counter.
Your minimum acceptable price is $500. You protect athlete value above all.

Consider: is this price fair for the production work involved?
If it meets your minimum and the brand is reasonable, accept.
If it's below your minimum, reject.

Respond with ONLY a JSON object:
{"decision": "accept"|"reject", "reasoning": "detailed reasoning"}"""


async def post_thought(thought_text: str, context: dict):
    """Fire-and-forget: post a reasoning chunk to the exchange."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{EXCHANGE_URL}/api/v1/agents/thinking",
                headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
                json={
                    "agent_id": credentials.get("agent_id", ""),
                    "thought": thought_text,
                    "context": context,
                },
            )
    except Exception:
        pass  # fire-and-forget


async def evaluate_with_gemini(user_message: str, context: dict | None = None) -> dict | None:
    """Call Gemini for evaluation with streaming thoughts. Returns parsed JSON or None on failure."""
    if not USE_LLM:
        return None

    full_prompt = f"{PIXOLOGY_SYSTEM_PROMPT}\n\n{user_message}"
    ctx = context or {}

    try:
        response_text = ""
        for chunk in gemini_client.models.generate_content_stream(
            model="gemini-3-flash-preview",
            contents=[types.Part.from_text(text=full_prompt)],
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
                thinking_config=types.ThinkingConfig(thinking_budget=4096),
            ),
        ):
            for part in chunk.candidates[0].content.parts:
                if part.thought:
                    # Post reasoning to exchange (fire-and-forget)
                    asyncio.create_task(post_thought(part.text, ctx))
                else:
                    response_text += part.text

        if "{" in response_text:
            json_str = response_text[response_text.index("{"):response_text.rindex("}") + 1]
            return json.loads(json_str)
    except Exception as e:
        logger.warning("Gemini call failed: %s, using fallback", e)
    return None


async def evaluate_counter_with_gemini(counter_price: float, context: dict | None = None) -> dict | None:
    """Call Gemini to evaluate a counter-offer. Returns parsed JSON or None on failure."""
    if not USE_LLM:
        return None

    user_message = (
        f"The demand agent has counter-offered:\n"
        f"- Their counter price: ${counter_price:.0f}\n"
        f"- Your minimum: $500\n"
        f"\nAccept or reject? Consider: is this price fair for the work involved?"
    )
    full_prompt = f"{COUNTER_EVAL_PROMPT}\n\n{user_message}"
    ctx = context or {}

    try:
        response_text = ""
        for chunk in gemini_client.models.generate_content_stream(
            model="gemini-3-flash-preview",
            contents=[types.Part.from_text(text=full_prompt)],
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_budget=2048),
            ),
        ):
            for part in chunk.candidates[0].content.parts:
                if part.thought:
                    asyncio.create_task(post_thought(part.text, ctx))
                else:
                    response_text += part.text

        if "{" in response_text:
            json_str = response_text[response_text.index("{"):response_text.rindex("}") + 1]
            return json.loads(json_str)
    except Exception as e:
        logger.warning("Gemini counter-eval failed: %s, using fallback", e)
    return None


# Agent state
credentials: dict = {}
MIN_ACCEPTABLE_PRICE = 500  # Minimum price to accept a proposal


async def onboard():
    """Register as supply agent on the exchange."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Read protocol
        logger.info("Reading protocol from %s/protocol.md ...", EXCHANGE_URL)
        resp = await client.get(f"{EXCHANGE_URL}/protocol.md")
        if resp.status_code == 200:
            logger.info("Protocol loaded (%d bytes)", len(resp.text))

        # Register
        logger.info("Registering as supply agent...")
        reg_resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/agents/register",
            headers={"Authorization": f"Bearer {ORG_KEY}"},
            json={
                "agent_type": "supply",
                "name": "Pixology Content Agent",
                "organization": "Pixology",
                "description": "Creates gameday graphics, social posts, and highlight reels for college athletes",
                "callback_url": f"http://localhost:{AGENT_PORT}/webhook",
                "supply_capabilities": {
                    "content_formats": ["gameday_graphic", "social_post", "highlight_reel"],
                    "sports": ["basketball", "football", "soccer"],
                    "turnaround_minutes": 45,
                },
            },
        )

        if reg_resp.status_code == 200:
            data = reg_resp.json()
            credentials.update(data)
            logger.info("Registered! agent_id=%s", data.get("agent_id"))
        else:
            logger.error("Registration failed: %s %s", reg_resp.status_code, reg_resp.text)
            return

        # Wait a moment, then signal a test opportunity
        await asyncio.sleep(10)  # Wait for other agents to register first
        await signal_test_opportunity(client)


async def signal_test_opportunity(client: httpx.AsyncClient):
    """Signal a test opportunity to the exchange."""
    logger.info("Signaling test opportunity: Jane Doe 1000th career point...")
    resp = await client.post(
        f"{EXCHANGE_URL}/api/v1/opportunities/",
        headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
        json={
            "content_description": "Jane Doe scores 1000th career point — MIT Women's Basketball milestone moment",
            "subjects": [
                {"athlete_name": "Jane Doe", "school": "MIT", "sport": "basketball"}
            ],
            "audience": {
                "projected_reach": 150000,
                "demographics": "College basketball fans, MIT alumni, women's sports enthusiasts",
                "trending_score": 8.5,
            },
            "available_formats": ["gameday_graphic", "social_post", "highlight_reel"],
            "min_price": 500,
            "sport": "basketball",
            "image_id": "basketball_dunk",
            "image_url": "/static/demo/basketball_dunk.jpg",
        },
    )

    if resp.status_code == 200:
        data = resp.json()
        logger.info(
            "Opportunity listed! opportunity_id=%s, matched=%d agents",
            data.get("opportunity_id"),
            data.get("matched_count", 0),
        )
    else:
        logger.error("Failed to signal opportunity: %s %s", resp.status_code, resp.text)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("LLM mode: %s", "ON (Gemini)" if USE_LLM else "OFF (hardcoded fallback)")
    await onboard()
    yield
    logger.info("Pixology agent shutting down")


app = FastAPI(title="Pixology Supply Agent", lifespan=lifespan)


def verify_signature(body: bytes, signature: str | None) -> bool:
    secret = credentials.get("webhook_secret", "")
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_aax_signature: str | None = Header(None),
    x_aax_event: str | None = Header(None),
):
    """Receive webhooks from AAX exchange."""
    body = await request.body()

    if x_aax_signature and not verify_signature(body, x_aax_signature):
        logger.warning("Webhook signature verification FAILED for %s", x_aax_event)

    payload = await request.json()
    logger.info("Webhook received: %s", x_aax_event)

    if x_aax_event == "proposal.received":
        asyncio.create_task(handle_proposal(payload))
        return {"status": "processing"}
    elif x_aax_event == "counter.received":
        asyncio.create_task(handle_counter(payload))
        return {"status": "processing"}
    elif x_aax_event == "brief.generated":
        asyncio.create_task(handle_brief(payload))
        return {"status": "processing"}
    elif x_aax_event == "content.revision_requested":
        asyncio.create_task(handle_revision(payload))
        return {"status": "processing"}
    elif x_aax_event == "deal.agreed":
        logger.info("Deal agreed! deal_id=%s", payload.get("deal_id"))
        return {"status": "acknowledged"}
    elif x_aax_event == "deal.completed":
        logger.info("Deal completed! deal_id=%s — content delivered", payload.get("deal_id"))
        return {"status": "acknowledged"}
    else:
        logger.info("Unhandled event: %s", x_aax_event)
        return {"status": "received"}


async def handle_brief(payload: dict):
    """Handle a creative brief — the platform generates branded content.

    In v3, the platform agent generates branded images using Gemini.
    The supply agent acknowledges the brief and waits for content options
    to review rather than generating content itself.
    """
    deal_id = payload.get("deal_id")
    brief = payload.get("brief", {})
    logger.info(
        "Brief received for deal %s: %s for %s — platform will generate branded content",
        deal_id,
        brief.get("moment_description"),
        brief.get("brand_name"),
    )
    # Platform handles content generation via Gemini image gen.
    # We'll receive content options to review once they're ready.


async def handle_revision(payload: dict):
    """Handle a content revision request."""
    deal_id = payload.get("deal_id")
    issues = payload.get("validation_issues", [])
    logger.info("Revision requested for deal %s: %s — platform will regenerate", deal_id, issues)

    # Resubmit to exchange
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{EXCHANGE_URL}/api/v1/content/{deal_id}",
                headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
                json={"content_url": content_url, "format": "gameday_graphic"},
            )
            if resp.status_code == 200:
                logger.info("Revised content submitted: %s", resp.json())
            else:
                logger.error("Revised content submission failed: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.error("Failed to submit revised content: %s", e)


async def handle_proposal(payload: dict):
    """Evaluate a proposal from a demand agent."""
    proposal_id = payload.get("proposal_id")
    demand_org = payload.get("demand_org", "Unknown")
    deal_terms = payload.get("deal_terms", {})
    price = deal_terms.get("price", {}).get("amount", 0)

    logger.info(
        "Evaluating proposal from %s: $%.2f (proposal_id=%s)",
        demand_org,
        price,
        proposal_id,
    )

    # Try Gemini first
    decision = None
    reasoning = ""
    counter_price = None

    if USE_LLM:
        user_msg = (
            f"Evaluate this proposal:\n"
            f"- Brand: {demand_org}\n"
            f"- Price offered: ${price:.0f}\n"
            f"- Content format: {deal_terms.get('content_format', 'unknown')}\n"
            f"- Platforms: {deal_terms.get('platforms', [])}\n"
            f"- Usage rights: {deal_terms.get('usage_rights_duration_days', 'N/A')} days\n"
            f"- Your minimum price: ${MIN_ACCEPTABLE_PRICE}\n"
            f"\nShould we accept, counter, or reject?"
        )
        result = await evaluate_with_gemini(user_msg, context={
            "proposal_id": proposal_id,
            "demand_org": demand_org,
            "action": "evaluate_proposal",
        })
        if result:
            decision = result.get("decision", "reject")
            reasoning = result.get("reasoning", "")
            counter_price = result.get("counter_price")
            logger.info("Gemini evaluation: %s", decision)

    # Fallback: price-based logic
    if decision is None:
        if price >= MIN_ACCEPTABLE_PRICE:
            decision = "accept"
            reasoning = (
                f"Price ${price:.0f} meets our minimum of ${MIN_ACCEPTABLE_PRICE}. "
                f"{demand_org} is a good brand partner. Accepting."
            )
        elif price >= MIN_ACCEPTABLE_PRICE * 0.7:
            decision = "counter"
            reasoning = (
                f"Price ${price:.0f} is below our minimum of ${MIN_ACCEPTABLE_PRICE} "
                f"but close enough to counter."
            )
            counter_price = MIN_ACCEPTABLE_PRICE
        else:
            decision = "reject"
            reasoning = f"Price ${price:.0f} is too far below our minimum of ${MIN_ACCEPTABLE_PRICE}."

    logger.info("Decision: %s — %s", decision, reasoning)

    # Submit response to exchange
    async with httpx.AsyncClient(timeout=30.0) as client:
        response_body: dict = {
            "decision": decision,
            "reasoning": reasoning,
        }
        if decision == "counter":
            response_body["counter_terms"] = {
                "price": {"amount": counter_price or MIN_ACCEPTABLE_PRICE, "currency": "USD"},
                "content_format": deal_terms.get("content_format", "gameday_graphic"),
                "usage_rights_duration_days": 14,
            }

        resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/proposals/{proposal_id}/respond",
            headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
            json=response_body,
        )

        if resp.status_code == 200:
            logger.info("Response submitted: %s", resp.json())
        else:
            logger.error("Failed to respond: %s %s", resp.status_code, resp.text)

    return {"status": decision}


async def handle_counter(payload: dict):
    """Handle a counter-offer from demand agent — evaluate with Gemini."""
    proposal_id = payload.get("proposal_id")
    counter_terms = payload.get("counter_terms") or {}
    counter_price = (counter_terms.get("price") or {}).get("amount", 0)
    demand_org = payload.get("demand_org", "Unknown")

    logger.info(
        "Counter received for proposal %s from %s: $%.2f",
        proposal_id,
        demand_org,
        counter_price,
    )

    # Try Gemini evaluation
    decision = None
    reasoning = ""

    if USE_LLM:
        result = await evaluate_counter_with_gemini(counter_price, context={
            "proposal_id": proposal_id,
            "demand_org": demand_org,
            "action": "evaluate_counter",
        })
        if result:
            decision = result.get("decision", "reject")
            reasoning = result.get("reasoning", "")
            logger.info("Gemini counter evaluation: %s", decision)

    # Fallback: price-based logic
    if decision is None:
        if counter_price >= MIN_ACCEPTABLE_PRICE:
            decision = "accept"
            reasoning = (
                f"Counter price ${counter_price:.0f} meets our minimum of "
                f"${MIN_ACCEPTABLE_PRICE}. Accepting."
            )
        else:
            decision = "reject"
            reasoning = (
                f"Counter price ${counter_price:.0f} is below our minimum of "
                f"${MIN_ACCEPTABLE_PRICE}. Cannot accept."
            )

    logger.info("Counter decision: %s — %s", decision, reasoning)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/proposals/{proposal_id}/respond",
            headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
            json={"decision": decision, "reasoning": reasoning},
        )
        if resp.status_code == 200:
            logger.info("Counter response submitted: %s", resp.json())
        else:
            logger.error("Failed to respond to counter: %s %s", resp.status_code, resp.text)

    return {"status": decision}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent_id": credentials.get("agent_id"),
        "registered": bool(credentials.get("agent_id")),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
