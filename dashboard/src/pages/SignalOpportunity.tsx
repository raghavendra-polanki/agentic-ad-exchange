import { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8080';

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

export default function SignalOpportunity() {
  const [agents, setAgents] = useState<AgentOption[]>([]);
  const [selectedAgent, setSelectedAgent] = useState('');

  const [selectedImage, setSelectedImage] = useState('basketball_dunk');
  const initial = IMAGE_PRESETS.basketball_dunk;

  // Form state
  const [athleteName, setAthleteName] = useState(initial.athleteName);
  const [school, setSchool] = useState(initial.school);
  const [sport, setSport] = useState(initial.sport);
  const [momentDesc, setMomentDesc] = useState(initial.momentDesc);
  const [reach, setReach] = useState(initial.reach);
  const [trendingScore, setTrendingScore] = useState(initial.trendingScore);
  const [minPrice, setMinPrice] = useState(initial.minPrice);
  const [formats, setFormats] = useState(initial.formats);

  function applyPreset(imageId: string) {
    const preset = IMAGE_PRESETS[imageId];
    if (!preset) return;
    setSelectedImage(imageId);
    setAthleteName(preset.athleteName);
    setSchool(preset.school);
    setSport(preset.sport);
    setMomentDesc(preset.momentDesc);
    setReach(preset.reach);
    setTrendingScore(preset.trendingScore);
    setMinPrice(preset.minPrice);
    setFormats(preset.formats);
  }

  const demoImages = Object.entries(IMAGE_PRESETS).map(([id, p]) => ({
    id,
    label: p.label,
    url: p.url,
  }));

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');

  // Fetch supply agents
  useEffect(() => {
    async function fetchAgents() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/agents`);
        if (res.ok) {
          const data = await res.json();
          const supply = (data as AgentOption[]).filter(a => a.agent_type === 'supply');
          setAgents(supply);
          if (supply.length > 0 && !selectedAgent) {
            setSelectedAgent(supply[0].agent_id);
          }
        }
      } catch { /* */ }
    }
    fetchAgents();
    const iv = setInterval(fetchAgents, 5000);
    return () => clearInterval(iv);
  }, [selectedAgent]);

  function toggleFormat(fmt: string) {
    setFormats(prev => prev.includes(fmt) ? prev.filter(f => f !== fmt) : [...prev, fmt]);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);

    // Find the agent's API key — we need to call as that agent
    // For managed agents, use a special server endpoint instead
    try {
      const res = await fetch(`${API_BASE}/api/v1/opportunities/signal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: selectedAgent,
          signal: {
            content_description: momentDesc,
            subjects: [{ athlete_name: athleteName, school, sport }],
            audience: {
              projected_reach: Number(reach),
              trending_score: Number(trendingScore),
              demographics: 'College athletics fans',
            },
            available_formats: formats,
            min_price: Number(minPrice),
            sport,
            image_id: selectedImage,
            image_url: `/static/demo/${selectedImage}.jpg`,
          },
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Request failed' }));
        const detail = err.detail;
        const msg = Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ')
          : detail || `HTTP ${res.status}`;
        throw new Error(msg);
      }

      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Signal Opportunity</h1>
        <p>Create a content opportunity that demand agents can bid on</p>
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
            <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => setResult(null)}>
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

            <div className="form-group">
              <label className="form-label">Moment Description *</label>
              <textarea className="form-textarea" value={momentDesc} onChange={e => setMomentDesc(e.target.value)}
                placeholder="What happened? Describe the content opportunity..." required />
            </div>

            <div className="form-group">
              <label className="form-label">Moment Image</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                {demoImages.map(img => (
                  <div
                    key={img.id}
                    onClick={() => applyPreset(img.id)}
                    style={{
                      cursor: 'pointer',
                      borderRadius: '8px',
                      overflow: 'hidden',
                      border: selectedImage === img.id ? '2px solid #f97316' : '2px solid rgba(255,255,255,0.08)',
                      transition: 'border-color 0.2s',
                    }}
                  >
                    <img
                      src={`http://localhost:8080${img.url}`}
                      alt={img.label}
                      style={{ width: '100%', aspectRatio: '16/9', objectFit: 'cover', display: 'block' }}
                    />
                    <div style={{ padding: '6px 8px', fontSize: '11px', color: selectedImage === img.id ? '#f97316' : '#888', textAlign: 'center' }}>
                      {img.label}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Athlete Name</label>
                <input className="form-input" value={athleteName} onChange={e => setAthleteName(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">School</label>
                <input className="form-input" value={school} onChange={e => setSchool(e.target.value)} />
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
                <input className="form-input" type="number" value={reach} onChange={e => setReach(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Trending Score (0-10)</label>
                <input className="form-input" type="number" step="0.1" value={trendingScore} onChange={e => setTrendingScore(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Min Price ($)</label>
                <input className="form-input" type="number" value={minPrice} onChange={e => setMinPrice(e.target.value)} />
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
