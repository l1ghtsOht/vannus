const TASK_LABELS = {
  writing: 'writing tools', coding: 'coding tools', analytics: 'analytics tools',
  automation: 'automation tools', support: 'customer support tools', appbuilding: 'app-building tools',
};

// Label text appended to query when constraint pill is active.
// Keep in sync with CONSTRAINTS in ConstraintPills.jsx and CONSTRAINT_LABELS in App.jsx.
const CONSTRAINT_LABELS = {
  free_tier:   'free',
  budget_20:   'under $20/mo',
  beginner:    'beginner-friendly',
  no_code:     'no-code',
  open_source: 'open source',
  api_access:  'API access',
  soc2:        'SOC 2 certified',
  gdpr:        'GDPR compliant',
  self_hosted: 'self-hosted',
  no_training: 'no training on data',
};

export default function LiveSummary({ task, constraints, query, onSubmit, toolCount = 254 }) {
  const taskLabel = task ? TASK_LABELS[task] : null;
  const constraintList = [...constraints].map(c => CONSTRAINT_LABELS[c] || c);
  const constraintStr = constraintList.length
    ? constraintList.map(c => `<span style="color:#a5b4fc">${c}</span>`).join(', ')
    : '';

  let html;
  if (query && query.length >= 3) {
    html = `Search: <strong style="color:#f0f0f5">"${query.slice(0, 60)}"</strong>${constraintStr ? ' with ' + constraintStr : ''} — then eliminate the rest.`;
  } else if (taskLabel && constraintStr) {
    html = `Find <strong style="color:#f0f0f5">${taskLabel}</strong> that are ${constraintStr} — then eliminate the rest.`;
  } else if (taskLabel) {
    html = `Find <strong style="color:#f0f0f5">${taskLabel}</strong> — then eliminate the rest.`;
  } else if (constraintStr) {
    html = `Find tools that are ${constraintStr} — then eliminate the rest.`;
  } else {
    html = 'Describe what you need above, or pick a task and constraints.';
  }

  return (
    <div className="max-w-[640px] mx-auto px-4 mt-4">
      <div
        className="flex items-center justify-between gap-3"
        style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: '16px',
          padding: '10px 12px 10px 20px',
        }}
      >
        <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.35)', flex: 1, minWidth: 0 }} dangerouslySetInnerHTML={{ __html: html }} />
        <button
          onClick={onSubmit}
          className="shrink-0 transition-all"
          style={{
            background: '#6366f1',
            color: 'white',
            borderRadius: '12px',
            padding: '10px 24px',
            fontWeight: 500,
            fontSize: '13px',
            border: 'none',
            boxShadow: '0 2px 12px rgba(99,102,241,0.25)',
            cursor: 'pointer',
          }}
        >
          Evaluate {toolCount} →
        </button>
      </div>
    </div>
  );
}
