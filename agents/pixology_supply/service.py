"""Pixology Supply Agent — content creation service for college athletics."""

import asyncio
import hashlib
import hmac
import json
import logging
import os
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

# ── LLM Setup ──
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("AAX_ANTHROPIC_API_KEY") or ""
USE_LLM = bool(ANTHROPIC_API_KEY)
if USE_LLM:
    from anthropic import Anthropic
    llm_client = Anthropic(api_key=ANTHROPIC_API_KEY)

PIXOLOGY_SYSTEM_PROMPT = """You are the Pixology Content Agent — a premium content creation service for college athletics.
You create gameday graphics, social posts, and highlight reels for athletes.
Your minimum acceptable price is $500.

When evaluating a brand's proposal to sponsor your content, consider:
- Is the price fair for the content quality and athlete's reach?
- Does the brand align with college athletics values?
- Are the usage rights reasonable (shorter is better for you)?
- Is the brand reputable and a good partner for your athletes?

Respond with ONLY a JSON object (no other text):
{"decision": "accept", "reasoning": "detailed reasoning here", "counter_price": null}
For counter: {"decision": "counter", "reasoning": "why countering", "counter_price": 750}
For reject: {"decision": "reject", "reasoning": "why rejecting", "counter_price": null}"""


async def evaluate_with_claude(user_message: str) -> dict | None:
    """Call Claude for evaluation. Returns parsed JSON or None on failure."""
    if not USE_LLM:
        return None
    try:
        response = llm_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=PIXOLOGY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text
        if "{" in text:
            json_str = text[text.index("{"):text.rindex("}") + 1]
            return json.loads(json_str)
    except Exception as e:
        logger.warning("Claude call failed: %s, using fallback", e)
    return None

# Agent state
credentials: dict = {}
MIN_ACCEPTABLE_PRICE = 500  # Minimum price to accept a proposal


async def onboard():
    """Register as supply agent on the exchange."""
    async with httpx.AsyncClient() as client:
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
        await asyncio.sleep(3)
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
    logger.info("LLM mode: %s", "ON" if USE_LLM else "OFF (hardcoded fallback)")
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
    elif x_aax_event == "deal.agreed":
        logger.info("Deal agreed! deal_id=%s", payload.get("deal_id"))
        return {"status": "acknowledged"}
    else:
        logger.info("Unhandled event: %s", x_aax_event)
        return {"status": "received"}


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

    # Try Claude first
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
        result = await evaluate_with_claude(user_msg)
        if result:
            decision = result.get("decision", "reject")
            reasoning = result.get("reasoning", "")
            counter_price = result.get("counter_price")
            logger.info("Claude evaluation: %s", decision)

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
    async with httpx.AsyncClient() as client:
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
    """Handle a counter-offer — for now, accept any counter."""
    proposal_id = payload.get("proposal_id")
    logger.info("Counter received for proposal %s — accepting", proposal_id)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/proposals/{proposal_id}/respond",
            headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
            json={"decision": "accept", "reasoning": "Counter terms acceptable."},
        )
        if resp.status_code == 200:
            logger.info("Accepted counter: %s", resp.json())

    return {"status": "accepted"}


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
