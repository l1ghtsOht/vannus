const REASON_STYLES = {
  BUDGET_EXCEEDED:           { bg: 'bg-red-500/10',    text: 'text-red-400/80',    label: 'Budget' },
  COMPLIANCE_FAILURE:        { bg: 'bg-orange-500/10', text: 'text-orange-400/80', label: 'Compliance' },
  NEGATIVE_INTENT_MATCH:     { bg: 'bg-yellow-500/10', text: 'text-yellow-400/80', label: 'Intent' },
  STACK_CONFLICT:            { bg: 'bg-purple-500/10', text: 'text-purple-400/80', label: 'Stack' },
  DEPLOYMENT_CONFLICT:       { bg: 'bg-blue-500/10',   text: 'text-blue-400/80',   label: 'Deploy' },
  ARCHITECTURAL_REDUNDANCY:  { bg: 'bg-gray-500/10',   text: 'text-gray-400/80',   label: 'Redundant' },
};

export default function ReasonCodeBadge({ code }) {
  const style = REASON_STYLES[code] || { bg: 'bg-white/5', text: 'text-white/40', label: code || '?' };

  return (
    <span className={`text-[9px] font-medium px-1.5 py-0.5 rounded ${style.bg} ${style.text} uppercase tracking-wider shrink-0`}>
      {style.label}
    </span>
  );
}
