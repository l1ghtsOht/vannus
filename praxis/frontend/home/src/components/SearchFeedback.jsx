import { useState } from 'react';
import { submitSearchFeedback } from '../utils/feedback';

export default function SearchFeedback({ sessionId, queryText, constraints, survivors, eliminatedCount }) {
  const [rating, setRating] = useState(null);
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleUp = () => {
    setRating('up');
    submitSearchFeedback(sessionId, queryText, constraints, survivors, eliminatedCount, 'up', null);
    setTimeout(() => setSubmitted(true), 300);
  };

  const handleDown = () => {
    setRating('down');
  };

  const handleCommentSubmit = () => {
    submitSearchFeedback(sessionId, queryText, constraints, survivors, eliminatedCount, 'down', comment || null);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="max-w-[640px] mx-auto px-4" style={{ textAlign: 'center', padding: '16px 0', opacity: 0.5, transition: 'opacity 2s ease' }}>
        <span style={{ fontSize: 13, color: '#34d399' }}>{'\u2713'} Thanks for the feedback</span>
      </div>
    );
  }

  return (
    <div className="max-w-[640px] mx-auto px-4" style={{ textAlign: 'center', padding: '16px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
        <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.35)' }}>Was this helpful?</span>

        <button
          onClick={handleUp}
          style={{
            width: 28, height: 28, borderRadius: '50%', border: `1px solid ${rating === 'up' ? 'rgba(99,102,241,0.4)' : 'rgba(255,255,255,0.08)'}`,
            background: rating === 'up' ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.04)',
            cursor: 'pointer', fontSize: 14, lineHeight: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s ease',
          }}
        >
          {'\uD83D\uDC4D'}
        </button>

        <button
          onClick={handleDown}
          style={{
            width: 28, height: 28, borderRadius: '50%', border: `1px solid ${rating === 'down' ? 'rgba(99,102,241,0.4)' : 'rgba(255,255,255,0.08)'}`,
            background: rating === 'down' ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.04)',
            cursor: 'pointer', fontSize: 14, lineHeight: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s ease',
          }}
        >
          {'\uD83D\uDC4E'}
        </button>
      </div>

      {rating === 'down' && !submitted && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 12, opacity: 1, transition: 'opacity 0.3s ease' }}>
          <input
            type="text"
            value={comment}
            onChange={e => setComment(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleCommentSubmit(); }}
            placeholder="What was wrong?"
            style={{
              background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 12, padding: '8px 14px', fontSize: 13, color: '#f0f0f5',
              outline: 'none', width: 240,
            }}
          />
          <button
            onClick={handleCommentSubmit}
            style={{
              width: 28, height: 28, borderRadius: '50%', background: '#6366f1',
              border: 'none', color: 'white', cursor: 'pointer', display: 'flex',
              alignItems: 'center', justifyContent: 'center', fontSize: 12,
            }}
          >
            {'\u2192'}
          </button>
        </div>
      )}
    </div>
  );
}
