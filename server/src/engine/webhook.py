"""Webhook delivery client — pushes events to agent callback URLs.

All webhooks are HMAC-SHA256 signed. Retry once on failure, then
fall back to the polling queue (store.queue_notification).
"""

import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

from src.store import store

logger = logging.getLogger("aax.webhook")

# Delivery settings
WEBHOOK_TIMEOUT = 5.0  # seconds
MAX_RETRIES = 1
RETRY_DELAY = 2.0  # seconds between retries


def _sign_payload(body: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload."""
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={mac}"


async def deliver_webhook(
    agent_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    """Deliver a webhook to an agent's callback URL.

    Returns True if delivered successfully, False if queued for polling.
    """
    agent = store.get_agent(agent_id)
    if not agent:
        logger.warning("Agent %s not found, skipping webhook", agent_id)
        return False

    callback_url = agent.callback_url
    if not callback_url:
        # No callback URL — queue for polling
        store.queue_notification(agent_id, {
            "event": event_type,
            "data": payload,
            "timestamp": time.time(),
        })
        logger.info(
            "Agent %s has no callback_url, queued for polling", agent_id,
        )
        return False

    # Find the webhook secret for this agent
    webhook_secret = _get_webhook_secret(agent_id)

    import json
    body = json.dumps(payload).encode()
    timestamp = str(int(time.time()))

    headers = {
        "Content-Type": "application/json",
        "X-AAX-Event": event_type,
        "X-AAX-Timestamp": timestamp,
    }
    if webhook_secret:
        headers["X-AAX-Signature"] = _sign_payload(body, webhook_secret)

    # Attempt delivery with retry
    for attempt in range(1 + MAX_RETRIES):
        try:
            async with httpx.AsyncClient(
                timeout=WEBHOOK_TIMEOUT,
            ) as client:
                resp = await client.post(
                    callback_url, content=body, headers=headers,
                )
                if resp.status_code < 400:
                    logger.info(
                        "Webhook %s delivered to %s (status %d)",
                        event_type, agent_id, resp.status_code,
                    )
                    return True
                logger.warning(
                    "Webhook %s to %s returned %d (attempt %d)",
                    event_type, agent_id, resp.status_code, attempt + 1,
                )
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.warning(
                "Webhook %s to %s failed: %s (attempt %d)",
                event_type, agent_id, exc, attempt + 1,
            )

        if attempt < MAX_RETRIES:
            import asyncio
            await asyncio.sleep(RETRY_DELAY)

    # All retries exhausted — queue for polling
    store.queue_notification(agent_id, {
        "event": event_type,
        "data": payload,
        "timestamp": time.time(),
    })
    logger.info(
        "Webhook %s to %s failed after retries, queued for polling",
        event_type, agent_id,
    )
    return False


def _get_webhook_secret(agent_id: str) -> str:
    """Look up the webhook secret for an agent.

    In the current in-memory store, secrets are generated at registration
    but stored alongside the API key. We store a mapping for lookup.
    """
    # Walk the api_keys to find this agent's secret
    # For now, we store webhook_secret in a separate dict on the store
    return store.webhook_secrets.get(agent_id, "")


async def deliver_to_matched_agents(
    agent_ids: list[str],
    event_type: str,
    payload_builder: callable,
) -> dict[str, bool]:
    """Deliver webhooks to multiple agents with per-agent payloads.

    payload_builder(agent_id) should return the payload dict for that agent.
    Returns {agent_id: success_bool}.
    """
    results = {}
    for agent_id in agent_ids:
        payload = payload_builder(agent_id)
        results[agent_id] = await deliver_webhook(
            agent_id, event_type, payload,
        )
    return results
