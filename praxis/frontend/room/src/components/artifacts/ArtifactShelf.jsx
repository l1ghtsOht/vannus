import { motion, AnimatePresence } from 'framer-motion';
import { useRoomState, useRoomDispatch, PHASES } from '../../context/RoomContext';
import ArtifactCard from './ArtifactCard';

export default function ArtifactShelf() {
  const { artifacts, phase, selectedArtifactId } = useRoomState();
  const dispatch = useRoomDispatch();

  if (!artifacts || artifacts.length === 0) return null;

  const isComplete = phase === PHASES.COMPLETE;
  const selectedArtifact = artifacts.find(a => a.id === selectedArtifactId) || artifacts[artifacts.length - 1];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mb-4"
    >
      {/* Artifact tabs when multiple */}
      {artifacts.length > 1 && (
        <div className="flex gap-1 mb-3 overflow-x-auto scrollbar-thin pb-1">
          {artifacts.map((artifact, idx) => {
            const isSelected = artifact.id === selectedArtifact?.id;
            return (
              <button
                key={artifact.id || idx}
                onClick={() => dispatch({ type: 'SET_SELECTED_ARTIFACT', payload: artifact.id })}
                className={`shrink-0 px-2.5 py-1 rounded-md text-[10px] font-medium transition-all ${
                  isSelected
                    ? 'bg-emerald-500/20 text-emerald-400/90 border border-emerald-500/30'
                    : 'bg-white/5 text-white/30 border border-white/[0.06] hover:bg-white/10 hover:text-white/50'
                }`}
              >
                {artifact.title || artifact.model_id || `Result ${idx + 1}`}
              </button>
            );
          })}
        </div>
      )}

      {/* Selected artifact rendered in canvas mode */}
      <AnimatePresence mode="wait">
        {selectedArtifact && (
          <ArtifactCard
            key={selectedArtifact.id}
            artifact={selectedArtifact}
            index={0}
            canvas
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}
