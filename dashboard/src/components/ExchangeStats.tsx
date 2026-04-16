import { useMemo } from "react";
import { useSSE } from "../hooks/useSSE";
import type { DealEvent } from "../types";

export function ExchangeStats() {
  const { events } = useSSE("deals");

  const stats = useMemo(() => {
    const dealMap = new Map<string, DealEvent>();
    for (let i = events.length - 1; i >= 0; i--) {
      const data = events[i].data as DealEvent;
      if (data.deal_id) {
        dealMap.set(data.deal_id, data);
      }
    }

    const deals = Array.from(dealMap.values());
    const activeStates = new Set([
      "opportunity_listed",
      "pre_screening",
      "matching",
      "awaiting_proposals",
      "proposal_received",
      "final_conflict_check",
      "awaiting_supply_evaluation",
      "negotiating",
    ]);
    const conflictStates = new Set(["conflict_blocked"]);

    const total = deals.length;
    const active = deals.filter((d) => activeStates.has(d.state)).length;
    const conflicts = deals.filter((d) => conflictStates.has(d.state)).length;
    const conflictRate = total > 0 ? Math.round((conflicts / total) * 100) : 0;

    return { total, active, conflicts, conflictRate };
  }, [events]);

  return (
    <div className="exchange-stats">
      <h3>Exchange</h3>
      <div className="stats-grid">
        <div className="stat">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Total Deals</span>
        </div>
        <div className="stat">
          <span className="stat-value stat-active">{stats.active}</span>
          <span className="stat-label">Active</span>
        </div>
        <div className="stat">
          <span className="stat-value stat-conflict">{stats.conflicts}</span>
          <span className="stat-label">Conflicts</span>
        </div>
        <div className="stat">
          <span className="stat-value">{stats.conflictRate}%</span>
          <span className="stat-label">Conflict Rate</span>
        </div>
      </div>
    </div>
  );
}
