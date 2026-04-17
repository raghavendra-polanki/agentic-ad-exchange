"""Nike Demand Agent — brand sponsorship for college athletics."""

import asyncio
import hashlib
import hmac
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, Request

logger = logging.getLogger("nike-agent")
logging.basicConfig(level=logging.INFO, format="%(name)s | %(message)s")

EXCHANGE_URL = os.getenv("AAX_EXCHANGE_URL", "http://localhost:8080")
ORG_KEY = os.getenv("AAX_ORG_KEY", "aax_org_nike_12345")
AGENT_PORT = int(os.getenv("AGENT_PORT", "8082"))

# Agent state
credentials = {}

# Nike brand config
BUDGET_PER_DEAL = 5000
BRAND_PROFILE = {
    "tone": "Bold, empowering, aspirational",
    "tagline": "Just Do It",
    "target_demographics": {"age_range": "18-35", "interests": ["sports", "athletics"]},
    "budget_per_deal_max": BUDGET_PER_DEAL,
    "budget_per_month_max": 50000,
    "competitor_exclusions": ["Adidas", "Under Armour", "New Balance"],
}


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
                "name": "Nike Basketball Agent",
                "organization": "Nike",
                "description": "Seeking premium basketball content moments for Nike sponsorship",
                "callback_url": f"http://localhost:{AGENT_PORT}/webhook",
                "brand_profile": BRAND_PROFILE,
                "standing_queries": [
                    {"sport": "basketball", "min_reach": 10000},
                    {"sport": "football", "min_reach": 50000},
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
    logger.info("Nike agent shutting down")


app = FastAPI(title="Nike Demand Agent", lifespan=lifespan)


def verify_signature(body: bytes, signature: str | None) -> bool:
    secret = credentials.get("webhook_secret", "")
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def evaluate_opportunity(signal: dict) -> tuple[bool, float, str]:
    """Evaluate an opportunity. Returns (should_bid, price, reasoning)."""
    description = signal.get("content_description", "")
    subjects = signal.get("subjects", [])
    audience = signal.get("audience", {})
    reach = audience.get("projected_reach", 0)
    sport = signal.get("sport", "")

    # Scoring logic
    score = 0
    reasons = []

    # Sport match
    if sport in ("basketball", "football"):
        score += 30
        reasons.append(f"{sport} matches Nike's focus")
    else:
        score += 10
        reasons.append(f"{sport} is secondary for Nike")

    # Reach
    if reach >= 100000:
        score += 30
        reasons.append(f"Strong reach ({reach:,})")
    elif reach >= 50000:
        score += 20
        reasons.append(f"Good reach ({reach:,})")
    elif reach >= 10000:
        score += 10
        reasons.append(f"Moderate reach ({reach:,})")

    # Content quality indicators
    if "milestone" in description.lower() or "record" in description.lower() or "1000" in description:
        score += 20
        reasons.append("Milestone narrative — strong storytelling potential")

    # Trending
    trending = audience.get("trending_score", 0)
    if trending >= 7:
        score += 20
        reasons.append(f"High trending score ({trending})")

    # Decision
    should_bid = score >= 40
    # Price scales with score
    price = min(BUDGET_PER_DEAL, max(500, int(BUDGET_PER_DEAL * score / 100)))

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
        return await handle_opportunity(payload)
    elif x_aax_event == "counter.received":
        return await handle_counter(payload)
    elif x_aax_event == "deal.agreed":
        logger.info("Deal agreed! deal_id=%s with %s",
                     payload.get("deal_id"), payload.get("supply_org"))
        return {"status": "acknowledged"}
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
        opportunity_id, supply_org,
        signal.get("content_description", "")[:80],
    )

    should_bid, price, reasoning = evaluate_opportunity(signal)
    logger.info("Evaluation: %s", reasoning)

    if not should_bid:
        # Pass on this opportunity
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
                    "content_format": "gameday_graphic",
                    "platforms": ["instagram", "twitter"],
                    "usage_rights_duration_days": 30,
                },
                "reasoning": reasoning,
                "scores": {
                    "audience_fit": 80,
                    "brand_alignment": 85,
                    "price_adequacy": 75,
                    "projected_roi": 70,
                    "overall": 78,
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
        "agent_id": credentials.get("agent_id"),
        "registered": bool(credentials.get("agent_id")),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
