import { motion } from 'framer-motion';

const MODEL_COLORS = {
  claude: '#8b5cf6',
  gemini: '#06b6d4',
  grok: '#f59e0b',
  'gpt-4o': '#10b981',
  'gpt-4': '#10b981',
  local: '#6b7280',
};

function getModelColor(name) {
  const lower = (name || '').toLowerCase();
  for (const [key, color] of Object.entries(MODEL_COLORS)) {
    if (lower.includes(key)) return color;
  }
  return '#6366f1';
}

export default function SurvivorCard({ survivor, index }) {
  const name = survivor.name || 'Unknown';
  const score = survivor.final_score ?? survivor.fit_score ?? null;
  const reasons = survivor.survival_reasons || survivor.reasons || [];
  const penalties = survivor.penalties_applied || survivor.caveats || [];
  const description = survivor.description || '';
  const color = getModelColor(name);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      transition={{
        delay: index * 0.12,
        type: 'spring',
        stiffness: 400,
        damping: 30,
      }}
      className="glass flex items-stretch overflow-hidden"
    >
      {/* Color Stripe */}
      <div className="w-1 shrink-0" style={{ backgroundColor: color }} />

      <div className="flex-1 p-3 pl-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-white/85">{name}</span>
          {score != null && (
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-white/5 text-white/50">
              {Math.round(score <= 1 ? score * 100 : score)}%
            </span>
          )}
        </div>

        {description && (
          <p className="text-xs text-white/35 mt-0.5 mb-1 line-clamp-2 leading-relaxed">
            {description.slice(0, 140)}{description.length > 140 ? '…' : ''}
          </p>
        )}

        {reasons.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {reasons.slice(0, 3).map((reason, i) => (
              <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400/70">
                {reason}
              </span>
            ))}
          </div>
        )}

        {penalties.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {penalties.slice(0, 2).map((pen, i) => (
              <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400/60">
                {typeof pen === 'string' ? pen : pen.reason || 'penalty'}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
