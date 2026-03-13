import { motion } from 'framer-motion';
import { useRoomState, useRoomDispatch } from '../../context/RoomContext';

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
  const { pinnedTools, passedTools } = useRoomState();
  const dispatch = useRoomDispatch();

  const name = survivor.name || 'Unknown';
  const score = survivor.final_score ?? survivor.fit_score ?? null;
  const reasons = survivor.survival_reasons || survivor.reasons || [];
  const penalties = survivor.penalties_applied || survivor.caveats || [];
  const description = survivor.description || '';
  const categories = survivor.categories || [];
  const color = getModelColor(name);

  const isPinned = pinnedTools.includes(name);
  const isPassed = passedTools.includes(name);

  const handlePin = (e) => {
    e.stopPropagation();
    if (isPinned) dispatch({ type: 'UNPIN_TOOL', payload: name });
    else dispatch({ type: 'PIN_TOOL', payload: name });
  };

  const handlePass = (e) => {
    e.stopPropagation();
    dispatch({ type: 'PASS_TOOL', payload: name });
  };

  const handleUnpass = (e) => {
    e.stopPropagation();
    dispatch({ type: 'UNPASS_TOOL', payload: name });
  };

  if (isPassed) {
    return (
      <motion.div
        initial={{ opacity: 0, x: -20, scale: 0.95 }}
        animate={{ opacity: 0.4, x: 0, scale: 1 }}
        transition={{ delay: index * 0.12, type: 'spring', stiffness: 400, damping: 30 }}
        className="glass flex items-stretch overflow-hidden"
      >
        <div className="w-1 shrink-0 bg-white/10" />
        <div className="flex-1 p-3 pl-4 flex items-center justify-between">
          <span className="text-sm text-white/40 line-through">{name}</span>
          <button
            onClick={handleUnpass}
            className="text-[10px] text-white/30 hover:text-white/60 px-2 py-0.5 rounded hover:bg-white/5 transition-all"
          >
            Undo
          </button>
        </div>
      </motion.div>
    );
  }

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
      className={`glass flex items-stretch overflow-hidden group relative ${isPinned ? 'bg-indigo-500/5' : ''}`}
    >
      {/* Color Stripe — indigo when pinned */}
      <div
        className="w-1 shrink-0 transition-colors duration-300"
        style={{ backgroundColor: isPinned ? '#6366f1' : color }}
      />

      <div className="flex-1 p-3 pl-4">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white/85">{name}</span>
            {isPinned && (
              <span className="text-[9px] font-medium text-indigo-400/80 px-1.5 py-0.5 rounded-full bg-indigo-500/15">
                In stack
              </span>
            )}
          </div>
          {score != null && (
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-white/5 text-white/50">
              {Math.round(score <= 1 ? score * 100 : score)}%
            </span>
          )}
        </div>

        {description && (
          <p className="text-xs text-white/35 mt-0.5 mb-1 line-clamp-2 leading-relaxed">
            {description.slice(0, 140)}{description.length > 140 ? '\u2026' : ''}
          </p>
        )}

        {reasons.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1.5">
            {reasons.slice(0, 4).map((reason, i) => (
              <span key={i} className="inline-block max-w-[160px] truncate text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400/80">
                {reason}
              </span>
            ))}
          </div>
        )}

        {penalties.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {penalties.slice(0, 3).map((pen, i) => (
              <span key={i} className="inline-block max-w-[160px] truncate text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400/70">
                {typeof pen === 'string' ? pen : pen.reason || 'penalty'}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Director action buttons — appear on hover */}
      <div className="absolute top-2 right-2 flex gap-1.5 items-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <button
          onClick={handlePin}
          className={`p-1.5 rounded-md border transition-all ${
            isPinned
              ? 'bg-indigo-500/20 border-indigo-500/30 text-indigo-400'
              : 'bg-white/5 border-white/10 text-white/40 hover:text-indigo-400 hover:border-indigo-500/30 hover:bg-indigo-500/10'
          }`}
          title={isPinned ? 'Remove from stack' : 'Add to stack'}
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
            {isPinned
              ? <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              : <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            }
          </svg>
        </button>
        <button
          onClick={handlePass}
          className="p-1.5 rounded-md bg-white/5 border border-white/10 text-white/40 hover:text-red-400 hover:border-red-500/30 hover:bg-red-500/10 transition-all"
          title="Pass on this tool"
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </motion.div>
  );
}
