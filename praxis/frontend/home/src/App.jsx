import { useState, useRef, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Aurora from './components/Aurora';
import Nav from './components/Nav';
import Hero from './components/Hero';
import CommandBar from './components/CommandBar';
import MagicBento from './components/MagicBento/MagicBento';
import ConstraintPills, { CONSTRAINTS } from './components/ConstraintPills';
import LiveSummary from './components/LiveSummary';
import PathCards from './components/PathCards';
import InlineResults from './components/InlineResults';
import FeedbackCapture from './components/FeedbackCapture';
import HowItWorks from './components/HowItWorks';
import Footer from './components/Footer';
import useSearch from './hooks/useSearch';

const CONSTRAINT_LABELS = {
  free_tier: 'free', budget_50: 'under $50/mo', budget_100: 'under $100/mo',
  hipaa: 'HIPAA-compliant', soc2: 'SOC2-certified', gdpr: 'GDPR-compliant',
  beginner: 'beginner-friendly', open_source: 'open source', api_access: 'API access',
};

export default function App() {
  const { results, loading, error, lastQuery, search, reset } = useSearch();
  const [query, setQuery] = useState('');
  const [activeConstraints, setActiveConstraints] = useState(new Set());
  const commandBarRef = useRef(null);

  const toggleConstraint = useCallback((id) => {
    setActiveConstraints(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleSubmit = useCallback((q) => {
    const text = q || query;
    if (!text.trim()) return;
    const cLabels = [...activeConstraints].map(c => CONSTRAINT_LABELS[c] || c);
    const fullQuery = cLabels.length ? text + ', ' + cLabels.join(', ') : text;
    search(fullQuery);
  }, [query, activeConstraints, search]);

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  const handleCompare = useCallback(() => {
    commandBarRef.current?.setMode('compare');
    commandBarRef.current?.focus();
  }, []);

  const handleBentoClick = useCallback((searchQuery) => {
    setQuery(searchQuery);
    handleSubmit(searchQuery);
  }, [handleSubmit]);

  const hasResults = !!results;
  const showExplore = !hasResults && !loading;

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      {/* React Bits Aurora background */}
      <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none' }}>
        <Aurora
          colorStops={["#6366f1", "#e0e0ff", "#6366f1"]}
          amplitude={1.2}
          blend={0.6}
          speed={0.5}
        />
      </div>

      <div className="relative z-10">
        <Nav />
        <Hero />
        <CommandBar ref={commandBarRef} value={query} onChange={setQuery} onSubmit={handleSubmit} />

        <AnimatePresence mode="wait">
          {showExplore && (
            <motion.div key="explore" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
              <div className="relative py-4 px-6">
                <div className="max-w-2xl mx-auto">
                  <MagicBento
                    textAutoHide={false}
                    enableStars={true}
                    enableSpotlight={true}
                    enableBorderGlow={true}
                    enableTilt={false}
                    enableMagnetism={false}
                    clickEffect={true}
                    spotlightRadius={400}
                    particleCount={12}
                    glowColor="99, 102, 241"
                    disableAnimations={false}
                    onCardClick={handleBentoClick}
                  />
                </div>
              </div>
              <ConstraintPills active={activeConstraints} onToggle={toggleConstraint} />
              <LiveSummary task={null} constraints={activeConstraints} query={query} onSubmit={() => handleSubmit(query)} />
              <PathCards onCompare={handleCompare} />
              <div className="text-center text-[11px] text-white/30 mt-5 mb-8">
                253 tools · 11 trust signals · elimination-first methodology
              </div>
            </motion.div>
          )}

          {loading && (
            <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex items-center justify-center gap-2.5 py-16">
              <motion.div
                className="w-2 h-2 rounded-full bg-[#6366f1]"
                animate={{ scale: [0.8, 1.2, 0.8], opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.2, repeat: Infinity }}
              />
              <span className="text-[14px] text-white/40">Evaluating 253 tools...</span>
            </motion.div>
          )}

          {hasResults && (
            <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <InlineResults results={results} onReset={handleReset} />
              <FeedbackCapture query={lastQuery} results={results} />
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <div className="max-w-[640px] mx-auto px-4 text-center py-8">
            <div className="text-2xl mb-2 opacity-30">⚠</div>
            <p className="text-[13px] text-white/30">Something went wrong. Make sure the API is running on port 8000.</p>
          </div>
        )}

        <HowItWorks />
        <Footer />
      </div>
    </div>
  );
}
