const TASK_LABELS = {
  writing: 'writing tools', coding: 'coding tools', analytics: 'analytics tools',
  automation: 'automation tools', support: 'customer support tools', appbuilding: 'app-building tools',
};

const CONSTRAINT_LABELS = {
  free_tier: 'free', budget_50: 'under $50/mo', budget_100: 'under $100/mo',
  hipaa: 'HIPAA-compliant', soc2: 'SOC2-certified', gdpr: 'GDPR-compliant',
  beginner: 'beginner-friendly', open_source: 'open source', api_access: 'API access',
};

export default function LiveSummary({ task, constraints, query, onSubmit }) {
  const taskLabel = task ? TASK_LABELS[task] : null;
  const constraintList = [...constraints].map(c => CONSTRAINT_LABELS[c] || c);
  const constraintStr = constraintList.length
    ? constraintList.map(c => `<span style="color:#6366f1">${c}</span>`).join(', ')
    : '';

  let html;
  if (query && query.length >= 3) {
    html = `Search: <strong>"${query.slice(0, 60)}"</strong>${constraintStr ? ' with ' + constraintStr : ''} — then eliminate the rest.`;
  } else if (taskLabel && constraintStr) {
    html = `Find <strong>${taskLabel}</strong> that are ${constraintStr} — then eliminate the rest.`;
  } else if (taskLabel) {
    html = `Find <strong>${taskLabel}</strong> — then eliminate the rest.`;
  } else if (constraintStr) {
    html = `Find tools that are ${constraintStr} — then eliminate the rest.`;
  } else {
    html = 'Describe what you need above, or pick a task and constraints.';
  }

  return (
    <div className="max-w-[640px] mx-auto px-4 mt-4">
      <div
        className="flex items-center justify-between gap-3 rounded-xl"
        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', padding: '10px 14px' }}
      >
        <span className="text-[13px] text-white/40 flex-1 min-w-0" dangerouslySetInnerHTML={{ __html: html }} />
        <button
          onClick={onSubmit}
          className="shrink-0 text-[12px] font-semibold py-1.5 px-4 rounded-full transition-all hover:opacity-90"
          style={{ background: '#6366f1', color: 'white' }}
        >
          Evaluate 253 →
        </button>
      </div>
    </div>
  );
}
