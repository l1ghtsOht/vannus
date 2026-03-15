import { useState } from 'react';

export default function FeedbackCapture({ query, results }) {
  const [rated, setRated] = useState(false);
  const [copied, setCopied] = useState(false);

  const sendFeedback = (rating) => {
    fetch('/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, tool: 'homepage_search', rating, details: { from_ui: true } }),
    }).catch(() => {});
    setRated(true);
  };

  const copyResults = () => {
    const tools = results?.tools || [];
    let text = `Praxis recommendation for "${query}":\n`;
    tools.slice(0, 8).forEach((t, i) => {
      text += `${i + 1}. ${t.name} (${t._pct}% fit) — ${(t.description || '').slice(0, 80)}\n`;
    });
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="max-w-[640px] mx-auto px-4">
      <div className="flex items-center flex-wrap gap-3 py-4 text-[12px] text-white/30" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        {rated ? (
          <span style={{ color: '#6366f1' }}>Thanks for the feedback!</span>
        ) : (
          <>
            <span>Was this helpful?</span>
            <button onClick={() => sendFeedback(1)} className="px-3 py-1 rounded-lg text-white/50 cursor-pointer transition-all hover:border-[#6366f1] hover:text-[#6366f1]" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>👍 Yes</button>
            <button onClick={() => sendFeedback(-1)} className="px-3 py-1 rounded-lg text-white/50 cursor-pointer transition-all hover:border-[#6366f1] hover:text-[#6366f1]" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>👎 No</button>
          </>
        )}
        <span className="text-white/10">|</span>
        <button onClick={copyResults} className="px-3 py-1 rounded-lg text-white/50 cursor-pointer transition-all hover:border-[#6366f1] hover:text-[#6366f1]" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
          {copied ? '✓ Copied!' : '📋 Copy results'}
        </button>
      </div>
    </div>
  );
}
