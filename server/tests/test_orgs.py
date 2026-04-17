"""Tests for org registration and management API."""

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
    yield


def _register_org(**overrides) -> dict:
    payload = {
        "name": "Nike, Inc.",
        "domain": "nike.com",
        "budget_monthly_max": 50000.0,
        "budget_per_deal_max": 5000.0,
        "competitor_exclusions": ["Adidas", "Under Armour"],
    }
    payload.update(overrides)
    return client.post("/api/v1/orgs/register", json=payload)


def test_register_org():
    resp = _register_org()
    assert resp.status_code == 200
    data = resp.json()
    assert data["org_id"].startswith("org_")
    assert data["org_key"].startswith("aax_org_")
    assert "protocol.md" in data["protocol_url"]
    assert "message" in data


def test_get_org_me():
    reg = _register_org()
    org_key = reg.json()["org_key"]

    resp = client.get(
        "/api/v1/orgs/me",
        headers={"Authorization": f"Bearer {org_key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Nike, Inc."
    assert data["domain"] == "nike.com"
    assert data["budget_per_deal_max"] == 5000.0


def test_list_orgs():
    _register_org(name="Nike")
    _register_org(name="Pixology", domain="pixology.com")

    resp = client.get("/api/v1/orgs/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {o["name"] for o in data}
    assert names == {"Nike", "Pixology"}


def test_invalid_org_key():
    resp = client.get(
        "/api/v1/orgs/me",
        headers={"Authorization": "Bearer aax_org_boguskey"},
    )
    assert resp.status_code == 401


def test_missing_auth():
    resp = client.get("/api/v1/orgs/me")
    assert resp.status_code == 401
