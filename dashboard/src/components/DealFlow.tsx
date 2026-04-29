import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { DealInfo } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';

export default function DealFlow() {
  const navigate = useNavigate();
  const [deals, setDeals] = useState<DealInfo[]>([]);

  useEffect(() => {
    async function fetchDeals() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/deals`);
        if (res.ok) {
          const raw = await res.json();
          const list = Array.isArray(raw) ? raw : raw.deals ?? [];
          setDeals(list.map((d: Record<string, unknown>) => {
            const terms = d.deal_terms as Record<string, unknown> | undefined;
            const price = terms?.price as Record<string, unknown> | undefined;
            return {
              deal_id: (d.deal_id as string) || '',
              supply_agent_id: '',
              demand_agent_id: '',
              supply_org_name: (d.supply_org as string) || '',
              demand_org_name: (d.demand_org as string) || '',
              status: (d.state as string) || 'proposed',
              proposed_price: price ? (price.amount as number) || 0 : 0,
              final_price: d.state === 'deal_agreed' && price ? (price.amount as number) : undefined,
              content_type: (d.moment_description as string) || '',
              created_at: (d.created_at as string) || new Date().toISOString(),
              updated_at: (d.updated_at as string) || new Date().toISOString(),
            } as DealInfo;
          }));
        }
      } catch {
        // Server not running
      }
    }

    fetchDeals();
    const interval = setInterval(fetchDeals, 5000);
    return () => clearInterval(interval);
  }, []);

  // SSE for real-time deal updates
  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource(`${API_BASE}/api/v1/stream/deals`);

      // Map SSE event data to DealInfo shape
      function sseToDeaInfo(data: Record<string, unknown>): DealInfo {
        const price = data.deal_terms
          ? (data.deal_terms as Record<string, unknown>).price as Record<string, unknown> | undefined
          : undefined;
        return {
          deal_id: (data.deal_id as string) || '',
          supply_agent_id: '',
          demand_agent_id: '',
          supply_org_name: (data.supply_org as string) || '',
          demand_org_name: (data.demand_org as string) || '',
          status: ((data.state as string) || 'proposed') as DealInfo['status'],
          proposed_price: price ? (price.amount as number) || 0 : 0,
          final_price: undefined,
          content_type: data.moment_description as string | undefined,
          created_at: (data.timestamp as string) || new Date().toISOString(),
          updated_at: (data.timestamp as string) || new Date().toISOString(),
        };
      }

      const handleEvent = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          const deal = sseToDeaInfo(data);
          if (!deal.deal_id) return;
          setDeals((prev) => {
            const idx = prev.findIndex((d) => d.deal_id === deal.deal_id);
            if (idx >= 0) {
              const updated = [...prev];
              updated[idx] = { ...updated[idx], ...deal };
              return updated;
            }
            return [deal, ...prev];
          });
        } catch {
          // ignore parse errors
        }
      };

      // Listen to all deal event types from the SSE bus
      const eventTypes = [
        'deal_created', 'deal_update', 'deal_agreed',
        'deal_rejected', 'deal_expired', 'conflict_blocked',
        'proposals_ranked',
      ];
      eventTypes.forEach((t) => es!.addEventListener(t, handleEvent));
      es.onerror = () => { es?.close(); };
    } catch {
      // SSE not available
    }
    return () => es?.close();
  }, []);

  function formatTime(ts: string) {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function statusBadgeClass(status: string): string {
    switch (status) {
      case 'proposed':
      case 'negotiating':
        return 'badge-proposed';
      case 'accepted':
      case 'content_pending':
      case 'content_review':
        return 'badge-active';
      case 'completed':
        return 'badge-completed';
      case 'rejected':
      case 'blocked':
        return 'badge-blocked';
      case 'expired':
        return 'badge-expired';
      default:
        return '';
    }
  }

  return (
    <div className="card" style={{ flex: 1 }}>
      <div className="card-header">
        <span className="card-title">Deal Flow</span>
        <span className="badge badge-active">{deals.length} deals</span>
      </div>

      {deals.length === 0 ? (
        <div className="empty-state">
          <p>No deals yet — waiting for agents to connect</p>
        </div>
      ) : (
        <div>
          {deals.map((deal) => (
            <div key={deal.deal_id} className="deal-item clickable" onClick={() => navigate(`/deals/${deal.deal_id}`)}>
              <div className="deal-parties">
                <div className="deal-parties-names">
                  {deal.supply_org_name} <span>&harr;</span> {deal.demand_org_name}
                </div>
                <div className="deal-meta">
                  <code>{deal.deal_id.slice(0, 8)}</code> &middot; {formatTime(deal.created_at)}
                  {deal.content_type && <> &middot; {deal.content_type}</>}
                </div>
              </div>
              <span className={`badge ${statusBadgeClass(deal.status)}`}>
                {(deal.status || 'unknown').replace('_', ' ')}
              </span>
              <span className="deal-price">
                ${(deal.final_price ?? deal.proposed_price ?? 0).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
