import { useState } from 'react';
import { motion } from 'framer-motion';
import { useRoomState, useRoomDispatch } from '../../context/RoomContext';
import useQuerySubmit from '../../hooks/useQuerySubmit';
import CommandBar from './CommandBar';

const CONSTRAINT_KEYS = [
  { key: 'budget', label: 'Budget', placeholder: '$300/mo' },
  { key: 'compliance', label: 'Compliance', placeholder: 'HIPAA' },
  { key: 'industry', label: 'Industry', placeholder: 'Healthcare' },
];

export default function TopBar() {
  const { query, phase, differentialResult, contextVector, cost, error } = useRoomState();
  const dispatch = useRoomDispatch();
  const { isRunning, constraints, setConstraint, removeConstraint } = useQuerySubmit();
  const [editingChip, setEditingChip] = useState(null);

  const survivors = differentialResult?.tools_recommended || differentialResult?.survivors || [];
  const totalConsidered = differentialResult?.tools_considered || 0;
  const isIdle = phase === 'idle';

  const contextChips = [];
  if (contextVector) {
    Object.entries(contextVector).forEach(([key, val]) => {
      if (val?.value) contextChips.push({ key, label: key.replace('_', ' '), value: val.value });
    });
  }
  Object.entries(constraints).forEach(([key, val]) => {
    if (val && !contextChips.find(c => c.key === key)) {
      contextChips.push({ key, label: key, value: val });
    }
  });

  return (
    <div
      className="relative z-30 flex items-center gap-3 px-4 py-2 border-b border-white/[0.06] flex-wrap"
      style={{ background: 'rgba(10,10,15,0.85)', backdropFilter: 'blur(30px)' }}
    >
      {/* Back link */}
      <a href="/" className="text-white/30 hover:text-white/60 text-sm shrink-0 transition-colors">{'\u2190'} Praxis</a>
      <span className="text-white/10 shrink-0">|</span>

      {/* Compact command bar input */}
      <div className="flex-1 min-w-[200px]">
        <CommandBar compact />
      </div>

      {/* Pipeline badge */}
      {!isIdle && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`shrink-0 px-3 py-1 rounded-full text-[11px] font-medium flex items-center gap-2 ${
            isRunning
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20'
              : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
          }`}
        >
          {isRunning && (
            <motion.div
              className="w-1.5 h-1.5 rounded-full bg-current"
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
          )}
          {isRunning ? 'Analyzing...' : `${survivors.length} survived / ${totalConsidered}`}
        </motion.div>
      )}

      {/* Context chips (compact) */}
      {contextChips.slice(0, 3).map(chip => (
        <div key={chip.key} className="relative shrink-0">
          <button
            onClick={() => setEditingChip(editingChip === chip.key ? null : chip.key)}
            className="px-2 py-0.5 rounded-full text-[10px] border border-indigo-500/30 text-indigo-300/70 bg-indigo-500/8 hover:bg-indigo-500/15 transition-all"
          >
            {chip.label}: {typeof chip.value === 'string' ? chip.value.slice(0, 15) : chip.value}
          </button>
          {editingChip === chip.key && (
            <div className="absolute top-full mt-1 left-0 z-50 flex items-center gap-2 px-3 py-2 rounded-lg"
                 style={{ background: 'rgba(15,15,20,0.95)', border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 8px 24px rgba(0,0,0,0.5)' }}>
              <input
                autoFocus
                type="text"
                defaultValue={constraints[chip.key] || ''}
                onBlur={e => { setConstraint(chip.key, e.target.value.trim()); setEditingChip(null); }}
                onKeyDown={e => { if (e.key === 'Enter') { setConstraint(chip.key, e.target.value.trim()); setEditingChip(null); } }}
                className="bg-transparent border-b border-white/20 focus:border-indigo-500/60 outline-none text-xs text-white/80 w-24 py-0.5"
              />
              {constraints[chip.key] && (
                <button onClick={() => { removeConstraint(chip.key); setEditingChip(null); }} className="text-red-400/60 text-xs">{'\u00d7'}</button>
              )}
            </div>
          )}
        </div>
      ))}

      {/* Cost / Dry run indicator */}
      {cost.total > 0 ? (
        <span className="text-[11px] text-white/30 font-mono shrink-0">${cost.total.toFixed(4)}</span>
      ) : phase !== 'idle' ? (
        <span className="text-[10px] text-white/20 shrink-0">Dry run</span>
      ) : null}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] text-red-400/70 truncate max-w-[120px]">{error}</span>
          <button onClick={() => dispatch({ type: 'SET_ERROR', payload: null })} className="text-red-400/40 hover:text-red-400/80 text-xs">{'\u00d7'}</button>
        </div>
      )}

      {/* New conversation */}
      <button
        onClick={() => dispatch({ type: 'NEW_CONVERSATION' })}
        className="text-[10px] text-white/30 hover:text-white/60 px-2 py-1 rounded-md bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] transition-all shrink-0"
      >
        New
      </button>
    </div>
  );
}
