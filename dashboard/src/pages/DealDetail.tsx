import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import type { ContentOption } from '../types';

const API_BASE = 'http://localhost:8080';

interface DealEvent {
  type: string; actor: string; actor_type: string; timestamp: string;
  reasoning?: string; price?: number; proposal_id?: string; round?: number;
  scores?: Record<string, number>;
  conflicts?: Array<{ conflict_type: string; description: string; entities_involved: string[] }>;
  matched_count?: number; description?: string;
  brief?: { athlete_name: string; brand_name: string; moment_description: string; deal_terms?: { content_format?: string } };
  content_url?: string; passed?: boolean; score?: number;
  checks?: Record<string, boolean>; issues?: string[];
  scene_analysis?: { scene_type: string; mood: string; categories: string[]; creative_notes: string };
  options?: ContentOption[];
}

interface DealTrace {
  deal_id: string; events: DealEvent[];
  deal: {
    deal_id: string; opportunity_id: string; supply_org: string; demand_org: string;
    state: string; moment_description: string; created_at: string; updated_at: string;
    negotiation_round: number; max_rounds: number; winning_proposal_id: string;
    deal_terms?: { price?: { amount: number }; content_format?: string; platforms?: string[]; usage_rights_duration_days?: number; compliance_disclosures?: string[] };
  };
  proposals: Array<{ proposal_id: string; demand_org: string; scores?: { audience_fit: number; brand_alignment: number; price_adequacy: number; projected_roi: number; overall: number } }>;
  agreement?: Record<string, unknown>;
  opportunity?: {
    image_url?: string;
    scene_analysis?: {
      scene_type: string; mood: string; sport: string;
      brand_zones: Array<{ zone_id: string; tier: number; description: string; natural_fit_score: number }>;
      categories: string[]; creative_notes: string;
    };
  };
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const c = value >= 80 ? 'var(--green)' : value >= 60 ? 'var(--orange)' : 'var(--red)';
  return (
    <div className="t-score">
      <span className="t-score-label">{label}</span>
      <div className="t-score-track"><div className="t-score-fill" style={{ width: `${value}%`, background: c }} /></div>
      <span className="t-score-val">{value}</span>
    </div>
  );
}

export default function DealDetail() {
  const { dealId } = useParams<{ dealId: string }>();
  const [trace, setTrace] = useState<DealTrace | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [generatedOptions, setGeneratedOptions] = useState<ContentOption[]>([]);
  const [lightboxIdx, setLightboxIdx] = useState<number | null>(null);
  const [revealedCount, setRevealedCount] = useState(0);
  const threadEndRef = useRef<HTMLDivElement>(null);

  // Data fetching
  useEffect(() => {
    let active = true;
    async function fetchTrace() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/deals/${dealId}/trace`);
        if (!active) return;
        if (res.ok) {
          const data = await res.json();
          setTrace(data);
          if (data.agreement?.content_options) {
            setGeneratedOptions(data.agreement.content_options);
          }
        } else if (res.status === 404) setNotFound(true);
      } catch { /* */ }
      finally { if (active) setLoading(false); }
    }
    fetchTrace();
    const iv = setInterval(fetchTrace, 4000);
    return () => { active = false; clearInterval(iv); };
  }, [dealId]);

  // SSE — listen for content_generated to update images immediately
  useEffect(() => {
    const es = new EventSource(`${API_BASE}/api/v1/stream/deals`);
    es.addEventListener('content_generated', (e: MessageEvent) => {
      const d = JSON.parse(e.data);
      if (d.deal_id !== dealId) return;
      if (d.options) setGeneratedOptions(d.options);
    });
    return () => es.close();
  }, [dealId]);

  // Progressive reveal: show events one at a time with a timer
  useEffect(() => {
    if (!trace) return;
    const total = trace.events.length;
    if (revealedCount >= total) return;

    const timer = setTimeout(() => {
      setRevealedCount(prev => {
        const next = Math.min(prev + 1, total);
        // Auto-scroll on each reveal
        if (next > prev) {
          setTimeout(() => threadEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
        }
        return next;
      });
    }, revealedCount === 0 ? 100 : 400); // first one fast, then 400ms between each

    return () => clearTimeout(timer);
  }, [trace, revealedCount]);

  if (loading) return <div className="empty-state">Loading...</div>;
  if (notFound || !trace) return <div><Link to="/" className="dd-back">&larr; Dashboard</Link><div className="empty-state">Deal not found</div></div>;

  const { deal, proposals, events, opportunity } = trace;
  const price = deal.deal_terms?.price?.amount;
  const fmt = deal.deal_terms?.content_format?.replace(/_/g, ' ') || 'content';
  const isTerminal = ['deal_agreed','completed','fulfillment_brief_sent','content_generating'].includes(deal.state);
  const isFailed = ['deal_rejected','deal_expired','conflict_blocked'].includes(deal.state);
  const imageUrl = opportunity?.image_url ? `${API_BASE}${opportunity.image_url}` : null;
  const scene = opportunity?.scene_analysis;
  const ts = (s: string) => new Date(s).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const headline = deal.moment_description.split('—')[0]?.trim() || deal.moment_description;
  const tagline = deal.moment_description.split('—')[1]?.trim() || '';

  // Compute "pending agent" — the next agent about to act.
  // This renders as a proper thread entry (avatar + name + skeleton) BEFORE the
  // real event arrives. When the real event is revealed/added, pending recomputes.
  const hasMoreToReveal = revealedCount < events.length;
  const revealedEvents = events.slice(0, revealedCount);
  const pendingAgent = (() => {
    // Priority 1: While progressively revealing from REST, show the NEXT event's agent
    if (hasMoreToReveal) {
      const nextEvent = events[revealedCount];
      if (nextEvent) {
        const actionMap: Record<string, string> = {
          scene_analyzed: 'analyzing the scene',
          proposal_submitted: 'evaluating opportunity',
          agent_passed: 'evaluating opportunity',
          counter_offer: 'considering counter-offer',
          proposal_accepted: 'making decision',
          proposal_rejected: 'making decision',
          brief_generated: 'preparing creative brief',
          content_generated: 'generating branded images',
          content_validated: 'validating content',
        };
        return {
          name: nextEvent.actor || 'Platform',
          type: nextEvent.actor_type || 'platform',
          action: actionMap[nextEvent.type] || 'processing',
        };
      }
    }

    // Priority 2: Check platform background work (runs regardless of deal state)
    // Scene analysis in progress (has image but no analysis)
    if (opportunity?.image_id && !opportunity?.scene_analysis) {
      return { name: 'Platform AI', type: 'platform', action: 'analyzing the scene' };
    }
    // Image generation in progress — deal is agreed/proceeding but images not yet generated.
    const hasDealAgreed = events.some(e =>
      e.type === 'proposal_accepted' || e.type === 'deal_completed'
    ) || ['deal_agreed', 'fulfillment_brief_sent', 'content_generating', 'fulfillment_content_submitted'].includes(deal.state);
    const hasContentGen = events.some(e => e.type === 'content_generated');
    if (hasDealAgreed && !hasContentGen && generatedOptions.length === 0 && !isFailed) {
      return { name: 'Platform', type: 'platform', action: 'generating branded images' };
    }

    // Validator working — content generated but not yet validated
    const hasContentValidated = events.some(e => e.type === 'content_validated');
    if (hasContentGen && !hasContentValidated && deal.state !== 'completed' && !isFailed) {
      return { name: 'Validator', type: 'validator', action: 'reviewing generated content' };
    }

    // Priority 3: If deal is in terminal/failed state and no platform work, no pending
    if (isFailed || deal.state === 'completed') return null;

    // Priority 4: Agent activity based on deal state
    if (deal.state === 'awaiting_proposals') {
      return { name: 'Demand Agents', type: 'demand', action: 'reviewing opportunity' };
    }
    if (deal.state === 'awaiting_supply_evaluation') {
      return { name: deal.supply_org || 'Supply Agent', type: 'supply', action: 'evaluating proposal' };
    }
    if (deal.state === 'negotiating') {
      const lastEv = revealedEvents[revealedEvents.length - 1];
      if (lastEv?.type === 'counter_offer') {
        const nextParty = lastEv.actor_type === 'supply' ? deal.demand_org : deal.supply_org;
        const nextType = lastEv.actor_type === 'supply' ? 'demand' : 'supply';
        return { name: nextParty || 'Agent', type: nextType, action: 'considering counter-offer' };
      }
      return { name: 'Agents', type: 'demand', action: 'negotiating' };
    }
    return null;
  })();

  return (
    <div className="deal-v3">
      <Link to="/" className="deal-v3__back">&larr; Back to Dashboard</Link>

      {/* ── TOP BAR: Deal summary ── */}
      <div className="deal-v3__topbar">
        <div className="deal-v3__topbar-left">
          <h1 className="deal-v3__title">{headline}</h1>
          {tagline && <p className="deal-v3__subtitle">{tagline}</p>}
        </div>
        <div className="deal-v3__topbar-right">
          <span className={`deal-v3__status ${isTerminal ? 'agreed' : isFailed ? 'failed' : 'active'}`}>
            {deal.state.replace(/_/g, ' ')}
          </span>
          {price != null && <span className="deal-v3__price">${price.toLocaleString()}</span>}
          <div className="deal-v3__parties">
            <span className="deal-v3__party"><span className="dd-dot dd-dot--supply" />{deal.supply_org}</span>
            <span className="deal-v3__vs">vs</span>
            <span className="deal-v3__party"><span className="dd-dot dd-dot--demand" />{deal.demand_org || '...'}</span>
          </div>
        </div>
      </div>

      {/* ── MAIN: Three columns — image/analysis | thread | generated ── */}
      <div className={`deal-v3__main ${generatedOptions.length > 0 ? 'deal-v3__main--3col' : ''}`}>

        {/* LEFT: Image + Analysis */}
        <div className="deal-v3__sidebar">
          {imageUrl && (
            <div className="deal-v3__img-card">
              <div className="deal-v3__img-label">Source Image</div>
              <img src={imageUrl} alt={headline} />
            </div>
          )}

          {scene && (
            <div className="deal-v3__analysis">
              <h3>Scene Analysis</h3>
              <div className="deal-v3__tags">
                {[scene.scene_type, scene.mood, scene.sport].map(t => (
                  <span key={t} className="deal-v3__tag">{t.replace(/_/g, ' ')}</span>
                ))}
              </div>
              {scene.brand_zones.slice(0, 4).map((z, i) => (
                <div key={i} className="deal-v3__zone">
                  <span className={`deal-v3__tier deal-v3__tier--${z.tier}`}>T{z.tier}</span>
                  <span className="deal-v3__zone-name">{z.zone_id.replace(/_/g, ' ')}</span>
                  <span className="deal-v3__zone-score">{z.natural_fit_score}</span>
                </div>
              ))}
              <div className="deal-v3__cats">
                {scene.categories.slice(0, 4).map(c => (
                  <span key={c} className="deal-v3__cat">{c.replace(/_/g, ' ')}</span>
                ))}
              </div>
            </div>
          )}

          <div className="deal-v3__meta">
            <div><span>Format</span><strong>{fmt}</strong></div>
            <div><span>Round</span><strong>{deal.negotiation_round || 1} / {deal.max_rounds}</strong></div>
            <div><span>Created</span><strong>{ts(deal.created_at)}</strong></div>
            <div><span>ID</span><strong style={{fontSize:10}}>{deal.deal_id}</strong></div>
          </div>
        </div>

        {/* RIGHT: Thread */}
        <div className="deal-v3__thread-area">
          <div className="deal-v3__thread-header">
            <span>Negotiation Thread</span>
            <span className="deal-v3__thread-count">{events.length} events</span>
          </div>
          <div className="deal-v3__thread">
            {events.slice(0, revealedCount).map((ev, i) => {
              const cls = ev.actor_type === 'supply' ? 'supply' : ev.actor_type === 'platform' ? 'platform' : 'demand';
              const ini = ev.actor?.charAt(0) || '?';
              const isLatest = i === revealedCount - 1;
              const tv3cls = `tv3${isLatest ? ' tv3--new' : ''}`;
              const tv3style = undefined;

              // Opportunity listed
              if (ev.type === 'opportunity_listed') return (
                <div key={i} className={tv3cls} style={tv3style}>
                  <div className={`tv3__av ${cls}`}>{ini}</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>{ev.actor}</b> listed opportunity &mdash; {ev.matched_count} matched <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                  </div>
                </div>
              );

              // Scene analyzed
              if (ev.type === 'scene_analyzed') return (
                <div key={i} className={tv3cls} style={tv3style}>
                  <div className="tv3__av platform">A</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>Platform AI</b> analyzed scene <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                  </div>
                </div>
              );

              // Proposal
              if (ev.type === 'proposal_submitted') {
                const prop = proposals.find(p => p.proposal_id === ev.proposal_id);
                const s = ev.scores || prop?.scores;
                return (
                  <div key={i} className={tv3cls} style={tv3style}>
                    <div className={`tv3__av ${cls}`}>{ini}</div>
                    <div className="tv3__body">
                      <div className="tv3__head"><b>{ev.actor}</b> bid <strong className="tv3__price">${ev.price?.toLocaleString()}</strong> <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                      {ev.reasoning && <div className="tv3__reasoning">{ev.reasoning}</div>}
                      {s && (
                        <div className="t-scores-grid">
                          <div className="t-overall"><span className="t-overall-num">{s.overall}</span><span className="t-overall-label">Score</span></div>
                          <div className="t-scores-list">
                            <ScoreBar label="Audience" value={s.audience_fit} />
                            <ScoreBar label="Brand" value={s.brand_alignment} />
                            <ScoreBar label="Price" value={s.price_adequacy} />
                            <ScoreBar label="ROI" value={s.projected_roi} />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              }

              // Counter
              if (ev.type === 'counter_offer') return (
                <div key={i} className={tv3cls} style={tv3style}>
                  <div className={`tv3__av ${cls}`}>{ini}</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>{ev.actor}</b> <span className="tv3__badge tv3__badge--counter">COUNTER R{ev.round}</span> <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                    {ev.reasoning && <div className="tv3__reasoning">{ev.reasoning}</div>}
                  </div>
                </div>
              );

              // Accept/Reject
              if (ev.type === 'proposal_accepted' || ev.type === 'proposal_rejected') {
                const ok = ev.type === 'proposal_accepted';
                return (
                  <div key={i} className={tv3cls} style={tv3style}>
                    <div className={`tv3__av ${cls}`}>{ini}</div>
                    <div className="tv3__body">
                      <div className="tv3__head"><b>{ev.actor}</b> <span className={`tv3__badge tv3__badge--${ok?'accept':'reject'}`}>{ok?'ACCEPTED':'REJECTED'}</span> <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                      {ev.reasoning && <div className="tv3__text">{ev.reasoning}</div>}
                    </div>
                  </div>
                );
              }

              // Conflict
              if (ev.type === 'conflict_blocked') return (
                <div key={i} className={tv3cls} style={tv3style}>
                  <div className="tv3__av" style={{background:'var(--red)'}}>{ini}</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>{ev.actor}</b> <span className="tv3__badge tv3__badge--reject">BLOCKED</span></div>
                    {ev.conflicts?.map((c,j) => <div key={j} className="tv3__text" style={{color:'var(--red)'}}>{c.description}</div>)}
                  </div>
                </div>
              );

              // Brief
              if (ev.type === 'brief_generated') return (
                <div key={i} className={tv3cls} style={tv3style}>
                  <div className="tv3__av platform">B</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>Platform</b> creative brief <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                    <div className="tv3__text">{fmt} for {ev.brief?.brand_name} ft. {ev.brief?.athlete_name}</div>
                  </div>
                </div>
              );

              // Content generated
              if (ev.type === 'content_generated') return (
                <div key={i} className={tv3cls} style={tv3style}>
                  <div className="tv3__av platform">G</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>Platform</b> generated {ev.options?.length || 0} branded options <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                  </div>
                </div>
              );

              // Validation
              if (ev.type === 'content_validated') return (
                <div key={i} className={tv3cls} style={tv3style}>
                  <div className="tv3__av" style={{background: ev.passed ? 'var(--green)' : 'var(--red)'}}>{ev.passed ? '\u2713' : '\u2717'}</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>Validator</b> {((ev.score??0)*100).toFixed(0)}% <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                    {ev.checks && <div className="t-val-checks">{Object.entries(ev.checks).map(([k,v]) => <span key={k} className={`t-val-check ${v?'pass':'fail'}`}>{v?'\u2713':'\u2717'} {k.replace(/_/g,' ')}</span>)}</div>}
                  </div>
                </div>
              );

              // Agent passed on opportunity
              if (ev.type === 'agent_passed') return (
                <div key={i} className={`${tv3cls} tv3--passed`} style={tv3style}>
                  <div className={`tv3__av ${cls}`}>{ini}</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>{ev.actor}</b> <span className="tv3__badge tv3__badge--passed">PASSED</span> <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                    {ev.reasoning && <div className="tv3__reasoning">{ev.reasoning}</div>}
                  </div>
                </div>
              );

              if (ev.type === 'deal_completed') return null;

              // Fallback
              return (
                <div key={i} className={tv3cls} style={tv3style}>
                  <div className={`tv3__av ${cls}`}>{ini}</div>
                  <div className="tv3__body">
                    <div className="tv3__head"><b>{ev.actor}</b> {ev.type.replace(/_/g,' ')} <span className="tv3__time">{ts(ev.timestamp)}</span></div>
                    {ev.reasoning && <div className="tv3__text">{ev.reasoning}</div>}
                  </div>
                </div>
              );
            })}

            {/* Outcome */}
            {isTerminal && (
              <div className="tv3 tv3--outcome">
                <div className="tv3__av" style={{background:'var(--green)'}}>&#10003;</div>
                <div className="tv3__body"><div className="tv3__head"><b>Deal Agreed</b> &mdash; {deal.supply_org} + {deal.demand_org}{price != null && <> at <strong>${price.toLocaleString()}</strong></>}</div></div>
              </div>
            )}
            {isFailed && (
              <div className="tv3 tv3--outcome">
                <div className="tv3__av" style={{background:'var(--red)'}}>&#10005;</div>
                <div className="tv3__body"><div className="tv3__head"><b>Deal Failed</b> &mdash; {deal.state.replace(/_/g,' ')}</div></div>
              </div>
            )}

            {/* Pending agent — appears as a thread entry the moment an agent is
                brought into the loop, replaced when their real event arrives */}
            {pendingAgent && (() => {
              const avClass = pendingAgent.type === 'supply' ? 'supply'
                : pendingAgent.type === 'platform' ? 'platform'
                : pendingAgent.type === 'validator' ? 'validator'
                : 'demand';
              const ini = pendingAgent.name.charAt(0).toUpperCase();
              return (
                <div className="tv3 tv3--thinking">
                  <div className={`tv3__av ${avClass}`}>{ini}</div>
                  <div className="tv3__body">
                    <div className="tv3__head">
                      <b>{pendingAgent.name}</b>{' '}
                      <span className="tv3__thinking-label">is {pendingAgent.action}...</span>
                    </div>
                    <div className="tv3__skeleton">
                      <div className="tv3__skeleton-line tv3__skeleton-line--1" />
                      <div className="tv3__skeleton-line tv3__skeleton-line--2" />
                      <div className="tv3__skeleton-line tv3__skeleton-line--3" />
                    </div>
                  </div>
                </div>
              );
            })()}
            {generatedOptions.length > 0 && (
              <div className="tv3">
                <div className="tv3__av" style={{background:'var(--green)'}}>&#10003;</div>
                <div className="tv3__body"><div className="tv3__head"><b>Platform</b> <span className="tv3__badge tv3__badge--accept">IMAGES READY</span> {generatedOptions.length} branded options generated</div></div>
              </div>
            )}
            <div ref={threadEndRef} />
          </div>
        </div>

        {/* RIGHT: Generated Images */}
        {generatedOptions.length > 0 && (
          <div className="deal-v3__right-col">
            <div className="deal-v3__right-header">Generated Content</div>
            {generatedOptions.map((opt, idx) => (
              <div key={opt.option_id} className="deal-v3__right-card" onClick={() => opt.image_url && !opt.placeholder && setLightboxIdx(idx)}>
                {opt.image_url && !opt.placeholder
                  ? <img src={`${API_BASE}${opt.image_url}`} alt={opt.style} />
                  : <div className="deal-v3__gen-placeholder"><span className="thinking-dots thinking-dots--large"><span/><span/><span/></span></div>}
                <div className="deal-v3__right-label">{opt.style}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── LIGHTBOX ── */}
      {lightboxIdx !== null && generatedOptions[lightboxIdx] && (
        <div className="dd-lightbox" onClick={() => setLightboxIdx(null)}>
          <button className="dd-lightbox__close" onClick={() => setLightboxIdx(null)}>&times;</button>
          {lightboxIdx > 0 && <button className="dd-lightbox__nav dd-lightbox__nav--prev" onClick={e=>{e.stopPropagation();setLightboxIdx(lightboxIdx-1)}}>&lsaquo;</button>}
          {lightboxIdx < generatedOptions.length-1 && <button className="dd-lightbox__nav dd-lightbox__nav--next" onClick={e=>{e.stopPropagation();setLightboxIdx(lightboxIdx+1)}}>&rsaquo;</button>}
          <div className="dd-lightbox__content" onClick={e=>e.stopPropagation()}>
            <img className="dd-lightbox__img" src={`${API_BASE}${generatedOptions[lightboxIdx].image_url}`} alt={generatedOptions[lightboxIdx].style} />
            <div className="dd-lightbox__caption">
              <div className="dd-lightbox__style">{generatedOptions[lightboxIdx].style}</div>
              <div className="dd-lightbox__desc">{generatedOptions[lightboxIdx].description}</div>
            </div>
          </div>
          <div className="dd-lightbox__counter">{lightboxIdx+1} / {generatedOptions.length}</div>
        </div>
      )}
    </div>
  );
}
