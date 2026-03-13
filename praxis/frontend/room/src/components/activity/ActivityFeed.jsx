import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRoomState, PHASES } from '../../context/RoomContext';

const KIND_STYLES = {
  system:      { icon: '\u25C6', color: '#6b7280', bg: 'rgba(107,114,128,0.08)' },
  elimination: { icon: '\u2702', color: '#8b5cf6', bg: 'rgba(139,92,246,0.08)' },
  routing:     { icon: '\u25CE', color: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
  execution:   { icon: '\u25B8', color: '#06b6d4', bg: 'rgba(6,182,212,0.08)' },
  artifact:    { icon: '\u25C8', color: '#10b981', bg: 'rgba(16,185,129,0.08)' },
  error:       { icon: '\u2715', color: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
  trust:       { icon: '\u25C7', color: '#14b8a6', bg: 'rgba(20,184,166,0.08)' },
};

/* ── Change 5: Human-voice text replacements ── */
function humanize(text) {
  if (!text || typeof text !== 'string') return text;
  // Strip "Result saved:" entries entirely
  if (/^Result saved:/i.test(text)) return null;
  // Replace pipeline jargon
  let out = text;
  out = out.replace(/^Finding the best tools[\u2026.]*/i, 'Scanning 246 tools\u2026');
  out = out.replace(/^Getting answers[\u2026.]*/i, 'Composing your recommendation\u2026');
  out = out.replace(/^Reviewed (\d+) tools\.\s*(\d+) match your needs\.$/i, '$1 tools reviewed \u2192 $2 match');
  out = out.replace(/^Recommended:/i, 'Top matches:');
  return out;
}

function formatTime(ts) {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function ActivityFeed() {
  const { activityLog, phase, differentialResult } = useRoomState();
  const endRef = useRef(null);
  const [collapsed, setCollapsed] = useState(false);
  const collapseTimerRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activityLog.length]);

  // Change 3: collapse pipeline log 1.5s after DONE
  useEffect(() => {
    if (phase === PHASES.COMPLETE) {
      collapseTimerRef.current = setTimeout(() => setCollapsed(true), 1500);
    } else {
      setCollapsed(false);
      if (collapseTimerRef.current) clearTimeout(collapseTimerRef.current);
    }
    return () => { if (collapseTimerRef.current) clearTimeout(collapseTimerRef.current); };
  }, [phase]);

  if (activityLog.length === 0 && phase === PHASES.IDLE) {
    return null;
  }

  const survivors = differentialResult?.tools_recommended || differentialResult?.survivors || [];
  const totalEvaluated = differentialResult?.tools_considered || survivors.length;

  // When collapsed, show only summary line
  if (collapsed && phase === PHASES.COMPLETE && differentialResult) {
    return (
      <div className="px-3 py-3">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
          className="flex items-center gap-2.5 px-3 py-2 rounded-lg"
          style={{ background: 'rgba(16,185,129,0.08)' }}
        >
          <span className="text-emerald-400/80 text-xs">{'\u2713'}</span>
          <p className="text-[13px] text-white/60 leading-relaxed">
            Evaluated <span className="text-white/80 font-medium">{totalEvaluated}</span> tools {'\u2192'}{' '}
            <span className="text-emerald-400/80 font-medium">{survivors.length}</span> match your context
          </p>
        </motion.div>
        <div ref={endRef} />
      </div>
    );
  }

  return (
    <div className="overflow-y-auto px-2 py-3 space-y-1.5 scrollbar-thin">
      <AnimatePresence initial={false}>
        {activityLog.map((entry) => {
          if (entry.kind === 'divider') {
            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="flex items-center gap-3 px-3 py-2"
              >
                <div className="flex-1 h-px bg-white/[0.08]" />
                <span className="text-[10px] text-white/20 font-mono shrink-0">{entry.text}</span>
                <div className="flex-1 h-px bg-white/[0.08]" />
              </motion.div>
            );
          }
          // Apply human-voice text transform
          const displayText = humanize(entry.text);
          if (displayText === null) return null; // filtered out (e.g. "Result saved:")

          const style = KIND_STYLES[entry.kind] || KIND_STYLES.system;
          return (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, y: 8, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, transition: { duration: 0.3 } }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="flex items-start gap-2.5 px-3 py-2 rounded-lg"
              style={{ background: style.bg }}
            >
              <span className="text-[11px] mt-0.5 shrink-0" style={{ color: style.color }}>
                {style.icon}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] text-white/75 leading-relaxed break-words">{displayText}</p>
                {entry.detail && (
                  <p className="text-[11px] text-white/30 mt-0.5 leading-relaxed">{entry.detail}</p>
                )}
              </div>
              <span className="text-[9px] text-white/15 shrink-0 mt-0.5 font-mono tabular-nums">
                {formatTime(entry.timestamp)}
              </span>
            </motion.div>
          );
        })}
      </AnimatePresence>
      <div ref={endRef} />
    </div>
  );
}
