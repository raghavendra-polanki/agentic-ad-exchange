import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';

interface Athlete {
  athlete_id: string;
  name: string;
  school: string;
  sport: string;
  social_handles: Record<string, string>;
  profile_image_url: string | null;
}

interface Delegation {
  grant_id: string;
  athlete_id: string;
  grantee_agent_id: string;
  sports: string[];
  moment_types: string[];
  valid_from: string;
  valid_until: string;
  max_deals_per_week: number | null;
  revoked: boolean;
  revoked_at: string | null;
  revoke_reason: string | null;
  created_at: string;
}

interface AthleteDetail {
  profile: Athlete;
  active_delegations: Delegation[];
  past_delegations: Delegation[];
}

interface AgentSummary {
  agent_id: string;
  name: string;
  organization: string;
  agent_type: string;
}

function timeUntil(iso: string): string {
  const ms = new Date(iso).getTime() - Date.now();
  if (ms < 0) return 'expired';
  const days = Math.floor(ms / (1000 * 60 * 60 * 24));
  const hours = Math.floor((ms % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  if (days >= 1) return `${days}d ${hours}h`;
  return `${hours}h`;
}

export default function AthletesList() {
  const [athletes, setAthletes] = useState<Athlete[]>([]);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState('');
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/athletes`)
      .then(async r => {
        const data = await r.json();
        if (!r.ok) throw new Error((data as { detail?: string }).detail || `HTTP ${r.status}`);
        if (!Array.isArray(data)) throw new Error(`Expected array, got: ${JSON.stringify(data).slice(0, 200)}`);
        setAthletes(data);
      })
      .catch(e => setError(e instanceof Error ? e.message : 'Load failed'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><p>Loading…</p></div>;

  return (
    <div>
      <div className="page-header">
        <h1>Athletes</h1>
        <p>Pre-seeded roster. Grant or revoke delegation rights to supply agents from each athlete's profile.</p>
      </div>
      {error && <div className="card" style={{borderColor:'var(--red)',color:'var(--red)'}}>Failed to load athletes: {error}</div>}

      <div className="brand-grid">
        {athletes.map(a => (
          <Link key={a.athlete_id} to={`/athletes/${a.athlete_id}`} className="brand-card">
            <div className="brand-card__header">
              <h3>{a.name}</h3>
              <span className="brand-card__version">{a.sport}</span>
            </div>
            <div className="brand-card__name">{a.school}</div>
            {Object.keys(a.social_handles).length > 0 && (
              <div className="brand-card__chips">
                {Object.entries(a.social_handles).map(([platform, handle]) => (
                  <span key={platform} className="brand-card__chip" style={{ background: 'rgba(139,92,246,0.1)', color: '#a78bfa' }}>
                    {platform}: {handle}
                  </span>
                ))}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}

export function AthleteDetailPage() {
  const { athleteId } = useParams<{ athleteId: string }>();
  const [detail, setDetail] = useState<AthleteDetail | null>(null);
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // grant form
  const [granteeId, setGranteeId] = useState('');
  const [sports, setSports] = useState('*');
  const [duration, setDuration] = useState(30);
  const [granting, setGranting] = useState(false);

  async function reload() {
    if (!athleteId) return;
    const res = await fetch(`${API_BASE}/api/v1/athletes/${athleteId}`);
    setDetail(await res.json());
  }

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/v1/athletes/${athleteId}`).then(r => r.json()),
      fetch(`${API_BASE}/api/v1/agents`).then(r => r.json()),
    ])
      .then(([d, a]) => {
        setDetail(d);
        const aArr: AgentSummary[] = Array.isArray(a) ? a : [];
        const supplyAgents = aArr.filter(x => x.agent_type === 'supply');
        setAgents(supplyAgents);
        if (supplyAgents.length > 0) setGranteeId(supplyAgents[0].agent_id);
      })
      .catch(e => setError(e instanceof Error ? e.message : 'Load failed'))
      .finally(() => setLoading(false));
  }, [athleteId]);

  async function grant() {
    setGranting(true);
    setError('');
    try {
      const sportsArr = sports.split(',').map(s => s.trim()).filter(Boolean);
      const res = await fetch(`${API_BASE}/api/v1/athletes/${athleteId}/delegations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grantee_agent_id: granteeId,
          sports: sportsArr.length > 0 ? sportsArr : ['*'],
          moment_types: ['*'],
          duration_days: duration,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Grant failed');
    } finally {
      setGranting(false);
    }
  }

  async function revoke(grantId: string) {
    if (!confirm('Revoke this delegation? Future signals using this grant will be rejected.')) return;
    await fetch(`${API_BASE}/api/v1/delegations/${grantId}`, { method: 'DELETE' });
    await reload();
  }

  if (loading) return <div className="page"><p>Loading…</p></div>;
  if (!detail) return <div className="page"><p>Athlete not found.</p><Link to="/athletes">Back</Link></div>;

  const { profile, active_delegations, past_delegations } = detail;

  return (
    <div>
      <Link to="/athletes" className="deal-v3__back">&larr; Back to Athletes</Link>
      <div className="page-header">
        <h1>{profile.name}</h1>
        <p>{profile.school} · {profile.sport}</p>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Active delegations ({active_delegations.length})</span>
        </div>
        {active_delegations.length === 0 && (
          <p style={{ color: 'var(--text-muted)', padding: '8px 0' }}>
            No active delegations. Signals naming this athlete will be rejected at the platform.
          </p>
        )}
        {active_delegations.map(g => (
          <div key={g.grant_id} className="delegation-row">
            <div>
              <div className="delegation-row__title">
                <strong>{agents.find(a => a.agent_id === g.grantee_agent_id)?.organization || g.grantee_agent_id}</strong>
                <span className="delegation-row__chip">sports: {g.sports.join(', ')}</span>
                <span className="delegation-row__chip">expires in {timeUntil(g.valid_until)}</span>
              </div>
              <div className="delegation-row__sub">
                Granted {new Date(g.created_at).toLocaleString()} · grant_id={g.grant_id}
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => revoke(g.grant_id)}>Revoke</button>
          </div>
        ))}
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-header">
          <span className="card-title">Grant new delegation</span>
        </div>
        <div className="form-grid form-grid--3col">
          <div className="form-group">
            <label className="form-label">Supply agent</label>
            <select className="form-input" value={granteeId} onChange={e => setGranteeId(e.target.value)}>
              {agents.map(a => (
                <option key={a.agent_id} value={a.agent_id}>{a.organization} — {a.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Sports <span className="form-hint">(comma-sep, * for any)</span></label>
            <input className="form-input" value={sports} onChange={e => setSports(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Duration (days)</label>
            <input className="form-input" type="number" value={duration} onChange={e => setDuration(Number(e.target.value))} />
          </div>
        </div>
        <button className="btn btn-primary" onClick={grant} disabled={granting || !granteeId}>
          {granting ? 'Granting…' : 'Grant delegation'}
        </button>
        {error && <span style={{ color: 'var(--red)', fontSize: 13, marginLeft: 12 }}>{error}</span>}
      </div>

      {past_delegations.length > 0 && (
        <div className="card" style={{ marginTop: 16, opacity: 0.7 }}>
          <div className="card-header">
            <span className="card-title">Past delegations ({past_delegations.length})</span>
          </div>
          {past_delegations.map(g => (
            <div key={g.grant_id} className="delegation-row">
              <div>
                <div className="delegation-row__title">
                  <strong>{agents.find(a => a.agent_id === g.grantee_agent_id)?.organization || g.grantee_agent_id}</strong>
                  <span className="delegation-row__chip" style={{ color: 'var(--text-muted)' }}>
                    {g.revoked ? `revoked${g.revoke_reason ? `: ${g.revoke_reason}` : ''}` : 'expired'}
                  </span>
                </div>
                <div className="delegation-row__sub">
                  {new Date(g.created_at).toLocaleString()} → {new Date(g.valid_until).toLocaleString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
