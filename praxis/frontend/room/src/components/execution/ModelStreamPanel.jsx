import { motion } from 'framer-motion';
import StreamingText from './StreamingText';

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

export default function ModelStreamPanel({ modelId, content, isActive, index }) {
  const color = getModelColor(modelId);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, type: 'spring', stiffness: 300, damping: 28 }}
      className="glass overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-white/[0.04]">
        <div
          className="w-2 h-2 rounded-full shrink-0"
          style={{ backgroundColor: color }}
        />
        <span className="text-xs font-medium text-white/60">{modelId}</span>
        <div className="flex-1" />
        {isActive ? (
          <motion.span
            className="text-[10px] text-white/30"
            animate={{ opacity: [0.3, 0.8, 0.3] }}
            transition={{ duration: 1, repeat: Infinity }}
          >
            streaming…
          </motion.span>
        ) : (
          <span className="text-[10px] text-emerald-400/50">complete</span>
        )}
      </div>

      {/* Content */}
      <div className="px-4 py-3 max-h-80 overflow-y-auto">
        <StreamingText text={content || ''} isStreaming={isActive} />
      </div>

      {/* Color Accent Bar */}
      <div className="h-[2px]" style={{ backgroundColor: `${color}30` }}>
        {isActive && (
          <motion.div
            className="h-full"
            style={{ backgroundColor: color }}
            animate={{ width: ['0%', '100%'] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
        )}
      </div>
    </motion.div>
  );
}
