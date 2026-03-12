import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReasonCodeBadge from './ReasonCodeBadge';

export default function EliminationAccordion({ eliminated }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl overflow-hidden border border-white/[0.06]">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs text-white/40 hover:text-white/60 hover:bg-white/[0.02] transition-all"
      >
        <span>{eliminated.length} eliminated</span>
        <motion.svg
          viewBox="0 0 20 20"
          fill="currentColor"
          className="w-3.5 h-3.5"
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </motion.svg>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-2 space-y-1">
              {eliminated.map((item, i) => (
                <motion.div
                  key={item.name || i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-white/[0.02]"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="w-1 h-3 rounded-full bg-red-500/40 shrink-0" />
                    <span className="text-xs text-white/40 truncate">{item.name}</span>
                  </div>
                  <ReasonCodeBadge code={item.reason_type || item.code} />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
