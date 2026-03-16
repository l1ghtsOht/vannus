import { useState } from 'react';
import { submitToolFeedback } from '../utils/feedback';

const FLAG_OPTIONS = [
  { value: 'wrong_tier', label: 'Wrong tier' },
  { value: 'wrong_score', label: 'Wrong score' },
  { value: 'outdated_info', label: 'Outdated info' },
  { value: 'missing_badge', label: 'Missing badge' },
  { value: 'other', label: 'Other' },
];

export default function ToolFlag({ sessionId, toolName, currentTier }) {
  const [isOpen, setIsOpen] = useState(false);
  const [flagType, setFlagType] = useState('wrong_tier');
  const [reason, setReason] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    submitToolFeedback(sessionId, toolName, currentTier, null, flagType, reason || null);
    setSubmitted(true);
  };

  if (submitted) {
    return <span style={{ fontSize: 11, color: '#34d399' }}>{'\u2713'} Flagged</span>;
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        style={{ fontSize: 11, color: 'rgba(255,255,255,0.2)', background: 'none', border: 'none', cursor: 'pointer', transition: 'color 0.2s' }}
        onMouseEnter={e => e.target.style.color = 'rgba(255,255,255,0.4)'}
        onMouseLeave={e => e.target.style.color = 'rgba(255,255,255,0.2)'}
      >
        {'\u2691'} Flag rating
      </button>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, transition: 'opacity 0.3s ease' }}>
      <select
        value={flagType}
        onChange={e => setFlagType(e.target.value)}
        style={{
          background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 8, padding: '4px 8px', fontSize: 11, color: 'rgba(255,255,255,0.5)',
          outline: 'none', cursor: 'pointer',
        }}
      >
        {FLAG_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <input
        type="text"
        value={reason}
        onChange={e => setReason(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') handleSubmit(); }}
        placeholder="Optional reason..."
        style={{
          background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 8, padding: '4px 8px', fontSize: 11, color: '#f0f0f5',
          outline: 'none', width: 120,
        }}
      />
      <button
        onClick={handleSubmit}
        style={{
          fontSize: 11, padding: '4px 10px', borderRadius: 8, cursor: 'pointer',
          background: 'transparent', border: '1px solid rgba(255,255,255,0.08)',
          color: 'rgba(255,255,255,0.4)', transition: 'all 0.2s',
        }}
      >
        Submit
      </button>
    </div>
  );
}
