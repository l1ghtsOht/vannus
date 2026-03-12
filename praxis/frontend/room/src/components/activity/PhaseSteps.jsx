import { motion } from 'framer-motion';
import { useRoomState, PHASES } from '../../context/RoomContext';

const STEPS = [
  { key: 'parse',     label: 'Understanding', phases: [PHASES.ELIMINATING] },
  { key: 'eliminate', label: 'Filtering',     phases: [PHASES.ELIMINATING] },
  { key: 'route',     label: 'Selecting',     phases: [PHASES.ROUTING] },
  { key: 'execute',   label: 'Creating',      phases: [PHASES.EXECUTING] },
  { key: 'complete',  label: 'Done',          phases: [PHASES.COMPLETE] },
];

const PHASE_ORDER = [PHASES.IDLE, PHASES.ELIMINATING, PHASES.ROUTING, PHASES.EXECUTING, PHASES.COMPLETE];

function stepStatus(stepPhases, currentPhase) {
  const currentIdx = PHASE_ORDER.indexOf(currentPhase);
  const stepIdx = PHASE_ORDER.indexOf(stepPhases[0]);
  if (currentIdx > stepIdx) return 'done';
  if (stepPhases.includes(currentPhase)) return 'active';
  return 'pending';
}

export default function PhaseSteps() {
  const { phase } = useRoomState();

  if (phase === PHASES.IDLE) return null;

  return (
    <div className="flex items-center gap-1 px-4 py-2.5 border-b border-white/[0.04]">
      {STEPS.map((step, i) => {
        const status = stepStatus(step.phases, phase);
        return (
          <div key={step.key} className="flex items-center gap-1">
            {i > 0 && (
              <div
                className="w-6 h-px mx-0.5"
                style={{
                  background: status === 'pending'
                    ? 'rgba(255,255,255,0.06)'
                    : 'rgba(99,102,241,0.4)',
                }}
              />
            )}
            <div className="flex items-center gap-1.5">
              {status === 'done' ? (
                <div className="w-4 h-4 rounded-full bg-[#6366f1]/20 flex items-center justify-center">
                  <svg viewBox="0 0 12 12" className="w-2.5 h-2.5 text-[#6366f1]">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              ) : status === 'active' ? (
                <motion.div
                  className="w-4 h-4 rounded-full flex items-center justify-center"
                  style={{ background: 'rgba(99,102,241,0.25)', boxShadow: '0 0 12px rgba(99,102,241,0.3)' }}
                  animate={{ scale: [1, 1.15, 1], opacity: [0.8, 1, 0.8] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-[#6366f1]" />
                </motion.div>
              ) : (
                <div className="w-4 h-4 rounded-full bg-white/[0.04] flex items-center justify-center">
                  <div className="w-1 h-1 rounded-full bg-white/10" />
                </div>
              )}
              <span
                className="text-[10px] uppercase tracking-wider font-medium"
                style={{
                  color: status === 'active' ? 'rgba(99,102,241,0.9)'
                       : status === 'done' ? 'rgba(255,255,255,0.4)'
                       : 'rgba(255,255,255,0.15)',
                }}
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
