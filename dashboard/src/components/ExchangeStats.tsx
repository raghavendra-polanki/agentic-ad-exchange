import { useState, useEffect } from 'react';
import type { ExchangeStatsData } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';

export default function ExchangeStats() {
  const [stats, setStats] = useState<ExchangeStatsData>({
    total_deals: 0,
    active_agents: 0,
    deals_today: 0,
    total_orgs: 0,
  });

  useEffect(() => {
    async function fetchStats() {
      try {
        const [statsRes, orgsRes, agentsRes] = await Promise.all([
          fetch(`${API_BASE}/api/v1/deals/stats`).catch(() => null),
          fetch(`${API_BASE}/api/v1/orgs/`).catch(() => null),
          fetch(`${API_BASE}/api/v1/agents`).catch(() => null),
        ]);

        const statsData = statsRes?.ok ? await statsRes.json() : {};
        const orgsData = orgsRes?.ok ? await orgsRes.json() : [];
        const agentsData = agentsRes?.ok ? await agentsRes.json() : [];

        setStats({
          total_deals: statsData.total_deals ?? 0,
          active_agents: Array.isArray(agentsData) ? agentsData.length : 0,
          deals_today: statsData.completed_deals ?? 0,
          total_orgs: Array.isArray(orgsData) ? orgsData.length : 0,
        });
      } catch {
        // Server not running — keep defaults
      }
    }

    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  // SSE for real-time updates
  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource(`${API_BASE}/api/v1/stream/deals`);
      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'stats_update') {
            setStats((prev) => ({ ...prev, ...data.stats }));
          }
        } catch {
          // ignore parse errors
        }
      };
      es.onerror = () => {
        es?.close();
      };
    } catch {
      // SSE not available
    }
    return () => es?.close();
  }, []);

  const statCards = [
    { label: 'Total Deals', value: stats.total_deals },
    { label: 'Active Agents', value: stats.active_agents },
    { label: 'Total Orgs', value: stats.total_orgs },
    { label: 'Deals Today', value: stats.deals_today },
  ];

  return (
    <div className="stats-grid">
      {statCards.map((s) => (
        <div key={s.label} className="stat-card">
          <div className="stat-label">{s.label}</div>
          <div className="stat-value">{s.value}</div>
        </div>
      ))}
    </div>
  );
}
