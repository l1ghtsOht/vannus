import { useRoomState } from '../../context/RoomContext';
import ContextField from './ContextField';

const FIELD_ORDER = [
  'task_type', 'industry', 'budget', 'existing_tools', 'team_size',
  'skill_level', 'compliance', 'constraints', 'timeline',
];

const FIELD_LABELS = {
  task_type: 'What you need',
  industry: 'Your industry',
  budget: 'Budget',
  existing_tools: 'Current tools',
  team_size: 'Team size',
  skill_level: 'Technical level',
  compliance: 'Compliance needs',
  constraints: 'Constraints',
  timeline: 'Timeline',
};

/* Check if a field value is empty/null/internal-reasoning */
function isFieldEmpty(extraction) {
  if (!extraction) return true;
  const v = extraction.value;
  if (v == null) return true;
  if (typeof v === 'string') {
    const trimmed = v.trim();
    if (!trimmed || trimmed === 'null' || trimmed === 'undefined') return true;
    // Internal reasoning bleed-through
    if (trimmed.length > 100) return true;
    if (/^Step\s*\d/i.test(trimmed)) return true;
    if (/sub-quer/i.test(trimmed)) return true;
    if (/Search for tools/i.test(trimmed)) return true;
  }
  return false;
}

export default function ContextPanel() {
  const { contextVector } = useRoomState();

  if (!contextVector) {
    return (
      <div className="space-y-3 mb-4">
        <h3 className="text-xs font-medium text-white/30 uppercase tracking-wider mb-2">Your Business Profile</h3>
        <p className="text-xs text-white/20 italic">Awaiting query…</p>
      </div>
    );
  }

  const fields = FIELD_ORDER
    .map(key => {
      const extraction = contextVector[key];
      if (isFieldEmpty(extraction)) return null;
      return { key, label: FIELD_LABELS[key] || key, ...extraction };
    })
    .filter(Boolean);

  const t1 = fields.filter(f => f.confidence >= 0.9);
  const t2 = fields.filter(f => f.confidence >= 0.6 && f.confidence < 0.9);
  const t3 = fields.filter(f => f.confidence < 0.6);

  return (
    <div className="space-y-3 mb-4">
      <h3 className="text-xs font-medium text-white/30 uppercase tracking-wider mb-2">Your Business Profile</h3>

      {t1.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] uppercase tracking-wider text-emerald-400/60 font-medium">Confirmed</span>
          {t1.map(f => <ContextField key={f.key} field={f} />)}
        </div>
      )}

      {t2.length > 0 && (
        <div className="space-y-1 mt-2">
          <span className="text-[10px] uppercase tracking-wider text-amber-400/60 font-medium">Likely</span>
          {t2.map(f => <ContextField key={f.key} field={f} />)}
        </div>
      )}

      {t3.length > 0 && (
        <div className="space-y-1 mt-2">
          <span className="text-[10px] uppercase tracking-wider text-red-400/60 font-medium">Needs Clarification</span>
          {t3.map(f => <ContextField key={f.key} field={f} />)}
        </div>
      )}

      {fields.length === 0 && (
        <p className="text-xs text-white/20 italic">No profile data extracted yet.</p>
      )}
    </div>
  );
}
