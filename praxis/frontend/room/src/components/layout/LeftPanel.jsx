import { motion, AnimatePresence } from 'framer-motion';
import { useRoomState, useRoomDispatch } from '../../context/RoomContext';

export default function LeftPanel({ children }) {
  const { leftPanelOpen } = useRoomState();
  const dispatch = useRoomDispatch();

  return (
    <>
      <AnimatePresence mode="wait">
        {leftPanelOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="relative z-10 flex flex-col h-full overflow-hidden border-r border-white/[0.08]"
            style={{ background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(20px)' }}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
              <span className="text-xs font-medium text-white/40 uppercase tracking-wider">Your Profile</span>
              <button
                onClick={() => dispatch({ type: 'TOGGLE_LEFT_PANEL' })}
                className="text-white/25 hover:text-white/60 transition-colors"
              >
                <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                  <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3">
              {children}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
      {!leftPanelOpen && (
        <button
          onClick={() => dispatch({ type: 'TOGGLE_LEFT_PANEL' })}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20 p-1.5 rounded-r-lg bg-white/5 hover:bg-white/10 border border-l-0 border-white/[0.08] text-white/30 hover:text-white/60 transition-all"
        >
          <svg viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        </button>
      )}
    </>
  );
}
