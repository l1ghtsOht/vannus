import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { useRoomState, useRoomDispatch, PHASES } from '../../context/RoomContext';
import SurvivorCard from './SurvivorCard';
import EliminationAccordion from './EliminationAccordion';

/* ── Collapsed summary for archived queries ── */
function ArchivedQuery({ entry, onExpand }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 0.3 }}
      className="mb-4 cursor-pointer"
      onClick={onExpand}
    >
      <div className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-white/[0.03] transition-colors">
        <span className="text-emerald-400/60 text-xs">{'\u2713'}</span>
        <span className="text-xs text-white/40">
          Evaluated <span className="font-medium">{entry.toolsConsidered}</span> tools {'\u2192'}{' '}
          <span className="text-emerald-400/60 font-medium">{entry.matchCount}</span> match
        </span>
        <span className="text-[9px] text-white/15 ml-auto">{'\u25B8'} Show</span>
      </div>
    </motion.div>
  );
}

export default function EliminationDisplay() {
  const { differentialResult, phase, queryHistory } = useRoomState();
  const dispatch = useRoomDispatch();
  const [displayCount, setDisplayCount] = useState(0);
  const [showCards, setShowCards] = useState(false);
  const [expandedCardId, setExpandedCardId] = useState(null);

  const toggleCard = (id) => setExpandedCardId(prev => prev === id ? null : id);

  const survivors = differentialResult?.tools_recommended || differentialResult?.survivors || [];
  const eliminated = differentialResult?.eliminated || [];
  const totalEvaluated = differentialResult?.tools_considered || survivors.length;
  const eliminatedCount = totalEvaluated - survivors.length;
  const displayNarrative = differentialResult?.funnel_narrative || differentialResult?.narrative || '';

  // Count-up animation — always called, guards internally
  useEffect(() => {
    if (!differentialResult || totalEvaluated <= 0) {
      setDisplayCount(0);
      setShowCards(false);
      setExpandedCardId(null);
      return;
    }
    setShowCards(false);
    setExpandedCardId(null);
    let current = 0;
    const step = Math.max(1, Math.ceil(totalEvaluated / 30));
    const timer = setInterval(() => {
      current = Math.min(current + step, totalEvaluated);
      setDisplayCount(current);
      if (current >= totalEvaluated) {
        clearInterval(timer);
        setTimeout(() => setShowCards(true), 200);
      }
    }, 25);
    return () => clearInterval(timer);
  }, [differentialResult, totalEvaluated]);

  // ── Early returns AFTER all hooks ──
  if (!differentialResult && phase !== PHASES.ELIMINATING) return null;

  // Show scanning animation during elimination
  if (phase === PHASES.ELIMINATING && !differentialResult) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3 mb-3">
          <motion.div
            className="w-2 h-2 rounded-full bg-[#8b5cf6]"
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 0.8, repeat: Infinity }}
          />
          <motion.span
            className="text-sm text-white/50"
            animate={{ opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            Finding the best tools for you…
          </motion.span>
        </div>
        <div className="space-y-1">
          {[0, 1, 2, 3].map(i => (
            <motion.div
              key={i}
              className="h-1 rounded-full bg-white/[0.04]"
              initial={{ scaleX: 0 }}
              animate={{ scaleX: [0, 1, 0.3] }}
              transition={{ duration: 1.2, delay: i * 0.15, repeat: Infinity }}
              style={{ transformOrigin: 'left' }}
            />
          ))}
        </div>
      </motion.div>
    );
  }

  if (!differentialResult) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mb-6"
    >
      {/* Archived previous queries */}
      {queryHistory.length > 0 && queryHistory.map((entry, i) => (
        <ArchivedQuery key={i} entry={entry} onExpand={() => {}} />
      ))}

      {/* Scanner line */}
      <motion.div
        initial={{ scaleX: 0, opacity: 1 }}
        animate={{ scaleX: 1, opacity: 0 }}
        transition={{ duration: 1.2, ease: 'linear' }}
        className="h-px mb-4"
        style={{
          background: 'linear-gradient(90deg, transparent, #6366f1, transparent)',
          transformOrigin: 'left',
        }}
      />

      {/* Narrative — strip backend error bleed-through */}
      {displayNarrative && showCards && (() => {
        const cleaned = displayNarrative
          .split(/(?<=[.!?])\s+/)
          .filter(s => !/I wasn't able to fully address/i.test(s))
          .filter(s => !/Sub-query not well covered/i.test(s))
          .filter(s => !/I won't be able to fully/i.test(s))
          .join(' ')
          .trim();
        if (!cleaned) return null;
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs text-white/30 mb-4 leading-relaxed prose prose-invert prose-xs max-w-none"
          >
            <ReactMarkdown>{cleaned}</ReactMarkdown>
          </motion.div>
        );
      })()}

      {/* Survivors */}
      <AnimatePresence>
        {showCards && survivors.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-2 mb-4"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
              <span className="text-[11px] font-medium text-emerald-400/70 uppercase tracking-wider">
                {survivors.length} Matched
              </span>
            </div>
            {survivors.map((survivor, idx) => (
              <SurvivorCard
                key={survivor.name || idx}
                survivor={survivor}
                index={idx}
                isExpanded={expandedCardId === (survivor.name || idx)}
                onToggle={toggleCard}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Eliminated Accordion */}
      {showCards && eliminated.length > 0 && (
        <EliminationAccordion eliminated={eliminated} expandedCardId={expandedCardId} onToggleCard={toggleCard} />
      )}
    </motion.div>
  );
}
