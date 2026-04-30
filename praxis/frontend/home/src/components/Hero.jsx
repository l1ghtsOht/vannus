import { motion } from 'framer-motion';

export default function Hero() {
  return (
    <div className="text-center pt-24 pb-6 px-4">
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-6xl font-bold tracking-tight max-[600px]:text-4xl"
        style={{ background: 'linear-gradient(135deg, #f0f0f5 0%, #6366f1 50%, #50e3c2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}
      >
        Vannus
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.15 }}
        className="text-lg text-white/50 mt-3 max-w-md mx-auto max-[600px]:text-base"
      >
        Clarity in a crowded AI landscape.
      </motion.p>
    </div>
  );
}
