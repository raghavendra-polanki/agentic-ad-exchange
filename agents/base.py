"""Base AAX Agent Client — shared HTTP client for communicating with the exchange."""

import httpx
import yaml


class AAXAgentClient:
    """Base client for agents to talk to the AAX exchange."""

    def __init__(self, exchange_url: str = "http://localhost:8080/api/v1"):
        self.exchange_url = exchange_url
        self.agent_id: str | None = None
        self.api_key: str | None = None
        self.http = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def register(self, registration: dict) -> dict:
        """POST /agents/register"""
        resp = await self.http.post(
            f"{self.exchange_url}/agents/register", json=registration
        )
        resp.raise_for_status()
        data = resp.json()
        self.agent_id = data["agent_id"]
        self.api_key = data["api_key"]
        return data

    async def signal_opportunity(self, signal: dict) -> dict:
        """POST /opportunities (supply agents)"""
        resp = await self.http.post(
            f"{self.exchange_url}/opportunities",
            json=signal,
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def submit_proposal(self, opportunity_id: str, proposal: dict) -> dict:
        """POST /opportunities/{id}/propose (demand agents)"""
        resp = await self.http.post(
            f"{self.exchange_url}/opportunities/{opportunity_id}/propose",
            json=proposal,
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def respond_to_proposal(self, proposal_id: str, response: dict) -> dict:
        """POST /proposals/{id}/respond"""
        resp = await self.http.post(
            f"{self.exchange_url}/proposals/{proposal_id}/respond",
            json=response,
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def submit_content(self, deal_id: str, content: dict) -> dict:
        """POST /content/{deal_id}"""
        resp = await self.http.post(
            f"{self.exchange_url}/content/{deal_id}",
            json=content,
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def get_deal(self, deal_id: str) -> dict:
        """GET /deals/{deal_id}"""
        resp = await self.http.get(
            f"{self.exchange_url}/deals/{deal_id}",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def poll_notifications(self) -> list[dict]:
        """GET /agents/{agent_id}/notifications"""
        resp = await self.http.get(
            f"{self.exchange_url}/agents/{self.agent_id}/notifications",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("notifications", [])

    async def get_deal_trace(self, deal_id: str) -> dict:
        """GET /deals/{deal_id}/trace"""
        resp = await self.http.get(
            f"{self.exchange_url}/deals/{deal_id}/trace",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    async def pass_opportunity(self, opportunity_id: str) -> dict:
        """POST /opportunities/{opportunity_id}/pass"""
        resp = await self.http.post(
            f"{self.exchange_url}/opportunities/{opportunity_id}/pass",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    @staticmethod
    def load_config(config_path: str) -> dict:
        with open(config_path) as f:
            return yaml.safe_load(f)
