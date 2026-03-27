import { useState, useEffect, useMemo } from 'react';
import SearchFilter from './components/SearchFilter';
import TierSection from './components/TierSection';
import ToolCardFull from './components/ToolCardFull';
import ToolCardCompact from './components/ToolCardCompact';

function Nav() {
  return (
    <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, padding: '0.65rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2rem', background: 'rgba(6,6,14,0.75)', backdropFilter: 'blur(30px)', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
      <a href="/" style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f0f0f5', textDecoration: 'none', letterSpacing: '-0.5px' }}>Praxis</a>
      <a href="/static/tools.html" style={{ fontSize: '0.82rem', fontWeight: 500, color: '#6366f1', textDecoration: 'none' }}>Tools</a>
      <a href="/static/differential.html" style={{ fontSize: '0.82rem', fontWeight: 500, color: 'rgba(255,255,255,0.55)', textDecoration: 'none' }}>Diagnosis</a>
      <a href="/journey" style={{ fontSize: '0.82rem', fontWeight: 500, color: 'rgba(255,255,255,0.55)', textDecoration: 'none' }}>Build My Stack</a>
      <a href="/static/manifesto.html" style={{ fontSize: '0.82rem', fontWeight: 500, color: 'rgba(255,255,255,0.55)', textDecoration: 'none' }}>Methodology</a>
      <a href="/static/pricing.html" style={{ fontSize: '0.82rem', fontWeight: 500, color: 'rgba(255,255,255,0.55)', textDecoration: 'none' }}>Pricing</a>
    </nav>
  );
}

function Footer() {
  return (
    <footer style={{ background: 'rgba(0,0,0,0.3)', borderTop: '1px solid rgba(255,255,255,0.06)', padding: '48px 40px 24px', marginTop: 40 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32, maxWidth: 800, margin: '0 auto' }}>
        <div><div style={{ fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 12 }}>Product</div><a href="/static/tools.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>All Tools</a><a href="/static/differential.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>Diagnosis</a><a href="/journey" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>Build My Stack</a><a href="/room" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>Room</a></div>
        <div><div style={{ fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 12 }}>Resources</div><a href="/static/tuesday-test.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>ROI Calculator</a><a href="/static/rfp.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>RFP Builder</a><a href="/static/stack-advisor.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>Stack Advisor</a><a href="/static/trust_badges.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>Trust Badges</a></div>
        <div><div style={{ fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 12 }}>Company</div><a href="/static/pricing.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>Pricing</a><a href="/static/manifesto.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>Methodology</a><a href="/static/partners.html" style={{ display: 'block', fontSize: 13, color: 'rgba(255,255,255,0.35)', textDecoration: 'none', lineHeight: 2 }}>Partners</a></div>
      </div>
      <div style={{ maxWidth: 800, margin: '32px auto 0', paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: 11, color: 'rgba(255,255,255,0.25)', textAlign: 'center' }}>&copy; 2026 Praxis AI</div>
    </footer>
  );
}

function FragileAccordion({ tools }) {
  const [open, setOpen] = useState(false);
  if (!tools || tools.length === 0) return null;
  return (
    <div className="max-w-5xl mx-auto px-4" style={{ marginBottom: 40 }}>
      <button onClick={() => setOpen(!open)} style={{ width: '100%', textAlign: 'left', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: '14px 20px', color: 'rgba(239,68,68,0.7)', fontSize: 14, cursor: 'pointer', transition: 'all 0.2s ease', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ transform: open ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s', display: 'inline-block' }}>▸</span>
        {open ? 'Hide' : 'Show'} {tools.length} High-Risk / API-Dependent Tools
      </button>
      {open && (
        <div style={{ marginTop: 8 }}>
          <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', marginBottom: 12, padding: '0 4px' }}>These tools have limited compliance, depend on external APIs, or lack proven durability. Use with caution.</p>
          {tools.map(t => (
            <div key={t.name} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 4px', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: 13 }}>
              <span style={{ color: '#f0f0f5', fontWeight: 500, minWidth: 120, flexShrink: 0 }}>{t.name}</span>
              <span style={{ color: 'rgba(255,255,255,0.3)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.description}</span>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#ef4444', flexShrink: 0 }}>{t.grade}</span>
              <a href={`/room?q=${encodeURIComponent(t.name)}`} style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', textDecoration: 'none', flexShrink: 0 }}>Evaluate →</a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [activeTier, setActiveTier] = useState('all');
  const [sortBy, setSortBy] = useState('rank');

  useEffect(() => {
    fetch('/tools/tiered')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const tiers = data?.tiers || {};
  const counts = useMemo(() => ({
    total: data?.counts ? Object.values(data.counts).reduce((a, b) => a + b, 0) : 0,
    sovereign: data?.counts?.sovereign || 0,
    durable: data?.counts?.durable || 0,
    moderate: data?.counts?.moderate || 0,
  }), [data]);

  const filterAndSort = (tools) => {
    if (!tools) return [];
    let filtered = tools;
    if (query.trim()) {
      const q = query.toLowerCase();
      filtered = tools.filter(t => t.name.toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q) || (t.categories || []).join(' ').toLowerCase().includes(q));
    }
    const sorted = [...filtered];
    if (sortBy === 'name_asc') sorted.sort((a, b) => a.name.localeCompare(b.name));
    else if (sortBy === 'name_desc') sorted.sort((a, b) => b.name.localeCompare(a.name));
    else if (sortBy === 'compliance') sorted.sort((a, b) => (b.compliance?.length || 0) - (a.compliance?.length || 0));
    else sorted.sort((a, b) => (b.resilience_score || 0) - (a.resilience_score || 0));
    return sorted;
  };

  const sovereign = filterAndSort(tiers.sovereign);
  const durable = filterAndSort(tiers.durable);
  const moderate = filterAndSort(tiers.moderate);
  const fragileWrapper = filterAndSort([...(tiers.fragile || []), ...(tiers.wrapper || [])]);

  const showTier = (t) => activeTier === 'all' || activeTier === t;

  return (
    <div style={{ minHeight: '100vh' }}>
      <Nav />
      <div style={{ paddingTop: 80 }}>
        <div className="max-w-5xl mx-auto px-4" style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, color: '#f0f0f5', marginBottom: 6 }}>Tools</h1>
          <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.4)' }}>253 AI tools scored across 6 architectural dimensions. Ranked by survival, not popularity.</p>
        </div>

        <SearchFilter query={query} onQueryChange={setQuery} activeTier={activeTier} onTierChange={setActiveTier} sortBy={sortBy} onSortChange={setSortBy} counts={counts} />

        {loading && (
          <div className="max-w-5xl mx-auto px-4" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
            {[0,1,2,3,4,5].map(i => <div key={i} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 16, height: 200, animation: 'pulse 1.5s ease infinite' }} />)}
          </div>
        )}

        {!loading && query && sovereign.length === 0 && durable.length === 0 && moderate.length === 0 && fragileWrapper.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: 24, opacity: 0.2, marginBottom: 8 }}>∅</div>
            <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.3)' }}>No tools match "{query}"</p>
            <button onClick={() => setQuery('')} style={{ marginTop: 12, fontSize: 13, color: '#6366f1', background: 'none', border: 'none', cursor: 'pointer' }}>Clear search</button>
          </div>
        )}

        {showTier('sovereign') && <TierSection tier="sovereign" tools={sovereign} CardComponent={ToolCardFull} columns={3} />}
        {showTier('durable') && <TierSection tier="durable" tools={durable} CardComponent={ToolCardFull} columns={3} />}
        {showTier('moderate') && <TierSection tier="moderate" tools={moderate} CardComponent={ToolCardCompact} columns={1} />}
        {(activeTier === 'all') && <FragileAccordion tools={fragileWrapper} />}

        <Footer />
      </div>
    </div>
  );
}
