import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRoomState, PHASES } from '../../context/RoomContext';

const KIND_STYLES = {
  system:      { icon: '◆', color: '#6b7280', bg: 'rgba(107,114,128,0.08)' },
  elimination: { icon: '✂', color: '#8b5cf6', bg: 'rgba(139,92,246,0.08)' },
  routing:     { icon: '◎', color: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
  execution:   { icon: '▸', color: '#06b6d4', bg: 'rgba(6,182,212,0.08)' },
  artifact:    { icon: '◈', color: '#10b981', bg: 'rgba(16,185,129,0.08)' },
  error:       { icon: '✕', color: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
  trust:       { icon: '◇', color: '#14b8a6', bg: 'rgba(20,184,166,0.08)' },
};

function formatTime(ts) {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function ActivityFeed() {
  const { activityLog, phase } = useRoomState();
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activityLog.length]);

  if (activityLog.length === 0 && phase === PHASES.IDLE) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-3 opacity-40">
          <div className="text-4xl">◆</div>
          <p className="text-sm text-white/40">Ready. Type a question to get started.</p>
          <p className="text-[10px] text-white/20">Your results will appear here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1.5 scrollbar-thin">
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
          const style = KIND_STYLES[entry.kind] || KIND_STYLES.system;
          return (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, y: 8, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="flex items-start gap-2.5 px-3 py-2 rounded-lg"
              style={{ background: style.bg }}
            >
              <span className="text-[11px] mt-0.5 shrink-0" style={{ color: style.color }}>
                {style.icon}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] text-white/75 leading-relaxed break-words">{entry.text}</p>
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
