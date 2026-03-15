import { useState, useRef, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Nav from './components/Nav';
import Hero from './components/Hero';
import CommandBar from './components/CommandBar';
import TaskGrid from './components/TaskGrid';
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
  const [selectedTask, setSelectedTask] = useState(null);
  const [activeConstraints, setActiveConstraints] = useState(new Set());
  const commandBarRef = useRef(null);

  const handleTaskSelect = useCallback((task) => {
    if (selectedTask === task.id) {
      setSelectedTask(null);
    } else {
      setSelectedTask(task.id);
      setQuery(task.query);
      commandBarRef.current?.focus();
    }
  }, [selectedTask]);

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

  const hasResults = !!results;
  const showExplore = !hasResults && !loading;

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      {/* Animated aurora background */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <motion.div
          animate={{ x: [0, 40, -30, 20], y: [0, -30, 20, -10], scale: [1, 1.1, 0.95, 1.05] }}
          transition={{ duration: 18, repeat: Infinity, repeatType: 'reverse' }}
          className="absolute rounded-full"
          style={{ width: 700, height: 700, top: '-15%', left: '-10%', background: 'radial-gradient(circle, #6366f1 0%, transparent 70%)', filter: 'blur(120px)', opacity: 0.35 }}
        />
        <motion.div
          animate={{ x: [0, -30, 20, -20], y: [0, 20, -30, 10], scale: [1, 0.95, 1.1, 1] }}
          transition={{ duration: 22, repeat: Infinity, repeatType: 'reverse', delay: 8 }}
          className="absolute rounded-full"
          style={{ width: 600, height: 600, bottom: '-20%', right: '-10%', background: 'radial-gradient(circle, #50e3c2 0%, transparent 70%)', filter: 'blur(120px)', opacity: 0.35 }}
        />
        <motion.div
          animate={{ x: [-20, 20, -10], y: [0, -20, 10], scale: [1, 1.05, 0.98] }}
          transition={{ duration: 25, repeat: Infinity, repeatType: 'reverse' }}
          className="absolute rounded-full"
          style={{ width: 500, height: 500, top: '40%', left: '50%', transform: 'translateX(-50%)', background: 'radial-gradient(circle, #f5a623 0%, transparent 70%)', filter: 'blur(100px)', opacity: 0.15 }}
        />
      </div>

      <div className="relative z-10">
        <Nav />
        <Hero />
        <CommandBar ref={commandBarRef} value={query} onChange={setQuery} onSubmit={handleSubmit} />

        <AnimatePresence mode="wait">
          {showExplore && (
            <motion.div key="explore" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
              <TaskGrid selected={selectedTask} onSelect={handleTaskSelect} />
              <ConstraintPills active={activeConstraints} onToggle={toggleConstraint} />
              <LiveSummary task={selectedTask} constraints={activeConstraints} query={query} onSubmit={() => handleSubmit(query)} />
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
