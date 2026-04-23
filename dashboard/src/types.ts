/* ── Agent Types ── */

export interface AgentInfo {
  agent_id: string;
  org_id: string;
  org_name: string;
  name: string;
  agent_type: 'supply' | 'demand';
  description: string;
  is_active: boolean;
  last_seen?: string;
  capabilities?: Record<string, unknown>;
}

/* ── Deal Types ── */

export type DealStatus =
  | 'proposed'
  | 'negotiating'
  | 'accepted'
  | 'content_pending'
  | 'content_review'
  | 'completed'
  | 'rejected'
  | 'expired'
  | 'blocked';

export interface DealInfo {
  deal_id: string;
  supply_agent_id: string;
  demand_agent_id: string;
  supply_org_name: string;
  demand_org_name: string;
  status: DealStatus;
  proposed_price: number;
  final_price?: number;
  content_type?: string;
  created_at: string;
  updated_at: string;
}

/* ── Exchange Stats ── */

export interface ExchangeStatsData {
  total_deals: number;
  active_agents: number;
  deals_today: number;
  total_orgs: number;
}

/* ── Organization Types ── */

export interface OrgInfo {
  org_id: string;
  name: string;
  domain: string;
  budget_monthly_max: number;
  agent_count: number;
  is_active: boolean;
}

export interface OrgCredentials {
  org_id: string;
  org_key: string;
  protocol_url: string;
  message: string;
}

/* ── SSE Event Types ── */

export interface SSEEvent {
  type: string;
  data: unknown;
  timestamp: string;
}

/* ── v3: Scene Analysis & Thinking ── */

export interface BrandZone {
  zone_id: string;
  description: string;
  tier: number;
  placement_type: string;
  feasibility: string;
  natural_fit_score: number;
}

export interface SceneAnalysis {
  scene_type: string;
  mood: string;
  sport: string;
  athlete_visibility: Record<string, boolean>;
  brand_zones: BrandZone[];
  categories: string[];
  pricing_guidance: Record<string, number[]>;
  creative_notes: string;
}

export interface AgentThinkingEvent {
  agent_id: string;
  agent_name: string;
  deal_id: string;
  thought_chunk: string;
  timestamp?: string;
}

export interface ContentOption {
  option_id: number;
  image_url: string | null;
  style: string;
  description: string;
  placeholder?: boolean;
}

export interface ContentReviewEvent {
  deal_id: string;
  agent_id: string;
  agent_name: string;
  option_id: number;
  decision: 'approve' | 'reject';
  reasoning: string;
}
