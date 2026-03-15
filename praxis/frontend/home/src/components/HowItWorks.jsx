import { motion } from 'framer-motion';

const STEPS = [
  { num: '1', title: 'You describe what you need', desc: 'Task type, budget, compliance requirements, skill level. Tell us what matters to your business.' },
  { num: '2', title: 'We eliminate what doesn\'t fit', desc: '253 tools checked against your budget, compliance, trust scores, and skill level. Most don\'t survive.' },
  { num: '3', title: 'You keep the survivors', desc: 'Ranked by fit, with reasons for every elimination and every recommendation. Full transparency.' },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="max-w-[800px] mx-auto px-4 py-16" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
      <div className="text-center mb-8">
        <h2 className="text-lg font-medium text-white">How it works</h2>
        <p className="text-[13px] text-white/35 mt-1">Elimination-first. Not recommendation-first.</p>
      </div>
      <div className="grid grid-cols-3 gap-4 max-[700px]:grid-cols-1">
        {STEPS.map((step, i) => (
          <motion.div
            key={step.num}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ delay: i * 0.12 }}
            className="text-center rounded-2xl p-6"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}
          >
            <div className="text-2xl font-bold text-[#6366f1] mb-2.5">{step.num}</div>
            <div className="text-[15px] font-bold text-white mb-2">{step.title}</div>
            <div className="text-[13px] text-white/40 leading-relaxed">{step.desc}</div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
