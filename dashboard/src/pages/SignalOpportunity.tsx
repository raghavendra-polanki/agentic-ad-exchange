import { useState, useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';

interface AgentOption {
  agent_id: string;
  name: string;
  organization: string;
  agent_type: string;
}

interface SignalPreset {
  label: string;
  url: string;
  athleteName: string;
  school: string;
  sport: string;
  momentDesc: string;
  reach: string;
  trendingScore: string;
  minPrice: string;
  formats: string[];
}

const IMAGE_PRESETS: Record<string, SignalPreset> = {
  basketball_dunk: {
    label: 'Duke vs. UNC — Rivalry Dunk',
    url: '/static/demo/basketball_dunk.jpg',
    athleteName: 'Cooper Reed',
    school: 'Duke',
    sport: 'basketball',
    momentDesc:
      "Cooper Reed throws down a monster two-handed slam in the final minute vs. North Carolina — Duke's biggest rivalry game of the season. The dunk seals a 78-76 win. Clip is trending on X and Instagram, already 2M views in 3 hours. Premium basketball moment, broadcast-grade footage.",
    reach: '450000',
    trendingScore: '9.2',
    minPrice: '1500',
    formats: ['gameday_graphic', 'social_post', 'highlight_reel'],
  },
  football_catch: {
    label: 'Ohio State — Game-Winning Dive',
    url: '/static/demo/football_catch.jpg',
    athleteName: 'Marcus Johnson',
    school: 'Ohio State',
    sport: 'football',
    momentDesc:
      "Marcus Johnson makes a sweat-soaked diving catch in the end zone with 8 seconds left vs. Michigan — 4th down, game on the line, rain pouring. Mud, grit, pure performance under pressure. The hydration and endurance moment. Trending nationally, ESPN top-10 play.",
    reach: '850000',
    trendingScore: '9.5',
    minPrice: '1200',
    formats: ['gameday_graphic', 'social_post', 'highlight_reel', 'video_clip'],
  },
  celebration: {
    label: 'MIT Hockey — Upset Celebration',
    url: '/static/demo/celebration.jpg',
    athleteName: 'MIT Engineers',
    school: 'MIT',
    sport: 'hockey',
    momentDesc:
      "MIT Engineers pull off a shock 4-3 overtime upset over Boston College — locker room erupts, team jumping and screaming. Pure college joy, dorm-life energy. Students flooding Mass Ave to celebrate. Small but ultra-engaged campus audience, perfect for a local-business hang-out moment.",
    reach: '12000',
    trendingScore: '6.8',
    minPrice: '100',
    formats: ['social_post', 'story'],
  },
};

type SourceMode = { kind: 'empty' } | { kind: 'upload'; file: File; previewUrl: string } | { kind: 'preset'; presetId: string };

export default function SignalOpportunity() {
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedAgent, setSelectedAgent] = useState('');

  const [source, setSource] = useState<SourceMode>({ kind: 'empty' });
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [presetMenuOpen, setPresetMenuOpen] = useState(false);

  // Form state — start blank for the custom-upload primary flow
  const [athleteName, setAthleteName] = useState('');
  const [school, setSchool] = useState('');
  const [sport, setSport] = useState('basketball');
  const [momentDesc, setMomentDesc] = useState('');
  const [reach, setReach] = useState('');
  const [trendingScore, setTrendingScore] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [formats, setFormats] = useState<string[]>(['gameday_graphic', 'social_post']);

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');

  // Fetch supply agents
  useEffect(() => {
    async function fetchAgents() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/agents`);
        if (!res.ok) return;
        const data = await res.json();
        const supply = (Array.isArray(data) ? data as AgentOption[] : []).filter(a => a.agent_type === 'supply');
        setAgents(supply);
        setSelectedAgent(prev => prev || (supply[0]?.agent_id ?? ''));
      } catch { /* */ }
    }
    fetchAgents();
    const iv = setInterval(fetchAgents, 5000);
    return () => clearInterval(iv);
  }, []);

  function applyPreset(imageId: string) {
    const preset = IMAGE_PRESETS[imageId];
    if (!preset) return;
    setSource({ kind: 'preset', presetId: imageId });
    setAthleteName(preset.athleteName);
    setSchool(preset.school);
    setSport(preset.sport);
    setMomentDesc(preset.momentDesc);
    setReach(preset.reach);
    setTrendingScore(preset.trendingScore);
    setMinPrice(preset.minPrice);
    setFormats(preset.formats);
    setPresetMenuOpen(false);
  }

  function clearImage() {
    if (source.kind === 'upload') URL.revokeObjectURL(source.previewUrl);
    setSource({ kind: 'empty' });
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function onFile(file: File | null) {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Please pick an image file (PNG, JPG, or WEBP).');
      return;
    }
    if (source.kind === 'upload') URL.revokeObjectURL(source.previewUrl);
    setSource({ kind: 'upload', file, previewUrl: URL.createObjectURL(file) });
    setError('');
  }

  function toggleFormat(fmt: string) {
    setFormats(prev => prev.includes(fmt) ? prev.filter(f => f !== fmt) : [...prev, fmt]);
  }

  function buildSignalPayload() {
    return {
      content_description: momentDesc,
      subjects: [{ athlete_name: athleteName, school, sport }],
      audience: {
        projected_reach: Number(reach) || 0,
        trending_score: Number(trendingScore) || 0,
        demographics: 'College athletics fans',
      },
      available_formats: formats,
      min_price: Number(minPrice) || 0,
      sport,
    };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setResult(null);

    if (source.kind === 'empty') {
      setError('Add a moment image — upload your own or load a demo preset.');
      return;
    }
    if (!momentDesc.trim()) {
      setError('Moment description is required.');
      return;
    }
    if (!athleteName.trim() || !school.trim()) {
      setError('Athlete name and school are required.');
      return;
    }

    setLoading(true);
    try {
      let res: Response;
      if (source.kind === 'upload') {
        const form = new FormData();
        form.append('image', source.file);
        form.append('signal_json', JSON.stringify(buildSignalPayload()));
        form.append('agent_id', selectedAgent);
        res = await fetch(`${API_BASE}/api/v1/opportunities/signal-with-image`, {
          method: 'POST',
          body: form,
        });
      } else {
        // preset
        const preset = IMAGE_PRESETS[source.presetId];
        res = await fetch(`${API_BASE}/api/v1/opportunities/signal`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id: selectedAgent,
            signal: {
              ...buildSignalPayload(),
              image_id: source.presetId,
              image_url: preset.url,
            },
          }),
        });
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        const detail = (err as { detail?: unknown }).detail;
        const msg = Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ')
          : (typeof detail === 'string' ? detail : `HTTP ${res.status}`);
        throw new Error(msg);
      }
      const json = await res.json();
      // Server may return rejection (delegation) — surface as error if so
      if (json.status === 'rejected') {
        setError(`${json.detail || 'Signal rejected'} (${json.reason})`);
      } else {
        setResult(json);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  const sourcePreviewUrl =
    source.kind === 'upload' ? source.previewUrl :
    source.kind === 'preset' ? `${API_BASE}${IMAGE_PRESETS[source.presetId].url}` :
    null;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Signal Opportunity</h1>
          <p>Create a content opportunity that demand agents can bid on</p>
        </div>
        <div style={{ position: 'relative' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setPresetMenuOpen(o => !o)}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            Load demo preset
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          {presetMenuOpen && (
            <div className="preset-menu">
              {Object.entries(IMAGE_PRESETS).map(([id, p]) => (
                <button key={id} type="button" className="preset-menu__item" onClick={() => applyPreset(id)}>
                  <img src={`${API_BASE}${p.url}`} alt={p.label} />
                  <span>{p.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {result ? (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Opportunity Listed</span>
            <span className="badge badge-completed">LIVE</span>
          </div>
          <div className="credentials-card">
            <p style={{ color: 'var(--text-primary)', marginBottom: '12px' }}>
              Opportunity is live! {(result as Record<string, unknown>).matched_count as number || 0} demand agents matched.
            </p>
            <div className="credential-row">
              <span className="credential-label">Opportunity ID</span>
              <span className="credential-value">{(result as Record<string, unknown>).opportunity_id as string}</span>
            </div>
            <div className="credential-row">
              <span className="credential-label">Deal ID</span>
              <span className="credential-value">{(result as Record<string, unknown>).deal_id as string}</span>
            </div>
            <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => { setResult(null); clearImage(); }}>
              Signal Another
            </button>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Content Moment</span>
          </div>
          <form onSubmit={handleSubmit}>
            {agents.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>
                No supply agents registered. Create a supply agent on the Onboard page first.
              </p>
            ) : (
              <div className="form-group">
                <label className="form-label">Supply Agent</label>
                <select className="form-input" value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)}>
                  {agents.map(a => (
                    <option key={a.agent_id} value={a.agent_id}>
                      {a.name} ({a.organization})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Source image — drop zone or preview */}
            <div className="form-group">
              <label className="form-label">Source Moment</label>
              {source.kind === 'empty' ? (
                <div
                  className="upload-dropzone"
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={e => { e.preventDefault(); }}
                  onDrop={e => {
                    e.preventDefault();
                    const f = e.dataTransfer.files?.[0];
                    if (f) onFile(f);
                  }}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="36" height="36">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  <div className="upload-dropzone__title">Click or drop an image here</div>
                  <div className="upload-dropzone__hint">PNG, JPG, or WEBP — up to ~10 MB</div>
                  <div className="upload-dropzone__alt">
                    or <button type="button" className="link-button" onClick={(e) => { e.stopPropagation(); setPresetMenuOpen(true); }}>load a demo preset</button>
                  </div>
                </div>
              ) : (
                <div className="upload-preview">
                  <img src={sourcePreviewUrl ?? ''} alt="moment" />
                  <div className="upload-preview__meta">
                    <div className="upload-preview__title">
                      {source.kind === 'upload' ? source.file.name : IMAGE_PRESETS[source.presetId].label}
                    </div>
                    <div className="upload-preview__sub">
                      {source.kind === 'upload' ? `${Math.round(source.file.size / 1024)} KB · custom upload` : 'demo preset'}
                    </div>
                  </div>
                  <div className="upload-preview__actions">
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => fileInputRef.current?.click()}>Replace</button>
                    <button type="button" className="btn btn-secondary btn-sm" onClick={clearImage}>Clear</button>
                  </div>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={e => onFile(e.target.files?.[0] ?? null)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Moment Description *</label>
              <textarea className="form-textarea" value={momentDesc} onChange={e => setMomentDesc(e.target.value)}
                placeholder="What happened? Describe the content opportunity..." required />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Athlete Name *</label>
                <input className="form-input" value={athleteName} onChange={e => setAthleteName(e.target.value)} placeholder="Cooper Reed" />
              </div>
              <div className="form-group">
                <label className="form-label">School *</label>
                <input className="form-input" value={school} onChange={e => setSchool(e.target.value)} placeholder="Duke" />
              </div>
              <div className="form-group">
                <label className="form-label">Sport</label>
                <select className="form-input" value={sport} onChange={e => setSport(e.target.value)}>
                  <option value="basketball">Basketball</option>
                  <option value="football">Football</option>
                  <option value="soccer">Soccer</option>
                  <option value="baseball">Baseball</option>
                  <option value="track">Track</option>
                  <option value="swimming">Swimming</option>
                  <option value="hockey">Hockey</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Audience Reach</label>
                <input className="form-input" type="number" value={reach} onChange={e => setReach(e.target.value)} placeholder="100000" />
              </div>
              <div className="form-group">
                <label className="form-label">Trending Score (0-10)</label>
                <input className="form-input" type="number" step="0.1" value={trendingScore} onChange={e => setTrendingScore(e.target.value)} placeholder="7.5" />
              </div>
              <div className="form-group">
                <label className="form-label">Min Price ($)</label>
                <input className="form-input" type="number" value={minPrice} onChange={e => setMinPrice(e.target.value)} placeholder="500" />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Content Formats</label>
              <div className="checkbox-group">
                {[
                  { value: 'gameday_graphic', label: 'Gameday Graphic' },
                  { value: 'social_post', label: 'Social Post' },
                  { value: 'highlight_reel', label: 'Highlight Reel' },
                  { value: 'story', label: 'Story' },
                  { value: 'video_clip', label: 'Video Clip' },
                ].map(fmt => (
                  <label key={fmt.value} className="checkbox-label">
                    <input type="checkbox" checked={formats.includes(fmt.value)} onChange={() => toggleFormat(fmt.value)} />
                    {fmt.label}
                  </label>
                ))}
              </div>
            </div>

            {error && <p style={{ color: 'var(--red)', fontSize: '13px', marginBottom: '12px' }}>{error}</p>}

            <button className="btn btn-primary" type="submit" disabled={loading || !selectedAgent}>
              {loading ? 'Signaling...' : 'Signal Opportunity'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
