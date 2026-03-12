import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRoomState, PHASES } from '../../context/RoomContext';
import PatternBadge from './PatternBadge';
import ModelCard from './ModelCard';
import RoutingExplanation from './RoutingExplanation';

export default function RoutingPlan() {
  const { differentialResult, routingDecision, phase } = useRoomState();
  const [expanded, setExpanded] = useState(false);

  // Show during routing, executing, and complete phases
  if (phase !== PHASES.ROUTING && phase !== PHASES.EXECUTING && phase !== PHASES.COMPLETE) return null;
  if (!differentialResult) return null;

  const survivors = differentialResult.tools_recommended || differentialResult.survivors || [];
  const strategy = routingDecision?.strategy || (survivors.length > 1 ? 'FAN_OUT' : 'SINGLE');
  const summaryText = survivors.length > 1
    ? `Using ${survivors.length} models together`
    : `Using best matching model`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className="mb-6"
    >
      {/* Strategy Header */}
      <div
        className="flex items-center gap-3 mb-4 cursor-pointer group"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="w-1 h-4 rounded-full bg-[#f59e0b]" />
        <span className="text-sm text-white/60">{summaryText}</span>
        <PatternBadge strategy={strategy} />
        <svg
          viewBox="0 0 20 20"
          fill="currentColor"
          className={`w-3 h-3 text-white/25 group-hover:text-white/50 transition-transform ${expanded ? 'rotate-180' : ''}`}
        >
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
            {/* Routing Explanation */}
            {routingDecision?.reasoning && (
              <RoutingExplanation reasoning={routingDecision.reasoning} />
            )}

            {/* Model Cards */}
            <div className="space-y-2 mb-4">
              <AnimatePresence mode="popLayout">
                {survivors.map((model, idx) => (
                  <ModelCard key={model.name || idx} model={model} index={idx} />
                ))}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
