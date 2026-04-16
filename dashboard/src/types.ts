export interface Price {
  amount: number;
  currency: string;
}

export interface DealTerms {
  price: Price;
  content_format: string;
  platforms?: string[];
  usage_rights_duration_days?: number;
  exclusivity_window_hours?: number;
  brand_assets?: Record<string, unknown>;
  compliance_disclosures?: string[];
}

export interface ConflictExplanation {
  conflict_type: string;
  description: string;
  entities_involved: string[];
  chain: string;
}

export interface ConflictResult {
  status: string;
  brand: string;
  conflicts: ConflictExplanation[];
  check_type: string;
}

export interface ScoreBreakdown {
  audience_fit: number;
  brand_alignment: number;
  price_adequacy: number;
  projected_roi: number;
  overall: number;
  reasoning?: string;
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
  conflicts?: ConflictExplanation[];
  reasoning?: string;
  scores?: ScoreBreakdown;
  negotiation_round?: number;
  max_rounds?: number;
  matched_count?: number;
  prescreen_results?: PrescreenResult[];
  timestamp: string;
}

export interface PrescreenResult {
  agent_id: string;
  organization: string;
  status: string;
  conflicts: ConflictExplanation[];
}

export interface AgentStatus {
  agent_id: string;
  name: string;
  agent_type: "supply" | "demand";
  organization: string;
  status: string;
  is_active: boolean;
}

export interface SSEEvent {
  event: string;
  data: DealEvent | AgentStatus | Record<string, unknown>;
  timestamp: string;
}
