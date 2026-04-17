import { useState, useEffect } from 'react';
import type { DealInfo } from '../types';

const API_BASE = 'http://localhost:8080';

export default function DealFlow() {
  const [deals, setDeals] = useState<DealInfo[]>([]);

  useEffect(() => {
    async function fetchDeals() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/deals/`);
        if (res.ok) {
          const data = await res.json();
          setDeals(Array.isArray(data) ? data : data.deals ?? []);
        }
      } catch {
        // Server not running
      }
    }

    fetchDeals();
    const interval = setInterval(fetchDeals, 10000);
    return () => clearInterval(interval);
  }, []);

  // SSE for real-time deal updates
  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource(`${API_BASE}/api/v1/stream/deals`);
      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'deal_update' && data.deal) {
            setDeals((prev) => {
              const idx = prev.findIndex((d) => d.deal_id === data.deal.deal_id);
              if (idx >= 0) {
                const updated = [...prev];
                updated[idx] = data.deal;
                return updated;
              }
              return [data.deal, ...prev];
            });
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
            <div key={deal.deal_id} className="deal-item">
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
                {deal.status.replace('_', ' ')}
              </span>
              <span className="deal-price">
                ${(deal.final_price ?? deal.proposed_price).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
