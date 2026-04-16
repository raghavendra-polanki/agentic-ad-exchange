import { useMemo } from "react";
import { useSSE } from "../hooks/useSSE";
import type { DealEvent } from "../types";

const STATE_PROGRESS: Record<string, number> = {
  opportunity_listed: 10,
  pre_screening: 20,
  matching: 30,
  awaiting_proposals: 40,
  proposal_received: 50,
  final_conflict_check: 60,
  awaiting_supply_evaluation: 65,
  negotiating: 70,
  deal_agreed: 90,
  completed: 100,
  deal_rejected: -1,
  expired: -1,
  conflict_blocked: -1,
};

const STATE_COLORS: Record<string, string> = {
  opportunity_listed: "#3b82f6",
  pre_screening: "#3b82f6",
  matching: "#3b82f6",
  awaiting_proposals: "#8b5cf6",
  proposal_received: "#8b5cf6",
  final_conflict_check: "#f59e0b",
  awaiting_supply_evaluation: "#f59e0b",
  negotiating: "#06b6d4",
  deal_agreed: "#22c55e",
  completed: "#eab308",
  deal_rejected: "#ef4444",
  expired: "#6b7280",
  conflict_blocked: "#ef4444",
};

function formatState(state: string): string {
  return state
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function DealCard({ deal }: { deal: DealEvent }) {
  const progress = STATE_PROGRESS[deal.state] ?? 0;
  const color = STATE_COLORS[deal.state] ?? "#6b7280";
  const isFailed = progress < 0;

  return (
    <div className={`deal-card ${isFailed ? "deal-failed" : ""}`}>
      <div className="deal-header">
        <span className="deal-id">{deal.deal_id.slice(0, 8)}...</span>
        <span className="deal-state" style={{ backgroundColor: color }}>
          {formatState(deal.state)}
        </span>
      </div>

      <p className="deal-moment">{deal.moment_description || "Deal"}</p>

      <div className="deal-agents">
        <span className="agent-supply">{deal.supply_org || "Supply"}</span>
        <span className="deal-arrow">&harr;</span>
        <span className="agent-demand">{deal.demand_org || "Demand"}</span>
      </div>

      {!isFailed && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%`, backgroundColor: color }}
          />
        </div>
      )}

      {deal.deal_terms && (
        <div className="deal-terms">
          <span>
            ${deal.deal_terms.price?.toLocaleString()} {deal.deal_terms.currency}
          </span>
          {deal.deal_terms.content_format && (
            <span className="deal-format">{deal.deal_terms.content_format}</span>
          )}
        </div>
      )}

      {deal.conflict_result?.has_conflict && (
        <div className="conflict-info">
          Conflict: {deal.conflict_result.conflicting_brand} &mdash;{" "}
          {deal.conflict_result.reason}
        </div>
      )}

      {deal.negotiation_round != null && deal.max_rounds != null && (
        <div className="negotiation-info">
          Round {deal.negotiation_round}/{deal.max_rounds}
        </div>
      )}

      {deal.reasoning && (
        <div className="deal-reasoning">&ldquo;{deal.reasoning}&rdquo;</div>
      )}

      <div className="deal-timestamp">
        {new Date(deal.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
}

export function DealFlow() {
  const { events, connected } = useSSE("deals");

  // Aggregate events by deal_id, keeping latest state per deal
  const deals = useMemo(() => {
    const dealMap = new Map<string, DealEvent>();
    // events are newest-first, so iterate in reverse to get latest on top
    for (let i = events.length - 1; i >= 0; i--) {
      const evt = events[i];
      const data = evt.data as DealEvent;
      if (data.deal_id) {
        dealMap.set(data.deal_id, { ...data, timestamp: evt.timestamp });
      }
    }
    const allDeals = Array.from(dealMap.values());
    // Sort: active deals first, then by timestamp descending
    const failedStates = new Set(["deal_rejected", "expired", "conflict_blocked", "completed"]);
    allDeals.sort((a, b) => {
      const aActive = !failedStates.has(a.state);
      const bActive = !failedStates.has(b.state);
      if (aActive !== bActive) return aActive ? -1 : 1;
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });
    return allDeals;
  }, [events]);

  return (
    <div className="deal-flow">
      <div className="section-header">
        <h2>Live Deal Flow</h2>
        <span className={`connection-status ${connected ? "online" : "offline"}`}>
          {connected ? "Connected" : "Connecting..."}
        </span>
      </div>
      {deals.length === 0 ? (
        <div className="empty-state">
          <p>No deals yet. Waiting for agent activity...</p>
          <p className="empty-hint">
            Push test events via POST /api/v1/stream/test-event
          </p>
        </div>
      ) : (
        <div className="deal-grid">
          {deals.map((deal) => (
            <DealCard key={deal.deal_id} deal={deal} />
          ))}
        </div>
      )}
    </div>
  );
}
