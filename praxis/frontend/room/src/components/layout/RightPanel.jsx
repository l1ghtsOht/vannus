import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRoomState, useRoomDispatch } from '../../context/RoomContext';

function StackItem({ name, survivor, onUnpin }) {
  const score = survivor?.final_score ?? survivor?.fit_score ?? null;
  const categories = survivor?.categories || [];
  const cat = categories[0] || '';

  return (
    <motion.div
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-colors group"
    >
      <span className="text-indigo-400/80 text-xs shrink-0">{'\u2713'}</span>
      <span className="text-sm text-white/80 font-medium flex-1 min-w-0 truncate">{name}</span>
      {cat && <span className="text-[10px] text-white/30 shrink-0 truncate max-w-[70px]">{cat}</span>}
      {score != null && (
        <span className="text-[11px] font-mono text-indigo-400/70 shrink-0">
          {Math.round(score <= 1 ? score * 100 : score)}%
        </span>
      )}
      <button
        onClick={() => onUnpin(name)}
        className="text-white/20 hover:text-red-400/70 opacity-0 group-hover:opacity-100 transition-all shrink-0"
        title="Remove from stack"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>
    </motion.div>
  );
}

export default function RightPanel({ children }) {
  const { rightPanelOpen, pinnedTools, differentialResult } = useRoomState();
  const dispatch = useRoomDispatch();
  const [copied, setCopied] = useState(false);

  const survivors = differentialResult?.tools_recommended || differentialResult?.survivors || [];
  const survivorMap = {};
  survivors.forEach(s => { survivorMap[s.name || ''] = s; });

  const handleUnpin = (name) => dispatch({ type: 'UNPIN_TOOL', payload: name });

  const handleCopy = () => {
    const text = pinnedTools.join('\n');
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <>
      <AnimatePresence mode="wait">
        {rightPanelOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 400, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="relative z-10 flex flex-col h-full overflow-hidden border-l border-white/[0.08]"
            style={{ background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(20px)' }}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
              <span className="text-xs font-medium text-white/40 uppercase tracking-wider">
                Your Stack{pinnedTools.length > 0 ? ` (${pinnedTools.length})` : ''}
              </span>
              <button
                onClick={() => dispatch({ type: 'TOGGLE_RIGHT_PANEL' })}
                className="text-white/25 hover:text-white/60 transition-colors"
              >
                <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3">
              {/* Pinned tools stack */}
              {pinnedTools.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-center">
                  <p className="text-xs text-white/25 leading-relaxed">
                    No instruments selected yet.
                  </p>
                  <p className="text-xs text-white/15 mt-2 leading-relaxed">
                    Pin tools from the results<br />to start building your stack.
                  </p>
                </div>
              ) : (
                <div className="space-y-0.5 mb-4">
                  <AnimatePresence>
                    {pinnedTools.map(name => (
                      <StackItem
                        key={name}
                        name={name}
                        survivor={survivorMap[name]}
                        onUnpin={handleUnpin}
                      />
                    ))}
                  </AnimatePresence>

                  {/* Copy stack button */}
                  <div className="pt-3 mt-2 border-t border-white/[0.06]">
                    <button
                      onClick={handleCopy}
                      className="w-full text-[11px] text-white/40 hover:text-white/70 py-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] hover:border-white/[0.1] transition-all"
                    >
                      {copied ? 'Copied!' : 'Copy stack'}
                    </button>
                  </div>
                </div>
              )}

              {/* Cost breakdown underneath */}
              {children}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
      {!rightPanelOpen && (
        <button
          onClick={() => dispatch({ type: 'TOGGLE_RIGHT_PANEL' })}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-20 p-1.5 rounded-l-lg bg-white/5 hover:bg-white/10 border border-r-0 border-white/[0.08] text-white/30 hover:text-white/60 transition-all"
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </button>
      )}
    </>
  );
}
