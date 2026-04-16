import { useState, useEffect, useRef } from "react";
import type { SSEEvent } from "../types";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8080/api/v1";

export function useSSE(endpoint: string) {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const url = `${API_BASE}/stream/${endpoint}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);

    const eventTypes = [
      "deal_update",
      "deal_created",
      "deal_agreed",
      "deal_rejected",
      "deal_expired",
      "proposal_received",
      "conflict_blocked",
      "negotiation_round",
      "content_submitted",
      "content_validated",
      "deal_completed",
      "opportunity_listed",
      "agent_status",
      "fulfillment_update",
      "match_scored",
      "proposals_ranked",
    ];

    eventTypes.forEach((type) => {
      es.addEventListener(type, (e: MessageEvent) => {
        const newEvent: SSEEvent = {
          event: type,
          data: JSON.parse(e.data),
          timestamp: new Date().toISOString(),
        };
        setEvents((prev) => [newEvent, ...prev].slice(0, 100));
      });
    });

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [endpoint]);

  return { events, connected };
}
