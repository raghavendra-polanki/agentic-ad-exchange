"""Gatorade Demand Agent — sports hydration sponsorship for college athletics.

Demonstrates conflict blocking: the exchange will reject proposals when an
athlete already has a competing NIL deal (e.g. BodyArmor).

Uses Gemini for LLM reasoning with streaming thoughts.
"""

import asyncio
import hashlib
import hmac
import json
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
    llm_client = genai.Client(api_key=GEMINI_API_KEY)

GATORADE_SYSTEM_PROMPT = """You are Gatorade's autonomous sponsorship agent for college athletics.

## Your Identity
- Brand: Gatorade — "Is It In You?"
- Tone: Energetic, performance-focused, authentic
- Budget: up to $3,000 per deal, $25,000/month
- Competitors: BodyArmor, Powerade, Prime Hydration (NEVER co-sponsor)

## Your Strategy
- Focus on performance-driven moments (records, comebacks, peak achievement)
- Basketball and football are primary sports
- Hydration/energy moments are perfect (post-game, training, halftime)
- Walk away from lifestyle/ceremony moments (not brand-aligned)

## Your Evaluation Framework
1. PERFORMANCE FIT: Is this a peak athletic performance moment?
2. HYDRATION RELEVANCE: Can hydration/energy be naturally placed?
3. AUDIENCE: Is reach > 30k in target demographics?
4. PRICE: Keep under $3,000 — Gatorade is disciplined
5. COMPETITION: Any conflict with BodyArmor/Powerade NIL deals?

## Negotiation Style
- Moderate bidder — not aggressive like Nike
- Accept if price is fair, don't over-negotiate
- Reject quickly if moment doesn't fit (save budget for better ones)

Respond with ONLY JSON:
{"should_bid": true, "price": 1500, "reasoning": "...", "scores": {"audience_fit": 75, "brand_alignment": 80, "price_adequacy": 70, "projected_roi": 65, "overall": 72}}"""

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


async def post_thinking(thought_chunk: str, deal_id: str | None = None):
    """Post agent thinking to the exchange for dashboard visibility."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{EXCHANGE_URL}/api/v1/agents/thinking",
                headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
                json={"thought_chunk": thought_chunk, "deal_id": deal_id},
            )
    except Exception as e:
        logger.debug("Failed to post thinking: %s", e)


async def evaluate_with_gemini(user_message: str, deal_id: str | None = None) -> dict | None:
    """Call Gemini for evaluation with streaming thoughts. Returns parsed JSON or None."""
    if not USE_LLM:
        return None
    try:
        full_prompt = f"{GATORADE_SYSTEM_PROMPT}\n\n{user_message}"
        response_text = ""

        for chunk in llm_client.models.generate_content_stream(
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
                    await post_thinking(part.text, deal_id)
                else:
                    response_text += part.text

        # Parse JSON from response
        if "{" in response_text:
            json_str = response_text[response_text.index("{"):response_text.rindex("}") + 1]
            return json.loads(json_str)
    except Exception as e:
        logger.warning("Gemini call failed: %s, using fallback", e)
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
    logger.info("LLM mode: %s", "Gemini ON" if USE_LLM else "OFF (hardcoded fallback)")
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


async def evaluate_opportunity(signal: dict, deal_id: str | None = None) -> tuple[bool, float, str, dict | None]:
    """Evaluate an opportunity. Returns (should_bid, price, reasoning, scores)."""
    # Try Gemini first
    if USE_LLM:
        subjects = signal.get("subjects", [])
        athlete = subjects[0].get("athlete_name", "Unknown") if subjects else "Unknown"
        school = subjects[0].get("school", "") if subjects else ""
        user_msg = (
            f"Evaluate this content opportunity for Gatorade:\n"
            f"- Athlete: {athlete} ({school})\n"
            f"- Sport: {signal.get('sport', 'unknown')}\n"
            f"- Moment: {signal.get('content_description', '')}\n"
            f"- Audience reach: {signal.get('audience', {}).get('projected_reach', 0):,}\n"
            f"- Trending score: {signal.get('audience', {}).get('trending_score', 0)}\n"
            f"- Min price: ${signal.get('min_price', 0)}\n"
            f"- Available formats: {signal.get('available_formats', [])}\n"
            f"\nShould Gatorade bid? If yes, at what price (max $3,000)?"
        )
        result = await evaluate_with_gemini(user_msg, deal_id)
        if result:
            should_bid = result.get("should_bid", False)
            price = min(BUDGET_PER_DEAL, result.get("price", 0))
            reasoning = result.get("reasoning", "")
            scores = result.get("scores")
            logger.info("Gemini evaluation: bid=%s, $%s", should_bid, price)
            return should_bid, price, reasoning, scores

    # Fallback: hardcoded scoring
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

    scores_dict = {
        "audience_fit": min(100, int(reach / 2000)),
        "brand_alignment": 80 if sport in ("basketball", "football") else 40,
        "price_adequacy": 70,
        "projected_roi": min(100, int(trending * 10)) if trending else 50,
        "overall": score,
    }

    return should_bid, price, reasoning, scores_dict


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

    should_bid, price, reasoning, scores = await evaluate_opportunity(signal, opportunity_id)
    logger.info("Evaluation: %s", reasoning)

    if not should_bid:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{EXCHANGE_URL}/api/v1/opportunities/{opportunity_id}/pass",
                headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
                json={"reasoning": reasoning},
            )
        return {"status": "passed"}

    # Submit proposal
    try:
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
                    "scores": scores or {
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
    except Exception as e:
        logger.error("Failed to submit proposal: %s", e)

    return {"status": "proposed", "price": price}


async def handle_counter(payload: dict):
    """Handle counter-offer. Accept if within budget."""
    proposal_id = payload.get("proposal_id")
    counter_terms = payload.get("counter_terms") or {}
    counter_price = (counter_terms.get("price") or {}).get("amount", 0)

    logger.info("Counter received: $%.2f for proposal %s", counter_price, proposal_id)

    if counter_price <= BUDGET_PER_DEAL:
        decision = "accept"
        reasoning = f"Counter of ${counter_price} is within budget. Accepting."
    else:
        decision = "reject"
        reasoning = f"Counter of ${counter_price} exceeds budget of ${BUDGET_PER_DEAL}."

    logger.info("Decision: %s — %s", decision, reasoning)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{EXCHANGE_URL}/api/v1/proposals/{proposal_id}/respond",
                headers={"Authorization": f"Bearer {credentials.get('api_key', '')}"},
                json={"decision": decision, "reasoning": reasoning},
            )
            if resp.status_code == 200:
                logger.info("Response: %s", resp.json())
    except Exception as e:
        logger.error("Failed to respond to counter: %s", e)

    return {"status": decision}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": "Gatorade",
        "agent_id": credentials.get("agent_id"),
        "registered": bool(credentials.get("agent_id")),
        "llm": "gemini" if USE_LLM else "fallback",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
