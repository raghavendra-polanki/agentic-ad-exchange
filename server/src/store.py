"""In-memory store for Phase 1. Replaces Firestore for local development."""

import secrets
import uuid
from datetime import datetime, UTC

from src.schemas.agents import (
    AgentCredentials,
    AgentType,
    DemandAgentProfile,
    RegisterAgentRequest,
    SupplyAgentProfile,
)
from src.schemas.deals import DealSummary
from src.schemas.opportunities import OpportunityRecord, OpportunityStatus
from src.schemas.proposals import ProposalRecord, ProposalStatus


class ExchangeStore:
    """Singleton in-memory store for all exchange state."""

    def __init__(self):
        self.agents: dict[str, SupplyAgentProfile | DemandAgentProfile] = {}
        self.api_keys: dict[str, str] = {}  # api_key -> agent_id
        self.opportunities: dict[str, OpportunityRecord] = {}
        self.proposals: dict[str, ProposalRecord] = {}
        self.deals: dict[str, DealSummary] = {}
        self.deal_events: dict[str, list[dict]] = {}  # deal_id -> events
        self.deal_results: dict[str, dict] = {}  # deal_id -> full engine result

    def register_agent(self, req: RegisterAgentRequest) -> AgentCredentials:
        agent_id = f"agt_{uuid.uuid4().hex[:12]}"
        api_key = f"aax_sk_{secrets.token_urlsafe(32)}"

        if req.agent_type == AgentType.SUPPLY:
            profile = SupplyAgentProfile(
                agent_id=agent_id,
                name=req.name,
                organization=req.organization,
                description=req.description,
                callback_url=str(req.callback_url) if req.callback_url else None,
                capabilities=req.supply_capabilities or SupplyAgentProfile.model_fields["capabilities"].default,
            )
        else:
            profile = DemandAgentProfile(
                agent_id=agent_id,
                name=req.name,
                organization=req.organization,
                description=req.description,
                callback_url=str(req.callback_url) if req.callback_url else None,
                brand_profile=req.brand_profile or DemandAgentProfile.model_fields["brand_profile"].default,
                standing_queries=req.standing_queries,
            )

        self.agents[agent_id] = profile
        self.api_keys[api_key] = agent_id

        return AgentCredentials(agent_id=agent_id, api_key=api_key)

    def get_agent_by_key(self, api_key: str):
        agent_id = self.api_keys.get(api_key)
        if agent_id:
            return self.agents.get(agent_id)
        return None

    def get_agent(self, agent_id: str):
        return self.agents.get(agent_id)

    def get_demand_agents(self) -> list[DemandAgentProfile]:
        return [a for a in self.agents.values() if isinstance(a, DemandAgentProfile) and a.is_active]

    def get_supply_agents(self) -> list[SupplyAgentProfile]:
        return [a for a in self.agents.values() if isinstance(a, SupplyAgentProfile) and a.is_active]

    def create_opportunity(self, supply_agent_id: str, supply_org: str, signal) -> OpportunityRecord:
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
            deal = self.deals[deal_id]
            for k, v in kwargs.items():
                if hasattr(deal, k):
                    object.__setattr__(deal, k, v)
            object.__setattr__(deal, 'updated_at', datetime.now(UTC))

    def add_deal_event(self, deal_id: str, event: dict):
        if deal_id not in self.deal_events:
            self.deal_events[deal_id] = []
        self.deal_events[deal_id].append(event)

    def get_all_agents_summary(self) -> list[dict]:
        result = []
        for agent in self.agents.values():
            result.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "organization": agent.organization,
                "agent_type": agent.agent_type,
                "is_active": agent.is_active,
            })
        return result


# Singleton
store = ExchangeStore()
