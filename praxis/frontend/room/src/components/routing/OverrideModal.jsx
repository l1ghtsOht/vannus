import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function OverrideModal({ models, onSelect, onClose }) {
  if (!models || models.length === 0) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          onClick={e => e.stopPropagation()}
          className="glass p-5 max-w-sm w-full mx-4"
        >
          <h3 className="text-sm font-medium text-white/70 mb-4">Override Model Selection</h3>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {models.map((model, i) => (
              <button
                key={model.name || i}
                onClick={() => { onSelect(model); onClose(); }}
                className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 transition-colors flex items-center justify-between"
              >
                <span className="text-xs text-white/60">{model.name}</span>
                {model.trust_score != null && (
                  <span className="text-[10px] text-white/30 font-mono">{(model.trust_score * 100).toFixed(0)}%</span>
                )}
              </button>
            ))}
          </div>

          <button
            onClick={onClose}
            className="mt-4 w-full text-xs text-white/30 hover:text-white/50 py-2 transition-colors"
          >
            Cancel
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
