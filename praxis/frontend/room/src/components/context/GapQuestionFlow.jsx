import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function GapQuestionFlow({ gaps, onAnswer, onClose }) {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});

  if (!gaps || gaps.length === 0) return null;
  const current = gaps[currentIdx];

  const handleAnswer = (value) => {
    const updated = { ...answers, [current.key]: value };
    setAnswers(updated);
    if (currentIdx < gaps.length - 1) {
      setCurrentIdx(currentIdx + 1);
    } else {
      onAnswer(updated);
      onClose();
    }
  };

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
          className="glass p-6 max-w-md w-full mx-4"
        >
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs text-white/40 uppercase tracking-wider">
              Gap Question {currentIdx + 1}/{gaps.length}
            </span>
            <button onClick={onClose} className="text-white/30 hover:text-white/60">
              <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>

          <h4 className="text-sm text-white/80 font-medium mb-1">{current.label || current.key}</h4>
          <p className="text-xs text-white/40 mb-4">{current.description || 'Please provide this missing context.'}</p>

          <input
            autoFocus
            type="text"
            placeholder="Type your answer…"
            onKeyDown={e => e.key === 'Enter' && e.target.value && handleAnswer(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/80 placeholder-white/20 outline-none focus:border-[#6366f1]/50 transition-colors"
          />

          <div className="flex justify-between items-center mt-4">
            <button
              onClick={onClose}
              className="text-xs text-white/30 hover:text-white/60 transition-colors px-3 py-1"
            >
              Skip All
            </button>
            <div className="flex gap-1">
              {gaps.map((_, i) => (
                <div
                  key={i}
                  className="w-1.5 h-1.5 rounded-full transition-colors"
                  style={{ backgroundColor: i <= currentIdx ? '#6366f1' : 'rgba(255,255,255,0.1)' }}
                />
              ))}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
