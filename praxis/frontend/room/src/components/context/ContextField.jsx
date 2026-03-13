import { motion } from 'framer-motion';

function tierColor(confidence) {
  if (confidence >= 0.9) return '#10b981';
  if (confidence >= 0.6) return '#f59e0b';
  return '#ef4444';
}

function formatKey(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function isInternalReasoning(val) {
  if (typeof val !== 'string') return false;
  if (val.length > 100) return true;
  if (/^Step\s*\d/i.test(val)) return true;
  if (/sub-quer/i.test(val)) return true;
  if (/Search for tools/i.test(val)) return true;
  return false;
}

export default function ContextField({ field }) {
  const { key, value, confidence, tier, source, label } = field;

  // Bug 3: skip null/undefined/empty values
  if (value == null || value === 'null' || value === 'undefined' || value === '') return null;
  // Bug 2: skip internal reasoning text bleeding through
  if (isInternalReasoning(value)) return null;

  const color = tierColor(confidence);

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-2 py-1.5 px-2 rounded-lg hover:bg-white/[0.03] transition-colors group"
    >
      {/* Confidence Dot */}
      <div className="mt-1 shrink-0">
        <div
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}40` }}
        />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-1">
          <span className="text-[11px] text-white/50 font-medium">{label || formatKey(key)}</span>
          <span className="text-[9px] text-white/20 font-mono">{(confidence * 100).toFixed(0)}%</span>
        </div>
        <p className="text-xs text-white/70 truncate">{typeof value === 'string' ? value : JSON.stringify(value)}</p>
        {source && (
          <span className="text-[9px] text-white/15 italic opacity-0 group-hover:opacity-100 transition-opacity">
            via {source}
          </span>
        )}
      </div>
    </motion.div>
  );
}
