import { useState } from 'react';
import type { OrgCredentials } from '../types';

const API_BASE = 'http://localhost:8080';

const CONTENT_FORMATS = [
  { value: 'gameday_graphic', label: 'Gameday Graphic' },
  { value: 'highlight_reel', label: 'Highlight Reel' },
  { value: 'social_post', label: 'Social Post' },
  { value: 'story', label: 'Story' },
  { value: 'video_clip', label: 'Video Clip' },
];
const SPORTS = [
  { value: 'basketball', label: 'Basketball' },
  { value: 'football', label: 'Football' },
  { value: 'soccer', label: 'Soccer' },
  { value: 'baseball', label: 'Baseball' },
  { value: 'track', label: 'Track' },
  { value: 'swimming', label: 'Swimming' },
  { value: 'other', label: 'Other' },
];

export default function Onboarding() {
  // Org form state
  const [orgName, setOrgName] = useState('');
  const [orgDomain, setOrgDomain] = useState('');
  const [monthlyBudget, setMonthlyBudget] = useState('');
  const [perDealBudget, setPerDealBudget] = useState('');
  const [competitors, setCompetitors] = useState('');
  const [orgCreds, setOrgCreds] = useState<OrgCredentials | null>(null);
  const [orgLoading, setOrgLoading] = useState(false);
  const [orgError, setOrgError] = useState('');

  // Agent form state
  const [agentType, setAgentType] = useState<'supply' | 'demand'>('demand');
  const [agentName, setAgentName] = useState('');
  const [agentDesc, setAgentDesc] = useState('');
  // Demand-specific
  const [brandTone, setBrandTone] = useState('');
  const [tagline, setTagline] = useState('');
  const [budgetPerDeal, setBudgetPerDeal] = useState('');
  // Supply-specific
  const [contentFormats, setContentFormats] = useState<string[]>([]);
  const [sports, setSports] = useState<string[]>([]);
  const [turnaround, setTurnaround] = useState('60');

  const [agentLoading, setAgentLoading] = useState(false);
  const [agentError, setAgentError] = useState('');
  const [agentSuccess, setAgentSuccess] = useState<Record<string, string> | null>(null);
  const [copied, setCopied] = useState('');

  async function handleOrgSubmit(e: React.FormEvent) {
    e.preventDefault();
    setOrgError('');
    setOrgLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/orgs/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: orgName,
          domain: orgDomain || undefined,
          budget_monthly_max: monthlyBudget ? Number(monthlyBudget) : undefined,
          budget_per_deal_max: perDealBudget ? Number(perDealBudget) : undefined,
          competitor_exclusions: competitors
            ? competitors.split(',').map((s) => s.trim()).filter(Boolean)
            : [],
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

      const data: OrgCredentials = await res.json();
      setOrgCreds(data);
    } catch (err) {
      setOrgError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setOrgLoading(false);
    }
  }

  async function handleAgentSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!orgCreds) return;
    setAgentError('');
    setAgentLoading(true);

    // Build type-specific profile matching server schemas
    const extra: Record<string, unknown> = {};
    if (agentType === 'demand') {
      extra.brand_profile = {
        tone: brandTone || '',
        tagline: tagline || '',
        budget_per_deal_max: budgetPerDeal ? Number(budgetPerDeal) : 5000,
      };
    } else {
      extra.supply_capabilities = {
        content_formats: contentFormats,
        sports: sports,
        turnaround_minutes: turnaround ? Number(turnaround) : 60,
      };
    }

    try {
      // Use managed agent endpoint — creates + starts the agent with Claude
      const res = await fetch(`${API_BASE}/api/v1/agents/managed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${orgCreds.org_key}`,
        },
        body: JSON.stringify({
          name: agentName,
          agent_type: agentType,
          organization: orgName,
          description: agentDesc || undefined,
          ...extra,
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

      const data = await res.json();
      setAgentSuccess(data);
    } catch (err) {
      setAgentError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setAgentLoading(false);
    }
  }

  function copyToClipboard(text: string, label: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(''), 2000);
    });
  }

  function toggleArrayItem(arr: string[], item: string, setter: (v: string[]) => void) {
    if (arr.includes(item)) {
      setter(arr.filter((x) => x !== item));
    } else {
      setter([...arr, item]);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Onboard</h1>
        <p>Register an organization and create managed agents</p>
      </div>

      <div className="onboarding-sections">
        {/* Section 1: Create Organization */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Create Organization</span>
          </div>

          {orgCreds ? (
            <div className="credentials-card">
              <h3>Organization Created</h3>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
                {orgCreds.message}
              </p>

              <div className="credential-row">
                <span className="credential-label">Org ID</span>
                <span
                  className="credential-value"
                  onClick={() => copyToClipboard(orgCreds.org_id, 'org_id')}
                  title="Click to copy"
                >
                  {orgCreds.org_id}
                  {copied === 'org_id' && ' (copied)'}
                </span>
              </div>
              <div className="credential-row">
                <span className="credential-label">Org Key</span>
                <span
                  className="credential-value"
                  onClick={() => copyToClipboard(orgCreds.org_key, 'org_key')}
                  title="Click to copy"
                >
                  {orgCreds.org_key}
                  {copied === 'org_key' && ' (copied)'}
                </span>
              </div>
              <div className="credential-row">
                <span className="credential-label">Protocol URL</span>
                <span
                  className="credential-value"
                  onClick={() => copyToClipboard(orgCreds.protocol_url, 'url')}
                  title="Click to copy"
                >
                  {orgCreds.protocol_url}
                  {copied === 'url' && ' (copied)'}
                </span>
              </div>
              <p className="copy-hint">Click any value to copy. Give these credentials to your agent.</p>
            </div>
          ) : (
            <form onSubmit={handleOrgSubmit}>
              <div className="form-group">
                <label className="form-label">Organization Name *</label>
                <input
                  className="form-input"
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="e.g., Nike, Pixology"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Domain (optional)</label>
                <input
                  className="form-input"
                  type="text"
                  value={orgDomain}
                  onChange={(e) => setOrgDomain(e.target.value)}
                  placeholder="e.g., sportswear, content-creation"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Monthly Budget ($)</label>
                <input
                  className="form-input"
                  type="number"
                  value={monthlyBudget}
                  onChange={(e) => setMonthlyBudget(e.target.value)}
                  placeholder="50000"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Per-Deal Budget ($)</label>
                <input
                  className="form-input"
                  type="number"
                  value={perDealBudget}
                  onChange={(e) => setPerDealBudget(e.target.value)}
                  placeholder="5000"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Competitor Exclusions (comma-separated)</label>
                <input
                  className="form-input"
                  type="text"
                  value={competitors}
                  onChange={(e) => setCompetitors(e.target.value)}
                  placeholder="e.g., Adidas, Puma"
                />
              </div>

              {orgError && (
                <p style={{ color: 'var(--red)', fontSize: '13px', marginBottom: '12px' }}>
                  {orgError}
                </p>
              )}

              <button className="btn btn-primary" type="submit" disabled={orgLoading || !orgName}>
                {orgLoading ? 'Creating...' : 'Create Organization'}
              </button>
            </form>
          )}
        </div>

        {/* Section 2: Create Managed Agent */}
        {orgCreds && (
          <div className="card">
            <div className="card-header">
              <span className="card-title">Create Managed Agent</span>
            </div>

            {agentSuccess ? (
              <div className="success-card">
                <h3>Agent Created</h3>
                <p style={{ color: 'var(--text-secondary)' }}>
                  Agent <strong>{agentSuccess.name || agentName}</strong> is now registered
                  and ready to participate on the exchange.
                </p>
                {agentSuccess.agent_id && (
                  <p style={{ marginTop: '8px' }}>
                    <code>Agent ID: {agentSuccess.agent_id}</code>
                  </p>
                )}
              </div>
            ) : (
              <form onSubmit={handleAgentSubmit}>
                <div className="form-group">
                  <label className="form-label">Agent Type</label>
                  <div className="toggle-group">
                    <button
                      type="button"
                      className={`toggle-option ${agentType === 'supply' ? 'active' : ''}`}
                      onClick={() => setAgentType('supply')}
                    >
                      Supply
                    </button>
                    <button
                      type="button"
                      className={`toggle-option ${agentType === 'demand' ? 'active' : ''}`}
                      onClick={() => setAgentType('demand')}
                    >
                      Demand
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Agent Name *</label>
                  <input
                    className="form-input"
                    type="text"
                    value={agentName}
                    onChange={(e) => setAgentName(e.target.value)}
                    placeholder="e.g., Nike NIL Agent"
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    className="form-textarea"
                    value={agentDesc}
                    onChange={(e) => setAgentDesc(e.target.value)}
                    placeholder="What does this agent do?"
                  />
                </div>

                {agentType === 'demand' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Brand Tone</label>
                      <input
                        className="form-input"
                        type="text"
                        value={brandTone}
                        onChange={(e) => setBrandTone(e.target.value)}
                        placeholder="e.g., Bold, premium, aspirational"
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Tagline</label>
                      <input
                        className="form-input"
                        type="text"
                        value={tagline}
                        onChange={(e) => setTagline(e.target.value)}
                        placeholder="e.g., Just Do It"
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Budget per Deal ($)</label>
                      <input
                        className="form-input"
                        type="number"
                        value={budgetPerDeal}
                        onChange={(e) => setBudgetPerDeal(e.target.value)}
                        placeholder="5000"
                      />
                    </div>
                  </>
                )}

                {agentType === 'supply' && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Content Formats</label>
                      <div className="checkbox-group">
                        {CONTENT_FORMATS.map((fmt) => (
                          <label key={fmt.value} className="checkbox-label">
                            <input
                              type="checkbox"
                              checked={contentFormats.includes(fmt.value)}
                              onChange={() => toggleArrayItem(contentFormats, fmt.value, setContentFormats)}
                            />
                            {fmt.label}
                          </label>
                        ))}
                      </div>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Sports</label>
                      <div className="checkbox-group">
                        {SPORTS.map((sport) => (
                          <label key={sport.value} className="checkbox-label">
                            <input
                              type="checkbox"
                              checked={sports.includes(sport.value)}
                              onChange={() => toggleArrayItem(sports, sport.value, setSports)}
                            />
                            {sport.label}
                          </label>
                        ))}
                      </div>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Turnaround (minutes)</label>
                      <input
                        className="form-input"
                        type="number"
                        value={turnaround}
                        onChange={(e) => setTurnaround(e.target.value)}
                        placeholder="60"
                      />
                    </div>
                  </>
                )}

                {agentError && (
                  <p style={{ color: 'var(--red)', fontSize: '13px', marginBottom: '12px' }}>
                    {agentError}
                  </p>
                )}

                <button className="btn btn-primary" type="submit" disabled={agentLoading || !agentName}>
                  {agentLoading ? 'Creating...' : 'Create Agent'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
