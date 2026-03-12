const PATTERN_STYLES = {
  SINGLE:      { icon: '◉', color: '#6366f1', label: 'Single' },
  FAN_OUT:     { icon: '⋔', color: '#06b6d4', label: 'Fan-Out' },
  CHAIN:       { icon: '⟿', color: '#f59e0b', label: 'Chain' },
  CONSENSUS:   { icon: '◎', color: '#10b981', label: 'Consensus' },
  ADVERSARIAL: { icon: '⚔', color: '#ef4444', label: 'Adversarial' },
};

export default function PatternBadge({ strategy }) {
  const style = PATTERN_STYLES[strategy] || PATTERN_STYLES.SINGLE;

  return (
    <span
      className="inline-flex items-center gap-1.5 text-[10px] font-medium px-2 py-0.5 rounded-full uppercase tracking-wider"
      style={{
        backgroundColor: `${style.color}15`,
        color: `${style.color}cc`,
        border: `1px solid ${style.color}25`,
      }}
    >
      <span>{style.icon}</span>
      <span>{style.label}</span>
    </span>
  );
}
