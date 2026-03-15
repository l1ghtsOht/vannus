import { motion } from 'framer-motion';

const CONSTRAINTS = [
  { id: 'free_tier', label: 'Free tier' },
  { id: 'budget_50', label: 'Under $50' },
  { id: 'budget_100', label: 'Under $100' },
  { id: 'hipaa', label: 'HIPAA (healthcare)' },
  { id: 'soc2', label: 'SOC2 (security)' },
  { id: 'gdpr', label: 'GDPR (EU privacy)' },
  { id: 'beginner', label: 'Beginner' },
  { id: 'open_source', label: 'Open source' },
  { id: 'api_access', label: 'API access (developers)' },
];

export default function ConstraintPills({ active, onToggle }) {
  return (
    <div className="max-w-[640px] mx-auto px-4 mt-5">
      <div className="flex items-center gap-2.5 mb-2">
        <span className="text-[11px] text-white/20 uppercase tracking-wide whitespace-nowrap">Add constraints</span>
        <div className="flex-1 h-px bg-white/[0.06]" />
      </div>
      <div className="flex flex-wrap gap-1.5">
        {CONSTRAINTS.map(c => {
          const isActive = active.has(c.id);
          return (
            <motion.button
              key={c.id}
              layout
              whileTap={{ scale: 0.95 }}
              onClick={() => onToggle(c.id)}
              className="text-[11px] py-1 px-3 rounded-full cursor-pointer transition-all"
              style={{
                background: isActive ? '#6366f1' : 'transparent',
                color: isActive ? 'white' : 'rgba(255,255,255,0.5)',
                border: `1px solid ${isActive ? '#6366f1' : 'rgba(255,255,255,0.1)'}`,
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
