import { motion, AnimatePresence } from 'framer-motion';
import ToolCard from './ToolCard';

export default function InlineResults({ results, onReset }) {
  if (!results) return null;
  const { tools, totalTools, eliminatedCount } = results;
  const showCount = Math.min(8, tools.length);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-[640px] mx-auto px-4 mt-6"
    >
      {/* Summary */}
      <div className="text-center text-[13px] text-white/40 pb-4 mb-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <strong className="text-white/70">{totalTools}</strong> evaluated ·{' '}
        <strong className="text-white/70">{eliminatedCount}</strong> eliminated ·{' '}
        <strong className="text-white/70">{tools.length}</strong> survived
      </div>

      {/* Cards */}
      <AnimatePresence>
        {tools.slice(0, showCount).map((tool, i) => (
          <ToolCard key={tool.name || i} tool={tool} index={i} isTopPick={i === 0} />
        ))}
      </AnimatePresence>

      {tools.length > 8 && (
        <div className="text-center text-[12px] text-white/30 py-3 cursor-pointer hover:text-[#6366f1]">
          Show all {tools.length} results
        </div>
      )}

      {/* Reset */}
      <div className="text-center py-4">
        <button onClick={onReset} className="text-[13px] text-white/30 hover:text-[#6366f1] transition-colors bg-transparent border-none cursor-pointer">
          ← Search again
        </button>
      </div>
    </motion.div>
  );
}
