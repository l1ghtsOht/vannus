import { motion } from 'framer-motion';

const TASKS = [
  { id: 'writing', label: 'Write content', query: 'I need writing tools for...', icon: 'M3 14.5l1-4L12.5 2l2.5 2.5L6.5 13l-4 1z' },
  { id: 'coding', label: 'Write code', query: 'I need coding tools for...', icon: 'M5 5L2 9l3 4M13 5l3 4-3 4M10 3L8 15' },
  { id: 'analytics', label: 'Analyze data', query: 'I need analytics tools for...', icon: 'M3 14V8M7 14V5M11 14V9M15 14V3' },
  { id: 'automation', label: 'Automate work', query: 'I need automation tools for...', icon: null },
  { id: 'support', label: 'Serve customers', query: 'I need customer support tools for...', icon: null },
  { id: 'appbuilding', label: 'Build an app', query: 'I need app-building tools for...', icon: null },
];

const CUSTOM_ICONS = {
  automation: <><circle cx="9" cy="9" r="6" stroke="currentColor" strokeWidth="1.3"/><path d="M9 5v4l3 2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/></>,
  support: <><circle cx="9" cy="6" r="3" stroke="currentColor" strokeWidth="1.3"/><path d="M3 16c0-3.3 2.7-6 6-6s6 2.7 6 6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></>,
  appbuilding: <><rect x="2" y="3" width="14" height="12" rx="2" stroke="currentColor" strokeWidth="1.3"/><path d="M2 7h14" stroke="currentColor" strokeWidth="1.3"/></>,
};

export default function TaskGrid({ selected, onSelect }) {
  return (
    <div className="max-w-[640px] mx-auto px-4 mt-4 grid grid-cols-3 gap-2 max-[700px]:grid-cols-2 max-[500px]:grid-cols-1">
      {TASKS.map((task, i) => (
        <motion.button
          key={task.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 + i * 0.05 }}
          whileHover={{ scale: 1.02 }}
          onClick={() => onSelect(task)}
          className={`flex flex-col items-center gap-1.5 py-3 px-2 rounded-xl text-center cursor-pointer transition-all ${
            selected === task.id
              ? 'border-[#6366f1] text-[#6366f1] bg-[rgba(99,102,241,0.04)]'
              : 'text-white/50 hover:border-white/15'
          }`}
          style={{ background: selected === task.id ? 'rgba(99,102,241,0.04)' : 'rgba(255,255,255,0.03)', border: `1px solid ${selected === task.id ? '#6366f1' : 'rgba(255,255,255,0.08)'}`, borderRadius: '12px' }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" className="shrink-0">
            {task.icon ? (
              <path d={task.icon} stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
            ) : (
              CUSTOM_ICONS[task.id]
            )}
          </svg>
          <span className="text-xs font-semibold">{task.label}</span>
        </motion.button>
      ))}
    </div>
  );
}
