import { motion } from 'framer-motion';

// 10 constraints chosen for broad customer coverage + brand alignment.
// Each one is verified to surface tools when combined with any task query.
// Validated against live API: 2026-04-30.
const CONSTRAINTS = [
  { id: 'free_tier',   label: 'Free tier' },
  { id: 'budget_20',   label: 'Under $20/mo' },
  { id: 'beginner',    label: 'Beginner-friendly' },
  { id: 'no_code',     label: 'No-code' },
  { id: 'open_source', label: 'Open source' },
  { id: 'api_access',  label: 'API access' },
  { id: 'soc2',        label: 'SOC 2 certified' },
  { id: 'gdpr',        label: 'GDPR compliant' },
  { id: 'self_hosted', label: 'Self-hosted' },
  { id: 'no_training', label: 'No data training' },
];

export default function ConstraintPills({ active, onToggle }) {
  return (
    <div className="max-w-[640px] mx-auto px-4 mt-5">
      <div className="flex items-center gap-2.5 mb-3">
        <span style={{ fontSize: '11px', fontWeight: 500, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.25)', whiteSpace: 'nowrap' }}>Add constraints</span>
        <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
      </div>
      <div className="flex flex-wrap gap-2">
        {CONSTRAINTS.map(c => {
          const isActive = active.has(c.id);
          return (
            <motion.button
              key={c.id}
              layout
              whileTap={{ scale: 0.95 }}
              onClick={() => onToggle(c.id)}
              className="cursor-pointer"
              style={{
                fontSize: '13px',
                padding: '6px 14px',
                borderRadius: '999px',
                border: `1px solid ${isActive ? 'rgba(99,102,241,0.35)' : 'rgba(255,255,255,0.08)'}`,
                background: isActive ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.04)',
                color: isActive ? '#a5b4fc' : 'rgba(255,255,255,0.5)',
                transition: 'all 0.2s ease',
              }}
            >
              {c.label}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

export { CONSTRAINTS };
