import { useState, useEffect } from 'react';
import type { AgentInfo } from '../types';

const API_BASE = 'http://localhost:8080';

interface AgentPanelProps {
  /** If true, show as full-page grid instead of compact sidebar list */
  fullPage?: boolean;
}

export default function AgentPanel({ fullPage = false }: AgentPanelProps) {
  const [agents, setAgents] = useState<AgentInfo[]>([]);

  useEffect(() => {
    async function fetchAgents() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/agents`);
        if (res.ok) {
          const raw = await res.json();
          const list = Array.isArray(raw) ? raw : raw.agents ?? [];
          // Map server fields to AgentInfo
          setAgents(list.map((a: Record<string, unknown>) => ({
            agent_id: a.agent_id || '',
            org_id: a.org_id || '',
            org_name: (a.organization as string) || (a.name as string) || '',
            name: (a.name as string) || '',
            agent_type: (a.agent_type as string) || 'demand',
            description: '',
            is_active: a.is_active ?? true,
            last_seen: a.last_seen as string | undefined,
          })));
        }
      } catch {
        // Server not running
      }
    }

    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  // SSE for real-time agent updates
  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource(`${API_BASE}/api/v1/stream/agents`);

      const handleAgent = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          const agent: AgentInfo = {
            agent_id: data.agent_id || '',
            org_id: data.org_id || '',
            org_name: data.organization || data.name || '',
            name: data.name || '',
            agent_type: data.agent_type || 'demand',
            description: '',
            is_active: data.is_active ?? true,
            last_seen: data.last_seen,
          };
          if (!agent.agent_id) return;
          setAgents((prev) => {
            const idx = prev.findIndex((a) => a.agent_id === agent.agent_id);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = agent;
              return updated;
            }
            return [...prev, agent];
          });
        } catch {
          // ignore parse errors
        }
      };

      es.addEventListener('agent_status', handleAgent);
      es.onerror = () => { es?.close(); };
    } catch {
      // SSE not available
    }
    return () => es?.close();
  }, []);

  function getInitial(name: string) {
    return name.charAt(0).toUpperCase();
  }

  function formatLastSeen(ts?: string) {
    if (!ts) return 'Never';
    const d = new Date(ts);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return d.toLocaleDateString();
  }

  if (agents.length === 0) {
    return (
      <div className={fullPage ? '' : 'card'}>
        {!fullPage && (
          <div className="card-header">
            <span className="card-title">Agents</span>
          </div>
        )}
        <div className="empty-state">
          <p>No agents registered yet</p>
        </div>
      </div>
    );
  }

  if (fullPage) {
    return (
      <div className="agents-grid">
        {agents.map((agent) => (
          <div key={agent.agent_id} className="agent-card">
            <div className={`agent-avatar ${agent.agent_type}`}>
              {getInitial(agent.org_name || agent.name)}
            </div>
            <div className="agent-card-info">
              <div className="agent-card-name">{agent.name}</div>
              <div className="agent-card-org">{agent.org_name}</div>
            </div>
            <div className="agent-card-meta">
              <span className={`badge badge-${agent.agent_type}`}>
                {agent.agent_type.toUpperCase()}
              </span>
              <div className={`agent-status-dot ${agent.is_active ? 'active' : 'offline'}`} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Agents</span>
        <span className="badge badge-active">{agents.length} registered</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {agents.map((agent) => (
          <div key={agent.agent_id} className="agent-card">
            <div className={`agent-avatar ${agent.agent_type}`}>
              {getInitial(agent.org_name || agent.name)}
            </div>
            <div className="agent-card-info">
              <div className="agent-card-name">{agent.name}</div>
              <div className="agent-card-org">
                {agent.org_name} &middot; {formatLastSeen(agent.last_seen)}
              </div>
            </div>
            <div className="agent-card-meta">
              <span className={`badge badge-${agent.agent_type}`}>
                {agent.agent_type.toUpperCase()}
              </span>
              <div className={`agent-status-dot ${agent.is_active ? 'active' : 'offline'}`} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
