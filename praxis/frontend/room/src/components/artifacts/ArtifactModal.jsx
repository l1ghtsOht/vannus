import { motion } from 'framer-motion';

export default function ArtifactModal({ artifact, onClose }) {
  const { model_id, content, artifact_type, created_at, metadata } = artifact;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.92, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.92, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        onClick={e => e.stopPropagation()}
        className="glass p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white/70">{model_id}</span>
            {artifact_type && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-white/30">{artifact_type}</span>
            )}
          </div>
          <button onClick={onClose} className="text-white/30 hover:text-white/60 transition-colors">
            <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        <pre className="text-sm text-white/65 font-mono whitespace-pre-wrap leading-relaxed bg-white/[0.02] rounded-lg p-4 border border-white/[0.04]">
          {content}
        </pre>

        {created_at && (
          <p className="text-[10px] text-white/20 mt-3">
            Generated {new Date(created_at).toLocaleString()}
          </p>
        )}
      </motion.div>
    </motion.div>
  );
}
