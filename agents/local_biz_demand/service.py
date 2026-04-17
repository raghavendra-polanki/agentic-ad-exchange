"""Campus Pizza Demand Agent — small local business with limited budget.

Demonstrates conservative bidding: only targets affordable, local opportunities
with small reach requirements. Skips expensive national-level deals.
"""

import asyncio
import hashlib
import hmac
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, Request

logger = logging.getLogger("campus-pizza-agent")
logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

EXCHANGE_URL = os.getenv("AAX_EXCHANGE_URL", "http://localhost:8080")
ORG_KEY = os.getenv("AAX_ORG_KEY", "aax_org_campus_pizza_12345")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8084"))

# Agent state
credentials = {}

# Campus Pizza brand config
BUDGET_PER_DEAL = 200
BRAND_PROFILE = {
    "tone": "casual, fun, community-driven",
    "tagline": "Fuel Your Game Day",
    "target_demographics": {"age_range": "18-24", "interests": ["college", "pizza", "game day"]},
    "budget_per_deal_max": BUDGET_PER_DEAL,
    "budget_per_month_max": 1000,
    "competitor_exclusions": ["Dominos", "Papa Johns"],
}

# ── Load .env from project root ──
from pathlib import Path
_env_file = Path(__file__).resolve().parent.parent.parent / "server" / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# Claude reasoning support
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("AAX_ANTHROPIC_API_KEY") or ""
SYSTEM_PROMPT = (
    "You are Campus Pizza's ad agent — a small pizza shop near MIT campus.\n"
    "Budget: VERY limited, max $200 per deal.\n"
    "Target: MIT athletes only, local student audience.\n"
    "You're looking for affordable, community-focused sponsorship moments.\n"
    "Skip expensive or national-level opportunities — they're not for you."
)


async def get_llm_reasoning(signal: dict, score: int, price: float) -> str | None:
    """Ask Claude for reasoning on the opportunity, if API key is set."""
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        resp = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Evaluate this sponsorship opportunity for Campus Pizza.\n"
                        f"Sport: {signal.get('sport', 'unknown')}\n"
                        f"School: {signal.get('school', 'unknown')}\n"
                        f"Description: {signal.get('content_description', 'N/A')}\n"
                        f"Reach: {signal.get('audience', {}).get('projected_reach', 0):,}\n"
                        f"Min price: ${signal.get('min_price', 'N/A')}\n"
                        f"Our score: {score}/100, proposed price: ${price:.0f}\n\n"
                        f"Give a 2-sentence take on whether this is worth it for a small local pizza shop."
                    ),
                }
            ],
        )
        return resp.content[0].text
    except Exception as e:
        logger.warning("LLM reasoning failed: %s", e)
        return None


async def onboard():
    """Register as demand agent on the exchange."""
    async with httpx.AsyncClient() as client:
        logger.info("Reading protocol from %s/protocol.md ...", EXCHANGE_URL)
        resp = await client.get(f"{EXCHANGE_URL}/protocol.md")
        if resp.status_code == 200:
            logger.info("Protocol loaded (%d bytes)", len(resp.text))

        logger.info("Registering as demand agent...")
        reg_resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/agents/register",
            headers={"Authorization": f"Bearer {ORG_KEY}"},
            json={
                "agent_type": "demand",
                "name": "Campus Pizza Game Day Agent",
                "organization": "Campus Pizza",
                "description": "Affordable local sponsorship for MIT college athletics",
                "callback_url": f"http://localhost:{AGENT_PORT}/webhook",
                "brand_profile": BRAND_PROFILE,
                "standing_queries": [
                    {"sport": "all", "min_reach": 5000},
                ],
            },
        )

        if reg_resp.status_code == 200:
            data = reg_resp.json()
            credentials.update(data)
            logger.info("Registered! agent_id=%s", data.get("agent_id"))
            logger.info("Constraints: %s", data.get("constraints"))
        else:
            logger.error("Registration failed: %s %s", reg_resp.status_code, reg_resp.text)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await onboard()
    yield
    logger.info("Campus Pizza agent shutting down")


app = FastAPI(title="Campus Pizza Demand Agent", lifespan=lifespan)


def verify_signature(body: bytes, signature: str | None) -> bool:
    secret = credentials.get("webhook_secret", "")
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def evaluate_opportunity(signal: dict) -> tuple[bool, float, str]:
    """Evaluate an opportunity. Very conservative — small budget local business."""
    audience = signal.get("audience", {})
    reach = audience.get("projected_reach", 0)
    sport = signal.get("sport", "")
    school = signal.get("school", "").lower()
    min_price = signal.get("min_price", 0)
    content_format = signal.get("content_format", "")

    score = 0
    reasons = []

    # School match — MIT is our home turf
    if "mit" in school:
        score += 40
        reasons.append("MIT athlete — our local community!")
    else:
        score += 10
        reasons.append(f"Non-MIT school ({signal.get('school', 'unknown')})")

    # Sport popularity for campus engagement
    popular_sports = ["basketball", "football", "soccer", "hockey"]
    if sport in popular_sports:
        score += 20
        reasons.append(f"{sport} drives campus buzz")
    else:
        score += 5
        reasons.append(f"{sport} has limited campus draw")

    # Price — we need it cheap
    if min_price and min_price < 300:
        score += 20
        reasons.append(f"Affordable min price (${min_price})")
    elif min_price and min_price >= 300:
        score -= 10
        reasons.append(f"Too expensive (min ${min_price})")

    # Content format — social posts are our sweet spot
    if content_format == "social_post":
        score += 20
        reasons.append("Social post format — perfect for local reach")
    elif content_format:
        score += 5
        reasons.append(f"Format: {content_format}")

    # Hard pass on huge reach opportunities (they'll be too expensive)
    if reach > 200000:
        score -= 20
        reasons.append(f"Reach too large ({reach:,}) — national-level, not for us")

    # Decision
    should_bid = score >= 50
    price = min(BUDGET_PER_DEAL, max(50, score * 2))

    reasoning = f"Score: {score}/100. " + " | ".join(reasons)
    if should_bid:
        reasoning += f" → Bidding ${price}"
    else:
        reasoning += " → Passing (too expensive or not local enough)"

    return should_bid, price, reasoning


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

    if x_aax_event == "opportunity.matched":
        asyncio.create_task(handle_opportunity(payload))
        return {"status": "processing"}
    elif x_aax_event == "counter.received":
        asyncio.create_task(handle_counter(payload))
        return {"status": "processing"}
    elif x_aax_event == "deal.agreed":
        logger.info(
            "Deal agreed! deal_id=%s with %s",
            payload.get("deal_id"),
            payload.get("supply_org"),
        )
        return {"status": "acknowledged"}
    elif x_aax_event == "proposal.conflict_blocked":
        logger.warning(
            "CONFLICT BLOCKED: Proposal %s — reason: %s",
            payload.get("proposal_id"),
            payload.get("reason", "unknown"),
        )
        return {"status": "acknowledged_conflict"}
    else:
        logger.info("Unhandled event: %s", x_aax_event)
        return {"status": "received"}


async def handle_opportunity(payload: dict):
    """Evaluate an opportunity and submit proposal if interested."""
    opportunity_id = payload.get("opportunity_id")
    signal = payload.get("signal", {})
    supply_org = payload.get("supply_org", "Unknown")

    logger.info(
        "Evaluating opportunity %s from %s: %s",
        opportunity_id,
        supply_org,
        signal.get("content_description", "")[:80],
    )

    should_bid, price, reasoning = evaluate_opportunity(signal)

    # Optionally enhance reasoning with Claude
    llm_reasoning = await get_llm_reasoning(signal, int(price / BUDGET_PER_DEAL * 100), price)
    if llm_reasoning:
        reasoning += f" | Claude: {llm_reasoning}"

    logger.info("Evaluation: %s", reasoning)

    if not should_bid:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{EXCHANGE_URL}/api/v1/opportunities/{opportunity_id}/pass",
                headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
            )
        return {"status": "passed"}

    # Submit proposal
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/opportunities/{opportunity_id}/propose",
            headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
            json={
                "deal_terms": {
                    "price": {"amount": price, "currency": "USD"},
                    "content_format": "social_post",
                    "platforms": ["instagram"],
                    "usage_rights_duration_days": 7,
                },
                "reasoning": reasoning,
                "scores": {
                    "audience_fit": 60,
                    "brand_alignment": 65,
                    "price_adequacy": 90,
                    "projected_roi": 55,
                    "overall": 62,
                },
            },
        )

        if resp.status_code == 200:
            data = resp.json()
            logger.info("Proposal submitted: %s", data)
        else:
            logger.error("Proposal failed: %s %s", resp.status_code, resp.text)

    return {"status": "proposed", "price": price}


async def handle_counter(payload: dict):
    """Handle counter-offer. Very price-sensitive — only accept if cheap."""
    proposal_id = payload.get("proposal_id")
    counter_terms = payload.get("counter_terms", {})
    counter_price = counter_terms.get("price", {}).get("amount", 0)

    logger.info("Counter received: $%.2f for proposal %s", counter_price, proposal_id)

    if counter_price <= BUDGET_PER_DEAL:
        decision = "accept"
        reasoning = f"Counter of ${counter_price} fits our small budget. Accepting."
    else:
        decision = "reject"
        reasoning = f"Counter of ${counter_price} exceeds our max of ${BUDGET_PER_DEAL}. Way too expensive for a local pizza shop."

    logger.info("Decision: %s — %s", decision, reasoning)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/proposals/{proposal_id}/respond",
            headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
            json={"decision": decision, "reasoning": reasoning},
        )
        if resp.status_code == 200:
            logger.info("Response: %s", resp.json())

    return {"status": decision}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": "Campus Pizza",
        "agent_id": credentials.get("agent_id"),
        "registered": bool(credentials.get("agent_id")),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
