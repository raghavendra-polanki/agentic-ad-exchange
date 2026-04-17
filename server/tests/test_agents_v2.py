"""Tests for agent registration v2 with org key and agent-oriented responses."""

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.store import store

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_store():
    store.orgs.clear()
    store.org_keys.clear()
    store.agents.clear()
    store.api_keys.clear()
    store.agent_org.clear()
    store.agent_last_seen.clear()
    store.pending_notifications.clear()
    store.webhook_secrets.clear()
    yield


def _register_org() -> dict:
    resp = client.post(
        "/api/v1/orgs/register",
        json={
            "name": "Nike",
            "domain": "nike.com",
            "budget_monthly_max": 50000.0,
            "budget_per_deal_max": 5000.0,
        },
    )
    return resp.json()


def _register_agent(org_key: str, **overrides):
    payload = {
        "agent_type": "demand",
        "name": "Nike Basketball Agent",
        "organization": "Nike",
        "description": "Nike demand agent",
    }
    payload.update(overrides)
    return client.post(
        "/api/v1/agents/register",
        json=payload,
        headers={"Authorization": f"Bearer {org_key}"},
    )


def test_register_agent_with_org_key():
    org = _register_org()
    resp = _register_agent(org["org_key"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"].startswith("agt_")
    assert data["api_key"].startswith("aax_sk_")
    assert data["webhook_secret"].startswith("whsec_")
    assert data["status"] == "registered"


def test_register_agent_without_auth():
    resp = client.post(
        "/api/v1/agents/register",
        json={"agent_type": "supply", "name": "Test", "organization": "Test"},
    )
    assert resp.status_code == 401
    assert "Authorization" in resp.json()["detail"]


def test_register_agent_invalid_org_key():
    resp = client.post(
        "/api/v1/agents/register",
        json={"agent_type": "supply", "name": "Test", "organization": "Test"},
        headers={"Authorization": "Bearer aax_org_boguskey"},
    )
    assert resp.status_code == 401


def test_register_agent_non_org_key():
    """Using an agent API key (not org key) should fail."""
    resp = client.post(
        "/api/v1/agents/register",
        json={"agent_type": "supply", "name": "Test", "organization": "Test"},
        headers={"Authorization": "Bearer aax_sk_somethingelse"},
    )
    assert resp.status_code == 401
    assert "aax_org_" in resp.json()["detail"]


def test_agent_oriented_response_message():
    org = _register_org()
    resp = _register_agent(org["org_key"])
    data = resp.json()
    assert "Welcome to AAX" in data["message"]
    assert "demand" in data["message"]
    assert "Nike" in data["message"]


def test_agent_oriented_response_next_actions_no_callback():
    org = _register_org()
    resp = _register_agent(org["org_key"])
    data = resp.json()
    assert len(data["next_actions"]) > 0
    action = data["next_actions"][0]
    assert action["action"] == "set_callback_url"
    assert "PATCH" in action["endpoint"]


def test_agent_oriented_response_next_actions_with_callback():
    org = _register_org()
    resp = _register_agent(
        org["org_key"],
        callback_url="https://myagent.example.com/webhook",
    )
    data = resp.json()
    action = data["next_actions"][0]
    assert action["action"] == "wait_for_opportunities"


def test_agent_oriented_response_constraints():
    org = _register_org()
    resp = _register_agent(org["org_key"])
    data = resp.json()
    c = data["constraints"]
    assert c["budget_per_deal"] == 5000.0
    assert c["budget_monthly_remaining"] == 50000.0
    assert c["max_proposals_per_hour"] == 20


def test_heartbeat():
    org = _register_org()
    agent_resp = _register_agent(org["org_key"]).json()
    api_key = agent_resp["api_key"]

    resp = client.post(
        "/api/v1/agents/heartbeat",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["agent_id"] == agent_resp["agent_id"]


def test_poll_notifications_empty():
    org = _register_org()
    agent_resp = _register_agent(org["org_key"]).json()

    resp = client.get(
        "/api/v1/agents/me/notifications",
        headers={"Authorization": f"Bearer {agent_resp['api_key']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["notifications"] == []


def test_poll_notifications_drains():
    org = _register_org()
    agent_resp = _register_agent(org["org_key"]).json()
    agent_id = agent_resp["agent_id"]

    # Queue a notification
    store.queue_notification(agent_id, {"type": "opportunity", "id": "opp_123"})

    resp = client.get(
        "/api/v1/agents/me/notifications",
        headers={"Authorization": f"Bearer {agent_resp['api_key']}"},
    )
    assert len(resp.json()["notifications"]) == 1

    # Second poll should be empty (drained)
    resp2 = client.get(
        "/api/v1/agents/me/notifications",
        headers={"Authorization": f"Bearer {agent_resp['api_key']}"},
    )
    assert resp2.json()["notifications"] == []


def test_get_agent_profile():
    org = _register_org()
    agent_resp = _register_agent(org["org_key"]).json()

    resp = client.get(
        "/api/v1/agents/me",
        headers={"Authorization": f"Bearer {agent_resp['api_key']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == agent_resp["agent_id"]
    assert data["agent_type"] == "demand"
    assert data["organization"] == "Nike"
