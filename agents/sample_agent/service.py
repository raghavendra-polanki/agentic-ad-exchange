"""Sample self-hosted agent — proves Path B onboarding works."""

import asyncio
import hashlib
import hmac
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, Request

logger = logging.getLogger("sample-agent")
logging.basicConfig(level=logging.INFO)

EXCHANGE_URL = os.getenv("AAX_EXCHANGE_URL", "http://localhost:8080")
ORG_KEY = os.getenv("AAX_ORG_KEY", "")  # Human provides this
AGENT_PORT = int(os.getenv("AGENT_PORT", "8090"))

# State
agent_credentials = {}


async def onboard():
    """Read protocol and self-register on the exchange."""
    async with httpx.AsyncClient() as client:
        # Step 1: Read protocol
        logger.info(f"Reading protocol from {EXCHANGE_URL}/protocol.md ...")
        resp = await client.get(f"{EXCHANGE_URL}/protocol.md")
        if resp.status_code == 200:
            logger.info("Protocol loaded (%d bytes)", len(resp.text))
            # In a real LLM agent, this would be fed to the LLM
            # For this PoC, we know the registration endpoint
        else:
            logger.warning(
                "Protocol not available (status %d), proceeding with known endpoints",
                resp.status_code,
            )

        # Step 2: Register
        logger.info("Registering as demand agent under org key...")
        reg_resp = await client.post(
            f"{EXCHANGE_URL}/api/v1/agents/register",
            headers={"Authorization": f"Bearer {ORG_KEY}"},
            json={
                "agent_type": "demand",
                "name": "Sample External Agent",
                "organization": "Demo Corp",
                "description": "A sample self-hosted agent proving Path B onboarding",
                "callback_url": f"http://localhost:{AGENT_PORT}/webhook",
                "brand_profile": {
                    "tone": "professional",
                    "tagline": "Innovation meets quality",
                    "budget_per_deal_max": 3000,
                    "budget_per_month_max": 25000,
                },
                "standing_queries": [{"sport": "basketball", "min_reach": 5000}],
            },
        )

        if reg_resp.status_code == 200:
            data = reg_resp.json()
            agent_credentials.update(data)
            logger.info("Registered! agent_id=%s", data.get("agent_id"))
            logger.info("Next actions: %s", data.get("next_actions"))
            logger.info("Constraints: %s", data.get("constraints"))
        else:
            logger.error("Registration failed: %s %s", reg_resp.status_code, reg_resp.text)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Onboard on startup
    await onboard()
    yield
    logger.info("Sample agent shutting down")


app = FastAPI(title="Sample Self-Hosted Agent", lifespan=lifespan)


def verify_webhook(body: bytes, signature: str | None, timestamp: str | None) -> bool:
    """Verify webhook HMAC signature from AAX exchange."""
    secret = agent_credentials.get("webhook_secret", "")
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@app.post("/webhook")
async def receive_webhook(
    request: Request,
    x_aax_signature: str | None = Header(None),
    x_aax_timestamp: str | None = Header(None),
    x_aax_event: str | None = Header(None),
):
    """Receive webhooks from the AAX exchange."""
    body = await request.body()

    # Verify signature (log warning if failed, don't reject for demo)
    if x_aax_signature and not verify_webhook(body, x_aax_signature, x_aax_timestamp):
        logger.warning("Webhook signature verification FAILED")

    payload = await request.json()
    logger.info("Received webhook: event=%s", x_aax_event)
    logger.info("Payload: %s", payload)

    # In a real agent, this would trigger LLM evaluation
    # For this PoC, just acknowledge
    return {"status": "received", "event": x_aax_event}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent_id": agent_credentials.get("agent_id"),
        "registered": bool(agent_credentials.get("agent_id")),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
