import { motion } from 'framer-motion';

function trustLevel(score) {
  if (score >= 0.8) return { color: '#10b981', label: 'Healthy' };
  if (score >= 0.5) return { color: '#f59e0b', label: 'Mild' };
  return { color: '#ef4444', label: 'Severe' };
}

export default function TrustPill({ score }) {
  if (score == null) return null;
  const { color, label } = trustLevel(score);

  return (
    <motion.span
      className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full"
      style={{
        backgroundColor: `${color}15`,
        color: `${color}cc`,
        border: `1px solid ${color}25`,
      }}
      animate={label === 'Severe' ? {
        boxShadow: [`0 0 8px ${color}20`, `0 0 16px ${color}40`, `0 0 8px ${color}20`],
      } : {}}
      transition={label === 'Severe' ? { duration: 1.2, repeat: Infinity } : {}}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </motion.span>
  );
}
