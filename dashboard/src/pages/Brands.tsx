import { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';

interface BrandRules {
  agent_id: string;
  brand: string;
  agent_name: string;
  budget_per_deal_max: number;
  budget_per_month_max: number;
  auto_approve_threshold_usd: number;
  competitor_exclusions: string[];
  target_demographics: { age_range: string | null; interests: string[] };
  voice_md: string;
  updated_at: string;
  version: number;
}

export default function BrandsList() {
  const [brands, setBrands] = useState<BrandRules[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/brands`)
      .then(r => r.json())
      .then((data: BrandRules[]) => setBrands(data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page"><div className="page-header"><h1>Brands</h1></div><p>Loading…</p></div>;

  return (
    <div>
      <div className="page-header">
        <h1>Brands</h1>
        <p>Editable brand personas for managed demand agents. Edits take effect on the next bid.</p>
      </div>

      <div className="brand-grid">
        {brands.map(b => (
          <Link key={b.agent_id} to={`/brands/${b.agent_id}`} className="brand-card">
            <div className="brand-card__header">
              <h3>{b.brand}</h3>
              <span className="brand-card__version">v{b.version}</span>
            </div>
            <div className="brand-card__name">{b.agent_name}</div>
            <div className="brand-card__metrics">
              <div className="brand-card__metric">
                <span className="brand-card__metric-label">Per-deal cap</span>
                <span className="brand-card__metric-value">${b.budget_per_deal_max.toLocaleString()}</span>
              </div>
              <div className="brand-card__metric">
                <span className="brand-card__metric-label">Auto-approve below</span>
                <span className="brand-card__metric-value">${b.auto_approve_threshold_usd.toLocaleString()}</span>
              </div>
              <div className="brand-card__metric">
                <span className="brand-card__metric-label">Exclusions</span>
                <span className="brand-card__metric-value">{b.competitor_exclusions.length}</span>
              </div>
            </div>
            {b.competitor_exclusions.length > 0 && (
              <div className="brand-card__chips">
                {b.competitor_exclusions.slice(0, 3).map(c => (
                  <span key={c} className="brand-card__chip">{c}</span>
                ))}
                {b.competitor_exclusions.length > 3 && <span className="brand-card__chip">+{b.competitor_exclusions.length - 3}</span>}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}

function chipsToList(s: string): string[] {
  return s.split(',').map(x => x.trim()).filter(Boolean);
}

export function BrandEdit() {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const [rules, setRules] = useState<BrandRules | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [savedAt, setSavedAt] = useState<string | null>(null);

  // Form fields (mirror BrandRules but as editable strings/numbers)
  const [brand, setBrand] = useState('');
  const [agentName, setAgentName] = useState('');
  const [perDeal, setPerDeal] = useState(0);
  const [perMonth, setPerMonth] = useState(0);
  const [autoApprove, setAutoApprove] = useState(0);
  const [exclusions, setExclusions] = useState('');
  const [ageRange, setAgeRange] = useState('');
  const [interests, setInterests] = useState('');
  const [voice, setVoice] = useState('');

  useEffect(() => {
    if (!agentId) return;
    fetch(`${API_BASE}/api/v1/brands/${agentId}`)
      .then(r => r.json())
      .then((data: BrandRules) => {
        setRules(data);
        setBrand(data.brand);
        setAgentName(data.agent_name);
        setPerDeal(data.budget_per_deal_max);
        setPerMonth(data.budget_per_month_max);
        setAutoApprove(data.auto_approve_threshold_usd);
        setExclusions(data.competitor_exclusions.join(', '));
        setAgeRange(data.target_demographics.age_range || '');
        setInterests(data.target_demographics.interests.join(', '));
        setVoice(data.voice_md);
      })
      .finally(() => setLoading(false));
  }, [agentId]);

  async function save() {
    setSaving(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/brands/${agentId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          brand,
          agent_name: agentName,
          budget_per_deal_max: perDeal,
          budget_per_month_max: perMonth,
          auto_approve_threshold_usd: autoApprove,
          competitor_exclusions: chipsToList(exclusions),
          target_demographics: {
            age_range: ageRange || null,
            interests: chipsToList(interests),
          },
          voice_md: voice,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const updated: BrandRules = await res.json();
      setRules(updated);
      setSavedAt(new Date().toLocaleTimeString());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="page"><p>Loading…</p></div>;
  if (!rules) return <div className="page"><p>Brand not found.</p><Link to="/brands">Back</Link></div>;

  return (
    <div>
      <Link to="/brands" className="deal-v3__back">&larr; Back to Brands</Link>
      <div className="page-header">
        <h1>{rules.brand}</h1>
        <p>{rules.agent_name} · v{rules.version} · last updated {new Date(rules.updated_at).toLocaleString()}</p>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Hard rules</span>
        </div>

        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Brand display name</label>
            <input className="form-input" value={brand} onChange={e => setBrand(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Agent name</label>
            <input className="form-input" value={agentName} onChange={e => setAgentName(e.target.value)} />
          </div>
        </div>

        <div className="form-grid form-grid--3col">
          <div className="form-group">
            <label className="form-label">Per-deal cap (USD)</label>
            <input className="form-input" type="number" value={perDeal} onChange={e => setPerDeal(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label className="form-label">Per-month cap (USD)</label>
            <input className="form-input" type="number" value={perMonth} onChange={e => setPerMonth(Number(e.target.value))} />
          </div>
          <div className="form-group">
            <label className="form-label">Auto-approve below (USD)</label>
            <input className="form-input" type="number" value={autoApprove} onChange={e => setAutoApprove(Number(e.target.value))} />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Competitor exclusions <span className="form-hint">(comma-separated)</span></label>
          <input className="form-input" value={exclusions} onChange={e => setExclusions(e.target.value)} placeholder="Adidas, Under Armour" />
        </div>

        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Target age range</label>
            <input className="form-input" value={ageRange} onChange={e => setAgeRange(e.target.value)} placeholder="18-35" />
          </div>
          <div className="form-group">
            <label className="form-label">Target interests <span className="form-hint">(comma-separated)</span></label>
            <input className="form-input" value={interests} onChange={e => setInterests(e.target.value)} placeholder="basketball, athletics" />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-header">
          <span className="card-title">Voice (Markdown)</span>
          <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
            Injected into the agent's Gemini system prompt verbatim.
          </span>
        </div>
        <textarea
          className="form-textarea"
          rows={14}
          value={voice}
          onChange={e => setVoice(e.target.value)}
          spellCheck={false}
          style={{ fontFamily: 'ui-monospace, "SF Mono", Consolas, monospace', fontSize: 13, lineHeight: 1.5 }}
        />
      </div>

      <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 12 }}>
        <button className="btn btn-primary" onClick={save} disabled={saving}>
          {saving ? 'Saving…' : 'Save changes'}
        </button>
        {savedAt && <span style={{ color: 'var(--green)', fontSize: 13 }}>Saved at {savedAt}</span>}
        {error && <span style={{ color: 'var(--red)', fontSize: 13 }}>{error}</span>}
        <button className="btn btn-secondary" onClick={() => navigate('/brands')} disabled={saving}>Cancel</button>
      </div>
    </div>
  );
}
