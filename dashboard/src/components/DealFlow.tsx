import { useMemo, useState, useEffect } from "react";
import { useSSE } from "../hooks/useSSE";
import { FulfillmentTracker } from "./FulfillmentTracker";
import type { DealEvent } from "../types";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8080/api/v1";

const STATE_PROGRESS: Record<string, number> = {
  opportunity_listed: 10,
  pre_screening: 20,
  matching: 25,
  awaiting_proposals: 40,
  proposal_received: 50,
  final_conflict_check: 60,
  awaiting_supply_evaluation: 65,
  negotiating: 70,
  deal_agreed: 90,
  completed: 100,
  deal_rejected: -1,
  deal_expired: -1,
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
  deal_expired: "#6b7280",
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
        <span className="deal-id">{deal.deal_id}</span>
        <div className="deal-badges">
          <span className="deal-state" style={{ backgroundColor: color }}>
            {formatState(deal.state)}
          </span>
          {deal.scores && (
            <span className="deal-score">
              Score: {deal.scores.overall}/100
            </span>
          )}
        </div>
      </div>

      <p className="deal-moment">{deal.moment_description || "Deal"}</p>

      <div className="deal-agents">
        <span className="agent-supply">{deal.supply_org || "Supply"}</span>
        <span className="deal-arrow">&harr;</span>
        <span className="agent-demand">{deal.demand_org || "Awaiting..."}</span>
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
          <span className="deal-price">
            ${deal.deal_terms.price?.amount?.toLocaleString() ?? "—"}
          </span>
          {deal.deal_terms.content_format && (
            <span className="deal-format">{deal.deal_terms.content_format}</span>
          )}
          {deal.deal_terms.platforms && deal.deal_terms.platforms.length > 0 && (
            <span className="deal-platforms">
              {deal.deal_terms.platforms.join(", ")}
            </span>
          )}
        </div>
      )}

      {deal.match_scores && deal.match_scores.length > 0 && (
        <div className="match-scores">
          {deal.match_scores.map((ms, i) => (
            <span
              key={i}
              className={`match-badge ${ms.conflict_status}`}
            >
              {ms.organization}: {Math.round(ms.relevance_score)}
              {ms.conflict_status === "blocked" ? " \u2717" : " \u2713"}
            </span>
          ))}
        </div>
      )}

      {deal.all_proposals && deal.all_proposals.length > 0 && (
        <div className="proposals-list">
          {deal.all_proposals.map((p, i) => (
            <div key={i} className={`proposal-item ${p.status}`}>
              <span className="proposal-org">{p.demand_org}</span>
              <span className="proposal-price">
                ${p.price?.toLocaleString()}
              </span>
              <span className="proposal-score">{p.score}/100</span>
              <span className={`proposal-status ${p.status}`}>
                {p.status === "won"
                  ? "\u2605"
                  : p.status === "blocked"
                    ? "\u2717"
                    : "\u2014"}
              </span>
            </div>
          ))}
        </div>
      )}

      {deal.conflicts && deal.conflicts.length > 0 && (
        <div className="conflict-info">
          {deal.conflicts.map((c, i) => (
            <div key={i} className="conflict-item">
              <span className="conflict-badge">BLOCKED</span> {c.description}
            </div>
          ))}
        </div>
      )}

      {deal.matched_count != null && (
        <div className="matched-info">
          {deal.matched_count} agent{deal.matched_count !== 1 ? "s" : ""} matched
        </div>
      )}

      {deal.prescreen_results && deal.prescreen_results.length > 0 && (
        <div className="prescreen-results">
          {deal.prescreen_results.map((r, i) => (
            <span key={i} className={`prescreen-badge ${r.status}`}>
              {r.organization}: {r.status === "cleared" ? "\u2713" : "\u2717"}
            </span>
          ))}
        </div>
      )}

      {deal.reasoning && (
        <div className="deal-reasoning">&ldquo;{deal.reasoning}&rdquo;</div>
      )}

      <FulfillmentTracker deal={deal} />

      <div className="deal-timestamp">
        {new Date(deal.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
}

export function DealFlow() {
  const { events, connected } = useSSE("deals");
  const [restDeals, setRestDeals] = useState<DealEvent[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/deals`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setRestDeals(
            data.map((d: Record<string, unknown>) => ({
              ...d,
              timestamp:
                (d.updated_at as string) ||
                (d.created_at as string) ||
                new Date().toISOString(),
            })) as DealEvent[],
          );
        }
      })
      .catch(() => {});
  }, []);

  const deals = useMemo(() => {
    const dealMap = new Map<string, DealEvent>();
    for (const d of restDeals) {
      dealMap.set(d.deal_id, d);
    }
    for (let i = events.length - 1; i >= 0; i--) {
      const evt = events[i];
      const data = evt.data as DealEvent;
      if (data.deal_id) {
        const existing = dealMap.get(data.deal_id);
        dealMap.set(data.deal_id, {
          ...(existing || {}),
          ...data,
          timestamp: evt.timestamp,
        } as DealEvent);
      }
    }
    const allDeals = Array.from(dealMap.values());
    const failedStates = new Set([
      "deal_rejected",
      "deal_expired",
      "conflict_blocked",
      "completed",
    ]);
    allDeals.sort((a, b) => {
      const aActive = !failedStates.has(a.state);
      const bActive = !failedStates.has(b.state);
      if (aActive !== bActive) return aActive ? -1 : 1;
      return (
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
    });
    return allDeals;
  }, [events, restDeals]);

  return (
    <div className="deal-flow">
      <div className="section-header">
        <h2>Live Deal Flow</h2>
        <span
          className={`connection-status ${connected ? "online" : "offline"}`}
        >
          {connected ? "\u25CF Connected" : "\u25CB Connecting..."}
        </span>
      </div>
      {deals.length === 0 ? (
        <div className="empty-state">
          <p>No deals yet. Run the demo to see live activity:</p>
          <code>cd agents && python run_demo.py</code>
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
