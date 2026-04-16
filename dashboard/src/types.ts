export interface DealTerms {
  price: number;
  currency: string;
  content_format: string;
  usage_rights: string;
  exclusivity_window_hours?: number;
  deliverables?: string[];
}

export interface ConflictResult {
  has_conflict: boolean;
  conflict_type?: string;
  conflicting_brand?: string;
  reason?: string;
}

export interface ScoreBreakdown {
  relevance: number;
  brand_fit: number;
  audience_match: number;
  budget_fit: number;
  overall: number;
}

export interface DealEvent {
  deal_id: string;
  opportunity_id: string;
  state: string;
  supply_org: string;
  demand_org: string;
  moment_description: string;
  deal_terms?: DealTerms;
  conflict_result?: ConflictResult;
  reasoning?: string;
  scores?: ScoreBreakdown;
  negotiation_round?: number;
  max_rounds?: number;
  timestamp: string;
}

export interface AgentStatus {
  agent_id: string;
  name: string;
  agent_type: "supply" | "demand";
  organization: string;
  online: boolean;
  active_deals: number;
}

export interface SSEEvent {
  event: string;
  data: DealEvent | AgentStatus | Record<string, unknown>;
  timestamp: string;
}
