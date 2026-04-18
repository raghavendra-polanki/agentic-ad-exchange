import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

const API_BASE = 'http://localhost:8080';

interface DealEvent {
  type: string;
  actor: string;
  actor_type: string;
  timestamp: string;
  reasoning?: string;
  price?: number;
  proposal_id?: string;
  round?: number;
  scores?: Record<string, number>;
  conflicts?: Array<{ conflict_type: string; description: string; entities_involved: string[] }>;
  counter_terms?: Record<string, unknown>;
  matched_count?: number;
  description?: string;
  brief?: {
    deal_id: string;
    athlete_name: string;
    school: string;
    sport: string;
    moment_description: string;
    brand_name: string;
    deal_terms?: { content_format?: string };
  };
  content_url?: string;
  format?: string;
  passed?: boolean;
  score?: number;
  checks?: Record<string, boolean>;
  issues?: string[];
}

interface DealTrace {
  deal_id: string;
  events: DealEvent[];
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

  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    async function fetchTrace() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/deals/${dealId}/trace`);
        if (res.ok) {
          setTrace(await res.json());
        } else if (res.status === 404) {
          setNotFound(true);
        }
      } catch { /* */ }
      finally { setLoading(false); }
    }
    fetchTrace();
    // Only poll if deal exists
    const iv = setInterval(() => { if (!notFound) fetchTrace(); }, 5000);
    return () => clearInterval(iv);
  }, [dealId]);

  if (loading) return <div className="empty-state">Loading...</div>;
  if (notFound || !trace) return (
    <div className="dd">
      <Link to="/" className="dd-back">&larr; Dashboard</Link>
      <div className="empty-state">Deal not found — it may have been cleared on server restart.</div>
    </div>
  );

  const { deal, proposals, agreement, events } = trace;
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

            {/* Render all events chronologically */}
            {events.map((ev, i) => {
              const avatarCls = ev.actor_type === 'supply' ? 'supply' : 'demand';
              const initial = ev.actor?.charAt(0) || '?';

              if (ev.type === 'opportunity_listed') {
                return (
                  <div key={i} className="t-entry">
                    <div className="t-left">
                      <div className={`t-avatar ${avatarCls}`}>{initial}</div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">{ev.actor}</span>
                        <span className="t-action">listed opportunity &mdash; {ev.matched_count} agents matched</span>
                        <span className="t-time">{t(ev.timestamp)}</span>
                      </div>
                      <p className="t-text">{ev.description || deal.moment_description}</p>
                    </div>
                  </div>
                );
              }

              if (ev.type === 'conflict_blocked') {
                return (
                  <div key={i} className="t-entry">
                    <div className="t-left">
                      <div className="t-avatar demand" style={{ background: 'var(--red)' }}>{initial}</div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">{ev.actor}</span>
                        <span className="t-decision rejected">BLOCKED</span>
                        <span className="t-time">{t(ev.timestamp)}</span>
                      </div>
                      {ev.conflicts && ev.conflicts.length > 0 && (
                        <div className="t-conflict">
                          {ev.conflicts.map((c, j) => (
                            <p key={j} className="t-conflict-item">
                              <strong>{c.conflict_type}:</strong> {c.description}
                              {c.entities_involved?.length > 0 && <> ({c.entities_involved.join(', ')})</>}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              }

              if (ev.type === 'proposal_submitted') {
                // Find matching proposal for scores
                const prop = proposals.find(p => p.proposal_id === ev.proposal_id);
                return (
                  <div key={i} className="t-entry">
                    <div className="t-left">
                      <div className={`t-avatar ${avatarCls}`}>{initial}</div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">{ev.actor}</span>
                        <span className="t-action">
                          submitted proposal &mdash; <strong className="t-price">${ev.price?.toLocaleString()}</strong>
                        </span>
                        <span className="t-time">{t(ev.timestamp)}</span>
                      </div>
                      {ev.reasoning && (
                        <div className="t-reasoning">
                          <div className="t-reasoning-tag">Agent Thinking</div>
                          <p>{ev.reasoning}</p>
                        </div>
                      )}
                      {(ev.scores || prop?.scores) && (() => {
                        const s = ev.scores || prop?.scores;
                        if (!s) return null;
                        return (
                          <div className="t-scores-grid">
                            <div className="t-overall">
                              <span className="t-overall-num">{s.overall}</span>
                              <span className="t-overall-label">Score</span>
                            </div>
                            <div className="t-scores-list">
                              <ScoreBar label="Audience" value={s.audience_fit} />
                              <ScoreBar label="Brand Fit" value={s.brand_alignment} />
                              <ScoreBar label="Price" value={s.price_adequacy} />
                              <ScoreBar label="ROI" value={s.projected_roi} />
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                );
              }

              if (ev.type === 'proposal_accepted' || ev.type === 'proposal_rejected') {
                const isAccept = ev.type === 'proposal_accepted';
                return (
                  <div key={i} className="t-entry">
                    <div className="t-left">
                      <div className={`t-avatar ${avatarCls}`}>{initial}</div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">{ev.actor}</span>
                        <span className={`t-decision ${isAccept ? 'accepted' : 'rejected'}`}>
                          {isAccept ? 'ACCEPTED' : 'REJECTED'}
                        </span>
                        <span className="t-time">{t(ev.timestamp)}</span>
                      </div>
                      {ev.reasoning && <p className="t-text">{ev.reasoning}</p>}
                    </div>
                  </div>
                );
              }

              if (ev.type === 'counter_offer') {
                return (
                  <div key={i} className="t-entry">
                    <div className="t-left">
                      <div className={`t-avatar ${avatarCls}`}>{initial}</div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">{ev.actor}</span>
                        <span className="t-decision countered">COUNTER (Round {ev.round})</span>
                        <span className="t-time">{t(ev.timestamp)}</span>
                      </div>
                      {ev.reasoning && (
                        <div className="t-reasoning">
                          <div className="t-reasoning-tag">Agent Thinking</div>
                          <p>{ev.reasoning}</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              }

              if (ev.type === 'brief_generated') {
                return (
                  <div key={i} className="t-entry">
                    <div className="t-left">
                      <div className="t-avatar" style={{background: 'var(--amber)'}}>B</div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">AAX Exchange</span>
                        <span className="t-action">generated creative brief</span>
                        <span className="t-time">{t(ev.timestamp)}</span>
                      </div>
                      <p className="t-text">
                        Create {ev.brief?.deal_terms?.content_format} featuring {ev.brief?.athlete_name} ({ev.brief?.school}){' '}
                        for {ev.brief?.brand_name}. Moment: {ev.brief?.moment_description}
                      </p>
                    </div>
                  </div>
                );
              }

              if (ev.type === 'content_submitted') {
                return (
                  <div key={i} className="t-entry">
                    <div className="t-left">
                      <div className={`t-avatar ${avatarCls}`}>{initial}</div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">{ev.actor}</span>
                        <span className="t-action">submitted content</span>
                        <span className="t-time">{t(ev.timestamp)}</span>
                      </div>
                      <p className="t-text">Content submitted: <a href={ev.content_url} target="_blank" rel="noopener noreferrer">{ev.content_url}</a></p>
                    </div>
                  </div>
                );
              }

              if (ev.type === 'content_validated') {
                return (
                  <div key={i} className="t-entry">
                    <div className="t-left">
                      <div className="t-avatar" style={{background: ev.passed ? 'var(--green)' : 'var(--red)'}}>
                        {ev.passed ? '\u2713' : '\u2717'}
                      </div>
                      <div className="t-line" />
                    </div>
                    <div className="t-body">
                      <div className="t-head">
                        <span className="t-name">AAX Exchange</span>
                        <span className="t-action">validated content</span>
                        <span className="t-time">{t(ev.timestamp)}</span>
                      </div>
                      <div className="t-validation">
                        <div className="t-val-score">Score: {((ev.score ?? 0) * 100).toFixed(0)}%</div>
                        {ev.checks && (
                          <div className="t-val-checks">
                            {Object.entries(ev.checks).map(([check, passed]) => (
                              <span key={check} className={`t-val-check ${passed ? 'pass' : 'fail'}`}>
                                {passed ? '\u2713' : '\u2717'} {check.replace(/_/g, ' ')}
                              </span>
                            ))}
                          </div>
                        )}
                        {ev.issues && ev.issues.length > 0 && (
                          <div className="t-val-issues">
                            {ev.issues.map((issue, j) => <p key={j}>{issue}</p>)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              }

              if (ev.type === 'deal_completed') {
                // Handled by the outcome card below
                return null;
              }

              // Unknown event type — render generically
              return (
                <div key={i} className="t-entry">
                  <div className="t-left">
                    <div className={`t-avatar ${avatarCls}`}>{initial}</div>
                    <div className="t-line" />
                  </div>
                  <div className="t-body">
                    <div className="t-head">
                      <span className="t-name">{ev.actor}</span>
                      <span className="t-action">{ev.type.replace(/_/g, ' ')}</span>
                      <span className="t-time">{t(ev.timestamp)}</span>
                    </div>
                    {ev.reasoning && <p className="t-text">{ev.reasoning}</p>}
                  </div>
                </div>
              );
            })}

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
