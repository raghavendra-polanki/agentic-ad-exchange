import { useState, useEffect, useRef } from "react";
import type { AgentThinkingEvent } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8080";

interface ThinkingPanelProps {
  dealId: string;
  /** Historical reasoning from deal events (pre-loaded) */
  historicalThoughts?: Array<{
    agent_name: string;
    agent_type: string;
    text: string;
    timestamp: string;
  }>;
}

interface ThoughtEntry {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  text: string;
  timestamp: string;
  isNew: boolean; // for animation
}

export default function ThinkingPanel({
  dealId,
  historicalThoughts,
}: ThinkingPanelProps) {
  const [thoughts, setThoughts] = useState<ThoughtEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);
  const thinkingTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Load historical thoughts from deal events
  useEffect(() => {
    if (historicalThoughts && historicalThoughts.length > 0) {
      setThoughts(
        historicalThoughts.map((t) => ({
          agent_id: t.agent_type,
          agent_name: t.agent_name,
          agent_type: t.agent_type,
          text: t.text,
          timestamp: t.timestamp,
          isNew: false,
        }))
      );
    }
  }, [historicalThoughts]);

  // Subscribe to live SSE thoughts
  useEffect(() => {
    const url = `${API_BASE}/api/v1/stream/deals`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);

    es.addEventListener("agent_thinking", (e: MessageEvent) => {
      const data: AgentThinkingEvent = JSON.parse(e.data);
      if (data.deal_id === dealId) {
        setIsThinking(true);
        // Clear thinking indicator after 3s of no new chunks
        if (thinkingTimeoutRef.current)
          clearTimeout(thinkingTimeoutRef.current);
        thinkingTimeoutRef.current = setTimeout(
          () => setIsThinking(false),
          3000
        );

        setThoughts((prev) => [
          ...prev,
          {
            agent_id: data.agent_id,
            agent_name: data.agent_name,
            agent_type: data.agent_id === "platform" ? "platform" : "agent",
            text: data.thought_chunk,
            timestamp: data.timestamp || new Date().toISOString(),
            isNew: true,
          },
        ]);
      }
    });

    return () => {
      es.close();
      esRef.current = null;
      if (thinkingTimeoutRef.current)
        clearTimeout(thinkingTimeoutRef.current);
    };
  }, [dealId]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thoughts]);

  const getAgentColor = (entry: ThoughtEntry) => {
    if (entry.agent_type === "platform" || entry.agent_id === "platform")
      return "#8b5cf6";
    if (
      entry.agent_type === "supply" ||
      entry.agent_name.toLowerCase().includes("pixology")
    )
      return "#f97316";
    return "#3b82f6";
  };

  const getAgentLabel = (entry: ThoughtEntry) => {
    if (entry.agent_id === "platform") return "Platform AI";
    return entry.agent_name || "Agent";
  };

  // Group consecutive thoughts by same agent
  const grouped: {
    agent_id: string;
    agent_name: string;
    agent_type: string;
    color: string;
    chunks: string[];
    isNew: boolean;
  }[] = [];
  for (const t of thoughts) {
    const last = grouped[grouped.length - 1];
    if (last && last.agent_id === t.agent_id) {
      last.chunks.push(t.text);
      if (t.isNew) last.isNew = true;
    } else {
      grouped.push({
        agent_id: t.agent_id,
        agent_name: getAgentLabel(t),
        agent_type: t.agent_type,
        color: getAgentColor(t),
        chunks: [t.text],
        isNew: t.isNew,
      });
    }
  }

  return (
    <div className="thinking-panel">
      <div className="thinking-panel__header">
        <span className="thinking-panel__icon">{"\u{1F9E0}"}</span>
        <span>Agent Reasoning</span>
        {isThinking && (
          <span className="thinking-panel__thinking-indicator">
            <span className="thinking-dots">
              <span />
              <span />
              <span />
            </span>
            thinking
          </span>
        )}
        <span
          className={`thinking-panel__status ${connected ? "thinking-panel__status--live" : ""}`}
        >
          {connected ? "LIVE" : "CONNECTING"}
        </span>
      </div>
      <div className="thinking-panel__content">
        {grouped.length === 0 ? (
          <p className="thinking-panel__placeholder">
            Agent thoughts will stream here as they reason through the deal...
          </p>
        ) : (
          grouped.map((group, i) => (
            <div
              key={i}
              className={`thinking-panel__group ${group.isNew ? "thinking-panel__group--new" : ""}`}
            >
              <div className="thinking-panel__agent">
                <span
                  className="thinking-panel__avatar"
                  style={{ backgroundColor: group.color }}
                >
                  {group.agent_name.charAt(0).toUpperCase()}
                </span>
                <span
                  className="thinking-panel__name"
                  style={{ color: group.color }}
                >
                  {group.agent_name}
                </span>
              </div>
              <div
                className="thinking-panel__thought"
                style={{ borderLeftColor: group.color + "60" }}
              >
                {group.chunks.join("")}
              </div>
            </div>
          ))
        )}
        {isThinking && (
          <div className="thinking-panel__group thinking-panel__group--new">
            <div className="thinking-panel__thought thinking-panel__thought--typing">
              <span className="thinking-dots thinking-dots--large">
                <span />
                <span />
                <span />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
