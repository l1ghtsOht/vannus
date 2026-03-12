import { motion, AnimatePresence } from 'framer-motion';

export default function DecayOverlay({ severity, modelId }) {
  if (!severity) return null;

  const isSevere = severity === 'SEVERE';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl pointer-events-none"
        style={{
          backgroundColor: isSevere ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.05)',
        }}
      >
        <motion.div
          className="absolute inset-0 rounded-2xl"
          animate={{
            boxShadow: isSevere
              ? ['inset 0 0 20px rgba(239,68,68,0.15)', 'inset 0 0 40px rgba(239,68,68,0.25)', 'inset 0 0 20px rgba(239,68,68,0.15)']
              : ['inset 0 0 15px rgba(245,158,11,0.10)', 'inset 0 0 25px rgba(245,158,11,0.18)', 'inset 0 0 15px rgba(245,158,11,0.10)'],
          }}
          transition={{ duration: isSevere ? 0.8 : 1.5, repeat: Infinity }}
        />
        {isSevere && (
          <motion.span
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-xs font-medium text-red-400/70 bg-red-500/10 px-3 py-1 rounded-full border border-red-500/20"
          >
            Rerouting…
          </motion.span>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
