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

function trustColor(score) {
  if (score >= 0.8) return '#10b981';
  if (score >= 0.5) return '#f59e0b';
  return '#ef4444';
}

export default function TrustIndicator({ modelId, data }) {
  const color = getModelColor(modelId);
  const trust = data?.trust_score ?? data?.trust ?? 1;
  const tColor = trustColor(trust);

  return (
    <div className="flex items-center gap-2 py-1.5 px-2 rounded-lg hover:bg-white/[0.02] transition-colors">
      <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
      <span className="text-[11px] text-white/50 flex-1 truncate">{modelId}</span>
      <div className="flex items-center gap-1.5">
        <div className="w-12 h-1 rounded-full bg-white/[0.04] overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: tColor }}
            initial={{ width: 0 }}
            animate={{ width: `${trust * 100}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>
        <span className="text-[9px] font-mono text-white/30">{(trust * 100).toFixed(0)}</span>
      </div>
    </div>
  );
}
