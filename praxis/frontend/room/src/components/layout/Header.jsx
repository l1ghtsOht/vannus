import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useRoomState, useRoomDispatch } from '../../context/RoomContext';

const LS_KEY = 'praxis_room_name';

export default function Header() {
  const { room, cost, phase, pinnedTools } = useRoomState();
  const dispatch = useRoomDispatch();
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState('');
  const inputRef = useRef(null);

  // Load saved room name from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(LS_KEY);
    if (saved && room && room.name !== saved) {
      dispatch({ type: 'UPDATE_ROOM_NAME', payload: saved });
    }
  }, [room?.id]);

  const displayName = room?.name || localStorage.getItem(LS_KEY) || 'My Room';

  const startEditing = () => {
    setEditValue(displayName);
    setEditing(true);
  };

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const commitName = () => {
    const newName = editValue.trim();
    setEditing(false);
    if (newName && newName !== displayName) {
      dispatch({ type: 'UPDATE_ROOM_NAME', payload: newName });
      localStorage.setItem(LS_KEY, newName);
      if (room?.id) {
        fetch(`/room/${room.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: newName }),
        }).catch(() => {});
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); commitName(); }
    if (e.key === 'Escape') { setEditing(false); }
  };

  return (
    <header className="relative z-30 flex items-center justify-between px-5 py-3 border-b border-white/[0.08]"
            style={{ background: 'rgba(10,10,15,0.7)', backdropFilter: 'blur(30px)' }}>
      {/* Left: Back link + Logo + Room Name */}
      <div className="flex items-center gap-3">
        <a
          href="/"
          className="text-white/40 hover:text-white/70 text-sm transition-colors"
          title="Back to Praxis"
        >{'\u2190'} Praxis</a>
        <span className="text-white/15">|</span>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#6366f1] flex items-center justify-center">
            <span className="text-white text-xs font-bold">P</span>
          </div>
          <span className="text-sm font-semibold text-white/80 tracking-tight">Room</span>
        </div>
        <span className="text-white/20">|</span>
        {editing ? (
          <input
            ref={inputRef}
            type="text"
            value={editValue}
            onChange={e => setEditValue(e.target.value)}
            onBlur={commitName}
            onKeyDown={handleKeyDown}
            className="text-sm font-medium text-white/70 bg-white/5 outline-none px-2 py-0.5 rounded border border-white/10 focus:border-indigo-500/40 min-w-[60px] max-w-[200px]"
          />
        ) : (
          <span
            onClick={startEditing}
            className="text-sm font-medium text-white/70 px-2 py-0.5 rounded hover:bg-white/5 cursor-text min-w-[60px] select-none"
            title="Click to rename"
          >
            {displayName}
          </span>
        )}
      </div>

      {/* Center: Phase Indicator */}
      <div className="flex items-center gap-2">
        <motion.div
          className="h-1.5 w-1.5 rounded-full"
          style={{ backgroundColor: phaseColor(phase) }}
          animate={{ scale: [1, 1.3, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        />
        <span className="text-xs text-white/40 uppercase tracking-widest font-medium">{phase}</span>
      </div>

      {/* Right: Cost + Stack count + Actions */}
      <div className="flex items-center gap-4">
        {cost.total > 0 && (
          <div className="text-xs text-white/50 font-mono">
            ${cost.total.toFixed(4)}
          </div>
        )}
        {pinnedTools.length > 0 && (
          <div className="text-[11px] text-indigo-400/70 font-medium">
            {pinnedTools.length} in stack
          </div>
        )}
        <button
          onClick={() => dispatch({ type: 'NEW_CONVERSATION' })}
          className="text-[11px] text-white/40 hover:text-white/80 px-2.5 py-1 rounded-md bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/[0.15] transition-all"
          title="Start a new conversation"
        >
          New conversation
        </button>
        <button
          className="text-white/30 hover:text-white/70 transition-colors text-sm"
          title="History"
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </header>
  );
}

function phaseColor(phase) {
  const map = {
    idle: '#6366f1',
    eliminating: '#8b5cf6',
    routing: '#f59e0b',
    executing: '#06b6d4',
    complete: '#10b981',
  };
  return map[phase] || '#6366f1';
}
