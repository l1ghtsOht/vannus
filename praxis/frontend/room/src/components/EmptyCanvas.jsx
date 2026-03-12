import { motion } from 'framer-motion';
import { useRoomDispatch } from '../context/RoomContext';

const SUGGESTIONS = [
  'I want to build a website',
  'I need HIPAA-compliant writing tools under $50/mo',
  'Help me set up email marketing for my restaurant',
  'I want to automate my invoicing workflow',
  'Build a CRM for my 5-person sales team',
];

export default function EmptyCanvas() {
  const dispatch = useRoomDispatch();

  const handleSuggestion = (text) => {
    dispatch({ type: 'SET_QUERY', payload: text });
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      className="flex-1 flex flex-col items-center justify-center gap-8 px-12 py-16"
    >
      {/* Ambient orb */}
      <motion.div
        animate={{
          scale: [1, 1.05, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="w-20 h-20 rounded-full"
        style={{
          background: 'radial-gradient(circle, #6366f1 0%, transparent 70%)',
          filter: 'blur(20px)',
        }}
      />

      <div className="text-center">
        <h2 className="text-xl font-semibold text-white/90 mb-2">
          What do you want to build?
        </h2>
        <p className="text-sm text-white/40">
          Praxis evaluates 246 tools and eliminates everything that doesn't fit your context.
        </p>
      </div>

      {/* Suggestion chips */}
      <div className="flex flex-wrap gap-2 justify-center max-w-lg">
        {SUGGESTIONS.map((suggestion, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.08 }}
            whileHover={{ scale: 1.03, y: -1 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => handleSuggestion(suggestion)}
            className="px-3.5 py-1.5 rounded-full text-xs text-white/40 hover:text-white/70 transition-colors cursor-pointer"
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
            }}
          >
            {suggestion}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}
