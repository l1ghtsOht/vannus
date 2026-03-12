import { motion, AnimatePresence } from 'framer-motion';
import { useRoomState, PHASES } from '../../context/RoomContext';
import ModelStreamPanel from './ModelStreamPanel';

export default function ExecutionStream() {
  const { phase, streamingBuffers, activeModels, executionEvents } = useRoomState();

  if (phase !== PHASES.EXECUTING && phase !== PHASES.COMPLETE) return null;

  // Collect all models that have streaming data
  const modelIds = Object.keys(streamingBuffers);
  if (modelIds.length === 0 && phase === PHASES.EXECUTING) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mb-6"
      >
        <div className="flex items-center gap-3">
          <div className="w-1 h-4 rounded-full bg-[#06b6d4]" />
          <span className="text-sm text-white/60">Working…</span>
          <motion.span
            className="text-xs text-white/30"
            animate={{ opacity: [0.3, 0.7, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            Getting started…
          </motion.span>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mb-6"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-1 h-4 rounded-full bg-[#06b6d4]" />
        <span className="text-sm text-white/60">
          {phase === PHASES.COMPLETE ? 'Done' : 'Working…'}
        </span>
        {phase === PHASES.EXECUTING && activeModels.length > 0 && (
          <span className="text-[10px] text-white/25">
            {activeModels.length} active
          </span>
        )}
      </div>

      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {modelIds.map((modelId, idx) => (
            <ModelStreamPanel
              key={modelId}
              modelId={modelId}
              content={streamingBuffers[modelId]}
              isActive={activeModels.includes(modelId)}
              index={idx}
            />
          ))}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
