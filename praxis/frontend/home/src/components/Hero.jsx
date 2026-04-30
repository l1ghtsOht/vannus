import { motion } from 'framer-motion';

export default function Hero() {
  return (
    <div className="text-center pt-28 pb-8 px-4">
      <motion.h1
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="text-7xl font-bold tracking-tighter max-[600px]:text-5xl"
        style={{
          background: 'linear-gradient(135deg, #ffffff 0%, #c7d2fe 35%, #6366f1 65%, #34d399 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          lineHeight: 1.05,
        }}
      >
        Vannus
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="text-lg text-white/45 mt-4 max-w-md mx-auto max-[600px]:text-base"
        style={{ letterSpacing: '0.01em', lineHeight: 1.5 }}
      >
        Not every AI tool deserves your time.
      </motion.p>
    </div>
  );
}
