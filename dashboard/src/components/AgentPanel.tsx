import { useMemo, useState, useEffect } from "react";
import { useSSE } from "../hooks/useSSE";
import type { AgentStatus } from "../types";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8080/api/v1";

export function AgentPanel() {
  const { events, connected } = useSSE("agents");
  const [restAgents, setRestAgents] = useState<AgentStatus[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/agents`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setRestAgents(data as AgentStatus[]);
        }
      })
      .catch(() => {});
  }, []);

  const agents = useMemo(() => {
    const agentMap = new Map<string, AgentStatus>();
    for (const a of restAgents) {
      agentMap.set(a.agent_id, { ...a, status: "online" });
    }
    for (let i = events.length - 1; i >= 0; i--) {
      const data = events[i].data as AgentStatus;
      if (data.agent_id) {
        agentMap.set(data.agent_id, data);
      }
    }
    return Array.from(agentMap.values());
  }, [events, restAgents]);

  return (
    <div className="agent-panel">
      <div className="section-header">
        <h3>Agents</h3>
        <span className={`connection-dot ${connected ? "online" : "offline"}`} />
      </div>
      {agents.length === 0 ? (
        <p className="panel-empty">No agents registered</p>
      ) : (
        <ul className="agent-list">
          {agents.map((agent) => (
            <li key={agent.agent_id} className="agent-item">
              <div className="agent-row">
                <span
                  className={`status-dot ${agent.is_active || agent.status === "online" ? "online" : "offline"}`}
                />
                <span className="agent-name">{agent.name}</span>
                <span className={`agent-type type-${agent.agent_type}`}>
                  {agent.agent_type}
                </span>
              </div>
              <div className="agent-meta">
                <span>{agent.organization}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
