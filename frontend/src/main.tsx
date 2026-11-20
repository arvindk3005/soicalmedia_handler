import { FormEvent, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { api, clearToken, setToken } from './api/client';
import './styles.css';

type ReachPotential = {
  score: number;
  tier: 'Low' | 'Moderate' | 'High' | 'Viral Potential';
  hook_strength: number;
  algorithm_alignment: string;
  virality_drivers: string[];
  reach_limiters: string[];
};

type ContentValue = {
  score: number;
  clarity_score: number;
  originality_score: number;
  engagement_depth_score: number;
  value_proposition: string;
  target_audience_fit: string;
  sentiment: string;
};

type ImprovementItem = {
  priority: 'High' | 'Medium' | 'Low';
  category: string;
  issue: string;
  action: string;
  expected_impact: string;
};

type ActionableImprovements = {
  suggested_hooks: string[];
  improvements: ImprovementItem[];
  optimized_rewrite: string;
  cta_suggestion: string;
  hashtags: string[];
};

type Analysis = {
  id?: string;
  overall_score: number;
  executive_summary: string;
  platform: 'linkedin' | 'x' | 'instagram';
  provider: 'gemini' | 'ollama';
  model: string;
  reach_potential: ReachPotential;
  content_value: ContentValue;
  actionable_improvements: ActionableImprovements;
};

type QueryRecord = {
  id: string;
  content: string;
  platform: string;
  provider: string;
  model?: string;
  analysis?: Analysis;
  created_at?: string;
};

function ScoreBar({ label, score }: { label: string; score: number }) {
  const clamped = Math.max(0, Math.min(100, score));
  const tone = clamped >= 75 ? 'high' : clamped >= 50 ? 'mid' : 'low';
  return (
    <div className="score-bar-row">
      <div className="score-bar-meta">
        <span>{label}</span>
        <strong>{clamped}/100</strong>
      </div>
      <div className="score-bar-track">
        <div className={`score-bar-fill ${tone}`} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}

function App() {
  const [authed, setAuthed] = useState<boolean>(Boolean(localStorage.getItem('pulsepilot_token')));
  const [queries, setQueries] = useState<QueryRecord[]>([]);
  const [message, setMessage] = useState('');
  const [platform, setPlatform] = useState<'linkedin' | 'x' | 'instagram'>('linkedin');
  const [provider, setProvider] = useState<'gemini' | 'ollama'>('gemini');
  const [goal, setGoal] = useState<'reach' | 'engagement' | 'leads' | 'brand_awareness'>('reach');
  const [targetAudience, setTargetAudience] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [copiedRewrite, setCopiedRewrite] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);

  const loadHistory = async () => {
    try {
      const data = await api<QueryRecord[]>('/queries');
      setQueries(data);
    } catch (err) {
      console.warn('Could not load query history:', err);
    }
  };

  useEffect(() => {
    if (authed) {
      loadHistory();
    }
  }, [authed]);

  async function authenticate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    const form = new FormData(e.currentTarget);
    try {
      const path = isRegistering ? '/auth/register' : '/auth/login';
      const payload = isRegistering
        ? { name: form.get('name'), email: form.get('email'), password: form.get('password') }
        : { email: form.get('email'), password: form.get('password') };

      const res = await api<{ access_token: string }>(path, {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setToken(res.access_token);
      setAuthed(true);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function handleAnalyse(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError('');
    setCopiedRewrite(false);

    try {
      let attachmentId: string | undefined = undefined;

      if (file) {
        const formData = new FormData();
        formData.append('file', file);
        const uploadRes = await api<{ id: string }>('/uploads', {
          method: 'POST',
          body: formData,
        });
        attachmentId = uploadRes.id;
      }

      const result = await api<Analysis>('/analysis', {
        method: 'POST',
        body: JSON.stringify({
          content: message,
          platform,
          attachment_id: attachmentId,
          provider,
          goal,
          target_audience: targetAudience.trim() || undefined,
        }),
      });

      setAnalysis(result);

      await api('/posts', {
        method: 'POST',
        body: JSON.stringify({
          content: message,
          platform,
          impressions: 0,
          engagement: 0,
          analysis: result,
        }),
      }).catch(console.warn);

      await loadHistory();
      setFile(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function copyRewrite(text: string) {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedRewrite(true);
      setTimeout(() => setCopiedRewrite(false), 2000);
    });
  }

  if (!authed) {
    return (
      <main className="auth">
        <section>
          <p className="eyebrow">PULSEPILOT AI</p>
          <h1>Make every post more intentional.</h1>
          <p className="muted">
            {isRegistering
              ? 'Create your workspace to start analyzing reach potential, content value, and improvements with Gemini & Ollama.'
              : 'Sign in to access your private content intelligence workspace.'}
          </p>

          <form onSubmit={authenticate}>
            {isRegistering && (
              <div>
                <input name="name" placeholder="Your full name" minLength={2} required />
              </div>
            )}
            <div>
              <input name="email" type="email" placeholder="Email address" required />
            </div>
            <div>
              <input
                name="password"
                type="password"
                placeholder="Password (minimum 8 characters)"
                minLength={8}
                required
              />
            </div>
            <button disabled={busy} style={{ width: '100%', marginTop: '8px' }}>
              {busy ? (isRegistering ? 'Creating workspace…' : 'Signing in…') : isRegistering ? 'Create workspace' : 'Sign in'}
            </button>
          </form>

          {error && <div className="error-banner">{error}</div>}

          <p className="switch">
            {isRegistering ? 'Already have an account?' : 'New to PulsePilot?'}{' '}
            <button
              type="button"
              className="link"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError('');
              }}
            >
              {isRegistering ? 'Sign in' : 'Create an account'}
            </button>
          </p>
        </section>
      </main>
    );
  }

  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">PULSEPILOT AI</p>
          <h1>Social Content Intelligence</h1>
        </div>
        <button
          className="quiet"
          onClick={() => {
            clearToken();
            setAuthed(false);
          }}
        >
          Sign out
        </button>
      </header>

      <section className="grid">
        <div className="card composer">
          <h2>Analyze & Optimize Post</h2>
          <form onSubmit={handleAnalyse}>
            <div className="form-row">
              <div className="form-group">
                <label>Target Platform</label>
                <select value={platform} onChange={(e) => setPlatform(e.target.value as any)}>
                  <option value="linkedin">LinkedIn</option>
                  <option value="x">X (formerly Twitter)</option>
                  <option value="instagram">Instagram</option>
                </select>
              </div>

              <div className="form-group">
                <label>AI Intelligence Engine</label>
                <select value={provider} onChange={(e) => setProvider(e.target.value as any)}>
                  <option value="gemini">Google Gemini (Cloud AI)</option>
                  <option value="ollama">Ollama (Localhost AI)</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Primary Goal</label>
                <select value={goal} onChange={(e) => setGoal(e.target.value as any)}>
                  <option value="reach">Maximize Reach</option>
                  <option value="engagement">Spark Engagement</option>
                  <option value="leads">Generate Leads</option>
                  <option value="brand_awareness">Brand Awareness</option>
                </select>
              </div>

              <div className="form-group">
                <label>Target Audience (Optional)</label>
                <input
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  placeholder="e.g., B2B SaaS founders, AI engineers"
                  maxLength={200}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Draft Content</label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Paste your draft caption, hook, or article excerpt here…"
                required
                minLength={3}
              />
            </div>

            <div className="upload-section">
              <label htmlFor="file-upload" className="upload-btn">
                📎 Attach PDF or Image
              </label>
              <input
                id="file-upload"
                type="file"
                accept="image/*,application/pdf"
                style={{ display: 'none' }}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />

              {file && (
                <span className="file-indicator">
                  📄 {file.name}
                  <button type="button" className="link" onClick={() => setFile(null)} style={{ color: '#ff9aa2', marginLeft: '6px' }}>
                    Remove
                  </button>
                </span>
              )}
            </div>

            <button disabled={busy} style={{ width: '100%', marginTop: '6px' }}>
              {busy ? `Analyzing via ${provider.toUpperCase()}…` : `Run AI Analysis (${provider.toUpperCase()})`}
            </button>
          </form>

          {error && <div className="error-banner">{error}</div>}
        </div>

        <div className="card">
          <h2>Saved Queries & Posts</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            Stored securely in MongoDB.
          </p>

          <div className="history-list">
            {queries.length > 0 ? (
              queries.map((q) => (
                <div
                  key={q.id}
                  className="history-item"
                  onClick={() => {
                    if (q.analysis && q.analysis.reach_potential) {
                      setAnalysis(q.analysis);
                    }
                    setMessage(q.content);
                    if (q.platform) setPlatform(q.platform as any);
                  }}
                  title="Click to view full analysis"
                >
                  <div className="history-item-header">
                    <span className="badge badge-platform">{q.platform}</span>
                    <span className={`badge ${q.provider === 'gemini' ? 'badge-gemini' : 'badge-ollama'}`}>
                      {q.provider}
                    </span>
                    {typeof q.analysis?.overall_score === 'number' && (
                      <span className="badge badge-score">{q.analysis.overall_score}/100</span>
                    )}
                    {q.analysis?.reach_potential?.tier && (
                      <span className="badge badge-sentiment">{q.analysis.reach_potential.tier}</span>
                    )}
                  </div>
                  <p>{q.content}</p>
                </div>
              ))
            ) : (
              <p className="muted">Your saved analyses and queries will appear here once submitted.</p>
            )}
          </div>
        </div>
      </section>

      {analysis && (
        <section className="result card">
          <div className="result-header">
            <span className={`badge ${analysis.provider === 'gemini' ? 'badge-gemini' : 'badge-ollama'}`}>
              Powered by {analysis.provider.toUpperCase()} ({analysis.model})
            </span>
            <span className="badge badge-platform">{analysis.platform}</span>
            <span className="badge badge-sentiment">{analysis.content_value.sentiment}</span>
            <span className="badge badge-tier">Reach: {analysis.reach_potential.tier}</span>
          </div>

          <div className="scorecards">
            <div className="scorecard highlight">
              <span className="scorecard-label">Overall Score</span>
              <strong className="scorecard-value">{analysis.overall_score}</strong>
            </div>
            <div className="scorecard">
              <span className="scorecard-label">Reach Potential</span>
              <strong className="scorecard-value">{analysis.reach_potential.score}</strong>
            </div>
            <div className="scorecard">
              <span className="scorecard-label">Content Value</span>
              <strong className="scorecard-value">{analysis.content_value.score}</strong>
            </div>
            <div className="scorecard">
              <span className="scorecard-label">Hook Strength</span>
              <strong className="scorecard-value">{analysis.reach_potential.hook_strength}</strong>
            </div>
          </div>

          <div className="result-section">
            <h4>Executive Summary</h4>
            <p>{analysis.executive_summary}</p>
          </div>

          <div className="analysis-columns">
            <div className="result-section">
              <h4>Reach Potential Breakdown</h4>
              <p className="subcopy">{analysis.reach_potential.algorithm_alignment}</p>
              <div className="pill-list-group">
                <strong>Virality Drivers</strong>
                <ul>
                  {analysis.reach_potential.virality_drivers.map((item, idx) => (
                    <li key={idx}>+ {item}</li>
                  ))}
                </ul>
              </div>
              {analysis.reach_potential.reach_limiters.length > 0 && (
                <div className="pill-list-group limiters">
                  <strong>Reach Limiters</strong>
                  <ul>
                    {analysis.reach_potential.reach_limiters.map((item, idx) => (
                      <li key={idx}>- {item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="result-section">
              <h4>Content Value Breakdown</h4>
              <ScoreBar label="Clarity & Scannability" score={analysis.content_value.clarity_score} />
              <ScoreBar label="Originality" score={analysis.content_value.originality_score} />
              <ScoreBar label="Engagement Depth" score={analysis.content_value.engagement_depth_score} />
              <div className="meta-detail">
                <strong>Value Proposition:</strong> {analysis.content_value.value_proposition}
              </div>
              <div className="meta-detail">
                <strong>Audience Fit:</strong> {analysis.content_value.target_audience_fit}
              </div>
            </div>
          </div>

          <div className="result-section">
            <h4>Alternative Hooks</h4>
            <ul className="hooks-list">
              {analysis.actionable_improvements.suggested_hooks.map((hook, idx) => (
                <li key={idx}>"{hook}"</li>
              ))}
            </ul>
          </div>

          <div className="result-section">
            <h4>Prioritized Actionable Improvements</h4>
            <div className="improvements-grid">
              {analysis.actionable_improvements.improvements.map((imp, idx) => (
                <div key={idx} className="improvement-card">
                  <div className="improvement-card-header">
                    <span className={`badge badge-priority-${imp.priority.toLowerCase()}`}>{imp.priority}</span>
                    <span className="badge badge-platform">{imp.category}</span>
                  </div>
                  <p><strong>Issue:</strong> {imp.issue}</p>
                  <p><strong>Action:</strong> {imp.action}</p>
                  <p className="muted-impact"><strong>Expected Impact:</strong> {imp.expected_impact}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="result-section">
            <div className="rewrite-header">
              <h4>Optimized Rewrite</h4>
              <button
                type="button"
                className="quiet small-btn"
                onClick={() => copyRewrite(analysis.actionable_improvements.optimized_rewrite)}
              >
                {copiedRewrite ? 'Copied!' : 'Copy Rewrite'}
              </button>
            </div>
            <pre className="rewrite-box">{analysis.actionable_improvements.optimized_rewrite}</pre>
            <div className="meta-detail" style={{ marginTop: '12px' }}>
              <strong>Recommended CTA:</strong> {analysis.actionable_improvements.cta_suggestion}
            </div>
          </div>

          <div>
            <h4 style={{ margin: '14px 0 6px', fontSize: '0.85rem', color: '#8db5ff', textTransform: 'uppercase' }}>
              Discovery Hashtags
            </h4>
            <div className="hashtags-container">
              {analysis.actionable_improvements.hashtags.map((tag) => (
                <span key={tag}>{tag.startsWith('#') ? tag : `#${tag}`}</span>
              ))}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
