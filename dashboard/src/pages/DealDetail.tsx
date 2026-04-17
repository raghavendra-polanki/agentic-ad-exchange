import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

const API_BASE = 'http://localhost:8080';

interface DealTrace {
  deal_id: string;
  deal: {
    deal_id: string;
    opportunity_id: string;
    supply_org: string;
    demand_org: string;
    state: string;
    moment_description: string;
    created_at: string;
    updated_at: string;
    negotiation_round: number;
    max_rounds: number;
    winning_proposal_id: string;
    deal_terms?: {
      price?: { amount: number; currency: string };
      content_format?: string;
      platforms?: string[];
      usage_rights_duration_days?: number;
      compliance_disclosures?: string[];
    };
  };
  proposals: Array<{
    proposal_id: string;
    demand_org: string;
    demand_agent_id: string;
    status: string;
    reasoning: string;
    round: number;
    created_at: string;
    deal_terms?: {
      price?: { amount: number; currency: string };
      content_format?: string;
      platforms?: string[];
      usage_rights_duration_days?: number;
    };
    scores?: {
      audience_fit: number;
      brand_alignment: number;
      price_adequacy: number;
      projected_roi: number;
      overall: number;
    };
  }>;
  agreement?: {
    deal_id: string;
    supply_org: string;
    demand_org: string;
    agreed_at: string;
    final_terms?: {
      price?: { amount: number; currency: string };
      content_format?: string;
      platforms?: string[];
      usage_rights_duration_days?: number;
    };
  };
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? 'var(--green)' : value >= 60 ? 'var(--orange)' : 'var(--red)';
  return (
    <div className="t-score">
      <span className="t-score-label">{label}</span>
      <div className="t-score-track">
        <div className="t-score-fill" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="t-score-val">{value}</span>
    </div>
  );
}

export default function DealDetail() {
  const { dealId } = useParams<{ dealId: string }>();
  const [trace, setTrace] = useState<DealTrace | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTrace() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/deals/${dealId}/trace`);
        if (res.ok) setTrace(await res.json());
      } catch { /* */ }
      finally { setLoading(false); }
    }
    fetchTrace();
    const iv = setInterval(fetchTrace, 5000);
    return () => clearInterval(iv);
  }, [dealId]);

  if (loading) return <div className="empty-state">Loading...</div>;
  if (!trace) return <div className="empty-state">Deal not found</div>;

  const { deal, proposals, agreement } = trace;
  const price = deal.deal_terms?.price?.amount;
  const fmt = deal.deal_terms?.content_format?.replace(/_/g, ' ') || 'content';
  const platforms = deal.deal_terms?.platforms || [];
  const isAgreed = deal.state === 'deal_agreed' || deal.state === 'completed';
  const isFailed = deal.state === 'deal_rejected' || deal.state === 'deal_expired' || deal.state === 'conflict_blocked';

  function t(ts: string) {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  const momentParts = deal.moment_description.split('—');
  const headline = momentParts[0]?.trim() || deal.moment_description;
  const tagline = momentParts[1]?.trim() || '';

  return (
    <div className="dd">
      <Link to="/" className="dd-back">&larr; Dashboard</Link>

      {/* ── Hero: Content Preview (full width) ── */}
      <div className="dd-hero-full">
        <div className="dd-preview">
          <div className="dd-preview-inner">
            <span className="dd-fmt-badge">{fmt}</span>
            <div className="dd-preview-bottom">
              <h1 className="dd-headline">{headline}</h1>
              {tagline && <p className="dd-tagline">{tagline}</p>}
              <div className="dd-preview-meta">
                <span>by {deal.supply_org}</span>
                {platforms.map(p => <span key={p} className="dd-plat">{p}</span>)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Two-column: Thread + Sidebar ── */}
      <div className="dd-layout">

        {/* Left: Negotiation Thread */}
        <div className="dd-thread-panel">
          <h2 className="dd-section">Negotiation Thread</h2>
          <div className="dd-thread">

            {/* Signal */}
            <div className="t-entry">
              <div className="t-left">
                <div className="t-avatar supply">{deal.supply_org.charAt(0)}</div>
                <div className="t-line" />
              </div>
              <div className="t-body">
                <div className="t-head">
                  <span className="t-name">{deal.supply_org}</span>
                  <span className="t-action">listed opportunity</span>
                  <span className="t-time">{t(deal.created_at)}</span>
                </div>
                <p className="t-text">{deal.moment_description}</p>
              </div>
            </div>

            {/* Proposals */}
            {proposals.map((prop) => (
              <div key={prop.proposal_id}>
                <div className="t-entry">
                  <div className="t-left">
                    <div className="t-avatar demand">{prop.demand_org.charAt(0)}</div>
                    <div className="t-line" />
                  </div>
                  <div className="t-body">
                    <div className="t-head">
                      <span className="t-name">{prop.demand_org}</span>
                      <span className="t-action">
                        submitted proposal &mdash; <strong className="t-price">${prop.deal_terms?.price?.amount?.toLocaleString()}</strong>
                      </span>
                      <span className="t-time">{t(prop.created_at)}</span>
                    </div>

                    {prop.reasoning && (
                      <div className="t-reasoning">
                        <div className="t-reasoning-tag">Agent Thinking</div>
                        <p>{prop.reasoning}</p>
                      </div>
                    )}

                    {prop.scores && (
                      <div className="t-scores-grid">
                        <div className="t-overall">
                          <span className="t-overall-num">{prop.scores.overall}</span>
                          <span className="t-overall-label">Score</span>
                        </div>
                        <div className="t-scores-list">
                          <ScoreBar label="Audience" value={prop.scores.audience_fit} />
                          <ScoreBar label="Brand Fit" value={prop.scores.brand_alignment} />
                          <ScoreBar label="Price" value={prop.scores.price_adequacy} />
                          <ScoreBar label="ROI" value={prop.scores.projected_roi} />
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Supply response */}
                {(prop.status === 'accepted' || prop.status === 'rejected' || prop.status === 'countered') && (
                  <div className="t-entry">
                    <div className="t-left">
                      <div className="t-avatar supply">{deal.supply_org.charAt(0)}</div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">{deal.supply_org}</span>
                        <span className={`t-decision ${prop.status}`}>{prop.status}</span>
                      </div>
                      {prop.status === 'accepted' && (
                        <p className="t-text">Price ${prop.deal_terms?.price?.amount?.toLocaleString()} meets requirements. {prop.demand_org} is a strong brand partner.</p>
                      )}
                      {prop.status === 'rejected' && (
                        <p className="t-text t-text-dim">Proposal did not meet content requirements.</p>
                      )}
                      {prop.status === 'countered' && (
                        <p className="t-text">Counter-offer proposed with adjusted terms.</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Outcome */}
            {isAgreed && agreement && (
              <div className="t-entry t-outcome-entry">
                <div className="t-left">
                  <div className="t-outcome-dot">&#10003;</div>
                </div>
                <div className="t-body">
                  <div className="t-outcome-card">
                    <strong>Deal Closed</strong> &mdash; {agreement.supply_org} will create {fmt} for {agreement.demand_org} at{' '}
                    <strong>${agreement.final_terms?.price?.amount?.toLocaleString()}</strong>.
                    {agreement.final_terms?.platforms && <> Platforms: {agreement.final_terms.platforms.join(', ')}.</>}
                    {agreement.final_terms?.usage_rights_duration_days && <> {agreement.final_terms.usage_rights_duration_days}-day usage rights.</>}
                  </div>
                </div>
              </div>
            )}

            {isFailed && (
              <div className="t-entry t-outcome-entry">
                <div className="t-left">
                  <div className="t-outcome-dot failed">&#10005;</div>
                </div>
                <div className="t-body">
                  <div className="t-outcome-card failed">
                    <strong>Deal Did Not Close</strong> &mdash; {deal.state.replace(/_/g, ' ')}.
                    {deal.state === 'deal_expired' && ' The opportunity expired before terms were agreed.'}
                    {deal.state === 'deal_rejected' && ' The proposal was rejected by the supply agent.'}
                    {deal.state === 'conflict_blocked' && ' A conflict was detected that prevented the deal.'}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Deal Sidebar (sticky) */}
        <div className="dd-sidebar">
          <div className="dd-sidebar-inner">

            {/* Status + Price */}
            <div className="dd-sb-card">
              <span className={`dd-status ${isAgreed ? 'agreed' : isFailed ? 'failed' : 'active'}`}>
                {deal.state.replace(/_/g, ' ')}
              </span>
              {price != null && <div className="dd-sb-price">${price.toLocaleString()}</div>}
              <div className="dd-sb-id">{deal.deal_id}</div>
            </div>

            {/* Parties */}
            <div className="dd-sb-card">
              <div className="dd-sb-label">Parties</div>
              <div className="dd-sb-party">
                <div className="dd-sb-dot supply" />
                <div>
                  <div className="dd-sb-role">Content Creator</div>
                  <div className="dd-sb-name">{deal.supply_org}</div>
                </div>
              </div>
              <div className="dd-sb-party">
                <div className="dd-sb-dot demand" />
                <div>
                  <div className="dd-sb-role">Brand Sponsor</div>
                  <div className="dd-sb-name">{deal.demand_org || 'Pending'}</div>
                </div>
              </div>
            </div>

            {/* Deal Terms */}
            <div className="dd-sb-card">
              <div className="dd-sb-label">Deal Terms</div>
              <div className="dd-sb-row"><span>Format</span><strong>{fmt}</strong></div>
              <div className="dd-sb-row"><span>Platforms</span><strong>{platforms.join(', ') || '—'}</strong></div>
              <div className="dd-sb-row"><span>Usage Rights</span><strong>{deal.deal_terms?.usage_rights_duration_days || '—'} days</strong></div>
              <div className="dd-sb-row"><span>Negotiation</span><strong>Round {deal.negotiation_round || 1} of {deal.max_rounds}</strong></div>
              {deal.deal_terms?.compliance_disclosures && deal.deal_terms.compliance_disclosures.length > 0 && (
                <div className="dd-sb-row"><span>Disclosures</span><strong>{deal.deal_terms.compliance_disclosures.join(', ')}</strong></div>
              )}
            </div>

            {/* Timeline */}
            <div className="dd-sb-card">
              <div className="dd-sb-label">Timeline</div>
              <div className="dd-sb-row"><span>Created</span><strong>{t(deal.created_at)}</strong></div>
              <div className="dd-sb-row"><span>Updated</span><strong>{t(deal.updated_at)}</strong></div>
              {agreement && <div className="dd-sb-row"><span>Agreed</span><strong>{t(agreement.agreed_at)}</strong></div>}
              <div className="dd-sb-row"><span>Proposals</span><strong>{proposals.length}</strong></div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
