import { motion, AnimatePresence } from 'framer-motion';

export default function DecayAlertList({ alerts }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="mt-3">
      <span className="text-[10px] uppercase tracking-wider text-red-400/50 font-medium mb-1 block">
        Decay Alerts
      </span>
      <div className="space-y-1">
        <AnimatePresence>
          {alerts.map((alert, i) => (
            <motion.div
              key={alert.model_id || i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 8 }}
              className="flex items-center gap-2 py-1 px-2 rounded-lg bg-red-500/[0.04] border border-red-500/[0.08]"
            >
              <motion.div
                className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1, repeat: Infinity }}
              />
              <span className="text-[10px] text-red-400/60 truncate">{alert.model_id || 'Unknown'}</span>
              <span className="text-[9px] text-red-400/30 ml-auto shrink-0">{alert.severity}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
