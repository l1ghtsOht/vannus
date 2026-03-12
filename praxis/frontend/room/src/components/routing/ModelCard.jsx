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

export default function ModelCard({ model, index }) {
  const name = model.name || 'Unknown';
  const final_score = model.final_score ?? model.fit_score ?? null;
  const survival_reasons = model.survival_reasons || model.reasons || [];
  const cost_estimate_usd = model.cost_estimate_usd ?? null;
  const description = model.description || '';
  const color = getModelColor(name);

  return (
    <motion.div
      initial={{ opacity: 0, x: -16, scale: 0.97 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      transition={{
        delay: index * 0.08,
        type: 'spring',
        stiffness: 400,
        damping: 28,
      }}
      className="glass flex items-stretch overflow-hidden group"
    >
      {/* Color Stripe */}
      <div className="w-1.5 shrink-0 rounded-l-2xl" style={{ backgroundColor: color }} />

      <div className="flex-1 p-3 pl-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white/85">{name}</span>
            {final_score != null && (
              <span
                className="text-[10px] font-mono px-1.5 py-0.5 rounded-full"
                style={{ backgroundColor: `${color}15`, color: `${color}cc` }}
              >
                {Math.round(final_score <= 1 ? final_score * 100 : final_score)}%
              </span>
            )}
          </div>
          {cost_estimate_usd != null && (
            <span className="text-[10px] text-white/30 font-mono">~${cost_estimate_usd.toFixed(4)}</span>
          )}
        </div>

        {description && (
          <p className="text-xs text-white/35 mt-1 line-clamp-1">
            {description.slice(0, 100)}
          </p>
        )}
        {survival_reasons.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {survival_reasons.slice(0, 2).map((r, i) => (
              <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-white/30">{r}</span>
            ))}
          </div>
        )}
      </div>

      {/* Highlight pulse on appear */}
      <motion.div
        className="absolute inset-0 rounded-2xl pointer-events-none"
        initial={{ opacity: 0.15 }}
        animate={{ opacity: 0 }}
        transition={{ duration: 0.8, delay: index * 0.08 }}
        style={{ backgroundColor: color }}
      />
    </motion.div>
  );
}
