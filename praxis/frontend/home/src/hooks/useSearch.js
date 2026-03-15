import { useState, useCallback } from 'react';

export default function useSearch() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState('');

  const search = useCallback(async (query) => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setLastQuery(query);
    try {
      const res = await fetch('/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const tools = Array.isArray(data) ? data : (data.results || []);
      const totalTools = data.total_tools || data.tools_considered || 253;

      // Normalize scores
      const maxScore = tools.length ? Math.max(...tools.map(t => t.fit_score || t.score || t.confidence || 0)) : 1;
      const normalized = tools.map(t => {
        const raw = t.fit_score || t.score || t.confidence || 0;
        return { ...t, _pct: maxScore > 0 ? Math.min(99, Math.round((raw / maxScore) * 95 + 5)) : 50 };
      }).sort((a, b) => b._pct - a._pct);

      setResults({ tools: normalized, totalTools, eliminatedCount: Math.max(0, totalTools - normalized.length) });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return { results, loading, error, lastQuery, search, reset };
}
