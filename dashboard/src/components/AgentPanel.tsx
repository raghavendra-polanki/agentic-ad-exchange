import { useMemo } from "react";
import { useSSE } from "../hooks/useSSE";
import type { AgentStatus } from "../types";

export function AgentPanel() {
  const { events, connected } = useSSE("agents");

  const agents = useMemo(() => {
    const agentMap = new Map<string, AgentStatus>();
    for (let i = events.length - 1; i >= 0; i--) {
      const evt = events[i];
      const data = evt.data as AgentStatus;
      if (data.agent_id) {
        agentMap.set(data.agent_id, data);
      }
    }
    return Array.from(agentMap.values());
  }, [events]);

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
                  className={`status-dot ${agent.online ? "online" : "offline"}`}
                />
                <span className="agent-name">{agent.name}</span>
                <span className={`agent-type type-${agent.agent_type}`}>
                  {agent.agent_type}
                </span>
              </div>
              <div className="agent-meta">
                <span>{agent.organization}</span>
                <span>{agent.active_deals} active deal{agent.active_deals !== 1 ? "s" : ""}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
