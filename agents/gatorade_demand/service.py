"""Gatorade Demand Agent — sports hydration sponsorship for college athletics.

Demonstrates conflict blocking: the exchange will reject proposals when an
athlete already has a competing NIL deal (e.g. BodyArmor).
"""

import asyncio
import hashlib
import hmac
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, Request

logger = logging.getLogger("gatorade-agent")
logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

EXCHANGE_URL = os.getenv("AAX_EXCHANGE_URL", "http://localhost:8080")
ORG_KEY = os.getenv("AAX_ORG_KEY", "aax_org_gatorade_12345")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8083"))

# Agent state
credentials = {}

# Gatorade brand config
BUDGET_PER_DEAL = 3000
BRAND_PROFILE = {
    "tone": "energetic, performance-focused, authentic",
    "tagline": "Is It In You?",
    "target_demographics": {"age_range": "18-30", "interests": ["sports", "fitness", "hydration"]},
    "budget_per_deal_max": BUDGET_PER_DEAL,
    "budget_per_month_max": 25000,
    "competitor_exclusions": ["BodyArmor", "Powerade", "Prime Hydration"],
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
    "You are the Gatorade Sports Agent — representing Gatorade's sponsorship of college athletics.\n"
    'Brand: "Is It In You?" — energetic, performance-focused, authentic.\n'
    "Budget: up to $3,000 per deal.\n"
    "Competitors: BodyArmor, Powerade, Prime Hydration — NEVER sponsor alongside these.\n"
    "Focus: performance-driven moments — records, comebacks, peak athletic achievement."
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
                        f"Evaluate this sponsorship opportunity for Gatorade.\n"
                        f"Sport: {signal.get('sport', 'unknown')}\n"
                        f"Description: {signal.get('content_description', 'N/A')}\n"
                        f"Reach: {signal.get('audience', {}).get('projected_reach', 0):,}\n"
                        f"Trending: {signal.get('audience', {}).get('trending_score', 0)}\n"
                        f"Our score: {score}/100, proposed price: ${price:.0f}\n\n"
                        f"Give a 2-sentence take on whether this fits Gatorade's brand."
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
    async with httpx.AsyncClient(timeout=30.0) as client:
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
                "name": "Gatorade Sports Agent",
                "organization": "Gatorade",
                "description": "Seeking performance-driven college athletics content for Gatorade sponsorship",
                "callback_url": f"http://localhost:{AGENT_PORT}/webhook",
                "brand_profile": BRAND_PROFILE,
                "standing_queries": [
                    {"sport": "basketball", "min_reach": 30000},
                    {"sport": "football", "min_reach": 30000},
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
    logger.info("Gatorade agent shutting down")


app = FastAPI(title="Gatorade Demand Agent", lifespan=lifespan)


def verify_signature(body: bytes, signature: str | None) -> bool:
    secret = credentials.get("webhook_secret", "")
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def evaluate_opportunity(signal: dict) -> tuple[bool, float, str]:
    """Evaluate an opportunity. Returns (should_bid, price, reasoning)."""
    audience = signal.get("audience", {})
    reach = audience.get("projected_reach", 0)
    sport = signal.get("sport", "")
    description = signal.get("content_description", "").lower()
    trending = audience.get("trending_score", 0)

    score = 0
    reasons = []

    # Sport match — basketball and football are Gatorade's focus
    if sport in ("basketball", "football"):
        score += 30
        reasons.append(f"{sport} matches Gatorade's focus")
    else:
        score += 5
        reasons.append(f"{sport} is not a Gatorade priority sport")

    # Reach
    if reach >= 100000:
        score += 30
        reasons.append(f"Excellent reach ({reach:,})")
    elif reach >= 50000:
        score += 20
        reasons.append(f"Good reach ({reach:,})")
    elif reach >= 30000:
        score += 10
        reasons.append(f"Moderate reach ({reach:,})")

    # Trending
    if trending >= 7:
        score += 20
        reasons.append(f"High trending score ({trending})")
    elif trending >= 4:
        score += 10
        reasons.append(f"Moderate trending ({trending})")

    # Performance keywords
    performance_keywords = ["record", "comeback", "clutch", "MVP", "championship", "victory", "winning"]
    matched_keywords = [kw for kw in performance_keywords if kw.lower() in description]
    if matched_keywords:
        score += 20
        reasons.append(f"Performance keywords: {', '.join(matched_keywords)}")

    # Decision
    should_bid = score >= 50
    price = min(BUDGET_PER_DEAL, max(300, int(BUDGET_PER_DEAL * score / 100)))

    reasoning = f"Score: {score}/100. " + " | ".join(reasons)
    if should_bid:
        reasoning += f" → Bidding ${price}"
    else:
        reasoning += " → Passing (below threshold)"

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
            "CONFLICT BLOCKED: Proposal %s was rejected due to conflict: %s",
            payload.get("proposal_id"),
            payload.get("reason", "competitor exclusion"),
        )
        logger.warning(
            "Conflicting entity: %s — Gatorade cannot sponsor alongside competitors",
            payload.get("conflicting_entity", "unknown"),
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{EXCHANGE_URL}/api/v1/opportunities/{opportunity_id}/pass",
                headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
            )
        return {"status": "passed"}

    # Submit proposal
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/opportunities/{opportunity_id}/propose",
            headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
            json={
                "deal_terms": {
                    "price": {"amount": price, "currency": "USD"},
                    "content_format": "gameday_graphic",
                    "platforms": ["instagram", "twitter"],
                    "usage_rights_duration_days": 14,
                },
                "reasoning": reasoning,
                "scores": {
                    "audience_fit": 75,
                    "brand_alignment": 80,
                    "price_adequacy": 70,
                    "projected_roi": 65,
                    "overall": 72,
                },
            },
        )

        if resp.status_code == 200:
            data = resp.json()
            logger.info("Proposal submitted: %s", data)
            if data.get("status") == "conflict_blocked":
                logger.warning(
                    "CONFLICT BLOCKED at submission: %s",
                    data.get("reason", "competitor exclusion detected"),
                )
        else:
            logger.error("Proposal failed: %s %s", resp.status_code, resp.text)

    return {"status": "proposed", "price": price}


async def handle_counter(payload: dict):
    """Handle counter-offer. Accept if within budget."""
    proposal_id = payload.get("proposal_id")
    counter_terms = payload.get("counter_terms", {})
    counter_price = counter_terms.get("price", {}).get("amount", 0)

    logger.info("Counter received: $%.2f for proposal %s", counter_price, proposal_id)

    if counter_price <= BUDGET_PER_DEAL:
        decision = "accept"
        reasoning = f"Counter of ${counter_price} is within budget. Accepting."
    else:
        decision = "reject"
        reasoning = f"Counter of ${counter_price} exceeds budget of ${BUDGET_PER_DEAL}."

    logger.info("Decision: %s — %s", decision, reasoning)

    async with httpx.AsyncClient(timeout=30.0) as client:
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
        "agent": "Gatorade",
        "agent_id": credentials.get("agent_id"),
        "registered": bool(credentials.get("agent_id")),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
