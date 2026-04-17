"""In-memory store. Replaces Firestore for local development."""

import secrets
import uuid
from datetime import UTC, datetime

from src.schemas.agents import (
    AgentCredentials,
    AgentType,
    DemandAgentProfile,
    RegisterAgentRequest,
    SupplyAgentProfile,
)
from src.schemas.deals import DealSummary
from src.schemas.opportunities import OpportunityRecord
from src.schemas.orgs import OrgCredentials, OrgProfile, RegisterOrgRequest
from src.schemas.proposals import ProposalRecord


class ExchangeStore:
    """Singleton in-memory store for all exchange state."""

    def __init__(self):
        # Organizations
        self.orgs: dict[str, OrgProfile] = {}  # org_id -> profile
        self.org_keys: dict[str, str] = {}  # org_key -> org_id

        # Agents
        self.agents: dict[str, SupplyAgentProfile | DemandAgentProfile] = {}
        self.api_keys: dict[str, str] = {}  # api_key -> agent_id
        self.agent_org: dict[str, str] = {}  # agent_id -> org_id
        self.agent_last_seen: dict[str, datetime] = {}  # agent_id -> timestamp
        self.webhook_secrets: dict[str, str] = {}  # agent_id -> webhook_secret

        # Notifications (polling fallback for agents without webhooks)
        self.pending_notifications: dict[str, list[dict]] = {}  # agent_id -> queue

        # Deals
        self.opportunities: dict[str, OpportunityRecord] = {}
        self.proposals: dict[str, ProposalRecord] = {}
        self.deals: dict[str, DealSummary] = {}
        self.deal_events: dict[str, list[dict]] = {}  # deal_id -> events
        self.deal_results: dict[str, dict] = {}  # deal_id -> full engine result

    # ── Organization methods ──

    def register_org(
        self, req: RegisterOrgRequest, protocol_base_url: str,
    ) -> OrgCredentials:
        org_id = f"org_{uuid.uuid4().hex[:12]}"
        # Fixed org keys for easy testing (e.g. aax_org_12345)
        org_key = f"aax_org_{req.name.lower().replace(' ', '_')}_12345"

        profile = OrgProfile(
            org_id=org_id,
            name=req.name,
            domain=req.domain,
            org_key=org_key,
            budget_monthly_max=req.budget_monthly_max,
            budget_per_deal_max=req.budget_per_deal_max,
            competitor_exclusions=req.competitor_exclusions,
            auto_approve_below=req.auto_approve_below,
        )
        self.orgs[org_id] = profile
        self.org_keys[org_key] = org_id

        return OrgCredentials(
            org_id=org_id,
            org_key=org_key,
            protocol_url=f"{protocol_base_url}/protocol.md",
        )

    def get_org_by_key(self, org_key: str) -> OrgProfile | None:
        org_id = self.org_keys.get(org_key)
        if org_id:
            return self.orgs.get(org_id)
        return None

    def get_org(self, org_id: str) -> OrgProfile | None:
        return self.orgs.get(org_id)

    def get_all_orgs_summary(self) -> list[dict]:
        return [
            {
                "org_id": org.org_id,
                "name": org.name,
                "domain": org.domain,
                "budget_monthly_max": org.budget_monthly_max,
                "agent_count": sum(
                    1 for aid, oid in self.agent_org.items() if oid == org.org_id
                ),
                "is_active": org.is_active,
            }
            for org in self.orgs.values()
        ]

    # ── Agent methods ──

    def register_agent(
        self, req: RegisterAgentRequest, org_id: str | None = None,
    ) -> AgentCredentials:
        agent_id = f"agt_{uuid.uuid4().hex[:12]}"
        api_key = f"aax_sk_{secrets.token_urlsafe(32)}"
        webhook_secret = f"whsec_{secrets.token_urlsafe(24)}"

        if req.agent_type == AgentType.SUPPLY:
            profile = SupplyAgentProfile(
                agent_id=agent_id,
                name=req.name,
                organization=req.organization,
                description=req.description,
                callback_url=str(req.callback_url) if req.callback_url else None,
                capabilities=(
                    req.supply_capabilities
                    or SupplyAgentProfile.model_fields["capabilities"].default
                ),
            )
        else:
            profile = DemandAgentProfile(
                agent_id=agent_id,
                name=req.name,
                organization=req.organization,
                description=req.description,
                callback_url=str(req.callback_url) if req.callback_url else None,
                brand_profile=(
                    req.brand_profile
                    or DemandAgentProfile.model_fields["brand_profile"].default
                ),
                standing_queries=req.standing_queries,
            )

        self.agents[agent_id] = profile
        self.api_keys[api_key] = agent_id
        self.agent_last_seen[agent_id] = datetime.now(UTC)
        self.pending_notifications[agent_id] = []
        self.webhook_secrets[agent_id] = webhook_secret

        if org_id:
            self.agent_org[agent_id] = org_id

        return AgentCredentials(
            agent_id=agent_id,
            api_key=api_key,
            webhook_secret=webhook_secret,
        )

    def touch_agent(self, agent_id: str):
        """Update last_seen timestamp (heartbeat)."""
        self.agent_last_seen[agent_id] = datetime.now(UTC)

    def get_agent_by_key(self, api_key: str):
        agent_id = self.api_keys.get(api_key)
        if agent_id:
            return self.agents.get(agent_id)
        return None

    def get_agent(self, agent_id: str):
        return self.agents.get(agent_id)

    def get_demand_agents(self) -> list[DemandAgentProfile]:
        return [
            a for a in self.agents.values()
            if isinstance(a, DemandAgentProfile) and a.is_active
        ]

    def get_supply_agents(self) -> list[SupplyAgentProfile]:
        return [
            a for a in self.agents.values()
            if isinstance(a, SupplyAgentProfile) and a.is_active
        ]

    def get_all_agents_summary(self) -> list[dict]:
        result = []
        for agent in self.agents.values():
            last_seen = self.agent_last_seen.get(agent.agent_id)
            org_id = self.agent_org.get(agent.agent_id)
            result.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "organization": agent.organization,
                "agent_type": agent.agent_type,
                "is_active": agent.is_active,
                "last_seen": last_seen.isoformat() if last_seen else None,
                "org_id": org_id,
            })
        return result

    # ── Notification methods ──

    def queue_notification(self, agent_id: str, notification: dict):
        """Add notification to agent's polling queue."""
        if agent_id not in self.pending_notifications:
            self.pending_notifications[agent_id] = []
        self.pending_notifications[agent_id].append(notification)

    def drain_notifications(self, agent_id: str) -> list[dict]:
        """Return and clear pending notifications for an agent."""
        notifications = self.pending_notifications.get(agent_id, [])
        self.pending_notifications[agent_id] = []
        return notifications

    # ── Deal methods (unchanged) ──

    def create_opportunity(
        self, supply_agent_id: str, supply_org: str, signal,
    ) -> OpportunityRecord:
        opp_id = f"opp_{uuid.uuid4().hex[:8]}"
        record = OpportunityRecord(
            opportunity_id=opp_id,
            supply_agent_id=supply_agent_id,
            supply_org=supply_org,
            signal=signal,
        )
        self.opportunities[opp_id] = record
        return record

    def create_proposal(self, proposal_data: dict) -> ProposalRecord:
        prop_id = f"prop_{uuid.uuid4().hex[:8]}"
        record = ProposalRecord(proposal_id=prop_id, **proposal_data)
        self.proposals[prop_id] = record
        return record

    def create_deal(self, deal_summary: DealSummary):
        self.deals[deal_summary.deal_id] = deal_summary

    def update_deal(self, deal_id: str, **kwargs):
        if deal_id in self.deals:
            kwargs["updated_at"] = datetime.now(UTC)
            self.deals[deal_id] = self.deals[deal_id].model_copy(update=kwargs)

    def add_deal_event(self, deal_id: str, event: dict):
        if deal_id not in self.deal_events:
            self.deal_events[deal_id] = []
        self.deal_events[deal_id].append(event)


# Singleton
store = ExchangeStore()
