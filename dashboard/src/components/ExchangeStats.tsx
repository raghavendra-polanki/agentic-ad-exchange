import { useMemo, useState, useEffect } from "react";
import { useSSE } from "../hooks/useSSE";
import type { DealEvent } from "../types";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8080/api/v1";

const ACTIVE_STATES = new Set([
  "opportunity_listed",
  "pre_screening",
  "matching",
  "awaiting_proposals",
  "proposal_received",
  "final_conflict_check",
  "awaiting_supply_evaluation",
  "negotiating",
]);

export function ExchangeStats() {
  const { events } = useSSE("deals");
  const [restStats, setRestStats] = useState({
    total: 0,
    active: 0,
    completed: 0,
    conflictRate: 0,
  });

  useEffect(() => {
    fetch(`${API_BASE}/deals/stats`)
      .then((r) => r.json())
      .then((data) => {
        setRestStats({
          total: data.total_deals ?? 0,
          active: data.active_deals ?? 0,
          completed: data.completed_deals ?? 0,
          conflictRate: data.conflict_rate ?? 0,
        });
      })
      .catch(() => {});
  }, []);

  const stats = useMemo(() => {
    const dealMap = new Map<string, string>();
    for (let i = events.length - 1; i >= 0; i--) {
      const data = events[i].data as DealEvent;
      if (data.deal_id && !dealMap.has(data.deal_id)) {
        dealMap.set(data.deal_id, data.state);
      }
    }

    if (dealMap.size === 0) return restStats;

    const total = Math.max(dealMap.size, restStats.total);
    let active = 0;
    let conflicts = 0;
    let completed = 0;
    for (const state of dealMap.values()) {
      if (ACTIVE_STATES.has(state)) active++;
      if (state === "conflict_blocked" || state === "deal_rejected") conflicts++;
      if (state === "deal_agreed" || state === "completed") completed++;
    }
    return {
      total,
      active,
      completed,
      conflictRate: total > 0 ? Math.round((conflicts / total) * 100) : 0,
    };
  }, [events, restStats]);

  return (
    <div className="exchange-stats">
      <h3>Exchange</h3>
      <div className="stats-grid">
        <div className="stat">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Total Deals</span>
        </div>
        <div className="stat">
          <span className="stat-value stat-green">{stats.active}</span>
          <span className="stat-label">Active</span>
        </div>
        <div className="stat">
          <span className="stat-value">{stats.completed}</span>
          <span className="stat-label">Completed</span>
        </div>
        <div className="stat">
          <span className="stat-value stat-red">{stats.conflictRate}%</span>
          <span className="stat-label">Conflict Rate</span>
        </div>
      </div>
    </div>
  );
}
